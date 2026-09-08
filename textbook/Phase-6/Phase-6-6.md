# Phase 6-6: 手実装の破綻 ── 計算量と実測(理論 + オラクル)(作業単位 6-6)

## この章のゴール

**コードを書かない理論章**(Phase 5-2 と同型)。2 つを確かめる:

1. **3 手実装は小規模で最適** ── 全割当を全列挙する正解オラクル `_brute_force_optimal` と、
   Backtracking / B&B のスコアが一致すること(Greedy はオラクル以上 = 最適を外しうること)。
2. **規模を上げると破綻する** ── Backtracking / B&B は最悪 O(kⁿ)。中規模で現実的な時間に
   収まらなくなる ── これが 6-7 で OR-Tools CP-SAT を用意する理由。

**この章で作成 / 更新するファイル**: `tests/unit/test_shift_breakdown.py`。実装ファイルは無い。

対応サンプル: `textbook/samples/tests/unit/test_shift_breakdown.py`。設計は `Phase-0-5.md` §2.3・§3.2、README §19。

---

## 1. 全割当の全列挙 ── 正解オラクル

```python
# tests/unit/test_shift_breakdown.py(要点。全文は samples)
def _brute_force_optimal(problem) -> float | None:
    """全割当を列挙し、hard 制約を満たすものの最良スコア。小規模専用、registry 非搭載。"""
    slots = sorted(data.slots, key=lambda s: s.id)
    choices = [
        list(combinations([st.id for st in eligible_staff(slot, data)], slot.required_headcount))
        for slot in slots
    ]
    best = None
    for combo in product(*choices):
        assignment = {slot.id: list(picks) for slot, picks in zip(slots, combo, strict=True)}
        if not respects_hard(data, assignment):     # 6-3 の common.respects_hard
            continue
        s, _ = score(problem, data, assignment)     # 6-1 の weighted_sum
        best = s if best is None else min(best, s)
    return best
```

- Phase 3 の `BruteForceRouteStrategy` / Phase 5-2 の `_all_spanning_trees` と同じ発想 ──
  **小規模で厳密解を出し、貪欲・枝刈りアルゴリズムの裏取りに使う**。
- `itertools.product` で「各スロットの combo」の直積を全部回す。組合せ爆発するので小規模専用の
  インラインヘルパ(registry には載せない ── shift の全探索は route と違いベンチ対象にもしない)。

---

## 2. 計算量(`Phase-0-5.md` §2.3)

| アルゴリズム | 時間 | 最適性 |
| --- | --- | --- |
| Greedy | O(n log n) 程度 | 保証なし。hard 制約を破ることも |
| Backtracking | 最悪 O(kⁿ)、枝刈りで大幅減 | 探索しきれば最適 |
| Branch and Bound | 最悪 O(kⁿ)、下界で枝刈り | 最適(打ち切らなければ) |
| OR-Tools CP-SAT | 実用上は多くの規模で現実的、理論は NP 困難 | 最適 or 実行不能を判定 |

`n` = スロット数、`k` = スロットあたりの combo 数(≒ `C(eligible, headcount)`)。枝刈りは指数を
多項式にはしない。

---

## 3. 破綻シナリオ(`Phase-0-5.md` §3.2)

| シナリオ | スタッフ | 日数 | スロット/日 | バックトラッキング | 判断 |
| --- | --- | --- | --- | --- | --- |
| 教材の小例 | 3 | 2 | 2 | 一瞬 | 手実装で十分 |
| 小規模店舗 | 8 | 7 | 3 | 枝刈り次第。秒〜十数秒 | 手実装の上限に近い |
| 中規模(README の例) | 20 | 7 | 3 | 現実的な時間で終わらない可能性大 | **CP-SAT 必須** |

`build_scaled_shift_problem(n_staff, n_days, seed)`(6-3 で追加)で規模を振り、seed を for ループで
回すプロパティテストで「小さいうちは Backtracking == オラクル」を確認する。中規模の 1 ケースは
「終わること(数秒以内)」だけを確認する(実際の破綻の実測は 6-7 の `analysis/shift_analysis.py`)。

---

## 4. まとめ

- `_brute_force_optimal` = 全割当の全列挙オラクル(小規模専用、registry 非搭載)。
- Backtracking / B&B は小規模でオラクルと一致(最適)、Greedy はオラクル以上(最適を外しうる)。
- 最悪 O(kⁿ)。中規模(20×7×3)で手実装は破綻 → 6-7 で CP-SAT。

## テスト観点(`textbook/samples/tests/unit/test_shift_breakdown.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: 3 手実装(Greedy / Backtracking / B&B)の最適性。`_brute_force_optimal` が正解オラクル
> - **ドライバ**: このテスト関数。`build_shift_problem` / `build_scaled_shift_problem` が入力生成
> - **スタブ**: **不要** ── すべて純粋。Kruskal / Prim と同じ「小規模で厳密解 → 裏取り」の型

| ケース | 期待 |
| --- | --- |
| `build_shift_problem` の Backtracking / B&B スコア | `== _brute_force_optimal(...)` |
| Greedy スコア | `>= _brute_force_optimal(...)`(最適を外しうる) |
| `build_scaled_shift_problem(4, 2, seed=0..4)` の Backtracking | `== _brute_force_optimal(...)`(小規模は最適) |
| `build_scaled_shift_problem(8, 3)` の Backtracking | `status in {"valid", "infeasible"}`(数秒以内に終わる) |

`uv run pytest tests/unit/test_shift_breakdown.py`。

---

次章([Phase-6-7](./Phase-6-7.md))では、作業単位 6-7 ── OR-Tools CP-SAT トラック。
手実装と同じ `AlgorithmStrategy` 契約・同じ `ShiftSolution` の裏で CP-SAT が探索する。
`analysis/shift_analysis.py` で「どの規模で切り替えるべきか」を実測し、registry を最終形にする。
