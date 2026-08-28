"""解の表現パッケージ。公開窓口(re-export + __all__)。設計は Phase-0-2.md §6 / §2.5。"""

from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.domain.solutions.solution import (
    AlgorithmFamily,
    AlgorithmMeta,
    CandidateSolution,
    ConstraintViolation,
    SolutionData,
    SolutionStatus,
)

__all__ = [
    "AlgorithmFamily",
    "AlgorithmMeta",
    "CandidateSolution",
    "ConstraintViolation",
    "RouteSolution",
    "ShiftSolution",
    "SolutionData",
    "SolutionStatus",
]
