# Phase 9-8: ジョブキュー基盤(作業単位 9-8)

## この章のゴール

README Phase 9 節「ジョブキューを導入するとしたらここ」を実行に移す。MVP(Phase 0〜6)以来YAGNI で見送ってきた非同期実行基盤を、**problem_type に依存しない横断インフラ**として追加する── CVRP + MILP(9-6)のような重い solve が既存のタイムアウト(`SOLVE_TIMEOUT_SECONDS`、既定10 秒)を超える場面で、`POST /api/v1/solve` の代わりに使える選択肢を用意する。

**既存の同期経路(`POST /api/v1/solve`、Phase 1)は 1 バイトも変えない**。新設する
`POST /api/v1/jobs` / `GET /api/v1/jobs/{id}` が並存するだけ ── route/network/shift/travel/project/logistics のどの problem_type でも両方の経路が使える。

**この章で作成 / 更新するファイル**: `app/models/job.py`、`app/repositories/job.py`、
`app/schemas/job.py`、`app/services/job.py`、`app/worker.py`、`app/api/routes/jobs.py`(新規)。
**既存への変更**(現行版は samples): `app/models/__init__.py`、`app/api/routes/__init__.py`、
`app/core/config.py`、`pyproject.toml`(`arq` 追加)、`docker-compose.yml`(`worker` サービス追加)。
新規 alembic マイグレーション 1 本(手順は §5)。

---

## 1. ライブラリの選定 ── なぜ arq か

README は「ジョブキューを導入するとしたらここ」とだけ書いており、ライブラリは指定していない。
選定は「① 有力ライブラリの全体像を見る → ② 本プロジェクトの環境制約で候補を絞る →③ 絞った候補を比較する」の 3 段で進める。

### 1.1 Python のジョブキュー/非同期タスク実行ライブラリ ── 有力な選択肢の全体像

実行モデル(sync ワーカー vs asyncio ネイティブ)と、必要とするインフラ(Redis / RabbitMQ /Postgres / ブローカー不要)で大きく 4 系統に分かれる。

- **Redis(または複数ブローカー対応)+ sync ワーカーの老舗系**:
  **Celery**(最も老舗・高機能。RabbitMQ / Redis / SQS 等ブローカーを選べる、chain / group / chordのようなワークフロー DSL(Canvas)、`celery beat` による定期実行、リトライ・レート制限・優先度キューまで一通り揃う。ワーカーは prefork(マルチプロセス)が既定で、本質的にsync 関数を前提にした設計)、**RQ(Redis Queue)**(Redis 専用、Celery よりずっと薄い API、fork ベースの sync ワーカー、依存が軽く学習コストが低い)、**Dramatiq**(Redis /RabbitMQ を選べる、Celery よりシンプルな API で「素朴な Celery」的な立ち位置、こちらもワーカーは sync 前提)。
- **asyncio ネイティブ + Redis 系(新しめの世代)**:
  **arq**(Redis 専用、`async def` の関数をそのままジョブにできる、依存が薄い)、**SAQ**
  (arq に強く影響を受けた設計で発想は近いが、コミュニティ規模・実績で arq に劣る)、**TaskIQ**(asyncio ネイティブでブローカーを Redis / RabbitMQ / NATS 等から選べる汎用性を持つ、比較的新しく実績はこれからの段階)。
- **Postgres ネイティブ系(ブローカー不要)**:
  **Procrastinate**(ジョブテーブル + `LISTEN`/`NOTIFY` で Postgres だけをブローカーとして使う、asyncio ネイティブ)、**pgqueuer**(同じく Postgres ベースで Procrastinate よりさらに薄い実装)。
  Redis を新たに増やしたくない構成(Postgres しか無いプロジェクト)で有力。
- **隣接するが別カテゴリのもの**: **Prefect / Temporal / Airflow / Dagster** は DAG 単位のワークフローオーケストレーション基盤で、複数ステップ・スケジューリング UI・リトライ戦略の可視化まで含む重量級インフラ ── 「1 リクエストを非同期に逃がす」という本章のスコープに対しては過剰。**APScheduler** はプロセス内の cron/interval スケジューラであり、分散ワーカーにジョブを配る「キュー」ではない(用途が異なる ── 定期実行が要るなら arq/Celery と併用する側)。

### 1.2 現環境での候補 ── 制約で絞り込む

DeciTima の `decitima-api` は次の環境的制約を持つ:

1. **サービス層はほぼ全面 `async def`**(`SolveService.solve` を含む)。FastAPI + SQLAlchemyの非同期エンジン(`asyncpg`)前提で組んである。
2. **Redis は Phase 1 以来 `redis.asyncio.Redis` の共有プール**(`app/infrastructure/redis.py::get_redis_pool()`)として既に本番導線に入っている(`RateLimiter` とリフレッシュトークン失効)。RabbitMQ 等の別ブローカーは導入していない。
3. Postgres は既に `Problem`/`Solution`/`BenchmarkRun` の永続化に使っているが、
   キューイング目的の `LISTEN`/`NOTIFY` 機構はまだ使っていない。
4. 必要な機能は「重い `solve` を 1 種類、非同期にキックして結果をポーリングで取れる」だけ
   ── ワークフロー DSL・定期実行・優先度キューは現時点で要らない(YAGNI)。

この制約に照らすと、現実的な候補は **Celery(Redis ブローカー)/ RQ / Dramatiq(Redis
ブローカー)/ Procrastinate(Postgres)/ TaskIQ(Redis ブローカー)/ arq** の 6 つに絞られる(SAQ は arq と設計思想がほぼ重なり実績で劣るため、pgqueuer は Procrastinate と同じPostgres 系統の代表として Procrastinate 側で評価すれば足りるので、比較表からは割愛する)。

### 1.3 候補比較

| ライブラリ             | 実行モデル                 | 必要インフラ                         | `async def` タスクの扱い                              | FastAPI との親和性                                                                                                                                                                         | 依存の重さ・機能量                                |
| ----------------- | --------------------- | ------------------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **Celery**        | sync ワーカー(prefork 既定) | Redis または RabbitMQ 等           | 非対応(タスク内で `asyncio.run()` を都度張る必要がある)           | ルートから `task.delay()` を呼ぶのは sync 呼び出しなので、async ルート内では `run_in_threadpool` 等でイベントループを塞がない配慮が要る。FastAPI 専用の統合パッケージは無い                                                                    | 重い(Canvas・beat・リトライ戦略等フル装備。本章の要件に対しては過剰) |
| **RQ**            | sync ワーカー(fork)       | Redis のみ                       | 非対応(同上)                                         | Celery と同じく `.enqueue()` が sync API。FastAPI 向けの統合は特に無い                                                                                                                                | 軽量(Celery ほどの機能は無い)                      |
| **Dramatiq**      | sync ワーカー             | Redis または RabbitMQ             | 非対応(同上)                                         | 同上(sync API、FastAPI 固有の統合は無い)                                                                                                                                                         | 中程度(Celery より薄いが RQ より機能はある)             |
| **Procrastinate** | asyncio ネイティブ         | **Postgres のみ**(Redis 不要)      | 対応(`async def` タスクをそのまま登録できる)                   | `await app.configure_task(...).defer_async(...)` を async ルートから直接呼べる。FastAPI の `lifespan` で `App` を起動/終了する公式例あり                                                                        | 中程度(`LISTEN`/`NOTIFY` ベースの独自機構)          |
| **TaskIQ**        | asyncio ネイティブ         | Redis / RabbitMQ / NATS 等(選択制) | 対応                                              | **`taskiq-fastapi` という専用パッケージがあり、FastAPI の Dependency Injection コンテキストをワーカー側にも伝播できる**(ルートと同じ `Depends` をタスク内でも使い回せる)                                                                  | 中程度(ブローカー抽象化層+DI 連携がある分やや厚い)             |
| **arq**           | **asyncio ネイティブ**     | **Redis のみ(既存の共有プールと同種)**      | **対応**(`async def solve_job(ctx, ...)` をそのまま登録) | 専用の統合パッケージは無いが、`await pool.enqueue_job(...)` が素の `async def` ルート/サービスから違和感なく呼べる。プール(`create_pool`/`close`)の生成・破棄は FastAPI の `lifespan` に自然に乗る ── 既存の `get_redis_pool()`(Phase 1)と同じ設計 | **軽量**(必要な機能(エンキュー・実行・結果取得)に絞られている)      |

### 1.4 結論

**arq を採用する。** 決め手は 3 つ:

- **実行モデルの一致**: `SolveService.solve` は `async def` であり、ワーカー側もそのまま`await` で呼びたい。Celery/RQ/Dramatiq は sync ワーカーが前提なので、タスク内で`asyncio.run(...)` を都度張る(イベントループの使い捨て・非同期リソース(DB エンジン等)をワーカープロセス内でどう使い回すかの設計をもう 1 段考える)必要が生まれる。arq はこの境界がそもそも存在しない。
- **FastAPI の非同期リクエストサイクルへの素直な組み込み**: `JobService.enqueue` は
  `POST /jobs` という async ルートから呼ばれる(§3)。arq の pool.enqueue_job(...)` は`await` するだけの非同期呼び出しで、Celery/RQ/Dramatiq のような sync API を async ルートの中で呼ぶ際の「イベントループを塞がないための一手間」が要らない。また enqueue 用のRedis プール(`arq.create_pool`)は FastAPI の `lifespan` で開閉でき、既存の`get_redis_pool()`(`app/infrastructure/redis.py`、Phase 1)と同じ設計パターンに収まる。
  TaskIQ の `taskiq-fastapi` が提供する「ルートとワーカーで `Depends` を共有する」仕組みは魅力的だが、`solve_job` は `on_startup` で自前のエンジン/Redis クライアントを作るだけで完結しており(§3)、FastAPI の DI コンテキストをワーカー側へ伝播させる実在の消費者が無い ── 進行のルール #17 の判定基準に照らして見送る。
- **インフラの重複回避**(進行のルール #17 の判定基準「今この Phase を駆動する実在の
  消費者は何か」): Redis は Phase 1 の `RateLimiter` とリフレッシュトークン失効で**既に本番導線に入っている実在の消費者**。Procrastinate(Postgres 専用)を選んでも Redis は消せずインフラが 1 つ減るわけではなく、逆に「キュー用に Postgres の LISTEN/NOTIFY」という新しい機構を増やすだけになる。arq は既存の Redis 共有プールにジョブキューという用途を**足すだけ**で済む。

Celery の Canvas(複数ジョブの連鎖・集約)や `celery beat`(定期実行)のような機能は、
本章の要件(`solve` を 1 種類だけ非同期に逃がす)には現時点で不要 ── 将来、複数ステップのワークフローや定期実行が実在の消費者として現れたら、そのとき Celery や TaskIQ への乗り換え・併用を再検討する(YAGNI。CLAUDE.md「設計上の決定事項」でジョブキュー自体の導入も MVP 以来 Phase 9 まで遅延させてきたのと同じ判断軸)。

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

`app/repositories/job.py::JobRepository` は既存 `CRUDRepository[Job]` を継承し、`create()` と`update_status()` を足すだけ ── `ProblemRepository` / `SolutionRepository`(Phase 1)と同型。

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

- **`solve_job` は `SolveService.solve`(Phase 1)をそのまま呼ぶ** ── validate → select →compute → verify → 永続化のロジックを一切重複させない(進行のルール #17)。ワーカーは「いつ・どう呼ぶか」の皮だけを足す。
- **`bypass_rate_limit=True`** ── `resource="job_submit"` の制限は投入時点(`JobService.enqueue`)で既にかけてある。ワーカー側で `resource="solve"` の制限を二重にかけない。
- **ワーカーは別プロセス**(`uv run arq app.worker.WorkerSettings`)なので、FastAPI のリクエストスコープの DB セッション(`SessionDep`)は使い回せない ── `on_startup` で専用のエンジン・`session_factory`・Redis クライアントを作り `ctx`(worker context dict)に積む(arq の定番パターン)。
- **`_job_id=str(job.id)`** ── arq 自身のジョブ id と、こちらの `Job.id` を揃えておく。
  副作用として arq の一意性保証(同じ `_job_id` の二重投入は `None` を返す)も効き、後からarq 側の状態(`arq.jobs.Job(job_id, redis).status()`)を突き合わせやすくなる(§6 のintegration テストで使う)。

---

## 4. API ── 既存 `/solve` と併存する `/jobs`

```python
# app/api/routes/jobs.py(要点)
POST /api/v1/jobs        -> 202 Accepted + {"job_id": ..., "status": "queued"}
GET  /api/v1/jobs/{id}   -> {"job_id", "problem_type", "status", "result"?, "error"?, ...}
```

- `POST /jobs` のリクエストボディは `schemas/optimization.py::SolveRequest` を**そのまま再利用**する(`problem` / `algorithm` / `persist` / `timeout_seconds` ── 同期 `/solve` と同じ入力形)。
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

- `backend` サービスと同じ `build.context` / `volumes` を共有し、コマンドだけ `arq` に差し替える ── 同じイメージ・同じコードなので二重管理にならない。
- `pyproject.toml` に `arq` を追加(`uv add arq`。Phase 6-7 の `ortools` 追加と同じ手順)。
- 新規テーブル `jobs` のマイグレーションは
   `uv run alembic revision --autogenerate -m "add jobs table"`
  → `uv run alembic upgrade head` 
  をユーザー側で実行する(生成される migration ファイルの中身は各自の DB 状態に依存するため、教材としてはコマンド手順のみ示す。Phase 1〜8 の「`alembic upgrade head` は no-op」から**初めて実テーブルが増える**)。
  
  > Docker環境の場合はdocker-compose.ymlと同階層のディレクトリで
  > `docker compose exec backend uv run alembic revision --autogenerate -m "add jobs table"　`
  > → `docker compose exec backenduv run alembic upgrade head`

---

## 6. まとめ

- ジョブキューは **problem_type に依存しない横断インフラ**として追加した ── 特定のドメインロジックには触れていない。
- 既存の同期経路(`SolveService` / `POST /solve`)は無変更。`JobService` / `solve_job` はそれを**呼ぶ側**として追加しただけ(進行のルール #17 の「重複させない」を体現)。
- Phase 9 で唯一「スタブが要る」章 ── `JobService.enqueue` のユニットテストは実際に Redis へ繋がず arq プールをフェイクに差し替える。実際にジョブが Redis に積まれ、ワーカーが処理できることは integration テスト(実 Postgres + 実 Redis)で確認する。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `JobService.enqueue` / `get_status`(`tests/unit/test_job_service.py`)、
>   `solve_job`(状態遷移と `SolveService` への委譲、`tests/unit/test_worker.py`)
> - **ドライバ**: 各テスト関数。`db_session` フィクスチャ(投入側)/ 専用のインメモリSQLite エンジン + `session_factory`(ワーカー側、`tests/api/conftest.py::api` と同型)
> - **スタブ**: **`JobService.enqueue` だけ要る** ── `arq.create_pool` をフェイクプールに差し替え、実際には Redis へ繋がず呼び出し引数だけ記録する。`solve_job` 自体は`SolveService.solve` を直接呼ぶだけの純粋な処理なのでスタブ不要(`FakeRedis` はコンストラクタが要求するだけ)
> - 実際に Redis へジョブが届き arq 側の Job オブジェクトから状態が見えることは`tests/integration/test_jobs_e2e.py`(`-m integration`)で確認する

> **写経の罠(`test_jobs_e2e.py` の最終検証)**: `enqueue` に使った `pg_session`
> (`expire_on_commit=False`)を、`solve_job` 実行後の最終検証(`row.status == "succeeded"`)
> でもそのまま使い回すと、SQLAlchemy の identity map に古い `job` インスタンス
> (status="queued")が残っており `session.get()` がそれを返してしまう ── `solve_job` は
> **別セッション**で更新・commit しているため、DB 上は正しく "succeeded" でも
> `AssertionError: assert 'queued' == 'succeeded'` になる。本番の `GET /jobs/{id}` は
> リクエストごとに新規セッション(`get_db`)を使うのでこの穴は無い ── バグはテストが
> セッションを使い回したことだけ。**修正 = 最終検証だけ新しいセッションで読み直す**
> (samples に反映済み。詳細 `q_a.md` Q52)。

| ケース                                    | 期待                                                               |
| -------------------------------------- | ---------------------------------------------------------------- |
| `enqueue` が queued な Job を作りキューへ積む     | `status == "queued"`、フェイクプールに記録                                  |
| `enqueue` が infeasible な問題を弾く          | `InfeasibleProblemError`、キューには積まれない                              |
| `get_status`(未知の id)                   | `None`                                                           |
| `get_status`(作成済み)                     | 作成した Job と同一                                                     |
| `solve_job` が成功パスを処理                   | `status == "succeeded"`、`payload["result"]["status"] == "valid"` |
| `solve_job` が失敗パスを記録(registry を空にして誘発) | `status == "failed"`、`payload["error"]` あり                       |
| `solve_job`(未知の job_id)                | 例外を出さず静かに戻る                                                      |
| (integration)実 Redis へのエンキュー           | arq 側 `status() == JobStatus.queued`                             |

`uv run pytest tests/unit/test_job_service.py tests/unit/test_worker.py` /
`uv run pytest -m integration tests/integration/test_jobs_e2e.py`(要 `docker compose up postgres redis`)/
`uvx pyright app/models app/repositories app/schemas app/services app/worker.py app/api`。

---

次章([Phase-9-9](./Phase-9-9.md))では、作業単位 9-9 ── decitima-ui の Logistics Optimizer
ページ。車両ルートを `GraphCanvas` で色分け表示し、`POST /jobs` → ポーリングの UI を実装する。
