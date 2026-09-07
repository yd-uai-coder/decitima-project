"""グラフの到達可能性クエリ(プリミティブ)。

`build_adjacency`(dijkstra.py)と BFS(search/bfs.py)の薄い合成。「禁止エッジを除いた
グラフで goal が start から到達できるか」を bool で返すだけの純粋関数。
Validation の実行可能性チェック(ProblemValidationService)が hard ゲートとして使う。
registry には載せない ── ストラテジーではなくグラフのクエリ。

`build_adjacency` が dijkstra.py に置かれているのは Phase 1 の現実的な選択。グラフ
プリミティブの整理は Phase 4(A* / Bellman-Ford / MST 追加時)で検討する。
"""

# [以降 Phase で修正予定 ── Phase 4-1] このファイルの現行版はこのまま(スナップショット)。
# Phase 4-1 で build_adjacency の import 元が graph/dijkstra → graph/adjacency に変わる(挙動は不変)。
# 現行版 textbook/Phase-4/samples/app/algorithms/graph/reachability.py。

from __future__ import annotations

from app.algorithms.graph.dijkstra import build_adjacency
from app.algorithms.search.bfs import reachable_nodes
from app.domain.problems.route_planner import RouteData


def route_reachable(data: RouteData, forbidden_edge_ids: set[str]) -> bool:
    """禁止エッジを除いたグラフで data.goal が data.start から到達可能なら True。"""
    adjacency = build_adjacency(data, forbidden_edge_ids)
    # build_adjacency は (隣接, edge_id, weight) を返すので id だけの隣接に落とす
    plain = {node: [nxt for nxt, _eid, _w in edges] for node, edges in adjacency.items()}
    return data.goal in reachable_nodes(plain, data.start)
