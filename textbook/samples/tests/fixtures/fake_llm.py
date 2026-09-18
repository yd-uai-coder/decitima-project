# DeciTima samples │ 初出 Phase 11(11-3) │ 改訂 Phase 12,14
"""LLM クライアントの挙動を模したテスト用スタブ。

以前(テンプレート由来)は `tests/unit/test_ai_graph_nodes.py` にクラス定義が直接埋め込まれて
いたが、Phase 11 で複数のテストファイルから使うため切り出した。Web検索QA用の
`FakeSearchTool` は Tavily の廃止(11-3)に伴い持ち越さない。

`with_structured_output(schema)` の呼び出しごとに `schema` を `structured_output_calls` に
記録する ── どのドメインでどのスキーマが使われたかを検証する章(11-5)で使う。

# (Phase 12-2) `AlgorithmRecommendationService` は LangGraph を介さない素の async 関数のため
# `llm.ainvoke(...)` を直接呼ぶ(11-3〜11-6 のノードは同期 `invoke` のみ)。第二の消費者として
# `ainvoke` を両クラスに追加する(既存の `invoke` は無変更 ── 後方互換)。

# (Phase 14-5) `ComparisonService` は LLM Only 戦略を複数回再実行し、回によって違う解・例外に
# なるケースをテストする必要がある(再現性・エラー率)。固定の `structured` 1 個では表せない
# ため、任意の `structured_sequence`(呼び出しごとに1つずつ消費するリスト。要素が
# `Exception` インスタンスならその回は例外を送出する)を追加した。`structured=` のみを渡す
# 既存の呼び出しは無変更で動く(`_sequence` が None なら従来どおり固定値を返す)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from pydantic import BaseModel


class FakeLLM:
    """Gemini LLM クライアント(`get_gemini_llm` の戻り値)の挙動を模したスタブ。"""

    def __init__(
        self,
        content: str | None = None,
        structured: BaseModel | None = None,
        structured_sequence: list[BaseModel | Exception] | None = None,  # (Phase 14-5)
    ) -> None:
        # content: invoke()が返すAIMessageの本文
        # structured: with_structured_output().invoke()が返す構造化レスポンス(固定1件)
        # structured_sequence: 呼び出しごとに1つずつ消費する構造化レスポンス/例外の列(Phase 14-5)
        self._content = content
        self._structured = structured
        self._structured_sequence = structured_sequence
        self.structured_output_calls: list[type[BaseModel]] = []

    def invoke(self, _messages: Any) -> AIMessage:
        """通常のinvoke呼び出しの結果としてAIMessageを返す。"""
        return AIMessage(content=self._content)

    async def ainvoke(self, messages: Any) -> AIMessage:  # (Phase 12-2)
        """invoke の非同期版(結果は同じ)。"""
        return self.invoke(messages)

    def with_structured_output(self, schema: type[BaseModel]) -> _FakeStructuredLLM:
        """構造化出力用のサブクライアントを返す。呼ばれた schema を記録する。"""
        self.structured_output_calls.append(schema)
        return _FakeStructuredLLM(self._structured, self._structured_sequence)


class _FakeStructuredLLM:
    """with_structured_output()が返す、構造化レスポンスのみを返すテスト用スタブ。"""

    def __init__(
        self,
        structured: BaseModel | None,
        sequence: list[BaseModel | Exception] | None = None,  # (Phase 14-5)
    ) -> None:
        self._structured = structured
        self._sequence = sequence

    def invoke(self, _messages: Any) -> BaseModel | None:
        """構造化済みレスポンスをそのまま返す。sequence 指定時は先頭から1つずつ消費し、
        値が Exception インスタンスならその回の呼び出しとして送出する(Phase 14-5)。"""
        if self._sequence is not None:
            item = self._sequence.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return self._structured

    async def ainvoke(self, messages: Any) -> BaseModel | None:  # (Phase 12-2)
        """invoke の非同期版(結果は同じ)。"""
        return self.invoke(messages)
