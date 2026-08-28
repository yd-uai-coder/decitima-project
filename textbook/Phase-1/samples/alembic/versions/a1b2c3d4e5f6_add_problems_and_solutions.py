"""add problems and solutions tables

Revision ID: a1b2c3d4e5f6
Revises: 2b97c8ec8533
Create Date: 2026-08-28 00:00:00.000000

--- 写経メモ(Phase 1 / 作業単位 1-5)---
これは `uv run alembic revision --autogenerate -m "add problems and solutions tables"` の
出力を、既存 2b97c8ec8533_initial_schema.py と同じスタイルに整えたもの。
実際に自分の環境で autogenerate し、生成物がこのファイルと同等か目視確認する
(JSONB / index / FK / down_revision が意図どおりか。Phase-0-8.md §6.2)。
revision 文字列は自分の生成物の値を使う。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "2b97c8ec8533"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# payload カラムの型。Postgres では JSONB(検索・インデックス可)。
_JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "problems",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("problem_type", sa.String(length=64), nullable=False),
        sa.Column("payload", _JSONB, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_problems_user_id", "problems", ["user_id"])
    op.create_index("ix_problems_problem_type", "problems", ["problem_type"])

    op.create_table(
        "solutions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("algorithm_name", sa.String(length=64), nullable=False),
        sa.Column("algorithm_implementation", sa.String(length=64), nullable=False),
        sa.Column("payload", _JSONB, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_solutions_problem_id", "solutions", ["problem_id"])
    op.create_index("ix_solutions_algorithm_name", "solutions", ["algorithm_name"])


def downgrade() -> None:
    op.drop_index("ix_solutions_algorithm_name", table_name="solutions")
    op.drop_index("ix_solutions_problem_id", table_name="solutions")
    op.drop_table("solutions")
    op.drop_index("ix_problems_problem_type", table_name="problems")
    op.drop_index("ix_problems_user_id", table_name="problems")
    op.drop_table("problems")
