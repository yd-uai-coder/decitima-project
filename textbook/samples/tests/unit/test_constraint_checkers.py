# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 2,7
"""作業単位 2-3: 制約 kind ごとのチェッカー(app/domain/constraints/)。

各チェッカーは純粋関数。スタブ不要 ── 問題と解を手で組んで直接呼ぶ。
Phase 7-3 で forbidden / required_inclusion が travel 解(selected_place_ids)にも効くケースを追記。
あわせて 7-3 で解 → 要素 id 集合の抽出を `constraints/elements.py::solution_element_ids` に共通化
(route の nodes/edges 分岐を直接テストする ── #15。写経漏れをこのファイルで赤にする)。
"""

from tests.fixtures.optimization import (
    build_route_problem,
    build_shift_problem,
    build_shift_solution,
    build_travel_problem,
    build_travel_solution,
)

from app.domain.constraints import CHECKERS
from app.domain.constraints.elements import solution_element_ids
from app.domain.constraints.forbidden import check_forbidden
from app.domain.constraints.numeric_bound import check_numeric_bound
from app.domain.constraints.required_inclusion import check_required_inclusion
from app.domain.constraints.staffing import check_staffing
from app.domain.problems.problem import (
    ForbiddenConstraint,
    NumericBoundConstraint,
    RequiredInclusionConstraint,
    StaffingConstraint,
)
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution

_META = AlgorithmMeta(name="x", family="graph", implementation="handwritten")


def _route_solution(*, weight: float = 9.0) -> CandidateSolution:
    return CandidateSolution(
        status="valid",
        assignments=RouteSolution(
            path_node_ids=["A", "B", "C", "E"],
            path_edge_ids=["e_ab", "e_bc", "e_ce"],
            total_weight=weight,
        ),
        metrics={"total_weight": weight},
        produced_by=_META,
    )


def test_registry_has_all_mvp_kinds() -> None:
    assert set(CHECKERS) == {"forbidden", "required_inclusion", "numeric_bound", "staffing"}


_ROUTE_PROBLEM = build_route_problem()


def test_numeric_bound_satisfied_returns_none() -> None:
    c = NumericBoundConstraint(severity="hard", field="total_weight", operator="<=", value=10)
    assert check_numeric_bound(c, _ROUTE_PROBLEM, _route_solution(weight=9.0)) is None


def test_numeric_bound_violated_returns_violation() -> None:
    c = NumericBoundConstraint(severity="hard", field="total_weight", operator="<=", value=8)
    v = check_numeric_bound(c, _ROUTE_PROBLEM, _route_solution(weight=9.0))
    assert v is not None and v.severity == "hard"


def test_numeric_bound_missing_metric_is_skipped() -> None:
    c = NumericBoundConstraint(severity="hard", field="labor_cost", operator="<=", value=1)
    assert check_numeric_bound(c, _ROUTE_PROBLEM, _route_solution()) is None


def test_solution_element_ids_route_aspect_splits_nodes_and_edges() -> None:
    # forbidden(edges)と required_inclusion(nodes)で route 解の見る id 列が変わる
    sol = _route_solution()
    assert solution_element_ids(sol, aspect="nodes") == {"A", "B", "C", "E"}
    assert solution_element_ids(sol, aspect="edges") == {"e_ab", "e_bc", "e_ce"}
    # forbidden / required_inclusion の対象外の解型は None(チェッカーは素通し)
    shift_sol = build_shift_solution({"s1": ["tanaka"]})
    assert solution_element_ids(shift_sol, aspect="edges") is None


def test_forbidden_on_non_route_solution_is_skipped() -> None:
    c = ForbiddenConstraint(severity="hard", items=["e_bd"])
    shift_sol = build_shift_solution({"s1": ["tanaka"]})
    assert check_forbidden(c, build_shift_problem(), shift_sol) is None


# (Phase 7-3) travel 解にも既存チェッカーが効くケース
def test_forbidden_on_travel_solution_flags_visited_place() -> None:
    c = ForbiddenConstraint(severity="hard", items=["P3"])
    sol = build_travel_solution(["P1", "P3"], ["P1", "P3"])
    v = check_forbidden(c, build_travel_problem(), sol)
    assert v is not None and v.detail["forbidden_hit"] == ["P3"]


def test_required_inclusion_on_travel_solution_flags_missing_place() -> None:
    c = RequiredInclusionConstraint(severity="hard", items=["P4"])
    sol = build_travel_solution(["P1", "P2"], ["P1", "P2"])
    v = check_required_inclusion(c, build_travel_problem(), sol)
    assert v is not None and v.detail["missing"] == ["P4"]


def test_required_inclusion_missing_node_returns_violation() -> None:
    c = RequiredInclusionConstraint(severity="hard", items=["D"])
    v = check_required_inclusion(c, _ROUTE_PROBLEM, _route_solution())
    assert v is not None and v.detail["missing"] == ["D"]


def test_staffing_exact_headcount_returns_none() -> None:
    problem = build_shift_problem()
    sol = build_shift_solution({"s1": ["tanaka"], "s2": ["sato"], "s3": ["ito"], "s4": ["sato"]})
    assert check_staffing(StaffingConstraint(severity="hard"), problem, sol) is None


def test_staffing_understaffed_returns_violation() -> None:
    problem = build_shift_problem()
    sol = build_shift_solution({"s1": ["tanaka"], "s2": [], "s3": ["ito"], "s4": ["sato"]})
    v = check_staffing(StaffingConstraint(severity="hard"), problem, sol)
    assert v is not None and v.detail["slots"][0]["slot"] == "s2"
