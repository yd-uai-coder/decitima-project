# Phase 1 samples ── 実装の初期状態(単一の真実源)

このディレクトリは **`decitima-api/backend/` に重ねる前提** の実装スケッチです。
進行のルール #3 のとおり、教材本文(`Phase-1-*.md`)は要点の抜粋だけを載せ、
動くコードはここにあります。ユーザーはここから `decitima-api/backend/app/` と
`decitima-api/backend/tests/` へ **ファイル単位で写経・改変** して実装します。

**`samples/` には Phase 1 で新規に作るファイルだけを置いています。**
既存 `decitima-api` ファイルへの追記(下表の 5 ファイル)は samples に入れず、各章に差分として
示しています。

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `alembic/versions/*.py` | `decitima-api/backend/alembic/versions/`(実際は autogenerate。§下記) |

## 既存ファイルへの追記(samples には含めない)

これらは既にリポジトリにあるファイル。追記内容は各章を参照:

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `app/services/errors.py` | `from typing import ClassVar` / `AppError`・`BadRequestError` の import / 末尾に `ProblemValidationError`・`InfeasibleProblemError`・`NoAlgorithmError`・`SolveTimeoutError` の 4 クラス | Phase-1-2 §4 |
| `app/models/__init__.py` | `from app.models.optimization import Problem, Solution` / `__all__` に `Problem`, `Solution` | Phase-1-5 §3 |
| `alembic/env.py` | モデル登録の import 行に `Problem, Solution` を追加 | Phase-1-5 §3 |
| `app/core/config.py` | `class Settings` に `SOLVE_RATE_LIMIT_PER_HOUR` / `SOLVE_RATE_LIMIT_PER_DAY` / `SOLVE_TIMEOUT_SECONDS` | Phase-1-6 §1 |
| `app/api/routes/__init__.py` | `solve` / `algorithms` / `solutions` ルーターの import と `include_router` | Phase-1-7 §3 |

`alembic/env.py` の変更(参考):

```python
# 変更前
from app.models import Conversation, Message, User  # noqa: F401
# 変更後
from app.models import Conversation, Message, Problem, Solution, User  # noqa: F401
```

## 検証

samples は decitima-api の実ツリーに重ねて検証しています(絶対 import `from app...` /
`from tests...` がそのまま解決する)。手元で追試するなら:

```bash
# 1. decitima-api/backend を複製(.venv は除外、シンボリックリンクで流用)
# 2. samples/{app,tests,alembic/versions} を複製に重ねる
# 3. 上表の 5 ファイルのうち config / errors / models/__init__ / api/routes/__init__ の
#    4 点の追記を複製側に適用する(これらは samples に無いため)
# 4. 複製ディレクトリで:
uv run pytest                       # 89 passed, 3 deselected(integration は既定で除外)
uv run ruff check app tests         # All checks passed
uv run ruff format --check app tests
uvx pyright app tests               # 0 errors(app/ai 等テンプレ既知債務は pyproject で ignore 済み)
```

`tests/integration/test_optimization_persistence.py` は実 PostgreSQL が必要
(`docker compose up postgres` → `uv run pytest -m integration`)。教材生成時は未実行。

## alembic マイグレーション

`alembic/versions/a1b2c3d4e5f6_add_problems_and_solutions.py` は
`uv run alembic revision --autogenerate -m "add problems and solutions tables"` の出力を
既存 `2b97c8ec8533_initial_schema.py` のスタイルに整えたもの。実際は自分の環境で
autogenerate し、生成物がこれと同等か目視確認してから `uv run alembic upgrade head`。
`revision` 文字列は生成物の値を使う。

## Phase 1 で作るもの(作業単位)

| 単位 | samples の中心ファイル(新規) | 既存ファイルへの追記 | 章 |
| --- | --- | --- | --- |
| 1-1 | `app/domain/problems/**`, `app/domain/solutions/**` | ― | Phase-1-1 |
| 1-2 | `app/algorithms/base.py`, `app/algorithms/registry.py`, `app/services/algorithm_selection.py` | `app/services/errors.py` | Phase-1-2 |
| 1-3 | `app/algorithms/search/{linear_search,binary_search,bfs,dfs}.py` | ― | Phase-1-3 |
| 1-4 | `app/algorithms/graph/dijkstra.py` | ― | Phase-1-4 |
| 1-5 | `app/models/optimization.py`, `app/repositories/optimization.py`, `alembic/versions/*.py` | `app/models/__init__.py`, `alembic/env.py` | Phase-1-5 |
| 1-6 | `app/services/{validation,verification,solve}.py`, `app/schemas/optimization.py`, `app/api/routes/solve.py` | `app/core/config.py` | Phase-1-6 |
| 1-7 | `app/services/optimization_read.py`, `app/api/routes/{algorithms,solutions}.py` | `app/api/routes/__init__.py` | Phase-1-7 |

`app/domain/objectives/`(多目的の重み付き和の評価器)は Phase 1 では作らない ── Phase 1 で
registry に載る `DijkstraStrategy` は単一目的で消費者がいないため。Phase 5(Shift Scheduler)で追加。
