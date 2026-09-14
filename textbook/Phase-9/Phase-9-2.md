# Phase 9-2: logistics_common(共通足回り)+ Verification(作業単位 9-2)

## この章のゴール

9-1 で `LogisticsData` / `LogisticsSolution` の骨格が揃った。この章では、5 つの strategy(9-3〜9-6)が共有する「配送先の集まり → 実際に回る順+距離」の変換を 1 箇所に集約する ──
`travel_common.py`(Phase 7-4)/ `project_common.py`(Phase 8-4)と同じ役割の
`logistics_common.py`。あわせて `services/verification.py` に容量・距離の検算
(`_verify_logistics_routes`)を追加する。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/logistics_common.py`(新規)、
`tests/unit/test_logistics_common.py`(新規)。**既存への変更**(現行版は samples):
`app/services/verification.py`(`_verify_logistics_routes` 追加、`# (Phase 9-2)`)。

設計は `Phase-7-4.md`(travel_common)/ `Phase-8-4.md`(project_common)── 同型の共通足回り。

---

## 1. `logistics_common.py` ── 5 strategy の共通足回り

```python
# app/algorithms/optimization/logistics_common.py(全文は samples)
def parse_logistics_problem(problem) -> tuple[LogisticsData, set[str]]:
    """(LogisticsData, 使えない道路区間 id) を返す。"""

def all_pairs(data: LogisticsData, forbidden_segment_ids: set[str]) -> AllPairs:
    """道路網全体の全点対距離(Floyd-Warshall。7-1 の再利用)。strategy が1度計算して使い回す。"""

def capacity_ok(vehicle: Vehicle, stops: list[DeliveryStop]) -> bool:
    """stops を1台の vehicle にまとめて積めるか(重量・体積の両方)。"""

def route_for_vehicle(depot_id: str, stops: list[DeliveryStop], dist: AllPairs) -> tuple[list[str], float] | None:
    """1台分の配送先を回る最短順(TSP近似の再利用)と往復距離。回れないなら None。"""

def route_distance(depot_id: str, node_order: list[str], dist: AllPairs) -> float:
    """*与えられた順*の往復距離(検算専用。再最適化しない)。"""

def logistics_solution(data, assignment: Mapping[str, list[str]], dist, meta, *, ops) -> CandidateSolution:
    """vehicle ごとの配送先集合を実際の順+距離へ確定し CandidateSolution に詰める。"""

def infeasible_logistics_solution(meta: AlgorithmMeta) -> CandidateSolution: ...
```

- `route_for_vehicle` は `optimize_waypoint_order(depot_id, depot_id, ...)` を**デポを起点=終点の閉路**として呼ぶ(travel の `order_and_cost` が anchor に戻る閉路として呼ぶのと同じ発想)。
  返る `node_order` は必ず `[depot, ...訪問順..., depot]` の形なので、**中間だけを取り出すには`node_order[1:-1]` が要る**(`node_order[:-1]` だけでは先頭のデポが residual で残る ──
  写経の罠)。
- 同じノードに複数配送先があってもよい ── `by_node` でノードごとにグルーピングし、TSP はノード単位で解いてから配送先 id の列に展開する。
- `route_distance` は「strategy が申告した順」をそのまま検算する専用関数 ──
  `route_for_vehicle` が内部で呼ぶ「最適化した後の確定計算」と、Verification が呼ぶ「申告値の裏取り」を同じ関数に統一し、数値が絶対にズレないようにする(`travel_common.tour_cost` と同じ設計)。

> **写経の罠**: `route_for_vehicle` の `node_order[1:-1]` を `node_order[:-1]` と書き間違えると、`stop_ids` の先頭にデポの id が紛れ込む。9-3 以降の strategy テストで`set(stop_ids) == {配送先の id 集合}` のようなアサーションが `AssertionError` になったら、まずここを疑う(間接的なエラーほど有効 ── `_dijkstra_segment` の教訓と同型。Q30)。

---

## 2. Verification ── 容量・距離の検算

```python
# app/services/verification.py(追加。全文は samples)
def _verify_logistics_routes(problem, solution) -> list[ConstraintViolation]:
    """各車両の容量を超えていないか(hard)/ 申告した distance が実際の巡回距離と合うか(hard)。

    Floyd-Warshall で全点対距離を出し直し、solution.routes の各 stop_ids の順
    (再最適化しない)で距離を積んで比べる。合わなければ strategy が嘘をついている。
    """
```

- `_verify_logistics_routes` は `SolutionVerificationService.verify` の `structural` リストに
  `_verify_travel_plan` / `_verify_project_resources` と並んで追加する。
- **容量違反**は `constraint_kind="logistics_capacity"`、**距離の不整合**は
  `constraint_kind="logistics_structure"`(9-1 の構造検証と同じ kind ── どちらも「解の形が壊れている」という同種の問題として扱う)。
- travel の `_verify_travel_plan` / project の `_verify_project_resources` と同じ切り分け:
  「純粋な形の整合」は 9-1 の `verify_logistics_structure`(domain)、「グラフ計算を伴う裏取り」はここ(services)。

---

## 3. まとめ

- `logistics_common.py` は Phase 4/7 のプリミティブ(`floyd_warshall` / `optimize_waypoint_order`)
  を**1 バイトも変えず**再利用する ── Phase 9 に新規プリミティブがほぼ無い理由がここに表れる。
- `route_for_vehicle` / `route_distance` の二本立ては travel の
  `order_and_cost` / `tour_cost` と同じ設計判断(最適化と検算を同じ計算ロジックに統一し、strategy と Verification の数値が drift しないようにする)。
- Verification の追加は `_verify_logistics_routes` の 1 本のみ。9-1 の `verify_logistics_structure`
  (純粋)と役割が重ならないよう「容量・距離の実測」に限定している。

## テスト観点(`textbook/samples/tests/unit/test_logistics_common.py`)

> **テスト対象 / ドライバ / スタブ**
> 
> - **対象**: `parse_logistics_problem` / `all_pairs` / `capacity_ok` / `route_for_vehicle` /
>   `route_distance` / `logistics_solution` / `infeasible_logistics_solution`(いずれも純粋)、
>   `SolutionVerificationService`(容量・距離の検算)
> - **ドライバ**: このテスト関数。`build_logistics_problem`(9-1)で問題を、
>   `build_logistics_solution`(9-1)で手組みの解を作る ── **strategy はまだ存在しない**(9-3〜9-6)
>   ので、`logistics_solution` の呼び出しはこのテストが直接行う
> - **スタブ**: **不要** ── いずれも純粋(DB / Redis を触らない)

| ケース                                        | 期待                                                          |
| ------------------------------------------ | ----------------------------------------------------------- |
| `parse_logistics_problem` に別 problem_type  | `TypeError`                                                 |
| `forbidden` constraint から区間 id を抽出         | 集合が一致                                                       |
| `all_pairs` の手計算との突き合わせ                    | D-N1=4 / D-N2=3 / N1-N3=5 / N2-N3=3                         |
| 禁止区間ありの `all_pairs`                        | 迂回した距離になる                                                   |
| `capacity_ok`                              | 重量・体積どちらか一方でも超えれば False                                     |
| `route_for_vehicle`(P1,P2)                 | `stop_ids` が {P1,P2}、距離 9.0                                 |
| `route_for_vehicle([])`                    | `([], 0.0)`                                                 |
| `route_distance` と `route_for_vehicle` の整合 | 同じ距離を返す                                                     |
| 道路が無いときの `route_for_vehicle`               | `None`                                                      |
| `logistics_solution`(V1={P1,P2}, V2={P3})  | `total_distance == 21.0`、`vehicles_used == 2.0`             |
| 空リストの vehicle                              | routes に含まれない                                               |
| 回れない `logistics_solution`                  | `status == "infeasible"`                                    |
| 正直な解の検証                                    | `logistics_structure` / `logistics_capacity` の violation なし |
| distance を嘘の値にした解                          | `logistics_structure` violation、`status == "invalid"`       |
| 容量を超える割当                                   | `logistics_capacity` violation、`status == "invalid"`        |

`uv run pytest tests/unit/test_logistics_common.py` / `uvx pyright app/algorithms/optimization app/services`。

---

次章([Phase-9-3](./Phase-9-3.md))では、作業単位 9-3 ── `KnapsackDpLogisticsStrategy`(主力)。
車両を1台ずつ `knapsack_2d`(Phase 7-2 の再利用)で容量に収まる配送先の部分集合を選び、
`logistics_common.route_for_vehicle` で巡回順と実距離を確定する。
