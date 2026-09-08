# Phase 4-5: networkx トラック + 検証オラクル + rule-based 選択(作業単位 4-5)

## この章のゴール

`AlgorithmStrategy` は「手実装トラック」と「産業ソルバートラック」を同じ契約で並べるための
インターフェース(`Phase-0-4.md` §5.2 / `CLAUDE.md` の 2 トラック方針)。ここで最初の
**`library:*` トラック**を入れる ── `networkx` の最短経路を `AlgorithmStrategy` で包む。

- `graph/networkx_shortest.py` ── `NetworkxShortestPath`(`meta.name="dijkstra"`、`implementation="library:networkx"`)
- `pyproject.toml` に `networkx>=3.3`(runtime。solve / benchmark のリクエスト経路で動く)
- 手実装 Dijkstra / Bellman-Ford の**別実装オラクル**(プロパティテストで一致を確認)
- `services/algorithm_selection.py` を rule-based に(負辺→Bellman-Ford / 全座標→A* / 既定→Dijkstra)

**この章で作成 / 更新するファイル**: `app/algorithms/graph/networkx_shortest.py`。
**既存ファイルへの変更**: `app/services/algorithm_selection.py`(rule-based 化。現行版は samples)、
`app/algorithms/registry.py`(`NetworkxShortestPath` の import + 1 行)、
`pyproject.toml`(`networkx>=3.3`)、`decitima-api/README.md`(依存追加の注記)。

対応サンプル: `textbook/samples/app/algorithms/graph/networkx_shortest.py`、`textbook/samples/app/services/algorithm_selection.py`。
テストは `textbook/samples/tests/unit/test_route_strategies.py`(networkx セクション)、`textbook/samples/tests/unit/test_algorithm_selection.py`。
設計は `Phase-0-4.md` §5.2・§6、`Phase-0-9.md` Q19、README §8(実装方針の境界表)。

---

## 1. `networkx` の追加(既存ファイルへの追記)

```toml
# pyproject.toml
[project]
dependencies = [
    # ...
    "networkx>=3.3",   # ← Phase 4。産業ソルバートラック(solve / benchmark のリクエスト経路)
]
```

```bash
uv sync              # uv.lock 更新
# Docker 開発環境を使っている場合は再ビルド(Phase-0-9.md L145)
docker compose build backend
```

> NetworkX は、**Pythonでグラフ構造（Graph）を扱うためのライブラリ**

- **runtime 依存**(`[project].dependencies`)にする ── `numpy` や `pandas`(分析トラック、dev 依存)と違い、`NetworkxShortestPath` は `POST /solve` `/benchmark` のハンドラの中で動く。
- `decitima-api/README.md` の「依存ライブラリ」節に networkx を追記(Phase まで遅延していたもの。`decitima-api/CLAUDE.md` の「依存ライブラリの遅延追加」も更新)。

---

## 2. `NetworkxShortestPath`

```python
# app/algorithms/graph/networkx_shortest.py(要点。全文は samples)
class NetworkxShortestPath:
    meta = AlgorithmMeta(name="dijkstra", family="graph",     # ← 手実装 Dijkstra と同じ name
        implementation="library:networkx",
        time_complexity="O((V+E) log V)", space_complexity="O(V+E)")

    def solve(self, problem):
        graph = _to_graph(data, forbidden)        # RouteData → nx.Graph / nx.DiGraph
        negative = any(w < 0 for *_e, w in graph.edges(data="weight"))
        # 負閉路チェック → infeasible + segments.negative_cycle_violation()(4-2 で追加、再利用)
        order = optimize_waypoint_order(data.start, data.goal, required, cost)  # 共有ロジック
        # 区間ごとに nx.dijkstra_path / nx.bellman_ford_path → RouteSolution
        return route_solution(Segment(node_ids, edge_ids, total), None, self.meta)  # ops=None
```

- **`meta.name` は手実装 Dijkstra と同じ `"dijkstra"`**。区別は `implementation` フィールド
  (`Phase-0-4.md` §5.2 / `Phase-1-4.md` の指示)。狙いは:
  - ベンチで「同じアルゴリズムの 手実装 vs ライブラリ」を並べる(`GET /algorithms` は
    `(name, implementation)` で集約するので 2 行に分かれて見える)
  - Phase 14 の「LLM vs Algorithm」比較の土台
- **`_ops` を積まない**(`route_solution(..., None, ...)`)── 仕事の大半が C 実装の中で、外から数えられない。「ライブラリトラックは操作回数を出せない」こと自体が「手実装 vs 産業ソルバー」比較の論点(`Phase-0-9.md` Q19)。ベンチの `operation_count` は `None` になる。
- **平行エッジは軽い方だけ残す** ── `RouteData` は同じノード対に複数エッジを持てるが
  `nx.Graph` は 1 本しか持てない。`_add_min_edge` で最小重みを採用(最短経路では重い方は絶対に使わないので等価)。
- 必須経由の順序最適化は `optimize_waypoint_order`(4-4)を**そのまま再利用** ── networkx にも同じ小 TSP ロジックが効く。
- 負閉路 violation も**独自定義しない** ── `segments.py` の `negative_cycle_violation()`
  (4-2 で `BellmanFordStrategy` のために追加した公開関数)をそのまま import して使う。
  「手実装と別実装の 2 本目の消費者」という位置づけそのままに、ヘルパも 1 本目の置き場所(`segments.py`)を再利用する(`Phase-4-2.md` §2)。

### オラクルとしての利用

```python
# tests/unit/test_route_strategies.py
def test_networkx_matches_handwritten_dijkstra_property():
    for seed in range(30):
        problem = build_scaled_route_problem(12, seed=seed)
        hw = DijkstraStrategy().solve(problem)
        lib = NetworkxShortestPath().solve(problem)
        assert hw.status == lib.status
        if hw.status == "valid":
            assert hw.metrics["total_weight"] == pytest.approx(lib.metrics["total_weight"])
```

- **BruteForce(Phase 3)は「厳密最適」オラクル**、**networkx は「別実装での照合」オラクル**。
  役割が違う ── BruteForce は「最適値そのもの」を保証、networkx は「別の成熟した実装と一致するか」を保証(実装ミスの検出力が高い)。

---

## 3. rule-based `select_strategy`

Phase 1 の `select_strategy` は「候補の先頭」を返すだけだった。README §6 / `Phase-0-4.md` §6 が「Rule Based ── Phase 4/5 で実装」としていた分を、ここで**問題特性の単純な if** として入れる。

```python
# app/services/algorithm_selection.py(要点。全文は samples)
def _preferred_name(problem) -> str | None:
    data = problem.data
    if isinstance(data, RouteData):
        if data.allow_negative or any(e.weight < 0 for e in data.edges):
            return "bellman_ford"                         # 負辺 → Bellman-Ford
        if data.nodes and all(n.x is not None and n.y is not None for n in data.nodes):
            return "a_star"                               # 全ノードに座標 → A*
        return "dijkstra"                                 # 既定は手実装 Dijkstra
    return None

def select_strategy(problem, requested=None) -> AlgorithmStrategy:
    if requested is not None:
        # meta.name 一致(無ければ NoAlgorithmError)
    candidates = get_strategies(problem.problem_type)
    preferred = _preferred_name(problem)
    return next((s for s in candidates if s.meta.name == preferred), candidates[0])
```

- **`registry.find_strategy` は純粋のまま**(候補の先頭)── 「問題特性を見た賢い選択」は副作用こそ無いが「ユースケースの知識」なので services 層に置く(Phase 1 で `NoAlgorithmError`
  を registry から services に分離したのと同じ判断。`Phase-1-2.md` §3)。
- **`library:networkx` は明示 request 時のみ** ── `_preferred_name` は `"dijkstra"`(手実装)を返すので、自動選択で networkx が使われることはない。ベンチでは全候補が走る。
- **`network_design` の分岐は Phase 5-3 で足す** ── この章は route の分岐だけ。新 `problem_type`
  を配線する Phase 5 で `_preferred_name` に `network_design → "kruskal"` を 1 行加える。
- **学習型の選択(蓄積 benchmark から「問題特徴 → 最適アルゴリズム」を導出)は Phase 12**。
  Phase 4 は「if 文で分ける」ところまで。

---

## 4. registry の配線(既存ファイルへの追記)

```python
# app/algorithms/registry.py
from app.algorithms.graph.networkx_shortest import NetworkxShortestPath   # ← この章で有効化

"route_planning": [
    DijkstraStrategy(),
    BellmanFordStrategy(),
    AStarStrategy(),
    NetworkxShortestPath(),      # ← 追加(手実装 Dijkstra と同 name / 別 implementation)
    BruteForceRouteStrategy(),
],
```

**手実装 strategy を先頭に置く** ── `find_strategy` の requested 一致は `next(...)` で先頭を返すので、`?algorithm=dijkstra` は手実装が当たる(望ましい既定)。

---

## 5. まとめ

- `networkx` を runtime 依存に追加(`library:*` トラックは solve / benchmark のリクエスト経路)。
- `NetworkxShortestPath` は `name="dijkstra"` / `implementation="library:networkx"` / `_ops` なし。
  手実装 Dijkstra・Bellman-Ford の別実装オラクル。
- `select_strategy` を rule-based に ── 負辺→bellman_ford / 全座標→a_star / 既定→dijkstra。
- 学習型の選択は Phase 12。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `NetworkxShortestPath.solve`(`test_route_strategies.py`)、`select_strategy`(`test_algorithm_selection.py`)
> - **ドライバ**: このテスト関数。`build_scaled_route_problem`(seed ループ)/ `build_negative_route_problem` / `build_coord_route_problem`
> - **スタブ**: **不要** ── networkx は決定論的(外部プロセスもネットワークも無い)。
>   `select_strategy` は実 REGISTRY(Phase 4 end 状態で全 strategy 登録済み)を回すだけ

| ファイル                | ケース                                                          | 期待                         |
| ------------------- | ------------------------------------------------------------ | -------------------------- |
| route_strategies    | seed 0〜29 で `dijkstra.total_weight == networkx.total_weight` | オラクル一致                     |
| route_strategies    | networkx 解の `metrics`                                        | `"_ops"` を含まない             |
| algorithm_selection | 既定の route problem                                            | `dijkstra` / `handwritten` |
| algorithm_selection | 負辺 problem                                                   | `bellman_ford`             |
| algorithm_selection | 全ノード座標つき                                                     | `a_star`                   |
| algorithm_selection | `requested="dijkstra"` on 座標つき                               | `dijkstra`(requested が勝つ)  |

`uv run pytest tests/unit/test_route_strategies.py tests/unit/test_algorithm_selection.py` /
`uvx pyright app/algorithms/graph/networkx_shortest.py app/services/algorithm_selection.py`。

---

次章([Phase-4-6](./Phase-4-6.md))では、作業単位 4-6 ── ここまでで揃った route の 4 strategy
(Dijkstra / Bellman-Ford / A* / networkx)を benchmark にかけ、`analysis/route_benchmark.py` で
「密度 × アルゴリズム」の実測を読む。

> Network Designer(最小全域木 ── 新 `problem_type` `network_design`)は **Phase 5** に分けた。
> Phase 4 を完了したら「Phase 5 を開始する」でそちらへ進む(Union-Find / MST 理論 / 配線 / Kruskal・Prim)。
