# Phase 0-8: DB 設計

## この章のゴール

DeciTima が永続化するデータのスキーマを設計する。

- 何を保存するのか(problems / solutions / verifications / benchmark_runs)
- 正規化するか、JSONB に寄せるか
- ORM モデル案(既存テンプレートのパターンを踏襲)
- Alembic マイグレーションの運用
- Phase 1 で最初に作るテーブルの範囲

---

## 1. なぜ保存するのか

FR-6(問題・解・検証結果を永続化し後から参照できる)と、
Phase 0-5 / 0-7 で決めた「solve 結果は `solution_id` で引ける」を満たすため。

保存によって可能になること:

- **再現性の証跡**(NFR-1): 「この問題に、このアルゴリズムで、この解が出た」を残す。
- **比較**(NFR-3 / Phase 3): 同じ問題に対する複数アルゴリズムの解を並べる。
- **監査**(NFR-4): なぜその解になったかを後から追える。
- **非同期化への布石**(Phase 0-5): 将来 solve をジョブ化しても、結果テーブルと
  取得 API は変わらない。

---

## 2. 保存する対象

| テーブル | 保存するもの | 導入 Phase |
| --- | --- | --- |
| `problems` | 投入された `OptimizationProblem` | 1 |
| `solutions` | アルゴリズムが出した `CandidateSolution`(検証後) | 1 |
| `verifications` | 検証の詳細(違反一覧、判定)。**[Phase 2 で確定] 作らない** ── `Solution.status` + `payload` に埋める(§4) | ~~2~~ 見送り |
| `benchmark_runs` | ベンチマーク 1 回分(問題 + 複数解 + 実測メトリクス) | 3 |

MVP で Phase 1 に作るのは **`problems` と `solutions` の 2 つ**。
`benchmark_runs` は Phase 3 で追加する。`verifications` は作らない([Phase 2 で確定] §4)。

---

## 3. 正規化 vs JSONB

### 3.1 判断

DeciTima のスキーマは **ハイブリッド**(Phase 0-2)── 共通の骨格 + `problem_type`
ごとに形の違う `data` / `assignments`。これを完全に正規化すると:

- `route_nodes` / `route_edges` / `shift_staff` / `shift_slots` / `assignments` / ...
  と problem_type ごとにテーブルが増殖する。
- problem_type を 1 つ足すたびにマイグレーションが要る。
- Pydantic モデルと ORM の二重メンテになる。

一方で全部を 1 個の JSON カラムに入れると、検索・集計ができない。

**採用: JSONB 中心 + 検索・集計に使う列だけ正規カラムに切り出す。**

| カラムにするもの(検索・結合・集計に使う) | JSONB に入れるもの(そのまま読み書きするだけ) |
| --- | --- |
| `id`, `user_id`, `problem_type`, `created_at` | `OptimizationProblem` 全体(`payload`) |
| `solution.status`, `algorithm_name`, `algorithm_implementation` | `CandidateSolution` 全体、`metrics`、`violations` |

### 3.2 なぜ JSONB(JSON ではなく)

PostgreSQL の `JSONB` は:

- バイナリ格納で読み出しが速い。
- `->`, `->>`, `@>` などで部分検索・インデックスができる(将来
  「total_weight が N 以下の解」を引きたくなったとき対応可能)。
- SQLAlchemy 2.x では `from sqlalchemy.dialects.postgresql import JSONB` で使える。

ユニットテスト(インメモリ SQLite、`conftest.py` の `db_session`)では
SQLite に JSONB がないため、**`JSON`(汎用)にフォールバックする型**を使う。

```python
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Postgres では JSONB、それ以外(SQLite テスト)では JSON
JsonB = JSON().with_variant(JSONB(), "postgresql")
```

### 3.3 ミューテーション追跡

JSON カラムの中身を Python 側で書き換えても SQLAlchemy が変更を検知しない
既知の落とし穴がある。DeciTima では **JSON カラムは書き換えず、毎回まるごと
代入する**方針(`payload = new_problem.model_dump()`)にする。
これなら `MutableDict` を導入しなくてよい。

---

## 4. ORM モデル案

既存 `app/models/conversation.py` のパターンを踏襲:
uuid 主キー / タイムゾーン付き `created_at` / `Mapped[...]` + `mapped_column`。

```python
# app/models/optimization.py
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

JsonB = JSON().with_variant(JSONB(), "postgresql")


class Problem(Base):
    """投入された OptimizationProblem 1件。payload に問題定義の全体を持つ。"""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # problem_type: 検索・集計に使うので JSON からカラムへ切り出す
    problem_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # payload: OptimizationProblem.model_dump() の全体
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    solutions: Mapped[list["Solution"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )


class Solution(Base):
    """あるアルゴリズムが Problem に対して出した検証済みの CandidateSolution 1件。"""

    __tablename__ = "solutions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # status / algorithm_* は比較 UI とベンチで頻繁に絞り込むのでカラム化
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    algorithm_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    algorithm_implementation: Mapped[str] = mapped_column(String(64), nullable=False)
    # payload: CandidateSolution.model_dump() の全体(metrics / violations 含む)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem: Mapped["Problem"] = relationship(back_populates="solutions")
```

### `verifications` は別テーブルにしない

MVP では検証結果(`status` / `violations` / `soft_penalty` / metrics)は
`Solution.status`(カラム)と `Solution.payload`(JSONB)の中に入っている。独立したクエリ需要
(「hard 違反した解だけ集計」など)が出てきたら `verifications` テーブルに切り出す。YAGNI。

> **[Phase 2 で確定 ── `verifications` テーブルは作らない]** 当初「Phase 2 で切り出す」候補
> だったが撤回。MVP(Phase 0〜5)に payload 内クエリ需要が無く、取得はすべて id / 実カラム経由
> (Notes Q12)。`benchmark_runs`(Phase 3)を作るとき、または実際にそのクエリ需要が出たときに、
> 消費者と一緒に切り出す。詳細 `Phase-2-introduction.md` §7。

---

## 5. リポジトリ

既存 `CRUDRepository[ModelType]`(`app/repositories/base.py`)を継承。

```python
# app/repositories/optimization.py
from app.models.optimization import Problem, Solution
from app.repositories.base import CRUDRepository


class ProblemRepository(CRUDRepository[Problem]):
    model = Problem


class SolutionRepository(CRUDRepository[Solution]):
    model = Solution

    async def list_for_problem(self, problem_id) -> list[Solution]:
        """ある問題に紐づく全解を生成日時順で返す(比較 UI 用)。"""
        return await self.list_all(problem_id=problem_id, order_by=Solution.created_at)
```

`flush()` はするが `commit()` はしない(リポジトリ層の既存方針)。
`commit()` は `SolveService` が握る。

---

## 6. Alembic マイグレーション

### 6.1 新モデルの登録が 2 か所必要

既存の `alembic/env.py` は:

```python
from app.models import Conversation, Message, User  # noqa: F401
```

でモデルを metadata に登録している。DeciTima のモデルも:

1. `app/models/__init__.py` に `Problem`, `Solution` を追加(re-export)
2. `alembic/env.py` の import に追加

の両方をやらないと `--autogenerate` が拾わない。

```python
# app/models/__init__.py
from app.models.conversation import Conversation, Message
from app.models.optimization import Problem, Solution
from app.models.user import User

__all__ = ["Conversation", "Message", "Problem", "Solution", "User"]
```

```python
# alembic/env.py
from app.models import Conversation, Message, Problem, Solution, User  # noqa: F401
```

### 6.2 手順(Phase 1 で実施)

```bash
cd decitima-api/backend
uv run alembic revision --autogenerate -m "add problems and solutions tables"
# 生成された versions/xxxx_*.py を目視確認（JSONB / index / FK が意図どおりか）
uv run alembic upgrade head
```

- 既存の初期スキーマ migration(`2b97c8ec8533_initial_schema.py`)は**残す**。
  DeciTima のテーブルは新しい migration として積む。
- `ruff` は `alembic/versions/` を除外設定済み(`pyproject.toml`)なので
  生成コードの lint は気にしなくてよい。

---

## 7. データフローとの対応(Phase 0-3 の再確認)

```
SolveService.solve():
    ...
    (g) 永続化:
        problem_row = await ProblemRepository(session).get_or_create(
            lookup={...}, defaults={"user_id": ..., "problem_type": problem.problem_type,
                                    "payload": problem.model_dump(mode="json")})
        solution_row = Solution(
            problem_id=problem_row.id, status=solution.status,
            algorithm_name=solution.produced_by.name,
            algorithm_implementation=solution.produced_by.implementation,
            payload=solution.model_dump(mode="json"))
        session.add(solution_row)
        await session.flush()          # ← id を確定（repository 層の役割）
    (h) await session.commit()          # ← SolveService の役割
```

`persist=False`(教材の試行)なら (g)(h) をスキップし、`problem_id` / `solution_id` は None。

---

## 8. まとめ

- 保存対象は `problems` / `solutions`(MVP)、`verifications`(Phase 2)、
  `benchmark_runs`(Phase 3)。
- **JSONB 中心 + 検索キーだけカラム化**。problem_type を足してもマイグレーション不要。
  テストの SQLite 向けに `JSON().with_variant(JSONB(), "postgresql")`。
- JSON カラムは書き換えず毎回まるごと代入(ミューテーション追跡の落とし穴回避)。
- ORM は既存 `conversation.py` のパターン踏襲。リポジトリは `CRUDRepository` 継承。
- 新モデルは `app/models/__init__.py` と `alembic/env.py` の**両方**に登録してから
  `--autogenerate`。

次章(Phase 0-9)では、ここまでの設計をどうテストするか ── テスト戦略と
Docker 環境、そして Phase 1 への引き継ぎをまとめる。
