"""Problem / Solution のリポジトリ。設計は Phase-0-8.md §5。

既存 CRUDRepository[ModelType] を継承し、固有クエリだけ足す。
flush() はするが commit() はしない(トランザクション境界は SolveService)。
"""

# [以降 Phase で修正予定 ── Phase 3-3] このファイルの現行版はこのまま(スナップショット)。
# Phase 3-3 で BenchmarkRunRepository がこのファイルに同居する(data 層 = model / schema /
# repository は「永続化の関心事」で 1 ファイルにまとめる。route / service は「操作」で割る)。
# この Phase では samples のまま(2 クラス)で実装してよい。
# 現行版 textbook/Phase-3/samples/app/repositories/optimization.py。

import uuid
from typing import Any

from app.models.optimization import Problem, Solution
from app.repositories.base import CRUDRepository


class ProblemRepository(CRUDRepository[Problem]):
    model = Problem

    async def create(
        self, *, user_id: uuid.UUID, problem_type: str, payload: dict[str, Any]
    ) -> Problem:
        """問題を1件追加し、flush して id を確定させた状態で返す。"""
        row = Problem(user_id=user_id, problem_type=problem_type, payload=payload)
        self._session.add(row)
        await self._session.flush()
        return row


class SolutionRepository(CRUDRepository[Solution]):
    model = Solution

    async def create(
        self,
        *,
        problem_id: uuid.UUID,
        status: str,
        algorithm_name: str,
        algorithm_implementation: str,
        payload: dict[str, Any],
    ) -> Solution:
        """解を1件追加し、flush して id を確定させた状態で返す。"""
        row = Solution(
            problem_id=problem_id,
            status=status,
            algorithm_name=algorithm_name,
            algorithm_implementation=algorithm_implementation,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_for_problem(self, problem_id: uuid.UUID) -> list[Solution]:
        """ある問題に紐づく全解を生成日時順で返す(比較 UI 用。Phase 3 で本格利用)。"""
        return await self.list_all(problem_id=problem_id, order_by=Solution.created_at)
