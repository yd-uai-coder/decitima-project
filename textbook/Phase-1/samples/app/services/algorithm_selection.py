"""アルゴリズム選択(サービス層)。

registry.find_strategy(純粋)を呼び、該当が無ければ NoAlgorithmError(AppError 派生 →
HTTP 400)を送出する。純粋な registry 層に AppError を持ち込まないための薄いラッパー
(Phase-0-3.md §2.2 の依存方向 / Phase-0-4.md §6)。
"""

from __future__ import annotations

from app.algorithms.base import AlgorithmStrategy
from app.algorithms.registry import find_strategy
from app.domain.problems.problem import OptimizationProblem
from app.services.errors import NoAlgorithmError


def select_strategy(
    problem: OptimizationProblem, requested: str | None = None
) -> AlgorithmStrategy:
    """problem に適用するアルゴリズムを1つ選ぶ。無ければ NoAlgorithmError。"""
    strategy = find_strategy(problem, requested)
    if strategy is None:
        if requested is not None:
            raise NoAlgorithmError(
                f"algorithm {requested!r} is not registered for {problem.problem_type!r}"
            )
        raise NoAlgorithmError(f"no algorithm registered for {problem.problem_type!r}")
    return strategy
