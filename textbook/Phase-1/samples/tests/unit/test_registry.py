"""作業単位 1-2: AlgorithmStrategy Protocol と registry / select_strategy。

この章の時点では registry に実 strategy は載っていない(DijkstraStrategy は 1-4 で有効化)。
registry の「機構」(登録・照会・選択・送出)を、具体アルゴリズムに依存せず
フェイクを fixture で差し込んでテストする(進行ルール #15)。
実体(dijkstra)が route_planning から引けることの確認は test_dijkstra_strategy.py(1-4)。
"""

import pytest
from tests.fixtures.optimization import build_route_problem, build_shift_problem

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import REGISTRY, all_strategies, find_strategy, get_strategies
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution
from app.services.algorithm_selection import select_strategy
from app.services.errors import NoAlgorithmError


class _FakeStrategy:
    """Protocol は継承不要 ── meta と solve を持てば AlgorithmStrategy として通る。"""

    meta = AlgorithmMeta(name="fake", family="graph", implementation="handwritten")

    def solve(self, problem):  # noqa: ANN001, ANN201
        return CandidateSolution(
            status="valid",
            assignments=RouteSolution(path_node_ids=[], path_edge_ids=[], total_weight=0.0),
            produced_by=self.meta,
        )


@pytest.fixture
def route_has_fake(monkeypatch: pytest.MonkeyPatch) -> _FakeStrategy:
    """REGISTRY["route_planning"] にフェイク1件を差し込んだ状態(テスト後は自動で戻る)。"""
    fake = _FakeStrategy()
    monkeypatch.setitem(REGISTRY, "route_planning", [fake])
    return fake


def test_fake_conforms_to_protocol() -> None:
    # @runtime_checkable なので isinstance が使える。名前の存在しか見ない点に注意
    assert isinstance(_FakeStrategy(), AlgorithmStrategy)


def test_get_strategies_returns_registered_candidates(route_has_fake: _FakeStrategy) -> None:
    assert route_has_fake in get_strategies("route_planning")
    assert get_strategies("unknown_type") == []


def test_all_strategies_returns_pairs(route_has_fake: _FakeStrategy) -> None:
    pairs = all_strategies()
    assert ("route_planning",) not in pairs  # ペアであってタプル1要素ではない
    assert ("route_planning", route_has_fake) in pairs


def test_select_strategy_default_returns_first_candidate(route_has_fake: _FakeStrategy) -> None:
    assert select_strategy(build_route_problem()).meta.name == "fake"


def test_select_strategy_honors_requested_name(route_has_fake: _FakeStrategy) -> None:
    assert select_strategy(build_route_problem(), requested="fake").meta.name == "fake"


def test_select_strategy_unknown_requested_raises(route_has_fake: _FakeStrategy) -> None:
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_route_problem(), requested="a_star")


def test_select_strategy_unregistered_problem_type_raises() -> None:
    # shift_scheduling はまだ登録アルゴリズムが無い(Phase 5)
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_shift_problem())


def test_find_strategy_name_mismatch_returns_none(route_has_fake: _FakeStrategy) -> None:
    # 候補はあるが requested 名が一致しない → 送出せず None(next(..., None) の分岐)
    assert find_strategy(build_route_problem(), requested="nope") is None


def test_find_strategy_empty_candidates_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # 候補ゼロでも送出せず None(送出は services 層の select_strategy の役割)
    monkeypatch.setitem(REGISTRY, "route_planning", [])
    assert find_strategy(build_route_problem()) is None
