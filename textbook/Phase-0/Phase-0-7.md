# Phase 0-7: API 設計

## この章のゴール

DeciTima のバックエンド API を設計する。

- エンドポイント一覧と、MVP で実際に生やすものの絞り込み
- リクエスト/レスポンススキーマ(`app/schemas/`)
- 同期実行の契約と、結果を後から引く導線
- エラーレスポンスの形式(既存ハンドラに乗せる)
- 認証・レート制限の適用

「実装計画(Implementation Plan)」の一部にあたる。

---

## 1. API 設計の原則

`decitima-api` のテンプレート方針(`decitima-api/CLAUDE.md`)を踏襲する。

- **routes は薄く**: 「サービスを呼ぶ → スキーマに詰めて返す」だけ。ロジックも
  例外処理も書かない。
- **プレフィックスは `/api/v1`**(既存 `settings.API_V1_PREFIX`)。
- **認証は JWT**(既存 `CurrentUserDep`)。
- **エラーは `AppError` → `register_error_handlers` が JSON 化**。

---

## 2. エンドポイント一覧

README 17 節は `algorithms.py / optimization.py / scheduling.py / projects.py /
simulation.py / llm.py` を挙げているが、これは Phase 14 までの全体像。
**MVP(Phase 0〜5)で必要なものだけ**に絞る。

| メソッド & パス | 用途 | 導入 Phase | MVP |
| --- | --- | --- | --- |
| `POST /api/v1/solve` | 構造化問題を解いて解を返す(本流) | 1 | ✅ |
| `GET /api/v1/problems/{id}` | 永続化された問題を取得 | 1 | ✅ |
| `GET /api/v1/solutions/{id}` | 永続化された解を取得(将来の非同期化に備える) | 1 | ✅ |
| `GET /api/v1/problems/{id}/solutions` | ある問題に対する全解(複数アルゴリズム分) | 3 | ✅ |
| `POST /api/v1/verify` | 問題 + 解を渡して検証だけ実行 | 2 | ✅ |
| `GET /api/v1/algorithms` | registry のアルゴリズム一覧(name / family / implementation) | 1 | ✅ |
| `POST /api/v1/benchmark` | 1 問題を複数アルゴリズムで解いて比較 | 3 | ✅ |
| `POST /api/v1/algorithms/{name}/run` | 生のアルゴリズム単体実行(教材・デバッグ用) | 1 | 任意 |
| `POST /api/v1/simulate` | What-if シナリオ比較 | 9 | ❌ |
| `POST /api/v1/interpret` | 自然言語 → OptimizationProblem(LLM) | 10 | ❌ |

Route Planner / Shift Scheduler は**専用エンドポイントを作らない**。
`POST /solve` に `problem_type` 付きの `OptimizationProblem` を渡すだけ。
これが共通スキーマ設計(Phase 0-2)の狙いどおりの姿。

---

## 3. リクエスト / レスポンススキーマ

`app/schemas/optimization.py`(新規)。`app/domain/` のモデルを import して薄く包む。

### 3.1 `POST /solve`

```python
class SolveRequest(BaseModel):
    """solve API のリクエスト。構造化済みの問題と、任意のアルゴリズム指定。"""

    problem: OptimizationProblem          # domain のモデルをそのまま
    algorithm: str | None = None          # 指定なければ rule-based 選択
    persist: bool = True                  # False なら結果を保存しない（教材の試行用）
    timeout_seconds: float | None = None   # 上限は settings で制限


class SolveResponse(BaseModel):
    """solve API のレスポンス。解と、永続化された場合の ID。"""

    solution: CandidateSolution
    problem_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
```

### 3.2 `POST /verify`

```python
class VerifyRequest(BaseModel):
    problem: OptimizationProblem
    solution: CandidateSolution

class VerifyResponse(BaseModel):
    status: Literal["valid", "invalid", "infeasible"]
    violations: list[ConstraintViolation]
    metrics: dict[str, float]
```

### 3.3 `GET /algorithms`

```python
class AlgorithmInfo(BaseModel):
    name: str
    family: str
    implementation: str
    problem_types: list[str]      # registry でこのアルゴリズムが登録されている problem_type
    time_complexity: str | None = None

class AlgorithmListResponse(BaseModel):
    algorithms: list[AlgorithmInfo]
```

### 3.4 `POST /benchmark`(Phase 3)

```python
class BenchmarkRequest(BaseModel):
    problem: OptimizationProblem
    algorithms: list[str] | None = None   # None なら problem_type の全候補
    runs: int = 3                          # 中央値を取るための試行回数

class BenchmarkEntry(BaseModel):
    algorithm: AlgorithmMeta
    solution_status: str
    metrics: dict[str, float]              # total_weight / labor_cost 等
    elapsed_ms_median: float
    peak_memory_kb: float
    operation_count: int | None = None

class BenchmarkResponse(BaseModel):
    entries: list[BenchmarkEntry]          # solve 品質と実行コストを並べて比較できる
```

> **[Phase 3 でサンプル修正 ── 実装に同期]** このスケッチのとおり実装したうえで:
> `BenchmarkEntry` に `elapsed_ms_p25` / `elapsed_ms_p75`(中央値だけでなく散らばりも)、
> `hard_violations` / `soft_violations`(6 指標の「制約違反数」)、`quality_ratio`(指標「解の
> 品質」= 目的値 / run 中最良値)を追加。`BenchmarkRequest` に `persist` / `timeout_seconds`、
> `BenchmarkResponse` に `benchmark_id`(solve と同じ永続化パターン)。以降 samples は
> `textbook/Phase-3/samples/app/schemas/optimization.py`。詳細 `Phase-3-1.md` / `Phase-3-3.md`。

---

## 4. `POST /solve` の実装スケッチ

```python
# app/api/routes/solve.py
from fastapi import APIRouter
from app.api.deps import CurrentUserDep, RedisDep, SessionDep
from app.schemas.optimization import SolveRequest, SolveResponse
from app.services.solve import SolveService

router = APIRouter(prefix="/solve", tags=["solve"])


@router.post("", response_model=SolveResponse)
async def solve(
    payload: SolveRequest,
    session: SessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> SolveResponse:
    """構造化された最適化問題を受け取り、決定論的に解いて検証済みの解を返す。"""
    result = await SolveService(session, redis).solve(
        user_id=current_user.id,
        request=payload,
        bypass_rate_limit=current_user.is_superuser,
    )
    return SolveResponse(
        solution=result.solution,
        problem_id=result.problem_id,
        solution_id=result.solution_id,
    )
```

ルートはこれだけ。バリデーション NG・タイムアウト・アルゴリズム未登録は
`SolveService` 内で `AppError` 派生が送出され、既存ハンドラが JSON 化する。

---

## 5. エラーレスポンスの形式

既存テンプレートの `register_error_handlers` は `AppError` を
`{"detail": "<message>"}` + 対応ステータスコードに変換する。
DeciTima もこの形式に乗る。

| 事象 | ステータス | ボディ |
| --- | --- | --- |
| Pydantic 型/値域違反 | 422 | `{"detail": [{"loc": [...], "msg": "...", ...}]}`(FastAPI 標準) |
| セマンティック検査 NG | 400 | `{"detail": "start node 'X' not found in nodes; ..."}` |
| 実行不可能 | 400 | `{"detail": "required headcount 3 exceeds 2 available staff for slot s1"}` |
| アルゴリズム未登録 | 400 | `{"detail": "no algorithm registered for 'travel_planning'"}` |
| タイムアウト | 504 | `{"detail": "solve exceeded 10.0s"}` |
| レート制限 | 429 | `{"detail": "Rate limit exceeded for solve (20 per 3600s)"}` |
| 認証エラー | 401 | 生の `HTTPException`(認証境界の既存方針) |

`decitima-ui` の `apiFetch` は `{detail: string}` と 422 の
`{detail: [{msg}]}` の両方をパースできる(既存実装)。そのまま連携できる。

---

## 6. 認証とレート制限

### 6.1 認証

- solve / verify / benchmark は **認証必須**(`CurrentUserDep`)。
- `GET /algorithms` は認証不要でもよいが、MVP では統一して認証必須にしておく
  (公開の必要が出たら緩める)。

### 6.2 レート制限

既存の `RateLimiter`(`app/services/rate_limit.py`)を `resource="solve"` で再利用。

```python
# SolveService の中
await RateLimiter(
    redis,
    resource="solve",
    limits=[
        RateLimit(window_seconds=3600, max_requests=settings.SOLVE_RATE_LIMIT_PER_HOUR),
        RateLimit(window_seconds=86400, max_requests=settings.SOLVE_RATE_LIMIT_PER_DAY),
    ],
).enforce(str(user_id))
```

- `settings` に `SOLVE_RATE_LIMIT_PER_HOUR` / `_PER_DAY` を追加(既存の
  `CHAT_RATE_LIMIT_*` と同じパターン)。
- `is_superuser` はレート制限バイパス(既存 chat と同じ挙動)。
- **`RateLimiter` の汎用性**: `resource` を変えるだけで別機能に使える設計は
  テンプレート由来の良い部分。DeciTima 側で改善(複数リソースの一括
  enforce など)が出たら `fastapi-langchain-template` への還元を提案する。

---

## 7. OpenAPI とドキュメント

- 開発環境では `/docs`(Swagger)/ `/redoc` が有効(既存)。本番は無効(既存)。
- `SolveRequest` に `OptimizationProblem` がそのまま入るので、Swagger 上で
  ハイブリッドスキーマ(判別可能ユニオン)がどう見えるか Phase 1 で確認する。
  Pydantic v2 + FastAPI は discriminated union の OpenAPI 出力に対応している。
- `decitima-ui` は当面 OpenAPI 自動生成を使わず、`src/lib/api/types.ts` に
  手書きの TS 型を置く(Phase 0-3)。API が固まる Phase 1 以降で見直す。

---

## 8. 検証 ── 2 題材の API 呼び出し

### 8.1 Route Planner

```
POST /api/v1/solve
Authorization: Bearer <token>
{
  "problem": { "problem_type": "route_planning", "objectives": [...],
               "constraints": [...], "data": { ... } },
  "algorithm": "dijkstra"
}
        ▼
200 OK
{
  "solution": { "status": "valid",
                "assignments": { "problem_type": "route_planning",
                                 "path_node_ids": ["A","B","C","E"], ... },
                "metrics": { "total_weight": 9 },
                "produced_by": { "name": "dijkstra", "implementation": "handwritten" } },
  "problem_id": "…", "solution_id": "…"
}
```

### 8.2 Shift Scheduler

同じ `POST /solve`。`problem.problem_type` が `"shift_scheduling"` で
`data` が `ShiftData`、`objectives` が 2 要素(多目的)。レスポンスの
`solution.assignments` が `ShiftSolution`(割当表)。

**確認**: 2 つの全く違う問題が同じ 1 エンドポイントで扱える。
`problem_type` の判別子がリクエスト/レスポンス両方で効いている。

### 8.3 比較(Phase 3)

```
POST /api/v1/benchmark
{ "problem": { "problem_type": "route_planning", ... },
  "algorithms": ["dijkstra", "a_star"], "runs": 5 }
        ▼
{ "entries": [
    { "algorithm": {"name":"dijkstra","implementation":"handwritten"},
      "metrics": {"total_weight": 9}, "elapsed_ms_median": 0.8, "operation_count": 12 },
    { "algorithm": {"name":"a_star","implementation":"handwritten"},
      "metrics": {"total_weight": 9}, "elapsed_ms_median": 0.5, "operation_count": 7 }
] }
```

将来 networkx 版を registry に足せば、この `entries` に
`{"name":"dijkstra","implementation":"library:networkx"}` が並ぶ。

---

## 9. まとめ

- MVP のエンドポイントは `POST /solve` を軸に、`problems` / `solutions` /
  `verify` / `algorithms` / `benchmark`。Route / Shift の専用エンドポイントは作らない。
- スキーマ(`app/schemas/optimization.py`)は `app/domain/` のモデルを薄く包む。
- ルートは「サービス呼ぶ → 詰めて返す」だけ。エラーは `AppError` 派生 → 既存ハンドラ。
- 認証は既存 `CurrentUserDep`、レート制限は既存 `RateLimiter` を `resource="solve"` で。
- solve 結果は必ず永続化し `solution_id` で引ける ── 将来の非同期化に備える。

次章(Phase 0-8)では、永続化する **DB** のスキーマを設計する。

---

## 後続 Phase での改訂

- **[Phase 1]** `POST /solve` / `GET /algorithms` / `GET /problems|solutions/{id}` を実装
  (`Phase-1-6.md` / `Phase-1-7.md`)。
- **[Phase 2]** `POST /api/v1/verify` を §3.2 の設計どおり実装。`VerifyService` は DB を
  触らず、Semantic Validation も走らせない(解の検証だけ)。レート制限は `resource="verify"`。
  `Phase-2-5.md`。
