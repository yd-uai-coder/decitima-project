"""BellmanFordStrategy(ベルマン・フォード法)── 辺の緩和を V-1 回繰り返す最短経路。

Dijkstra との違い:
  - **負の重みを扱える**(Dijkstra は settled したノードを二度と見ないので負辺で壊れる)
  - **負閉路を検出できる**(V-1 回の後もう1回緩和して更新が起きたら負閉路)
  - 代わりに遅い: O(V*E)

`RouteData.allow_negative=True` の問題はこの strategy が担当する(`Phase-0-4.md` §2.4 の
Strategy 例、README §8「Bellman-Ford ── 負辺・負閉路検出」)。

注意: **無向グラフの負辺は即・負閉路**(a→b→a で無限に下がる)。負辺のデモは有向エッジで作る。
"""

from __future__ import annotations

from app.algorithms.graph.adjacency import Adjacency, build_adjacency
from app.algorithms.graph.segments import (
    Segment,
    collect_route_constraints,
    negative_cycle_violation,
    plan_route,
    reconstruct_path,
    route_solution,
)
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.route_planner import RouteData
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution


class _NegativeCycle(Exception):
    """start から到達できる負閉路を検出した ── 最短経路は定義できない。"""


def _bellman_ford_segment(
    adjacency: Adjacency, start: str, goal: str
) -> tuple[Segment | None, int]:
    """start→goal の最短経路を1区間ぶん。負閉路があれば _NegativeCycle を送出。"""
    # (u, v, edge_id, weight) に平坦化して繰り返し緩和する
    edges = [(u, v, eid, w) for u, nbrs in adjacency.items() for v, eid, w in nbrs]
    dist: dict[str, float] = {start: 0.0}
    prev: dict[str, tuple[str, str]] = {}
    ops = 0

    # V-1 回: 各回で「もう1本エッジを挟んだ経路」まで最短が確定する
    for _ in range(max(len(adjacency) - 1, 0)):
        changed = False
        for u, v, eid, w in edges:
            ops += 1
            if u in dist and dist[u] + w < dist.get(v, float("inf")):
                dist[v] = dist[u] + w
                prev[v] = (u, eid)
                changed = True
        if not changed:
            break  # 更新が無くなったら早期終了

    # V-1 回の後でも緩和できる = start から届く負閉路
    for u, v, _eid, w in edges:
        ops += 1
        if u in dist and dist[u] + w < dist.get(v, float("inf")):
            raise _NegativeCycle

    if goal not in dist:
        return None, ops
    # 経路復元(prev を辿るだけ)は Dijkstra / A* と共通 ── segments.reconstruct_path
    return reconstruct_path(prev, start, goal, dist[goal]), ops


class BellmanFordStrategy:
    """手実装のベルマン・フォード法(implementation="handwritten")。"""

    meta = AlgorithmMeta(
        name="bellman_ford",
        family="graph",
        implementation="handwritten",
        time_complexity="O(V*E)",
        space_complexity="O(V)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = problem.data
        if not isinstance(data, RouteData):
            raise TypeError(f"BellmanFordStrategy expects RouteData, got {type(data).__name__}")

        forbidden, required = collect_route_constraints(problem)
        adjacency = build_adjacency(data, forbidden)
        try:
            seg, ops = plan_route(
                data.start,
                data.goal,
                required,
                lambda a, b: _bellman_ford_segment(adjacency, a, b),
            )
        except _NegativeCycle:
            return route_solution(None, 0, self.meta, violations=[negative_cycle_violation()])
        return route_solution(seg, ops, self.meta)
