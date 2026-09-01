"""ProblemValidationService ── 問題定義の妥当性(Algorithm Engine に渡す前)。

設計は Phase-0-6.md §2。Phase 1 は **route_planning 限定の最小実装**。
- Input Validation(型・値域)は Pydantic の Field 制約が既に担う(route_planner.py の
  weight=Field(ge=0) 等)。
- ここで行う Semantic Validation: start/goal が nodes に存在 / エッジ端点が nodes に存在 /
  禁止エッジ除去後も start→goal が到達可能か(BFS)。
- 「明らかに無理」(到達不能)は InfeasibleProblemError。整合性の欠陥は ProblemValidationError。
- shift_scheduling の検査、kind ごとのチェッカーの domain/ への切り出しは Phase 2。

原則: 「明らかに無理」だけを弾き、グレーゾーンは通す(Phase-0-6.md §2.4)。
"""

# [以降 Phase で修正予定 ── Phase 2-2] このファイルの Phase 1 版はこのまま(スナップショット)。
# Phase 2-2 で: Semantic 検査を app/domain/problems/semantic.py の SEMANTIC_CHECKS レジストリへ
# 切り出し、このサービスはレジストリを回すだけに縮小(到達可能性のみ algorithms を使うので残置)。
# 解決される問題: shift の未検証、problem_type 追加時のサービス改修。
# 現行版 textbook/Phase-2/samples/app/services/validation.py。詳細 Phase-2-2.md。

from __future__ import annotations

from app.algorithms.graph.dijkstra import build_adjacency
from app.algorithms.search.bfs import reachable_nodes
from app.domain.problems.problem import ForbiddenConstraint, OptimizationProblem
from app.domain.problems.route_planner import RouteData
from app.services.errors import InfeasibleProblemError, ProblemValidationError


class ProblemValidationService:
    """OptimizationProblem がアルゴリズムに渡せる状態か、問題全体を見て検査する。"""

    def validate(self, problem: OptimizationProblem) -> None:
        """検査に通れば None を返す。整合性 NG は ProblemValidationError、
        到達不能は InfeasibleProblemError を送出する。"""
        if isinstance(problem.data, RouteData):
            self._validate_route(problem, problem.data)
        # shift_scheduling は Phase 2/5 で追加。それまでは素通し(グレーは通す)

    def _validate_route(self, problem: OptimizationProblem, data: RouteData) -> None:
        node_ids = {n.id for n in data.nodes}
        errors: list[str] = []

        # start / goal が nodes に存在するか
        if data.start not in node_ids:
            errors.append(f"start node {data.start!r} not found in nodes")
        if data.goal not in node_ids:
            errors.append(f"goal node {data.goal!r} not found in nodes")

        # 各エッジの端点が nodes に存在するか
        for edge in data.edges:
            for endpoint in (edge.source, edge.target):
                if endpoint not in node_ids:
                    errors.append(f"edge {edge.id!r} references unknown node {endpoint!r}")

        if errors:
            raise ProblemValidationError("; ".join(errors))

        # 禁止エッジを除いたグラフで start から goal に到達できるか
        forbidden = {
            item
            for c in problem.constraints
            if isinstance(c, ForbiddenConstraint)
            for item in c.items
        }
        adjacency = build_adjacency(data, forbidden)
        # build_adjacency は (隣接, edge_id, weight) を返すので id だけの隣接に落とす
        plain = {node: [nxt for nxt, _eid, _w in edges] for node, edges in adjacency.items()}
        if data.goal not in reachable_nodes(plain, data.start):
            raise InfeasibleProblemError(
                f"goal {data.goal!r} is unreachable from {data.start!r} "
                f"after removing {len(forbidden)} forbidden edge(s)"
            )
