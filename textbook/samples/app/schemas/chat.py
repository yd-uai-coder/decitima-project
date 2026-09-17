# DeciTima samples │ Phase 11(11-7)
"""会話(Conversation/Message)の読み出し用スキーマ。

以前(テンプレート由来)の `ChatRequest`/`ChatResponse` は Web検索QAチャット機能の廃止に伴い
削除した(`StructuringRequest`/`StructuringResponse`(app/schemas/structuring.py)に置換)。
`MessageRead`/`ConversationRead`/`ConversationDetail` は `ProblemStructuringService` が
会話記録に使うためそのまま再利用する。
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

MessageRole = Literal["user", "assistant", "system", "tool"]


class MessageRead(BaseModel):
    """メッセージ1件をAPIレスポンスとして返す際のスキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    """会話の概要（メッセージ本文を含まない）をAPIレスポンスとして返す際のスキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    """会話の詳細（メッセージ一覧を含む）をAPIレスポンスとして返す際のスキーマ。"""

    messages: list[MessageRead] = []
