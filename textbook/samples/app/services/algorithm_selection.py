# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 4,5,6,7,8,9,11,15
"""アルゴリズム選択(サービス層)。

`registry.find_strategy` は「候補の先頭」を返すだけの純粋関数。ここでは問題特性を見て
どの実装を使うか決める **rule-based** の分岐を持つ(README §6 / `Phase-0-4.md` §6)。

責務分離: registry は検索だけ、例外送出(NoAlgorithmError)は services。

Phase 6-3 で shift 分岐、Phase 7-5 で travel 分岐(→ Knapsack DP)、
Phase 8-6 で project 分岐(資源制約あり → priority_list / なし → cpm)、
Phase 9-7 で logistics 分岐(既定 → knapsack_dp)を追加。
Phase 11-9 で travel 分岐に規模ガードを追加(budget×time_budget×places数 が大きいと
knapsack_dp の DP グリッドが肥大化しタイムアウト連鎖するため、greedy にフォールバック)。
Phase 15-2 で実測に基づきガード閾値を見直し(2,000,000→4,000,000)、logistics 分岐は
実測の結果ガード不要と判断した(詳細 `Phase-15-2.md`)。
"""

from __future__ import annotations

import math

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import find_strategy, get_strategies
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.project_manager import ProjectData  # (Phase 8-6)
from app.domain.problems.route_planner import RouteData
from app.domain.problems.shift_scheduler import ShiftData
from app.domain.problems.travel_planner import TravelData  # (Phase 11-9)
from app.services.errors import NoAlgorithmError

# (Phase 11-9)
# knapsack_dp は O(places数×floor(budget)×floor(time_budget)) の擬多項式。
# 実測(cap_a=15000,cap_b=16,n=5→0.74秒 / cap_a=100000,cap_b=16,n=5→5.23秒)から、
# /benchmark の runs=3 逐次実行でも SOLVE_TIMEOUT_SECONDS(10秒)に収まる規模に制限する
# (暫定閾値。Phase 15 の性能テストで見直す可能性あり)。
# _MAX_KNAPSACK_DP_CELLS = 2_000_000
# (Phase 15-2) 実測(cells=2,000,000 → 3run合計 約2.6秒/ cells=4,000,000 → 約5.8秒。
# いずれも SOLVE_TIMEOUT_SECONDS=10秒 に十分な余裕)の結果、閾値を緩和。
# Phase 11-9 の実インシデント(budget=100,000, n=5, time_budget=16 → cells=8,000,000)は
# 引き続き閾値を超え greedy にフォールバックするため、修正は安全(詳細 `Phase-15-2.md`)。
_MAX_KNAPSACK_DP_CELLS = 4_000_000


def _preferred_name(problem: OptimizationProblem) -> str | None:
    """問題特性から使いたい meta.name を決める。候補に無ければ呼び出し側が先頭にフォールバック。"""
    data = problem.data
    if isinstance(data, RouteData):
        # 負辺 → Bellman-Ford(Dijkstra / A* は settled 不変条件が壊れる)
        if data.allow_negative or any(e.weight < 0 for e in data.edges):
            return "bellman_ford"
        # 全ノードに座標がある → A*(ヒューリスティックが効く)
        if data.nodes and all(n.x is not None and n.y is not None for n in data.nodes):
            return "a_star"
        # 既定は手実装 Dijkstra(library:networkx は明示 request 時のみ)
        return "dijkstra"
    if problem.problem_type == "network_design":
        return "kruskal"
    if isinstance(data, ShiftData):
        # 既定は Backtracking(小規模で最適)。実規模は ?algorithm=cp_sat を明示 request
        return "backtracking"
    if problem.problem_type == "travel_planning":
        # (Phase 7-5)
        # return "knapsack_dp"
        # (Phase 11-9) budget/time_budget が大きく DP グリッドが肥大化する場合は
        # タイムアウト連鎖(裏スレッドは止まらない)を避けるため greedy にフォールバックする。
        # 厳密な確認は ?algorithm=knapsack_dp / brute_force を明示 request
        if isinstance(data, TravelData):
            cells = len(data.places) * math.floor(data.budget) * math.floor(data.time_budget)
            if cells > _MAX_KNAPSACK_DP_CELLS:
                return "greedy"
        return "knapsack_dp"
    if isinstance(data, ProjectData):  # (Phase 8-6)
        # 資源制約あり → priority_list(資源 feasible な貪欲)。厳密は ?algorithm=cp_sat
        # 資源制約なし → cpm(純粋なクリティカルパス。O(V+E))
        return "priority_list" if data.resource_capacity is not None else "cpm"
    if problem.problem_type == "logistics_planning":  # (Phase 9-7)
        # 既定は Knapsack DP(高速)。厳密確認は ?algorithm=brute_force、
        # 台数最小化は ?algorithm=pulp_milp を明示 request
        # (Phase 15-2) travel と同型のガードは付けない ── LogisticsDataPatch は depot_id しか
        # 公開せず capacity_weight/capacity_volume は LLM が触れない(常にベース問題のカタログ
        # 由来)。現実的な容量範囲(数十〜数百)では cells は travel のような桁に届かないことを
        # 実測済み(詳細 `Phase-15-2.md`)。
        return "knapsack_dp"
    return None


def select_strategy(
    problem: OptimizationProblem, requested: str | None = None
) -> AlgorithmStrategy:
    """problem に適用するアルゴリズムを1つ選ぶ。無ければ NoAlgorithmError。"""
    if requested is not None:
        strategy = find_strategy(problem, requested)
        if strategy is None:
            raise NoAlgorithmError(
                f"algorithm {requested!r} is not registered for {problem.problem_type!r}"
            )
        return strategy

    candidates = get_strategies(problem.problem_type)
    if not candidates:
        raise NoAlgorithmError(f"no algorithm registered for {problem.problem_type!r}")

    preferred = _preferred_name(problem)
    return next((s for s in candidates if s.meta.name == preferred), candidates[0])
