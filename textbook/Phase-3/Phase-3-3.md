# Phase 3-3: BenchmarkService + POST /benchmark + benchmark_runs 永続化(作業単位 3-3)

## この章のゴール

Phase 3 の本体。1 問題を registry の全アルゴリズムで解いて実測を横並びにする
`BenchmarkService` と `POST /api/v1/benchmark`、そして結果を保存する `benchmark_runs`
テーブルを作る。**Phase 1 以来の初めての ORM 作業**(モデル + マイグレーション + リポジトリ)。

**この章で新規作成するファイル**:
`app/services/benchmark.py`、`app/api/routes/benchmark.py`、
`alembic/versions/d4f1a9c2b8e7_add_benchmark_runs_table.py`。
**既存ファイルへの変更**:
`app/models/optimization.py`(`BenchmarkRun` を追加。現行版は samples)、
`app/repositories/optimization.py`(`BenchmarkRunRepository` を追加。現行版は samples ── §2.2)、
`app/services/optimization_read.py`(`get_benchmark_run`。現行版は samples ── GET は 3-4)、
`app/schemas/optimization.py`(3-1 で追記済み)、
追記のみ: `app/core/config.py` / `app/api/routes/__init__.py` / `app/models/__init__.py` /
`alembic/env.py` / `app/algorithms/registry.py`(3-2 で追記済み)。

対応サンプル: `samples/app/services/benchmark.py`、`samples/app/api/routes/benchmark.py`、
`samples/app/repositories/optimization.py`、`samples/app/models/optimization.py`、
`samples/alembic/versions/d4f1a9c2b8e7_add_benchmark_runs_table.py`。
テストは `samples/tests/unit/test_benchmark_service.py`、`test_benchmark_repository.py`、
`samples/tests/api/test_benchmark_api.py`、`samples/tests/integration/test_benchmark_persistence.py`。
設計は `Phase-0-5.md` §4、`Phase-0-7.md` §3.4、`Phase-0-8.md` §2。

---

## 1. `BenchmarkService`

`SolveService` と同じ「ユースケース + トランザクション境界」。ライフサイクルは
`Phase-3-introduction.md` §2 の図のとおり。

```python
# app/services/benchmark.py(要点。全文は samples)
class BenchmarkService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._runs_repo = BenchmarkRunRepository(session)
        self._validation = ProblemValidationService()
        self._verification = SolutionVerificationService()
        self._rate_limiter = RateLimiter(redis, resource="benchmark", limits=[...])

    async def run(self, *, user_id, request: BenchmarkRequest, bypass_rate_limit=False) -> BenchmarkOutcome:
        # (a) レート制限
        # (b) self._validation.validate(problem)          ← 実際に解くので Validation を通す
        # (c) strategies = get_strategies(problem.problem_type)
        #     request.algorithms があれば meta.name でフィルタ。空 → NoAlgorithmError
        # (d) for strategy in strategies:
        #         solution, measurement = await asyncio.wait_for(
        #             asyncio.to_thread(measure_call, partial(strategy.solve, problem), request.runs),
        #             timeout)                            ← 1 run あたり timeout
        # (e)     verified = self._verification.verify(problem, solution)  ← 計測の外
        #         hard/soft = 違反件数
        #         entries.append(BenchmarkEntry(...))
        # (f) _annotate_quality_ratio(problem, entries)   ← 3-4 で解説
        # (g) if request.persist: benchmark_runs に 1 行、await self._session.commit()
        return BenchmarkOutcome(entries=entries, benchmark_id=...)
```

判断のポイント:

- **`BenchmarkService(session, redis)`** ── benchmark はトランザクション境界なので、
  `SolveService` と同じく `session` を受け取る(`VerifyService` は DB を触らないので `redis` だけ、
  という対比)。
- **Validation を通す** ── verify との決定的な違い。「解けない問題」を測るのは無意味なので、
  `SolveService` (b) と同じく最初に弾く。
- **タイムアウトは 1 run あたり** ── `measure_call` の中で `runs` 回まわる全体を
  `asyncio.wait_for` で監視する(`SolveService` と同じく `to_thread` にスレッド退避)。
  `functools.partial(strategy.solve, problem)` で引数を固定。
- **Verification は計測の外**でかける ── 検証時間はアルゴリズムの性能ではない。結果の
  `verified.status` / `verified.violations` から `solution_status` / `hard_violations` /
  `soft_violations` を entry に載せる。
- `operation_count` は `solution.metrics.get("_ops")` を `int` に(数えていなければ `None`)。

---

## 2. `benchmark_runs` テーブル(ORM の追記)

```python
# app/models/optimization.py に追加(全文は samples)
class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)   # {problem, entries, runs}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- **JSONB 中心 + 検索キーだけカラム化**(`Phase-0-8.md` §3)。カラムは `user_id` /
  `problem_type` / `created_at`(「自分の過去のベンチ実行」を引くのに要る 3 つ)。実測値本体は
  すべて `payload`。
- **`Problem` への FK を張らない** ── benchmark は「N 回 solve して保存」ではなく、
  **独立した測定記録**。`payload["problem"]` に問題ごと入れて自己完結させる。
  `GET /problems/{id}/solutions`(複数アルゴリズム分)の話とは別系統(Phase 3 では拡張しない)。
- `JsonB = JSON().with_variant(JSONB(), "postgresql")` は Phase 1 と同じ ── SQLite テストでは
  汎用 JSON にフォールバック。

### 2.1 マイグレーション

```python
# alembic/versions/d4f1a9c2b8e7_add_benchmark_runs_table.py(全文は samples)
revision = "d4f1a9c2b8e7"
down_revision = "c65b3aa7b03f"       # ← Phase 1 の add_problems_and_solutions の次
# op.create_table("benchmark_runs", ...) + user_id / problem_type の index
```

- 手順(`Phase-0-8.md` §6.1): `app/models/__init__.py` と `alembic/env.py` の**両方**に
  `BenchmarkRun` を登録してから `uv run alembic revision --autogenerate`。samples の
  マイグレーションはその生成物を整形したもの ── 写経後 `uv run alembic upgrade head` で
  `benchmark_runs` が生える(SQLite / Postgres 双方確認済み)。

### 2.2 リポジトリ ── `repositories/optimization.py` に同居させる

```python
# app/repositories/optimization.py に追記(全文は samples ── ProblemRepository / SolutionRepository と同じファイル)
class BenchmarkRunRepository(CRUDRepository[BenchmarkRun]):
    model = BenchmarkRun
    async def create(self, *, user_id, problem_type, payload) -> BenchmarkRun:
        row = BenchmarkRun(user_id=user_id, problem_type=problem_type, payload=payload)
        self._session.add(row); await self._session.flush(); return row
```

`get_by_id` は基底 `CRUDRepository` が提供。`flush` のみ(`commit` は `BenchmarkService`)──
Phase 1 の `ProblemRepository` / `SolutionRepository` と同型なので、**同じ
`repositories/optimization.py` に足す**(新規ファイルにしない ── 理由は §2.3)。

### 2.3 レイヤー分割の粒度 ── 「永続化の関心事」 vs 「操作」

benchmark は `models` / `schemas` / `repositories` では `optimization.py` に**同居**し、
`api/routes` / `services` では `benchmark.py` に**分ける**。この非対称は意図的:

| 層 | 分割の軸 | benchmark |
| --- | --- | --- |
| models / schemas / repositories | **永続化の関心事**(≒ どのテーブル群か) | `optimization.py`(`Problem` / `Solution` / `BenchmarkRun` は同じ「最適化レコード」。全部 JSONB payload + 検索キーカラム、`Phase-0-8.md` §3) |
| api/routes / services | **操作**(エンドポイント群 / ユースケース) | `benchmark.py`(`solve.py` / `verify.py` / `solutions.py` / `algorithms.py` と同じ粒度) |

- **なぜ data 層はまとめるか** ── `BenchmarkRun` は 18 行、`BenchmarkRunRepository` は 8 行。
  別ファイルにすると import ボイラープレートが中身と同じ行数になり、`models/__init__.py` /
  `alembic/env.py` の登録リストも伸びる。CL 開発の分割基準(`Phase-0-2.md` §2.5「**変更理由と
  消費者が別なら分割**」)で見ても、`BenchmarkRun` は `Problem` / `Solution` と同じ永続化理由で
  変わり、消費者(`OptimizationReadService`)も重なる → 同居が正。
- **格納先はファイル名でなく import で辿る** ── `models/__init__.py` が全 re-export するので
  `from app.models import BenchmarkRun` はどのファイルに書いても通る。「層をまたいで
  `benchmark.py` が並ぶ」ことにナビゲーション上の価値はほぼない(grep / go-to-definition /
  import 文で十分)。だからファイル名の対称性のために極小ファイルを量産しない。
- **この節が要る理由(記録)** ── 初版では `repositories/benchmark.py` を単独ファイルにしていた。
  実際の動機は「`repositories/optimization.py` を触ると samples の現行版再出荷 + 改訂マーカーが
  要る」という **samples 運用の都合**で、設計判断ではなかった。Phase 3 のレビューで
  `Phase-0-8.md` §5 の当初計画(全 repo を `optimization.py` に同居)へ是正した。

---

## 3. ルート(POST)

```python
# app/api/routes/benchmark.py(要点。GET は 3-4 で足す)
router = APIRouter(tags=["benchmark"])       # prefix なし(solutions.py と同じ流儀)

@router.post("/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(payload, session: SessionDep, redis: RedisDep, current_user: CurrentUserDep):
    outcome = await BenchmarkService(session, redis).run(
        user_id=current_user.id, request=payload, bypass_rate_limit=current_user.is_superuser)
    return BenchmarkResponse(entries=outcome.entries, benchmark_id=outcome.benchmark_id)
```

---

## 4. 既存への追記

```python
# app/core/config.py の class Settings 内(VERIFY の下)
    BENCHMARK_RATE_LIMIT_PER_HOUR: int = 10
    BENCHMARK_RATE_LIMIT_PER_DAY: int = 50
```

benchmark は solve を「アルゴリズム数 × runs 回」まわすので solve より重い。時間・日次の
両方に上限。per-run タイムアウトは `SOLVE_TIMEOUT_SECONDS` を再利用。

```python
# app/api/routes/__init__.py
from app.api.routes.benchmark import router as benchmark_router   # ← 追加
api_router.include_router(benchmark_router)                        # ← 追加
```

```python
# app/models/__init__.py
from app.models.optimization import BenchmarkRun, Problem, Solution
__all__ = ["BenchmarkRun", "Conversation", "Message", "Problem", "Solution", "User"]

# alembic/env.py
from app.models import BenchmarkRun, Conversation, Message, Problem, Solution, User  # noqa: F401
```

---

## 5. 既存への変更の当て方(写経手順)

1. `samples/app/schemas/optimization.py`(3-1 で写経済み ── `Benchmark*` を含む現行版)。
2. `samples/app/models/optimization.py` で上書き(`BenchmarkRun` が増えるだけ)。
3. `app/models/__init__.py` / `alembic/env.py` に `BenchmarkRun` を足す。
4. `samples/app/repositories/optimization.py` で上書き(`BenchmarkRunRepository` が増える)。
   `samples/app/services/benchmark.py`、`samples/app/api/routes/benchmark.py` を新規写経。
5. `samples/app/services/optimization_read.py` で上書き(`get_benchmark_run` が増える ──
   GET ルートは 3-4 で足すが、メソッドは現行版に含めておく)。
6. `app/core/config.py` に `BENCHMARK_*`、`app/api/routes/__init__.py` に `benchmark_router`。
7. `samples/alembic/versions/d4f1a9c2b8e7_...py` を新規写経 → `uv run alembic upgrade head`。
8. `samples/tests/**` の benchmark 系を新規写経 → `uv run pytest` → 緑。

---

## 6. テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - `test_benchmark_service.py`: **対象** = `BenchmarkService`。**ドライバ** = テスト関数 +
>   `db_session`。**スタブ** = `FakeRedis`(RateLimiter の Redis 役)のみ。Validation / Verification /
>   strategy / `measure_call` はすべて本物(純粋)。
> - `test_benchmark_repository.py`: **対象** = `BenchmarkRunRepository`。**ドライバ** = `db_session`。
>   **スタブ不要** ── インメモリ SQLite が実 Postgres の代役そのもの(Phase-1-5 と同型)。
> - `test_benchmark_api.py`: **対象** = ルート + サービス一式。**ドライバ** = `httpx.AsyncClient`。
>   **スタブ** = 依存差し替え(`get_redis` → `FakeRedis`、`get_db` → SQLite)。
> - `test_benchmark_persistence.py`(統合): 実 PostgreSQL。JSONB のラウンドトリップ確認。

| ファイル | ケース | 期待 |
| --- | --- | --- |
| service | 制約なし route | dijkstra + brute_force の 2 entry。各 entry に実測 + `hard/soft_violations == 0` |
| service | `algorithms=["dijkstra"]` | 1 entry |
| service | `algorithms=["nope"]` | `NoAlgorithmError` |
| service | `e_ce`・`e_de` 禁止(到達不能) | `InfeasibleProblemError`(計測前に弾く) |
| service | `start="Z"` | `ProblemValidationError` |
| service | `persist=True` / `False` | 行作成 + `benchmark_id` / `benchmark_id is None` |
| repo | create → get_by_id | payload が JSON ラウンドトリップ |
| api | `POST /benchmark` | 200 / entries 形状 / `benchmark_id` |
| api | 認証なし | 401 |
| api | `start="Z"` | 400 |
| 統合 | `BenchmarkRun` を実 PG に保存 → 取得 | `payload["runs"]` / `entries[0]` が一致 |

`uv run pytest tests/unit/test_benchmark_service.py tests/unit/test_benchmark_repository.py tests/api/test_benchmark_api.py` /
`uv run alembic upgrade head` / `uvx pyright app/services/benchmark.py app/api/routes/benchmark.py`。

---

## 7. まとめ

- `BenchmarkService` = レート制限 → Validation → strategy 解決 → 各 strategy を `measure_call` →
  Verification で違反数 → (3-4: quality_ratio)→ persist。
- `benchmark_runs` は JSONB payload 中心、検索キー(user_id / problem_type / created_at)だけ
  カラム化。`Problem` への FK は張らない(自己完結の測定記録)。
- Phase 1 の repository / migration パターンをそのまま再利用 ── `BenchmarkRunRepository` は
  `repositories/optimization.py` に同居(§2.3。data 層は「永続化の関心事」、route / service は「操作」で割る)。

次章([Phase-3-4](./Phase-3-4.md))では、作業単位 3-4 ── 入力サイズ別カーブと解の品質
(`quality_ratio`)、そして `GET /api/v1/benchmarks/{id}` を仕上げる。
