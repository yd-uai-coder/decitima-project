"""AlgorithmStrategy ── すべての「問題まるごとを解く」アルゴリズムが満たす契約。

設計は Phase-0-4.md §2。要点:
- typing.Protocol(継承を強制しない構造的部分型)。手実装 / ライブラリラッパー /
  テスト用フェイクの 3 種が同じ契約に乗れる。
- @runtime_checkable: isinstance(obj, AlgorithmStrategy) を実行時に使えるようにする。
- solve は「純粋」: 入力は OptimizationProblem のみ、出力は CandidateSolution のみ。
  DB・ネットワーク・時刻・グローバル状態に触れない(乱数は problem.metadata["seed"] 経由)。
- solve は「検証しない」: 解を作るだけ。制約充足の判定は Verification が別途行う。
  ただし「解が存在しない」と判断できたら status="infeasible" を返してよい。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.problems.problem import OptimizationProblem
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution


@runtime_checkable
class AlgorithmStrategy(Protocol):
    """1つのアルゴリズムが満たす契約。problem を受けて候補解を返すだけ。"""

    meta: AlgorithmMeta

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        """OptimizationProblem を決定論的に解いて CandidateSolution を返す。検証はしない。"""
        ...
