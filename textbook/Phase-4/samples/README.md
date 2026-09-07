# Phase 4 samples ── 実装の初期状態(単一の真実源)

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文(`Phase-4-*.md`)は要点の抜粋だけ、動くコードはここ。ユーザーはここから
`decitima-api/backend/app/` `tests/` `analysis/` と `decitima-ui/src/` へ **ファイル単位で写経・改変** する。

**Phase 4 = Route Planner のみ**。`network_design`(MST。Kruskal / Prim / Union-Find /
Network Designer ページ)は `textbook/Phase-5/samples/`。

**`samples/` に置くもの**:

- Phase 4 で **新規に作る** ファイル
- Phase 1 / 2 / 3 のファイルを Phase 4 が **書き換える** もの(現行版をここに置く)

**`samples/` に置かないもの**(既存テンプレートファイルへの追記 → 各章に差分で示す):

- backend: `app/algorithms/registry.py` / `pyproject.toml` / `decitima-api/README.md`
- ui: 追記系はすべて現行版を samples に同梱(`src/lib/api/types.ts` / `src/lib/menu-tree.ts`)

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `analysis/**` | `decitima-api/backend/analysis/**` |
| `ui/src/**` | `decitima-ui/src/**` |

## Phase 4 で作る / 変えるもの(作業単位)

| 単位 | samples の中心ファイル | 既存への変更 | 章 |
| --- | --- | --- | --- |
| 4-1 | `app/algorithms/graph/{adjacency,segments,waypoints}.py`、`app/algorithms/graph/{dijkstra,reachability}.py`(現行版)、`app/algorithms/optimization/brute_force.py`(現行版)、`tests/unit/test_graph_primitives.py`(adjacency + segments + waypoints + **dijkstra 統合スモーク**)、`tests/unit/test_dijkstra_strategy.py`(Phase 1 の現行版 ── docstring 追記のみ、公開挙動の回帰。#16) | ― | Phase-4-1 |
| 4-2 | `app/algorithms/graph/bellman_ford.py`、`app/domain/problems/route_planner.py`(現行版 = `allow_negative`)、`tests/unit/test_route_strategies.py`、`tests/fixtures/optimization.py`(現行版) | `registry.py`(BellmanFordStrategy) | Phase-4-2 |
| 4-3 | `app/algorithms/graph/a_star.py` | `registry.py`(AStarStrategy) | Phase-4-3 |
| 4-4 | `tests/unit/test_route_strategies.py`(経由順最適化セクションを追加。`waypoints.py` / `segments.py` は 4-1 で最終形) | ― | Phase-4-4 |
| 4-5 | `app/algorithms/graph/networkx_shortest.py`、`app/services/algorithm_selection.py`(現行版 = rule-based、route の分岐のみ) | `registry.py`(NetworkxShortestPath)、`pyproject.toml`(`networkx>=3.3`) | Phase-4-5 |
| 4-6 | `analysis/route_benchmark.py`、`analysis/plots.py`(現行版)、`analysis/README.md`(現行版)、`analysis/data/{.gitignore,sample_route_benchmark_runs.jsonl}`、`analysis/notebooks/route_benchmark.ipynb`、`tests/analysis/test_route_benchmark.py`、`tests/fixtures/optimization.py`(現行版 = `density`) | ― | Phase-4-6 |
| 4-7 | `ui: components/ui/charts/GraphCanvas.tsx` + `.test.tsx`、`lib/api/types.ts`(現行版 = route のみのユニオン)、`features/optimization/route-planner/api/route-planner.ts`、`features/optimization/route-planner/sample-problems.ts`、`features/optimization/components/ProblemJsonEditor.tsx` | ― | Phase-4-7 |
| 4-8 | `ui: features/optimization/route-planner/{stores,hooks,components}`、`app/(pages)/optimization/route-planner/page.tsx`、`lib/menu-tree.ts`(現行版 = route エントリ) | ― | Phase-4-8 |

## 既存テンプレートファイルへの追記(samples には含めない)

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `app/algorithms/registry.py` | Phase 4 の各 route strategy を import + リストに 1 行(4-2/4-3/4-5)。`"network_design"` キーは Phase 5-4 | 各章 §「registry の配線」 |
| `pyproject.toml` | `[project].dependencies` に `"networkx>=3.3"` → `uv sync`(runtime。`library:networkx` strategy は solve / benchmark のリクエスト経路で動く) | Phase-4-5 §1 |
| `decitima-api/README.md` | networkx 追加時の `uv sync` / Docker 再ビルド注記 | Phase-4-5 §1 |

## Phase 1 / 2 / 3 samples 側のマーカー(進行のルール #12)

Phase 4 / 5 が書き換えた以前の Phase のファイルは、以前の `samples/` 側にコード本体をそのまま残し
(スナップショット)、docstring 直後にマーカーを付けて現行版へ誘導する。詳細は各 Phase の
introduction「後続 Phase での改訂」節。`grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で一覧できる。

route 側(Phase 4 で書き換え):

- `Phase-1/samples/app/domain/problems/route_planner.py` ── `[以降 Phase で修正予定 ── Phase 4-2]`(`allow_negative` / `ge=0` 撤廃)
- `Phase-1/samples/app/algorithms/graph/dijkstra.py` ── `[以降 Phase で修正予定 ── Phase 4-1 / 4-4]`(`build_adjacency` 移設、`_waypoints` → `optimize_waypoint_order`)
- `Phase-1/samples/tests/unit/test_dijkstra_strategy.py` ── `[以降 Phase で修正予定 ── Phase 4-1]`(docstring に 4-1 の変更点を追記。アサーションは不変 ── 公開挙動が変わらないから。#16)
- `Phase-2/samples/app/algorithms/graph/reachability.py` ── `[以降 Phase で修正予定 ── Phase 4-1]`
- `Phase-3/samples/app/algorithms/optimization/brute_force.py` ── `[以降 Phase で修正予定 ── Phase 4-1]`(import 元変更)
- `Phase-3/samples/app/services/algorithm_selection.py` ── `[以降 Phase で修正予定 ── Phase 4-5]`(rule-based。network 分岐は Phase 5-3)
- `Phase-3/samples/tests/fixtures/optimization.py` ── `[以降 Phase で修正予定 ── Phase 4-2 / 4-6 / 5-3]`(`allow_negative` / `density` / network fixture)
- `Phase-3/samples/tests/unit/test_benchmark_service.py`・`tests/api/test_benchmark_api.py` ── `[以降 Phase で修正予定 ── Phase 4-2 / 5-3]`(登録 strategy 増加で entry 数が変わる)
- `Phase-3/samples/analysis/plots.py`・`analysis/README.md` ── `[以降 Phase で修正予定 ── Phase 4-6]`

network 側(Phase 5 で書き換え。詳細は `textbook/Phase-5/samples/README.md`):

- `Phase-1/samples/app/domain/problems/problem.py`・`solutions/solution.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`(ユニオンに `network_design`)
- `Phase-2/samples/app/domain/problems/semantic.py`・`solutions/structure.py`・`services/validation.py` ── `[以降 Phase で修正予定 ── Phase 5-3]`

## 検証(overlay)

### backend ── **Phase 3 end 状態**(現在の `decitima-api/backend` 作業ツリー)に重ねる

```bash
rsync -a --exclude '.venv' --exclude '.git' --exclude '__pycache__' decitima-api/backend/ <work>/
ln -s <abs>/decitima-api/backend/.venv <work>/.venv
rsync -a textbook/Phase-4/samples/app/      <work>/app/
rsync -a textbook/Phase-4/samples/tests/    <work>/tests/
rsync -a textbook/Phase-4/samples/analysis/ <work>/analysis/
#  + registry.py の Phase 4 route strategy import/登録(上表)
#  + pyproject.toml に "networkx>=3.3"
uv pip install --python .venv/bin/python 'networkx>=3.3'

uv run pytest                          # 183 passed, 2 deselected
uv run ruff check  --config pyproject.toml <phase 4 files>   # All checks passed
uv run ruff format --check --config pyproject.toml <phase 4 files>
uvx pyright app tests                  # Phase 4 分は 0 errors
DATABASE_URL="sqlite+aiosqlite:///./x.db" REDIS_URL=... JWT_SECRET_KEY=... \
  uv run alembic upgrade head          # no-op ── route は既存スキーマ、新テーブルなし
DATABASE_URL="sqlite+aiosqlite:///./x.db" ... MPLBACKEND=Agg PYTHONPATH=. \
  uv run --with jupyter --with nbconvert --with ipykernel \
  jupyter nbconvert --execute --to notebook --stdout analysis/notebooks/route_benchmark.ipynb
```

> 既知: `tests/unit/test_brute_force_strategy.py` に `test_deterministic_same_input_same_output` が
> **2 回定義**されており pyright が `reportRedeclaration` を 1 件出す。これは Phase 3 の写経時に
> 混入した重複で、**Phase 4 とは無関係**(Phase 3 samples 側は 1 回。写経先の当該 1 行を消せば解消)。

### ui ── decitima-ui に重ねる

```bash
rsync -a --exclude 'node_modules' --exclude '.next' --exclude '.git' decitima-ui/ <work-ui>/
ln -s <abs>/decitima-ui/node_modules <work-ui>/node_modules
rsync -a textbook/Phase-4/samples/ui/src/ <work-ui>/src/

npx tsc --noEmit                       # clean
npx vitest run src/features/optimization src/components/ui/charts/GraphCanvas.test.tsx
                                       # 13 passed(GraphCanvas 3 + route-planner store 4 + Phase 3 分)
npx eslint src/components/ui/charts src/features/optimization src/lib/api/types.ts \
  src/lib/menu-tree.ts 'src/app/(pages)/optimization'    # clean
```

(注: `src/components/layout/Menu.test.tsx` は Phase 3 以前から失敗しているテンプレートのテスト rot。
Phase 4 の変更とは無関係で件数は増えない。prettier はこのリポジトリの lint ゲートではない ── eslint のみ。)
