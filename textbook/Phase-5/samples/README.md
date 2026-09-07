# Phase 5 samples ── 実装の初期状態(単一の真実源)

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文(`Phase-5-*.md`)は要点の抜粋だけ、動くコードはここ。

**Phase 5 = Network Designer(最小全域木)**。Route Planner は `textbook/Phase-4/samples/`。
Phase 5 は **Phase 4 end 状態の上に重ねる**。

**`samples/` に置くもの**:

- Phase 5 で **新規に作る** ファイル(`union_find` / `connectivity` / `mst` / `kruskal` / `prim` /
  `networkx_mst` / `network_design`(problems・solutions)/ network-designer UI 一式)
- Phase 1〜4 のファイルを Phase 5 が **書き換える** もの(現行版 = network アームを含む full 版):
  `domain/problems/{problem,__init__,semantic}.py` / `domain/solutions/{solution,structure}.py` /
  `domain/constraints/{forbidden,required_inclusion}.py` / `algorithms/graph/adjacency.py`
  (`build_link_adjacency` 追加)/ `services/{validation,verification,algorithm_selection}.py` /
  `tests/fixtures/optimization.py` / `tests/unit/{test_benchmark_service,test_algorithm_selection}.py` /
  `tests/unit/test_graph_primitives.py`(Phase 4-1 の route プリミティブテスト + 5-3 で network 4 本を追記) /
  `tests/api/test_benchmark_api.py` / `ui/src/lib/{api/types.ts,menu-tree.ts}`

**`samples/` に置かないもの**(既存テンプレートファイルへの追記 → 各章に差分で示す):

- backend: `app/algorithms/registry.py`(`"network_design"` キー + 3 本)

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `ui/src/**` | `decitima-ui/src/**` |

## Phase 5 で作る / 変えるもの(作業単位)

| 単位 | samples の中心ファイル | 既存への変更 | 章 |
| --- | --- | --- | --- |
| 5-1 | `app/algorithms/graph/union_find.py`、`tests/unit/test_union_find.py` | ― | Phase-5-1 |
| 5-2 | ── (理論章 ── samples なし。cut / cycle property の実測テストと network fixture は 5-3) | ― | Phase-5-2 |
| 5-3 | `app/domain/problems/network_design.py`、`app/domain/solutions/network_design.py`、`app/algorithms/graph/connectivity.py`、`app/algorithms/graph/adjacency.py`(現行版 = `build_link_adjacency`)、`app/domain/problems/{problem,__init__,semantic}.py`(現行版)、`app/domain/solutions/{solution,structure}.py`(現行版)、`app/domain/constraints/{forbidden,required_inclusion}.py`(現行版)、`app/services/{validation,verification,algorithm_selection}.py`(現行版)、`tests/fixtures/optimization.py`(現行版 = network fixture)、`tests/unit/{test_network_design,test_mst_properties,test_graph_primitives}.py` | ― | Phase-5-3 |
| 5-4 | `app/algorithms/graph/{mst,kruskal,prim,networkx_mst}.py`、`tests/unit/{test_mst_strategies,test_algorithm_selection}.py`(`test_mst_strategies` に 5-3 から移設した end-to-end パイプラインテストを含む)、`tests/unit/test_benchmark_service.py`(現行版)、`tests/api/test_benchmark_api.py`(現行版) | `registry.py`(`"network_design"` キー + 3 本) | Phase-5-4 |
| 5-5 | `ui: features/optimization/network-designer/{api,stores,hooks,components,sample-problems.ts}`、`app/(pages)/optimization/network-designer/page.tsx`、`lib/api/types.ts`(現行版 = network アーム)、`lib/menu-tree.ts`(現行版 = network エントリ) | ― | Phase-5-5 |

## 既存テンプレートファイルへの追記(samples には含めない)

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `app/algorithms/registry.py` | `"network_design": [KruskalStrategy(), PrimStrategy(), NetworkxMST()]` キーを新設(5-3 でコメントアウト状態、5-4 で有効化) | Phase-5-3 §3 / Phase-5-4 §5 |

## Phase 1 / 2 samples 側のマーカー(進行のルール #12)

Phase 5 が判別ユニオンを 3 メンバーにする分:

- `Phase-1/samples/app/domain/problems/problem.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`(ユニオンに `network_design`)
- `Phase-1/samples/app/domain/solutions/solution.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`
- `Phase-2/samples/app/domain/problems/semantic.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`
- `Phase-2/samples/app/domain/solutions/structure.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`
- `Phase-2/samples/app/services/validation.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`
- `Phase-3/samples/tests/fixtures/optimization.py` ── `[以降 Phase で修正予定 ── Phase 4-2 / 4-6 / 5-3]`(network fixture 部分)
- `Phase-3/samples/tests/unit/test_benchmark_service.py`・`tests/api/test_benchmark_api.py` ── `[以降 Phase で修正予定 ── Phase 4-2 / 5-3]`(network_design の entry 追加)

`grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で一覧できる。

## 検証(overlay)

### backend ── **Phase 4 end 状態**の上に重ねる

```bash
# 1. クリーン base(Phase 3 end)を取り、Phase 4 samples を重ねて「Phase 4 end 状態」を作る
rsync -a --exclude '.venv' --exclude '.git' --exclude '__pycache__' decitima-api/backend/ <work>/
ln -s <abs>/decitima-api/backend/.venv <work>/.venv
rsync -a textbook/Phase-4/samples/app/ textbook/Phase-4/samples/tests/ textbook/Phase-4/samples/analysis/ <work>/...
#  + Phase 4 の registry.py route strategy / pyproject の networkx
uv pip install --python .venv/bin/python 'networkx>=3.3'

# 2. その上に Phase 5 samples を重ねる
rsync -a textbook/Phase-5/samples/app/   <work>/app/
rsync -a textbook/Phase-5/samples/tests/ <work>/tests/
#  + registry.py に "network_design" キー(KruskalStrategy / PrimStrategy / NetworkxMST)

uv run pytest                          # 217 passed, 2 deselected  (analysis 6 本込み)
uv run ruff check  --config pyproject.toml <phase 5 files>   # All checks passed
uv run ruff format --check --config pyproject.toml <phase 5 files>
uvx pyright app tests                  # Phase 5 分は 0 errors
DATABASE_URL="sqlite+aiosqlite:///./x.db" REDIS_URL=... JWT_SECRET_KEY=... \
  uv run alembic upgrade head          # no-op ── network_design は JSONB payload、新テーブルなし
```

> 既知(Phase 4 と同じ): 写経先の `tests/unit/test_brute_force_strategy.py` に
> `test_deterministic_same_input_same_output` が 2 回定義されていると pyright が 1 件出す。
> Phase 5 とは無関係(samples 側は 1 回)。Phase 5 の clean な `problem.py` を重ねると、
> 写経先の `ForbiddenConstraint` 二重定義(Phase 1 写経時の混入)は解消される。

### ui ── decitima-ui に重ねる

```bash
rsync -a --exclude 'node_modules' --exclude '.next' --exclude '.git' decitima-ui/ <work-ui>/
ln -s <abs>/decitima-ui/node_modules <work-ui>/node_modules
rsync -a textbook/Phase-4/samples/ui/src/ <work-ui>/src/    # Phase 4 UI end 状態
rsync -a textbook/Phase-5/samples/ui/src/ <work-ui>/src/    # network アーム / network-designer

npx tsc --noEmit                       # clean
npx vitest run src/features/optimization   # 16 passed(route-planner 4 + network-designer 3 + GraphCanvas 3 + Phase 3 分)
npx eslint src/features/optimization src/lib/api/types.ts src/lib/menu-tree.ts \
  'src/app/(pages)/optimization'        # clean
```

(注: `src/components/layout/Menu.test.tsx` は Phase 3 以前から失敗しているテンプレートのテスト rot。
Phase 5 の変更とは無関係で件数は増えない。)
