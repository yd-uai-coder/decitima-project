# Phase 4-3: A* とヒューリスティック探索(作業単位 4-3)

## この章のゴール

A* は「Dijkstra + goal への推定残距離 h(n)」。優先度キューのキーを `g(n)`(start からの実距離)
ではなく `f(n) = g(n) + h(n)` にするだけ。h(n) が **可容**(実際の残距離を超えない)なら
最適性は保たれ、h(n) が正確なほど「goal と逆方向」のノードを展開しなくなる ── `_ops` が下がる。

- `graph/a_star.py` ── `AStarStrategy`。h(n) は `RouteNode.x/y` のユークリッド距離。座標が無ければ h(n)=0 で Dijkstra に縮退
- registry の route_planning に `AStarStrategy()` を追加
- 「不可容な h だと非最適になる」をテストで**わざと赤**にして確認(進行のルール #14 の趣旨)

> ヒューリスティック探索（heuristic search）**とは、問題の探索において、**「どちらの方向に進めば目的地に近そうか」という推定（ヒューリスティック）を利用して、探索を効率化する手法。
> 
> ヒューリスティック探索の代表的なアルゴリズムが**A*（A-star）**
> 
> |          | ダイクストラ法 | A*             |
> | -------- | ------- | -------------- |
> | 評価       | `g(n)`  | `g(n) + h(n)`  |
> | ゴールまでの推定 | 使わない    | **使う**         |
> | 探索範囲     | 広くなりやすい | **絞り込みやすい**    |
> | 最短経路     | ○       | 条件を満たす `h` なら○ |
> | 負の重み     | ×       | 基本的に×          |

**この章で新規作成するファイル**: `app/algorithms/graph/a_star.py`。
**既存ファイルへの変更**: `app/algorithms/registry.py`(`AStarStrategy` の import + 1 行)。

対応サンプル: `samples/app/algorithms/graph/a_star.py`。
テストは `samples/tests/unit/test_route_strategies.py`(A* セクション)。
設計は `Phase-0-5.md` §2.2(A* の計算量)、README §8。

---

## 1. `AStarStrategy`

```python
# app/algorithms/graph/a_star.py(要点。全文は samples)
type _Coords = dict[str, tuple[float, float]]

def _heuristic(coords: _Coords, node: str, goal: str) -> float:
    if node not in coords or goal not in coords:
        return 0.0                            # 座標が無ければ h(n)=0(常に可容 → Dijkstra 相当)
    (x1, y1), (x2, y2) = coords[node], coords[goal]
    return math.hypot(x1 - x2, y1 - y2)

def _astar_segment(adjacency, start, goal, coords) -> tuple[Segment | None, int]:
    g = {start: 0.0}
    heap = [(_heuristic(coords, start, goal), start)]    # キーは f = g + h
    while heap:
        _f, node = heapq.heappop(heap); pops += 1
        if node in settled: continue
        settled.add(node)
        if node == goal: break
        for nxt, edge_id, weight in adjacency.get(node, ()):
            ng = g[node] + weight
            if ng < g.get(nxt, inf):
                g[nxt] = ng; prev[nxt] = (node, edge_id)
                heapq.heappush(heap, (ng + _heuristic(coords, nxt, goal), nxt))
    if goal not in settled:
        return None, pops
    return reconstruct_path(prev, start, goal, g[goal]), pops   # 復元は Dijkstra / Bellman-Ford と共通

class AStarStrategy:
    meta = AlgorithmMeta(name="a_star", family="graph", implementation="handwritten",
        time_complexity="O((V+E) log V)", space_complexity="O(V)")

    def solve(self, problem):
        forbidden, required = collect_route_constraints(problem)
        adjacency = build_adjacency(data, forbidden)
        if has_negative_weight(adjacency):                # A* も負辺は扱えない
            return route_solution(None, None, self.meta, violations=[negative_weight_violation("a_star")])
        coords = {n.id: (n.x, n.y) for n in data.nodes if n.x is not None and n.y is not None}
        seg, ops = plan_route(data.start, data.goal, required,
                              lambda a, b: _astar_segment(adjacency, a, b, coords))
        return route_solution(seg, ops, self.meta)
```

- **`_ops` = heap pop 数**(Dijkstra と同じ数え方)。だから A* と Dijkstra の `_ops` は**直接
  比較できる**数少ない例 ── 「A* は何ノード少なく展開したか」が読める(4-8 の Route Benchmark で使う)。
- **座標が一部のノードにしか無いときは h(n)=0** にフォールバック。0 は「実距離を絶対に超えない」
  ので可容性が保たれ、その区間だけ Dijkstra 相当になる(最適性は崩れない)。
- 共通足回り(`segments.plan_route` / `route_solution` / `reconstruct_path`)は Dijkstra /
  Bellman-Ford と同じ。A* 固有なのは「heap キーを g+h にする」+ `_heuristic` だけ。

---

## 2. 可容性(admissibility)── なぜ h が実距離を超えてはいけないか

A* が最適解を返す条件は **h(n) ≤ (n から goal への実最短距離)**。

- **weight が「両端の直線距離」なら euclidean h は常に可容**(三角不等式)。テストの
  `build_coord_route_problem` はこの形なので A* == Dijkstra の最適値。
- **weight が「所要時間」や「料金」だと euclidean h は過大評価しうる** ── 直線距離が長くても
  高速道路で速い、等。過大評価すると A* は「近道に見えるが実は遠い」経路を先に確定して
  **非最適解**を返す。

教材のテストでは、わざと過大な h(座標を 10 倍に膨らませる等)で「A* が Dijkstra より重い解を
返す」ことを 1 ケース**赤で**確認する ── 「不変条件を破ると何が壊れるか」を体で覚えるため
(進行のルール #14 / `Phase-1` の「わざと赤にして境界確認」)。

---

## 3. 座標をどう用意するか

`RouteNode.x/y` は Phase 1 から `float | None` で持たせてあった(まさに A* のため。
`Phase-0-introduction.md` §... / README §19 Phase 4 設計のポイント)。UI(4-8)では
問題 JSON にノード座標を書けば A* が自動選択される。座標が無い問題は Dijkstra のまま。

---

## 4. registry の配線(既存ファイルへの追記)

```python
# app/algorithms/registry.py
from app.algorithms.graph.a_star import AStarStrategy   # ← この章で有効化

"route_planning": [
    DijkstraStrategy(),
    BellmanFordStrategy(),
    AStarStrategy(),             # ← 追加
    BruteForceRouteStrategy(),
    # NetworkxShortestPath(),    ← 4-5
],
```

`GET /api/v1/algorithms` に `a_star` が現れ、ベンチに乗る。単発 `solve` で A* が選ばれるのは
「全ノードに座標がある」とき(4-5 の rule-based selection)。

---

## 5. まとめ

- A* = Dijkstra のキーを `f = g + h` にしただけ。h(n) は座標のユークリッド距離、無ければ 0。
- h が可容なら最適性は保たれ、`_ops`(heap pop 数)が Dijkstra 以下になる。
- h が過大評価だと非最適解 ── テストで 1 ケースわざと赤にして確認する。
- `_ops` の数え方が Dijkstra と同じなので、A* と Dijkstra は `_ops` を直接比較できる。

## テスト観点(`samples/tests/unit/test_route_strategies.py` の A* セクション)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `AStarStrategy.solve` / `_heuristic`
> - **ドライバ**: このテスト関数。`build_coord_route_problem`(座標つき格子)/ `build_route_problem`(座標なし)
> - **スタブ**: **不要** ── `solve` は純粋

| ケース                        | 期待                                                   |
| -------------------------- | ---------------------------------------------------- |
| 座標つきグラフ                    | `a_star.total_weight == dijkstra.total_weight`(最適一致) |
| 同じグラフ(goal と逆方向の寄り道クラスタあり) | `a_star._ops < dijkstra._ops`(展開ノードが減る)              |
| 座標なしグラフ                    | `a_star` の経路 == `dijkstra` の経路(h(n)=0 で縮退)           |
| 負辺グラフ + A*                 | `status == "infeasible"`                             |

`uv run pytest tests/unit/test_route_strategies.py -k a_star` /
`uvx pyright app/algorithms/graph/a_star.py`。

---

次章([Phase-4-4](./Phase-4-4.md))では、作業単位 4-4 ── 必須経由地が 2 点以上あるとき、
訪問順を最適化する(小さな TSP)。`optimize_waypoint_order` を `segments.plan_route` に配線する。
