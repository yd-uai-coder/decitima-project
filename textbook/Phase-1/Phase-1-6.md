# Phase 1-6: solve API ── Validation・Verification・SolveService(作業単位 1-6)

## この章のゴール

Phase 1 の計算部品(スキーマ / registry / Dijkstra / 永続化)を `POST /api/v1/solve` の
1 本のパイプラインに束ねる。

- `ProblemValidationService`(route 限定の最小 Semantic Validation)
- `SolutionVerificationService`(route 限定の最小 Verification)
- `SolveService`(ライフサイクル、タイムアウト)
- `SolveRequest` / `SolveResponse`(`app/schemas/optimization.py`)、`app/api/routes/solve.py`
- `settings` への追記

**この章で作成 / 更新するファイル**: `app/services/validation.py`、`app/services/verification.py`、
`app/services/solve.py`、`app/schemas/optimization.py`(§5 の solve 部分。取得系スキーマは
[Phase-1-7](./Phase-1-7.md))、`app/api/routes/solve.py`、`tests/api/conftest.py`(§6 の `api` フィクスチャ)。
**既存ファイルへの追記**: `app/core/config.py`(§1)、`app/api/routes/__init__.py`(§5 ── `solve_router` の集約。
`algorithms` / `solutions` は [Phase-1-7](./Phase-1-7.md) §3)。

対応サンプル: `textbook/samples/app/services/{validation,verification,solve}.py`,
`textbook/samples/app/schemas/optimization.py`, `textbook/samples/app/api/routes/solve.py`,
`textbook/samples/tests/api/conftest.py`。
テストは `textbook/samples/tests/unit/test_{validation,verification,solve}_service.py`、
`textbook/samples/tests/api/test_solve_api.py`。設計は `Phase-0-6.md`(V&V)/ `Phase-0-7.md`(API)。

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
`NoAlgorithmError` / `SolveTimeoutError`)は [Phase-1-2](./Phase-1-2.md) §4 で足した(これも既存ファイルへの追記)。

---

## 2. ProblemValidationService(route 限定・最小)

`Phase-0-6.md` §2。Input Validation(型・値域)は Pydantic の `Field` が既に担う。
ここは **Semantic Validation** ── 問題全体を見ないと分からない検査。

```python
# app/services/validation.py
class ProblemValidationService:
    def validate(self, problem: OptimizationProblem) -> None:
        # まず、RouteDataのフィールドが揃っているかをチェック -> _validate_routeを通す
        # Phase 2-2で差し替えとなる。
        if isinstance(problem.data, RouteData):
            self._validate_route(problem, problem.data)
        # shift_scheduling は Phase 2/6。それまでは素通し(グレーは通す)
        
    # Phase 2-2で差し替えとなる。※一部機能を関数化して分離。
    def _validate_route(self, problem, data: RouteData) -> None:
        # ここから if errors: の行までが Phase 2-2で関数化されて分離する->validate関数から呼び出される。
        node_ids = {n.id for n in data.nodes}
        errors = []
        if data.start not in node_ids:  errors.append(...)          # start が nodes に存在
        if data.goal not in node_ids:   errors.append(...)          # goal が nodes に存在
        for edge in data.edges:                                     # エッジ端点が nodes に存在
            ...
        if errors:  raise ProblemValidationError("; ".join(errors))

        forbidden = {禁止エッジ id}
        adjacency = build_adjacency(data, forbidden)                # ← Phase-1-4 の関数を再利用
        plain = {node: [nxt for nxt, _e, _w in edges] ...}
        if data.goal not in reachable_nodes(plain, data.start):     # ← Phase-1-3 の BFS
            raise InfeasibleProblemError("goal ... is unreachable ...")
```

- 整合性の欠陥(未知ノード参照など)→ `ProblemValidationError`(400)
- 「明らかに無理」(禁止エッジ除去後に到達不能)→ `InfeasibleProblemError`(400)。
  アルゴリズムを走らせない ── 走らせても `infeasible` が返るだけ(`Phase-0-6.md` §2.4)。
- **原則**: 「明らかに無理」だけ弾き、グレーゾーンは通す。

> **[以降 Phase で修正予定 ── Phase 2-2]** この節の実装は samples のとおり
> (`isinstance(problem.data, RouteData)` のハードコード分岐、shift は素通し)で進める。
> Phase 2-2 での変更: 当初〈上記〉→ 現在〈純粋述語の検査関数を
> `app/domain/problems/semantic.py` の `SEMANTIC_CHECKS` レジストリに集約。到達可能性は
> 「計算」なので `route_reachable`(`app/algorithms/graph/reachability.py`)に起こし、
> `validate` はレジストリを回す + `route_reachable` を呼んで判定する。shift も検証〉。
> 理由(解決される問題)〈shift の未検証、problem_type 追加のたびにサービスを改修する必要、
> 到達可能性の計算がサービスにインラインされていた〉。詳細 `Phase-2-2.md`。

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

> **[以降 Phase で修正予定 ── Phase 2-3 / 2-4]** この節の実装は samples のとおり
> (チェッカー関数と `_CHECKERS` dict、`_verify_route_structure` を全部このファイルにインライン、
> route 限定)で進める。Phase 2-3 / 2-4 での変更: 当初〈上記〉→ 現在〈kind ごとのチェッカーを
> `app/domain/constraints/`(`CHECKERS` レジストリ)、構造検証を
> `app/domain/solutions/structure.py`(route + shift)へ移設。`verify` は「構造検証 →
> metrics enrich → `CHECKERS` ディスパッチ → hard/soft 集計」のオーケストレーションに縮小〉。
> 理由(解決される問題)〈shift 解の未検証、`numeric_bound` / `staffing` の未対応、制約 kind を
> 足すたびにサービスを触る必要〉。詳細 `Phase-2-3.md` / `Phase-2-4.md`。

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

> @dataclass(frozen=True)
> データを保持するクラスを簡潔に定義しつつ、インスタンス生成後の属性変更を禁止する。(frozen:インスタンス生成後の再代入の禁止)

- **タイムアウト**: 同期・純粋な `solve` を `asyncio.to_thread` に逃がし `wait_for` で監視。
  超過で `SolveTimeoutError`(504)。ただしスレッド自体は止められない(MVP の割り切り。
  `Phase-0-5.md` §5)。
- **`commit` はこのサービスだけ**。リポジトリは `flush` のみ。
- 例外はここで握らず伝播(`register_error_handlers` が JSON 化)。

---

## 5. スキーマと solve ルート

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
# 取得系のスキーマ(AlgorithmInfo / AlgorithmListResponse / SolutionRead / ProblemRead)は
# 同じファイルにあるが解説は Phase-1-7 §1。
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

**`solve` ルーターを集約に足す**(既存 `app/api/routes/__init__.py` への追記。進行ルール #15 ──
この章の `test_solve_api.py` がルートの登録に依存するため、1-6 で足す):

```python
# app/api/routes/__init__.py
from app.api.routes.solve import router as solve_router   # ← 追加
# ...
api_router.include_router(solve_router)                    # ← 追加
```

`algorithms` / `solutions` ルーターの集約は [Phase-1-7](./Phase-1-7.md) §3(それぞれの章で
作るルートを、その章で集約に足す)。

---

## 6. テスト観点

> **テスト対象 / ドライバ / スタブ**(進行ルール #14):
> 
> - **対象**: `ProblemValidationService` / `SolutionVerificationService`(純粋寄り)、
>   `SolveService`(オーケストレーション + トランザクション境界)、`solve` ルート
> - **ドライバ**: サービス層テストはテスト関数、API テストは `httpx.AsyncClient`
> - **スタブ / テストダブル**: サービス層 = `db_session`(SQLite)+ `FakeRedis`
>   (RateLimiter が呼ぶ Redis の代役)。API = FastAPI 依存差し替え
>   (`get_db` → SQLite、`get_redis` → `FakeRedis`)。**`strategy.solve` は本物を使う**
>   (純粋なのでスタブ不要)。

| ファイル                           | 観点                                                                                                                                                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_validation_service.py`   | 正常系通過 / 未知ノードで `ProblemValidationError` / 到達不能で `InfeasibleProblemError` / shift は素通し                                                                                                                                   |
| `test_verification_service.py` | 違反ゼロで `valid` / 禁止エッジ使用で `invalid` / 必須ノード欠落で `invalid` / `total_weight` 不整合で `invalid` / 元の解を書き換えない / `infeasible` は素通し                                                                                                |
| `test_solve_service.py`        | 永続化されて `problem_id`/`solution_id` が返る / `problem_ref` = `problem_id` / `persist=false` で id は None / 到達不能で `InfeasibleProblemError` / 未対応 problem_type で `NoAlgorithmError` / `timeout_seconds` 極小で `SolveTimeoutError` |
| `test_solve_api.py`            | Route 問題で `status="valid"` の検証済み解(A→B→C→E, weight 9)/ `persist=false` で id は null / 未対応 problem_type で 400 / 到達不能で 400 / 認証なしで 401                                                                                      |

API テストは `httpx.AsyncClient` + 依存差し替え(`get_db` → インメモリ SQLite、`get_redis` →
`FakeRedis`)+ `create_access_token` で JWT 発行。実 PG / Redis 不要。この `api` フィクスチャは
**この章で `tests/api/conftest.py` を新規作成**する(`textbook/samples/tests/api/conftest.py`。進行ルール #15 ──
フィクスチャは初出の章の作成物)。

---

## 7. まとめ

- `SolveService.solve` = レート制限 → Validation → `select_strategy` → 計算(タイムアウト監視)→
  Verification → 永続化 → commit。例外はハンドラ任せ。
- Phase 1 の Validation / Verification は **route_planning 限定の最小実装**。
  kind ごとの Checker の枠(`_CHECKERS`)は置くが中身は `forbidden` / `required_inclusion` だけ。
- ルートは薄い。API テストは依存差し替えで実 PG / Redis 不要。
- `settings` の 3 行と errors の 4 クラスは既存ファイルへの追記(samples に含めない)。

次章([Phase-1-7](./Phase-1-7.md))では、作業単位 1-7 ── 取得系(`GET /algorithms` /
`GET /solutions/{id}` ほか)とルーター集約、そして Phase 2 への引き継ぎをまとめる。
