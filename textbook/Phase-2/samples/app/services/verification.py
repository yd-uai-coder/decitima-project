"""SolutionVerificationService ── 解の制約充足(候補解が出た後)。

設計は Phase-0-6.md §3。Phase 2 で route 限定から全 problem_type・全 kind へ一般化した。

- 解の型ごとの「構造検証」は app/domain/solutions/structure.py
  (verify_route_structure / verify_shift_structure)。shift はここで
  labor_cost / day_off_satisfaction の metrics も確定する。
- 制約 kind ごとのチェッカーは app/domain/constraints/(CHECKERS レジストリ)。

このサービス自体はロジックを持たず、「構造検証 → metrics enrich → kind ディスパッチ →
hard/soft 集計」の純粋なオーケストレーションに徹する。
hard 違反 → status="invalid"、soft 違反 → soft_penalty を metrics に加算。
解は書き換えず model_copy(update=...) で新インスタンスを返す(生の解を監査用に残す)。
"""

from __future__ import annotations

from app.domain.constraints import CHECKERS
from app.domain.problems.problem import OptimizationProblem
from app.domain.solutions.solution import CandidateSolution, ConstraintViolation
from app.domain.solutions.structure import structural_verify


class SolutionVerificationService:
    """候補解が制約を満たすか検証し、status / violations / metrics を確定する。"""

    def verify(
        self, problem: OptimizationProblem, solution: CandidateSolution
    ) -> CandidateSolution:
        if solution.status == "infeasible":
            return solution  # 解が無いものは検証しない

        # 1. 構造検証。解の型ごとに常に必要な検査 + 追加メトリクス(shift の labor_cost 等)
        structural, extra_metrics = structural_verify(problem, solution)
        enriched = solution.model_copy(update={"metrics": {**solution.metrics, **extra_metrics}})

        # 2. 制約 kind ごとのチェッカー。enriched の metrics(構造検証後)を読む
        kind_violations: list[ConstraintViolation] = []
        for c in problem.constraints:
            checker = CHECKERS.get(c.kind)
            if checker is None:
                continue  # 専用チェッカーの無い kind は素通し
            v = checker(c, problem, enriched)
            if v is not None:
                kind_violations.append(v)

        violations = [*structural, *kind_violations]
        has_hard = any(v.severity == "hard" for v in violations)

        return enriched.model_copy(
            update={
                "status": "invalid" if has_hard else enriched.status,
                "violations": violations,
                "metrics": {**enriched.metrics, "soft_penalty": _soft_penalty(problem, violations)},
            }
        )


def _soft_penalty(problem: OptimizationProblem, violations: list[ConstraintViolation]) -> float:
    """違反した soft 制約の penalty 合計。kind 一致で対応付ける(Phase-0-6.md §3.2)。"""
    violated_kinds = {v.constraint_kind for v in violations if v.severity == "soft"}
    return sum(
        (c.penalty or 0.0)
        for c in problem.constraints
        if c.severity == "soft" and c.kind in violated_kinds
    )
