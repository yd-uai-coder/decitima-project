"""作業単位 1-2: AlgorithmStrategy Protocol と registry / select_strategy。"""

import pytest
from tests.fixtures.optimization import build_route_problem

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import all_strategies, find_strategy, get_strategies
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution
from app.services.algorithm_selection import select_strategy
from app.services.errors import NoAlgorithmError


class _FakeStrategy:
    """Protocol は継承不要 ── meta と solve を持てば AlgorithmStrategy として通る。"""

    meta = AlgorithmMeta(name="fake", family="graph", implementation="handwritten")

    def solve(self, problem):  # noqa: ANN001, ANN201
        return CandidateSolution(
            status="valid",
            assignments=RouteSolution(path_node_ids=[], path_edge_ids=[], total_weight=0.0),
            produced_by=self.meta,
        )


def test_fake_conforms_to_protocol() -> None:
    assert isinstance(_FakeStrategy(), AlgorithmStrategy)


def test_dijkstra_is_registered_for_route_planning() -> None:
    names = [s.meta.name for s in get_strategies("route_planning")]
    assert "dijkstra" in names


def test_all_strategies_returns_pairs() -> None:
    pairs = all_strategies()
    assert ("route_planning",) not in pairs  # ペアであってタプル1要素ではない
    assert any(pt == "route_planning" and s.meta.name == "dijkstra" for pt, s in pairs)


def test_select_strategy_default_returns_first_candidate() -> None:
    strategy = select_strategy(build_route_problem())
    assert strategy.meta.name == "dijkstra"


def test_select_strategy_honors_requested_name() -> None:
    strategy = select_strategy(build_route_problem(), requested="dijkstra")
    assert strategy.meta.name == "dijkstra"


def test_select_strategy_unknown_requested_raises() -> None:
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_route_problem(), requested="a_star")


def test_select_strategy_unregistered_problem_type_raises() -> None:
    # shift_scheduling はまだ登録アルゴリズムが無い(Phase 5)
    from tests.fixtures.optimization import build_shift_problem

    with pytest.raises(NoAlgorithmError):
        select_strategy(build_shift_problem())


def test_find_strategy_returns_none_instead_of_raising() -> None:
    assert find_strategy(build_route_problem(), requested="nope") is None
