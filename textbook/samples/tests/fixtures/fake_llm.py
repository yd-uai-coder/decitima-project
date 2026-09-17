# DeciTima samples │ 初出 Phase 11(11-3) │ 改訂 Phase 12
"""LLM クライアントの挙動を模したテスト用スタブ。

以前(テンプレート由来)は `tests/unit/test_ai_graph_nodes.py` にクラス定義が直接埋め込まれて
いたが、Phase 11 で複数のテストファイルから使うため切り出した。Web検索QA用の
`FakeSearchTool` は Tavily の廃止(11-3)に伴い持ち越さない。

`with_structured_output(schema)` の呼び出しごとに `schema` を `structured_output_calls` に
記録する ── どのドメインでどのスキーマが使われたかを検証する章(11-5)で使う。

# (Phase 12) `AlgorithmRecommendationService` は LangGraph を介さない素の async 関数のため
# `llm.ainvoke(...)` を直接呼ぶ(11-3〜11-6 のノードは同期 `invoke` のみ)。第二の消費者として
# `ainvoke` を両クラスに追加する(既存の `invoke` は無変更 ── 後方互換)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from pydantic import BaseModel


class FakeLLM:
    """Gemini LLM クライアント(`get_gemini_llm` の戻り値)の挙動を模したスタブ。"""

    def __init__(self, content: str | None = None, structured: BaseModel | None = None) -> None:
        # content: invoke()が返すAIMessageの本文
        # structured: with_structured_output().invoke()が返す構造化レスポンス
        self._content = content
        self._structured = structured
        self.structured_output_calls: list[type[BaseModel]] = []

    def invoke(self, _messages: Any) -> AIMessage:
        """通常のinvoke呼び出しの結果としてAIMessageを返す。"""
        return AIMessage(content=self._content)

    async def ainvoke(self, messages: Any) -> AIMessage:  # (Phase 12)
        """invoke の非同期版(結果は同じ)。"""
        return self.invoke(messages)

    def with_structured_output(self, schema: type[BaseModel]) -> _FakeStructuredLLM:
        """構造化出力用のサブクライアントを返す。呼ばれた schema を記録する。"""
        self.structured_output_calls.append(schema)
        return _FakeStructuredLLM(self._structured)


class _FakeStructuredLLM:
    """with_structured_output()が返す、構造化レスポンスのみを返すテスト用スタブ。"""

    def __init__(self, structured: BaseModel | None) -> None:
        self._structured = structured

    def invoke(self, _messages: Any) -> BaseModel | None:
        """構造化済みレスポンスをそのまま返す。"""
        return self._structured

    async def ainvoke(self, messages: Any) -> BaseModel | None:  # (Phase 12)
        """invoke の非同期版(結果は同じ)。"""
        return self.invoke(messages)
