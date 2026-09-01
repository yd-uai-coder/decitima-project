"""制約 kind ごとのチェッカー関数と、その公開レジストリ。

SolutionVerificationService(app/services/verification.py)は制約の `kind` を見て
ここへディスパッチする。制約の「型」(ConstraintBase とサブタイプ)は
app/domain/problems/problem.py 側にあり、ここは「その kind をどう検証するか」の
ロジックだけを持つ。app/algorithms/registry.py と同じ『機構のレジストリ』。
設計は Phase-0-6.md §3 / Phase-0-2.md §4.5。

新しい制約 kind を足すとき ── サブタイプを problem.py に定義し、チェッカーをここに1ファイル
追加し、CHECKERS に1エントリ足すだけ(既存のアルゴリズム・サービスには触れない)。
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.constraints.forbidden import check_forbidden
from app.domain.constraints.numeric_bound import check_numeric_bound
from app.domain.constraints.required_inclusion import check_required_inclusion
from app.domain.constraints.staffing import check_staffing
from app.domain.solutions.solution import ConstraintViolation

# チェッカーの共通シグネチャ: (制約, 問題, 検証中の解) -> 違反1件 or None。
# 第1引数の具体型は kind ごとに異なる(ForbiddenConstraint 等)ので ... で受ける
# (Phase 1 の _Checker と同じ割り切り)。
type ConstraintChecker = Callable[..., ConstraintViolation | None]

# kind -> チェッカー。verification.py はこの dict だけを見る
CHECKERS: dict[str, ConstraintChecker] = {
    "forbidden": check_forbidden,
    "required_inclusion": check_required_inclusion,
    "numeric_bound": check_numeric_bound,
    "staffing": check_staffing,
}

__all__ = [
    "CHECKERS",
    "ConstraintChecker",
    "check_forbidden",
    "check_numeric_bound",
    "check_required_inclusion",
    "check_staffing",
]
