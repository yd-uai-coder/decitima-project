"""作業単位 1-6(補助): ProblemValidationService(route 限定の最小実装)。"""

# [以降 Phase で修正予定 ── Phase 2-2] このファイルの Phase 1 版はこのまま(スナップショット)。
# Phase 2-2 で shift が検証されるようになり test_shift_problem_passes_through_for_now は失効、
# route + shift の現行版に差し替わる。
# 現行版 textbook/Phase-2/samples/tests/unit/test_validation_service.py。詳細 Phase-2-2.md。

import pytest
from tests.fixtures.optimization import build_route_problem, build_shift_problem

from app.domain.problems.problem import Objective, OptimizationProblem
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.services.errors import InfeasibleProblemError, ProblemValidationError
from app.services.validation import ProblemValidationService

_SERVICE = ProblemValidationService()


def test_valid_route_problem_passes() -> None:
    # 例外が出なければ OK
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


def test_shift_problem_passes_through_for_now() -> None:
    # Phase 1 では shift の semantic validation は未実装 → 素通し(グレーは通す)
    _SERVICE.validate(build_shift_problem())
