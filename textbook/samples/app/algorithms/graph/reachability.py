# DeciTima samples │ 初出 Phase 2 │ 改訂 Phase 4,9
"""グラフの到達可能性クエリ(プリミティブ)。

`build_adjacency`(Phase 4 で `adjacency.py` へ移設)と BFS(`search/bfs.py`)の薄い合成。
「禁止エッジを除いたグラフで goal が start から到達できるか」を bool で返すだけの純粋関数。
Validation の実行可能性チェック(`ProblemValidationService`)が hard ゲートとして使う。
registry には載せない ── ストラテジーではなくグラフのクエリ。

Phase 9-1 で `logistics_deliveries_reachable`(デポから全配送先ノードへの到達可能性、
複数ターゲット版)を追加。
"""

from __future__ import annotations

from app.algorithms.graph.adjacency import (
    build_adjacency,
    build_logistics_adjacency,  # (Phase 9-1)
    plain_adjacency,
)
from app.algorithms.search.bfs import reachable_nodes
from app.domain.problems.logistics import LogisticsData  # (Phase 9-1)
from app.domain.problems.route_planner import RouteData


def route_reachable(data: RouteData, forbidden_edge_ids: set[str]) -> bool:
    """禁止エッジを除いたグラフで data.goal が data.start から到達可能なら True。"""
    adjacency = build_adjacency(data, forbidden_edge_ids)
    return data.goal in reachable_nodes(plain_adjacency(adjacency), data.start)


def logistics_deliveries_reachable(data: LogisticsData, forbidden_segment_ids: set[str]) -> bool:
    """禁止区間を除いた道路網で、デポから全配送先ノードへ到達可能なら True(複数ターゲット版)。"""
    adjacency = build_logistics_adjacency(data, forbidden_segment_ids)
    reached = reachable_nodes(plain_adjacency(adjacency), data.depot_id)
    return all(d.node_id in reached for d in data.deliveries)
