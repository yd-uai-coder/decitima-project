"""Phase 0-4 の Algorithm Engine インターフェースのスケッチ。

decitima-api には未配線。Phase 1 で app/algorithms/ 配下へ実装する。
ここでは Protocol と registry の「形」だけを示し、ダミーの strategy で
契約が成立することを確認する。
"""

from __future__ import annotations

import os
import sys
from typing import Protocol, runtime_checkable

sys.path.insert(0, os.path.dirname(__file__))

from problem_schema import (  # noqa: E402
    AlgorithmMeta,
    CandidateSolution,
    OptimizationProblem,
    RouteSolution,
)


@runtime_checkable
class AlgorithmStrategy(Protocol):
    """1つのアルゴリズムが満たす契約。problem を受けて候補解を返すだけ。"""

    meta: AlgorithmMeta

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        """OptimizationProblem を決定論的に解いて CandidateSolution を返す。検証はしない。"""
        ...


# ---------------------------------------------------------------------------
# ダミー実装（Phase 1 で本物に置き換える）
# ---------------------------------------------------------------------------


class _StubDijkstra:
    """契約が満たせることを確認するためのダミー。常に固定の経路を返す。"""

    meta = AlgorithmMeta(
        name="dijkstra",
        family="graph",
        implementation="handwritten",
        time_complexity="O((V+E) log V)",
        space_complexity="O(V)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        # 本来はここで heapq を使ったダイクストラ法（Phase 1）
        return CandidateSolution(
            status="valid",
            assignments=RouteSolution(path_node_ids=[], path_edge_ids=[], total_weight=0.0),
            metrics={"total_weight": 0.0},
            produced_by=self.meta,
        )


# ---------------------------------------------------------------------------
# registry: problem_type -> 候補アルゴリズム
# ---------------------------------------------------------------------------

REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [_StubDijkstra()],
    "shift_scheduling": [],  # Phase 1/5 で Greedy / Backtracking を追加
}


def get_strategies(problem_type: str) -> list[AlgorithmStrategy]:
    """problem_type に対応するアルゴリズム候補を返す。未登録なら空リスト。"""
    return REGISTRY.get(problem_type, [])


def select_strategy(
    problem: OptimizationProblem, requested: str | None = None
) -> AlgorithmStrategy:
    """rule-based のアルゴリズム選択。requested の明示指定を最優先する。"""
    candidates = get_strategies(problem.problem_type)
    if not candidates:
        raise LookupError(f"no algorithm registered for {problem.problem_type!r}")

    # 明示指定があれば名前で探す
    if requested is not None:
        for strategy in candidates:
            if strategy.meta.name == requested:
                return strategy
        raise LookupError(f"algorithm {requested!r} not found")

    # MVP の rule はシンプルに先頭を返す（Phase 4/5 で問題特性による分岐を入れる）
    return candidates[0]


if __name__ == "__main__":
    from problem_schema import Objective, OptimizationProblem, RouteData, RouteNode, RouteEdge

    problem = OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id="A"), RouteNode(id="B")],
            edges=[RouteEdge(id="e_ab", source="A", target="B", weight=1)],
            start="A",
            goal="B",
        ),
    )
    strategy = select_strategy(problem)
    solution = strategy.solve(problem)
    assert isinstance(strategy, AlgorithmStrategy)
    print("algorithm_strategy OK:", strategy.meta.name, "->", solution.status)
