# Phase 9-1: logistics_planning problem_type の配線(作業単位 9-1)

## この章のゴール

「複数車両で複数配送先を分担して回る」(README §12.5)は、これまでの route(単一経路)/network(全域木)/ travel(部分集合)/ project(スケジュール)のどれとも違う、新しい
`problem_type` `logistics_planning` が要る。**Phase 5-3(network)/ 7-3(travel)/ 8-3(project)で新 problem_type を足した手順がそのまま雛形**。判別可能ユニオンにメンバーを 1 つずつ足すだけで、既存 5 problem_type のコードには一切触れず、**新しい DB テーブルも作らない**(hybrid JSONB。
`alembic upgrade head` は no-op)。

**project との共通点が 1 つ**: logistics にも「計算ゲート」が要る ── **「デポから全配送先へ
道路網で到達できるか」**。これは BFS を走らせる計算なので、`domain/problems/semantic.py`(純粋述語)ではなく `services/validation.py` が判定する ──「これは計算か? 述語か?」(`Phase-2-2.md` §3)の **5 例目**(route の到達可能性 → network の連結性 → project の非巡回性に続く)。

Phase 9 には Phase 7-1/7-2 や 8-1/8-2 のような「章単位のプリミティブ新設」が無い ── 使うプリミティブ(Floyd-Warshall / Knapsack DP / TSP 近似)がすべて Phase 4・7 で完成済みのため、9-1 はいきなりドメイン配線から始まる。

触るファイルは多いが依存は一方向。**下の順に写経する**:

1. `domain/problems/logistics.py` / `domain/solutions/logistics.py` ── 葉。
   以降のほぼ全ファイルがこれを import する(§1)
2. `domain/problems/problem.py` / `domain/solutions/solution.py` / それぞれの `__init__.py`── 判別可能ユニオンに 1 メンバー、re-export(§2)
3. `domain/problems/semantic.py`(§3)/ `domain/solutions/structure.py`(§4)── domain の純粋述語
4. `algorithms/graph/{adjacency,reachability}.py` ── 到達可能性クエリの追加(§5)
5. `services/validation.py` ── 到達可能性ゲート(§6)
6. `tests/fixtures/optimization.py`(logistics fixture、§7)→ `tests/unit/test_logistics_planning.py`

> **`services/verification.py` の容量・距離の検算(`_verify_logistics_routes`)はこの章では書かない。** `logistics_common.py`(9-2)がまだ無く、9-1 で
> `from app.algorithms.optimization.logistics_common import ...` を足すと **collection が`ImportError` で全崩れ**する(`verification.py` は `solve.py` / `benchmark.py` / 多数のテストがimport)。9-2 で `logistics_common` と一緒に足す(進行のルール #15。前例 Q34 / Q41 / Q42)。

**この章で作成 / 更新するファイル**: `app/domain/problems/logistics.py`、
`app/domain/solutions/logistics.py`(新規)、`tests/unit/test_logistics_planning.py`。
**既存への変更**(現行版は samples): `app/domain/problems/{problem,__init__,semantic}.py`、
`app/domain/solutions/{solution,__init__,structure}.py`、
`app/algorithms/graph/{adjacency,reachability}.py`、`app/services/validation.py`、
`tests/fixtures/optimization.py`(logistics fixture ── `build_logistics_problem` /
`build_disconnected_logistics_problem` / `build_scaled_logistics_problem` /
`build_logistics_solution`)。`app/services/verification.py` の検算は **9-2**。

設計は `Phase-0-2.md` §8.1、`Phase-5-3.md` / `Phase-7-3.md` / `Phase-8-3.md`(同型の配線)、
`Phase-2-2.md` §3。

---

## 1. 葉モジュール ── `LogisticsData` / `LogisticsSolution`

```python
# app/domain/problems/logistics.py(全文は samples)
class LogisticsNode(BaseModel):
    id: str
    label: str | None = None
    x: float | None = None
    y: float | None = None

class RoadSegment(BaseModel):
    id: str
    source: str
    target: str
    distance: float = Field(ge=0)
    directed: bool = False           # False なら双方向(一方通行なら True)

class Vehicle(BaseModel):
    id: str
    capacity_weight: float = Field(ge=0)
    capacity_volume: float = Field(ge=0)   # Knapsack DP の2次元容量に対応

class DeliveryStop(BaseModel):
    id: str
    node_id: str
    demand_weight: float = Field(ge=0)
    demand_volume: float = Field(ge=0)

class LogisticsData(BaseModel):
    problem_type: Literal["logistics_planning"] = "logistics_planning"
    depot_id: str
    nodes: list[LogisticsNode]
    segments: list[RoadSegment]
    vehicles: list[Vehicle]
    deliveries: list[DeliveryStop]

    @model_validator(mode="after")
    def _refs_and_ids(self) -> LogisticsData:
        # depot / 区間端点 / 配送先の node_id が実在するか、各 id が一意か、自己ループ禁止
        # 到達可能性は「走査」なので見ない ── validation.py が判定する

# app/domain/solutions/logistics.py
class VehicleRoute(BaseModel):
    vehicle_id: str
    stop_ids: list[str]     # この車両が訪れる配送先(DeliveryStop.id)の訪問順。デポは含まない
    distance: float         # デポ発 → 訪問順 → デポ着の往復距離

class LogisticsSolution(BaseModel):
    problem_type: Literal["logistics_planning"] = "logistics_planning"
    routes: list[VehicleRoute]   # 使わない車両は含めない
    total_distance: float        # Σ route.distance
```

- **道路網はノード + 区間**(`RouteData` に近い一般グラフ)── travel の `TravelData`(ほぼ完全グラフの `legs`)とは違う設計。README「Route Optimization」が Dijkstra/A* を挙げているのは一般グラフを前提にしているため。Phase 9 では全点対距離を **Floyd-Warshall**(Phase 7-1、密行列で十分な規模)で前処理する ── 個別の Dijkstra 呼び出しは行わない。
- **容量・需要は重量・体積の 2 次元**(Knapsack DP がそのまま使える。Phase 7 の予算×時間と同型)。README「Packing Optimization」に対応。
- **`DeliveryStop.node_id` は道路網のノードを指す**(1 ノードに複数配送先があってもよい ──9-2 の `logistics_common.route_for_vehicle` がノード単位でグルーピングして TSP を回す)。
- 葉なので兄弟(`route_planner.py` 等)を import しない。travel が独自の `TravelLeg` を持つのと同じ理由で `RouteEdge` を再利用せず `RoadSegment` を独自に定義する(進行のルール #17 ──
  「以前の Phase を過剰に触らない」は明文ルールではないが、ここは共通化を**駆動する消費者が無い**ので見送りが正しい判断)。

---

## 2. ユニオンへの追加

```python
# app/domain/problems/problem.py
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData | TravelData | ProjectData
    | LogisticsData,   # (Phase 9-1)
    Field(discriminator="problem_type"),
]
class OptimizationProblem(BaseModel):
    problem_type: Literal[
        "route_planning", "shift_scheduling", "network_design", "travel_planning",
        "project_scheduling", "logistics_planning",  # (Phase 9-1)
    ]

# app/domain/solutions/solution.py
type SolutionData = Annotated[
    RouteSolution | ShiftSolution | NetworkDesignSolution | TravelSolution | ProjectSolution
    | LogisticsSolution,   # (Phase 9-1)
    Field(discriminator="problem_type"),
]
```

`domain/problems/__init__.py` に `LogisticsNode` / `RoadSegment` / `Vehicle` / `DeliveryStop` / `LogisticsData` を、`domain/solutions/__init__.py` に `LogisticsSolution` / `VehicleRoute` を re-export + `__all__`。`AlgorithmFamily`(`domain/solutions/solution.py` の Literal)は変更しない
── logistics の strategy は `family="optimization"` を再利用する(travel と同じ判断。§3 で後述)。

---

## 3. Semantic Validation ── 純粋述語だけ

```python
# app/domain/problems/semantic.py(追加。全文は samples)
def check_logistics_vehicles_exist(problem) -> list[SemanticIssue]:
    """配送先があるのに車両が1台も無ければ、誰も配送できない(infeasible)。"""

def check_logistics_capacity_feasible(problem) -> list[SemanticIssue]:
    """1件の配送先の需要が、どの車両の容量にも収まらないなら infeasible。
    project の resource_capacity / travel の budget_feasible と同型。"""

def check_logistics_fleet_capacity_covers_demand(problem) -> list[SemanticIssue]:
    """全車両の容量合計が全配送先の需要合計を下回るなら infeasible(必要条件。
    十分条件ではない ── 地理的な組合せの可否は「計算」なので strategy の solve に委ねる)。"""

SEMANTIC_CHECKS["logistics_planning"] = [
    check_logistics_vehicles_exist,
    check_logistics_capacity_feasible,
    check_logistics_fleet_capacity_covers_demand,
]
```

- 参照整合(depot / 区間端点 / 配送先の node_id)は `LogisticsData.model_validator` が既にやる (travel が leg 端点を、project が依存の端点を `model_validator` でやるのと同じ ── network だけsemantic 側でやる歴史的経緯)。だから semantic は「問題全体を見ないと分からない」3 つに絞る。
- `check_logistics_fleet_capacity_covers_demand` は**必要条件の粗いチェック**であることを明示する ── project の「1 タスクの需要 > capacity」のような厳密な判定と違い、「容量の合計は足りているが地理的にどう詰めても破綻する」ケースはここでは弾けない(それは strategy の solve が`infeasible` を返す形で表現する)。

---

## 4. 構造検証 ── 純粋述語は domain

```python
# app/domain/solutions/structure.py(追加)
#   structural_verify に 6 本目の isinstance arm  # (Phase 9-1)
def verify_logistics_structure(data: LogisticsData, sol: LogisticsSolution) -> list[ConstraintViolation]:
    """配送計画の「形」を検証(純粋述語のみ)。すべて hard:
      - 全配送先が重複なくちょうど1台の車両に割り当て済み(missing / duplicate を検出)
      - route.vehicle_id が実在し、同じ車両が複数 route に現れない
      - total_distance == Σ route.distance
    """
```

- **容量の再チェックと距離の再計算(Floyd-Warshall)はここでやらない** ── それは全点対距離を走らせる「計算」で、`domain` は `algorithms` を import できない(`Phase-0-3.md` §2.2)。
  `SolutionVerificationService` が **9-2** の `_verify_logistics_routes`
  (`logistics_common.all_pairs` / `route_distance` を使う)で行う。project の
  `verify_project_structure`(純粋)vs `_verify_project_resources`(imos 検算)と同じ切り分け。
- **`test_structural_verify_dispatches_logistics` は arm 未接続で赤になる形にする**(Q44 と同型)
  ── `total_distance` を意図的にズラした解を `structural_verify` **経由**で踏ませ、
  `constraint_kind == "logistics_structure"` の violation が返ることをアサートする。

---

## 5. 到達可能性クエリ ── `algorithms/graph/{adjacency,reachability}.py`

```python
# app/algorithms/graph/adjacency.py(追加)
def build_logistics_adjacency(data: LogisticsData, forbidden_segment_ids: set[str]) -> Adjacency:
    """LogisticsData から重み付き隣接リストを作る。build_adjacency(RouteData)と同型。"""

# app/algorithms/graph/reachability.py(追加)
def logistics_deliveries_reachable(data: LogisticsData, forbidden_segment_ids: set[str]) -> bool:
    """禁止区間を除いた道路網で、デポから全配送先ノードへ到達可能なら True(複数ターゲット版)。"""
```

`route_reachable`(単一 goal)の複数ターゲット版。`ForbiddenConstraint.items` は logistics では**道路区間の id**(route / network と同じ解釈。travel の「place を除外」とは違う)── 禁止区間は実際の距離計算(9-2 の `all_pairs`)にも効くので、Verification も同じ forbidden 集合で再計算する。

---

## 6. 到達可能性ゲート ── `services/validation.py`

```python
# app/services/validation.py(追加。全文は samples)
from app.algorithms.graph.reachability import logistics_deliveries_reachable  # (Phase 9-1)
from app.domain.problems.logistics import LogisticsData                       # (Phase 9-1)
...
        elif isinstance(problem.data, LogisticsData):   # project の has_cycle 分岐と同型
            if not logistics_deliveries_reachable(problem.data, forbidden):
                infeasible.append(
                    f"not all deliveries are reachable from depot {problem.data.depot_id!r} "
                    f"after removing {len(forbidden)} forbidden segment(s)"
                )
```

- `test_unreachable_delivery_is_infeasible` は `build_disconnected_logistics_problem()`
  (配送先の 1 つが道路で繋がっていない)で `InfeasibleProblemError`(match `"reachable"`)を確認。
- **`SolveService` / `VerifyService` / `BenchmarkService` は無変更** ── registry を回すだけ。
  ただし `registry["logistics_planning"]` は 9-7 まで空なので、フルパイプラインが緑になるのは 9-7。
  この章の `test_logistics_planning.py` はスキーマ / semantic / 構造検証 / 到達可能性ゲートまで。

---

## 7. logistics fixture(`tests/fixtures/optimization.py` に追加)

```python
# tests/fixtures/optimization.py(要点。全文は samples)
# デポ D + 3 配送先。D-N1=4, D-N2=3, D-N3=6, N1-N2=2, N2-N3=3(全区間無向)。
# 容量 10 に対し demand は P1=4, P2=5, P3=7 ── P1+P2=9 は収まるが P1+P3=11 / P2+P3=12 は超える。
# 2 台に分けると必ず {P1,P2}(距離 D-N1-N2-D=9)+ {P3}(距離 D-N3-D=12)= 21 になる
# (これ以外の分け方は容量オーバーで作れない)。5 strategy が一致して 21 を出すはずの最小例。
def build_logistics_problem(*, vehicles=None, deliveries=None, forbidden=None) -> OptimizationProblem: ...
def build_disconnected_logistics_problem() -> OptimizationProblem: ...  # 配送先の1つが孤立
def build_scaled_logistics_problem(n_deliveries, *, seed=0, n_vehicles=None) -> OptimizationProblem: ...
def build_logistics_solution(routes: list[tuple[str, list[str], float]], ...) -> CandidateSolution: ...
```

- **fixture の設計は 9-3〜9-6 の教材の核に合わせてある**: 容量が「{P1,P2} + {P3}」の 1 通りしか許さないので、knapsack_dp / greedy / branch_and_bound / brute_force / pulp_milp の**どれもが total_distance=21・vehicles_used=2 に一致するはず**(9-7 の end-to-end テストが確認する最小の一致点)。DP の「容量だけ見て移動距離を無視する」という違いが実際に効いてくる(手実装同士が食い違う)ケースは `build_scaled_logistics_problem` のランダム規模比較(9-7 のプロパティテスト、`quality_ratio`)で確認する。
- `build_scaled_logistics_problem` は `build_scaled_project_problem` と同型 ── seed 固定でRNG 呼び出し順を固定し決定論に。9-7 のオラクル比較・プロパティテストが使う。

---

## 8. まとめ

- 写経は葉 → ユニオン → semantic → structure → adjacency/reachability → validation → fixture→ テストの順。
- `LogisticsData` / `LogisticsSolution` をユニオンに 1 項目ずつ。route / network / shift /travel / project は無変更。
- 道路網はノード + 区間(一般グラフ)、容量・需要は重量・体積の 2 次元。到達可能性は`validation.py` が `logistics_deliveries_reachable` で(計算 / 述語の 5 例目)。
- 容量・距離の検算 `verification.py::_verify_logistics_routes` は **9-2**
  (`logistics_common` が要る)。この章の `verify_logistics_structure` は純粋述語だけ。
- `constraints/elements.py` は変更不要(logistics 解は全配送先を実施 ── forbidden /
  required_inclusion は非該当。未知の解型 → `None` → チェッカー素通し。Phase 8 と同型)。
  `numeric_bound` は `metrics["total_distance"]` を読むので無変更で効く(9-7 で確認)。

## テスト観点(`textbook/samples/tests/unit/test_logistics_planning.py`)

> **テスト対象 / ドライバ / スタブ**
> 
> - **対象**: `LogisticsData` / `LogisticsSolution` の判別可能ユニオン解決、
>   `LogisticsData.model_validator`、`SEMANTIC_CHECKS["logistics_planning"]`、
>   `verify_logistics_structure`、`structural_verify` の logistics ディスパッチ arm、
>   `ProblemValidationService.validate`(到達不能 → `InfeasibleProblemError`)
> - **ドライバ**: このテスト関数。`build_logistics_problem` / `build_disconnected_logistics_problem`
>   / `build_logistics_solution` が入力生成。`problem.data` は
>   `assert isinstance(..., LogisticsData)` で絞る
> - **スタブ**: **不要** ── スキーマは純粋な値オブジェクト、検査は純粋関数。
>   `ProblemValidationService` も DB / Redis を触らない
> - **`test_structural_verify_dispatches_logistics` は arm 未接続で赤になる形にする**(Q44、§4 参照)
> - フルパイプライン(validate→select→solve→verify)は **9-7**(`registry["logistics_planning"]` が
>   空のうちは `select_strategy` が `NoAlgorithmError` ── #15)

| ケース                                            | 期待                                                            |
| ---------------------------------------------- | ------------------------------------------------------------- |
| `build_logistics_problem()`                    | `problem_type == data.problem_type == "logistics_planning"`   |
| top と data の problem_type 不一致                  | `model_validator` が `ValidationError`                         |
| 未知の depot / 区間端点 / 配送先ノードを指す / 重複 id / 自己ループ区間 | `LogisticsData` の `model_validator` が `ValidationError`       |
| `SEMANTIC_CHECKS["logistics_planning"]`        | 3 チェック登録                                                      |
| 配送先はあるが車両ゼロ                                    | `InfeasibleProblemError`                                      |
| 1件の需要がどの車両の容量も超える                              | `InfeasibleProblemError`                                      |
| 需要合計が容量合計を超える                                  | `InfeasibleProblemError`                                      |
| 配送先の1つが道路で孤立                                   | `InfeasibleProblemError`(match `"reachable"`)                 |
| 整合した手組みルート                                     | `verify_logistics_structure == []`                            |
| 配送先の欠落 / 重複 / distance 不整合 / 未知 vehicle_id     | それぞれ violation                                                |
| `structural_verify`(distance 不整合の解を経由)         | `metrics == {}` / `logistics_structure` violation(arm 未接続なら赤) |

`uv run pytest tests/unit/test_logistics_planning.py` / `uvx pyright app/domain app/services`。

---

次章([Phase-9-2](./Phase-9-2.md))では、作業単位 9-2 ── `logistics_common.py`(共通足回り。
Floyd-Warshall / TSP 近似の再利用で「1 台分の巡回順+距離」を確定する)と、
`verification.py` の `_verify_logistics_routes`(容量・距離の検算)を実装する。
