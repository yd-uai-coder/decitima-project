# textbook/samples ── 実装の初期状態（単一の真実源・全 Phase 共有）

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文（`textbook/Phase-<N>/Phase-<N>-<M>.md`）は要点の抜粋だけ、動くコードはここ。

**このフォルダは 1 つ・全 Phase で共有する**（旧方式: Phase 毎に `Phase-<N>/samples/` を全文生成していた）。各ファイルは
**最新 Phase の end 状態**（現在 = Phase 8 end）。ファイル冒頭のコメントに Phase の系譜を書く:

```
# DeciTima samples │ Phase 4              ← Phase 4 でのみ作成・変更
# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 4,6   ← Phase 1 で作成、4 と 6 で変更
# DeciTima samples │ Phase 7(7-2: knapsack_2d / 7-4: KnapsackDpTravelStrategy)  ← 1 Phase 内で章をまたぐ
```
単一章で完結する新規ファイルはモジュール docstring 1 行目に `作業単位 <N>-<M>`(テストと同じ)。

## 写経モデル ── end 状態のみ + 章が delta を語る

- サンプルは常に完成形。「Phase 3 の時点のスナップショット」は無い。
- 各 `Phase-<N>-introduction.md` の実装前チェックリストと各章冒頭の「この章で作成 / 更新するファイル」が
  「この Phase で何を写経するか」を案内し、章本文が「この Phase の変更行」を説明する。
- 章単位の孤立テスト実行はしない（検証は end 状態でまとめて回す）。
- 章 N が作る / 触るどのファイルも、import 先（モジュール **と** そのシンボル）がその章までに
  存在すること。新規ファイル・既存追記の別なく。end 状態では常に解決するので、写経を章順に進める
  利用者だけが前方 import を踏む（`from x import foo` で `x` はあるが `foo` が後の章、も前方 import。
  後の章で生まれるものへの import を含むファイル / 関数 / クラスは最初の消費者の章へ寄せる ── #15）。
- **Phase 7 以降の更新**は「旧コードをコメントアウト + 新コードを `# (Phase N-M)` タグ付きで追記」
  （進行のルール #12。`#` の後にスペース 1 個 ── `ruff format` が正規化する）。
  新規ファイルは冒頭コメントに生成 Phase。

```python
def score(...):
    # (Phase 6-3)
    # return weighted_sum(objectives, metrics)
    # (Phase 9-2) 正規化を挟む
    return weighted_sum(objectives, normalize(metrics, ranges))
```

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `alembic/**` | `decitima-api/backend/alembic/**` |
| `analysis/**` | `decitima-api/backend/analysis/**` |
| `scripts/**` | `decitima-api/backend/scripts/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `pyproject.toml` | `decitima-api/backend/pyproject.toml`（DeciTima が足した依存・ruff 設定のみ差分で写す） |
| `ui/src/**` | `decitima-ui/src/**` |

Phase 0 の設計スケッチ（`textbook/Phase-0/samples/` の 4 ファイル ── `problem_schema.py` 等の
フラットなスケッチ）は実装前の設計フェーズの成果物で、この共有フォルダとは別。整理の正はここ。

## 検証（overlay ── 1 回）

> **生成中は章ごとの部分実行**（`uv run pytest tests/unit/test_<当該章>.py`）で回し、下記の
> full overlay（343 テスト）は **Phase 完了時の 1〜2 回だけ**。`ruff` の scope は必ず
> `app tests analysis`（`textbook/samples/` 全体は `alembic/versions/*.py` を巻き込む）。
> 理由は `cl-development-retrospective.md` §2.5。

### backend

```bash
# clean base（decitima-api/backend HEAD）
git -C decitima-api archive HEAD backend | tar -x -C <work>
ln -s "$(pwd)/decitima-api/backend/.venv" <work>/.venv

# 共有 samples を 1 回重ねる（--delete は付けない ── テンプレート由来ファイルを消さない）
rsync -a textbook/samples/{app,tests,analysis,alembic,scripts}/ <work>/…/
cp textbook/samples/pyproject.toml <work>/pyproject.toml
uv pip install --python <work>/.venv/bin/python 'pandas>=2.2' 'matplotlib>=3.9'   # analysis 用

cd <work>
uv run pytest                                              # 405 passed / 4 deselected
uv run ruff check  --config <backend>/pyproject.toml app tests analysis   # samples は clean
uv run ruff format --check --config <backend>/pyproject.toml app tests analysis
uvx pyright app tests                                      # 0 errors
DATABASE_URL=sqlite+aiosqlite:///./_ov.db REDIS_URL=redis://x JWT_SECRET_KEY=x \
  uv run alembic upgrade head                              # 2b97… → c65b… → d4f1…
PYTHONPATH=$PWD uv run --with jupyter --with nbconvert --with ipykernel \
  jupyter nbconvert --to notebook --execute analysis/notebooks/*.ipynb   # 4 本完走
```

### ui

```bash
git -C decitima-ui archive HEAD | tar -x -C <work-ui>
ln -s "$(pwd)/decitima-ui/node_modules" <work-ui>/node_modules
rsync -a textbook/samples/ui/src/ <work-ui>/src/

cd <work-ui>
npx tsc --noEmit                                           # clean
npx vitest run src/features/optimization src/components/auth src/components/ui/charts   # 35 passed
npx eslint src/features/optimization src/components/auth src/components/ui/charts \
  'src/app/(pages)/optimization' 'src/app/(pages)/login' src/lib/api/types.ts src/lib/menu-tree.ts   # clean
```

（`alembic/versions/*.py` は backend の ruff `extend-exclude` 対象なので lint しない。
`decitima-api/backend` HEAD 自体の pre-existing lint 債務 ── `app/services/errors.py` 等 ──
は samples の対象外。`src/components/layout/Menu.test.tsx` の既存失敗も Phase 3 以前からのテンプレート rot。）

最終検証: 2026-09-10（Phase 8 ── Project Manager。`project_scheduling` を 5 つ目の problem_type
として配線。Topological Sort（DFS）/ Critical Path Method / RCPSP（priority_list + OR-Tools
CP-SAT）/ networkx オラクルを追加。`difference_array.range_add`（imos、Phase 6）を `resource_profile`
で再利用（無変更・2 人目の消費者）。依存 DAG の閉路検出を `validation.py` に（「計算 / 述語」の
4 例目）。UI に `project-planner` スライスと `GanttCanvas`（ドメイン非依存）。backend 405 passed /
ui 35 passed / alembic no-op）。

前回（2026-09-10、Phase 7 ── Travel Planner）: `travel_planning` を 4 つ目の problem_type として
配線、Floyd-Warshall / Knapsack DP / Greedy / BruteForce。backend 343 passed / ui 31 passed。
