"""Phase 0-2 の検証: Shift Scheduler を共通スキーマで書き下す。

「3 人のスタッフを 2 日 × 2 スロットに割り当てる。各スロット 1 人必要。
週 10 時間まで。田中さんは 9/2 が希望休。人件費は最小化したい。」

多目的（人件費最小化 + 希望休充足最大化）と hard/soft 混在の制約が
共通スキーマで表現できることを確認する。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from problem_schema import (  # noqa: E402
    AlgorithmMeta,
    CandidateSolution,
    GenericConstraint,
    NumericBoundConstraint,
    Objective,
    OptimizationProblem,
    ShiftData,
    ShiftSlot,
    ShiftSolution,
    Staff,
    StaffingConstraint,
)

SLOT_HOURS = 5  # 各スロットは 5 時間（9-14 / 14-19）


def build_problem() -> OptimizationProblem:
    """例題の Shift Scheduler を OptimizationProblem として構築する。"""
    return OptimizationProblem(
        problem_type="shift_scheduling",
        objectives=[
            Objective(sense="minimize", target="labor_cost", weight=0.7),
            Objective(sense="maximize", target="day_off_satisfaction", weight=0.3),
        ],
        constraints=[
            StaffingConstraint(severity="hard"),
            NumericBoundConstraint(
                severity="hard", field="weekly_work_hours", op="<=", value=10
            ),
            # 希望休は soft。専用サブタイプを作らず GenericConstraint で表す
            GenericConstraint(kind="respect_days_off", severity="soft", penalty=5.0),
        ],
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
                ShiftSlot(id="s1", day="2026-09-01", start_hour=9, end_hour=14, required_headcount=1),
                ShiftSlot(id="s2", day="2026-09-01", start_hour=14, end_hour=19, required_headcount=1),
                ShiftSlot(id="s3", day="2026-09-02", start_hour=9, end_hour=14, required_headcount=1),
                ShiftSlot(id="s4", day="2026-09-02", start_hour=14, end_hour=19, required_headcount=1),
            ],
            max_weekly_hours=10,
        ),
    )


def expected_solution() -> CandidateSolution:
    """このアルゴリズムが返すべき解（Phase 5 のバックトラッキング実装の期待値）。"""
    # s1=ito, s2=sato, s3=sato, s4=tanaka
    assignments = {"s1": ["ito"], "s2": ["sato"], "s3": ["sato"], "s4": ["tanaka"]}
    return CandidateSolution(
        status="valid",
        assignments=ShiftSolution(assignments=assignments),
        metrics={"labor_cost": 21500.0, "day_off_satisfaction": 1.0, "soft_penalty": 0.0},
        violations=[],
        produced_by=AlgorithmMeta(
            name="backtracking", family="scheduling", implementation="handwritten"
        ),
    )


def _labor_cost(problem: OptimizationProblem, solution: CandidateSolution) -> float:
    """割当表から人件費（時給 × スロット時間の合計）を計算する。"""
    # discriminated union は消費側で isinstance で絞り込む
    assert isinstance(problem.data, ShiftData)
    assert isinstance(solution.assignments, ShiftSolution)
    wage = {s.id: s.hourly_wage for s in problem.data.staff}
    total = 0.0
    # 各スロットの割当スタッフぶんの人件費を積む
    for staff_ids in solution.assignments.assignments.values():
        for sid in staff_ids:
            total += wage[sid] * SLOT_HOURS
    return total


if __name__ == "__main__":
    problem = build_problem()
    solution = expected_solution()

    assert isinstance(problem.data, ShiftData)
    assert isinstance(solution.assignments, ShiftSolution)
    assert problem.problem_type == problem.data.problem_type
    assert solution.assignments.problem_type == "shift_scheduling"

    # 必要人数（hard）を満たしているか
    for slot in problem.data.slots:
        assigned = solution.assignments.assignments[slot.id]
        assert len(assigned) == slot.required_headcount, slot.id

    # metrics の labor_cost が割当表と整合しているか
    computed = _labor_cost(problem, solution)
    assert computed == solution.metrics["labor_cost"], (computed, solution.metrics["labor_cost"])

    print("shift_scheduler_example OK: labor_cost =", computed,
          "/ day_off_satisfaction =", solution.metrics["day_off_satisfaction"])
