# Phase 1-7: 取得系と Phase 2 への引き継ぎ(作業単位 1-7)

## この章のゴール

保存済みの問題・解を取り出す API と、registry の一覧 API を足す。将来 solve を非同期
ジョブ化しても、この取得 API は変わらない(`Phase-0-5.md` §5.2)。最後に Phase 1 を締めて
Phase 2 への引き継ぎをまとめる。

- `OptimizationReadService`(所有者スコープの取得)
- `GET /api/v1/algorithms` / `GET /api/v1/solutions/{id}` / `GET /api/v1/problems/{id}` /
  `GET /api/v1/problems/{id}/solutions`
- ルーター集約(`app/api/routes/__init__.py` への追記)
- Phase 2 の作業分割

**この章で新規作成するファイル**: `app/services/optimization_read.py`、
`app/api/routes/algorithms.py`、`app/api/routes/solutions.py`。取得系のレスポンススキーマ
(`AlgorithmInfo` / `AlgorithmListResponse` / `SolutionRead` / `ProblemRead`)は
`app/schemas/optimization.py`([Phase-1-6](./Phase-1-6.md) §5 で新規作成済みのファイル)に足す。
**既存ファイルへの追記**: `app/api/routes/__init__.py`(§3 ── `algorithms` / `solutions` の 2 本。
`solve` は [Phase-1-6](./Phase-1-6.md) §5 で追加済み)。

対応サンプル: `samples/app/services/optimization_read.py`,
`samples/app/api/routes/{algorithms,solutions}.py`, `samples/app/schemas/optimization.py`。
テストは `samples/tests/api/test_algorithms_solutions_api.py`。設計は `Phase-0-7.md` §2。

---

## 1. 取得系スキーマと `OptimizationReadService`

`app/schemas/optimization.py`(既存 = [Phase-1-6](./Phase-1-6.md) §5 で作った)に足す:

```python
# app/schemas/optimization.py(つづき)
class AlgorithmInfo(BaseModel):
    name: str
    family: str
    implementation: str
    problem_types: list[str]           # この (name, implementation) が登録されている problem_type
    time_complexity: str | None = None

class AlgorithmListResponse(BaseModel):
    algorithms: list[AlgorithmInfo]

class SolutionRead(BaseModel):         # 永続化された解の読み出し。payload に CandidateSolution 全体
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; problem_id: uuid.UUID; status: str
    algorithm_name: str; algorithm_implementation: str
    created_at: datetime; payload: dict

class ProblemRead(BaseModel):          # 同上、payload に OptimizationProblem 全体
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; problem_type: str; created_at: datetime; payload: dict
```

```python
# app/services/optimization_read.py ── 所有者スコープ(他ユーザーのものは NotFoundError → 404)
class OptimizationReadService:
    async def get_problem(self, problem_id, *, user_id) -> Problem: ...
    async def get_solution(self, solution_id, *, user_id) -> Solution:   # solutions ⨝ problems で所有者確認
    async def list_solutions_for_problem(self, problem_id, *, user_id) -> list[Solution]: ...
```

- 解の所有者は `Solution.problem_id → Problem.user_id`。`get_solution` は 2 テーブルを結合して
  `Problem.user_id == user_id` を条件に入れる。一致しなければ `NotFoundError`(404。403 ではなく
  「存在しない」に倒す)。

---

## 2. 取得系ルート

```python
# app/api/routes/algorithms.py    GET /api/v1/algorithms
#   registry の all_strategies() を (name, implementation) で集約し problem_types を付けて返す
router = APIRouter(prefix="/algorithms", tags=["algorithms"])

# app/api/routes/solutions.py     GET /api/v1/solutions/{id}
#                                 GET /api/v1/problems/{id}
#                                 GET /api/v1/problems/{id}/solutions
router = APIRouter(tags=["solutions"])   # prefix なし(/solutions と /problems の両方を持つ)
```

いずれも認証必須(MVP は統一。公開が必要になったら緩める)。ルートは薄く、
`OptimizationReadService` を呼んで `SolutionRead` / `ProblemRead` / `AlgorithmListResponse` に
詰めて返すだけ。

---

## 3. ルーター集約(既存ファイルへの追記)

`app/api/routes/__init__.py` は既存。samples には入れず、import と `include_router` を足す。
`solve_router` は [Phase-1-6](./Phase-1-6.md) §5 で追加済みなので、この章では
**`algorithms` / `solutions` の 2 本**を足す(進行ルール #15 ── ルートはそれを作る章で集約する):

```python
# app/api/routes/__init__.py
from app.api.routes.algorithms import router as algorithms_router  # ← 追加
from app.api.routes.auth import router as auth_router
from app.api.routes.solutions import router as solutions_router    # ← 追加
from app.api.routes.solve import router as solve_router            # (1-6 で追加済み)
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(solve_router)        # (1-6 で追加済み)
api_router.include_router(algorithms_router)   # ← 追加
api_router.include_router(solutions_router)    # ← 追加
# chat_router は Phase 10 まで無効のまま(既存の方針)
```

---

## 4. テスト観点

> **テスト対象 / ドライバ / スタブ**(進行ルール #14):
> - **対象**: `OptimizationReadService`(所有者スコープの取得)と取得系ルート
>   (`GET /algorithms` / `/solutions/{id}` / `/problems/{id}(/solutions)`)
> - **ドライバ**: `httpx.AsyncClient`(+ `create_access_token` で JWT 発行)
> - **スタブ / テストダブル**: 依存差し替え(`get_db` → インメモリ SQLite、
>   `get_redis` → `FakeRedis`)。registry は本物(純粋)。

| ファイル | 観点 |
| --- | --- |
| `test_algorithms_solutions_api.py` | `GET /algorithms` に `dijkstra`(family / implementation / problem_types)/ solve → `GET /solutions/{id}` で取得 / `GET /problems/{id}/solutions` / 未知 id で 404 / 他ユーザーの解は 404 |

API テストは [Phase-1-6](./Phase-1-6.md) §6 と同じく依存差し替え(実 PG / Redis 不要)。

---

## 5. Phase 2 への引き継ぎ

Phase 1 で「枠」を通した Validation / Verification を、Phase 2 で埋める。

| # | Phase 2 の作業単位 | 内容 |
| --- | --- | --- |
| 2-1 | Pydantic Validation の拡充 | `ShiftSlot` の `end_hour > start_hour` 等のフィールド間 `model_validator`、`field_validator` |
| 2-2 | Semantic Validation(shift) | 各スロットの割当可能スタッフ数 ≥ `required_headcount` / 必要スキル保持者の存在 / `max_weekly_hours` の下限。`_SEMANTIC_CHECKS` を problem_type ごとに整理し `domain/problems/` へ切り出す |
| 2-3 | Constraint Checker の全実装 | `numeric_bound` / `staffing` ほか kind ごとのチェッカーを `app/domain/constraints/` に。`_CHECKERS` を完成させる |
| 2-4 | Verification(shift) | 全スロット割当人数 / 週勤務時間 / 連続勤務日数 / available スロット / 希望休 → `soft_penalty` / `labor_cost` ・ `day_off_satisfaction` の metrics |
| 2-5 | `POST /api/v1/verify` | 問題 + 解を渡して検証だけ実行(`VerifyRequest` / `VerifyResponse` は `Phase-0-7.md` §3.2) |
| 2-6 | Invalid Solution Handling | `status="invalid"` の解のレスポンス表現・保存・UI への伝え方の整理 |
| 2-7 | `verifications` テーブル | 「hard 違反した解だけ集計」等のクエリ需要が出たら `Solution.payload` から切り出す(`Phase-0-8.md` §4) |

多目的の重み付き和の評価器(`app/domain/objectives/`)は Phase 1 では作らない。初の多目的
ストラテジー(Phase 5 の Shift Scheduler)を実装するときに追加する
(`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の `[Phase 1 改訂]` マーカー参照)。

---

## 6. まとめ

- 取得系は所有者スコープ。他ユーザーの問題・解は 404。
- `GET /algorithms` は registry を集約して返す ── Phase 3 のベンチマーク UI の入口。
- ルーター集約(`app/api/routes/__init__.py`)に solve / algorithms / solutions の 3 本を追加。
- Phase 2 は「Validation / Verification の枠を埋める」7 単位(上表)。

これで Phase 1 は完了。`Phase-1-introduction.md` の「次のフェーズ」を確認し、「Phase 2 を開始する」で
Phase 2 教材を生成する。
