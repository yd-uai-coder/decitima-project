"""Shift Scheduler の解(葉モジュール)。型のみ。解を作るのは Phase 6。設計は Phase-0-2.md §6。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ShiftSolution(BaseModel):
    """Shift Scheduler の解。スロット id ごとに割り当てたスタッフ id のリスト。"""

    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    assignments: dict[str, list[str]]  # slot_id -> [staff_id, ...]
