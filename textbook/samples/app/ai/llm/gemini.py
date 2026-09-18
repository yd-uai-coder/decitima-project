# DeciTima samples │ 初出 Phase 0(テンプレート由来、無改訂) │ 改訂 Phase 15
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.ai.llm.e2e_fixture import E2eFakeLLM
from app.core.config import settings


@lru_cache
def get_gemini_llm(*, temperature: float = 0.7) -> ChatGoogleGenerativeAI | E2eFakeLLM:
    """設定値から構築したChatGoogleGenerativeAIクライアントを、温度パラメータ単位でキャッシュして返す。

    # (Phase 15-9) E2E_TESTING=true のときは本物の Gemini API を一切呼ばず、決定論的な
    # フェイク(E2eFakeLLM)を返す。Playwright は実サーバープロセスに対して実行するため、
    # pytest の monkeypatch(プロセス内差し替え)が使えず、設定値で経路そのものを切り替える
    # 必要があった(`Phase-15-9.md` 参照)。呼び出し元(8箇所)は無改造 ── いずれも
    # `with_structured_output(schema).ainvoke(...)` のインターフェースだけを使うため、
    # このフェイクを返しても同じ呼び方で動く。
    """
    if settings.E2E_TESTING:
        return E2eFakeLLM()
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )
