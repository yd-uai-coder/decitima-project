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

**この章で作成 / 更新するファイル**: `app/services/optimization_read.py`、
`app/api/routes/algorithms.py`、`app/api/routes/solutions.py`。取得系のレスポンススキーマ
(`AlgorithmInfo` / `AlgorithmListResponse` / `SolutionRead` / `ProblemRead`)は
`app/schemas/optimization.py`([Phase-1-6](./Phase-1-6.md) §5 で新規作成済みのファイル)に足す。
**既存ファイルへの追記**: `app/api/routes/__init__.py`(§3 ── `algorithms` / `solutions` の 2 本。
`solve` は [Phase-1-6](./Phase-1-6.md) §5 で追加済み)。

対応サンプル: `textbook/samples/app/services/optimization_read.py`,
`textbook/samples/app/api/routes/{algorithms,solutions}.py`, `textbook/samples/app/schemas/optimization.py`。
テストは `textbook/samples/tests/api/test_algorithms_solutions_api.py`。設計は `Phase-0-7.md` §2。

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
# chat_router は Phase 11 まで無効のまま(既存の方針)
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
**Phase 2 開始時に 6 単位に確定した**(当初この表は 7 単位。`verifications` テーブルを落とした
理由は下記)。詳細は各 `Phase-2-M.md` と `Phase-2-introduction.md` §10。

| # | Phase 2 の作業単位 | 内容 |
| --- | --- | --- |
| 2-1 | Input Validation の拡充(Pydantic) | `ShiftSlot` の `end_hour > start_hour` の `model_validator` / `day` の ISO 日付 `field_validator` / `ShiftData` の id 重複を弾く `model_validator` |
| 2-2 | Semantic Validation の一般化 | route・shift の検査関数を `app/domain/problems/semantic.py` の `SEMANTIC_CHECKS` レジストリに集約。`validation.py` はそれを回すだけ(到達可能性のみ services に残置) |
| 2-3 | Constraint Checker 全実装 + `domain/constraints/` | `forbidden` / `required_inclusion`(移設)/ `numeric_bound` / `staffing` を kind ごと 1 ファイル + `CHECKERS` レジストリ。構造検証を `domain/solutions/structure.py` へ。`verification.py` はオーケストレーションに縮小 |
| 2-4 | Verification(shift) | `verify_shift_structure` ── 人数 / 可用性 / スキル / 週勤務時間 / 連続勤務日数(hard)、希望休(soft)、`labor_cost` ・ `day_off_satisfaction`(metrics)。手組み `ShiftSolution` fixture で検証 |
| 2-5 | `POST /api/v1/verify` | 問題 + 解を渡して検証だけ実行(`VerifyRequest` / `VerifyResponse` は `Phase-0-7.md` §3.2) |
| 2-6 | Invalid Solution Handling | `status="invalid"` の解が solve / verify を 200 で通る導線、`Solution.status` カラムへの保存(スキーマ変更なし)、UI への伝え方の方針 |

**旧 2-7「`verifications` テーブル」は作らない**: 検証結果は `Solution.status` カラム +
`Solution.payload` に既に入り、MVP に payload 内クエリ需要は無い(`Phase-0-8.md` §4、
`CLAUDE.md` Notes Q12)。`benchmark_runs`(Phase 3)を作るとき、または実際にそのクエリ需要が
出たときに切り出す。

多目的の重み付き和の評価器(`app/domain/objectives/`)は Phase 1 では作らない。初の多目的
ストラテジー(Phase 6 の Shift Scheduler)を実装するときに追加する
(`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の 「以降 Phase で修正予定」マーカー参照)。

---

## 6. まとめ

- 取得系は所有者スコープ。他ユーザーの問題・解は 404。
- `GET /algorithms` は registry を集約して返す ── Phase 3 のベンチマーク UI の入口。
- ルーター集約(`app/api/routes/__init__.py`)に solve / algorithms / solutions の 3 本を追加。
- Phase 2 は「Validation / Verification の枠を埋める」7 単位(上表)。

これで Phase 1 は完了。`Phase-1-introduction.md` の「次のフェーズ」を確認し、「Phase 2 を開始する」で
Phase 2 教材を生成する。
