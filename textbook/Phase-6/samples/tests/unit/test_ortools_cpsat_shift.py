"""作業単位 6-7: OrToolsCpSatShiftStrategy(産業ソルバートラック)。

対象 = `OrToolsCpSatShiftStrategy.solve`。ドライバ = このテスト関数。
スタブ不要 ── CP-SAT は num_search_workers=1 + random_seed 固定で決定論的。
"""

from tests.fixtures.optimization import (
    build_infeasible_shift_problem,
    build_scaled_shift_problem,
    build_shift_problem,
)

from app.algorithms.scheduling.ortools_cpsat import OrToolsCpSatShiftStrategy
from app.domain.problems.shift_scheduler import ShiftData
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.services.verification import SolutionVerificationService

_STRATEGY = OrToolsCpSatShiftStrategy()


def _assignments(sol) -> dict[str, list[str]]:
    assert isinstance(sol.assignments, ShiftSolution)
    return sol.assignments.assignments


def test_meta_is_library_track() -> None:
    assert _STRATEGY.meta.implementation == "library:ortools"


def test_solves_the_example_to_optimum() -> None:
    problem = build_shift_problem()
    verified = SolutionVerificationService().verify(problem, _STRATEGY.solve(problem))
    assert verified.status == "valid"
    assert verified.metrics["labor_cost"] == 20000.0
    assert verified.metrics["day_off_satisfaction"] == 1.0


def test_does_not_emit_ops() -> None:
    # 仕事がソルバーの中 ── 操作回数は出せない(2 トラック比較の論点)
    assert "_ops" not in _STRATEGY.solve(build_shift_problem()).metrics


def test_infeasible_returns_infeasible_status() -> None:
    # s1 が 2 人必要だが eligible 1 人 ── CP-SAT は解なしを判定
    sol = _STRATEGY.solve(build_infeasible_shift_problem())
    assert sol.status == "infeasible"


def test_deterministic_same_input_same_output() -> None:
    p = build_shift_problem()
    assert _STRATEGY.solve(p).model_dump() == _STRATEGY.solve(p).model_dump()


def test_scales_where_handwritten_would_not() -> None:
    # 12 スタッフ × 5 日 × 2 スロット ── 手実装バックトラッキングは現実的に終わらない規模
    problem = build_scaled_shift_problem(n_staff=12, n_days=5, seed=1)
    sol = _STRATEGY.solve(problem)
    assert sol.status in {"valid", "infeasible"}
    if sol.status == "valid":
        data = problem.data
        assert isinstance(data, ShiftData)
        for slot in data.slots:
            assert len(_assignments(sol).get(slot.id, [])) == slot.required_headcount
