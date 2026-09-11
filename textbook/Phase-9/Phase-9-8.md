# Phase 9-8: ジョブキュー基盤(作業単位 9-8)

## この章のゴール

README Phase 9 節「ジョブキューを導入するとしたらここ」を実行に移す。MVP(Phase 0〜6)以来
YAGNI で見送ってきた非同期実行基盤を、**problem_type に依存しない横断インフラ**として追加する
── CVRP + MILP(9-6)のような重い solve が既存のタイムアウト(`SOLVE_TIMEOUT_SECONDS`、既定
10 秒)を超える場面で、`POST /api/v1/solve` の代わりに使える選択肢を用意する。

**既存の同期経路(`POST /api/v1/solve`、Phase 1)は 1 バイトも変えない**。新設する
`POST /api/v1/jobs` / `GET /api/v1/jobs/{id}` が並存するだけ ── route/network/shift/travel/
project/logistics のどの problem_type でも両方の経路が使える。

**この章で作成 / 更新するファイル**: `app/models/job.py`、`app/repositories/job.py`、
`app/schemas/job.py`、`app/services/job.py`、`app/worker.py`、`app/api/routes/jobs.py`(新規)。
**既存への変更**(現行版は samples): `app/models/__init__.py`、`app/api/routes/__init__.py`、
`app/core/config.py`、`pyproject.toml`(`arq` 追加)、`docker-compose.yml`(`worker` サービス追加)。
新規 alembic マイグレーション 1 本(手順は §5)。

---

## 1. ライブラリの選定 ── なぜ arq か

README は「ジョブキューを導入するとしたらここ」とだけ書いており、ライブラリは指定していない。
候補は Celery / RQ / arq のような Redis ベースの選択肢だが、**既存の
`app/infrastructure/redis.py` が `redis.asyncio.Redis` の共有プールを既に使っている**
(Phase 1 以来、レート制限とリフレッシュトークン失効に利用)。arq は asyncio ネイティブで
Redis だけを要求する軽量なジョブキューライブラリ ── Celery / RQ のような sync Redis 前提の
ライブラリを新たに増やさずに済む(進行のルール #17 の判定基準「今この Phase を駆動する実在の
消費者は何か」に照らし、既存の非同期 Redis 利用パターンとの親和性が実在の理由)。

---

## 2. Job モデル ── Problem/Solution と同じハイブリッド JSONB

```python
# app/models/job.py(要点。全文は samples)
class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(..., primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(..., ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True, default="queued")
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(..., server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(..., server_default=func.now(), onupdate=func.now())
```

- `JsonB` は `models/optimization.py` で定義済みの型(`JSON().with_variant(JSONB(), "postgresql")`)
  を**そのまま import して再利用**する(2 バイト目のコピーを作らない ── 進行のルール #17)。
- `payload` の中身: `{"request": SolveRequest.model_dump(...), "result": CandidateSolution 相当 |
  None, "problem_id": str|None, "solution_id": str|None, "error": str|None}`。
- `status` は `queued -> running -> succeeded | failed` の一方向遷移(ワーカーが書き換える)。

`app/repositories/job.py::JobRepository` は既存 `CRUDRepository[Job]` を継承し、`create()` と
`update_status()` を足すだけ ── `ProblemRepository` / `SolutionRepository`(Phase 1)と同型。

---

## 3. JobService(投入側)と `app/worker.py`(処理側)の分離

```python
# app/services/job.py(要点)
class JobService:
    async def enqueue(self, *, user_id, request: SolveRequest, bypass_rate_limit=False) -> Job:
        # (a) レート制限(resource="job_submit") (b) Validation ← ジョブを作る前に明らかな不正を弾く
        # (c) Job 行を作成 + commit(status="queued")
        # (d) arq へエンキュー(_job_id を Job.id と揃える)
        await pool.enqueue_job("solve_job", str(job.id), _job_id=str(job.id))
```

```python
# app/worker.py(要点)
async def solve_job(ctx, job_id: str) -> None:
    # Job 行を読む -> status="running" -> SolveService.solve(bypass_rate_limit=True) -> 結果を書き戻す
    # 例外は握って status="failed" + payload["error"] に記録する

class WorkerSettings:
    functions = [solve_job]
    on_startup = on_startup   # 専用の DB エンジン + Redis クライアントを作る
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
```

- **`solve_job` は `SolveService.solve`(Phase 1)をそのまま呼ぶ** ── validate → select →
  compute → verify → 永続化のロジックを一切重複させない(進行のルール #17)。ワーカーは
  「いつ・どう呼ぶか」の皮だけを足す。
- **`bypass_rate_limit=True`** ── `resource="job_submit"` の制限は投入時点(`JobService.enqueue`)
  で既にかけてある。ワーカー側で `resource="solve"` の制限を二重にかけない。
- **ワーカーは別プロセス**(`uv run arq app.worker.WorkerSettings`)なので、FastAPI の
  リクエストスコープの DB セッション(`SessionDep`)は使い回せない ── `on_startup` で専用の
  エンジン・`session_factory`・Redis クライアントを作り `ctx`(worker context dict)に積む
  (arq の定番パターン)。
- **`_job_id=str(job.id)`** ── arq 自身のジョブ id と、こちらの `Job.id` を揃えておく。
  副作用として arq の一意性保証(同じ `_job_id` の二重投入は `None` を返す)も効き、後から
  arq 側の状態(`arq.jobs.Job(job_id, redis).status()`)を突き合わせやすくなる(§6 の
  integration テストで使う)。

---

## 4. API ── 既存 `/solve` と併存する `/jobs`

```python
# app/api/routes/jobs.py(要点)
POST /api/v1/jobs        -> 202 Accepted + {"job_id": ..., "status": "queued"}
GET  /api/v1/jobs/{id}   -> {"job_id", "problem_type", "status", "result"?, "error"?, ...}
```

- `POST /jobs` のリクエストボディは `schemas/optimization.py::SolveRequest` を**そのまま再利用**
  する(`problem` / `algorithm` / `persist` / `timeout_seconds` ── 同期 `/solve` と同じ入力形)。
  新規に定義するのはレスポンス(`JobSubmitResponse` / `JobStatusResponse`、`schemas/job.py`)だけ。
- `GET /jobs/{id}` は所有者以外(かつ非管理者)には 404 を返す(他人のジョブの存在を漏らさない)。
- `app/api/routes/__init__.py` に `jobs_router` を追加登録するだけ ── `solve_router` には触れない。

---

## 5. インフラ ── `docker-compose.yml` の `worker` サービス + マイグレーション

```yaml
# docker-compose.yml(追加。全文は samples)
worker:
  build:
    context: ./backend
    target: builder
  env_file: [.env]
  volumes: ["./backend:/app", "backend_venv:/app/.venv"]   # backend と同じコード・同じ venv
  command: ["uv", "run", "arq", "app.worker.WorkerSettings"]
  depends_on:
    postgres: { condition: service_healthy }
    redis: { condition: service_healthy }
  networks: [internal]
```

- `backend` サービスと同じ `build.context` / `volumes` を共有し、コマンドだけ `arq` に
  差し替える ── 同じイメージ・同じコードなので二重管理にならない。
- `pyproject.toml` に `arq` を追加(`uv add arq`。Phase 6-7 の `ortools` 追加と同じ手順)。
- 新規テーブル `jobs` のマイグレーションは `uv run alembic revision --autogenerate -m "add jobs table"`
  → `uv run alembic upgrade head` をユーザー側で実行する(生成される migration ファイルの中身は
  各自の DB 状態に依存するため、教材としてはコマンド手順のみ示す。Phase 1〜8 の
  「`alembic upgrade head` は no-op」から**初めて実テーブルが増える**)。

---

## 6. まとめ

- ジョブキューは **problem_type に依存しない横断インフラ**として追加した ── 特定のドメイン
  ロジックには触れていない。
- 既存の同期経路(`SolveService` / `POST /solve`)は無変更。`JobService` / `solve_job` は
  それを**呼ぶ側**として追加しただけ(進行のルール #17 の「重複させない」を体現)。
- Phase 9 で唯一「スタブが要る」章 ── `JobService.enqueue` のユニットテストは実際に Redis へ
  繋がず arq プールをフェイクに差し替える。実際にジョブが Redis に積まれ、ワーカーが処理できる
  ことは integration テスト(実 Postgres + 実 Redis)で確認する。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
>
> - **対象**: `JobService.enqueue` / `get_status`(`tests/unit/test_job_service.py`)、
>   `solve_job`(状態遷移と `SolveService` への委譲、`tests/unit/test_worker.py`)
> - **ドライバ**: 各テスト関数。`db_session` フィクスチャ(投入側)/ 専用のインメモリ
>   SQLite エンジン + `session_factory`(ワーカー側、`tests/api/conftest.py::api` と同型)
> - **スタブ**: **`JobService.enqueue` だけ要る** ── `arq.create_pool` をフェイクプールに
>   差し替え、実際には Redis へ繋がず呼び出し引数だけ記録する。`solve_job` 自体は
>   `SolveService.solve` を直接呼ぶだけの純粋な処理なのでスタブ不要(`FakeRedis` は
>   コンストラクタが要求するだけ)
> - 実際に Redis へジョブが届き arq 側の Job オブジェクトから状態が見えることは
>   `tests/integration/test_jobs_e2e.py`(`-m integration`)で確認する

| ケース | 期待 |
| --- | --- |
| `enqueue` が queued な Job を作りキューへ積む | `status == "queued"`、フェイクプールに記録 |
| `enqueue` が infeasible な問題を弾く | `InfeasibleProblemError`、キューには積まれない |
| `get_status`(未知の id) | `None` |
| `get_status`(作成済み) | 作成した Job と同一 |
| `solve_job` が成功パスを処理 | `status == "succeeded"`、`payload["result"]["status"] == "valid"` |
| `solve_job` が失敗パスを記録(registry を空にして誘発) | `status == "failed"`、`payload["error"]` あり |
| `solve_job`(未知の job_id) | 例外を出さず静かに戻る |
| (integration)実 Redis へのエンキュー | arq 側 `status() == JobStatus.queued` |

`uv run pytest tests/unit/test_job_service.py tests/unit/test_worker.py` /
`uv run pytest -m integration tests/integration/test_jobs_e2e.py`(要 `docker compose up postgres redis`)/
`uvx pyright app/models app/repositories app/schemas app/services app/worker.py app/api`。

---

次章([Phase-9-9](./Phase-9-9.md))では、作業単位 9-9 ── decitima-ui の Logistics Optimizer
ページ。車両ルートを `GraphCanvas` で色分け表示し、`POST /jobs` → ポーリングの UI を実装する。
