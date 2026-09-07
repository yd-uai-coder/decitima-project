# Phase 4-1: グラフプリミティブの整理(作業単位 4-1)

## この章のゴール

Phase 1 は `build_adjacency` を `graph/dijkstra.py` の中に置いていた。Phase 2 の `reachability.py`、
Phase 3 の `brute_force.py` がそれを import して使っており、Phase 4 では さらに Bellman-Ford / A* が
同じ関数を要る。`Phase-2-2.md` §3・`reachability.py` の docstring が予告したとおり、ここで
**route の共有プリミティブを独立させる**。

- `graph/adjacency.py` ── `build_adjacency`(RouteData → 重み付き隣接)を移設 + `plain_adjacency` / `has_negative_weight`
- `graph/segments.py` ── route strategy(Dijkstra / Bellman-Ford / A*)の共通足回り
- `graph/waypoints.py` ── 経由順の並べ替え。骨格を 4-1 で作る(2 点以上の必須経由の全順列最適化の深掘りは 4-4)

`network_design`(MST)用の `union_find.py` / `connectivity.py` / `adjacency.py::build_link_adjacency` は
route 消費者がいないので **Phase 5(Network Designer)** で足す。

**この章で新規作成するファイル**: `app/algorithms/graph/{adjacency,segments,waypoints}.py`。
**既存ファイルへの変更**(変更量は 3 ファイルで大きく違う ── §3):

- `app/algorithms/optimization/brute_force.py` ── import 行 1 つだけ(`solve` 本体は不変)
- `app/algorithms/graph/reachability.py` ── import 元変更 + インライン内包表記を `plain_adjacency()` 呼び出しに
- `app/algorithms/graph/dijkstra.py` ── **大幅リファクタ**。`build_adjacency` / `_Adjacency` 型 /
  `_Segment` クラス / `_waypoints` / 経路復元が外へ出て、`solve` は `collect_route_constraints` +
  `plan_route` + `route_solution`(すべて `segments.py`)への委譲に痩せる。残るのは
  `_dijkstra_segment`(アルゴリズム本体)+ `DijkstraStrategy` だけ

いずれも現行版は samples。

対応サンプル: `samples/app/algorithms/graph/{adjacency,segments,waypoints,dijkstra,reachability}.py`、`samples/app/algorithms/optimization/brute_force.py`。
テストは `samples/tests/unit/test_graph_primitives.py`。
設計は `Phase-0-4.md` §2.4(Strategy とプリミティブの 2 層)、`Phase-2-2.md` §3。

---

## 1. `adjacency.py` ── グラフの作り方だけを 1 ファイルに

```python
# app/algorithms/graph/adjacency.py(要点。全文は samples)
type Adjacency = dict[str, list[tuple[str, str, float]]]  # (隣接 id, エッジ id, 重み)

def build_adjacency(data: RouteData, forbidden_edge_ids: set[str]) -> Adjacency: ...
def plain_adjacency(adjacency: Adjacency) -> dict[str, list[str]]: ...     # 重み/id を落とす
def has_negative_weight(adjacency: Adjacency) -> bool: ...                 # 負辺が1本でも
```

- **`build_adjacency` は移設しただけ** ── 中身は Phase 1 と同じ(`edge.directed` が False なら
  逆向きも張る、forbidden は張らない)。変わったのは「置き場所」だけ。`dijkstra.py` にあった
  非公開エイリアス `type _Adjacency` も一緒に連れてきて、公開名 `Adjacency` に改名した。
- **`plain_adjacency`** は `reachability.py` がインラインでやっていた downgrade を関数化したもの
  (Phase 2 の `plain = {node: [nxt for nxt, _e, _w in edges] ...}` という内包表記そのもの)。
  BFS / 連結性判定は重みを見ないので、`(nxt, edge_id, weight)` から `nxt` だけ取り出す。
- **`has_negative_weight`** は 4-2 で Dijkstra / A* が「負辺グラフなら infeasible」の判定に使う。
- **`build_link_adjacency` はここに置かない** ── link(無向・network 専用)用の隣接ビルダーは
  Phase 5-3 でこのファイルに足す。route 側に消費者がいないので前倒ししない。

> **なぜ `dijkstra.py` に置いたままにしないのか**
> Phase 3-2 の注記どおり「共有する `build_adjacency` は第 3 の関心事」。`dijkstra.py` は
> 「優先度キューでの最短経路」、`bellman_ford.py` は「緩和による最短経路」── それぞれ変更理由も
> 消費者も違う。「グラフの作り方」は**そのどれでもない**共通の下地なので、独立したプリミティブ
> ファイルにする(`search/{bfs,dfs}.py` が別ファイルなのと同じ「1 ファイル 1 関心事」)。

---

## 2. `segments.py` ── route 3 strategy の「同じ部分」

Dijkstra / Bellman-Ford / A* は **区間(start→goal)の最短経路の求め方**だけが違う。
残りは全部同じ:

```text
制約から forbidden / required を集める
   → build_adjacency で隣接リスト
   → 必須経由地の順を決める
   → 区間ごとに最短経路を解いて連結する
   → CandidateSolution に詰める(seg が None なら infeasible)
```

```python
# app/algorithms/graph/segments.py(要点。全文は samples)
type SegmentFn = Callable[[str, str], tuple["Segment | None", int]]  # (start, goal) -> (経路, 操作回数)
class Segment:  # 1 区間の結果(node_ids / edge_ids / weight)

def reconstruct_path(prev, start, goal, weight) -> Segment:
    # 予測子マップ prev を goal から逆走して node/edge 列を組む ── 3 strategy 共通の経路復元
def collect_route_constraints(problem) -> tuple[set[str], list[str]]:  # (禁止エッジ, 必須経由)
def plan_route(start, goal, required, segment_fn) -> tuple[Segment | None, int]:
    # 経由順を optimize_waypoint_order で決め、区間ごとに segment_fn を呼んで連結。
    # 同じ区間は _SegmentCache が 1 度だけ解く。ops は全区間の合計。
def route_solution(seg, ops, meta, *, violations=None) -> CandidateSolution:
    # seg=None → infeasible。ops=None(ライブラリトラック)なら metrics に "_ops" を入れない。
```

- **中身は新規発明ではなく「`dijkstra.py::solve` のインライン処理を関数に起こしたもの」**:
  `Segment` は Phase 1 は `dijkstra.py` 内の非公開クラス `_Segment` だった(公開して移設)。
  `collect_route_constraints` は `solve` の制約収集ループ、`plan_route` は `_waypoints` +
  区間連結ループ、`route_solution` は `CandidateSolution` 構築、`reconstruct_path` は
  `_dijkstra_segment` 末尾の経路復元 ── どれも Phase 1 の `solve` / segment にベタ書きされていた
  処理をそのまま切り出した(§3.3 の before/after)。
- **`reconstruct_path` を公開(`_` なし)にして 3 strategy 共通にする**理由: 経路復元は
  「`prev` を辿るだけ」でアルゴリズム非依存 ── Dijkstra / Bellman-Ford / A* の `_xxx_segment` は
  どれも末尾がこれ。Phase 4 開始時点で消費者が 3 つと分かっているので、最初から共通の場所に置く
  (`dijkstra.py` に `_reconstruct` として `_` 付きで残すと、他の 2 つが import できず複製する)。
- 各 strategy は `_dijkstra_segment` / `_bellman_ford_segment` / `_astar_segment`(= 探索の本体)を
  書き、`plan_route(..., lambda a, b: _xxx_segment(adjacency, a, b))` を呼ぶだけになる。
  strategy ファイルが「アルゴリズムそのもの」に集中できる。
- **その `plan_route(...)` の呼び出し行を、さらに別関数でラップしない**(3 strategy で同じ形だが
  ラップしない)。`plan_route` 自体がすでに抽出済みの共通足回りで、その呼び出し行は
  「strategy が自分の区間ソルバ(`_xxx_segment`)を足回りに手渡す seam」── strategy ごとに
  見えているのが正しい。`関数名(start, goal, required, fn): return plan_route(start, goal, required, fn)`
  のようなラッパーは「名前を変えた `plan_route`」でしかなく、呼び出し側は結局同じ 4 引数を
  組み立てる ── ロジックゼロの間接層が増えるだけ。同じ理由で `solve` 本体もテンプレート化しない
  (本当に共通なのは `isinstance` ガードと `return route_solution(...)` だけで、負辺ガードの形は
  Bellman-Ford だけ違い、A* は `coords` を要る)。**共通化するのは *機構*(`plan_route` /
  `reconstruct_path` / `route_solution` / `collect_route_constraints` / `build_adjacency`)であって、
  *オーケストレーション*(`solve` 本体)ではない。**(相談ログ Q32)
- `_SegmentCache` が区間結果をメモ化する ── 順列全探索(4-4)で同じ (a, b) を何度も引くため。

---

## 3. `dijkstra.py` / `reachability.py` / `brute_force.py` の書き換え(既存への変更)

「共有プリミティブを独立させる」の裏側で、`build_adjacency` を使っていた 3 ファイルを直す。
**変更量は 3 ファイルで大きく違う** ── どの旧サンプルを新サンプルと突き合わせればよいかを先に:

| ファイル                                         | 旧サンプル(diff 元)                                   | 新サンプル(diff 先)                                   | 変更量                                      |
| -------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ---------------------------------------- |
| `app/algorithms/optimization/brute_force.py` | `Phase-3/samples/…/optimization/brute_force.py` | `Phase-4/samples/…/optimization/brute_force.py` | import 行 1 つ(`solve` 不変)                 |
| `app/algorithms/graph/reachability.py`       | `Phase-2/samples/…/graph/reachability.py`       | `Phase-4/samples/…/graph/reachability.py`       | import 元変更 + インライン → `plain_adjacency()` |
| `app/algorithms/graph/dijkstra.py`           | `Phase-1/samples/…/graph/dijkstra.py`           | `Phase-4/samples/…/graph/dijkstra.py`           | 大幅リファクタ(§3.3)                            |

### 3.1 `brute_force.py` ── import 行だけ

```python
# before                                          
from app.algorithms.graph.dijkstra  import build_adjacency
# after
from app.algorithms.graph.adjacency import build_adjacency
```

`solve` 本体は 1 文字も変わらない。全探索スタックの回し方も `_ops`(展開した部分パス数)の
数え方もそのまま。`build_adjacency` の**居場所**が変わっただけ。

### 3.2 `reachability.py` ── import + インライン述語の関数化

```python
# before(Phase 2)
from app.algorithms.graph.dijkstra import build_adjacency
...
plain = {node: [nxt for nxt, _eid, _w in edges] for node, edges in adjacency.items()}  # ← インライン
return data.goal in reachable_nodes(plain, data.start)

# after(Phase 4)
from app.algorithms.graph.adjacency import build_adjacency, plain_adjacency
...
return data.goal in reachable_nodes(plain_adjacency(adjacency), data.start)             # ← 関数呼び出し
```

Phase 2 でベタ書きしていた「重み付き隣接 → id だけの隣接」の内包表記が、§1 で
`adjacency.py::plain_adjacency` として関数になった。`reachability.py` は「呼ぶ側」に回るだけで挙動は不変。

### 3.3 `dijkstra.py` ── 4 つが外へ出て、`solve` が痩せる

Phase 1 の `dijkstra.py` は「グラフの作り方・区間の型・経由順・アルゴリズム・組み立て」を
1 ファイルに全部持っていた。Phase 4 で共有部分が独立するので、**4 つが出ていく**:

| Phase 1 の dijkstra.py にあったもの               | Phase 4 での行き先                                                                        | メモ     |
| ------------------------------------------ | ------------------------------------------------------------------------------------ | ------ |
| `build_adjacency` + `type _Adjacency`      | `adjacency.py`(`Adjacency` に改名・公開)                                                   | §1     |
| `_Segment` クラス                             | `segments.py`(`Segment` に改名・公開)                                                      | §2     |
| `_waypoints`(「与えられた順」)                     | 削除 → `waypoints.py::optimize_waypoint_order`(全順列版。深掘りは 4-4)。`segments.py::plan_route` が駆動 | §2     |
| `solve` 内の制約収集ループ                          | `segments.py::collect_route_constraints`                                             | 中身そのまま |
| `solve` 内の区間連結ループ + `CandidateSolution` 構築 | `segments.py::plan_route` + `route_solution`                                         | 中身そのまま |
| `solve` 内インラインの経路復元(`prev` を辿る)            | **`segments.py::reconstruct_path`(公開。dijkstra / bellman_ford / a_star が使う)**        | §2     |

**dijkstra.py に残るもの**: `_dijkstra_segment`(優先度キューでの最短経路 = アルゴリズム本体)、
`DijkstraStrategy`。経路復元は `segments.py` へ出た。

#### `_dijkstra_segment` の末尾 ── 経路復元は `segments.reconstruct_path` を呼ぶだけ

`_dijkstra_segment` 自体はほぼそのまま残るが、**末尾の経路復元は共通関数の呼び出し**になる。
`reconstruct_path` は `_reconstruct` を Bellman-Ford / A* でも使えるよう公開名で `segments.py` に
置いたもの(§2)── 「`prev` を辿るだけ」でアルゴリズム非依存だから:

```python
# before ── Phase 1: _dijkstra_segment の末尾(復元をインラインで書く)
    if goal not in settled:
        return None, pops
    node_ids = [goal]
    edge_ids: list[str] = []
    while node_ids[-1] != start:
        p_node, p_edge = prev[node_ids[-1]]
        node_ids.append(p_node)
        edge_ids.append(p_edge)
    node_ids.reverse()
    edge_ids.reverse()
    return _Segment(node_ids, edge_ids, dist[goal]), pops
```
```python
# after ── Phase 4: 復元は segments.reconstruct_path に。末尾は 1 行
from app.algorithms.graph.segments import reconstruct_path   # ← import に足す
    ...
    if goal not in settled:
        return None, pops
    return reconstruct_path(prev, start, goal, dist[goal]), pops   # ← return と , pops を落とさない
```
```python
# segments.py 側(全文は samples)── Phase 1 のインライン処理そのまま
def reconstruct_path(prev, start, goal, weight) -> Segment:
    node_ids = [goal]
    edge_ids: list[str] = []
    while node_ids[-1] != start:
        p_node, p_edge = prev[node_ids[-1]]
        node_ids.append(p_node)
        edge_ids.append(p_edge)
    node_ids.reverse()
    edge_ids.reverse()
    return Segment(node_ids, edge_ids, weight)
```

- `reconstruct_path` の第 4 引数は**距離**(`dist[goal]`)── `_dijkstra_segment` の中の変数。
  Bellman-Ford は `dist[goal]`、A* は `g[goal]` を渡す(名前が違うだけで意味は同じ「goal までの最短距離」)。
- 戻り値は `Segment`(node/edge 列 + 重み)。`_dijkstra_segment` は `(Segment | None, pops)` の
  タプルを返す契約のまま。

> **写経ミスの見分け方**: `TypeError: cannot unpack non-iterable NoneType object`(トレースは
> `segments.py` の `_SegmentCache.segment` を指す)が出たら、**`_dijkstra_segment`(or
> `_bellman_ford_segment` / `_astar_segment`)の末尾で `return … , pops` を写し損なった**印。
> `return` / `, pops` のどちらかを落とすと segment 関数が `None` を返し、`plan_route` が
> `seg, ops = segment_fn(a, b)` で落ちる。`reconstruct_path` は import 済みなので「関数を定義し忘れる」
> 罠は無い。

```python
# before ── Phase 1: dijkstra.py::solve(抜粋。~45 行。すべて 1 ファイル内で完結)
def solve(self, problem):
    data = problem.data
    if not isinstance(data, RouteData): raise TypeError(...)
    forbidden, required = set(), []                        # ── 制約収集(インライン)
    for c in problem.constraints:
        if isinstance(c, ForbiddenConstraint): forbidden.update(c.items)
        elif isinstance(c, RequiredInclusionConstraint): required.extend(c.items)
    adjacency = build_adjacency(data, forbidden)           # ── 同ファイル内の関数
    legs = _waypoints(data.start, data.goal, required)     # ── 同ファイル内(与えられた順)
    node_ids, edge_ids, total, total_ops = [], [], 0.0, 0  # ── 区間連結(インライン)
    for a, b in pairwise(legs):
        segment, ops = _dijkstra_segment(adjacency, a, b)
        total_ops += ops
        if segment is None: return CandidateSolution(status="infeasible", ...)
        node_ids.extend(...); edge_ids.extend(...); total += segment.weight
    return CandidateSolution(status="valid", assignments=RouteSolution(...), metrics={...})
```

```python
# after ── Phase 4: dijkstra.py::solve(抜粋。~20 行。共通処理は segments.py へ委譲)
def solve(self, problem):
    data = problem.data
    if not isinstance(data, RouteData): raise TypeError(...)
    forbidden, required = collect_route_constraints(problem)    # ← segments.py
    adjacency = build_adjacency(data, forbidden)                # ← adjacency.py
    if has_negative_weight(adjacency):                          # ← 負辺ガード(4-2 で追加)
        return route_solution(None, 0, self.meta,
                              violations=[negative_weight_violation("dijkstra")])
    seg, ops = plan_route(data.start, data.goal, required,      # ← segments.py(経由順 + 区間連結)
                          lambda a, b: _dijkstra_segment(adjacency, a, b))
    return route_solution(seg, ops, self.meta)                  # ← segments.py(CandidateSolution 構築)
```

- **`_dijkstra_segment` を `lambda a, b:` で渡す**のがこの設計の要 ── strategy は「区間 1 本の
  解き方」だけを提供し、「制約収集 → 隣接 → 経由順 → 連結 → 詰める」は `plan_route` が引き受ける。
  Bellman-Ford(4-2)/ A*(4-3)は `_bellman_ford_segment` / `_astar_segment` を書けば、`solve` は
  この 3 行そのままで済む。
- **挙動は Phase 1 と同一**。区間連結の順序・`_ops` の数え方・`total_weight` は不変で、
  写経先の `test_dijkstra_strategy.py`(Phase 1 のテスト)はそのまま緑 ── **だからこそ 4-1 写経後に
  再実行する**(進行のルール #16。§テスト観点)。赤ければ上の `_dijkstra_segment` /
  `reconstruct_path` 呼び出しの写経ミスがほぼ確実。負辺ガードだけ新しい振る舞い(4-2 で追加)。

**マーカー**(進行のルール #12): Phase 1 / 2 / 3 samples の `dijkstra.py` / `reachability.py` /
`brute_force.py` の冒頭に `# [以降 Phase で修正予定 ── Phase 4-1] ...`(dijkstra は `Phase 4-1 / 4-4`)を
付け、現行版(`Phase-4/samples/`)へ誘導する。コード本体はそのまま(その Phase を読む時点では
旧版で写経してよい)。

---

## 4. registry の配線

この章では registry に**何も足さない**。ただし Phase 4 全体を見越して、Phase 3 で
コメントアウトされている行はそのまま残す:

```python
# app/algorithms/registry.py(この章では変更なし)
"route_planning": [
    DijkstraStrategy(),
    BruteForceRouteStrategy(),
    # BellmanFordStrategy(),   ← 4-2 で有効化
    # AStarStrategy(),         ← 4-3 で有効化
    # NetworkxShortestPath(),  ← 4-5 で有効化
],
```

---

## 5. まとめ

- `build_adjacency` / `_Segment` / `_waypoints` / 経路復元を `dijkstra.py` から `adjacency.py` /
  `segments.py` / `waypoints.py` へ移設。`segments.py` は route 3 strategy の共通足回り(`Segment` /
  `collect_route_constraints` / `plan_route` / `route_solution` / **`reconstruct_path`**)= 旧
  `dijkstra.py::solve` / segment のインライン処理。`reconstruct_path` は 3 strategy が共通で使うので
  公開(`_` なし)にした。
- 消費者 3 ファイルの直し方は不揃い ── `brute_force.py` は import 1 行、`reachability.py` は
  import + `plain_adjacency()` 化、`dijkstra.py` は `solve` が委譲に痩せる(§3)。
- `waypoints.py` の骨格を 4-1 で作る(samples は end 状態 = 全順列版)。0〜1 経由なら「与えられた順」と
  同じ挙動なので、4-1〜4-3 は samples のまま写経してよい。`optimize_waypoint_order` の中身
  (2 点以上の必須経由を全順列で最適化)の深掘りは 4-4。
- `union_find` / `connectivity` / `build_link_adjacency` は Phase 5(消費者は Kruskal / 連結性ゲート)。
- 既存テスト(Phase 1 の `test_dijkstra_strategy.py`)は緑のまま ── 挙動は不変、置き場所だけ変わった。

## テスト観点(`samples/tests/unit/test_graph_primitives.py` + `test_dijkstra_strategy.py`)

3 ファイル(`adjacency` / `segments` / `waypoints`)を作り `dijkstra.py` を大改修する章なので、
テストは **`test_graph_primitives.py` が主**(章が作る全ファイルを踏む)+ Phase 1 の
`test_dijkstra_strategy.py` を再実行(#16 の補助の番人)。`test_graph_primitives.py` は
プリミティブの単体テストに加えて **`DijkstraStrategy().solve()` の統合スモーク**を持ち、
`dijkstra.py` リファクタの写経ミス(`_dijkstra_segment` の末尾)をその場で赤にする。

> **テスト対象(SUT)/ ドライバ / スタブ**(進行のルール #14):
>
> - **`test_graph_primitives.py`**
>   - **対象**: `build_adjacency` / `plain_adjacency` / `has_negative_weight`(adjacency.py)、
>     `plan_route` / `collect_route_constraints` / `route_solution`(segments.py)、
>     `optimize_waypoint_order`(waypoints.py)、**`DijkstraStrategy.solve` の統合スモーク**
>     (adjacency → segments → waypoints → `_dijkstra_segment` → `reconstruct_path` の連鎖)
>   - **ドライバ**: このテスト関数。`build_route_problem` が入力生成
>   - **スタブ**: adjacency 系と統合スモークは**不要**(純粋)。`plan_route` / `optimize_waypoint_order`
>     は **区間ソルバ / コスト関数をフェイク**にする(`_fake_segment_fn` / `lambda _a, _b: 1.0`)──
>     segments.py が「区間の解き方」を注入できる設計だから、実グラフ・実 Dijkstra 無しで
>     連結ロジックだけをテストできる(§2)。これがレイヤー分離の配当
> - **`test_dijkstra_strategy.py`**(Phase 1 のテストの現行版)
>   - **対象**: `DijkstraStrategy.solve` の**公開挙動**(最短経路 / total_weight / _ops の決定性 /
>     produced_by)。内部は `adjacency` → `segments` → `waypoints` → `_dijkstra_segment` →
>     `reconstruct_path` の連鎖を素通しで踏む
>   - **ドライバ**: このテスト関数。**スタブ不要**(solve は純粋)
>   - アサーションは Phase 1 のまま変えない ── 4-1 は内部リファクタで挙動は不変だから

| ファイル | ケース | 期待 |
| --- | --- | --- |
| graph_primitives | 無向エッジ | `adj["A"]` に B、`adj["B"]` に A の両方向 |
| graph_primitives | forbidden 指定 | その edge id がどの隣接にも現れない |
| graph_primitives | `plain_adjacency` | weight / edge_id が落ちて id だけの隣接になる |
| graph_primitives | `has_negative_weight` | 負辺 1 本で True、非負なら False |
| graph_primitives | `plan_route` にフェイク区間 2 本 | ノード列連結・境界ノード重複除去・weight 合計・ops 合計 |
| graph_primitives | フェイクが `None` を返す区間 | `plan_route` は `(None, ops)` |
| graph_primitives | `collect_route_constraints` | `({"e_bd"}, ["C"])` |
| graph_primitives | `optimize_waypoint_order`(0 / 1 経由) | `["A","E"]` / `["A","C","E"]` |
| graph_primitives | **統合スモーク** `DijkstraStrategy().solve()` | `status="valid"` / 最短 `["A","B","D","E"]` / weight 5(赤 = `_dijkstra_segment` 末尾の写経ミス) |
| dijkstra_strategy | 禁止・必須なし | 最短 `["A","B","D","E"]` / weight 5 |
| dijkstra_strategy | 橋禁止 + C 必須 | `["A","B","C","E"]` / weight 9 |
| dijkstra_strategy | 到達不能 | `status="infeasible"` / path 空 |
| dijkstra_strategy | 同じ入力を 2 回 solve | `model_dump()` 一致(決定性) |

> **4-1 写経後、必ず両方を回す**:
> ```bash
> uv run pytest tests/unit/test_graph_primitives.py tests/unit/test_dijkstra_strategy.py
> ```
> - `test_graph_primitives.py` は `segments` → `waypoints` と import を辿るので、3 ファイルの
>   どれかの**写経漏れで collection が赤**。統合スモークが `dijkstra.py` の**写経ミスで赤**
>   (`TypeError: cannot unpack non-iterable NoneType object` → `_dijkstra_segment` の末尾を見る)。
>   旧版は adjacency しか import せず、どちらも素通ししていた ── 進行のルール #15 / #16 で是正。
> - `test_dijkstra_strategy.py`(Phase 1)は**公開挙動の回帰**。赤なら同じく写経ミス。テストは正しい。

`uvx pyright app/algorithms/graph tests/unit/test_graph_primitives.py`。

---

次章([Phase-4-2](./Phase-4-2.md))では、作業単位 4-2 ── `RouteEdge.weight` の `Field(ge=0)` を外し
`RouteData.allow_negative` を足して、負辺と負閉路を扱う `BellmanFordStrategy` を作る。
