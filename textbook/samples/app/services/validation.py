# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 2,5
"""ProblemValidationService ── 問題定義の妥当性(Algorithm Engine に渡す前)。

- Input Validation(型・値域)は Pydantic の Field 制約 / model_validator が担う
  (route_planner.py の allow_negative ガード等)。
- Semantic Validation(問題全体の整合・実行可能性)は problem_type ごとの検査関数を
  app/domain/problems/semantic.py の SEMANTIC_CHECKS レジストリに集約。このサービスは
  レジストリを回すだけ。
- 例外: 「計算」が要る実行可能性チェックは graph アルゴリズム(app/algorithms/)を使うため
  domain → algorithms の逆流(Phase-0-3.md §2.2)を避けてここに置く:
    - route の到達可能性        route_reachable
    - network の全拠点連結性     all_nodes_connected(Phase 5-3)

整合性の欠陥 → ProblemValidationError(400)。原理的に解が無い → InfeasibleProblemError(400)。
原則: 「明らかに無理」だけを弾き、グレーゾーンは通す。
"""

from __future__ import annotations

from app.algorithms.graph.adjacency import build_link_adjacency
from app.algorithms.graph.connectivity import all_nodes_connected
from app.algorithms.graph.reachability import route_reachable
from app.domain.problems.network_design import NetworkDesignData
from app.domain.problems.problem import ForbiddenConstraint, OptimizationProblem
from app.domain.problems.route_planner import RouteData
from app.domain.problems.semantic import SEMANTIC_CHECKS
from app.services.errors import InfeasibleProblemError, ProblemValidationError


class ProblemValidationService:
    """OptimizationProblem がアルゴリズムに渡せる状態か、問題全体を見て検査する。"""

    def validate(self, problem: OptimizationProblem) -> None:
        """検査に通れば None。

        整合性 NG は ProblemValidationError、実行不能は InfeasibleProblemError。
        原則: 「明らかに無理」だけを弾き、グレーゾーンは通す。
        """
        issues = [
            issue
            for check in SEMANTIC_CHECKS.get(problem.problem_type, [])
            for issue in check(problem)
        ]

        # 整合性の欠陥が1件でもあれば、そちらを優先して弾く
        # (到達可能性 / 連結性の判定は端点が実在してこそ意味を持つため)
        integrity = [i.message for i in issues if not i.infeasible]
        if integrity:
            raise ProblemValidationError("; ".join(integrity))

        infeasible = [i.message for i in issues if i.infeasible]

        # forbidden な要素(エッジ / リンク id)を集める
        forbidden = {
            item
            for c in problem.constraints
            if isinstance(c, ForbiddenConstraint)
            for item in c.items
        }

        # route: goal が start から到達可能か ── 「計算」なので route_reachable(algorithms)に任せる
        if isinstance(problem.data, RouteData):
            if not route_reachable(problem.data, forbidden):
                infeasible.append(
                    f"goal {problem.data.goal!r} is unreachable from {problem.data.start!r} "
                    f"after removing {len(forbidden)} forbidden edge(s)"
                )
        # network: 敷設可能リンク全体で全拠点が繋がるか(繋がらなければ全域木は作れない)
        elif isinstance(problem.data, NetworkDesignData):
            adjacency = build_link_adjacency(problem.data, forbidden)
            if not all_nodes_connected((n.id for n in problem.data.nodes), adjacency):
                infeasible.append(
                    f"candidate links (minus {len(forbidden)} forbidden) cannot connect all nodes"
                )

        if infeasible:
            raise InfeasibleProblemError("; ".join(infeasible))
