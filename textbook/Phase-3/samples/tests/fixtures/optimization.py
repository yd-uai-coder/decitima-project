"""テスト用の問題・解ビルダー。

decitima-api の pyproject は pythonpath=["."] なので `from tests.fixtures.optimization import ...`
で import できる。

- Phase 2: shift の解ビルダーと infeasible な shift 問題を追加。
- Phase 3: `build_scaled_route_problem`(seed 固定のランダム連結グラフ)を追加 ──
  オラクルのプロパティテスト(Dijkstra == BruteForce)と入力サイズ曲線に使う。
"""

from __future__ import annotations

import random

from app.domain.problems.problem import (
    ForbiddenConstraint,
    GenericConstraint,
    NumericBoundConstraint,
    Objective,
    OptimizationProblem,
    RequiredInclusionConstraint,
    StaffingConstraint,
)
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.domain.solutions.solution import (
    AlgorithmMeta,
    CandidateSolution,
    SolutionStatus,
)

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
    max_total_weight: float | None = None,
    start: str = "A",
    goal: str = "E",
) -> OptimizationProblem:
    """例題の Route Planner。制約を差し替えて色々なケースを作れる。"""
    constraints: list = []
    if forbidden:
        constraints.append(ForbiddenConstraint(severity="hard", items=forbidden))
    if required:
        constraints.append(RequiredInclusionConstraint(severity="hard", items=required))
    if max_total_weight is not None:
        # Dijkstra はこの上限を無視して最短路を出す → Verification が invalid にする(Phase-2-6)
        constraints.append(
            NumericBoundConstraint(
                severity="hard", field="total_weight", operator="<=", value=max_total_weight
            )
        )
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


def build_scaled_route_problem(n: int, *, seed: int = 0) -> OptimizationProblem:
    """seed 固定のランダムな連結グラフ。start = 先頭ノード, goal = 末尾ノード。

    連鎖 n0-n1-...-n(n-1) を必ず張って連結性を保証し、ランダムな横エッジを n//2 本足す。
    n を振れば入力サイズ別カーブ、seed を振ればオラクルのプロパティテストに使える。
    """
    if n < 2:
        raise ValueError(f"n must be >= 2, got {n}")
    rng = random.Random(seed)
    ids = [f"n{i}" for i in range(n)]
    edges: list[RouteEdge] = []
    # 連鎖(連結性の保証)
    for i in range(n - 1):
        w = float(rng.randint(1, 9))
        edges.append(RouteEdge(id=f"e{i}_{i + 1}", source=ids[i], target=ids[i + 1], weight=w))
    # 追加の横エッジ
    for k in range(n // 2):
        a, b = rng.sample(range(n), 2)
        w = float(rng.randint(1, 9))
        edges.append(RouteEdge(id=f"x{k}_{a}_{b}", source=ids[a], target=ids[b], weight=w))
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id=i) for i in ids], edges=edges, start=ids[0], goal=ids[-1]
        ),
    )


def _slot(slot_id: str, day: str, start: int, end: int, headcount: int = 1) -> ShiftSlot:
    return ShiftSlot(
        id=slot_id, day=day, start_hour=start, end_hour=end, required_headcount=headcount
    )


def build_shift_problem(*, with_days_off_penalty: bool = False) -> OptimizationProblem:
    """Phase 0-2 §7.2 の例題。4 スロット × 各 required_headcount=1。

    有効解の一例: {s1:[tanaka], s2:[sato], s3:[ito], s4:[tanaka]}
      - tanaka は s4(2026-09-02)を希望休にしている → soft 違反
    """
    constraints: list = [StaffingConstraint(severity="hard")]
    if with_days_off_penalty:
        constraints.append(GenericConstraint(kind="respect_days_off", severity="soft", penalty=5.0))
    return OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[
            Objective(sense="minimize", target="labor_cost", weight=0.7),
            Objective(sense="maximize", target="day_off_satisfaction", weight=0.3),
        ],
        constraints=constraints,
        data=ShiftData(
            staff=[
                Staff(
                    id="tanaka",
                    hourly_wage=1200,
                    available_slot_ids=["s1", "s2", "s3", "s4"],
                    requested_days_off=["2026-09-02"],
                ),
                Staff(id="sato", hourly_wage=1000, available_slot_ids=["s1", "s2", "s3", "s4"]),
                Staff(id="ito", hourly_wage=1100, available_slot_ids=["s1", "s3"]),
            ],
            slots=[
                _slot("s1", "2026-09-01", 9, 14),
                _slot("s2", "2026-09-01", 14, 19),
                _slot("s3", "2026-09-02", 9, 14),
                _slot("s4", "2026-09-02", 14, 19),
            ],
            max_weekly_hours=20,
            max_consecutive_days=5,
        ),
    )


def build_infeasible_shift_problem() -> OptimizationProblem:
    """s1 が 2 人必要なのに s1 に入れるスタッフが 1 人だけ ── Semantic Validation で弾かれる。"""
    return OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[Objective(sense="minimize", target="labor_cost")],
        constraints=[StaffingConstraint(severity="hard")],
        data=ShiftData(
            staff=[Staff(id="only", hourly_wage=1000, available_slot_ids=["s1"])],
            slots=[_slot("s1", "2026-09-01", 9, 14, headcount=2)],
        ),
    )


def build_shift_solution(
    assignments: dict[str, list[str]], *, status: SolutionStatus = "valid"
) -> CandidateSolution:
    """手組みの ShiftSolution を CandidateSolution に包む(shift を解く strategy は Phase 5)。"""
    return CandidateSolution(
        status=status,
        assignments=ShiftSolution(assignments=assignments),
        produced_by=AlgorithmMeta(name="manual", family="scheduling", implementation="fixture"),
    )
