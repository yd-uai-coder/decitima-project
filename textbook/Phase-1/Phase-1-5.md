# Phase 1-5: DijkstraStrategy(作業単位 1-4)

## この章のゴール

Phase 1 で唯一 `registry` に載る `AlgorithmStrategy` を実装する。`route_planning` 専用。

- `RouteData` → 重み付き隣接リスト、`ForbiddenConstraint` のエッジ除外
- `RequiredInclusionConstraint`(0〜1 個)による区間分割
- `heapq` によるダイクストラ、非連結で `status="infeasible"`
- `metrics` に操作回数(`_ops`)を入れる規約(Phase 3 の布石)

対応サンプル: `samples/app/algorithms/graph/dijkstra.py`、
テストは `samples/tests/unit/test_dijkstra_strategy.py`。設計は `Phase-0-4.md` §5.1 / §7.1、
計算量 `Phase-0-5.md` §2.2。期待解は `Phase-0-2.md` §7.1(A→B→C→E, weight=9)。

---

## 1. solve の流れ

```text
DijkstraStrategy.solve(problem):
    data = problem.data                      # route_planning なので RouteData
    forbidden, required = 制約から集める      # ForbiddenConstraint.items / RequiredInclusionConstraint.items
    adjacency = build_adjacency(data, forbidden)      # forbidden のエッジは張らない
    legs = _waypoints(start, goal, required)          # [start, (必須...), goal]、連続重複は畳む
    for a, b in pairwise(legs):
        segment, ops = _dijkstra_segment(adjacency, a, b)   # heapq ダイクストラ
        if segment is None:  return infeasible な CandidateSolution
        経路を連結(区間の先頭ノードは前区間の末尾と重複するので落とす)
    return CandidateSolution(status="valid", assignments=RouteSolution(...),
                             metrics={"total_weight": ..., "_ops": ...}, produced_by=self.meta)
```

`status="valid"` は「解を作れた」の意味。**hard 制約を満たしているかは Verification が後で判定**
する(`Phase-0-4.md` §2.3)。だから Dijkstra は「禁止エッジを除いて探索する」ことはしても、
出した経路が必須ノードを通っているかの最終確認はしない(区間分割で構造的に通るようにはする)。

---

## 2. 隣接リストの構築

```python
# app/algorithms/graph/dijkstra.py
type _Adjacency = dict[str, list[tuple[str, str, float]]]   # node -> [(隣接node, edge_id, weight)]

def build_adjacency(data: RouteData, forbidden_edge_ids: set[str]) -> _Adjacency:
    adjacency: _Adjacency = {node.id: [] for node in data.nodes}
    for edge in data.edges:
        if edge.id in forbidden_edge_ids:
            continue
        adjacency.setdefault(edge.source, []).append((edge.target, edge.id, edge.weight))
        if not edge.directed:                       # 無向は逆向きも張る
            adjacency.setdefault(edge.target, []).append((edge.source, edge.id, edge.weight))
    return adjacency
```

`build_adjacency` は `ProblemValidationService`(route の到達可能性チェック)からも使う ──
だから strategy のトップレベル関数として export しておく([Phase-1-7](./Phase-1-7.md) §2)。

---

## 3. `heapq` ダイクストラ(1 区間)

```python
def _dijkstra_segment(adjacency, start, goal) -> tuple[_Segment | None, int]:
    dist: dict[str, float] = {start: 0.0}
    prev: dict[str, tuple[str, str]] = {}       # node -> (1つ前の node, その edge_id)
    heap: list[tuple[float, str]] = [(0.0, start)]
    settled: set[str] = set()
    pops = 0
    while heap:
        d, node = heapq.heappop(heap); pops += 1
        if node in settled:      continue        # 古い距離での重複エントリはスキップ
        settled.add(node)
        if node == goal:         break
        for nxt, edge_id, weight in adjacency.get(node, ()):
            nd = d + weight
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                prev[nxt] = (node, edge_id)
                heapq.heappush(heap, (nd, nxt))
    if goal not in settled:      return None, pops       # 非連結
    # goal から prev を辿って start→goal 順に復元
    ...
    return _Segment(node_ids, edge_ids, dist[goal]), pops
```

- **二分ヒープで O((V+E) log V)**(`Phase-0-5.md` §2.2)。
- 「settled に入ったらもう触らない」+「古いエントリはスキップ」が手実装の定石。
- `pops`(キューから取り出した回数)を返して `metrics["_ops"]` に積む。Phase 3 のベンチマークで
  「理論計算量の裏付け」に使う(`Phase-0-5.md` §4)。

---

## 4. 必須経由(`RequiredInclusionConstraint`)

Phase 1 は **必須経由 0〜1 個**を扱う(`Phase-0-5.md` §5.3)。

```python
def _waypoints(start, goal, required: list[str]) -> list[str]:
    points = [start, *required, goal]
    # 連続重複を畳む(required が start や goal と同じケース)
    collapsed = []
    for pt in points:
        if not collapsed or collapsed[-1] != pt:
            collapsed.append(pt)
    return collapsed
```

`legs = [start, C, goal]` なら「start→C」「C→goal」を別々にダイクストラして連結する。

- **必須経由 2 個以上**は「m! 通りの訪問順 × 各区間最短」= 小さな巡回セールスマン問題。
  Phase 1 は required を**与えられた順**でそのまま通す(決定論的で、順序が指定どおりなら正しい)。
  訪問順の最適化は Phase 4。

---

## 5. 非連結 → `infeasible`

どこかの区間で `_dijkstra_segment` が `None` を返したら:

```python
return CandidateSolution(
    status="infeasible",
    assignments=RouteSolution(path_node_ids=[], path_edge_ids=[], total_weight=0.0),
    metrics={"_ops": float(total_ops)},
    produced_by=self.meta,
)
```

`infeasible` は「解が存在しない」。`Phase-0-4.md` §2.3 が認めている唯一の「solve が status を
決めてよいケース」。Verification は `infeasible` の解を素通しする([Phase-1-7](./Phase-1-7.md) §4)。

---

## 6. `AlgorithmMeta`

```python
class DijkstraStrategy:
    meta = AlgorithmMeta(
        name="dijkstra", family="graph", implementation="handwritten",
        time_complexity="O((V+E) log V)", space_complexity="O(V)",
    )
```

`name="dijkstra"` + `implementation="handwritten"`。Phase 4 で `networkx` 版を足すときは
`name` は同じ `"dijkstra"`、`implementation="library:networkx"` にする。Phase 3 の
ベンチマークが「手実装 vs ライブラリ」をこの 2 つのキーで並べる。

---

## 7. テスト観点(`samples/tests/unit/test_dijkstra_strategy.py`)

`Phase-0-9.md` §1.1 の例 + α:

- 制約なし: A→B→D→E, weight 5(最短)
- `forbidden=["e_bd"], required=["C"]`: A→B→C→E, weight 9(`Phase-0-2.md` §7.1 の期待解)
  / `path_edge_ids` に `e_bd` を含まない / `path_node_ids` に `C` を含む
- 非連結(`forbidden=["e_ce","e_de"]`): `status="infeasible"`
- **再現性**: 同じ problem を 2 回解いて `model_dump()` が完全一致(NFR-1)
- `produced_by` に `name` / `implementation` / `family` が入っている

discriminated union の消費側は `assert isinstance(sol.assignments, RouteSolution)` で
絞り込む(サンプルの `_route(sol)` ヘルパ)。

---

## 8. まとめ

- `DijkstraStrategy` は route_planning 専用の `AlgorithmStrategy`。registry に載る唯一の Phase 1 strategy。
- `build_adjacency` で forbidden エッジを除外、`_waypoints` で必須経由(0〜1)を区間分割、
  `heapq` で各区間を解いて連結。
- 非連結は `status="infeasible"`。それ以外は `status="valid"`(hard 判定は Verification)。
- `metrics["_ops"]` に操作回数を積む(Phase 3 の布石)。
- 再現性テストを必ず入れる。

次章([Phase-1-6](./Phase-1-6.md))では、作業単位 1-5 ── 問題と解を永続化する
`Problem` / `Solution` モデルとリポジトリを実装する。
