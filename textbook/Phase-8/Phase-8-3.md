# Phase 8-3: project_scheduling problem_type の配線(作業単位 8-3)

## この章のゴール

「タスクの依存から工程を最短化する」(README §12.4)は route の単一経路でも network の全域木でもtravel の部分集合でも表せない ── 新しい `problem_type` `project_scheduling` が要る。
**Phase 5-3(network)/ 7-3(travel)で新 problem_type を足した手順がそのまま雛形**。判別可能
ユニオンにメンバーを 1 つずつ足すだけで、route / network / shift / travel のコードには一切触れず、**新しい DB テーブルも作らない**(hybrid JSONB。`alembic upgrade head` は no-op)。

**travel との共通点が 1 つ**: project にも「計算ゲート」が要る ── ただし travel と違って
**「解けるか」の計算ゲートが存在する**。依存グラフに閉路があると実行順が定義できない
(`InfeasibleProblemError`)。これは route の到達可能性 / network の連結性と同じ「BFS/DFS を走らせる計算」なので、`domain/problems/semantic.py`(純粋述語)ではなく `services/validation.py` が`topological.has_cycle`(8-1)で判定する ──「これは計算か? 述語か?」(`Phase-2-2.md` §3)の **4 例目**。

触るファイルは多いが依存は一方向。**下の順に写経する**:

1. `domain/problems/project_manager.py` / `domain/solutions/project_manager.py` ── 葉。
   以降のほぼ全ファイルがこれを import する(§1)
2. `domain/problems/problem.py` / `domain/solutions/solution.py` / それぞれの `__init__.py`
   ── 判別可能ユニオンに 1 メンバー、re-export(§2)
3. `domain/problems/semantic.py`(§3)/ `domain/solutions/structure.py`(§4)── domain の純粋述語
4. `services/validation.py` ── 閉路ゲート(§5)
5. `tests/fixtures/optimization.py`(project fixture、§6)→ `tests/unit/test_project_scheduling.py`

> **`verification.py` の資源プロファイル検算(`_verify_project_resources`)はこの章では書かない。**
> `resource_profile` / `peak_resource` は `project_common`(8-4)にあり、8-3 で
> `from app.algorithms.scheduling.project_common import ...` を足すと `project_common` がまだ無く
> **collection が `ImportError` で全崩れ**する(`verification.py` は `solve.py` / `benchmark.py` /
> 多数のテストが import)。8-4 で `project_common` と一緒に足す(進行のルール #15。前例 Q34 / Q41 / Q42)。

**この章で作成 / 更新するファイル**: `app/domain/problems/project_manager.py`、
`app/domain/solutions/project_manager.py`(新規)、`tests/unit/test_project_scheduling.py`。
**既存への変更**(現行版は samples): `app/domain/problems/{problem,__init__,semantic}.py`、
`app/domain/solutions/{solution,__init__,structure}.py`、`app/services/validation.py`、
`tests/fixtures/optimization.py`(project fixture ── `build_project_problem` /
`build_cyclic_project_problem` / `build_scaled_project_problem` / `build_project_solution`)。
`app/services/verification.py` の資源検算は **8-4**。

設計は `Phase-0-2.md` §8.1、`Phase-5-3.md` / `Phase-7-3.md`(同型の配線)、`Phase-2-2.md` §3。

---

## 1. 葉モジュール ── `ProjectData` / `ProjectSolution`

```python
# app/domain/problems/project_manager.py(全文は samples)
class ProjectTask(BaseModel):
    id: str
    name: str | None = None
    duration: int = Field(gt=0)            # 整数時間単位。imos の資源グリッドが綺麗に回る
    resource: int = Field(ge=0, default=0) # 実行中ずっと占有する資源量(消費は 8-4)

class TaskDependency(BaseModel):
    id: str
    predecessor: str
    successor: str                         # predecessor が終わってから successor(finish-to-start)

class ProjectData(BaseModel):
    problem_type: Literal["project_scheduling"] = "project_scheduling"
    tasks: list[ProjectTask]
    dependencies: list[TaskDependency] = Field(default_factory=list)
    resource_capacity: int | None = None   # None なら資源制約なし(純粋 CPM)

    @model_validator(mode="after")
    def _refs_and_ids(self) -> ProjectData:
        # 依存の端点が実在タスクか / task id・dependency id が一意か / predecessor != successor
        # 閉路は「走査」なので見ない ── validation.py が has_cycle で判定(Phase-2-2.md §3)

# app/domain/solutions/project_manager.py
class ScheduledTask(BaseModel):
    task_id: str
    start: float     # 実際の開始時刻(cpm では ES、priority_list / cp_sat では後ろ倒しも)
    finish: float    # start + duration
    slack: float     # 総余裕(LS − ES)。スケジュールの後ろ倒しとは独立

class ProjectSolution(BaseModel):
    problem_type: Literal["project_scheduling"] = "project_scheduling"
    task_order: list[str]
    schedule: list[ScheduledTask]
    critical_path: list[str]
    makespan: float
```

- **`duration: int`** ── 整数に限定する。8-4 で各タスクの `[start, finish)` を Difference Array(imos)で区間加算するとき、境界が整数だとグリッドが綺麗になる(小数版は Phase 7 knapsack のceil/floor と同じ「落とし穴」。README「完了予定日」も日単位)。非スコープ(introduction §7)。
- **依存はエッジリスト**(`TaskDependency(id, predecessor, successor)`)── `RouteEdge` / `NetworkLink` と同じく id が付くので、将来 forbidden / numeric_bound などの制約対象にもできる。今は使わない。
- **`resource` / `resource_capacity` は 8-3 では定義 + 基本の実行可能性検査(§3)まで**。
  スケジューリングでの消費は 8-4。
- 葉なので兄弟(`route_planner.py` 等)を import しない。

---

## 2. ユニオンへの追加

```python
# app/domain/problems/problem.py
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData | TravelData | ProjectData,   # (Phase 8-3)
    Field(discriminator="problem_type"),
]
class OptimizationProblem(BaseModel):
    problem_type: Literal[
        "route_planning", "shift_scheduling", "network_design", "travel_planning",
        "project_scheduling",  # (Phase 8-3)
    ]

# app/domain/solutions/solution.py
type SolutionData = Annotated[
    RouteSolution | ShiftSolution | NetworkDesignSolution | TravelSolution
    | ProjectSolution,   # (Phase 8-3)
    Field(discriminator="problem_type"),
]
```

`domain/problems/__init__.py` に `ProjectTask` / `TaskDependency` / `ProjectData` を、
`domain/solutions/__init__.py` に `ProjectSolution` / `ScheduledTask` を re-export + `__all__`。

---

## 3. Semantic Validation ── 純粋述語だけ

```python
# app/domain/problems/semantic.py(追加。全文は samples)
def check_project_has_tasks(problem) -> list[SemanticIssue]:
    """タスクが空 ── スケジュールする対象が無い(整合欠陥 → ProblemValidationError)。"""

def check_project_resource_capacity(problem) -> list[SemanticIssue]:
    """resource_capacity を 1 タスクの需要が超えるなら、そのタスクは永遠に実行できない
    (infeasible=True)。shift の weekly-hours-cover / travel の budget-feasible と同型。"""

SEMANTIC_CHECKS["project_scheduling"] = [
    check_project_has_tasks, check_project_resource_capacity,
]
```

- 依存の端点実在チェックは `ProjectData.model_validator` が既にやる(travel が leg 端点を`model_validator` でやるのと同じ ── network だけ semantic 側でやる歴史的経緯)。だから semantic は「問題全体を見ないと分からない」2 つに絞る。
- **`infeasible` の差が例外を分ける** ── タスクゼロは「直せる不整合」(`ProblemValidationError`)、「resource 3 のタスクに capacity 1」は「原理的に解なし」(`InfeasibleProblemError`)。

---

## 4. 構造検証 ── 純粋述語は domain

```python
# app/domain/solutions/structure.py(追加)
#   structural_verify に 5 本目の isinstance arm  # (Phase 8-3)
def verify_project_structure(data: ProjectData, sol: ProjectSolution) -> list[ConstraintViolation]:
    """スケジュールの「形」を検証(純粋述語のみ)。すべて hard:
      - task_order が全タスクの順列 / schedule が全タスクをちょうど 1 度ずつ
      - 各タスク finish == start + duration
      - 依存を守る: 各 dep で successor.start >= predecessor.finish(finish-to-start)
      - critical_path のタスクは slack ≈ 0
      - makespan == max(finish)
    """
```

- **資源プロファイルの再計算(imos)はここでやらない** ── それは Difference Array を走らせる「計算」で、`domain` は `algorithms` を import できない(`Phase-0-3.md` §2.2)。
  `SolutionVerificationService` が **8-4** の `_verify_project_resources`(`project_common.resource_profile` を使う)で行う。network の `verify_network_structure`(辺数を数える)vs `forms_spanning_tree`(BFS)、travel の `verify_travel_structure`(宣言値の範囲)vs `_verify_travel_plan`(Floyd-Warshall 検算)と同じ切り分け。
- **`test_structural_verify_dispatches_project` は arm 未接続で赤になる形にする**(Q44)──`finish != start + duration` の手組み解を `structural_verify` **経由**で踏ませ、`constraint_kind == "project_structure"` の violation が返ることをアサートする(`isinstance(violations, list)` だけでは `([], {})` でも緑になり番人にならない)。

---

## 5. 閉路ゲート ── `services/validation.py`

```python
# app/services/validation.py(追加。全文は samples)
from app.algorithms.graph.topological import has_cycle, successors_from_edges   # (Phase 8-3)
from app.domain.problems.project_manager import ProjectData                     # (Phase 8-3)
...
        elif isinstance(problem.data, ProjectData):   # network の all_nodes_connected 分岐と同型
            successors = successors_from_edges(
                (t.id for t in problem.data.tasks),
                ((d.predecessor, d.successor) for d in problem.data.dependencies),
            )
            if has_cycle(successors):
                infeasible.append("dependency graph has a cycle: no topological order exists")
```

- `model_validator` は閉路を弾かない(走査だから)。`ProjectData(tasks=[A,B], dependencies=[A→B, B→A])` は
  構築できてしまう ── だから `validation.py` が `has_cycle` で弾く。テスト
  `test_dependency_cycle_is_infeasible` は `build_cyclic_project_problem()`(A→B→C→A)で
  `InfeasibleProblemError`(match `"cycle"`)を確認する。
- **`SolveService` / `VerifyService` / `BenchmarkService` は無変更** ── registry を回すだけ。
  ただし `registry["project_scheduling"]` は 8-6 まで空なので、フルパイプラインが緑になるのは 8-6。
  この章の `test_project_scheduling.py` はスキーマ / semantic / 構造検証 / 閉路ゲートまで。

---

## 6. project fixture(`tests/fixtures/optimization.py` に追加)

```python
# tests/fixtures/optimization.py(要点。全文は samples)
_PROJECT_TASKS = [
    ProjectTask(id="A", name="設計",     duration=3, resource=2),
    ProjectTask(id="B", name="調達",     duration=2, resource=1),
    ProjectTask(id="C", name="実装",     duration=4, resource=3),   # capacity 3 を 1 人で使い切る
    ProjectTask(id="D", name="検証",     duration=2, resource=1),
    ProjectTask(id="E", name="リリース", duration=1, resource=2),
]
_PROJECT_DEPS = [A→C, B→D, C→E, D→E]   # クリティカルパス A→C→E、makespan 8、B/D は slack 3

def build_project_problem(*, resource_capacity=3, max_makespan=None, forbidden=None): ...
def build_cyclic_project_problem(): ...       # A→B→C→A(validation の infeasible 用)
def build_scaled_project_problem(n_tasks, *, seed=0, resource_capacity=None): ...  # ランダム DAG(i<j の辺のみ)
def build_project_solution(schedule: list[(task_id, start, finish, slack)], *, critical_path, makespan, ...): ...
```

- **fixture の設計は 8-4 / 8-5 の教材の核に合わせてある**: `resource_capacity=3` で
  cpm(資源無視)は C と D が t3〜4 で重なり peak 4 > 3 → Verification が invalid /
  priority_list は D を後ろに回して makespan 10(最適でない)/ cp_sat は 9(最適)。
- `build_scaled_project_problem` は `build_scaled_route_problem` と同型 ── seed 固定で RNG 呼び出し順を
  固定し決定論。依存は `i < j` の向きにだけ張るので必ず非巡回。8-6 のオラクル比較・プロパティテストが使う。

---

## 7. まとめ

- 写経は葉 → ユニオン → semantic → structure → validation → fixture → テストの順。
- `ProjectData` / `ProjectSolution` をユニオンに 1 項目ずつ。route / network / shift / travel は無変更。
- 依存はエッジリスト。Input Validation は `model_validator`(端点実在・id 一意・自己依存禁止)、**閉路は `validation.py` が `has_cycle` で**(計算 / 述語の 4 例目)。
- 資源プロファイルの検算 `verification.py::_verify_project_resources` は **8-4**
  (`project_common.resource_profile` が要る)。この章の `verify_project_structure` は純粋述語だけ。
- `constraints/elements.py` は変更不要(project 解は全タスク実施 ── forbidden / required_inclusion は非該当。未知の解型 → `None` → チェッカー素通し)。`numeric_bound` は `metrics["makespan"]` を読むので
  無変更で効く(8-6 の `test_end_to_end_invalid_when_makespan_bound_violated`)。

## テスト観点(`textbook/samples/tests/unit/test_project_scheduling.py`)

> **テスト対象 / ドライバ / スタブ**
> 
> - **対象**: `ProjectData` / `ProjectSolution` の判別可能ユニオン解決、`ProjectData.model_validator`、
>   `SEMANTIC_CHECKS["project_scheduling"]`、`verify_project_structure`、`structural_verify` の
>   project ディスパッチ arm、`ProblemValidationService.validate`(閉路 → `InfeasibleProblemError`)
> - **ドライバ**: このテスト関数。`build_project_problem` / `build_cyclic_project_problem` /
>   `build_project_solution` が入力生成。`problem.data` は `assert isinstance(..., ProjectData)` で絞る
> - **スタブ**: **不要** ── スキーマは純粋な値オブジェクト、検査は純粋関数。
>   `ProblemValidationService` も DB / Redis を触らない
> - **`test_structural_verify_dispatches_project` は arm 未接続で赤になる形にする**(Q44、§4 参照)
> - フルパイプライン(validate→select→solve→verify)は **8-6**(`registry["project_scheduling"]` が
>   空のうちは `select_strategy` が `NoAlgorithmError` ── #15)

| ケース                                     | 期待                                                                    |
| --------------------------------------- | --------------------------------------------------------------------- |
| `build_project_problem()`               | `problem_type == data.problem_type == "project_scheduling"`           |
| top と data の problem_type 不一致           | `model_validator` が `ValidationError`                                 |
| 未知タスクを指す依存 / 重複 id / 自己依存 / duration 0  | `ProjectData` / `ProjectTask` の `model_validator` が `ValidationError` |
| `SEMANTIC_CHECKS["project_scheduling"]` | 2 チェック登録                                                              |
| タスクゼロ                                   | `ProblemValidationError`                                              |
| resource 3 のタスクに capacity 1             | `InfeasibleProblemError`                                              |
| 依存が閉路(A→B→C→A)                          | `InfeasibleProblemError`(match `"cycle"`)                             |
| 整合した手組みスケジュール                           | `verify_project_structure == []`                                      |
| finish 不整合 / 依存違反 / 非順列 / クリティカルに slack | それぞれ violation                                                        |
| `structural_verify`(finish 不整合の解を経由)    | `metrics == {}` / `project_structure` violation(arm 未接続なら赤)           |

`uv run pytest tests/unit/test_project_scheduling.py` / `uvx pyright app/domain app/services`。

---

次章([Phase-8-4](./Phase-8-4.md))では、作業単位 8-4 ── 資源プロファイル(Difference Array の
2 人目の消費者)と、手実装 strategy 2 本。`project_common.py`(共通足回り)を新規作成し、
`cpm`(資源無視 = 下界)と `priority_list`(資源 feasible な貪欲 SGS)を実装、`verification.py` に
`_verify_project_resources`(imos で積み直し)を足す。
