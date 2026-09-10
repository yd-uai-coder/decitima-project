# DeciTima samples │ Phase 7(7-2: type Item / knapsack_2d、7-4: KnapsackDpTravelStrategy)
"""Knapsack DP(0/1 ナップサック)── 純粋関数 `knapsack_2d` と、それを使う Travel Strategy。

README §19 Phase 7「Dynamic Programming を実問題へ適用する」の中核。

- **作業単位 7-2** ── `knapsack_2d`: 2 次元容量(予算 × 時間)の 0/1 ナップサックをボトムアップ
  DP で解く純粋関数。各アイテムは「使う / 使わない」の 2 択。返すのは選んだアイテムの添字リスト。
- **作業単位 7-4** ── `KnapsackDpTravelStrategy`: place の cost / duration をアイテムの 2 次元
  「重さ」に、好み加重の効用を「価値」にして DP。**移動コストは DP に入れない**(README
  「Floyd-Warshall は前処理」)── 選んでから `travel_common.order_and_cost` が巡回順と移動分を
  計上する。つまり DP の解は「移動を無視した上界」で、実際は移動分だけ予算・時間を食う。この差は
  Verification が hard 判定し、7-6 の analysis で Greedy と比較する。`travel_common` が生まれる
  7-4 で追加する(7-2 の写経では `knapsack_2d` とそのテストだけ)。

計算量: 時間・空間ともに O(n · A · B)(**擬多項式** ── A, B は容量の数値そのものに比例)。
容量が大きいと配列が膨れる ── DP の古典的な注意点として教材で明示する。
"""

from __future__ import annotations

import math  # (Phase 7-4)

from app.algorithms.optimization.travel_common import (  # (Phase 7-4)
    all_pairs,
    parse_travel_problem,
    place_utility,
    travel_solution,
)
from app.domain.problems.problem import OptimizationProblem  # (Phase 7-4)
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution  # (Phase 7-4)

# アイテム: (容量Aの消費, 容量Bの消費, 価値)。A/B は非負整数。
type Item = tuple[int, int, float]


def knapsack_2d(items: list[Item], cap_a: int, cap_b: int) -> list[int]:
    """容量 (cap_a, cap_b) の 0/1 ナップサック。価値最大の添字リストを返す。

    dp[a][b] = 容量 (a, b) までで得られる最大価値。1 アイテムずつ「使わない / 使う」で更新。
    """
    if cap_a < 0 or cap_b < 0:
        return []
    # dp と、その状態に至ったアイテム採否(復元用)
    dp = [[0.0] * (cap_b + 1) for _ in range(cap_a + 1)]
    take = [[[False] * len(items) for _ in range(cap_b + 1)] for _ in range(cap_a + 1)]

    for idx, (wa, wb, value) in enumerate(items):
        # a, b を降順に見る ── 同じアイテムを二重に取らない(0/1 の要)
        for a in range(cap_a, wa - 1, -1):
            for b in range(cap_b, wb - 1, -1):
                cand = dp[a - wa][b - wb] + value
                if cand > dp[a][b]:
                    dp[a][b] = cand
                    take[a][b] = list(take[a - wa][b - wb])
                    take[a][b][idx] = True

    chosen = take[cap_a][cap_b]
    return [i for i, t in enumerate(chosen) if t]


# (Phase 7-4) ここから下は travel_common(7-4)が揃ってから。7-2 では書かない。
class KnapsackDpTravelStrategy:
    """place の選択を 2 次元ナップサック DP で解く手実装ストラテジー。"""

    meta = AlgorithmMeta(
        name="knapsack_dp",
        family="optimization",
        implementation="handwritten",
        time_complexity="O(n * budget * time)",  # 擬多項式
        space_complexity="O(n * budget * time)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data, forbidden, required = parse_travel_problem(problem)
        cost_dist, time_dist = all_pairs(data)

        cap_a = math.floor(data.budget)
        cap_b = math.floor(data.time_budget)
        candidates = [p for p in data.places if p.id not in forbidden]

        items: list[Item] = []
        ids: list[str] = []
        for p in candidates:
            wa = math.ceil(p.cost)  # 消費は切り上げ(容量オーバーを避ける保守側)
            wb = math.ceil(p.duration)
            if wa > cap_a or wb > cap_b:
                continue  # 単体で予算/時間を超える place は DP に入れない
            items.append((wa, wb, place_utility(data, p.id)))
            ids.append(p.id)

        ops = len(items) * (cap_a + 1) * (cap_b + 1)  # DP セルの更新回数(オーダーの目安)
        picked_idx = set(knapsack_2d(items, cap_a, cap_b))
        selected = [ids[i] for i in range(len(ids)) if i in picked_idx]
        selected += [rid for rid in sorted(required) if rid not in selected]  # 必須は後付け
        return travel_solution(data, selected, cost_dist, time_dist, ops, self.meta)
