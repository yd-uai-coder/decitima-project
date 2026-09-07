# Phase 4-2: 負の重み(スキーマ変更)+ Bellman-Ford(作業単位 4-2)

## この章のゴール

Dijkstra は「一度 settle したノードの最短距離は確定」という不変条件で速い。この前提は
**負の辺があると崩れる**。Bellman-Ford は代わりに「全辺を V-1 回緩和する」── 遅い(O(V·E))が
負辺を正しく扱え、**負閉路**(たどるたびにコストが下がる閉路 = 最短経路が定義できない)も検出できる。

Phase 1 は `RouteEdge.weight = Field(ge=0)` で負を Pydantic が弾いていた。これを外し、
opt-in の `RouteData.allow_negative` に置き換える。

- `RouteData.allow_negative: bool = False` + `model_validator`(False で負辺なら `ValidationError`)
- `graph/bellman_ford.py` ── `BellmanFordStrategy`
- Dijkstra / A* は負辺グラフを渡されたら `status="infeasible"`(壊れた解を返さない)
- registry の route_planning に `BellmanFordStrategy()` を追加

**この章で新規作成するファイル**: `app/algorithms/graph/bellman_ford.py`。
**既存ファイルへの変更**: `app/domain/problems/route_planner.py`(`allow_negative` 追加。現行版は samples)、
`app/algorithms/registry.py`(`BellmanFordStrategy` の import + 1 行)、
`tests/fixtures/optimization.py`(負辺・負閉路 fixture 追加。現行版は samples)、
`app/algorithms/graph/segments.py`(`negative_cycle_violation` 追加。現行版は samples)。

対応サンプル: `samples/app/algorithms/graph/bellman_ford.py`、`samples/app/domain/problems/route_planner.py`。
テストは `samples/tests/unit/test_route_strategies.py`。
設計は README §8(Bellman-Ford ── 負辺・負閉路検出)、`Phase-0-4.md` §2.4。

> ベルマンフォード法とダイクストラ法は、どちらも**単一始点最短経路問題（Single-Source Shortest Path）**を解くアルゴリズム。
> 
> 最大の違いは、**負の重みを扱えるか**と**計算速度**。
> 
> | 比較      | ダイクストラ法               | ベルマンフォード法  |
> | ------- | --------------------- | ---------- |
> | 最短経路    | ○                     | ○          |
> | 負の重み    | **×**                 | **○**      |
> | 負閉路の検出  | ×                     | **○**      |
> | 計算量     | O((V+E) log V) ※ヒープ使用 | **O(VE)**  |
> | 基本的な考え方 | 最短距離を順番に確定            | 全辺を繰り返し緩和  |
> | 高速性     | **高速**                | 遅い         |
> | 主な用途    | 通常の経路探索               | 負のコストがある問題 |
> 
> ※ `V` = 頂点数、`E` = 辺数。

---

## 1. スキーマ変更 ── `ge=0` を外し `allow_negative` に

```python
# app/domain/problems/route_planner.py(要点。全文は samples)
class RouteEdge(BaseModel):
    id: str
    source: str
    target: str
    weight: float                 # ← Field(ge=0) を撤廃
    directed: bool = False

class RouteData(BaseModel):
    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str
    goal: str
    allow_negative: bool = False  # ← 追加。True のときだけ負辺を許可

    @model_validator(mode="after")
    def _guard_negative_weights(self) -> RouteData:
        if not self.allow_negative:
            bad = [e.id for e in self.edges if e.weight < 0]
            if bad:
                raise ValueError(f"negative weight on edge(s) {bad}; set allow_negative=True ...")
        return self
```

- **既定の挙動は不変** ── `allow_negative` を指定しなければ False で、負辺は Pydantic が弾く
  (Phase 1 の `Field(ge=0)` と同じ結果)。既存の route problem / fixture / テストは無変更で通る。
- **ガードを `RouteEdge` から `RouteData` の `model_validator` に移した理由**: `ge=0` は
  「このフィールドは常に非負」という無条件の宣言。`allow_negative` は**親(RouteData)が持つ方針**
  なので、フィールド単体では判定できない ── 親レベルの `model_validator` が正しい場所。
- **なぜフラグで、負辺を常に許可しないのか**: 現実の経路コスト(距離・時間)は非負。負辺は
  「割引経路」「エネルギー回収」等の特殊なモデル化で、うっかり混入したら**バグ**の可能性が高い。
  デフォルトで弾き、意図したときだけ opt-in する(`Phase-0-2.md` §4.2 の「フラグ的な意味づけ」)。

> **[以降 Phase で修正予定 ── Phase 4-2]** ── この節が Phase 1 の `route_planner.py` を書き換える。
> Phase 1〜3 を読む時点では `weight: float = Field(ge=0)` のまま写経してよい。

---

## 2. `BellmanFordStrategy`

```python
# app/algorithms/graph/bellman_ford.py(要点。全文は samples)
from app.algorithms.graph.segments import reconstruct_path, negative_cycle_violation   # reconstruct_path は 4-1、negative_cycle_violation はこの章で追加
class _NegativeCycle(Exception): ...   # start から到達できる負閉路

def _bellman_ford_segment(adjacency, start, goal) -> tuple[Segment | None, int]:
    edges = [(u, v, eid, w) for u, nbrs in adjacency.items() for v, eid, w in nbrs]
    dist = {start: 0.0}
    for _ in range(max(len(adjacency) - 1, 0)):          # V-1 回
        changed = False
        for u, v, eid, w in edges:
            if u in dist and dist[u] + w < dist.get(v, inf):
                dist[v] = dist[u] + w; prev[v] = (u, eid); changed = True
        if not changed: break                            # 早期終了
    for u, v, _eid, w in edges:                          # もう1回緩和できたら…
        if u in dist and dist[u] + w < dist.get(v, inf):
            raise _NegativeCycle                         # …負閉路
    if goal not in dist:
        return None, ops
    return reconstruct_path(prev, start, goal, dist[goal]), ops   # 復元は Dijkstra / A* と共通

class BellmanFordStrategy:
    meta = AlgorithmMeta(name="bellman_ford", family="graph",
        implementation="handwritten", time_complexity="O(V*E)", space_complexity="O(V)")

    def solve(self, problem):
        forbidden, required = collect_route_constraints(problem)
        adjacency = build_adjacency(data, forbidden)
        try:
            seg, ops = plan_route(data.start, data.goal, required,
                                  lambda a, b: _bellman_ford_segment(adjacency, a, b))
        except _NegativeCycle:
            return route_solution(None, None, self.meta, violations=[negative_cycle_violation()])
        return route_solution(seg, ops, self.meta)
```

- **`_ops` = 緩和を試みた回数**(V-1 周 + 検出周)。Dijkstra の `_ops`(heap pop 数)とは
  単位が違う ── 並べても割り算しない。
- **負閉路は `_NegativeCycle` 例外で `plan_route` の外まで持ち上げ**、`solve` が
  `status="infeasible"` + `ConstraintViolation(constraint_kind="negative_cycle", severity="hard")`
  にする。「解が無い」は例外にせず候補解の status で表す(`Phase-0-6.md` §4)── ただし
  負閉路は「最短経路という概念自体が成立しない」ので理由を violation に残す。
  
  > ベルマンフォード法が負の閉路（negative cycle）を含む場合に、通常の意味での「最短距離」を求められない理由は、
  > 
  > **負の閉路を何周もすると、経路のコストをいくらでも小さくできてしまうから**
- **共通足回り(`segments.py`)をそのまま使う** ── 4-1 で作った `plan_route` / `route_solution` /
  `collect_route_constraints` / `reconstruct_path` を再利用。**Bellman-Ford 固有なのは緩和ループと
  負閉路検出だけ** ── 経路復元(`prev` を辿る)は Dijkstra の `_dijkstra_segment` と 1 文字も
  変わらないので、4-1 で `segments.reconstruct_path` に公開関数として出してある(`Phase-4-1.md` §2)。
- **`negative_cycle_violation()` はこの章で `segments.py` に追加する** ── 既にある
  `negative_weight_violation(algorithm)`(Dijkstra / A* が消費)と同じ理由で、`solve` の外に
  公開関数として置く。理由は「1 本目の消費者(この章の Bellman-Ford)の時点で、2 本目の消費者
  (4-5 の `NetworkxShortestPath`。同じ負閉路 violation を必要とする)が来ると分かっているから」
  ── ヘルパの置き場は「2 本目の消費者」で決まる、という判断を先回りする(`_reconstruct` /
  `reconstruct_path` の教訓と同型)。`_` を付けない(=公開)のも `negative_weight_violation` と
  揃える。

---

## 3. Dijkstra / A* の負辺ガード

```python
# dijkstra.py / a_star.py の solve 冒頭
adjacency = build_adjacency(data, forbidden)
if has_negative_weight(adjacency):
    return route_solution(None, None, self.meta,
                          violations=[negative_weight_violation("dijkstra")])
```

- `allow_negative=True` の problem で `?algorithm=dijkstra` を明示指定されても、Dijkstra は
  誤った解を返さず `infeasible` で降りる(防御的)。通常は rule-based selection(4-5)が
  そもそも `bellman_ford` を選ぶので、ここには来ない。

---

## 4. 負辺のデモは**有向グラフ**で作る

```python
# tests/fixtures/optimization.py(要点)
def build_negative_route_problem():
    # S->T 直行 = 5、S->A(2) + A->B(-4) + B->T(3) = 1 ── 負辺経由の方が短い
    edges = [
        RouteEdge(id="s_t", source="S", target="T", weight=5, directed=True),
        RouteEdge(id="s_a", source="S", target="A", weight=2, directed=True),
        RouteEdge(id="a_b", source="A", target="B", weight=-4, directed=True),
        RouteEdge(id="b_t", source="B", target="T", weight=3, directed=True),
    ]
    # RouteData(..., allow_negative=True)
```

**無向グラフに負辺を置くと、a→b→a を往復するたびにコストが下がる = 即・負閉路**になる。
Bellman-Ford の「負辺は扱えるが負閉路は弾く」を見せたいなら、負辺は**有向**にし、
負閉路のデモは有向の閉路(`build_negative_cycle_route_problem`)で作る。

---

## 5. registry の配線(既存ファイルへの追記)

```python
# app/algorithms/registry.py
from app.algorithms.graph.bellman_ford import BellmanFordStrategy   # ← この章で有効化

"route_planning": [
    DijkstraStrategy(),
    BellmanFordStrategy(),        # ← 追加
    BruteForceRouteStrategy(),
    # AStarStrategy(),            ← 4-3
],
```

`find_strategy` の既定は `candidates[0]` = Dijkstra のまま。Bellman-Ford は 4-5 の
rule-based selection が「負辺あり」を見て選ぶ。ベンチには全 strategy が乗るので、
`test_benchmark_service.py` の entry 数の期待値がこの章で変わる(現行版は samples、
Phase 3 samples にマーカー)。

---

## 6. まとめ

- `RouteEdge.weight` の `Field(ge=0)` を撤廃 → `RouteData.allow_negative` + `model_validator`。
  既定は False で従来どおり負を弾く。
- `BellmanFordStrategy` = V-1 回緩和 + もう 1 回で負閉路検出。`segments.py` の共通足回りに乗る。
- Dijkstra / A* は負辺グラフで `infeasible`(壊れた解を返さない)。
- 負辺のデモは有向で作る(無向 + 負辺 = 即・負閉路)。

## テスト観点(`samples/tests/unit/test_route_strategies.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `BellmanFordStrategy.solve`、`RouteData` の `model_validator`
> - **ドライバ**: このテスト関数。`build_negative_route_problem` / `build_negative_cycle_route_problem` が入力生成
> - **スタブ**: **不要** ── `solve` は純粋(`DijkstraStrategy` と同じ)。model_validator も純粋

| ケース                                        | 期待                                                          |
| ------------------------------------------ | ----------------------------------------------------------- |
| 負辺グラフ(S→A→B→T)                             | Bellman-Ford が `["S","A","B","T"]` / `total_weight == 1.0`  |
| 同じ負辺グラフ + Dijkstra                         | `status == "infeasible"` / violation kind `negative_weight` |
| 有向の負閉路                                     | `status == "infeasible"` / violation kind `negative_cycle`  |
| `allow_negative=False` で負辺 `RouteData` を構築 | `pydantic.ValidationError`(match `allow_negative`)          |

`uv run pytest tests/unit/test_route_strategies.py` /
`uvx pyright app/algorithms/graph/bellman_ford.py`。

---

次章([Phase-4-3](./Phase-4-3.md))では、作業単位 4-3 ── `RouteNode.x/y` を使って goal 方向を
優先探索する `AStarStrategy` を作る。ヒューリスティックが可容なら最適性は保たれ、探索が減る。
