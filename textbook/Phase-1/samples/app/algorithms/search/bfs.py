"""幅優先探索(プリミティブ)。README §8 の BFS。

無重みグラフの最短経路・到達可能性。隣接リスト(素の dict)を入力に取り、
OptimizationProblem は知らない。DijkstraStrategy の内部や、Phase 1 の
route Validation の「到達可能性オラクル」として使う。設計は Phase-0-5.md §2.1。
registry には載せない。
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping

# 隣接リスト: node_id -> 隣接 node_id の並び(無重み)
AdjacencyList = Mapping[str, Iterable[str]]


def bfs_distances(adjacency: AdjacencyList, start: str) -> dict[str, int]:
    """start からの各ノードへの最短ホップ数を返す。到達不能なノードは含めない。"""
    distances: dict[str, int] = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in adjacency.get(node, ()):
            # 未訪問なら「今のノードの距離 + 1」で確定(BFS なので初回訪問が最短)
            if nxt not in distances:
                distances[nxt] = distances[node] + 1
                queue.append(nxt)
    return distances


def reachable_nodes(adjacency: AdjacencyList, start: str) -> set[str]:
    """start から到達できるノード集合。route Validation の連結性チェックに使う。"""
    return set(bfs_distances(adjacency, start))


def bfs_shortest_path(adjacency: AdjacencyList, start: str, goal: str) -> list[str] | None:
    """start から goal までの無重み最短経路(ノード列)。到達不能なら None。"""
    if start == goal:
        return [start]
    # parent[n] = BFS 木で n に最初に到達したときの1つ前のノード
    parent: dict[str, str] = {}
    visited: set[str] = {start}
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in adjacency.get(node, ()):
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = node
            if nxt == goal:
                return _reconstruct(parent, start, goal)
            queue.append(nxt)
    return None


def _reconstruct(parent: Mapping[str, str], start: str, goal: str) -> list[str]:
    """parent 辞書を goal から start まで辿り、start→goal 順のノード列に直す。"""
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path
