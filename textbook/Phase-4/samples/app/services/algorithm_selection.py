"""アルゴリズム選択(サービス層)。

`registry.find_strategy` は「候補の先頭」を返すだけの純粋関数。ここでは問題特性を見て
route_planning の中からどの実装を使うか決める **rule-based** の分岐を持つ
(README §6 / `Phase-0-4.md` §6「Rule Based ── Phase 4-5 / 5-3 で実装」)。学習型の選択は Phase 12。

責務分離: registry は検索だけ、例外送出(NoAlgorithmError)は services。
Phase 5-3 で `network_design → kruskal` の分岐を `_preferred_name` に足す。
"""

# [以降 Phase で修正予定 ── Phase 5-3 / 6-3] Phase 6-3 で `_preferred_name` に
# `isinstance(data, ShiftData) → "backtracking"` の 1 分岐を足す(README §9)。
# 現行版 textbook/Phase-6/samples/app/services/algorithm_selection.py。

from __future__ import annotations

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import find_strategy, get_strategies
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.route_planner import RouteData
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
