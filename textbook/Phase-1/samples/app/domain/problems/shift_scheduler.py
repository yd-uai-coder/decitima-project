"""Shift Scheduler の問題固有データ(葉モジュール)。

Phase 1 ではこのスキーマの型だけを用意する。シフトを解くアルゴリズム(Greedy /
Backtracking)と shift 用の Validation / Verification は Phase 5。設計は Phase-0-2.md §5.2。
このファイルは兄弟モジュール(route_planner.py)を import しない。
"""

# [以降 Phase で修正予定 ── Phase 2-1] このファイルの Phase 1 版はこのまま(スナップショット)。
# Phase 2-1 で: ShiftSlot に end_hour > start_hour の model_validator と day の ISO 日付
# field_validator、ShiftData に slot/staff id 重複を弾く model_validator を追加。
# 解決される問題: フィールド間・コレクションの不整合な入力が Semantic Validation /
# Verification まで素通りしていた。
# 現行版 textbook/Phase-2/samples/app/domain/problems/shift_scheduler.py。詳細 Phase-2-1.md。

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
