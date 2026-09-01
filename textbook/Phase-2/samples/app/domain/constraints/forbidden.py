"""forbidden 制約のチェッカー ── 解に「使ってはいけない要素」が含まれていないか。

Phase 1 は services/verification.py にインラインだったものを Phase 2 で domain へ移設。
route 解の path_edge_ids(禁止エッジ)に対して働く。設計は Phase-0-6.md §3.1。
"""

from __future__ import annotations

from app.domain.problems.problem import ForbiddenConstraint, OptimizationProblem
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation


def check_forbidden(
    constraint: ForbiddenConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が禁止要素(禁止エッジ id 等)を含んでいれば違反を1件返す。"""
    # forbidden は現状 route 解にのみ適用。それ以外の解型では素通し(Phase 1 の assert から変更)
    if not isinstance(solution.assignments, RouteSolution):
        return None
    hit = set(solution.assignments.path_edge_ids) & set(constraint.items)
    if not hit:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"path uses forbidden edge(s): {sorted(hit)}",
        detail={"forbidden_hit": sorted(hit)},
    )
