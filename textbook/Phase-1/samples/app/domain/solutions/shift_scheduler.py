"""Shift Scheduler の解(葉モジュール)。型のみ。解を作るのは Phase 6。設計は Phase-0-2.md §6。"""

# [以降 Phase で修正予定 ── Phase 6-1] この Phase 1 版はこのまま(スナップショット)。
# Phase 6-1 で `type Assignment = dict[str, list[str]]` エイリアスを追加し
# `assignments: Assignment` に変える(共有語彙 ── shift を解く algorithms と検証する domain の
# 両レイヤーが循環なしで import できる唯一の家がこの葉。挙動不変)。
# 現行版 textbook/Phase-6/samples/app/domain/solutions/shift_scheduler.py。

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ShiftSolution(BaseModel):
    """Shift Scheduler の解。スロット id ごとに割り当てたスタッフ id のリスト。"""

    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    assignments: dict[str, list[str]]  # slot_id -> [staff_id, ...]
