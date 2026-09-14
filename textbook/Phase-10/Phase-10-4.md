# Phase 10-4: ジョブキュー配線 + Phase 9 改訂(作業単位 10-4)

## この章のゴール

`run_simulation`(純粋なオーケストレーション)を、Phase 9-8 のジョブキュー(`arq` + Redis)経由で非同期実行できるように配線する。`POST /api/v1/simulate` を新設し、結果のポーリングは**既存の `GET /api/v1/jobs/{id}` をそのまま再利用する**。そのために Phase 9-8 の`JobStatusResponse.result` の型を広げる ── Phase 10 で唯一、以前の Phase のファイルに手を入れる章(進行のルール #12/#17)。

**この章で作成 / 更新するファイル**: `app/api/routes/simulate.py`(新規)。
既存への変更(現行版は samples): `app/schemas/job.py`、`app/services/job.py`、
`app/worker.py`、`app/api/routes/__init__.py`、`app/core/config.py`。

---

## 1. なぜ非同期実行か ── 実消費者は何か

Phase 3 `BenchmarkService` や Phase 1 `SolveService` はどちらも同期 API(`/benchmark` /`/solve`)で完結する。Simulation を非同期(ジョブキュー経由)にした理由は、進行のルール#17 の判定基準「今この Phase を駆動する実在の消費者は何か」に照らして明確に答えられる:
**1 リクエストで N シナリオ分の solve が走り、しかも各シナリオが CP-SAT / PuLP MILP /Branch and Bound のような重いアルゴリズムを踏む可能性がある**(base problem の
problem_type によって選ばれるアルゴリズムが変わる、Phase 6-9)。同期 `/solve` の
タイムアウト(既定 10 秒)は 1 回の solve を想定した値であり、N 倍になるシナリオ実行にはそもそも不向き。README 自身も Phase 9 で「ジョブキューを導入するとしたらここ」と示唆しており、Phase 10 がその最初の実消費者になる。

**既存の同期経路には一切触れない** ── `/solve` / `/benchmark` は無変更。Phase 9-8 が
既に確立した「ジョブキューは横断インフラとして並存する」という設計方針(`Phase-9-8.md`)をそのまま適用する。

---

## 2. Phase 9 への改訂 ── `JobStatusResponse.result` の型を広げる

Phase 9-8 時点の `JobStatusResponse.result` は `CandidateSolution | None` に固定されていた(「重い solve を 1 件だけ非同期化する」ためだけに設計されていたため)。simulate ジョブは結果として `SimulationResult`(`base`/`scenarios` を持つ)を返す必要があり、この型を広げないと収まらない。

```python
# app/schemas/job.py(改訂。全文は samples)
from app.schemas.simulation import SimulationResult  # (Phase 10-4)

type JobResult = CandidateSolution | SimulationResult  # (Phase 10-4)

class JobStatusResponse(BaseModel):
    ...
    # (Phase 9-8)
    # result: CandidateSolution | None = None
    # (Phase 10-4) simulate ジョブの結果も返せるように型を広げる
    result: JobResult | None = None
```

**discriminator タグを持たない素の union で済む理由**: `CandidateSolution` の必須フィールド(`status`/`assignments`/`metrics`/`violations`/`produced_by`)と `SimulationResult` の必須フィールド(`base`/`scenarios`)は 1 つも重ならない。Pydantic の smart union は、入力 dict がどちらの必須フィールド集合に一致するかで自動的に判別できる ── `kind: Literal[...]` のようなタグを新設する必要が無い。

**この改訂の効果は「型を広げる」だけ**で、`app/worker.py::solve_job` が
`payload["result"]` に書き込む内容(`CandidateSolution.model_dump(mode="json")` そのもの)は1 バイトも変えていない。したがって Phase 9-8 の既存テスト(`tests/integration/test_jobs_e2e.py::test_enqueue_reaches_redis_and_solve_job_processes_it`)
は**無改造で green のまま**(進行のルール #12.4 のスモークが最小コストで済む好例)。

> 検討した別案: `payload["result"]` に `{"kind": "solve", "solution": {...}}` のようなラッパーを導入する discriminated union。型としてはより厳密だが、`solve_job` の書き込み方**と** 既存 e2e テストのアサーション(`row.payload["result"]["status"]`)の両方を変える必要があり、Phase 9 への侵襲が大きい。必須フィールドが重ならないことを確認した上で、素の union のほうを採用した。

---

## 3. `JobService.enqueue_simulation`(投入側)

`JobService.enqueue`(Phase 9-8)と同型だが、レート制限を別枠にする:

```python
# app/services/job.py(要点)
async def enqueue_simulation(self, *, user_id, request: SimulationRequest, bypass_rate_limit=False) -> Job:
    if not bypass_rate_limit:
        await self._simulate_rate_limiter.enforce(str(user_id))   # resource="simulate_submit"

    self._validation.validate(request.problem)   # base problem だけ Validation

    job = await self._jobs.create(
        user_id=user_id, problem_type=request.problem.problem_type,
        payload={"request": request.model_dump(mode="json"), "result": None, "error": None},
    )
    await self._session.commit()

    pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        await pool.enqueue_job("simulate_job", str(job.id), _job_id=str(job.id))
    finally:
        await pool.aclose()
    return job
```

**別枠のレート制限**(`resource="simulate_submit"`、`app/core/config.py` に
`SIMULATE_SUBMIT_RATE_LIMIT_PER_{HOUR,DAY}` を追加)── Phase 3 が `benchmark` を `solve` と別枠にしたのと同じ理由(1 リクエストで複数 solve を回す、重い操作は軽い操作と競合させない)。

**base problem だけ Validation** する ── 各シナリオの override が有効かどうかは
override の内容次第で、投入時点では判断できない(そもそも override は無限に多様)。
「明らかに無理な base」だけを投入前に弾き、各シナリオの検証は実行時(`run_simulation`、10-1/10-2 で実装済み)に委ねる。**新テーブルは作らない** ── `Job` は Phase 9-8 の`jobs` テーブル(JSONB `payload`)をそのまま再利用する(進行のルール #17。実消費者無しの専用テーブルは見送り)。

---

## 4. `app/worker.py::simulate_job`(処理側)

```python
# app/worker.py(要点)
async def simulate_job(ctx, job_id: str) -> None:
    async with ctx["session_factory"]() as session:
        jobs = JobRepository(session)
        job = await jobs.get_by_id(uuid.UUID(job_id))
        if job is None:
            return
        await jobs.update_status(job.id, status="running")
        await session.commit()

        request = SimulationRequest.model_validate(job.payload["request"])
        try:
            result = await run_simulation(request)
        except Exception as exc:
            await jobs.update_status(job.id, status="failed", payload={**job.payload, "error": str(exc)})
            await session.commit()
            return

        await jobs.update_status(job.id, status="succeeded", payload={**job.payload, "result": result.model_dump(mode="json")})
        await session.commit()

class WorkerSettings:
    functions = [solve_job, simulate_job]   # (Phase 10-4) simulate_job を追加
    ...
```

`solve_job`(Phase 9-8)との違いは 1 点だけ ── `SolveService(session, redis).solve(...)` の代わりに `run_simulation(request)` を直接呼ぶ。`run_simulation` は session/redis に依存しない素の関数なので(Phase 10-2)、`SimulationService` のようなクラスをインスタンス化する手間が無い。ロジックの重複はゼロ(進行のルール #17)。

---

## 5. API ── 既存 `/jobs` の GET を再利用する `/simulate`

```python
# app/api/routes/simulate.py(新規。全文は samples)
POST /api/v1/simulate   -> 202 Accepted + {"job_id": ..., "status": "queued"}
```

**専用の GET は新設しない** ── `GET /api/v1/jobs/{id}`(Phase 9-8)が §2 で広げた
`JobStatusResponse.result` をそのまま返せるため、simulate ジョブも既存の 1 本のポーリングエンドポイントで足りる。`app/api/routes/__init__.py` に `simulate_router` を追加登録するだけ(`solve_router` / `jobs_router` には触れない)。

---

## まとめ

- Phase 10 で唯一、以前の Phase(9-8)のファイルに手を入れる章。改訂は
  「`JobStatusResponse.result` の型を広げる」の 1 点に絞られ、`solve_job` の実装・既存テストともに無改造。
- 新テーブル・新マイグレーションは無い ── `jobs` テーブルをそのまま再利用。
- ポーリング API も既存 `GET /jobs/{id}` を再利用 ── 新設したのは投入用の
  `POST /simulate` と `JobService.enqueue_simulation` / `simulate_job` だけ。

## テスト観点(`tests/unit/test_job_service.py`(追記)/ `tests/integration/test_jobs_e2e.py`(追記)/ `tests/api/test_simulate_api.py`(新規))

> **対象**: `JobService.enqueue_simulation`(unit)、`simulate_job`(状態遷移、integration)、`POST /api/v1/simulate` の契約(api)
> **ドライバ**: 各テスト関数。`db_session` フィクスチャ(unit)/ 実 Postgres + 実 Redis(integration、`-m integration`)/ `api` フィクスチャ(FakeRedis + インメモリ SQLite、api)
> **スタブ**: `enqueue_simulation` のユニットテストだけ、Phase 9-8 と同じ
> `FakeRedis` + フェイク arq プール(`arq.create_pool` を差し替え)が要る。`simulate_job`自体は `run_simulation` を直接呼ぶだけの純粋な処理なのでスタブ不要

| ケース                                              | 期待                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------- |
| `enqueue_simulation` が queued な Job を作りキューへ積む    | `status=="queued"`、フェイクプールに `("simulate_job", ...)` が記録される          |
| `enqueue_simulation` が infeasible な base を弾く     | `InfeasibleProblemError`、キューには積まれない                                 |
| `enqueue_simulation` のレート制限は `enqueue`(solve)と別枠 | solve を 1 件積んだ直後でも simulate の投入がブロックされない                            |
| (integration)`simulate_job` が succeeded まで処理する   | `payload["result"]["base"]["status"]`・`scenarios[0]["label"]` が期待通り |
| `POST /api/v1/simulate` → 202 + job_id           | 既存 `GET /api/v1/jobs/{id}` でポーリングでき `status=="queued"` が見える         |
| `POST /api/v1/simulate` が infeasible な base を弾く  | 400                                                                 |

**既存テストの回帰確認**(#12.4 のスモーク): `tests/integration/test_jobs_e2e.py::
test_enqueue_reaches_redis_and_solve_job_processes_it`(Phase 9-8)が**無改造で green のまま**であることを確認する ── `JobStatusResponse.result` の型を広げただけで `solve_job` の書き込み方も既存アサーションも変わっていないことの直接的な証拠になる。

`uv run pytest tests/unit/test_job_service.py tests/api/test_simulate_api.py` /
`uv run pytest -m integration tests/integration/test_jobs_e2e.py`(要 `docker compose up postgres redis`)。

---

次章([Phase-10-5](./Phase-10-5.md))では、作業単位 10-5 ── succeeded な simulate ジョブをJSONL エクスポートし、pandas で比較表・感度分析カーブを集計する分析トラックを追加する。
