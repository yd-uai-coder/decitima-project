# Phase 2 samples ── 実装の初期状態(単一の真実源)

`decitima-api/backend/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、教材本文
(`Phase-2-*.md`)は要点の抜粋だけ、動くコードはここ。ユーザーはここから
`decitima-api/backend/app/` と `tests/` へ **ファイル単位で写経・改変** する。

**`samples/` に置くもの**:
- Phase 2 で **新規に作る** ファイル
- Phase 1 のファイルを Phase 2 が **書き換える** もの(現行版をここに置く)

**`samples/` に置かないもの**:
- 既存テンプレートファイルへの追記(`app/core/config.py` / `app/api/routes/__init__.py`)
  → 各章に差分で示す

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `tests/**` | `decitima-api/backend/tests/**` |

## Phase 2 で作る / 変えるもの(作業単位)

| 単位 | samples の中心ファイル | 既存への変更 | 章 |
| --- | --- | --- | --- |
| 2-1 | ― | `app/domain/problems/shift_scheduler.py`(validator 3 つ。現行版を samples に同梱) | Phase-2-1 |
| 2-2 | `app/domain/problems/semantic.py` | `app/services/validation.py`(全面改訂・現行版同梱)、`tests/unit/test_validation_service.py` | Phase-2-2 |
| 2-3 | `app/domain/constraints/{__init__,forbidden,required_inclusion,numeric_bound,staffing}.py`、`app/domain/solutions/structure.py` | `app/services/verification.py`(全面改訂・現行版同梱)、`tests/unit/test_verification_service.py` | Phase-2-3 |
| 2-4 | (`structure.py` の `verify_shift_structure` 部分) | `tests/fixtures/optimization.py`(`build_shift_solution` 等・現行版同梱) | Phase-2-4 |
| 2-5 | `app/services/verify.py`、`app/api/routes/verify.py`、`tests/api/test_verify_api.py` | `app/schemas/optimization.py`(`Verify*` 追加・現行版同梱)、`app/core/config.py`、`app/api/routes/__init__.py` | Phase-2-5 |
| 2-6 | `tests/api/test_solve_invalid.py` | ― | Phase-2-6 |

## 既存テンプレートファイルへの追記(samples には含めない)

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `app/core/config.py` | `class Settings` に `VERIFY_RATE_LIMIT_PER_HOUR: int = 60` | Phase-2-5 §1 |
| `app/api/routes/__init__.py` | `verify_router` の import と `include_router` | Phase-2-5 §4 |

## Phase 1 samples 側の 「以降 Phase で修正予定」マーカー(進行のルール #12)

Phase 2 が書き換えた Phase 1 のファイルは、`textbook/Phase-1/samples/` 側にコード本体を
そのまま残し(スナップショット)、docstring 直後に
`# [以降 Phase で修正予定 ── Phase 2-N] … 現行版 textbook/Phase-2/samples/…` を付けてある:

- `app/services/validation.py` / `app/services/verification.py`
- `app/domain/problems/shift_scheduler.py`
- `tests/fixtures/optimization.py`
- `tests/unit/test_validation_service.py` / `tests/unit/test_verification_service.py`

`grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で全変更点を一覧できる。

## 検証(overlay)

samples は実 `app/` ツリー鏡写しで `from app...` / `from tests...` の絶対 import を使うため、
単体では import が解決しない。`decitima-api/backend` に **Phase 1 end 状態** を作り、その上に
Phase 2 samples を重ねて検証する:

```bash
# 1. クリーンな base(backend の git ルートは decitima-api/)
git -C decitima-api archive HEAD backend | tar -x -C <work>
cd <work>/backend && ln -s <path>/decitima-api/backend/.venv .venv

# 2. Phase 1 end 状態
rsync -a <repo>/textbook/Phase-1/samples/app/   app/
rsync -a <repo>/textbook/Phase-1/samples/tests/ tests/
#    + Phase 1 の既存ファイル追記(errors.py 4 クラス / models/__init__ / alembic/env.py /
#      config.py の SOLVE_* / api/routes/__init__.py の 3 ルーター)
#    + registry.py の DijkstraStrategy 行 2 箇所のコメント解除

# 3. Phase 2 を重ねる
rsync -a <repo>/textbook/Phase-2/samples/app/   app/
rsync -a <repo>/textbook/Phase-2/samples/tests/ tests/
#    + config.py に VERIFY_RATE_LIMIT_PER_HOUR
#    + api/routes/__init__.py に verify_router

# 4. 実行
uv run pytest                       # 121 passed, 3 deselected
uv run ruff check app tests         # All checks passed
uv run ruff format --check app tests
uvx pyright app tests               # 0 errors
```

型注意(`decitima-api/CLAUDE.md`): pyright standard。`ConstraintChecker` /
`SemanticCheck` の型エイリアスは PEP 695 `type` 文。`NumericBoundConstraint` のフィールドは
`operator`(stdlib と被るが `from operator import le, ...` で関数を名前 import すれば衝突しない)。
