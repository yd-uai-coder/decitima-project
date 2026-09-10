# Phase 7-3: travel_planning problem_type の配線(作業単位 7-3)

## この章のゴール

「予算・時間内で効用最大の旅行プランを組む」(README §12.3)は route の単一経路でも network の全域木でも表現できない ── 新しい `problem_type` `travel_planning` が要る。**Phase 5-3 で`network_design` を足した手順がそのまま雛形**。判別可能ユニオンにメンバーを 1 つずつ足すだけで、route / network / shift のコードには一切触れず、**新しい DB テーブルも作らない**
(hybrid JSONB。`alembic upgrade head` は no-op)。

**network との違いが 1 つ**: travel には Validation の「計算ゲート」が無い。route の到達可能性 /network の連結性は「解けない問題を弾く BFS 計算」だったが、travel の訪問順(Floyd-Warshall +`optimize_waypoint_order`)は **strategy の仕事**であって Validation の仕事ではない ──
`services/validation.py` に travel の分岐は足さない。

触るファイルは多いが依存は一方向。**下の順に写経する**:

1. `domain/problems/travel_planner.py` / `domain/solutions/travel_planner.py` ── 葉。
   以降のほぼ全ファイルがこれを import する(§1)
2. `domain/problems/problem.py` / `domain/solutions/solution.py` / それぞれの `__init__.py`
   ── 判別可能ユニオンに 1 メンバー、re-export(§2)
3. `domain/problems/semantic.py`(§3)/ `domain/solutions/structure.py`(§4)── domain の純粋述語
4. `domain/constraints/elements.py`(新規)+ `{forbidden,required_inclusion}.py` ── 解 →
   要素 id 集合を共通化 + travel arm(§5)
5. `tests/fixtures/optimization.py`(travel fixture、§6)→ `tests/unit/test_travel_planning.py` /
   `tests/unit/test_constraint_checkers.py`(現行版)

> **`verification.py` の巡回コスト検算(`_verify_travel_plan`)はこの章では書かない。** `tour_cost` /`all_pairs` は `travel_common`(7-4)にあり、7-3 で `from app.algorithms.optimization.travel_common import ...` を足すと `travel_common` がまだ無く **collection が `ImportError` で全崩れ**する
> (`verification.py` は `solve.py` / `benchmark.py` / 約 8 テストが import)。7-4 で `travel_common` と
> 一緒に足す(進行のルール #15。前例 Q34 / Q41 / Q42)。

**この章で作成 / 更新するファイル**: `app/domain/problems/travel_planner.py`、
`app/domain/solutions/travel_planner.py`、`app/domain/constraints/elements.py`(新規 ──
forbidden / required_inclusion が共有する解 → 要素 id 集合)、`tests/unit/test_travel_planning.py`。
**既存への変更**(現行版は samples): `app/domain/problems/{problem,__init__,semantic}.py`、
`app/domain/solutions/{solution,__init__,structure}.py`、
`app/domain/constraints/{forbidden,required_inclusion}.py`(私設ヘルパを `elements.py` へ抽出)、
`tests/fixtures/optimization.py`(travel fixture ── `build_travel_problem` / `build_scaled_travel_problem` /
`build_travel_solution` / `_TRAVEL_PLACES` / `_TRAVEL_LEGS`)、`tests/unit/test_constraint_checkers.py`
(**現行版** = Phase 2 の checker テストに travel 解の 2 テストを追記。既存の assertion は不変)。
`app/services/verification.py` の travel arm は **7-4**。

設計は `Phase-0-2.md` §8.1、`Phase-5-3.md`(同型の配線)、`Phase-2-2.md` §3(計算 / 述語の切り分け)。

---

## 1. 葉モジュール ── `TravelData` / `TravelSolution`

```python
# app/domain/problems/travel_planner.py(全文は samples)
class Place(BaseModel):
    id: str
    name: str | None = None
    value: float                    # 基本効用(負でもよい ── 嫌々寄る場所)
    cost: float = Field(ge=0)       # 入場料など
    duration: float = Field(ge=0)   # 滞在時間

class TravelLeg(BaseModel):
    id: str
    endpoints: tuple[str, str]      # ← 常に無向(network の NetworkLink と同じ)
    travel_cost: float = Field(ge=0)
    travel_time: float = Field(ge=0)

class TravelData(BaseModel):
    problem_type: Literal["travel_planning"] = "travel_planning"
    places: list[Place]
    legs: list[TravelLeg]
    budget: float = Field(ge=0)         # place cost + 移動 cost の上限
    time_budget: float = Field(ge=0)    # place duration + 移動 time の上限
    start: str | None = None            # 起点 place の id(任意)
    preferences: dict[str, float] = Field(default_factory=dict)  # place_id -> 好み係数

    @model_validator(mode="after")
    def _refs_exist(self) -> TravelData:
        """leg 端点 / start / preferences のキーが places に実在するか(Input Validation)。"""
        # 未知 id を参照する leg / start / preferences キーがあれば ValueError

# app/domain/solutions/travel_planner.py
class TravelSolution(BaseModel):
    problem_type: Literal["travel_planning"] = "travel_planning"
    selected_place_ids: list[str]
    visit_order: list[str]        # selected の順列。start があれば先頭
    total_value: float
    total_cost: float
    total_time: float
```

- **`TravelLeg.endpoints: tuple[str, str]`** ── `NetworkLink` と同じく常に無向。route の`RouteEdge`(source / target / directed)とは型で区別する。
- **`model_validator` に Input Validation を寄せる**(`Phase-1-1.md` §2 と同じ) ── leg の端点 /start / preferences のキーが実在 place を指すか。Semantic Validation(§3)は「問題全体を見ないと分からない」ものだけ担当する。
- 葉なので兄弟(`route_planner.py` / `shift_scheduler.py` / `network_design.py`)を import しない。

---

## 2. ユニオンへの追加

```python
# app/domain/problems/problem.py
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData | TravelData,   # (Phase 7-3)
    Field(discriminator="problem_type"),
]
class OptimizationProblem(BaseModel):
    problem_type: Literal[
        "route_planning", "shift_scheduling", "network_design", "travel_planning"  # (Phase 7-3)
    ]

# app/domain/solutions/solution.py
type SolutionData = Annotated[
    RouteSolution | ShiftSolution | NetworkDesignSolution | TravelSolution,   # (Phase 7-3)
    Field(discriminator="problem_type"),
]
```

`domain/problems/__init__.py` に `Place` / `TravelData` / `TravelLeg` を、
`domain/solutions/__init__.py` に `TravelSolution` を re-export + `__all__`。

> **ついで修正**: `domain/solutions/__init__.py` の `__all__` に `NetworkDesignSolution` が
> 欠けていた(既存の不整合)── Phase 7 で補う(`# (Phase 7-3)` タグ)。

---

## 3. Semantic Validation ── 純粋述語だけ、計算ゲートは無し

```python
# app/domain/problems/semantic.py(追加。全文は samples)
def check_travel_place_refs(problem) -> list[SemanticIssue]:
    """訪問候補が空 ── 予算・時間があっても何も選べない(整合欠陥 → ProblemValidationError)。"""

def check_travel_budget_feasible(problem) -> list[SemanticIssue]:
    """一番安い place ですら予算を超える ── 1 つも訪れられない(infeasible=True)。"""

def check_travel_time_feasible(problem) -> list[SemanticIssue]:
    """一番短い滞在時間ですら time_budget を超える(infeasible=True)。"""

SEMANTIC_CHECKS["travel_planning"] = [
    check_travel_place_refs, check_travel_budget_feasible, check_travel_time_feasible,
]
```

- 3 本とも `(OptimizationProblem) -> list[SemanticIssue]`。先頭の `isinstance(problem.data, TravelData)`
  ガードで他 problem_type を素通す。
- **`infeasible` の差が例外を分ける** ── 候補ゼロは「直せる不整合」(`ProblemValidationError` 400)、最安 place > 予算は「原理的に解なし」(`InfeasibleProblemError` 400)。
- **`services/validation.py` に travel 分岐は足さない** ── route の `route_reachable` / network の`all_nodes_connected` に相当する「計算ゲート」が travel には無い。訪問順を繋げるかは strategy が`order_and_cost`(7-4)で判定し、繋げなければ `status="infeasible"` の候補を返す。
  これが `Phase-2-2.md` §3「これは計算か? 述語か? どの層の責務か?」の答え ──
  travel の「回れるか」は **solve の責務**であって Validation の責務ではない。

---

## 4. 構造検証 ── 純粋述語は domain

```python
# app/domain/solutions/structure.py(追加)
#   structural_verify に 4 本目の isinstance arm  # (Phase 7-3)
def verify_travel_structure(data: TravelData, sol: TravelSolution) -> list[ConstraintViolation]:
    """旅行プランの「形」を検証(純粋述語のみ):
      - selected_place_ids が実在 place か
      - visit_order が selected_place_ids の順列か(集合一致 + 重複なし)
      - total_value == Σ place.value * preference(申告値の検算)
      - total_cost / total_time が budget / time_budget を hard で超えないか
    """
```

- **移動費用の再計算はここでやらない** ── それは Floyd-Warshall を走らせる「計算」で、
  `domain` は `algorithms` を import できない(`Phase-0-3.md` §2.2)。`SolutionVerificationService`が **7-4** の `_verify_travel_plan`(`travel_common.tour_cost` を使う)で行う。network の
  `verify_network_structure`(辺数を数える)vs `forms_spanning_tree`(BFS で木を確かめる)の切り分けと同じ。
- `total_cost > data.budget + 1e-9` を hard 違反にするのは、DP が「移動無視の選択」を返して実際は予算超過、というケースを弾くため(この Phase の教材の核。7-5 で実演)。

> **`_verify_travel_plan` は 7-4 で**(§5 でなく)── 巡回コストの検算は `travel_common.all_pairs` /
> `tour_cost`(7-4)が要る。ここで `verification.py` に import を足すと `travel_common` が無く
> collection が全崩れ(進行のルール #15)。7-3 の `verify_travel_structure`(上)は純粋述語だけで
> `total_cost` フィールドの範囲は見るが、**巡回して積み直した実コストとの照合はしない** ── それが 7-4。

---

## 5. 既存の制約チェッカーが travel 解にも効く

`forbidden` / `required_inclusion` はどちらも「解が触れた要素 id の集合」を作って
`constraint.items` と突き合わせるだけ。その**集合を作る部分**を 7-3 で
`constraints/elements.py` に一本化する。

```python
# app/domain/constraints/elements.py(新規 ── forbidden / required_inclusion が共有)
type ElementAspect = Literal["nodes", "edges"]

def solution_element_ids(solution, *, aspect: ElementAspect) -> set[str] | None:
    """解が触れた要素の id 集合。対象外の解型は None(チェッカーは素通し)。"""
    assignments = solution.assignments
    if isinstance(assignments, RouteSolution):
        # route だけ node / edge を区別。required は経由ノード、forbidden は通行エッジ
        ids = assignments.path_node_ids if aspect == "nodes" else assignments.path_edge_ids
        return set(ids)
    if isinstance(assignments, NetworkDesignSolution):
        return set(assignments.selected_link_ids)
    if isinstance(assignments, TravelSolution):
        return set(assignments.selected_place_ids)
    return None

# app/domain/constraints/forbidden.py(要点)
used = solution_element_ids(solution, aspect="edges")   # 使った接続
# app/domain/constraints/required_inclusion.py(要点)
present = solution_element_ids(solution, aspect="nodes")  # 訪問・経由した地点
```

> **重複の解消(進行のルール #17)** ── `forbidden.py` / `required_inclusion.py` は
> Phase 2 以来、解 → 要素 id 集合の私設ヘルパ(`_used_element_ids` /
> `_present_element_ids`)を各自コピーで持ち、**Phase 5-3(network arm)/ 7-3(travel arm)が
> 同一の分岐を両方に足していた**(drift ハザードが実測で 2 回)。7-3 で
> `elements.solution_element_ids` に一本化 ── route の nodes/edges だけ `aspect` で分岐。
> `check_forbidden` / `check_required_inclusion` の公開シグネチャ・戻り値・既存テストの
> assertion は不変(挙動を変えない抽出)。凍結した以前の Phase のファイルを触ってでも
> 重複を残さない実例(Q38 `shift_metrics.py` と同型)。5 つ目の problem_type を足すとき、
> この分岐を直すのは **1 箇所**で済む。

- **「必須訪問地」→ `RequiredInclusionConstraint`(items = place id)、「行かない場所」→`ForbiddenConstraint`** ── `CHECKERS` レジストリは変更不要(kind ベース)。`elements.py` に travel arm を 1 つ足すだけ。
- `numeric_bound` は `metrics["total_cost"]` / `["total_time"]` / `["total_value"]` を読むので**無変更**で travel に効く(「総費用 ≤ X」など。7-5 の `test_end_to_end_invalid_when_numeric_bound_violated`)。
- `staffing` は shift 専用 ── travel には無関係(先頭ガードで素通し)。

---

## 6. travel fixture(`tests/fixtures/optimization.py` に追加)

```python
# tests/fixtures/optimization.py(要点。全文は samples)
_TRAVEL_PLACES = [
    Place(id="P0", name="home", value=0, cost=0, duration=0),   # 起点
    Place(id="P1", value=10, cost=4, duration=2),               # place cost 合計(P1..P4)= 18
    Place(id="P2", value=8,  cost=3, duration=3),
    Place(id="P3", value=6,  cost=5, duration=1),
    Place(id="P4", value=12, cost=6, duration=3),
]
_TRAVEL_LEGS = [  # 5 拠点のほぼ完全グラフ。移動は一律 cost 1 / time 1
    TravelLeg(id=f"L{a}{b}", endpoints=(f"P{a}", f"P{b}"), travel_cost=1, travel_time=1)
    for a in range(5) for b in range(a + 1, 5)
]

def build_travel_problem(*, budget=25, time_budget=20, start="P0",
                         forbidden=None, required=None, preferences=None) -> OptimizationProblem: ...
def build_scaled_travel_problem(n_places, seed=0) -> OptimizationProblem: ...  # 規模別 analysis / property
def build_travel_solution(selected_place_ids, visit_order, *, total_value=0.0,
                          total_cost=0.0, total_time=0.0, status="valid") -> CandidateSolution: ...
```

- **完全グラフ + 一律 cost 1** にしたのは意図的 ── `budget=25` なら DP が全 place を選んでもplace 18 + 移動 5(閉路 5 本)= 23 ≤ 25 で **valid**。`budget=20` なら 23 > 20 で DP は**invalid**(移動を無視した選択だから)。この 2 つで「移動を数えるかどうか」の差を作る。
- `build_scaled_travel_problem` は place をランダム生成(RNG 呼び出し順を固定して決定論)。
  一直線 + seed で数本の近道。7-5 のオラクル比較と 7-6 の analysis が使う。

---

## 7. パイプラインの確認 ── ルート・サービスは無変更

`SolveService` / `VerifyService` / `BenchmarkService` は「registry を回すオーケストレーション」
なので、`POST /api/v1/solve` に `travel_planning` problem を投げるだけで通る。専用エンドポイント
なし。`alembic upgrade head` は no-op。

ただし `registry["travel_planning"]` は 7-5 まで空なので、**validate→select→solve→verify のフルパイプラインが緑になるのは 7-5**。この章の `test_travel_planning.py` はスキーマ / semantic /
構造検証まで。

---

## 8. まとめ

- 写経は葉 → ユニオン → semantic → structure → チェッカー → fixture → テストの順。
- `TravelData` / `TravelSolution` をユニオンに 1 項目ずつ足す。route / network / shift は無変更。
- leg は無向(`endpoints: tuple`)。Input Validation は `model_validator`、Semantic は問題全体の検査。
- **travel には Validation の計算ゲートが無い** ── 「回れるか」は solve の責務(`Phase-2-2.md` §3)。
- 移動費用の検算 `verification.py::_verify_travel_plan` は **7-4**(`travel_common.tour_cost` が要る)。
  この章の `verify_travel_structure` は純粋述語だけ(`total_cost` フィールドの範囲は見る、巡回積み直しはしない)。
- 既存の forbidden / required_inclusion / numeric_bound チェッカーが travel 解にも効く。
  解 → 要素 id 集合の抽出は 7-3 で `constraints/elements.py::solution_element_ids` に共通化
  (私設ヘルパの重複を解消。route の nodes/edges だけ `aspect` で分岐。#17)。
- `solutions/__init__.py` の `__all__` の `NetworkDesignSolution` 欠落もついでに補う。

## テスト観点(`textbook/samples/tests/unit/{test_travel_planning,test_constraint_checkers}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_travel_planning.py`**
> 
> - **対象**: `TravelData` / `TravelSolution` の判別可能ユニオン解決、`model_validator`、
>   `SEMANTIC_CHECKS["travel_planning"]`、`verify_travel_structure`、`structural_verify` の
>   travel ディスパッチ arm
> - **ドライバ**: このテスト関数。`build_travel_problem` / `build_travel_solution` が入力生成。
>   `problem.data` は `assert isinstance(..., TravelData)` で絞る
> - **スタブ**: **不要** ── スキーマは純粋な値オブジェクト、検査は純粋関数。
>   `ProblemValidationService` も DB / Redis を触らない
> - **`test_structural_verify_dispatches_travel` は arm 未接続で赤になる形にする**(Q44)──
>   予算超過の手組み解を `structural_verify` **経由**で踏ませ、`"budget"` を含む violation が
>   返ることをアサートする(`isinstance(violations, list)` だけでは `([], {})` でも緑になり
>   番人にならない)
> - フルパイプライン(validate→select→solve→verify)は **7-5**(`registry["travel_planning"]` が
>   空のうちは `select_strategy` が `NoAlgorithmError` ── #15)
> 
> **`test_constraint_checkers.py`**(現行版 = Phase 2 + travel 2 本 + `elements` 1 本)
> 
> - **対象**: `check_forbidden` / `check_required_inclusion` が travel 解の `selected_place_ids` を
>   見るか / `elements.solution_element_ids` の `aspect="nodes"` vs `"edges"`(route 解で分岐)と
>   対象外の解型 → `None`
> - **ドライバ**: このテスト関数。`build_travel_solution` + `Forbidden` / `RequiredInclusion` 制約、
>   `_route_solution()` / `build_shift_solution` を `solution_element_ids` に直接渡す
> - **スタブ**: **不要**(純粋関数)。Phase 2 の route / network 分の assertion は不変(#16)
> - **`elements.py` をこのテストが直接 import する**(#15 ── 3 ファイル触って 1 つしか import
>   しない穴を作らない。写経漏れ / route 分岐の写経ミスはこのテストがその場で赤にする)

| ケース                                             | 期待                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------- |
| `build_travel_problem()`                        | `problem_type == data.problem_type == "travel_planning"`              |
| top と data の problem_type 不一致                   | `model_validator` が `ValidationError`                                 |
| leg が未知 place を指す                               | `TravelData` の `model_validator` が `ValidationError`("unknown place") |
| `SEMANTIC_CHECKS["travel_planning"]`            | 3 チェック登録                                                              |
| 候補 place ゼロ                                     | `ProblemValidationError`                                              |
| 最安 place > budget / 最短 duration > time_budget   | `InfeasibleProblemError`                                              |
| 整合した手組みプラン                                      | `verify_travel_structure == []`                                       |
| 未知 place / 順序不一致 / 予算超過の手組みプラン                  | それぞれ violation                                                        |
| `structural_verify`(予算超過の travel 解を経由)   | `metrics == {}` / `"budget"` を含む violation(arm 未接続なら赤)             |
| forbidden / required チェッカー on travel 解          | それぞれ違反を検出                                                             |
| `solution_element_ids(route sol, aspect=…)`     | `"nodes"` は path_node_ids、`"edges"` は path_edge_ids / shift 解は `None` |

`uv run pytest tests/unit/test_travel_planning.py tests/unit/test_constraint_checkers.py` /
`uvx pyright app/domain app/services`。

---

次章([Phase-7-4](./Phase-7-4.md))では、作業単位 7-4 ── 訪問順 + travel_common + DP strategy。
`travel_common.py`(全関数)を新規作成し、Floyd-Warshall(7-1)を `all_pairs` / `order_and_cost` に
注入。`optimize_waypoint_order` の m > 8 分岐を最近傍法 + 2-opt の近似に差し替え(Phase 4 の宿題)、
`KnapsackDpTravelStrategy` を `knapsack.py` に追加、`verification.py` に `_verify_travel_plan`(検算)を足す。
