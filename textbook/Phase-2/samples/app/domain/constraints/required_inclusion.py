"""required_inclusion 制約のチェッカー ── 解が「必ず含めるべき要素」をすべて含むか。

Phase 1 は services/verification.py にインラインだったものを Phase 2 で domain へ移設。
route 解の path_node_ids(必須経由ノード)に対して働く。設計は Phase-0-6.md §3.1。
"""

from __future__ import annotations

from app.domain.problems.problem import OptimizationProblem, RequiredInclusionConstraint
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation


def check_required_inclusion(
    constraint: RequiredInclusionConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が必須要素(必須経由ノード id 等)を取りこぼしていれば違反を1件返す。"""
    if not isinstance(solution.assignments, RouteSolution):
        return None
    missing = set(constraint.items) - set(solution.assignments.path_node_ids)
    if not missing:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"path misses required node(s): {sorted(missing)}",
        detail={"missing": sorted(missing)},
    )
