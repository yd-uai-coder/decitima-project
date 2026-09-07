"""DijkstraStrategy(ダイクストラ法)── 優先度キューを用いた手実装のダイクストラ法。

Phase 1 で唯一 registry に載っていた strategy。Phase 4 で:
  - `build_adjacency` を `adjacency.py` へ移設(import 元が変わっただけ)
  - 必須経由地の順序最適化を `segments.plan_route` 経由に(Phase 1 は「与えられた順」)
  - 負辺グラフ(`allow_negative=True`)を渡されたら infeasible で降りる(Bellman-Ford の担当)

区間の求め方(`_dijkstra_segment`)以外は Bellman-Ford / A* と同じで、共通部分は
`segments.py` に集約した(経路復元は `segments.reconstruct_path`)。solve は純粋・検証しない
(`Phase-0-4.md` §2.2)。
"""

from __future__ import annotations

import heapq

from app.algorithms.graph.adjacency import (
    Adjacency,
    build_adjacency,
    has_negative_weight,
)
from app.algorithms.graph.segments import (
    Segment,
    collect_route_constraints,
    negative_weight_violation,
    plan_route,
    reconstruct_path,
    route_solution,
)
from app.domain.problems.problem import OptimizationProblem
from app.domain.problems.route_planner import RouteData
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution


# 写経の罠: _dijkstra_segment は必ず (Segment | None, int) のタプルを返す。末尾は
#   return reconstruct_path(prev, start, goal, dist[goal]), pops
# で、return / , pops を落とすと None が返り、plan_route 内で
# TypeError: cannot unpack non-iterable NoneType object になる(そのときここを見る)。
def _dijkstra_segment(adjacency: Adjacency, start: str, goal: str) -> tuple[Segment | None, int]:
    """start→goal の最短経路を1区間ぶん求める。到達不能なら (None, pops)。

    pops は「優先度キューから取り出した回数」= 操作回数の目安(metrics["_ops"])。
    """
    dist: dict[str, float] = {start: 0.0}  # start から各ノードへの暫定最短距離
    prev: dict[str, tuple[str, str]] = {}  # 最短経路木で n の1つ前の (ノード id, エッジ id)
    heap: list[tuple[float, str]] = [(0.0, start)]
    settled: set[str] = set()
    pops = 0

    while heap:
        d, node = heapq.heappop(heap)
        pops += 1
        # 同じノードが古い距離で複数回入っていることがあるのでスキップ
        if node in settled:
            continue
        settled.add(node)
        if node == goal:
            break
        for nxt, edge_id, weight in adjacency.get(node, ()):
            nd = d + weight
            # より短い経路が見つかったら更新してヒープに積む
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                prev[nxt] = (node, edge_id)
                heapq.heappush(heap, (nd, nxt))

    if goal not in settled:
        return None, pops
    return reconstruct_path(prev, start, goal, dist[goal]), pops


class DijkstraStrategy:
    """手実装のダイクストラ法。学習・再現性の説明用(implementation="handwritten")。"""

    meta = AlgorithmMeta(
        name="dijkstra",
        family="graph",
        implementation="handwritten",
        time_complexity="O((V+E) log V)",
        space_complexity="O(V)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        """route_planning の OptimizationProblem を解いて候補解を返す。"""
        data = problem.data
        if not isinstance(data, RouteData):
            raise TypeError(f"DijkstraStrategy expects RouteData, got {type(data).__name__}")

        forbidden, required = collect_route_constraints(problem)
        adjacency = build_adjacency(data, forbidden)
        # 負辺があると Dijkstra の settled 不変条件が壊れる ── 負辺は Bellman-Ford の担当
        if has_negative_weight(adjacency):
            return route_solution(
                None, 0, self.meta, violations=[negative_weight_violation("dijkstra")]
            )

        seg, ops = plan_route(
            data.start,
            data.goal,
            required,
            lambda a, b: _dijkstra_segment(adjacency, a, b),
        )
        return route_solution(seg, ops, self.meta)
