"""テスト用の問題・解ビルダー。

decitima-api の pyproject は pythonpath=["."] なので `from tests.fixtures.optimization import ...`
で import できる。

Phase 4 追加(route):
  - build_scaled_route_problem に `density`(横エッジの本数を振れる。既定は Phase 3 と同じ挙動)
  - build_negative_route_problem … 有向 + 負辺(Bellman-Ford 用。無向だと負辺は即・負閉路)
  - build_negative_cycle_route_problem … 有向の負閉路
  - build_coord_route_problem … 座標つき(A* のヒューリスティック用)
Phase 5 追加(network):
  - build_network_problem / build_network_solution … network_design(MST)
  - build_disconnected_network_problem … 孤立ノードあり(infeasible 用)
"""

from __future__ import annotations

import random

from app.domain.problems.network_design import (
    NetworkDesignData,
    NetworkLink,
    NetworkNode,
)
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
from app.domain.solutions.network_design import NetworkDesignSolution
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
        constraints.append(
            NumericBoundConstraint(
                severity="hard",
                field="total_weight",
                operator="<=",
                value=max_total_weight,
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


def build_negative_route_problem() -> OptimizationProblem:
    """有向グラフ + 負辺(負閉路は無し)。S->A->B->T の負辺経路が S->T 直行より短い。

    直行 S->T = 5、S->A(2) + A->B(-4) + B->T(3) = 1。Dijkstra は S->T を settle して
    誤答するので、Bellman-Ford の出番。allow_negative=True。
    """
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id=n) for n in ["S", "A", "B", "T"]],
            edges=[
                RouteEdge(id="s_t", source="S", target="T", weight=5, directed=True),
                RouteEdge(id="s_a", source="S", target="A", weight=2, directed=True),
                RouteEdge(id="a_b", source="A", target="B", weight=-4, directed=True),
                RouteEdge(id="b_t", source="B", target="T", weight=3, directed=True),
            ],
            start="S",
            goal="T",
            allow_negative=True,
        ),
    )


def build_negative_cycle_route_problem() -> OptimizationProblem:
    """有向の負閉路(A->B->C->A の和が負)。start から到達でき、最短経路は定義できない。"""
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id=n) for n in ["S", "A", "B", "C", "T"]],
            edges=[
                RouteEdge(id="s_a", source="S", target="A", weight=1, directed=True),
                RouteEdge(id="a_b", source="A", target="B", weight=1, directed=True),
                RouteEdge(id="b_c", source="B", target="C", weight=-1, directed=True),
                RouteEdge(id="c_a", source="C", target="A", weight=-2, directed=True),
                RouteEdge(id="b_t", source="B", target="T", weight=1, directed=True),
            ],
            start="S",
            goal="T",
            allow_negative=True,
        ),
    )


def build_coord_route_problem(*, required: list[str] | None = None) -> OptimizationProblem:
    """座標つきグラフ。weight は両端の直線距離なので euclidean ヒューリスティックは可容。

    直線ハイウェイ P0(x=0)..P6(x=6) に、goal と逆方向(x<0)へ伸びる寄り道クラスタ D0..D3 を
    P1 からぶら下げる。Dijkstra は g が小さい D ノードも settle するが、A* は h(Dk, goal) が
    大きいので P チェーンを先に伸ばして goal に着き、D を pop しない ── `_ops` が下がる。
    """
    nodes = [RouteNode(id=f"P{i}", x=float(i), y=0.0) for i in range(7)]
    edges = [
        RouteEdge(id=f"p{i}", source=f"P{i}", target=f"P{i + 1}", weight=1.0) for i in range(6)
    ]
    for k in range(4):
        nodes.append(RouteNode(id=f"D{k}", x=-1.0 - k, y=0.0))
        src = "P1" if k == 0 else f"D{k - 1}"
        edges.append(RouteEdge(id=f"d{k}", source=src, target=f"D{k}", weight=1.0))

    constraints: list = []
    if required:
        constraints.append(RequiredInclusionConstraint(severity="hard", items=required))
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        constraints=constraints,
        data=RouteData(nodes=nodes, edges=edges, start="P0", goal="P6"),
    )


def build_scaled_route_problem(
    n: int, *, seed: int = 0, density: float = 0.5
) -> OptimizationProblem:
    """seed 固定のランダムな連結グラフ。start = 先頭ノード, goal = 末尾ノード。

    連鎖 n0-n1-...-n(n-1) を必ず張って連結性を保証し、ランダムな横エッジを int(n*density) 本足す。
    density=0.5(既定)なら Phase 3 と同じ本数(n//2)。密度を上げると経路の選択肢が増える。
    """
    if n < 2:
        raise ValueError(f"n must be >= 2, got {n}")
    rng = random.Random(seed)
    ids = [f"n{i}" for i in range(n)]
    edges: list[RouteEdge] = []
    for i in range(n - 1):
        w = float(rng.randint(1, 9))
        edges.append(RouteEdge(id=f"e{i}_{i + 1}", source=ids[i], target=ids[i + 1], weight=w))
    for k in range(int(n * density)):
        a, b = rng.sample(range(n), 2)
        w = float(rng.randint(1, 9))
        edges.append(RouteEdge(id=f"x{k}_{a}_{b}", source=ids[a], target=ids[b], weight=w))
    return OptimizationProblem(
        problem_type="route_planning",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=RouteData(
            nodes=[RouteNode(id=i) for i in ids],
            edges=edges,
            start=ids[0],
            goal=ids[-1],
        ),
    )


# ---------------------------------------------------------------------------
# network_design(MST)
# ---------------------------------------------------------------------------

# 5 拠点。既知の MST: L_ab(1) + L_bc(2) + L_cd(3) + L_be(4) = 10
_NETWORK_LINKS = [
    NetworkLink(id="L_ab", endpoints=("A", "B"), weight=1),
    NetworkLink(id="L_bc", endpoints=("B", "C"), weight=2),
    NetworkLink(id="L_cd", endpoints=("C", "D"), weight=3),
    NetworkLink(id="L_be", endpoints=("B", "E"), weight=4),
    NetworkLink(id="L_ac", endpoints=("A", "C"), weight=5),
    NetworkLink(id="L_de", endpoints=("D", "E"), weight=6),
    NetworkLink(id="L_ae", endpoints=("A", "E"), weight=7),
]


def build_network_problem(
    *,
    forbidden: list[str] | None = None,
    required: list[str] | None = None,
    max_total_weight: float | None = None,
) -> OptimizationProblem:
    """例題の Network Designer。MST の総コストは 10。"""
    constraints: list = []
    if forbidden:
        constraints.append(ForbiddenConstraint(severity="hard", items=forbidden))
    if required:
        constraints.append(RequiredInclusionConstraint(severity="hard", items=required))
    if max_total_weight is not None:
        constraints.append(
            NumericBoundConstraint(
                severity="hard",
                field="total_weight",
                operator="<=",
                value=max_total_weight,
            )
        )
    return OptimizationProblem(
        problem_type="network_design",
        objectives=[Objective(sense="minimize", target="total_weight")],
        constraints=constraints,
        data=NetworkDesignData(
            nodes=[NetworkNode(id=n) for n in ["A", "B", "C", "D", "E"]],
            links=list(_NETWORK_LINKS),
        ),
    )


def build_disconnected_network_problem() -> OptimizationProblem:
    """拠点 C が孤立 ── どのリンクも C に繋がらないので全域木は作れない(infeasible)。"""
    return OptimizationProblem(
        problem_type="network_design",
        objectives=[Objective(sense="minimize", target="total_weight")],
        data=NetworkDesignData(
            nodes=[NetworkNode(id=n) for n in ["A", "B", "C"]],
            links=[NetworkLink(id="L_ab", endpoints=("A", "B"), weight=1)],
        ),
    )


def build_network_solution(
    selected_link_ids: list[str],
    total_weight: float,
    *,
    status: SolutionStatus = "valid",
) -> CandidateSolution:
    """手組みの NetworkDesignSolution を CandidateSolution に包む。"""
    return CandidateSolution(
        status=status,
        assignments=NetworkDesignSolution(
            selected_link_ids=selected_link_ids, total_weight=total_weight
        ),
        produced_by=AlgorithmMeta(name="manual", family="graph", implementation="fixture"),
    )


def _slot(slot_id: str, day: str, start: int, end: int, headcount: int = 1) -> ShiftSlot:
    return ShiftSlot(
        id=slot_id,
        day=day,
        start_hour=start,
        end_hour=end,
        required_headcount=headcount,
    )


def build_shift_problem(*, with_days_off_penalty: bool = False) -> OptimizationProblem:
    """Phase 0-2 §7.2 の例題。4 スロット × 各 required_headcount=1。"""
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
    """手組みの ShiftSolution を CandidateSolution に包む(shift を解く strategy は Phase 6)。"""
    return CandidateSolution(
        status=status,
        assignments=ShiftSolution(assignments=assignments),
        produced_by=AlgorithmMeta(name="manual", family="scheduling", implementation="fixture"),
    )
