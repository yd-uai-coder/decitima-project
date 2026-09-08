# Phase 6-5: Branch and Bound ── 下界で枝刈り + 決定論的 anytime(作業単位 6-5)

## この章のゴール

`BranchAndBoundShiftStrategy` = **Backtracking + 下界(lower bound)**。部分割当の時点で「これ以上どう頑張っても `weighted_sum` はこの値未満にならない」楽観的な推定を計算し、現在の最良解 以上なら subtree を丸ごと切る(`Phase-0-5.md` §2.3)。

加えて **決定論的な anytime** ── `Phase-0-5.md` §5.1 が「Phase 6 で検討」としていた宿題の結論。

**この章で新規作成するファイル**: `app/algorithms/scheduling/branch_and_bound.py`、
`tests/unit/test_branch_and_bound_shift.py`。
**既存テンプレートへの追記**: `app/algorithms/registry.py`(B&B のコメントを外す)。

対応サンプル: 上記(registry は差分)。設計は `Phase-0-5.md` §2.3・§5.1。

---

## 1. 下界(lower bound)

`weighted_sum`(= 最小化するスカラー)の **admissible(真の最小を決して上回らない)** な下界:

```python
# app/algorithms/scheduling/branch_and_bound.py(要点)
def _lower_bound(problem, optimistic_labor: float) -> float:
    lb = 0.0
    for o in problem.objectives:
        if o.target == "labor_cost" and o.sense == "minimize":
            lb += o.weight * optimistic_labor        # final ≥ optimistic_labor
        elif o.sense == "maximize":                  # metric ≤ 1 → −w·metric ≥ −w
            lb -= o.weight
        # その他の minimize 目的(hour_variance 等、metric ≥ 0)→ 寄与 ≥ 0
    return lb
```

- `optimistic_labor` = `部分割当のコスト + 残りスロットを最安スタッフで埋めた場合のコスト`。
  残りぶんは **suffix sum**(`_suffix_cheapest[i]` = スロット i 以降の「最安で埋めたコスト」の和)でO(1) に。
- **admissible の証明**(weight ≥ 0 前提): labor 項 ≥ `w·optimistic_labor`(楽観 ≤ 実際)、
  maximize 項 ≥ `−w`(metric ≤ 1)、他の minimize 項 ≥ 0(metric ≥ 0)。合計 ≤ 真の最小 score。
- **枝刈り**: `_lower_bound(...) >= self.best_score` なら、この subtree に現最良を超える解は無い → return。

下界は「最大限タイト」でなくてよい ── 教材の狙いは「**下界があれば subtree を skip できる**」の実演。
テスト(6-5)で「B&B の `_ops` < Backtracking の `_ops`」= 枝刈りが効いていることを確認する。

---

## 2. 決定論的な anytime ── なぜ壁時計を使わないか

`Phase-0-5.md` §5.1:「B&B のように『その時点の最良解』を持つアルゴリズムは、タイムアウト時に『打ち切り』フラグを立てて返す選択肢を Phase 6 で検討」。

**壁時計(`time.perf_counter()`)を見るのは NG**:

- `solve` は純粋関数の契約 ── 時刻の読み取りは副作用(非決定的)。`test_deterministic_same_input_same_output`
  が赤くなる。
- そもそも `SolveService` は `solve` を別スレッドで `asyncio.wait_for` しており、タイムアウトしても**スレッドは止められない**(MVP の割り切り。`Phase-0-5.md` §5)。壁時計で途中解を返す仕組みは作れない。

代わりに **決定論的なノード予算**:

```python
_MAX_NODES = 200_000

def _recurse(self, i, assignments, partial_labor):
    if self.ops >= _MAX_NODES:
        self.truncated = True
        return
    ...
```

予算を超えたら探索を打ち切り、`shift_solution(search.best, ..., truncated=search.truncated)` が
`metrics["_truncated"] = 1.0`(`_` 接頭辞 = 診断指標)を立てて**その時点の最良解**を返す。
決定論なので純粋性は保たれる。壁時計 `SOLVE_TIMEOUT_SECONDS` は `SolveService` 側の安全網のまま(ノード予算でも終わらないほど 1 ノードが重い場合に 504)── **`services/solve.py` は変更しない**。

- `_ops` = ノード + 下界計算数。

---

## 3. registry の配線

```python
# app/algorithms/registry.py(B&B のコメントを外す)
from app.algorithms.scheduling.branch_and_bound import BranchAndBoundShiftStrategy

REGISTRY["shift_scheduling"] = [
    GreedyShiftStrategy(),
    BacktrackingShiftStrategy(),
    BranchAndBoundShiftStrategy(),        # ← 有効化
    # OrToolsCpSatShiftStrategy(),        # 6-7
]
```

`select_strategy` の既定は `"backtracking"` のまま(B&B は `?algorithm=branch_and_bound` 明示 or
Benchmark で走る)。

---

## 4. まとめ

- B&B = Backtracking + admissible な下界。`_lower_bound >= best_score` なら subtree を切る。
- 下界は `labor_cost` の楽観推定(suffix sum)+ maximize 目的の `−w`。weight ≥ 0 前提。
- **決定論的 anytime**: 壁時計でなくノード予算 `_MAX_NODES`。超過で最良解 + `metrics["_truncated"]`。
  純粋性を守るための割り切り。`solve.py` は変更しない。

## テスト観点(`samples/tests/unit/test_branch_and_bound_shift.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `BranchAndBoundShiftStrategy.solve`(純粋)
> - **ドライバ**: このテスト関数。`build_shift_problem` + `BacktrackingShiftStrategy` と比較
> - **スタブ**: **不要** ── solve は純粋(壁時計を見ないので決定論)

| ケース                | 期待                                           |
| ------------------ | -------------------------------------------- |
| 例題のスコア             | Backtracking の最適スコアと一致(下界で枝を切っても最適は不変)       |
| `_ops`             | B&B の `_ops` < Backtracking の `_ops`(枝刈りの効果) |
| verify 後           | `status="valid"` / `labor_cost == 20000`     |
| 小規模での `_truncated` | 付かない(ノード予算を使い切らない)                           |
| 同入力 → 同出力          | `model_dump()` が一致(決定論)                      |

`uv run pytest tests/unit/test_branch_and_bound_shift.py` / `uvx pyright app/algorithms/scheduling`。

---

次章([Phase-6-6](./Phase-6-6.md))では、作業単位 6-6 ── 手実装の破綻を実測する理論章
(実装ファイルなし。Phase 5-2 と同型)。全割当を全列挙する正解オラクルで 3 手実装の最適性を
裏取りし、規模を上げると Backtracking / B&B が現実的な時間に収まらなくなることを見る。
