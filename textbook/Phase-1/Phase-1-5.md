# Phase 1-5: 永続化 ── Problem / Solution モデルとリポジトリ(作業単位 1-5)

## この章のゴール

solve 結果を永続化し、`solution_id` で後から引ける土台を作る(FR-6 / `Phase-0-5.md` §5.2)。

- `app/models/optimization.py` ── `Problem` / `Solution`(JSONB payload + 検索キーのみカラム)
- `app/repositories/optimization.py` ── `CRUDRepository` 継承、`flush` のみ
- `app/models/__init__.py` と `alembic/env.py` の両方にモデル登録
- Alembic マイグレーションの生成と目視確認

**この章で新規作成するファイル**: `app/models/optimization.py`、`app/repositories/optimization.py`、新規マイグレーション(`alembic/versions/xxxx_*.py`)。
**既存ファイルへの追記**: `app/models/__init__.py`、`alembic/env.py`(§3)。

対応サンプル: `samples/app/models/optimization.py`, `samples/app/repositories/optimization.py`,
`samples/alembic/versions/a1b2c3d4e5f6_add_problems_and_solutions.py`。
テストは `samples/tests/unit/test_optimization_repository.py`(SQLite)と
`samples/tests/integration/test_optimization_persistence.py`(実 PG)。
`app/models/__init__.py` / `alembic/env.py` は既存ファイルへの追記(§3)で samples には含めない。
設計は `Phase-0-8.md`。

---

## 1. JSONB 中心 + 検索キーのみカラム化

ハイブリッドスキーマ(`Phase-0-2.md`)を完全正規化すると problem_type ごとにテーブルが
増殖する。逆に全部を 1 個の JSON に入れると検索できない。中間を取る(`Phase-0-8.md` §3)。

| カラムにする(検索・結合・集計に使う)                                      | JSONB に入れる(そのまま読み書き)                                |
| -------------------------------------------------------- | --------------------------------------------------- |
| `id` / `user_id` / `problem_type` / `created_at`         | `OptimizationProblem` 全体(`payload`)                 |
| `status` / `algorithm_name` / `algorithm_implementation` | `CandidateSolution` 全体(`metrics` / `violations` 含む) |

```python
# app/models/optimization.py
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Postgres では JSONB(検索・インデックス可)、SQLite テストでは汎用 JSON にフォールバック
JsonB = JSON().with_variant(JSONB(), "postgresql")


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    solutions: Mapped[list["Solution"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )


class Solution(Base):
    __tablename__ = "solutions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    algorithm_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    algorithm_implementation: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    problem: Mapped["Problem"] = relationship(back_populates="solutions")
```

> **JSONB*とは**
> JSON形式のデータを、PostgreSQLが検索・処理しやすい形に変換して保存する型
> 
> |            | JSON           | JSONB         |
> | ---------- | -------------- | ------------- |
> | 保存形式       | JSON文字列そのものに近い | バイナリ形式に変換     |
> | JSONの空白・順序 | 保持する           | 保持しない         |
> | JSONの解析    | 読み出すたびに必要      | 保存時に解析済み      |
> | 検索         | 比較的遅い          | 高速            |
> | インデックス     | 制限あり           | 強力            |
> | 一般的な用途     | JSON原文の保持      | JSONデータの検索・操作 |
> 
> そのため、**PostgreSQLでJSONを扱うならJSONBが選ばれることが多い**。
> JSONBは構造が可変・拡張的・一部だけJSONとして扱いたい場合に適しているため、取り扱う情報が画一的で明確なら通常のJSONがいい

既存 `app/models/conversation.py` のパターン(uuid PK / tz 付き `created_at` /
`Mapped` + `mapped_column`)を踏襲する。

### 1.1 JSON カラムは「まるごと代入」

Python 側で `row.payload["x"] = 1` と書き換えても SQLAlchemy が変更を検知しない
既知の落とし穴がある。DeciTima は **JSON カラムを書き換えず毎回まるごと代入**する
(`Phase-0-8.md` §3.3):

```python
row.payload = {**row.payload, "status": "invalid"}   # ○
# row.payload["status"] = "invalid"                  # × 追跡されない
```

`MutableDict` を導入しなくて済む。

---

## 2. リポジトリ

```python
# app/repositories/optimization.py
class ProblemRepository(CRUDRepository[Problem]):
    model = Problem
    async def create(self, *, user_id, problem_type, payload) -> Problem:
        row = Problem(user_id=user_id, problem_type=problem_type, payload=payload)
        self._session.add(row)
        await self._session.flush()          # id を確定。commit はしない
        return row

class SolutionRepository(CRUDRepository[Solution]):
    model = Solution
    async def create(self, *, problem_id, status, algorithm_name,
                     algorithm_implementation, payload) -> Solution: ...
    async def list_for_problem(self, problem_id) -> list[Solution]:
        return await self.list_all(problem_id=problem_id, order_by=Solution.created_at)
```

`flush()` はするが `commit()` はしない ── トランザクション境界は `SolveService`
(`decitima-api/CLAUDE.md` のリポジトリ層方針)。`get_by_id` / `find_one` / `list_all` は
`CRUDRepository` から継承。

---

## 3. モデル登録(既存ファイル 2 か所への追記)

`--autogenerate` が新モデルを拾うには **両方**に登録が要る(`Phase-0-8.md` §6.1)。
どちらも既存ファイルなので samples には入れず、次を足す:

```python
# ① app/models/__init__.py
from app.models.conversation import Conversation, Message
from app.models.optimization import Problem, Solution     # ← 追加
from app.models.user import User

__all__ = ["Conversation", "Message", "Problem", "Solution", "User"]   # ← Problem, Solution を追加
```

```python
# ② alembic/env.py(import 行を変更)
# 変更前: from app.models import Conversation, Message, User  # noqa: F401
from app.models import Conversation, Message, Problem, Solution, User  # noqa: F401
```

---

## 4. マイグレーション

```bash
cd decitima-api/backend
uv run alembic revision --autogenerate -m "add problems and solutions tables"
# 生成された versions/xxxx_*.py を目視確認(JSONB / index / FK / down_revision が意図どおりか)
uv run alembic upgrade head
```

```bash
#docker環境を利用する場合
docker compose up -d postgres
#空 DB のまま autogenerate すると users / conversations / messages まで CREATE する移行を吐きます(既存の初期 migration 済みの状態と差分を取りたい)。
docker compose run --rm backend uv run alembic upgrade head
docker compose run --rm backend uv run alembic revision --autogenerate -m "add problems and solutions tables"
docker compose run --rm backend uv run alembic upgrade head既存の初期 migration(`2b97c8ec8533_initial_schema.py`)は**残す**。新テーブルは新 migration として積む。
```

- `ruff` は `alembic/versions/` を除外設定済みなので生成コードの lint は気にしなくてよい。
- 生成物がどうなるべきかは `samples/alembic/versions/a1b2c3d4e5f6_add_problems_and_solutions.py`
  を参照(既存 migration のスタイルに整えたもの)。`revision` 文字列は自分の生成物の値を使う。
- payload カラムは Postgres 上で `JSONB`。migration では
  `postgresql.JSONB(astext_type=sa.Text())`。

---

## 5. テスト観点

> **テスト対象 / ドライバ / スタブ**(進行ルール #14):
> 
> - **対象**: `Problem` / `Solution` ORM と `ProblemRepository` / `SolutionRepository`
> - **ドライバ**: テスト関数
> - **スタブ / テストダブル**: `db_session`(インメモリ SQLite。本物の Postgres の代役)。
>   Phase 1 で**初めてテストダブルが登場する** ── リポジトリ層が DB に結合しているのは
>   正しい設計(純粋レイヤーではない)。実 PG 依存は `@pytest.mark.integration` に分離(§5.2)。

### 5.1 ユニット(`test_optimization_repository.py`、SQLite)

- `ProblemRepository.create` → `SolutionRepository.create` → `get_by_id` で往復、
  `payload["metrics"]["total_weight"]` が読める
- JSON カラムを「まるごと代入」で更新できる(部分書き換えは追跡されない)
- `list_for_problem` が `created_at` 昇順
  
  > テスト時にSQLiteを使う設定(backend/tests/confte st.py)
  > ※テンプレートリポジトリに既に含まれていることを確認
  
  ```bash
  @pytest_asyncio.fixture
  async def db_session() -> AsyncGenerator[AsyncSession]:
      """リポジトリ/サービスのユニットテスト用に、インメモリSQLiteの非同期セッションを提供する。"""
      engine = create_async_engine("sqlite+aiosqlite:///:memory:")
      async with engine.begin() as conn:
          # テスト用DBにモデル定義から全テーブルを作成する
          await conn.run_sync(Base.metadata.create_all)
      session_factory = async_sessionmaker(engine, expire_on_commit=False)
      async with session_factory() as session:
          yield session
      await engine.dispose()
  ```

### 5.2 統合(`test_optimization_persistence.py`、実 PG。`@pytest.mark.integration`)

- 実 Postgres 上で `Base.metadata.create_all` からテーブルが作れる
- JSONB カラムへの書き込み・読み出しと「まるごと代入」更新

`docker compose up postgres` してから `uv run pytest -m integration`。既定では除外される。

---

## 6. まとめ

- `Problem` / `Solution` は JSONB `payload` + 検索キー(`user_id` / `problem_type` / `status` /
  `algorithm_*`)のみカラム化。problem_type を足してもマイグレーション不要。
- SQLite テスト用に `JSON().with_variant(JSONB(), "postgresql")`。JSON はまるごと代入。
- リポジトリは `CRUDRepository` 継承 + `create` / `list_for_problem`。`flush` のみ。
- 新モデルは `app/models/__init__.py` と `alembic/env.py` の**両方**に登録してから autogenerate。

次章([Phase-1-6](./Phase-1-6.md))では、作業単位 1-6 ── `SolveService` /
最小 Validation・Verification / `POST /api/v1/solve` を実装する。
