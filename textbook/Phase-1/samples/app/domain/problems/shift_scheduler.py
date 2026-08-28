"""Shift Scheduler の問題固有データ(葉モジュール)。

Phase 1 ではこのスキーマの型だけを用意する。シフトを解くアルゴリズム(Greedy /
Backtracking)と shift 用の Validation / Verification は Phase 5。設計は Phase-0-2.md §5.2。
このファイルは兄弟モジュール(route_planner.py)を import しない。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Staff(BaseModel):
    """シフト問題のスタッフ1人。時給・スキル・勤務可能スロット・希望休。"""

    id: str
    name: str | None = None
    hourly_wage: float = Field(ge=0)
    skills: list[str] = Field(default_factory=list)
    available_slot_ids: list[str] = Field(default_factory=list)  # 勤務可能なスロット id
    requested_days_off: list[str] = Field(default_factory=list)  # 希望休の日付(soft 制約と連動)


class ShiftSlot(BaseModel):
    """シフト問題の勤務スロット1つ。日付・時間帯・必要人数・必要スキル。"""

    id: str
    day: str  # "2026-09-01" など
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    required_headcount: int = Field(ge=1)
    required_skills: list[str] = Field(default_factory=list)


class ShiftData(BaseModel):
    """Shift Scheduler の問題固有データ。スタッフ・スロット・全体上限。"""

    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    staff: list[Staff]
    slots: list[ShiftSlot]
    max_weekly_hours: float = 40
    max_consecutive_days: int = 5
