# DeciTima samples │ Phase 9
"""作業単位 9-8: jobs API のリクエスト・レスポンススキーマ。

ジョブ投入のリクエストは `schemas/optimization.py::SolveRequest` をそのまま再利用する
(problem / algorithm / persist / timeout_seconds ── 同期 solve と同じ入力形)。新規に
定義するのはレスポンス(投入直後のステータス、ポーリング結果)だけ。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.solutions.solution import CandidateSolution


class JobSubmitResponse(BaseModel):
    """POST /jobs のレスポンス。202 Accepted とともに返す(結果は GET /jobs/{id} でポーリング)。"""

    job_id: uuid.UUID
    status: str  # 投入直後は常に "queued"


class JobStatusResponse(BaseModel):
    """GET /jobs/{id} のレスポンス。status に応じて result / error のどちらかが埋まる。"""

    job_id: uuid.UUID
    problem_type: str
    status: str  # "queued" | "running" | "succeeded" | "failed"
    result: CandidateSolution | None = None  # succeeded のときだけ入る
    problem_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
    error: str | None = None  # failed のときだけ入る
    created_at: datetime
    updated_at: datetime
