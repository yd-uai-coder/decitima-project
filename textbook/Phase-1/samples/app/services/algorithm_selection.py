"""アルゴリズム選択(サービス層)。

registry.find_strategy(純粋)を呼び、該当が無ければ NoAlgorithmError(AppError 派生 →
HTTP 400)を送出する。純粋な registry 層に AppError を持ち込まないための薄いラッパー
(Phase-0-3.md §2.2 の依存方向 / Phase-0-4.md §6)。
"""

# [以降 Phase で修正予定 ── Phase 4-5] このファイルの現行版はこのまま(スナップショット)。
# Phase 4-5 で select_strategy を rule-based に(負辺→bellman_ford / 全ノード座標→a_star / network_design→kruskal / 既定→dijkstra)。
# 現行版 textbook/Phase-4/samples/app/services/algorithm_selection.py。

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
