"""solve / algorithms / solutions API のリクエスト・レスポンススキーマ。

設計は Phase-0-7.md §3。app/domain/ のモデルを import して薄く包む
(HTTP 境界の型 = schemas、システム内部の共通言語 = domain。Phase-0-3.md §2.4)。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.problems.problem import OptimizationProblem
from app.domain.solutions.solution import CandidateSolution


class SolveRequest(BaseModel):
    """solve API のリクエスト。構造化済みの問題と、任意のアルゴリズム指定。"""

    problem: OptimizationProblem  # domain のモデルをそのまま受ける
    algorithm: str | None = None  # 指定なければ rule-based 選択
    persist: bool = True  # False なら結果を保存しない(教材の試行用)
    timeout_seconds: float | None = Field(default=None, gt=0)  # 上限は settings で制限


class SolveResponse(BaseModel):
    """solve API のレスポンス。検証済みの解と、永続化された場合の ID。"""

    solution: CandidateSolution
    problem_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None


class AlgorithmInfo(BaseModel):
    """registry に登録された 1 アルゴリズムの公開情報。"""

    name: str
    family: str
    implementation: str
    problem_types: list[str]  # この (name, implementation) が登録されている problem_type
    time_complexity: str | None = None


class AlgorithmListResponse(BaseModel):
    algorithms: list[AlgorithmInfo]


class SolutionRead(BaseModel):
    """永続化された解 1 件の読み出し。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    problem_id: uuid.UUID
    status: str
    algorithm_name: str
    algorithm_implementation: str
    created_at: datetime
    payload: dict  # CandidateSolution.model_dump(mode="json") の全体


class ProblemRead(BaseModel):
    """永続化された問題 1 件の読み出し。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    problem_type: str
    created_at: datetime
    payload: dict  # OptimizationProblem.model_dump(mode="json") の全体
