# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 4,5,6,7,8
"""アルゴリズム選択(サービス層)。

`registry.find_strategy` は「候補の先頭」を返すだけの純粋関数。ここでは問題特性を見て
どの実装を使うか決める **rule-based** の分岐を持つ(README §6 / `Phase-0-4.md` §6)。

責務分離: registry は検索だけ、例外送出(NoAlgorithmError)は services。

Phase 6-3 で shift 分岐、Phase 7-5 で travel 分岐(→ Knapsack DP)、
Phase 8-6 で project 分岐(資源制約あり → priority_list / なし → cpm)を追加。
"""

from __future__ import annotations

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import find_strategy, get_strategies
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.project_manager import ProjectData  # (Phase 8-6)
from app.domain.problems.route_planner import RouteData
from app.domain.problems.shift_scheduler import ShiftData
from app.services.errors import NoAlgorithmError


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
    if problem.problem_type == "travel_planning":  # (Phase 7-5)
        # 既定は Knapsack DP。小規模の厳密確認は ?algorithm=brute_force
        return "knapsack_dp"
    if isinstance(data, ProjectData):  # (Phase 8-6)
        # 資源制約あり → priority_list(資源 feasible な貪欲)。厳密は ?algorithm=cp_sat
        # 資源制約なし → cpm(純粋なクリティカルパス。O(V+E))
        return "priority_list" if data.resource_capacity is not None else "cpm"
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
