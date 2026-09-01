"""BenchmarkRun のリポジトリ。

既存 CRUDRepository[ModelType] を継承し、create だけ足す(get_by_id は基底が提供)。
flush() はするが commit() はしない(トランザクション境界は BenchmarkService)。
"""

import uuid
from typing import Any

from app.models.optimization import BenchmarkRun
from app.repositories.base import CRUDRepository


class BenchmarkRunRepository(CRUDRepository[BenchmarkRun]):
    model = BenchmarkRun

    async def create(
        self, *, user_id: uuid.UUID, problem_type: str, payload: dict[str, Any]
    ) -> BenchmarkRun:
        """ベンチマーク実行を 1 件追加し、flush して id を確定させた状態で返す。"""
        row = BenchmarkRun(user_id=user_id, problem_type=problem_type, payload=payload)
        self._session.add(row)
        await self._session.flush()
        return row
