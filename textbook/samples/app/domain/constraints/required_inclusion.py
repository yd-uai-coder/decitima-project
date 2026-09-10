# DeciTima samples │ 初出 Phase 2 │ 改訂 Phase 5,7
"""required_inclusion 制約のチェッカー ── 解が「必ず含めるべき要素」をすべて含むか。

Phase 5-3 で network_design、Phase 7-3 で travel_planning に対応。意味は解型で変わる:
  - route 解   … 必須「経由ノード」id(path_node_ids に含まれるか)
  - network 解 … 必須「リンク」id(selected_link_ids に含まれるか)
  - travel 解  … 必須「訪問地」id(selected_place_ids に含まれるか)

Phase 7-3: 解 → 要素 id 集合の抽出を forbidden と共有する
`constraints/elements.py::solution_element_ids` に一本化した(進行のルール #17)。
"""

from __future__ import annotations

from app.domain.constraints.elements import solution_element_ids  # (Phase 7-3) 重複ヘルパを共通化
from app.domain.problems.problem import OptimizationProblem, RequiredInclusionConstraint
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation


def check_required_inclusion(
    constraint: RequiredInclusionConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が必須要素(必須経由ノード / 必須リンク id 等)を取りこぼしていれば違反を1件返す。"""
    # required_inclusion は「訪問・経由した地点」を対象にするので route 解では node を見る
    present = solution_element_ids(solution, aspect="nodes")
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
