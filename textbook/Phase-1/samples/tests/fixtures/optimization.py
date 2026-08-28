"""テスト用の問題ビルダー。Phase 0 の samples/route_planner_example.py 相当を関数化したもの。

decitima-api の pyproject は pythonpath=["."] なので `from tests.fixtures.optimization import ...`
で名前空間パッケージとして import できる。
"""

from __future__ import annotations

from app.domain.problems.problem import (
    ForbiddenConstraint,
    NumericBoundConstraint,
    Objective,
    OptimizationProblem,
    RequiredInclusionConstraint,
    StaffingConstraint,
)
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff

# Phase 0-2 §7.1 の例題:
#   「A から E まで最短で行きたい。ただし橋(edge e_bd)は工事中で通れない。C は必ず経由する。」
#   期待解: A -> B -> C -> E, total_weight = 9
_ROUTE_EDGES = [
    RouteEdge(id="e_ab", source="A", target="B", weight=2),
    RouteEdge(id="e_bc", source="B", target="C", weight=3),
    RouteEdge(id="e_bd", source="B", target="D", weight=1),
    RouteEdge(id="e_ce", source="C", target="E", weight=4),
    RouteEdge(id="e_de", source="D", target="E", weight=2),
]


def build_route_problem(
    *,
    forbidden: list[str] | None = None,
    required: list[str] | None = None,
    start: str = "A",
    goal: str = "E",
) -> OptimizationProblem:
    """例題の Route Planner。forbidden / required を差し替えて色々なケースを作れる。"""
    constraints: list = []
    if forbidden:
        constraints.append(ForbiddenConstraint(severity="hard", items=forbidden))
    if required:
        constraints.append(RequiredInclusionConstraint(severity="hard", items=required))
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        constraints=constraints,
        data=RouteData(
            nodes=[RouteNode(id=n) for n in ["A", "B", "C", "D", "E"]],
            edges=list(_ROUTE_EDGES),
            start=start,
            goal=goal,
        ),
    )


def _slot(slot_id: str, day: str, start: int, end: int) -> ShiftSlot:
    return ShiftSlot(id=slot_id, day=day, start_hour=start, end_hour=end, required_headcount=1)


def build_shift_problem() -> OptimizationProblem:
    """Phase 0-2 §7.2 の例題を型として構築(解くのは Phase 5。スキーマ往復の確認用)。"""
    return OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[
            Objective(sense="minimize", target="labor_cost", weight=0.7),
            Objective(sense="maximize", target="day_off_satisfaction", weight=0.3),
        ],
        constraints=[
            StaffingConstraint(severity="hard"),
            NumericBoundConstraint(severity="hard", field="weekly_work_hours", op="<=", value=10),
        ],
        data=ShiftData(
            staff=[
                Staff(
                    id="tanaka",
                    hourly_wage=1200,
                    available_slot_ids=["s1", "s2", "s3", "s4"],
                ),
                Staff(
                    id="sato",
                    hourly_wage=1000,
                    available_slot_ids=["s1", "s2", "s3", "s4"],
                ),
                Staff(id="ito", hourly_wage=1100, available_slot_ids=["s1", "s3"]),
            ],
            slots=[
                _slot("s1", "2026-09-01", 9, 14),
                _slot("s2", "2026-09-01", 14, 19),
                _slot("s3", "2026-09-02", 9, 14),
                _slot("s4", "2026-09-02", 14, 19),
            ],
            max_weekly_hours=10,
        ),
    )
