"""作業単位 1-6(補助): SolutionVerificationService(route 限定の最小実装)。"""

# [以降 Phase で修正予定 ── Phase 2-3 / 2-4] このファイルの Phase 1 版はこのまま(スナップショット)。
# Phase 2-3 / 2-4 で shift の構造検証・numeric_bound チェッカーのケースを追加した現行版に差し替わる。
# 現行版 textbook/Phase-2/samples/tests/unit/test_verification_service.py。詳細 Phase-2-3.md / Phase-2-4.md。

from tests.fixtures.optimization import build_route_problem

from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution
from app.services.verification import SolutionVerificationService

_STRATEGY = DijkstraStrategy()
_VERIFY = SolutionVerificationService()
_META = AlgorithmMeta(name="dijkstra", family="graph", implementation="handwritten")


def test_valid_solution_stays_valid_with_no_violations() -> None:
    problem = build_route_problem(forbidden=["e_bd"], required=["C"])
    verified = _VERIFY.verify(problem, _STRATEGY.solve(problem))
    assert verified.status == "valid"
    assert verified.violations == []
    assert verified.metrics["soft_penalty"] == 0.0


def test_solution_using_forbidden_edge_becomes_invalid() -> None:
    problem = build_route_problem(forbidden=["e_bd"])
    # わざと禁止エッジ e_bd を通る「悪い解」を作る
    bad = CandidateSolution(
        status="valid",
        assignments=RouteSolution(
            path_node_ids=["A", "B", "D", "E"],
            path_edge_ids=["e_ab", "e_bd", "e_de"],
            total_weight=5.0,
        ),
        metrics={"total_weight": 5.0},
        produced_by=_META,
    )
    verified = _VERIFY.verify(problem, bad)
    assert verified.status == "invalid"
    assert any(v.constraint_kind == "forbidden" for v in verified.violations)


def test_missing_required_node_becomes_invalid() -> None:
    problem = build_route_problem(required=["C"])
    bad = CandidateSolution(
        status="valid",
        assignments=RouteSolution(
            path_node_ids=["A", "B", "D", "E"],
            path_edge_ids=["e_ab", "e_bd", "e_de"],
            total_weight=5.0,
        ),
        metrics={"total_weight": 5.0},
        produced_by=_META,
    )
    verified = _VERIFY.verify(problem, bad)
    assert verified.status == "invalid"
    assert any(v.constraint_kind == "required_inclusion" for v in verified.violations)


def test_total_weight_mismatch_is_flagged() -> None:
    problem = build_route_problem()
    bad = CandidateSolution(
        status="valid",
        assignments=RouteSolution(
            path_node_ids=["A", "B", "D", "E"],
            path_edge_ids=["e_ab", "e_bd", "e_de"],
            total_weight=999.0,  # 実際の合計は 5
        ),
        produced_by=_META,
    )
    verified = _VERIFY.verify(problem, bad)
    assert verified.status == "invalid"


def test_verify_does_not_mutate_original() -> None:
    problem = build_route_problem()
    raw = _STRATEGY.solve(problem)
    _VERIFY.verify(problem, raw)
    assert "soft_penalty" not in raw.metrics  # 元の解は書き換えられていない


def test_infeasible_solution_is_passed_through() -> None:
    problem = build_route_problem(forbidden=["e_ce", "e_de"])
    raw = _STRATEGY.solve(problem)
    assert raw.status == "infeasible"
    assert _VERIFY.verify(problem, raw).status == "infeasible"
