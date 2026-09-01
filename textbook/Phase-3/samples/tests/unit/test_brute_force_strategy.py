"""作業単位 3-2: BruteForceRouteStrategy(正解オラクル)。

fixture グラフでの厳密性 + 「Dijkstra == BruteForce」プロパティ(seed を振って回す)。
対象は純粋なので**スタブ不要**。ドライバはこのテスト関数 + `build_scaled_route_problem`。
"""

from tests.fixtures.optimization import build_route_problem, build_scaled_route_problem

from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.algorithms.optimization.brute_force import BruteForceRouteStrategy
from app.algorithms.registry import get_strategies
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution

_BRUTE = BruteForceRouteStrategy()
_DIJKSTRA = DijkstraStrategy()


def _route(sol: CandidateSolution) -> RouteSolution:
    assert isinstance(sol.assignments, RouteSolution)
    return sol.assignments


def test_finds_true_shortest_path() -> None:
    # 禁止・必須なし → A-B-D-E = 5(Dijkstra と同じ)
    sol = _BRUTE.solve(build_route_problem())
    assert sol.status == "valid"
    assert _route(sol).total_weight == 5.0
    assert sol.metrics["total_weight"] == 5.0


def test_respects_forbidden_and_required() -> None:
    sol = _BRUTE.solve(build_route_problem(forbidden=["e_bd"], required=["C"]))
    assert _route(sol).path_node_ids == ["A", "B", "C", "E"]
    assert _route(sol).total_weight == 9.0
    assert "e_bd" not in _route(sol).path_edge_ids


def test_infeasible_when_disconnected() -> None:
    sol = _BRUTE.solve(build_route_problem(forbidden=["e_ce", "e_de"]))
    assert sol.status == "infeasible"
    assert _route(sol).path_node_ids == []


def test_ops_counted() -> None:
    sol = _BRUTE.solve(build_route_problem())
    assert sol.metrics["_ops"] > 0.0


def test_deterministic_same_input_same_output() -> None:
    p = build_route_problem(forbidden=["e_bd"], required=["C"])
    assert _BRUTE.solve(p).model_dump() == _BRUTE.solve(p).model_dump()


def test_registered_for_route_planning() -> None:
    assert "brute_force" in [s.meta.name for s in get_strategies("route_planning")]


def test_matches_dijkstra_on_random_graphs() -> None:
    """オラクル: 小さな連結グラフでは Dijkstra の最短距離 = 全探索の最短距離。"""
    for seed in range(50):
        problem = build_scaled_route_problem(6, seed=seed)
        d = _DIJKSTRA.solve(problem)
        b = _BRUTE.solve(problem)
        assert d.status == "valid" and b.status == "valid"
        assert _route(d).total_weight == _route(b).total_weight, f"seed={seed}"
