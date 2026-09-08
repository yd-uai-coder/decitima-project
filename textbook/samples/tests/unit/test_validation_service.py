# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 2
"""作業単位 2-2: ProblemValidationService(route + shift の Semantic Validation)。"""

import pytest
from tests.fixtures.optimization import (
    build_infeasible_shift_problem,
    build_route_problem,
    build_shift_problem,
)

from app.domain.problems.problem import Objective, OptimizationProblem
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff
from app.services.errors import InfeasibleProblemError, ProblemValidationError
from app.services.validation import ProblemValidationService

_SERVICE = ProblemValidationService()


# --- route ------------------------------------------------------------------


def test_valid_route_problem_passes() -> None:
    _SERVICE.validate(build_route_problem(forbidden=["e_bd"], required=["C"]))


def test_unknown_start_node_is_rejected() -> None:
    problem = OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id="A"), RouteNode(id="B")],
            edges=[RouteEdge(id="e_ab", source="A", target="B", weight=1)],
            start="Z",
            goal="B",
        ),
    )
    with pytest.raises(ProblemValidationError):
        _SERVICE.validate(problem)


def test_edge_referencing_unknown_node_is_rejected() -> None:
    problem = OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id="A"), RouteNode(id="B")],
            edges=[RouteEdge(id="e_ax", source="A", target="X", weight=1)],
            start="A",
            goal="B",
        ),
    )
    with pytest.raises(ProblemValidationError):
        _SERVICE.validate(problem)


def test_unreachable_goal_is_infeasible() -> None:
    with pytest.raises(InfeasibleProblemError):
        _SERVICE.validate(build_route_problem(forbidden=["e_ce", "e_de"]))


# --- shift(Phase 2 で素通しをやめ、検証する)---------------------------------


def test_valid_shift_problem_passes() -> None:
    _SERVICE.validate(build_shift_problem())


def test_shift_staff_referencing_unknown_slot_is_rejected() -> None:
    problem = OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[Objective(sense="minimize", target="labor_cost")],
        data=ShiftData(
            staff=[Staff(id="a", hourly_wage=1000, available_slot_ids=["s1", "ghost"])],
            slots=[
                ShiftSlot(
                    id="s1", day="2026-09-01", start_hour=9, end_hour=14, required_headcount=1
                )
            ],
        ),
    )
    with pytest.raises(ProblemValidationError):
        _SERVICE.validate(problem)


def test_shift_with_too_few_eligible_staff_is_infeasible() -> None:
    with pytest.raises(InfeasibleProblemError):
        _SERVICE.validate(build_infeasible_shift_problem())


def test_shift_missing_required_skill_holder_is_infeasible() -> None:
    problem = OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[Objective(sense="minimize", target="labor_cost")],
        data=ShiftData(
            staff=[Staff(id="a", hourly_wage=1000, skills=["cook"], available_slot_ids=["s1"])],
            slots=[
                ShiftSlot(
                    id="s1",
                    day="2026-09-01",
                    start_hour=9,
                    end_hour=14,
                    required_headcount=1,
                    required_skills=["barista"],
                )
            ],
        ),
    )
    with pytest.raises(InfeasibleProblemError):
        _SERVICE.validate(problem)
