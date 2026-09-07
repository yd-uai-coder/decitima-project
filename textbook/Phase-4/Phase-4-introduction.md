# Phase 4 — Route Planner(実装フェーズ)導入

作業章(`Phase-4-1.md` 以降)を始める前に、この 1 本で Phase 4 の全体像を掴む。
目的 / パイプライン上の位置 / グラフアルゴリズムの 2 層 / 進め方 / テスト / スコープ /
章一覧 / 実装前チェックリスト。

**Phase 4 と Phase 5 の分割について**: 当初 Phase 4 は Route Planner と Network Designer を
1 フェーズで扱う 11 章構成だったが、README §12 が両者を同格の製品機能として並べていること /
章数・ファイル数が他フェーズの倍近いこと / CL 開発の「小さく予測可能な単位」方針(`CLAUDE.md`
の重点課題)から、**Phase 4 = Route Planner(8 章)/ Phase 5 = Network Designer(5 章)** に
分けた。実装の順序は変わらない ── グラフプリミティブ → Bellman-Ford → A* → 経由順 → networkx
→(Phase 5)MST 配線 → Kruskal/Prim → UI。MVP は **Phase 0〜6**(Route Planner /
Network Designer / Shift Scheduler + 基盤)。

## 1. このフェーズの目的

Phase 1 で「決定論的に**計算できる**」、Phase 2 で「解が制約を満たすか**検証できる**」、
Phase 3 で「複数アルゴリズムを**測って比べられる**」土台が揃った。Phase 4 はその上に
**最初の実ドメインの深掘り**を載せる ── README §12.1 Route Planner。

README §19 の Phase 順序・原則 2 がこのフェーズの定義:

> **4 Route Planner**: Graph Model / Bellman-Ford / A* / 経路可視化 ── **最初の実ドメイン**。
> Phase 1 のグラフ資産を最大限再利用 ── 新パラダイムでなく「グラフの深掘り」。
> 制約はほぼ hard のみ、解は経路(列)で可視化・検証も素直。

**なぜ Shift(Phase 6)より先か**: route_planning は Phase 1 でスキーマもグラフ資産
(`DijkstraStrategy` / `build_adjacency` / BFS プリミティブ)も凍結済み。新しいアルゴリズムを
足すだけで済み、registry に載せれば Phase 3 のベンチにそのまま乗る。Shift は探索が本質的に
指数時間で「手実装の破綻 → OR-Tools への切り替え」という別の重い話になる。

Phase 4 で新しく入るもの:

| 新規                                                                            | 中身                                                                                               |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **グラフプリミティブの整理** `algorithms/graph/{adjacency,segments,waypoints}.py`         | `build_adjacency` を `dijkstra.py` から抽出。route 3 strategy の共通足回り                                   |
| **Bellman-Ford** `graph/bellman_ford.py`                                      | 負辺 OK・負閉路検出。`RouteEdge.weight` の `ge=0` を外し `RouteData.allow_negative` を追加                       |
| **A*** `graph/a_star.py`                                                      | `RouteNode.x/y` からユークリッド距離ヒューリスティック。可容なら最適性は保たれ、探索が減る                                            |
| **経由順の最適化** `graph/waypoints.py`                                              | 2 点以上の必須経由 = 小さな TSP。m ≤ 8 は順列全探索                                                                |
| **networkx トラック** `graph/networkx_shortest.py` + `rule-based select_strategy` | 手実装 Dijkstra の別実装オラクル兼「手実装 vs ライブラリ」比較の 2 本目。問題特性で使うアルゴリズムを自動選択(route の分岐のみ)                     |
| **Route Benchmark 分析** `analysis/route_benchmark.py`                          | Phase 3-8 の `analysis/` に 1 モジュール追加。「手実装が networkx に負ける size」                                    |
| **グラフ図** `ui: components/ui/charts/GraphCanvas.tsx`                           | 手描き SVG(ノード / エッジ / 経路ハイライト)。本格ライブラリは入れない(Phase 4 で確定)。ドメイン非依存なので Phase 5 の Network Designer も使う |
| **Route Planner ページ**(decitima-ui)                                            | 初の `src/features/optimization/route-planner/`                                                    |

`network_design`(MST。Kruskal / Prim / Union-Find / Network Designer ページ)は **Phase 5**。

---

## 2. パイプライン上の位置 ── 専用エンドポイントは作らない

Phase 1 で決めたとおり(`Phase-0-7.md`)、route は **`POST /api/v1/solve` に `problem_type`
付きの `OptimizationProblem` を渡すだけ**。サービス層は「registry を回すオーケストレーション」
なので、Bellman-Ford / A* / networkx を足しても route / verify / benchmark のルート・サービスは
**変更ゼロ**で通る(registry に append するだけ)。

`RouteData` にフィールドを 1 つ足す(`allow_negative`)以外、スキーマも DB も無変更。
`alembic upgrade head` は Phase 4 で **no-op**。

---

## 3. グラフアルゴリズムの 2 層(`Phase-0-4.md` §2.4 の再確認)

|         | AlgorithmStrategy(registry に載る)                                  | アルゴリズム・プリミティブ(載らない)                                                                                                  |
| ------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Phase 4 | `BellmanFordStrategy` / `AStarStrategy` / `NetworkxShortestPath` | `build_adjacency` / `plain_adjacency` / `has_negative_weight` / `optimize_waypoint_order` / `Segment` + `plan_route` + `reconstruct_path` |
| シグネチャ   | `solve(problem) -> CandidateSolution` に統一                        | それぞれ自然な形。`solve` の中や別の計算から呼ばれて初めて意味を持つ                                                                               |
| 例       | `AStarStrategy.solve()` が…                                       | …`plan_route`(共通足回り)を内部で使う                                                                                           |

route の 3 strategy(Dijkstra / Bellman-Ford / A*)は「区間の最短経路の求め方」だけが違い、
「制約集め → 隣接リスト → 経由順を決めて区間ごとに解いて連結 → CandidateSolution」は同じ。
その共通部分を `graph/segments.py`(`Segment` / `plan_route` / `route_solution` /
`reconstruct_path` ── 経路復元は 3 strategy で 1 文字も変わらないので公開関数に)に集約する。

**`_ops` の扱い**(`Phase-0-5.md` §4 / Phase 3 で確定): 各手実装 strategy は「内部の仕事量」を
`metrics["_ops"]` に積む(Dijkstra / A* = heap pop 数、Bellman-Ford = 緩和回数)。
**単位がアルゴリズムごとに違うので割り算しない**。`library:networkx` の strategy は
仕事が C の中なので `_ops` を出せない ── これ自体が「手実装 vs 産業ソルバー」比較の論点
(`Phase-0-9.md` Q19)。

> **Union-Find は Phase 5**: `network_design` の Kruskal が唯一の実消費者なので、`union_find.py`
> は Phase 5-1 で深掘りする(2 層の下側のプリミティブ)。

---

## 4. 章一覧(章 = 作業単位)

`Phase-4-M.md` = 作業単位 4-M。依存の薄い 4-1 から着手できる。

| 章                           | トピック                                             | 依存       | 主な内容                                                                                                                                   |
| --------------------------- | ------------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-4-1](./Phase-4-1.md) | グラフプリミティブの整理                                     | ―        | `graph/{adjacency,segments,waypoints}.py`。`dijkstra` / `reachability` / `brute_force` の import 元を `adjacency` へ                        |
| [Phase-4-2](./Phase-4-2.md) | 負の重み(スキーマ変更)+ Bellman-Ford                       | 4-1      | `RouteData.allow_negative` + `model_validator`。`graph/bellman_ford.py`。registry 登録。Dijkstra/A* の負辺ガード                                  |
| [Phase-4-3](./Phase-4-3.md) | A* とヒューリスティック探索                                  | 4-1      | `graph/a_star.py`。可容性の説明(不可容だと非最適 ── わざと赤で確認)                                                                                          |
| [Phase-4-4](./Phase-4-4.md) | 複数必須経由地の順序最適化(小 TSP)                             | 4-2, 4-3 | `graph/waypoints.py` の `optimize_waypoint_order`。`segments.plan_route` に配線                                                             |
| [Phase-4-5](./Phase-4-5.md) | networkx トラック + 検証オラクル + rule-based 選択           | 4-2, 4-3 | `graph/networkx_shortest.py`。`services/algorithm_selection.py` の rule-based 化(route のみ)。`pyproject` に `networkx`                       |
| [Phase-4-6](./Phase-4-6.md) | Route Benchmark 分析(`analysis/` を育てる)             | 4-2〜4-5  | `analysis/route_benchmark.py` + notebook。`build_scaled_route_problem` に `density`                                                      |
| [Phase-4-7](./Phase-4-7.md) | グラフ描画基盤 `GraphCanvas` + solve API 層(decitima-ui) | ―        | `components/ui/charts/GraphCanvas.tsx`、`lib/api/types.ts`(route のみのユニオン)、`features/optimization/route-planner/api`、`ProblemJsonEditor` |
| [Phase-4-8](./Phase-4-8.md) | Route Planner ページ(decitima-ui)                   | 4-7      | `route-planner/{stores,hooks,components}`、`app/(pages)/optimization/route-planner/page.tsx`、`lib/menu-tree.ts`                         |

4-1〜4-6 が decitima-api、4-7〜4-8 が decitima-ui。4-6 は 4-2〜4-5 のアルゴリズムが
registry に載っていることに依存するが UI とは独立。UI は 4-7(共有の `GraphCanvas` + api 層)を
先に作り、4-8 がそれを消費する。

registry を「集約モジュール」として育てる作法(進行のルール #15): 4-1 の時点では
`bellman_ford` / `a_star` / `networkx_shortest` はまだ無いので、`registry.py` の該当
import・登録行はコメントアウトのまま。各 strategy を作る章でコメントを外し、その章が
「registry から引ける」テストを持つ。フル検証は Phase 末の end 状態(全コメント解除)で回す。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1 / 2 / 3 と同じ)

1. 章(`Phase-4-*.md`)は **要点の抜粋** だけ。動くコードは `samples/`(実 `app/` `src/` ツリー
   鏡写し + 絶対 import)。
2. `samples/app/**` → `decitima-api/backend/app/**`、`samples/analysis/**` → `.../analysis/**`、
   `samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
3. `samples/` には **Phase 4 で新規に作るファイル**と、**Phase 1 / 2 / 3 のファイルを Phase 4 が
   書き換えるもの**(現行版)。既存テンプレートへの追記(`registry.py` / `pyproject.toml`)は
   各章に差分で示す。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる。

```text
textbook/Phase-4/
├── Phase-4-introduction.md   この導入
├── Phase-4-1.md 〜 4-8.md     各作業単位の解説
└── samples/
    ├── README.md             写経の対応表・overlay 検証手順(backend + ui)
    ├── app/**                → decitima-api/backend/app/**
    ├── tests/**              → decitima-api/backend/tests/**
    ├── analysis/**           → decitima-api/backend/analysis/**
    └── ui/src/**             → decitima-ui/src/**
```

**着手前に §10 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル                             | 使うもの                              | Phase 4 で書くもの                                                      |
| ------------------------------- | --------------------------------- | ------------------------------------------------------------------ |
| algorithms / primitives(純粋・主戦場) | 素の pytest。DB 不要                   | `adjacency` / `optimize_waypoint_order` / 各 route strategy         |
| domain(純粋)                      | 素の pytest                         | `RouteData.allow_negative` のラウンドトリップ / `model_validator`           |
| サービス層                           | `db_session`(SQLite)+ `FakeRedis` | `BenchmarkService`(entry 数が増える)/ `select_strategy` の rule-based 分岐 |
| API                             | `httpx.AsyncClient` + 依存差し替え      | `POST /benchmark` の route ケース(entry 数)                             |
| 分析                              | 素の pytest。固定サンプル JSONL            | `route_benchmark` の純粋関数 / `plots` スモーク                             |
| UI                              | Vitest + jsdom / node env         | `GraphCanvas` / route-planner store                                |

各 strategy・各プリミティブ・`analysis/route_benchmark` は**純粋**なのでスタブ不要 ──
これが「純粋レイヤー」設計(`Phase-0-3.md`)の帰結で、各章のテスト観点で毎回確認する。
`networkx` を使う strategy も**決定論的**なのでスタブ不要(外部プロセスもネットワークも無い)。

**写経ミスの番人**(進行のルール #15 / #16): 4-1 は 3 ファイル新規 + `dijkstra.py` を大きく
リファクタする(共通処理を `segments.py` へ委譲)。
- `test_graph_primitives.py`(章の第一テスト)── `segments` → `waypoints` と import を辿るので
  **写経漏れで collection が赤**。加えて `DijkstraStrategy().solve()` の**統合スモーク**を持ち、
  `_dijkstra_segment` の末尾の写経ミス(`TypeError: cannot unpack non-iterable NoneType object`)を
  その場で赤にする。
- `test_dijkstra_strategy.py`(Phase 1、写経後に再実行)── **公開挙動の回帰**。挙動は不変なので緑。
  赤なら同じく写経ミス(#16 の補助の番人)。

```bash
# decitima-api/backend(overlay end 状態)で
uv run pytest      # 183 passed, 2 deselected
# decitima-ui で
npx vitest run src/features/optimization src/components/ui/charts/GraphCanvas.test.tsx   # 13 passed
```

---

## 7. Phase 4 のスコープと非スコープ

| Phase 4 でやる                                                                | 送る先                                                                                                                  |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Bellman-Ford(負辺・負閉路)/ A*(座標ヒューリスティック)/ 経由順最適化(小 TSP)                       | ―                                                                                                                    |
| networkx を産業ソルバートラック兼オラクルとして導入 + rule-based の `select_strategy`(route の分岐) | 学習型のアルゴリズム選択(Phase 12。Phase 3 / 4 はデータを貯めるだけ)                                                                        |
| 経路図は**手描き SVG**(`GraphCanvas`)で対応。**本格ライブラリは入れない**(Phase 4 で確定)            | ―                                                                                                                    |
| Route Planner の入力 UI は**サンプル選択 + JSON テキストエリア**                            | リッチな作図エディタ(ノードをドラッグで配置 等)── 需要が出たら別 Phase                                                                            |
| `analysis/route_benchmark.py`(size / density 別の集計)                         | Phase 6 の `shift_analysis.py`、Phase 14 の実験フレームワーク                                                                    |
| ―                                                                          | **`network_design`(MST)/ Kruskal / Prim / Union-Find / Network Designer ページ**は Phase 5                               |
| ―                                                                          | **Floyd-Warshall(全点対距離)は Phase 7**(Travel Planner が前処理に使うプリミティブ)。TSP の近似も Phase 7                                    |
| ―                                                                          | **shift への全探索オラクル**(README §8「随時」。Phase 6)                                                                           |
| ―                                                                          | **CSR 行列ビルダー**(`to_csr`)── scipy を足す Phase まで遅延(`appendix/library-fork-impact.md` フック①)。`adjacency.py` に抽出済みなので追加は容易 |

**負辺のデモは有向グラフで作る** ── 無向グラフに負辺があると a→b→a で無限に下がる(= 即・負閉路)。
Bellman-Ford の「負閉路検出」を見せたいなら有向の閉路にする。

---

## 8. サンプルコード(`samples/`)

| 場所                                                                                               | 内容                                                                                                                      |
| ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `app/algorithms/graph/adjacency.py`                                                              | `build_adjacency` / `plain_adjacency` / `has_negative_weight`(新規。`dijkstra.py` から移設。`build_link_adjacency` は Phase 5-3) |
| `app/algorithms/graph/segments.py`                                                               | `Segment` / `plan_route` / `collect_route_constraints` / `route_solution` / `reconstruct_path`(新規。route 3 strategy の共通足回り)  |
| `app/algorithms/graph/waypoints.py`                                                              | `optimize_waypoint_order`(新規。骨格を 4-1、2 点以上の必須経由の全順列最適化の深掘りは 4-4)                                                       |
| `app/algorithms/graph/{bellman_ford,a_star}.py`                                                  | route strategy(新規)                                                                                                      |
| `app/algorithms/graph/networkx_shortest.py`                                                      | `library:networkx` トラック(新規)                                                                                             |
| `app/algorithms/graph/{dijkstra,reachability}.py` / `app/algorithms/optimization/brute_force.py` | 現行版(`build_adjacency` の import 元変更、Dijkstra は `segments` 経由に)                                                           |
| `app/domain/problems/route_planner.py`                                                           | 現行版(`allow_negative` / `weight` の `ge=0` 撤廃)                                                                            |
| `app/services/algorithm_selection.py`                                                            | 現行版(rule-based。route の分岐のみ。network 分岐は Phase 5-3)                                                                       |
| `analysis/route_benchmark.py` / `analysis/{plots,README}`                                        | Route Benchmark 集計(新規)+ 現行版                                                                                             |
| `analysis/data/sample_route_benchmark_runs.jsonl` / `notebooks/route_benchmark.ipynb`            | 固定サンプル + notebook(新規)                                                                                                   |
| `tests/**`                                                                                       | 各プリミティブ / route strategy / 分析 / UI のテスト。`test_benchmark_service.py`・`test_benchmark_api.py` は現行版                        |
| `tests/fixtures/optimization.py`                                                                 | 現行版(`allow_negative` / `density`。network fixture は Phase 5-3)                                                           |
| `ui/src/components/ui/charts/GraphCanvas.tsx`                                                    | 手描き SVG のグラフ描画(新規。還元候補)                                                                                                 |
| `ui/src/lib/api/types.ts` / `ui/src/lib/menu-tree.ts`                                            | 現行版(route DTO + route のみのユニオン / メニューに route エントリ)                                                                       |
| `ui/src/features/optimization/route-planner/**`                                                  | api / stores / hooks / components / sample-problems(新規)                                                                 |
| `ui/src/features/optimization/components/ProblemJsonEditor.tsx`                                  | 問題を JSON で編集する共有エディタ(新規)                                                                                                |
| `ui/src/app/(pages)/optimization/route-planner/page.tsx`                                         | ページ(`RequireAuth` で包む。新規)                                                                                               |

既存ファイルへの追記(samples に含めない、各章に差分):
`app/algorithms/registry.py`(Phase 4 route strategy)、`pyproject.toml`(`networkx>=3.3`)、`decitima-api/README.md`。

検証: `decitima-api/backend`(Phase 3 end 状態)に Phase 4 samples を overlay し
`uv pip install 'networkx>=3.3'` → `uv run pytest`(**183 passed, 2 deselected**)/ `ruff` /
`uvx pyright`(Phase 4 分 0 errors)/ `alembic upgrade head`(no-op)/ notebook 実行。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(**13 passed**)/ `npx eslint`。
手順は `samples/README.md`。

---

## 9. Phase 4 の成果物

- **textbook**: この `Phase-4/` 一式(導入 + `Phase-4-1`〜`4-8` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/algorithms/graph/**` の新規 5 ファイル /
  `app/domain/problems/route_planner.py`(`allow_negative`)/ `app/services/algorithm_selection.py` /
  `analysis/route_benchmark.py` + notebook / `tests/**` / `registry.py`・`pyproject.toml` への追記
- **decitima-ui の実装**(ユーザーが写経): `src/components/ui/charts/GraphCanvas.tsx` /
  `src/features/optimization/route-planner/**` + `components/ProblemJsonEditor.tsx` /
  `src/app/(pages)/optimization/route-planner/page.tsx` /
  `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版 = route のみ)
- **Phase 0 / 1 / 2 / 3 教材への「以降 Phase で修正予定」/「で確定」マーカー**
- **ルート `CLAUDE.md` の Notes**: Phase 4(Route)の設計決定 + 質問ログ Q27(スコープ相談)/
  Q29(Phase 4 / 5 分割の相談)。`decitima-api/CLAUDE.md` / `decitima-ui/CLAUDE.md` にも節を追加

---

## 10. Phase 4 実装前チェックリスト

進行のルール #11。教材生成後・実装着手前に、ここで疑問を出し切る。行 `4-M` ↔ 章 `Phase-4-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                            | 主なクラス・関数の責務(1 行)                                                                                                                                                                             |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4-1 | `graph/adjacency.py`・`graph/segments.py`・`graph/waypoints.py`(新規)、`graph/{dijkstra,reachability}.py`・`optimization/brute_force.py`(現行版)、`tests/unit/{test_graph_primitives,test_dijkstra_strategy}.py` | `build_adjacency`(RouteData → 重み付き隣接)/ `plain_adjacency` / `has_negative_weight` / `Segment` + `plan_route`(区間を経由順に解いて連結)/ `reconstruct_path`(3 strategy 共通の経路復元)は segments.py、`_dijkstra_segment` は dijkstra.py。`test_dijkstra_strategy.py`(Phase 1)を再実行(#16) |
| 4-2 | `graph/bellman_ford.py`(新規)、`domain/problems/route_planner.py`・`tests/fixtures/optimization.py`(現行版)                                                                                    | `RouteData.allow_negative` + `_guard_negative_weights`(False で負辺なら ValidationError)/ `BellmanFordStrategy.solve`(V-1 回緩和 → もう 1 回で負閉路 → infeasible + violation。復元は `segments.reconstruct_path`)/ Dijkstra/A* は負辺で infeasible |
| 4-3 | `graph/a_star.py`(新規)                                                                                                                                                                   | `AStarStrategy.solve`(heap キーを g+h に。復元は `segments.reconstruct_path`)/ `_heuristic`(両端に座標があればユークリッド、無ければ 0)/ 座標なしは Dijkstra と完全一致 |
| 4-4 | `tests/unit/test_route_strategies.py`(経由順セクション。`waypoints.py` / `segments.py` は 4-1 で最終形)                                                                                                | `optimize_waypoint_order`(m ≤ 8 は全順列、区間コストは呼び出し側が `cost` で渡す)/ どの順でも繋がらなければ None                                                                                                             |
| 4-5 | `graph/networkx_shortest.py`(新規)、`services/algorithm_selection.py`(現行版)、`pyproject.toml`                                                                                                | `NetworkxShortestPath`(name="dijkstra"、implementation="library:networkx"、`_ops` を出さない)/ `select_strategy`(負辺→bellman_ford / 全座標→a_star / 既定→dijkstra)                                        |
| 4-6 | `analysis/route_benchmark.py`(新規)、`analysis/{plots,README}`・`tests/fixtures/optimization.py`(現行版)、notebook + 固定 JSONL                                                                   | `load_route_benchmark_runs`(size / density 列を足す)/ `by_size` / `handwritten_vs_library`(speedup)/ `crossover_size` / `build_scaled_route_problem` に `density`(既定は Phase 3 と同じ本数)              |
| 4-7 | `ui: charts/GraphCanvas.tsx` + `.test.tsx`(新規)、`lib/api/types.ts`(現行版 = route のみ)、`features/optimization/route-planner/api`・`sample-problems.ts`、`components/ProblemJsonEditor.tsx`(新規) | `GraphCanvas`(x/y 配置 or 円環、highlight / dashed / directed 矢印)/ `solveRoute` / `compareRoute`(`apiFetch` 経由)/ route の DTO / JSON テキストエディタ                                                      |
| 4-8 | `ui: route-planner/{stores,hooks,components}`(新規)、`app/(pages)/optimization/route-planner/page.tsx`、`lib/menu-tree.ts`(現行版)                                                             | `useRoutePlannerStore`(problem / solution / comparison / solve / compare)/ `RoutePlannerPanel`(`"use client"`)/ `RouteResultCanvas`(経路ハイライト)/ ページは SSG + `RequireAuth`                       |

各単位ごとに `uv run ruff check .`(backend)/ `npx eslint`(ui)と各テストを通してからコミット。

---

## 11. 次のフェーズ

Phase 4 完了後、「**Phase 5 を開始する**」で **Network Designer**(最小全域木)の教材を生成する。
Phase 1 以来はじめての**新しい `problem_type` を端から端まで足す**教材 ── 判別ユニオンに 1 メンバー、
registry に 1 キー、既存の route / shift には一切触れない。Union-Find の深掘り / MST 理論
(cut property・交換論法)/ Kruskal・Prim、そして Phase 4-8 と同型の Network Designer ページ。
詳細: `textbook/Phase-5/Phase-5-introduction.md`。
