# Phase 8-4: 資源プロファイル + cpm / priority_list strategy(作業単位 8-4)

## この章のゴール

8-2 の CPM を `AlgorithmStrategy` に載せ、**資源制約つきスケジューリング(RCPSP)** の 2 つの手実装トラックを書く:

- **`cpm`** ── 資源を無視して各タスクを最早開始(ES)に置く。「資源が無限なら何日で終わるか」の**下界**。
  capacity がきついと資源超過 → Verification が `invalid`。
- **`priority_list`** ── 余裕(slack)の少ない順に、先行完了以降で資源上限を超えない最早時刻へ置く(serial schedule generation scheme)。**常に資源 feasible。ただし makespan は最適とは限らない**。

そのために「時刻ごとの資源使用量」= **資源プロファイル**が要る ── Phase 6 の
**Difference Array(imos 法)`range_add` を 1 バイトも変えずに再利用**(2 人目の消費者)。

> **RCPSP(resource-constrained project scheduling)** ── CPM に「同時に使える資源の上限」を足した問題。NP 困難。「どのタスクをいつ始めるか」の組合せ爆発は Phase 6 のシフト割当と同じ骨。
> **serial SGS** ── タスクを優先順位順に 1 本ずつ「置ける最早時刻」へ確定していく貪欲法。

**この章で作成 / 更新するファイル**:
`app/algorithms/scheduling/project_common.py`・`app/algorithms/scheduling/cpm.py`・
`app/algorithms/scheduling/priority_list.py`(新規)、
`tests/unit/test_project_common.py`・`tests/unit/test_cpm_strategy.py`(新規)。
**既存への変更**: `app/services/verification.py`(`_verify_project_resources` 追加、`# (Phase 8-4)`)。
`app/algorithms/patterns/difference_array.py` は **無変更で再利用**。

対応サンプル: `textbook/samples/app/algorithms/scheduling/{project_common,cpm,priority_list}.py`。
設計は README §12.4 / §19 Phase 8、`Phase-6-3.md`(2 トラックの骨)。

---

## 1. 共通足回り ── `project_common.py`

route の `segments.py` / network の `mst.py` / travel の `travel_common.py` と同型。4 strategy は「開始時刻の決め方」だけが違うので、パース・CPM 呼び出し・solution 組み立てをここに集約する(数値の drift 防止 ── Phase 6-1 の `shift_metrics` と同じ理由)。

```python
# app/algorithms/scheduling/project_common.py(要点。全文は samples)
def parse_project_problem(problem) -> ProjectData: ...          # 型チェック
def build_successors(data) -> dict[str, list[str]]:             # successors_from_edges(8-1)
def build_durations(data) -> dict[str, int]: ...

def resource_profile(schedule: list[ScheduledTask], demands) -> list[float]:
    """時刻 t ごとの資源使用量。各タスクの [start, finish) に demand を imos で区間加算。"""
    horizon = int(max(s.finish for s in schedule))
    updates = [(int(s.start), int(s.finish), float(demands.get(s.task_id, 0))) for s in schedule]
    return range_add(horizon, updates)                          # ← Phase 6 の imos、無変更

def peak_resource(profile) -> float: return max(profile, default=0.0)

def project_solution(data, starts, cpm_result, meta, *, ops) -> CandidateSolution:
    """実開始時刻(strategy が決める)+ CpmResult(slack / critical_path / order の供給元)を詰める。
    metrics = {"makespan", "peak_resource", ("_ops")}。status は "valid"(資源超過の hard 判定は Verification)。"""

def infeasible_project_solution(meta) -> CandidateSolution: ... # 閉路など解なし
```

- **`resource_profile` が imos の 2 人目の消費者**。naive に「毎タスク × 全時刻」を舐めるとO(タスク数 × 地平)、imos なら O(タスク数 + 地平)── `diff[start] += d / diff[finish] -= d` を記録して最後に 1 回の累積和。Phase 6 の `on_duty_by_hour`(時間帯別の在籍人数)と全く同じ形。
- **`ScheduledTask` の `slack` は CpmResult(資源無視)由来**。priority_list / cp_sat で開始時刻が後ろ倒しされても、`slack` は「資源が無ければどれだけ遅らせられるか」の構造的な余裕として残す。

---

## 2. `cpm` strategy ── 資源無視の下界

```python
# app/algorithms/scheduling/cpm.py(要点。全文は samples)
class CpmScheduleStrategy:
    meta = AlgorithmMeta(name="cpm", family="scheduling", implementation="handwritten",
                         time_complexity="O(V + E)", ...)

    def solve(self, problem):
        data = parse_project_problem(problem)
        try:
            result = cpm(build_durations(data), build_successors(data))   # ← 8-2
        except CyclicGraphError:
            return infeasible_project_solution(self.meta)   # 通常は validation が先に弾く
        starts = dict(result.earliest_start)                # ← 資源を見ない。全タスクを ES に
        return project_solution(data, starts, result, self.meta, ops=result.relaxations)
```

- `_ops` = CPM の緩和回数(前進 + 後退)。
- **capacity がきついと `resource_profile` の peak が capacity を超える** ── `cpm` はそれをそのまま`status="valid"` で返し、`SolutionVerificationService` が hard 違反で `invalid` にする(§4。Greedy strategy が埋まらないスロットをそのまま返すのと同じ ──「近似の制約違反はバグでなくinvalid な候補」。`Phase-0-6.md`)。

---

## 3. `priority_list` strategy ── 資源 feasible な貪欲 SGS

```python
# app/algorithms/scheduling/priority_list.py(要点。全文は samples)
class PriorityListScheduleStrategy:
    meta = AlgorithmMeta(name="priority_list", family="scheduling", implementation="handwritten", ...)

    def solve(self, problem):
        data = parse_project_problem(problem)
        dur = build_durations(data)
        result = cpm(dur, build_successors(data))   # slack / LS の供給元
        demand = {t.id: t.resource for t in data.tasks}
        cap = data.resource_capacity
        priority = sorted(result.order, key=lambda t: (result.latest_start[t], t))  # 余裕の少ない順

        starts, usage, ops = {}, {}, 0
        for t in priority:
            ready = max((starts[p] + dur[p] for p in result.predecessors[t]), default=0)
            start = ready
            if cap is not None and demand[t] > 0:
                while not all(usage.get(x, 0) + demand[t] <= cap
                              for x in range(start, start + dur[t])):
                    ops += 1; start += 1                    # demand を足せる最早時刻まで後ろ倒し
            starts[t] = start
            for x in range(start, start + dur[t]):
                usage[x] = usage.get(x, 0) + demand[t]
        return project_solution(data, starts, result, self.meta, ops=ops)
```

- **優先順位 = 最遅開始(LS)の昇順** = 余裕の少ないタスクから(min-slack first)。同点は id 昇順で決定論。
- **常に資源 feasible**(`while` で置ける時刻まで待つ)。**ただし最適ではない** ── fixture ではC(resource 3)を先に置いてしまい、D(resource 1)の置き場を C が塞ぎ、priority_list のmakespan は **10**(cpm の下界 8 / cp_sat の最適 9 より悪い)。
- `cap is None` なら `while` が空回りして cpm と同じ ES スケジュールになる。

---

## 4. Verification の資源検算 ── `_verify_project_resources`

```python
# app/services/verification.py(追加、# (Phase 8-4))
from app.algorithms.scheduling.project_common import peak_resource, resource_profile  # (Phase 8-4)
...
        structural = [
            *structural,
            *_verify_spanning_tree(problem, solution),
            *_verify_travel_plan(problem, solution),       # (Phase 7-4)
            *_verify_project_resources(problem, solution),  # (Phase 8-4)
        ]
...
def _verify_project_resources(problem, solution) -> list[ConstraintViolation]:
    """schedule の [start, finish) を imos で積み直し、peak > resource_capacity なら hard 違反。
    cpm は資源を無視して ES に詰めるのでここで invalid になる。priority_list / cp_sat は超えない。"""
    ...  # capacity is None なら空リスト
```

- `_verify_travel_plan`(Floyd-Warshall 検算)と同じ「計算はサービス層」の切り分け。
- **番人テスト**: `test_cpm_ignores_resources_and_verification_marks_it_invalid` ──`verify(problem_cap3, cpm.solve(problem_cap3))` が `status == "invalid"` かつ
  `constraint_kind == "project_resource"` の violation を含む。`_verify_project_resources` を`structural` の連結から外すと**このテストが赤**になる(overlay で逆確認済み)。

---

## 5. まとめ

- `project_common.py` = パース + CPM 呼び出し + `resource_profile`(imos)+ solution 組み立て。
  4 strategy が共有 ── 違うのは「開始時刻の決め方」だけ。
- `cpm` = ES に置く = 資源無視の下界。capacity 超過は Verification が invalid にする。
- `priority_list` = LS 昇順の貪欲 SGS = 常に feasible、ただし最適でないことがある。
- `_verify_project_resources` = imos で積み直し peak > capacity を hard(§4 の番人つき)。
- `patterns/difference_array.py` は **1 バイトも変えない**(2 人目の消費者)。

## テスト観点(`textbook/samples/tests/unit/{test_project_common,test_cpm_strategy}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_project_common.py`**
> 
> - **対象**: `parse_project_problem` / `build_successors` / `build_durations` /
>   `resource_profile`(imos)/ `peak_resource`(いずれも純粋)
> - **ドライバ**: このテスト関数。`build_project_problem` fixture + 手組みの `ScheduledTask`
> - **スタブ**: **不要** ── `range_add` は Phase 6 の imos プリミティブ(純粋)
> 
> **`test_cpm_strategy.py`**
> 
> - **対象**: `CpmScheduleStrategy.solve` / `PriorityListScheduleStrategy.solve` /
>   `_verify_project_resources`(`SolutionVerificationService` 経由)
> - **ドライバ**: このテスト関数。strategy を直接呼ぶ(registry / e2e は 8-6)
> - **スタブ**: **不要** ── strategy は純粋関数、verification は DB を持たない
> - **`test_cpm_ignores_resources_...` が資源検算 arm の番人**(§4)

| ケース                                       | 期待                                                                    |
| ----------------------------------------- | --------------------------------------------------------------------- |
| `resource_profile`([0,3)res2 + [0,2)res1) | `[3.0, 3.0, 2.0]` / `peak_resource == 3.0`                            |
| `cpm.solve`(capacity None)                | `status="valid"` / `makespan == 8` / `critical_path == ["A","C","E"]` |
| `verify(cap3, cpm.solve(cap3))`           | `status == "invalid"` / `project_resource` violation(番人)              |
| `verify(None, cpm.solve(None))`           | `status == "valid"`                                                   |
| `priority_list.solve`(cap3)               | `status="valid"` / 資源プロファイルの peak ≤ 3 / `makespan == 10`              |
| `priority_list` vs `cpm`(capacity None)   | 両方 `makespan == 8`                                                    |
| 決定論(cpm / priority_list、同入力)              | `model_dump()` 一致                                                     |

`uv run pytest tests/unit/test_project_common.py tests/unit/test_cpm_strategy.py` /
`uvx pyright app/algorithms/scheduling app/services`。

---

次章([Phase-8-5](./Phase-8-5.md))では、作業単位 8-5 ── OR-Tools CP-SAT で RCPSP を厳密に解く。
タスクごとの interval var、依存の `start[succ] >= end[pred]`、`add_cumulative` で資源上限、
`minimize(makespan)`。priority_list の貪欲が外した最適(fixture では 9)を CP-SAT が見つける
── Phase 6 の「手実装が破綻 → CP-SAT」を工程管理で再演。
