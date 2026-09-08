# DeciTima samples │ Phase 3
"""作業単位 3-4: 入力サイズ別カーブ + 解の品質。

対象 = DijkstraStrategy / BruteForceRouteStrategy(純粋)。ドライバ = このテスト関数 +
`build_scaled_route_problem`。スタブ不要。BenchmarkService を通さず strategy を直に回す
── 「入力サイズを振って操作回数の伸びを見る」というカーブの本質だけを確認する。
"""

from tests.fixtures.optimization import build_scaled_route_problem

from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.algorithms.optimization.brute_force import BruteForceRouteStrategy
from app.domain.solutions.route_planner import RouteSolution

_DIJKSTRA = DijkstraStrategy()
_BRUTE = BruteForceRouteStrategy()


def _weight(sol) -> float:
    assert isinstance(sol.assignments, RouteSolution)
    return sol.assignments.total_weight


def test_brute_force_ops_grow_much_faster_than_dijkstra() -> None:
    sizes = [4, 6, 8, 10]
    dijkstra_ops: list[float] = []
    brute_ops: list[float] = []
    for n in sizes:
        problem = build_scaled_route_problem(n, seed=1)
        dijkstra_ops.append(_DIJKSTRA.solve(problem).metrics["_ops"])
        brute_ops.append(_BRUTE.solve(problem).metrics["_ops"])

    # Dijkstra は多項式的、全探索は指数的 ── 最大サイズでの比が大きく開く
    assert brute_ops[-1] > dijkstra_ops[-1]
    assert brute_ops[-1] / brute_ops[0] > dijkstra_ops[-1] / max(dijkstra_ops[0], 1.0)


def test_both_find_the_same_optimum_at_every_size() -> None:
    for n in [4, 6, 8, 10]:
        problem = build_scaled_route_problem(n, seed=1)
        assert _weight(_DIJKSTRA.solve(problem)) == _weight(_BRUTE.solve(problem)), f"n={n}"
