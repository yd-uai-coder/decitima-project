# Phase 6-4: Backtracking ── 小規模で最適(作業単位 6-4)

## この章のゴール

`BacktrackingShiftStrategy` ── **スロットを順に、入れられるスタッフの組を試す DFS**。全スロットが埋まったら `weighted_sum` でスコアし、最良の割当を保持する。探索しきれば最適(`Phase-0-5.md` §2.3)。

`Phase-0-4.md` §7.2 のスケッチが下敷き ── 「スロットを順に見て割当可能なスタッフを試す(再帰)/制約を枝刈りに使う / 全スロット埋まったら objectives の重み付き和でスコア計算 / 最良を ShiftSolution に」。

**この章で新規作成するファイル**: `app/algorithms/scheduling/backtracking.py`、
`tests/unit/test_backtracking_shift.py`。
**既存テンプレートへの追記**: `app/algorithms/registry.py`(`"shift_scheduling"` の
`BacktrackingShiftStrategy()` 行と import のコメントを外す)。

対応サンプル: 上記(registry は差分)。設計は `Phase-0-4.md` §7.2、`Phase-0-5.md` §2.3。

---

## 1. `BacktrackingShiftStrategy`

```python
# app/algorithms/scheduling/backtracking.py(要点。全文は samples)
class BacktrackingShiftStrategy:
    meta = AlgorithmMeta(
        name="backtracking", family="scheduling", implementation="handwritten",
        time_complexity="最悪 O(kⁿ)、枝刈りで大幅減", space_complexity="O(スロット数)",
    )

    def solve(self, problem):
        data = parse_shift_problem(problem)
        search = _Search(problem, data)
        search.run()
        return shift_solution(search.best, data=data, ops=search.ops, meta=self.meta)
```

再帰の状態(週勤務時間・勤務日カウンタ)を持ち回るため `_Search` ヘルパを 1 回だけ生成する:

```python
class _Search:
    def _recurse(self, i, assignments):
        if i == len(self._slots):                       # 全スロット埋まった
            s, _ = score(self._problem, self._data, assignments)   # weighted_sum(6-1)
            if s < self.best_score:
                self.best_score = s
                self.best = {k: list(v) for k, v in assignments.items()}
            return
        slot = self._slots[i]
        for combo in combinations(self._eligible[slot.id], slot.required_headcount):
            self.ops += 1
            if not self._can_take(combo, length, day_ord):   # 週時間 or 連続日数で枝刈り
                continue
            self._apply(combo, length, day_ord, +1)          # 状態を進める
            assignments[slot.id] = [st.id for st in combo]
            self._recurse(i + 1, assignments)
            del assignments[slot.id]
            self._apply(combo, length, day_ord, -1)          # ロールバック
```

- **`itertools.combinations`** で「required_headcount 人の組」を列挙(headcount > 1 に対応)。
- **枝刈り** `_can_take`: 各スタッフについて `hours + length > max_weekly_hours` なら不可、
  `run_length_at(present | {day_ord}, day_ord) > max_consecutive_days` なら不可(6-2 の逐次判定)。
- **`_apply` / undo** ── 勤務日は `dict[int, int]`(序数 → カウント)で持ち、同じ日に別スロットで入っても正しくロールバックできるようにする(set だと二重登録で壊れる)。
- `_ops` = 展開したノード数(スロット × 試した組)。

### 小規模で最適になる理由

全 combo を試し、枝刈りは「hard 制約を破る枝」だけを切る。だから feasible な割当を漏らさず、その中で `weighted_sum` 最小のものを返す ── 探索しきれば最適(6-6 で全列挙オラクルと照合)。

### なぜ大規模で破綻するか

combo の総数はスロットごとに `C(eligible, headcount)`、それの積。枝刈りは指数を多項式にはしない。
スタッフ 20 × 7 日 × 3 スロットで現実的な時間に終わらない(`Phase-0-5.md` §3.2)── これが 6-7 でOR-Tools CP-SAT を用意する理由。6-6 で実測する。

---

## 2. registry の配線

```python
# app/algorithms/registry.py(6-3 のコメントを 1 行外す)
from app.algorithms.scheduling.backtracking import BacktrackingShiftStrategy   # ← 有効化

REGISTRY["shift_scheduling"] = [
    GreedyShiftStrategy(),
    BacktrackingShiftStrategy(),          # ← 有効化
    # BranchAndBoundShiftStrategy(),      # 6-5
    # OrToolsCpSatShiftStrategy(),        # 6-7
]
```

これで `select_strategy(build_shift_problem())` が `_preferred_name` の `"backtracking"` を候補から引けるようになり、shift の既定が Greedy → Backtracking に切り替わる。

---

## 3. まとめ

- スロット順の DFS。`combinations` で headcount 人の組を列挙、週時間 + 連続日数で枝刈り。
- 葉で `weighted_sum` スコア、最良を保持 ── 探索しきれば最適。
- 勤務日カウンタは `dict[int, int]` でロールバック可能に。
- 最悪 O(kⁿ)。registry に Backtracking を配線すると shift の既定になる。

## テスト観点(`samples/tests/unit/test_backtracking_shift.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `BacktrackingShiftStrategy.solve`(純粋)
> - **ドライバ**: このテスト関数。`build_shift_problem` が入力生成、`common.score` で別解と比較
> - **スタブ**: **不要** ── solve は純粋

| ケース                      | 期待                                                                                     |
| ------------------------ | -------------------------------------------------------------------------------------- |
| 例題 `build_shift_problem` | `status="valid"`、verify 後も valid、`labor_cost == 20000` / `day_off_satisfaction == 1.0` |
| 手組みの別解と比較                | Backtracking の解のスコア `<=` 別解のスコア                                                        |
| 同入力 → 同出力                | `model_dump()` が一致                                                                     |
| `_ops`                   | `> 0`(展開ノード数)                                                                          |

`uv run pytest tests/unit/test_backtracking_shift.py` / `uvx pyright app/algorithms/scheduling`。

---

次章([Phase-6-5](./Phase-6-5.md))では、作業単位 6-5 ── `BranchAndBoundShiftStrategy`。
Backtracking に**可容な下界**を足し、「これ以上どう頑張っても現最良を超えられない」枝を丸ごと切る。
さらに壁時計を使わない**決定論的な anytime**(ノード予算超過で最良解 + `_truncated`)。
