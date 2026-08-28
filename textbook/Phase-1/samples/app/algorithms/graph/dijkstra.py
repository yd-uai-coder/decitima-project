"""DijkstraStrategy ── 優先度キューを用いた手実装のダイクストラ法。

Phase 1 で唯一 registry に載る AlgorithmStrategy。route_planning 専用。設計は
Phase-0-4.md §5.1 / §7.1、計算量は Phase-0-5.md §2.2。

solve の流れ:
  1. problem.data(RouteData)から重み付き隣接リストを作る
  2. ForbiddenConstraint の items にあるエッジを除外
  3. RequiredInclusionConstraint があれば「start→必須→goal」に区間分割
     (Phase 1 は必須経由 0〜1 個。2 個以上の訪問順最適化は Phase 4)
  4. heapq でダイクストラ
  5. RouteSolution を組み立てて CandidateSolution(status="valid")を返す
     どこかの区間が非連結なら status="infeasible"

solve は純粋・検証しない(Phase-0-4.md §2.2 / §2.3)。制約を「満たしているか」の
判定は SolutionVerificationService の仕事。
"""

from __future__ import annotations

import heapq
from itertools import pairwise

from app.domain.problems.problem import (
    ForbiddenConstraint,
    OptimizationProblem,
    RequiredInclusionConstraint,
)
from app.domain.problems.route_planner import RouteData
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution

# 隣接リストの1エントリ: (隣接ノード id, そのエッジの id, 重み)
type _Adjacency = dict[str, list[tuple[str, str, float]]]


def build_adjacency(data: RouteData, forbidden_edge_ids: set[str]) -> _Adjacency:
    """RouteData から重み付き隣接リストを作る。forbidden のエッジは張らない。"""
    adjacency: _Adjacency = {node.id: [] for node in data.nodes}
    for edge in data.edges:
        if edge.id in forbidden_edge_ids:
            continue
        adjacency.setdefault(edge.source, []).append((edge.target, edge.id, edge.weight))
        if not edge.directed:
            # 無向エッジは逆向きも張る
            adjacency.setdefault(edge.target, []).append((edge.source, edge.id, edge.weight))
    return adjacency


class _Segment:
    """1 区間(始点→終点)のダイクストラ結果。"""

    __slots__ = ("node_ids", "edge_ids", "weight")

    def __init__(self, node_ids: list[str], edge_ids: list[str], weight: float) -> None:
        self.node_ids = node_ids
        self.edge_ids = edge_ids
        self.weight = weight


def _dijkstra_segment(adjacency: _Adjacency, start: str, goal: str) -> tuple[_Segment | None, int]:
    """start→goal の最短経路を1区間ぶん求める。到達不能なら (None, pops)。

    戻り値の第2要素 pops は「優先度キューから取り出した回数」= 操作回数の目安
    (Phase 3 のベンチマークで使う。metrics["_ops"] に積む)。
    """
    # dist[n] = start から n までの暫定最短距離
    dist: dict[str, float] = {start: 0.0}
    # prev[n] = 最短経路木で n の1つ前の (ノード id, エッジ id)
    prev: dict[str, tuple[str, str]] = {}
    # ヒープ要素: (暫定距離, ノード id)
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

    # goal から prev を辿って start→goal 順に復元する
    node_ids = [goal]
    edge_ids: list[str] = []
    while node_ids[-1] != start:
        p_node, p_edge = prev[node_ids[-1]]
        node_ids.append(p_node)
        edge_ids.append(p_edge)
    node_ids.reverse()
    edge_ids.reverse()
    return _Segment(node_ids, edge_ids, dist[goal]), pops


def _waypoints(start: str, goal: str, required: list[str]) -> list[str]:
    """訪問しなければならない順序列 [start, (必須...), goal] を作る(連続重複は畳む)。

    Phase 1 は required を「与えられた順」で通す。順序最適化(小さな TSP)は Phase 4。
    """
    points = [start, *required, goal]
    collapsed: list[str] = []
    for pt in points:
        if not collapsed or collapsed[-1] != pt:
            collapsed.append(pt)
    return collapsed


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
        # registry 経由なら必ず RouteData。念のため契約を確認する
        if not isinstance(data, RouteData):
            raise TypeError(f"DijkstraStrategy expects RouteData, got {type(data).__name__}")

        # 制約から「禁止エッジ」「必須経由ノード」を集める
        forbidden: set[str] = set()
        required: list[str] = []
        for c in problem.constraints:
            if isinstance(c, ForbiddenConstraint):
                forbidden.update(c.items)
            elif isinstance(c, RequiredInclusionConstraint):
                required.extend(c.items)

        adjacency = build_adjacency(data, forbidden)
        legs = _waypoints(data.start, data.goal, required)

        node_ids: list[str] = []
        edge_ids: list[str] = []
        total = 0.0
        total_ops = 0
        # 区間ごとに解いて連結する
        for a, b in pairwise(legs):
            segment, ops = _dijkstra_segment(adjacency, a, b)
            total_ops += ops
            if segment is None:
                # どこかの区間が非連結 → 解なし
                return CandidateSolution(
                    status="infeasible",
                    assignments=RouteSolution(path_node_ids=[], path_edge_ids=[], total_weight=0.0),
                    metrics={"_ops": float(total_ops)},
                    produced_by=self.meta,
                )
            # 区間の先頭ノードは前区間の末尾と重複するので落とす
            node_ids.extend(segment.node_ids if not node_ids else segment.node_ids[1:])
            edge_ids.extend(segment.edge_ids)
            total += segment.weight

        return CandidateSolution(
            status="valid",  # 「hard 制約を満たすか」は Verification が後で判定する
            assignments=RouteSolution(
                path_node_ids=node_ids, path_edge_ids=edge_ids, total_weight=total
            ),
            metrics={"total_weight": total, "_ops": float(total_ops)},
            produced_by=self.meta,
        )
