"""Problem / Solution の ORM モデル。設計は Phase-0-8.md §3 / §4。

方針: JSONB 中心 + 検索・集計に使うキーだけカラム化。problem_type を1つ足しても
マイグレーション不要。既存 app/models/conversation.py のパターン(uuid PK / tz 付き
created_at / Mapped + mapped_column)を踏襲する。
"""

# [以降 Phase で修正予定 ── Phase 3-3] このファイルの現行版はこのまま(スナップショット)。
# Phase 3-3 で BenchmarkRun(benchmark_runs テーブル)を追加する。
# 現行版 textbook/Phase-3/samples/app/models/optimization.py。

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Postgres では JSONB、それ以外(SQLite のユニットテスト)では汎用 JSON にフォールバック。
# JSONB は読み出しが速く、-> / ->> / @> で部分検索・インデックスができる(将来対応)。
JsonB = JSON().with_variant(JSONB(), "postgresql")


class Problem(Base):
    """投入された OptimizationProblem 1件。payload に問題定義の全体を持つ。"""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # problem_type: 検索・集計に使うので JSON からカラムへ切り出す
    problem_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # payload: OptimizationProblem.model_dump(mode="json") の全体
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    solutions: Mapped[list["Solution"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )


class Solution(Base):
    """あるアルゴリズムが Problem に対して出した検証済みの CandidateSolution 1件。"""

    __tablename__ = "solutions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # status / algorithm_* は比較 UI とベンチで頻繁に絞り込むのでカラム化
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    algorithm_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    algorithm_implementation: Mapped[str] = mapped_column(String(64), nullable=False)
    # payload: CandidateSolution.model_dump(mode="json") の全体(metrics / violations 含む)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem: Mapped["Problem"] = relationship(back_populates="solutions")
