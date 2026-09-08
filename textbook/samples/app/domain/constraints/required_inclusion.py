# DeciTima samples │ 初出 Phase 2 │ 改訂 Phase 5
"""required_inclusion 制約のチェッカー ── 解が「必ず含めるべき要素」をすべて含むか。

Phase 5-3 で network_design 解にも対応。意味は解型で変わる:
  - route 解   … 必須「経由ノード」id(path_node_ids に含まれるか)
  - network 解 … 必須「リンク」id(selected_link_ids に含まれるか)
"""

from __future__ import annotations

from app.domain.problems.problem import OptimizationProblem, RequiredInclusionConstraint
from app.domain.solutions.network_design import NetworkDesignSolution
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation


def _present_element_ids(solution: CandidateSolution) -> set[str] | None:
    """解に「含まれている要素」の id 集合。対象にできない解型は None。"""
    assignments = solution.assignments
    if isinstance(assignments, RouteSolution):
        return set(assignments.path_node_ids)
    if isinstance(assignments, NetworkDesignSolution):
        return set(assignments.selected_link_ids)
    return None


def check_required_inclusion(
    constraint: RequiredInclusionConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が必須要素(必須経由ノード / 必須リンク id 等)を取りこぼしていれば違反を1件返す。"""
    present = _present_element_ids(solution)
    if present is None:
        return None
    missing = sorted(set(constraint.items) - present)
    if not missing:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"solution misses required element(s): {missing}",
        detail={"missing": missing},
    )
