"""作業単位 4-5 / 5-4: rule-based の select_strategy(サービス層)。

対象 = select_strategy(registry を回すオーケストレーション)。ドライバ = このテスト関数。
スタブ = 実 REGISTRY(Phase 4/5 end 状態で全 strategy 登録済み)。network_design ケースは 5-4。
"""

import pytest
from tests.fixtures.optimization import (
    build_coord_route_problem,
    build_negative_route_problem,
    build_network_problem,
    build_route_problem,
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


def test_requested_name_still_wins() -> None:
    s = select_strategy(build_coord_route_problem(), requested="dijkstra")
    assert s.meta.name == "dijkstra"


def test_unknown_requested_raises() -> None:
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_route_problem(), requested="nope")
