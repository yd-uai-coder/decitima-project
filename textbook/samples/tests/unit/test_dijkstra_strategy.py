# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 4
"""作業単位 1-4 のテスト ── Phase 4-1 の現行版(進行のルール #16)。

Phase 1 で書いたこのテストを **4-1 の写経後に再実行する**。dijkstra.py の内部実装が
大きく変わったからだ:

  before(Phase 1)── build_adjacency / _Segment / _waypoints / 区間連結ループ が
                    ぜんぶ dijkstra.py の中にあった。
  after (Phase 4-1)── それらは adjacency.py / segments.py / waypoints.py へ移り、
                     solve() は collect_route_constraints + plan_route + route_solution
                     への委譲に痩せた(`Phase-4-1.md` §3.3)。

  → public な solve() の挙動 ── 最短経路 / total_weight / _ops の決定性 / produced_by ──
    は不変。だから下の 6 件のアサーションは Phase 1 のまま、そのまま緑になる。
    **ここが赤なら _dijkstra_segment / reconstruct_path の写経ミス(このテストが番人)。**

registry.py の DijkstraStrategy 行の有効化(進行ルール #15)もここで確認する。
"""

from tests.fixtures.optimization import build_route_problem

from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.algorithms.registry import get_strategies
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import CandidateSolution

_STRATEGY = DijkstraStrategy()


def _route(sol: CandidateSolution) -> RouteSolution:
    """assignments を RouteSolution に絞り込む(discriminated union の消費側の定石)。"""
    assert isinstance(sol.assignments, RouteSolution)
    return sol.assignments


def test_finds_shortest_path_without_constraints() -> None:
    # A-B-D-E = 2+1+2 = 5 が最短(禁止・必須なし)
    sol = _STRATEGY.solve(build_route_problem())
    assert sol.status == "valid"
    assert _route(sol).path_node_ids == ["A", "B", "D", "E"]
    assert _route(sol).total_weight == 5.0
    assert sol.metrics["total_weight"] == 5.0


def test_respects_forbidden_edge_and_required_node() -> None:
    # 橋 e_bd 禁止 + C 必須経由 → A-B-C-E = 9(Phase-0-2.md §7.1 の期待解)
    sol = _STRATEGY.solve(build_route_problem(forbidden=["e_bd"], required=["C"]))
    assert _route(sol).path_node_ids == ["A", "B", "C", "E"]
    assert _route(sol).path_edge_ids == ["e_ab", "e_bc", "e_ce"]
    assert _route(sol).total_weight == 9.0
    assert "e_bd" not in _route(sol).path_edge_ids
    assert "C" in _route(sol).path_node_ids


def test_infeasible_when_goal_unreachable() -> None:
    sol = _STRATEGY.solve(build_route_problem(forbidden=["e_ce", "e_de"]))
    assert sol.status == "infeasible"
    assert _route(sol).path_node_ids == []


def test_deterministic_same_input_same_output() -> None:
    p = build_route_problem(forbidden=["e_bd"], required=["C"])
    assert _STRATEGY.solve(p).model_dump() == _STRATEGY.solve(p).model_dump()


def test_produced_by_metadata_is_attached() -> None:
    sol = _STRATEGY.solve(build_route_problem())
    assert sol.produced_by.name == "dijkstra"
    assert sol.produced_by.implementation == "handwritten"
    assert sol.produced_by.family == "graph"


def test_dijkstra_registered_for_route_planning() -> None:
    # 1-4 で registry.py の import 行と REGISTRY エントリのコメントを外した結果、
    # route_planning から dijkstra を引ける(1-2 では機構をフェイクで検証済み)。
    assert "dijkstra" in [s.meta.name for s in get_strategies("route_planning")]
