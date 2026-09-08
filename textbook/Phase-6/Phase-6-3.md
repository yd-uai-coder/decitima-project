# Phase 6-3: Greedy ── 速いが hard 違反もある(作業単位 6-3)

## この章のゴール

最初のシフトソルバー = 貪欲法。**スロットを「入れられるスタッフが少ない順」= 厳しい順に見て、最も安い入れられるスタッフを取る**。速い(O(スロット数 × スタッフ数 log スタッフ数))が、最適は保証しない ── 埋まらないスロットが残ることも、目的値が最善でないこともある。

貪欲が hard 制約を破っても**例外は投げない**。`status="valid"` の候補を返し、hard 違反の判定はVerification に任せる(`Phase-0-6.md` ──「近似アルゴリズムの制約違反はバグでなく `invalid` な候補」)。

**この章で作成 / 更新するファイル**: `app/algorithms/scheduling/common.py`、
`app/algorithms/scheduling/greedy.py`、`tests/unit/test_greedy_shift.py`。
**既存ファイルへの変更**(現行版は samples): `app/services/algorithm_selection.py`
(`_preferred_name` に shift 分岐)、`tests/fixtures/optimization.py`
(`build_scaled_shift_problem` + `build_shift_problem(with_hour_variance=...)`)、
`tests/unit/test_algorithm_selection.py`(shift 選択のケース)。
**既存テンプレートへの追記**: `app/algorithms/registry.py`(`"shift_scheduling"` に Greedy を配線)。

写経順序: `common.py` → `greedy.py` → fixtures 現行版 → `algorithm_selection.py` 現行版
→ registry 追記 → テスト 2 本。

対応サンプル: 上記(registry は差分)。設計は `Phase-0-4.md` §5.3・§7.2。

---

## 1. `common.py` ── シフトソルバー共通の足回り

route の `segments.py` / network の `mst.py` と同じ「共通足回り」。4 strategy が使う:

```python
# app/algorithms/scheduling/common.py(要点。全文は samples)
from app.domain.solutions.shift_metrics import (   # 6-1 で新設。metrics 計算はそちらに集約
    assignment_metrics, distinct, hours_by_staff, working_days_by_staff,
)
from app.domain.solutions.shift_scheduler import Assignment, ShiftSolution
#   Assignment(= dict[str, list[str]])は shift_scheduler 定義。strategy は型を shift_scheduler
#   から、関数(eligible_staff / score / shift_solution ...)を common から import する

def parse_shift_problem(problem) -> ShiftData: ...              # 型チェック
def eligible_staff(slot, data) -> list[Staff]: ...             # available ∧ skills。時給昇順
def on_duty_by_hour(data, assignments) -> dict[str, list[float]] # imos 法(6-2 の range_add)
def respects_hard(data, assignments) -> bool                   # 完成割当の hard 制約チェック(探索の速い述語)
def score(problem, data, assignments) -> tuple[float, dict]    # (weighted_sum スカラー, metrics)
def shift_solution(assignments, *, data, ops, meta, truncated=False) -> CandidateSolution
```

- **metrics 計算は `domain/solutions/shift_metrics.py`(6-1 で新設)を import する** ── `assignment_metrics` /
  `hours_by_staff` / `working_days_by_staff` / `distinct`。検証器(`verify_shift_structure`)も同じ関数を
  呼ぶので、探索がスコアリングに使う値と検証で報告される値は **同じコードから出る**(注記でなく構造で保証。
  `Phase-2-4.md` §4)。`common.py` はもう metrics 式を持たない。
- `score` が `weighted_sum(problem.objectives, assignment_metrics(...))`(6-1)を呼ぶ ── これが多目的評価器の**初の消費者**。
- `shift_solution`: `assignments=None` → `status="infeasible"`。`ops=None`(ライブラリ)→ `_ops` なし。
  `truncated=True`(B&B の予算切れ)→ `metrics["_truncated"]=1.0`。
- **`status` は "valid" or "infeasible" だけ**。hard 違反 → `"invalid"` は Verification が確定する
  (`mst_solution` / `route_solution` と同じ約束)。

---

## 2. `GreedyShiftStrategy`

```python
# app/algorithms/scheduling/greedy.py(要点。全文は samples)
class GreedyShiftStrategy:
    meta = AlgorithmMeta(name="greedy", family="scheduling", implementation="handwritten", ...)

    def solve(self, problem):
        data = parse_shift_problem(problem)
        assignments, ops = {}, 0
        hours = {st.id: 0.0 for st in data.staff}      # 逐次追跡
        days = {st.id: set() for st in data.staff}      # 勤務日(序数集合)

        order = sorted(data.slots, key=lambda s: (len(eligible_staff(s, data)), s.id))  # 厳しい順
        for slot in order:
            picked = []
            for st in eligible_staff(slot, data):       # 時給昇順
                if len(picked) == slot.required_headcount: break
                ops += 1
                if hours[st.id] + length > data.max_weekly_hours: continue   # 週時間オーバー
                trial = days[st.id] | {day_ord}
                if run_length_at(trial, day_ord) > data.max_consecutive_days: continue  # 連続日数オーバー
                picked.append(st.id); hours[st.id] += length; days[st.id] = trial
            assignments[slot.id] = picked               # 埋まらなくてもそのまま
        return shift_solution(assignments, data=data, ops=ops, meta=self.meta)
```

- **`family="scheduling"`**(`app/algorithms/scheduling/` に対応)、`implementation="handwritten"`。
- スロットを **tightness 昇順**(eligible スタッフが少ない = 選択肢がないスロットを先に埋める)。
  同数なら id で決定的にタイブレーク(再現性)。
- 週勤務時間と連続勤務日数を**逐次**チェック(6-2 の `run_length_at`)。
- 埋まらないスロット → `assignments[slot.id] = []`(または不足分)。Verification が `check_staffing` /
  `shift_structure` で `invalid` にする。
- `_ops` = 割当を試みた回数(スロット × eligible スタッフ)。

---

## 3. registry と `select_strategy` の配線

```python
# app/algorithms/registry.py(追記)
from app.algorithms.scheduling.greedy import GreedyShiftStrategy
# from app.algorithms.scheduling.backtracking import BacktrackingShiftStrategy   # 作業単位 6-4 で有効化
# from app.algorithms.scheduling.branch_and_bound import BranchAndBoundShiftStrategy  # 6-5
# from app.algorithms.scheduling.ortools_cpsat import OrToolsCpSatShiftStrategy   # 6-7

REGISTRY = {
    "route_planning": [ ... ],
    "shift_scheduling": [
        GreedyShiftStrategy(),
        # BacktrackingShiftStrategy(),   # 6-4
        # BranchAndBoundShiftStrategy(), # 6-5
        # OrToolsCpSatShiftStrategy(),   # 6-7
    ],
    "network_design": [ ... ],
}
```

進行のルール #15: この章では Greedy だけ配線し、残りはコメントアウトのまま出荷する。

```python
# app/services/algorithm_selection.py(_preferred_name に 1 分岐。README §9)
if isinstance(data, ShiftData):
    return "backtracking"   # 既定は Backtracking(小規模で最適)。実規模は ?algorithm=cp_sat
```

- **6-3 の時点では `"backtracking"` はまだ登録されていない**ので、`_preferred_name` が返しても
  `select_strategy` は「候補の先頭」= Greedy にフォールバックする(`next(..., candidates[0])`)。
  6-4 で Backtracking を登録すると自動で既定が切り替わる。
- 共有 `textbook/samples/app/services/algorithm_selection.py` は冒頭コメントに `改訂 Phase 6` があり、
  shift 分岐の追加は `#(Phase 6-3)` タグで示される(#12)。

---

## 4. `build_scaled_shift_problem` fixture

```python
# tests/fixtures/optimization.py(追加)
def build_scaled_shift_problem(n_staff, n_days, *, slots_per_day=2, seed=0) -> OptimizationProblem:
    """規模を振れるシフト問題(手実装の破綻を実測する 6-6 用)。build_scaled_route_problem と同型。"""
```

- `build_scaled_route_problem` と同じく **seed 固定で RNG 呼び出し順を固定**し決定論に。
- スタッフは全スロット可用・スキルなし。スロットは 1 日 `slots_per_day` 本、各 headcount=1。
- あわせて `build_shift_problem(with_hour_variance=True)` を追加(第 3 目的つき。weight `100` は
  labor_cost と拮抗させる手調整値 ── 6-1 のスケール差の実演)。
- `Phase-2〜5 textbook/samples/tests/fixtures/optimization.py` に `[以降 Phase で修正予定 ── Phase 6-3]` マーカー。

---

## 5. まとめ

- `common.py` = 4 strategy 共通の足回り。`score` が `weighted_sum` を呼ぶ = 多目的評価器の初消費者。
- `GreedyShiftStrategy` = tightness 順 + 最安割当。速いが最適でない。hard 違反は例外でなく `invalid` 候補。
- registry は Greedy だけ配線(#15)。`select_strategy` の shift 既定は `"backtracking"`(6-4 で有効化)。
- `build_scaled_shift_problem` で規模を振れる(6-6 の破綻実測用)。

## テスト観点(`textbook/samples/tests/unit/{test_greedy_shift,test_algorithm_selection}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `GreedyShiftStrategy.solve`(純粋)+ `common.py` の `eligible_staff` / `respects_hard`
> - **ドライバ**: このテスト関数。`build_shift_problem` / `build_infeasible_shift_problem` が入力生成
> - **スタブ**: **不要** ── solve は純粋、`SolutionVerificationService` も DB / Redis を触らない

| ケース                                        | 期待                                                                 |
| ------------------------------------------ | ------------------------------------------------------------------ |
| 例題 `build_shift_problem`                   | 全 4 スロットが埋まり `status="valid"`、`_ops` あり                            |
| verify 後                                   | `status="valid"` / `day_off_satisfaction == 1.0` / `respects_hard` |
| 埋められない問題(`build_infeasible_shift_problem`) | strategy は `valid`、Verification が `invalid`                        |
| 同入力 → 同出力                                  | `model_dump()` が一致(純粋性)                                            |
| `eligible_staff(s1)` の順                    | 時給昇順(sato / ito / tanaka)                                          |
| `select_strategy(build_shift_problem())`   | `"backtracking"`(6-4 登録後)。6-3 単独では先頭にフォールバック                       |
| `select_strategy(..., requested="cp_sat")` | `"cp_sat"` / `library:ortools`(6-7 登録後)                            |

`uv run pytest tests/unit/test_greedy_shift.py tests/unit/test_algorithm_selection.py` /
`uvx pyright app/algorithms/scheduling app/services`。

---

次章([Phase-6-4](./Phase-6-4.md))では、作業単位 6-4 ── `BacktrackingShiftStrategy`。
スロットを順に全スタッフの組を試す DFS。週勤務時間・連続勤務日数で枝刈りし、全スロットが
埋まったら `weighted_sum` でスコアして最良を保持する。小規模なら最適。
