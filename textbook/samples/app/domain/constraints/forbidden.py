# DeciTima samples │ 初出 Phase 2 │ 改訂 Phase 5,7
"""forbidden 制約のチェッカー ── 解に「使ってはいけない要素」が含まれていないか。

Phase 5-3 で network_design、7-3 で travel_planning に対応。「使った要素」の意味は解型で変わる:
  - route 解   … 使ったエッジ id
  - network 解 … 選択したリンク id
  - travel 解  … 訪れた place id

Phase 7-3: 解 → 要素 id 集合の抽出を required_inclusion と共有する
`constraints/elements.py::solution_element_ids` に一本化した(進行のルール #17)。
"""

from __future__ import annotations

from app.domain.constraints.elements import solution_element_ids  # (Phase 7-3) 重複ヘルパを共通化
from app.domain.problems.problem import ForbiddenConstraint, OptimizationProblem
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation


def check_forbidden(
    constraint: ForbiddenConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解が禁止要素(禁止エッジ / 使えないリンク id 等)を含んでいれば違反を1件返す。"""
    # forbidden は「使った接続」を対象にするので route 解では edge を見る
    used = solution_element_ids(solution, aspect="edges")
    if used is None:
        return None  # この解型には forbidden を適用しない(素通し)
    hit = used & set(constraint.items)
    if not hit:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"solution uses forbidden element(s): {sorted(hit)}",
        detail={"forbidden_hit": sorted(hit)},
    )
