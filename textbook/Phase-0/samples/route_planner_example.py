"""Phase 0-2 の検証: Route Planner を共通スキーマで書き下す。

「A から E まで最短で行きたい。ただし橋(edge e_bd)は工事中で通れない。
C は必ず経由する。」

このファイルを実行すると、OptimizationProblem と想定解 CandidateSolution が
スキーマ上で問題なく構築できることを確認できる。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from problem_schema import (  # noqa: E402
    AlgorithmMeta,
    CandidateSolution,
    ForbiddenConstraint,
    Objective,
    OptimizationProblem,
    RequiredInclusionConstraint,
    RouteData,
    RouteEdge,
    RouteNode,
    RouteSolution,
)


def build_problem() -> OptimizationProblem:
    """例題の Route Planner を OptimizationProblem として構築する。"""
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        constraints=[
            # 橋は通行止め（hard）
            ForbiddenConstraint(severity="hard", items=["e_bd"]),
            # C は必須経由（hard）
            RequiredInclusionConstraint(severity="hard", items=["C"]),
        ],
        data=RouteData(
            nodes=[RouteNode(id=n) for n in ["A", "B", "C", "D", "E"]],
            edges=[
                RouteEdge(id="e_ab", source="A", target="B", weight=2),
                RouteEdge(id="e_bc", source="B", target="C", weight=3),
                RouteEdge(id="e_bd", source="B", target="D", weight=1),  # 禁止対象
                RouteEdge(id="e_ce", source="C", target="E", weight=4),
                RouteEdge(id="e_de", source="D", target="E", weight=2),
            ],
            start="A",
            goal="E",
        ),
    )


def expected_solution() -> CandidateSolution:
    """このアルゴリズムが返すべき解（Phase 1 の Dijkstra 実装の期待値）。"""
    return CandidateSolution(
        status="valid",
        assignments=RouteSolution(
            path_node_ids=["A", "B", "C", "E"],
            path_edge_ids=["e_ab", "e_bc", "e_ce"],
            total_weight=9.0,
        ),
        metrics={"total_weight": 9.0},
        violations=[],
        produced_by=AlgorithmMeta(
            name="dijkstra",
            family="graph",
            implementation="handwritten",
            time_complexity="O((V+E) log V)",
        ),
    )


if __name__ == "__main__":
    problem = build_problem()
    solution = expected_solution()

    # スキーマ上の整合を最小確認
    assert problem.problem_type == problem.data.problem_type
    assert solution.assignments.problem_type == "route_planning"
    edge_weight = {e.id: e.weight for e in problem.data.edges}
    total = sum(edge_weight[eid] for eid in solution.assignments.path_edge_ids)
    assert total == solution.assignments.total_weight, (total, solution.assignments.total_weight)

    print("route_planner_example OK:",
          " -> ".join(solution.assignments.path_node_ids),
          f"(weight={solution.assignments.total_weight})")
