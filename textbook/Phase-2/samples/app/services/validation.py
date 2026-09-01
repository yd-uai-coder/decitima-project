"""ProblemValidationService ── 問題定義の妥当性(Algorithm Engine に渡す前)。

設計は Phase-0-6.md §2。Phase 2 で route 限定から全 problem_type へ一般化した。

- Input Validation(型・単項の値域・フィールド間)は Pydantic が担う
  (app/domain/problems/ の Field / field_validator / model_validator)。
- Semantic Validation で「純粋な構造述語」(start が nodes にあるか 等)は problem_type
  ごとの検査関数を app/domain/problems/semantic.py の SEMANTIC_CHECKS レジストリに集約。
- 「到達可能性」は述語ではなく **グラフ計算**(BFS を走らせる)。計算そのものは
  app/algorithms/graph/reachability.py の route_reachable、このサービスはそれを呼んで
  hard ゲートとして判定するだけ(計算 = algorithms / 判定 = services。domain は不関与)。
- このサービスは「純粋述語のレジストリを回す」+「計算プリミティブを呼んで判定する」の
  オーケストレーションに徹する。

整合性の欠陥 → ProblemValidationError(400)。原理的に解が無い → InfeasibleProblemError(400)。
「明らかに無理」だけを弾き、グレーゾーンは通す(Phase-0-6.md §2.4)。
"""

from __future__ import annotations

from app.algorithms.graph.reachability import route_reachable
from app.domain.problems.problem import ForbiddenConstraint, OptimizationProblem
from app.domain.problems.route_planner import RouteData
from app.domain.problems.semantic import SEMANTIC_CHECKS
from app.services.errors import InfeasibleProblemError, ProblemValidationError


class ProblemValidationService:
    """OptimizationProblem がアルゴリズムに渡せる状態か、問題全体を見て検査する。"""

    def validate(self, problem: OptimizationProblem) -> None:
        """検査に通れば None。整合性 NG は ProblemValidationError、
        実行不可能は InfeasibleProblemError を送出する。"""
        issues = [
            issue
            for check in SEMANTIC_CHECKS.get(problem.problem_type, [])
            for issue in check(problem)
        ]

        # 整合性の欠陥が1件でもあれば、そちらを優先して弾く(到達可能性の判定は
        # 端点が実在してこそ意味を持つため)
        integrity = [i.message for i in issues if not i.infeasible]
        if integrity:
            raise ProblemValidationError("; ".join(integrity))

        infeasible = [i.message for i in issues if i.infeasible]
        if isinstance(problem.data, RouteData):
            # 到達可能性は「計算」── route_reachable(algorithms)に任せ、ここは判定だけ
            forbidden = {
                item
                for c in problem.constraints
                if isinstance(c, ForbiddenConstraint)
                for item in c.items
            }
            if not route_reachable(problem.data, forbidden):
                infeasible.append(
                    f"goal {problem.data.goal!r} is unreachable from {problem.data.start!r} "
                    f"after removing {len(forbidden)} forbidden edge(s)"
                )
        if infeasible:
            raise InfeasibleProblemError("; ".join(infeasible))
