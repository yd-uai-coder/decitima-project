# DeciTima samples │ 初出 Phase 4 │ 改訂 Phase 5,6,8
"""作業単位 4-5 / 5-4 / 6-3 / 8-6: rule-based の select_strategy(サービス層)。

対象 = select_strategy(registry を回すオーケストレーション)。ドライバ = このテスト関数。
スタブ = 実 REGISTRY(全 strategy 登録済み)。shift ケースは 6-3、project ケースは 8-6。
"""

import pytest
from tests.fixtures.optimization import (
    build_coord_route_problem,
    build_negative_route_problem,
    build_network_problem,
    build_project_problem,
    build_route_problem,
    build_shift_problem,
)

from app.services.algorithm_selection import select_strategy
from app.services.errors import NoAlgorithmError


def test_default_route_uses_handwritten_dijkstra() -> None:
    s = select_strategy(build_route_problem())
    assert s.meta.name == "dijkstra"
    assert s.meta.implementation == "handwritten"


def test_negative_graph_routes_to_bellman_ford() -> None:
    assert select_strategy(build_negative_route_problem()).meta.name == "bellman_ford"


def test_fully_coordinated_graph_routes_to_a_star() -> None:
    assert select_strategy(build_coord_route_problem()).meta.name == "a_star"


def test_network_design_defaults_to_kruskal() -> None:
    assert select_strategy(build_network_problem()).meta.name == "kruskal"


def test_shift_defaults_to_backtracking() -> None:
    # README §9: scheduling_with_constraints → Backtracking(小規模で最適)
    s = select_strategy(build_shift_problem())
    assert s.meta.name == "backtracking"
    assert s.meta.implementation == "handwritten"


def test_shift_honours_requested_cp_sat() -> None:
    s = select_strategy(build_shift_problem(), requested="cp_sat")
    assert s.meta.name == "cp_sat"
    assert s.meta.implementation == "library:ortools"


def test_project_with_capacity_defaults_to_priority_list() -> None:
    s = select_strategy(build_project_problem(resource_capacity=3))
    assert s.meta.name == "priority_list"
    assert s.meta.implementation == "handwritten"


def test_project_without_capacity_defaults_to_cpm() -> None:
    assert select_strategy(build_project_problem(resource_capacity=None)).meta.name == "cpm"


def test_requested_name_still_wins() -> None:
    s = select_strategy(build_coord_route_problem(), requested="dijkstra")
    assert s.meta.name == "dijkstra"


def test_unknown_requested_raises() -> None:
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_route_problem(), requested="nope")
