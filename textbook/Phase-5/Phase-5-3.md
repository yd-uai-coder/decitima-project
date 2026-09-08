# Phase 5-3: network_design problem_type の配線(作業単位 5-3)

## この章のゴール

「すべての拠点を最小コストで接続する」(README §12.6 Network Designer)は最小全域木(MST)。
`route_planning` は start→goal の**単一経路**なので、辺集合を返す MST は表現できない ──
新しい `problem_type` が要る。`Phase-0-2.md` §8.1 が設計済みで、`Phase-1-1.md` §5 が
「既存に触れず足せる」ことを予告していた。

**判別可能ユニオンにメンバーを 1 つずつ足すだけ**で、route / shift のコードには一切触らない。
**新しい DB テーブルも作らない**(hybrid JSONB。`alembic upgrade head` は no-op)。

触るファイルは多いが、依存の向きは一方向。**下の順に写経する**:

1. `domain/problems/network_design.py` / `domain/solutions/network_design.py` ── 葉。
   以降のほぼ全ファイルがこれを import する(§1)
2. `domain/problems/problem.py` / `domain/solutions/solution.py` / `domain/problems/__init__.py`
   ── 判別可能ユニオンに 1 メンバー、re-export(§2)
3. `algorithms/graph/adjacency.py` に `build_link_adjacency` / `algorithms/graph/connectivity.py`
   (新規)── グラフ・プリミティブ。**services より先**(§3)
4. `domain/problems/semantic.py`(§4)/ `domain/solutions/structure.py`(§5)── domain の純粋述語
5. `services/{validation,algorithm_selection}.py`(§4)/ `services/verification.py`(§5)
   ── 3・4 を呼ぶオーケストレーション
6. `domain/constraints/{forbidden,required_inclusion}.py` ── 制約チェッカーに network 分岐(§6)
7. `tests/fixtures/optimization.py`(network fixture、§8.1)→
   `tests/unit/{test_graph_primitives,test_network_design,test_mst_properties}.py`(§3.3 / §8 / §8）

**この章で作成 / 更新するファイル**: `app/domain/problems/network_design.py`、
`app/domain/solutions/network_design.py`、`app/algorithms/graph/connectivity.py`、
`tests/unit/test_network_design.py`、`tests/unit/test_mst_properties.py`。
**既存ファイルへの変更**(現行版は samples): `app/domain/problems/{problem,__init__,semantic}.py`、
`app/domain/solutions/{solution,structure}.py`、`app/domain/constraints/{forbidden,required_inclusion}.py`、
`app/algorithms/graph/adjacency.py`(`build_link_adjacency` 追加)、
`app/services/{validation,verification,algorithm_selection}.py`、
`tests/fixtures/optimization.py`(network fixture ── `build_network_problem` /
`build_network_solution` / `build_disconnected_network_problem` / `_NETWORK_LINKS` を追加)、
`tests/unit/test_graph_primitives.py`(**現行版** = Phase 4-1 の route プリミティブテストに
`build_link_adjacency` / `connectivity` の 4 テストを追記。route 分の assertion は 4-1 のまま)。

対応サンプル: 上記すべて。テストは
`textbook/samples/tests/unit/{test_graph_primitives,test_network_design,test_mst_properties}.py`。

- `test_graph_primitives.py` ── §3 のプリミティブ(`build_link_adjacency` / `connectivity`)の番人。
- `test_network_design.py` ── スキーマ / semantic / 構造検証 / 制約チェッカー(9 本)。
  validate→select→solve→verify のフルパイプラインは 5-4(registry が Kruskal / Prim で埋まる章)。
- `test_mst_properties.py` ── [Phase-5-2](./Phase-5-2.md) の MST 理論(cut / cycle property)を
  全域木の全列挙で実測。列挙オラクルが `forms_spanning_tree`(§3 の `connectivity.py`)と
  `NetworkDesignData` / `NetworkLink`(§1 の葉)に依存するので、5-2 でなくこの章の成果物にした
  (進行のルール #15)。§8 参照。

設計は `Phase-0-2.md` §8.1、`Phase-2-2.md` §3(計算 / 述語 / オーケストレーションの切り分け)。

---

## 1. 葉モジュール ── `NetworkDesignData` / `NetworkDesignSolution`

```python
# app/domain/problems/network_design.py(全文は samples)
class NetworkNode(BaseModel):
    id: str
    label: str | None = None

class NetworkLink(BaseModel):
    id: str
    endpoints: tuple[str, str]    # ← 常に無向。route の source/target と揃えない
    weight: float

class NetworkDesignData(BaseModel):
    problem_type: Literal["network_design"] = "network_design"
    nodes: list[NetworkNode]
    links: list[NetworkLink]      # この中から最小コストで全拠点を繋ぐ部分集合を選ぶ

# app/domain/solutions/network_design.py
class NetworkDesignSolution(BaseModel):
    problem_type: Literal["network_design"] = "network_design"
    selected_link_ids: list[str]  # 全域木なら len = ノード数 - 1
    total_weight: float
```

- **`NetworkLink.endpoints: tuple[str, str]`** ── route の `RouteEdge`(`source` / `target` /
  `directed`)と**あえて揃えない**。敷設リンクは常に無向(A-B のケーブルは A→B でも B→A でもない)。
  型が「このドメインでは向きが無い」ことを表す。
- 葉なので兄弟(`route_planner.py` / `shift_scheduler.py`)を import しない。ユニオンの合成は
  `problem.py` / `solution.py` が行う(`Phase-0-2.md` §2.5 / Q2)。

> **[以降 Phase で修正予定 ── Phase 5-3]** ── この節が Phase 1 の `problem.py` / `solution.py` /
> `__init__.py` を書き換える(ユニオンを 3 メンバーに)。Phase 1〜4 を読む時点では 2 メンバー
> (route / shift)のまま写経してよい。

---

## 2. ユニオンへの追加

```python
# app/domain/problems/problem.py
from app.domain.problems.network_design import NetworkDesignData
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData, Field(discriminator="problem_type")
]
class OptimizationProblem(BaseModel):
    problem_type: Literal["route_planning", "shift_scheduling", "network_design"]
    ...

# app/domain/solutions/solution.py

type SolutionData = Annotated[
    RouteSolution | ShiftSolution | NetworkDesignSolution, Field(discriminator="problem_type")
]
```

`__init__.py` に `NetworkDesignData` / `NetworkNode` / `NetworkLink` を re-export
(利用側は `from app.domain.problems import NetworkDesignData` と書ける)。

---

## 3. グラフ・プリミティブ ── `build_link_adjacency` / `connectivity.py`

`validation.py` / `verification.py` の network 分岐が呼ぶ**計算**を先に用意する。どちらも
`AlgorithmStrategy` ではなく **アルゴリズム・プリミティブ**(registry に載らない素の純粋関数。
`Phase-0-4.md` §2.4)。route の `route_reachable` / `build_adjacency` と同じ位置づけ。

### 3.1 `build_link_adjacency`(`adjacency.py` に追加)

```python
# app/algorithms/graph/adjacency.py(追加。全文は samples)
from app.domain.problems.network_design import NetworkDesignData  # ← module top に追加

def build_link_adjacency(data: NetworkDesignData, forbidden_link_ids: set[str]) -> Adjacency:
    """NetworkDesignData から重み付き隣接リストを作る。リンクは常に無向。"""
    adjacency: Adjacency = {node.id: [] for node in data.nodes}
    for link in data.links:
        if link.id in forbidden_link_ids:
            continue
        a, b = link.endpoints
        adjacency.setdefault(a, []).append((b, link.id, link.weight))
        adjacency.setdefault(b, []).append((a, link.id, link.weight))
    return adjacency
```

- `Adjacency`(= `dict[str, list[tuple[str, str, float]]]`)は Phase 4-1 で `adjacency.py` に定義済み。
  route の `build_adjacency` と**関心事(グラフの作り方)が同じ**なので同居させる。
- リンクは常に無向 → 両端に `(相手, link_id, weight)` を張る(`build_adjacency` は
  `edge.directed` を見て逆向きを張るか決めるが、こちらは常に両向き)。
- `forbidden_link_ids` に入った id はスキップ(`ForbiddenConstraint` で外されたリンク)。
- **`adjacency.py` は `network_design.py` を module top で import する**。`adjacency.py` は route の
  Dijkstra / Bellman-Ford / A* / BruteForce / `reachability` も import 元にしているので、ここで`network_design.py`(§1 の葉)の写経が済んでいないと **route のテストごと collection が赤**になる
  ── だから §1 → §3 の順。`adjacency.py` の module docstring も更新(samples 参照)。

### 3.2 `connectivity.py`(新規)── 連結性クエリ

```python
# app/algorithms/graph/connectivity.py(要点。全文は samples)
from app.algorithms.graph.adjacency import Adjacency, plain_adjacency
from app.algorithms.search.bfs import reachable_nodes   # Phase 1〜2 で作成済み

def all_nodes_connected(node_ids: Iterable[str], adjacency: Adjacency) -> bool:
    """adjacency 上で node_ids 全部が 1 つの連結成分に入っていれば True。0〜1 ノードは True。"""
    ids = list(node_ids)
    if len(ids) <= 1:
        return True
    reached = reachable_nodes(plain_adjacency(adjacency), ids[0])
    return all(nid in reached for nid in ids)

def forms_spanning_tree(node_ids: Iterable[str], link_pairs: Iterable[tuple[str, str]]) -> bool:
    """link_pairs が node_ids 全体を繋ぐ全域木か ──「辺数 == V-1」かつ「連結」なら閉路は無い(木の性質)。"""
    ...
```

- 責務: `network_design` の 2 つのグラフ計算 ──「敷設可能リンク全体で全拠点が連結か」
  (`all_nodes_connected`、Validation の hard ゲート)と「選んだリンクが全域木の形か」
  (`forms_spanning_tree`、Verification が使う。§5)。
- **どちらも既存の `bfs.reachable_nodes` の薄い合成**。`all_nodes_connected` は
  `plain_adjacency`(重み付き → id だけ)を挟んで 1 回 BFS。`forms_spanning_tree` は
  `link_pairs` から素の隣接を組んで BFS + 辺数チェック。
- **なぜ `domain` でなく `algorithms` か** ── BFS を走らせる「**計算**」だから
  (`Phase-2-2.md` §3 の「計算か? 述語か?」)。`domain` は `algorithms` を import できない
  (`Phase-0-3.md` §2.2 の依存方向)。判定(hard ゲートにするか)は `services` が決める。
- `union_find` は import しない(あちらは Kruskal 専用。連結性は BFS で足りる。
  `Phase-5-introduction.md` §3)。registry には**載せない**。

### 3.3 `test_graph_primitives.py` に network の 4 テストを追記(現行版)

`build_link_adjacency` × 2(無向で両端に張る / forbidden をスキップ)、`all_nodes_connected`
(連結 / 非連結 fixture)、`forms_spanning_tree`(木 / 閉路+孤立 / 辺数不足)。**この 4 本が
§3 の写経ミスの第一の番人**(#15 ── 章が作る全ファイルをその章のテストが 1 度は import する)。

Phase 4-1 の route プリミティブテスト(adjacency / segments / waypoints /
`test_dijkstra_solve_still_works_after_segments_refactor`)は**そのまま残す** ── `adjacency.py` に
`build_link_adjacency` を足す変更で route 分が壊れていないことをここで確認する(#16)。

---

## 4. Semantic Validation ── 「計算か? 述語か?」

`network_design` の検査は 3 種類。**純粋述語**(フィールドを見るだけ)は `semantic.py`、
**計算**(§3 の `all_nodes_connected`)は `services/validation.py` が呼ぶ:

| 検査                              | 種類               | 置き場所                                                                                 |
| ------------------------------- | ---------------- | ------------------------------------------------------------------------------------ |
| リンクの `endpoints` が nodes に実在するか | **純粋述語**         | `semantic.py::check_network_link_endpoints`(整合欠陥 → `ProblemValidationError`)         |
| 拠点 2 つ以上でリンク候補が空 → 全域木は作れない     | 純粋述語             | `semantic.py::check_network_has_links`(`infeasible=True` → `InfeasibleProblemError`) |
| 敷設可能リンク全体で**全拠点が連結**か           | **計算**(§3 の BFS) | `graph/connectivity.py::all_nodes_connected` を `services/validation.py` が呼ぶ          |

これは `Phase-2-2.md` §3 の切り分けそのもの ── route の到達可能性を `route_reachable`
(algorithms)に置き、判定は `validation.py`(services)がやったのと同じ。

```python
# app/domain/problems/semantic.py(追加。全文は samples)
def check_network_link_endpoints(problem: OptimizationProblem) -> list[SemanticIssue]:
    """各リンクの endpoints が nodes に実在するか(整合欠陥)。"""
    if not isinstance(problem.data, NetworkDesignData):
        return []
    node_ids = {n.id for n in problem.data.nodes}
    return [
        SemanticIssue(f"link {link.id!r} references unknown node {endpoint!r}")
        for link in problem.data.links
        for endpoint in link.endpoints
        if endpoint not in node_ids
    ]

def check_network_has_links(problem: OptimizationProblem) -> list[SemanticIssue]:
    """拠点が 2 つ以上あるのに敷設可能リンクが空 → 全域木は作れない(infeasible)。"""
    if not isinstance(problem.data, NetworkDesignData):
        return []
    if len(problem.data.nodes) >= 2 and not problem.data.links:
        return [SemanticIssue("... no candidate links", infeasible=True)]
    return []

SEMANTIC_CHECKS["network_design"] = [check_network_link_endpoints, check_network_has_links]
```

- どちらも `(OptimizationProblem) -> list[SemanticIssue]`(既存の `SemanticCheck` シグネチャ)。
  先頭の `isinstance` ガードで他 problem_type を素通す(route / shift の検査と同じ定石)。
- `SemanticIssue.infeasible` の差が呼び出し側の例外を分ける ── 未知 id 参照は「直せる不整合」
  (`ProblemValidationError` 400)、リンクゼロは「原理的に解なし」(`InfeasibleProblemError` 400)。

```python
# app/services/validation.py(route_reachable 呼び出しの隣に分岐を追加)
elif isinstance(problem.data, NetworkDesignData):
    adjacency = build_link_adjacency(problem.data, forbidden)     # ← §3.1
    if not all_nodes_connected((n.id for n in problem.data.nodes), adjacency):  # ← §3.2
        infeasible.append("candidate links ... cannot connect all nodes")
```

**`select_strategy` に 1 行**(Phase 4-5 で route の分岐だけ入れた `_preferred_name`):

```python
# app/services/algorithm_selection.py
if problem.problem_type == "network_design":
    return "kruskal"        # ← この 1 行を足す。registry["network_design"] は 5-4 で新設
```

`registry["network_design"]` はまだ空なので、この時点では `select_strategy` は
`NoAlgorithmError`(候補ゼロ)。5-4 で Kruskal / Prim を登録して初めて解ける。

---

## 5. 構造検証 ── 純粋述語は domain、全域木チェックは services

```python
# app/domain/solutions/structure.py::verify_network_structure(純粋述語のみ)
#   - 選んだ link が実在 id か
#   - len(selected) == len(nodes) - 1(全域木の辺数)
#   - total_weight == 選んだ link の weight 和
#   - link の endpoints が実在ノードか

# app/services/verification.py::_verify_spanning_tree(グラフ計算)
#   forms_spanning_tree(node_ids, [link.endpoints for 選んだ link])   ← §3.2
#   → 「辺数 V-1 かつ連結」なら閉路なし(木の性質)。違反なら network_structure hard violation
```

- **`verify_network_structure` は連結性・非閉路を見ない** ── それは `forms_spanning_tree`
  (§3.2 の `connectivity.py`)を走らせる計算で、`domain` は `algorithms` を import できない。
  `SolutionVerificationService` が両方を呼んで違反リストをまとめる。
- 教材の狙い(進行のルール #14 の趣旨): 「このチェックはどの層のものか?」を毎回問う。
  「辺の数を数える」は述語(domain)、「本当に木になっているか BFS で確かめる」は計算(algorithms)。

---

## 6. 既存の制約チェッカーが network 解にも効く

```python
# app/domain/constraints/forbidden.py / required_inclusion.py(要点)
def _used_element_ids(solution) -> set[str] | None:
    if isinstance(solution.assignments, RouteSolution):
        return set(solution.assignments.path_edge_ids)
    if isinstance(solution.assignments, NetworkDesignSolution):
        return set(solution.assignments.selected_link_ids)   # ← 追加
    return None
```

- **「必須リンク」→ `RequiredInclusionConstraint`(items = link id)、「使えないリンク」→
  `ForbiddenConstraint`** ── `CHECKERS` レジストリは変更不要(kind ベース)。チェッカー関数だけ
  「network 解では `selected_link_ids` を見る」分岐を足す。
- `numeric_bound` は `metrics["total_weight"]` を読むので**無変更**で network に効く
  (「総敷設コスト ≤ X」)。
- これが「新しい problem_type でも既存の検証機構がそのまま動く」= 共通スキーマ設計の成果。

---

## 7. パイプラインの確認 ── ルート・サービスは無変更

`SolveService` / `VerifyService` / `BenchmarkService` は「registry を回すオーケストレーション」
なので、`POST /api/v1/solve` に `network_design` problem を投げるだけで通る。専用エンドポイントは
作らない(`Phase-0-7.md` の狙いどおり)。`alembic upgrade head` は no-op(新テーブルなし)。

ただし `registry["network_design"]` は 5-4 まで空なので、**validate→select→solve→verify の
フルパイプラインが緑になるのは 5-4**(`test_mst_strategies.py::test_network_design_end_to_end_pipeline`)。
この章の `test_network_design.py` はスキーマ / semantic / 構造検証 / チェッカーまで(9 本)。

---

## 8. network fixture と MST 理論の実測 ── `test_mst_properties.py`

`NetworkDesignData` / `NetworkLink`(§1)と `forms_spanning_tree`(§3.2)がこの章で揃った。
これで [Phase-5-2](./Phase-5-2.md) の cut property / cycle property を、小グラフの**全域木の
全列挙**で実測できる ── 5-2 は理論だけを説明し、schema が揃うここで裏を取る。

### 8.1 network fixture(`tests/fixtures/optimization.py` に追加)

```python
# tests/fixtures/optimization.py(要点。全文は samples)
# 5 拠点。既知の MST: L_ab(1) + L_bc(2) + L_cd(3) + L_be(4) = 10
_NETWORK_LINKS = [
    NetworkLink(id="L_ab", endpoints=("A", "B"), weight=1),
    NetworkLink(id="L_bc", endpoints=("B", "C"), weight=2),
    NetworkLink(id="L_cd", endpoints=("C", "D"), weight=3),
    NetworkLink(id="L_be", endpoints=("B", "E"), weight=4),
    NetworkLink(id="L_ac", endpoints=("A", "C"), weight=5),   # 閉路 A-B-C-A の最重量辺
    NetworkLink(id="L_de", endpoints=("D", "E"), weight=6),
    NetworkLink(id="L_ae", endpoints=("A", "E"), weight=7),
]

def build_network_problem(*, objectives=..., constraints=...) -> OptimizationProblem: ...
def build_network_solution(selected_link_ids, total_weight) -> CandidateSolution: ...
def build_disconnected_network_problem() -> OptimizationProblem:  # 孤立ノードあり(infeasible 用)
```

- **重みを全て相異なる整数**にした ── MST が一意になり、テストの期待値がぶれない。
- `build_network_problem` はこの章のテスト(`test_network_design.py`)と 5-4 の
  `test_mst_strategies.py` も入力に使う共有 fixture。`NetworkDesignData`(§1 の葉)を import
  するので、この fixture は 5-3 より前には置けない。
- `build_disconnected_network_problem` は §4 の Validation テスト(候補リンクで全拠点が
  繋がらない → `InfeasibleProblemError`)と 5-4 の infeasible ケース用。

### 8.2 全域木の全列挙を正解オラクルにする(`tests/unit/test_mst_properties.py`)

```python
# tests/unit/test_mst_properties.py(要点。全文は samples)
def _all_spanning_trees(node_ids, links) -> list[tuple[NetworkLink, ...]]:
    """リンク候補から (V-1) 本を選ぶ組み合わせのうち、全域木になるものを全列挙(小グラフ専用)。"""
    need = max(len(node_ids) - 1, 0)
    return [combo for combo in combinations(links, need)
            if forms_spanning_tree(node_ids, [link.endpoints for link in combo])]
```

- `forms_spanning_tree`(§3.2 で作った `connectivity.py`)を**テストダブルなしで直接使う** ──
  「辺数 V-1 かつ連結」の純粋述語。§5 で `SolutionVerificationService` が使うために作ったものを、
  ここでは列挙のフィルタとして再利用する。
- Phase 3 の `BruteForceRouteStrategy` と同じ発想 ── **小規模で厳密解を出し、貪欲アルゴリズムの
  裏取りに使う**。5-4 の Kruskal / Prim も「総コスト == 既知の最小 10」で照合する。

| ケース(`test_mst_properties.py`)      | 期待                                 |
| ---------------------------------- | ---------------------------------- |
| `_all_spanning_trees` の最小重み        | `10.0`(fixture の既知 MST)            |
| カット `{A}` の最小 crossing edge `L_ab` | 全列挙した MST のいずれかに含まれる(cut property) |
| 閉路 A-B-C-A の最重量辺 `L_ac`            | どの MST にも含まれない(cycle property)     |

---

## 9. まとめ

- 写経は葉 → ユニオン → **グラフ・プリミティブ(§3)** → domain 述語 → services → チェッカー →
  fixture → テストの順。`build_link_adjacency` / `connectivity.py` を services より先に。
- `NetworkDesignData` / `NetworkDesignSolution` をユニオンに 1 項目ずつ足す。route / shift は無変更。
- リンクは無向(`endpoints: tuple`)── route の有向エッジと型で区別。
- semantic / structure は「純粋述語」だけ domain に、「連結性の計算」(`connectivity.py`)は
  algorithms に置き services が呼ぶ。
- 既存の forbidden / required_inclusion / numeric_bound チェッカーが network 解にも効く。
- 新テーブルなし・専用ルートなし ── ハイブリッドスキーマ設計の狙いどおり。
- schema と `forms_spanning_tree` が揃ったので、5-2 の MST 理論を全域木の全列挙で実測(`test_mst_properties.py`)。

## テスト観点(`textbook/samples/tests/unit/{test_graph_primitives,test_network_design,test_mst_properties}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_graph_primitives.py`**(§3 のプリミティブの番人。現行版 = Phase 4-1 route + network 4 本)
> 
> - **対象**: `build_link_adjacency`(`adjacency.py`)/ `all_nodes_connected` / `forms_spanning_tree`
>   (`connectivity.py`)。route 分(adjacency / segments / waypoints / dijkstra リファクタの
>   統合スモーク)は 4-1 の assertion のまま ── `adjacency.py` に手を入れて route が壊れていないか(#16)
> - **ドライバ**: このテスト関数。network 分は `build_network_problem` /
>   `build_disconnected_network_problem` が入力生成
> - **スタブ**: network 分は**不要**(純粋関数)。route 分の `plan_route` / `optimize_waypoint_order`
>   はフェイクの区間ソルバ / コスト関数を注入(4-1)
> 
> **`test_network_design.py`**(9 本)
> 
> - **対象**: `NetworkDesignData` の判別可能ユニオン解決、`semantic` チェック、
>   `verify_network_structure`、`ProblemValidationService` / `SolutionVerificationService` の network 分岐
> - **ドライバ**: このテスト関数。`build_network_problem` / `build_network_solution` /
>   `build_disconnected_network_problem` が入力生成
> - **スタブ**: **不要** ── スキーマは純粋な値オブジェクト、検査は純粋関数。
>   `ProblemValidationService` も DB / Redis を触らない
> - フルパイプライン(validate→select→solve→verify)は **5-4** の `test_mst_strategies.py`
>   ── `registry["network_design"]` が空のうちは `select_strategy` が `NoAlgorithmError`(#15)
> 
> **`test_mst_properties.py`**(5-2 の理論の実測 ── §8)
> 
> - **対象**: 「全域木の全列挙」を正解オラクルとした MST の性質(cut / cycle property / 既知 MST)。
>   `forms_spanning_tree`(§3.2 の `connectivity.py`)を列挙のフィルタとして直接使う
> - **ドライバ**: このテスト関数。`_all_spanning_trees` / `_min_trees` ヘルパ + `build_network_problem` fixture
> - **スタブ**: **不要** ── すべて純粋(小グラフの組み合わせ列挙)。Kruskal / Prim はまだ無い(5-4)ので
>   アルゴリズム実装に依存しない ── 「MST とは何か」だけを固める

| ケース                                     | 期待                                                             |
| --------------------------------------- | -------------------------------------------------------------- |
| `build_link_adjacency`(無向 / forbidden)  | 両端に張る / forbidden id は不在(`test_graph_primitives`)              |
| `all_nodes_connected`(連結 / 非連結)         | True / False(`test_graph_primitives`)                          |
| `forms_spanning_tree`(木 / 閉路+孤立 / 辺数）   | True / False / False(`test_graph_primitives`)                  |
| `build_network_problem()`               | `problem_type == data.problem_type == "network_design"`        |
| top と data の problem_type 不一致           | `model_validator` が `ValidationError`                          |
| `SEMANTIC_CHECKS["network_design"]`     | `check_network_link_endpoints` / `check_network_has_links`     |
| 連結な候補リンク                                | `validate` が例外なし                                               |
| forbidden で分断                           | `InfeasibleProblemError`                                       |
| 全域木の形の手組み解                              | `verify_network_structure == []`                               |
| 閉路 + 孤立を含む手組み解                          | verify 後 `status == "invalid"` / `network_structure` violation |
| forbidden / required チェッカー on network 解 | それぞれ違反を検出、`detail["missing"]`                                  |

`uv run pytest tests/unit/test_graph_primitives.py tests/unit/test_network_design.py tests/unit/test_mst_properties.py` /
`uvx pyright app/algorithms app/domain app/services`。

---

次章([Phase-5-4](./Phase-5-4.md))では、作業単位 5-4 ── `network_design` を実際に解く
Kruskal(5-1 の `UnionFind` を使う)/ Prim(heapq)と networkx_mst を作り、`registry` に
`"network_design"` キーを新設する。この章の `build_network_problem` fixture を
`test_mst_strategies.py` がそのまま再利用する。
