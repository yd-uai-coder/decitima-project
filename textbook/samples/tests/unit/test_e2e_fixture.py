# DeciTima samples │ 作業単位 15-9
"""E2E テスト専用フェイク(`app/ai/llm/e2e_fixture.py` + `get_gemini_llm` の切り替え)。

対象: `E2eFakeLLM`(構造化出力の固定応答)/ `get_gemini_llm`(`settings.E2E_TESTING` による分岐)。
ドライバ: このテスト関数。スタブ不要 ── `E2eFakeLLM` 自体が対象で、外部依存(実 Gemini API)を
呼ばないことを確認するのがこのテストの目的そのものであるため。
"""

from __future__ import annotations

from typing import cast

import pytest

from app.ai.llm.e2e_fixture import E2eFakeLLM
from app.ai.llm.gemini import get_gemini_llm
from app.core.config import settings
from app.schemas.structuring import (
    ObjectivesConstraintsExtraction,
    ProblemTypeClassification,
    TravelDataPatch,
)


@pytest.fixture(autouse=True)
def _reset_cache_and_flag(monkeypatch: pytest.MonkeyPatch):
    """`get_gemini_llm` は `lru_cache` されているため、E2E_TESTING の値をテストごとに
    切り替えてもキャッシュ経由で古い戻り値が漏れないよう、前後で必ずクリアする。"""
    get_gemini_llm.cache_clear()
    yield
    monkeypatch.setattr(settings, "E2E_TESTING", False)
    get_gemini_llm.cache_clear()


async def test_get_gemini_llm_returns_fake_when_e2e_testing_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "E2E_TESTING", True)

    llm = get_gemini_llm()

    assert isinstance(llm, E2eFakeLLM)


async def test_fake_returns_fixed_response_for_known_schemas() -> None:
    llm = E2eFakeLLM()

    # with_structured_output(schema).ainvoke() の戻り型は BaseModel(共通スーパークラス)
    # までしか narrowing されない ── app/services/explanation.py::_invoke_llm と同じ理由で cast する
    classification = cast(
        ProblemTypeClassification,
        await llm.with_structured_output(ProblemTypeClassification).ainvoke([]),
    )
    extraction = cast(
        ObjectivesConstraintsExtraction,
        await llm.with_structured_output(ObjectivesConstraintsExtraction).ainvoke([]),
    )
    patch = cast(TravelDataPatch, await llm.with_structured_output(TravelDataPatch).ainvoke([]))

    assert classification.problem_type == "travel_planning"
    assert extraction.objectives == []
    assert extraction.constraints == []
    assert patch.budget is None  # ベース問題をそのまま使う設計(全フィールド None)


def test_fake_supports_sync_invoke_too() -> None:
    """`app/ai/graph/nodes.py` は同期 `invoke()` を呼ぶ(`explanation.py`等は非同期
    `ainvoke()`)── 両方を実装していないと片方の経路だけで `AttributeError` になる
    (実測で発覚、詳細は `Phase-15-9.md`)。"""
    llm = E2eFakeLLM()

    classification = cast(
        ProblemTypeClassification, llm.with_structured_output(ProblemTypeClassification).invoke([])
    )

    assert classification.problem_type == "travel_planning"


async def test_fake_raises_for_unhandled_schema() -> None:
    from pydantic import BaseModel

    class _UnhandledSchema(BaseModel):
        pass

    llm = E2eFakeLLM()

    with pytest.raises(NotImplementedError):
        await llm.with_structured_output(_UnhandledSchema).ainvoke([])
