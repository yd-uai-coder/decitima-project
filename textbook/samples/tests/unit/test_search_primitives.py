# DeciTima samples │ Phase 1
"""作業単位 1-3: 探索プリミティブ(linear / binary search・BFS・DFS)。

正常系 / 空入力 / 単一要素 / 到達不能 / 既知の最短距離と一致(Phase-0-9.md §1.1)。
"""

import pytest

from app.algorithms.search.bfs import bfs_distances, bfs_shortest_path, reachable_nodes
from app.algorithms.search.binary_search import binary_search, is_sorted_ascending
from app.algorithms.search.dfs import dfs_has_path, dfs_preorder
from app.algorithms.search.linear_search import linear_search

# --- linear / binary search ---


@pytest.mark.parametrize(
    ("seq", "target", "expected"),
    [
        ([1, 3, 5, 7, 9], 7, 3),
        ([1, 3, 5, 7, 9], 1, 0),
        ([1, 3, 5, 7, 9], 9, 4),
        ([1, 3, 5, 7, 9], 4, -1),
        ([42], 42, 0),
        ([42], 7, -1),
        ([], 1, -1),
    ],
)
def test_binary_search(seq: list[int], target: int, expected: int) -> None:
    assert binary_search(seq, target) == expected


def test_binary_and_linear_agree_on_sorted_input() -> None:
    seq = [2, 4, 6, 8, 10, 12]
    for t in [*seq, 5, 0, 99]:
        assert binary_search(seq, t) == linear_search(seq, t)


def test_is_sorted_ascending() -> None:
    assert is_sorted_ascending([1, 1, 2, 3])
    assert not is_sorted_ascending([1, 3, 2])


# --- BFS ---

_ADJ = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": []}


def test_bfs_distances_are_shortest_hop_counts() -> None:
    assert bfs_distances(_ADJ, "A") == {"A": 0, "B": 1, "C": 1, "D": 2, "E": 3}


def test_bfs_shortest_path_len_matches_distance() -> None:
    path = bfs_shortest_path(_ADJ, "A", "E")
    assert path is not None
    assert path[0] == "A" and path[-1] == "E"
    assert len(path) - 1 == bfs_distances(_ADJ, "A")["E"]


def test_bfs_start_equals_goal() -> None:
    assert bfs_shortest_path(_ADJ, "A", "A") == ["A"]


def test_bfs_unreachable_returns_none() -> None:
    assert bfs_shortest_path({"A": [], "B": []}, "A", "B") is None
    assert reachable_nodes({"A": [], "B": []}, "A") == {"A"}


# --- DFS ---


def test_dfs_preorder_visits_all_reachable() -> None:
    order = dfs_preorder(_ADJ, "A")
    assert order[0] == "A"
    assert set(order) == {"A", "B", "C", "D", "E"}


def test_dfs_has_path() -> None:
    assert dfs_has_path(_ADJ, "A", "E")
    assert not dfs_has_path({"A": [], "B": []}, "A", "B")


def test_dfs_single_node() -> None:
    assert dfs_preorder({"X": []}, "X") == ["X"]
