"""ProblemValidationService ── 問題定義の妥当性(Algorithm Engine に渡す前)。

設計は Phase-0-6.md §2。Phase 2 で route 限定から全 problem_type へ一般化した。

- Input Validation(型・単項の値域・フィールド間)は Pydantic が担う
  (app/domain/problems/ の Field / field_validator / model_validator)。
- Semantic Validation(問題全体の整合・実行可能性)は problem_type ごとの検査関数を
  app/domain/problems/semantic.py の SEMANTIC_CHECKS レジストリに集約。このサービスは
  レジストリを回すだけ。
- 例外: route の「到達可能性」だけは graph アルゴリズム(app/algorithms/)を使うため、
  domain → algorithms の逆流(Phase-0-3.md §2.2)を避けてここに置く。

整合性の欠陥 → ProblemValidationError(400)。原理的に解が無い → InfeasibleProblemError(400)。
「明らかに無理」だけを弾き、グレーゾーンは通す(Phase-0-6.md §2.4)。
"""

from __future__ import annotations

from app.algorithms.graph.dijkstra import build_adjacency
from app.algorithms.search.bfs import reachable_nodes
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
            infeasible += self._route_unreachable(problem, problem.data)
        if infeasible:
            raise InfeasibleProblemError("; ".join(infeasible))

    def _route_unreachable(self, problem: OptimizationProblem, data: RouteData) -> list[str]:
        """禁止エッジを除いたグラフで start から goal に到達できなければメッセージを返す。"""
        forbidden = {
            item
            for c in problem.constraints
            if isinstance(c, ForbiddenConstraint)
            for item in c.items
        }
        adjacency = build_adjacency(data, forbidden)
        plain = {node: [nxt for nxt, _e, _w in edges] for node, edges in adjacency.items()}
        if data.goal in reachable_nodes(plain, data.start):
            return []
        return [
            f"goal {data.goal!r} is unreachable from {data.start!r} "
            f"after removing {len(forbidden)} forbidden edge(s)"
        ]
