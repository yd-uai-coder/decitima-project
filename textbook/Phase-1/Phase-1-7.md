# Phase 1-7: solve API・取得系・Phase 2 への引き継ぎ(作業単位 1-6 / 1-7)

## この章のゴール

Phase 1 の全部品を `POST /api/v1/solve` の 1 本のパイプラインに束ね、取得系を足す。

- `SolveService`(ライフサイクル、タイムアウト)
- **route 限定の最小** `ProblemValidationService` / `SolutionVerificationService`
- `app/schemas/optimization.py`、`app/api/routes/{solve,algorithms,solutions}.py`
- `settings` への追加、既存ルーター集約への配線
- Phase 2 に送る作業の分割表

対応サンプル: `samples/app/services/{validation,verification,solve,optimization_read}.py`,
`samples/app/schemas/optimization.py`,
`samples/app/api/routes/{solve,algorithms,solutions}.py`。
テストは `samples/tests/unit/test_{validation,verification,solve}_service.py`、
`samples/tests/api/*`。`app/core/config.py` / `app/api/routes/__init__.py` は既存ファイルへの
追記(§1 / §5.2)で samples には含めない。設計は `Phase-0-7.md`(API)/ `Phase-0-6.md`(V&V)。

---

## 1. `settings` と errors の追加(既存ファイルへの追記)

`app/core/config.py` は既存。samples には入れず、`Settings` の Rate limit セクションに 3 行足す:

```python
# app/core/config.py の class Settings 内、CHAT_RATE_LIMIT_* の下に
SOLVE_RATE_LIMIT_PER_HOUR: int = 20
SOLVE_RATE_LIMIT_PER_DAY: int = 100
SOLVE_TIMEOUT_SECONDS: float = 10.0
```

`app/services/errors.py` の 4 クラス(`ProblemValidationError` / `InfeasibleProblemError` /
`NoAlgorithmError` / `SolveTimeoutError`)は [Phase-1-3](./Phase-1-3.md) §4 で足した(これも既存ファイルへの追記)。

---

## 2. ProblemValidationService(route 限定・最小)

`Phase-0-6.md` §2。Input Validation(型・値域)は Pydantic の `Field` が既に担う。
ここは **Semantic Validation** ── 問題全体を見ないと分からない検査。

```python
# app/services/validation.py
class ProblemValidationService:
    def validate(self, problem: OptimizationProblem) -> None:
        if isinstance(problem.data, RouteData):
            self._validate_route(problem, problem.data)
        # shift_scheduling は Phase 2/5。それまでは素通し(グレーは通す)

    def _validate_route(self, problem, data: RouteData) -> None:
        node_ids = {n.id for n in data.nodes}
        errors = []
        if data.start not in node_ids:  errors.append(...)          # start が nodes に存在
        if data.goal not in node_ids:   errors.append(...)          # goal が nodes に存在
        for edge in data.edges:                                     # エッジ端点が nodes に存在
            ...
        if errors:  raise ProblemValidationError("; ".join(errors))

        forbidden = {禁止エッジ id}
        adjacency = build_adjacency(data, forbidden)                # ← Phase-1-5 の関数を再利用
        plain = {node: [nxt for nxt, _e, _w in edges] ...}
        if data.goal not in reachable_nodes(plain, data.start):     # ← Phase-1-4 の BFS
            raise InfeasibleProblemError("goal ... is unreachable ...")
```

- 整合性の欠陥(未知ノード参照など)→ `ProblemValidationError`(400)
- 「明らかに無理」(禁止エッジ除去後に到達不能)→ `InfeasibleProblemError`(400)。
  アルゴリズムを走らせない ── 走らせても `infeasible` が返るだけ(`Phase-0-6.md` §2.4)。
- **原則**: 「明らかに無理」だけ弾き、グレーゾーンは通す。

---

## 3. SolutionVerificationService(route 限定・最小)

`Phase-0-6.md` §3。

```python
# app/services/verification.py
class SolutionVerificationService:
    def verify(self, problem, solution: CandidateSolution) -> CandidateSolution:
        if solution.status == "infeasible":  return solution        # 解が無いものは検証しない
        violations = []
        # route 解の構造チェック(制約 kind に紐づかない、常に必要)
        if isinstance(solution.assignments, RouteSolution) and isinstance(problem.data, RouteData):
            violations += _verify_route_structure(problem.data, solution.assignments)
        # kind ごとのチェッカーにディスパッチ(枠は用意、中身は route の 2 つだけ)
        for c in problem.constraints:
            checker = _CHECKERS.get(c.kind)
            if checker: ...
        has_hard = any(v.severity == "hard" for v in violations)
        return solution.model_copy(update={
            "status": "invalid" if has_hard else solution.status,
            "violations": violations,
            "metrics": {**solution.metrics, "soft_penalty": _soft_penalty(problem, violations)},
        })

_CHECKERS = {
    "forbidden": _check_forbidden,                # 禁止エッジを使っていないか
    "required_inclusion": _check_required_inclusion,   # 必須ノードを通っているか
    # "numeric_bound" / "staffing" などは Phase 2
}
```

route 構造チェック(`_verify_route_structure`)= 経路連結 / start・goal / `path_edge_ids` 長さ /
各エッジが隣接ノード対を結ぶ / `total_weight` = エッジ weight 合計。すべて hard。

- **hard 違反 1 件でも → `status="invalid"`**。soft 違反 → `soft_penalty` を metrics に加算。
- **解は書き換えない** ── `model_copy(update=...)` で新インスタンスを返す。生の解も残る(監査用)。
- 未対応 kind は素通し(Phase 2 で埋める)。

---

## 4. SolveService ── ライフサイクル

```python
# app/services/solve.py
@dataclass(frozen=True)
class SolveOutcome:
    solution: CandidateSolution
    problem_id: uuid.UUID | None
    solution_id: uuid.UUID | None

class SolveService:
    def __init__(self, session, redis):
        self._problems = ProblemRepository(session)
        self._solutions = SolutionRepository(session)
        self._validation = ProblemValidationService()
        self._verification = SolutionVerificationService()
        self._rate_limiter = RateLimiter(redis, resource="solve", limits=[
            RateLimit(3600, settings.SOLVE_RATE_LIMIT_PER_HOUR),
            RateLimit(86400, settings.SOLVE_RATE_LIMIT_PER_DAY),
        ])

    async def solve(self, *, user_id, request: SolveRequest, bypass_rate_limit=False) -> SolveOutcome:
        problem = request.problem
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))          # (a)
        self._validation.validate(problem)                          # (b)
        strategy = select_strategy(problem, request.algorithm)      # (c)
        timeout = request.timeout_seconds or settings.SOLVE_TIMEOUT_SECONDS
        try:                                                        # (d) 純粋計算 + タイムアウト監視
            raw = await asyncio.wait_for(asyncio.to_thread(strategy.solve, problem), timeout)
        except TimeoutError as exc:
            raise SolveTimeoutError(f"solve exceeded {timeout}s") from exc
        verified = self._verification.verify(problem, raw)          # (e)
        if not request.persist:                                     # (f)
            return SolveOutcome(verified, None, None)
        problem_row = await self._problems.create(...)
        verified = verified.model_copy(update={"problem_ref": problem_row.id})
        solution_row = await self._solutions.create(...)
        await self._session.commit()                                # (g)
        return SolveOutcome(verified, problem_row.id, solution_row.id)
```

- **タイムアウト**: 同期・純粋な `solve` を `asyncio.to_thread` に逃がし `wait_for` で監視。
  超過で `SolveTimeoutError`(504)。ただしスレッド自体は止められない(MVP の割り切り。
  `Phase-0-5.md` §5)。
- **`commit` はこのサービスだけ**。リポジトリは `flush` のみ。
- 例外はここで握らず伝播(`register_error_handlers` が JSON 化)。

---

## 5. スキーマとルート

```python
# app/schemas/optimization.py
class SolveRequest(BaseModel):
    problem: OptimizationProblem
    algorithm: str | None = None
    persist: bool = True
    timeout_seconds: float | None = Field(default=None, gt=0)

class SolveResponse(BaseModel):
    solution: CandidateSolution
    problem_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
# + AlgorithmInfo / AlgorithmListResponse / SolutionRead / ProblemRead
```

```python
# app/api/routes/solve.py
router = APIRouter(prefix="/solve", tags=["solve"])

@router.post("", response_model=SolveResponse)
async def solve(payload: SolveRequest, session: SessionDep, redis: RedisDep,
                current_user: CurrentUserDep) -> SolveResponse:
    outcome = await SolveService(session, redis).solve(
        user_id=current_user.id, request=payload,
        bypass_rate_limit=current_user.is_superuser,
    )
    return SolveResponse(solution=outcome.solution, problem_id=outcome.problem_id,
                         solution_id=outcome.solution_id)
```

ルートはこれだけ。バリデーション NG・タイムアウト・アルゴリズム未登録は
`SolveService` 内で `AppError` 派生が飛び、既存ハンドラが JSON 化する。

### 5.1 取得系(作業単位 1-7)

```python
# app/services/optimization_read.py ── 所有者スコープ(他ユーザーのものは NotFoundError → 404)
class OptimizationReadService:
    async def get_problem(self, problem_id, *, user_id) -> Problem: ...
    async def get_solution(self, solution_id, *, user_id) -> Solution:   # solutions⨝problems で所有者確認
    async def list_solutions_for_problem(self, problem_id, *, user_id) -> list[Solution]: ...
```

```python
# app/api/routes/algorithms.py    GET /api/v1/algorithms
#   registry の all_strategies() を (name, implementation) で集約し problem_types を付けて返す
# app/api/routes/solutions.py     GET /api/v1/solutions/{id}
#                                 GET /api/v1/problems/{id}
#                                 GET /api/v1/problems/{id}/solutions
```

### 5.2 ルーター集約(既存ファイルへの追記)

`app/api/routes/__init__.py` は既存。samples には入れず、import と `include_router` を足す:

```python
# app/api/routes/__init__.py
from app.api.routes.algorithms import router as algorithms_router  # ← 追加
from app.api.routes.auth import router as auth_router
from app.api.routes.solutions import router as solutions_router    # ← 追加
from app.api.routes.solve import router as solve_router            # ← 追加
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(solve_router)        # ← 追加
api_router.include_router(algorithms_router)   # ← 追加
api_router.include_router(solutions_router)    # ← 追加
# chat_router は Phase 10 まで無効のまま(既存の方針)
```

---

## 6. テスト観点

| ファイル | 観点 |
| --- | --- |
| `test_validation_service.py` | 正常系通過 / 未知ノードで `ProblemValidationError` / 到達不能で `InfeasibleProblemError` / shift は素通し |
| `test_verification_service.py` | 違反ゼロで `valid` / 禁止エッジ使用で `invalid` / 必須ノード欠落で `invalid` / `total_weight` 不整合で `invalid` / 元の解を書き換えない / `infeasible` は素通し |
| `test_solve_service.py` | 永続化されて `problem_id`/`solution_id` が返る / `problem_ref` = `problem_id` / `persist=false` で id は None / 到達不能で `InfeasibleProblemError` / 未対応 problem_type で `NoAlgorithmError` / `timeout_seconds` 極小で `SolveTimeoutError` |
| `test_solve_api.py` | Route 問題で `status="valid"` の検証済み解(A→B→C→E, weight 9)/ `persist=false` で id は null / 未対応 problem_type で 400 / 到達不能で 400 / 認証なしで 401 |
| `test_algorithms_solutions_api.py` | `GET /algorithms` に `dijkstra`(family/implementation/problem_types)/ solve → `GET /solutions/{id}` / `GET /problems/{id}/solutions` / 未知 id で 404 |

API テストは `httpx.AsyncClient` + 依存差し替え(`get_db` → インメモリ SQLite、`get_redis` →
`FakeRedis`)+ `create_access_token` で JWT 発行。実 PG / Redis 不要(`samples/tests/api/conftest.py`)。

---

## 7. Phase 2 への引き継ぎ

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
ストラテジー(Phase 5 の Shift Scheduler)を実装するときに追加する。

---

## 8. まとめ

- `SolveService.solve` = レート制限 → Validation → `select_strategy` → 計算(タイムアウト監視)→
  Verification → 永続化 → commit。例外はハンドラ任せ。
- Phase 1 の Validation / Verification は **route_planning 限定の最小実装**。
  kind ごとの Checker の枠(`_CHECKERS`)は置くが中身は `forbidden` / `required_inclusion` だけ。
- ルートは薄い。API テストは依存差し替えで実 PG / Redis 不要。
- Phase 2 は「枠を埋める」7 単位(上表)。

これで Phase 1 は完了。`phase-1-index.md` の「Phase 2 実装前チェックリスト」で、
Phase 2 着手前の疑問を出し切る。
