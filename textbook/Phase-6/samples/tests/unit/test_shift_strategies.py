"""作業単位 6-7: 4 strategy の一致 + shift の end-to-end パイプライン。

対象 = registry["shift_scheduling"] の 4 strategy(Greedy / Backtracking / B&B / CP-SAT)と、
validate → select_strategy → solve → verify のフルパイプライン。
ドライバ = このテスト関数(`@pytest.mark.parametrize`)。スタブ不要。

end-to-end は registry が 4 strategy で埋まるこの章で初めて green(#15 ── Q35 と同型)。
"""

import pytest
from tests.fixtures.optimization import build_shift_problem

from app.algorithms.scheduling.backtracking import BacktrackingShiftStrategy
from app.algorithms.scheduling.branch_and_bound import BranchAndBoundShiftStrategy
from app.algorithms.scheduling.common import score
from app.algorithms.scheduling.greedy import GreedyShiftStrategy
from app.algorithms.scheduling.ortools_cpsat import OrToolsCpSatShiftStrategy
from app.domain.problems.shift_scheduler import ShiftData
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.services.algorithm_selection import select_strategy
from app.services.validation import ProblemValidationService
from app.services.verification import SolutionVerificationService

_EXACT = [BacktrackingShiftStrategy(), BranchAndBoundShiftStrategy(), OrToolsCpSatShiftStrategy()]
_IDS = [f"{s.meta.name}:{s.meta.implementation}" for s in _EXACT]


def _assignments(sol) -> dict[str, list[str]]:
    assert isinstance(sol.assignments, ShiftSolution)
    return sol.assignments.assignments


@pytest.mark.parametrize("strategy", _EXACT, ids=_IDS)
def test_exact_strategies_agree_on_labor_and_day_off(strategy) -> None:
    problem = build_shift_problem()
    verified = SolutionVerificationService().verify(problem, strategy.solve(problem))
    assert verified.status == "valid"
    assert verified.metrics["labor_cost"] == 20000.0
    assert verified.metrics["day_off_satisfaction"] == 1.0


@pytest.mark.parametrize("strategy", _EXACT, ids=_IDS)
def test_exact_strategies_reach_the_same_optimal_score(strategy) -> None:
    problem = build_shift_problem()
    data = problem.data
    assert isinstance(data, ShiftData)
    optimal = min(
        score(problem, data, _assignments(s.solve(problem)))[0]
        for s in (BacktrackingShiftStrategy(),)
    )
    s, _ = score(problem, data, _assignments(strategy.solve(problem)))
    assert s == optimal


def test_greedy_is_feasible_but_not_guaranteed_optimal() -> None:
    problem = build_shift_problem()
    verified = SolutionVerificationService().verify(problem, GreedyShiftStrategy().solve(problem))
    assert verified.status == "valid"


def test_shift_end_to_end_pipeline() -> None:
    """validate → select_strategy → solve → verify が shift で通る(専用 route 不要)。"""
    problem = build_shift_problem()
    ProblemValidationService().validate(problem)
    strategy = select_strategy(problem)
    assert strategy.meta.name == "backtracking"  # 既定
    verified = SolutionVerificationService().verify(problem, strategy.solve(problem))
    assert verified.status == "valid"
    assert verified.metrics["labor_cost"] == 20000.0


def test_three_objective_problem_all_strategies_feasible() -> None:
    # 第 3 目的(hour_variance)込みでも全 strategy が実行可能解を返す
    problem = build_shift_problem(with_hour_variance=True)
    for strategy in [GreedyShiftStrategy(), *_EXACT]:
        verified = SolutionVerificationService().verify(problem, strategy.solve(problem))
        assert verified.status == "valid"
        assert "hour_variance" in verified.metrics
