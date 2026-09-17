# Phase 11-7: サービス層 + API層(作業単位 11-7)

## この章のゴール

会話記録・レート制限・リトライを取りまとめる `ProblemStructuringService` と、
`POST /api/v1/structure` エンドポイントを実装する。テンプレート由来の `ChatService`/`app/api/routes/chat.py` を置き換える最終章。

**この章で作成/更新するファイル**: `app/services/structuring.py`
(`ProblemStructuringService` 追記、完成)、`app/api/routes/structure.py`(新規)、
`app/api/routes/__init__.py`・`app/core/config.py`・`app/schemas/chat.py`(現行版)。
**削除するファイル**: `app/services/chat.py`、`app/api/routes/chat.py`。

---

## 1. `ProblemStructuringService` ── `ChatService` の骨格を踏襲

```python
# app/services/structuring.py(追記)
class ProblemStructuringService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._rate_limiter = RateLimiter(
            redis, resource="structure",
            limits=[
                RateLimit(window_seconds=3600, max_requests=settings.STRUCTURE_RATE_LIMIT_PER_HOUR),
                RateLimit(window_seconds=86400, max_requests=settings.STRUCTURE_RATE_LIMIT_PER_DAY),
            ],
        )

    async def structure(
        self, *, user_id: uuid.UUID, conversation_id: uuid.UUID | None, text: str,
        bypass_rate_limit: bool = False,
    ) -> tuple[Conversation, OptimizationProblem]:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))

        conversation = await self._get_or_create_conversation(
            user_id=user_id, conversation_id=conversation_id, first_message=text
        )
        await self._conversations.add_message(conversation_id=conversation.id, role="user", content=text)

        from app.ai.graph.workflow import get_structuring_workflow  # 循環 import 回避(下記)

        workflow = get_structuring_workflow()
        result = await self._invoke_with_retry(workflow.ainvoke, {初期 state 8フィールド})

        problem: OptimizationProblem = result["problem"]
        summary = _summarize(problem, result["notes"])
        await self._conversations.add_message(
            conversation_id=conversation.id, role="assistant", content=summary
        )
        await self._session.commit()
        return conversation, problem
```

骨格(レート制限 → 会話取得/作成 → ワークフロー呼び出し → 会話記録 → commit)は旧
`ChatService.send_message` とほぼ同型。`Conversation`/`Message` モデル・
`ConversationRepository`(`create`/`get_by_id`/`add_message`)は**無改造で再利用** ──
Phase 0〜10 の間ずっと実消費者が無かったこれらの資産が、Phase 11 で初めて動く。

**`problem_type` を別途返さない**: `structure()` の戻り値は `(Conversation,
OptimizationProblem)` の2要素だけ。`problem.problem_type` は `Literal[6種]` で型付け済みなので、これとは別に `str` 型の `problem_type` を返す必要が無い(冗長な情報を持たせない
── pyright が「`str` を `Literal` に代入できない」と指摘するのを `cast` で握りつぶすのでは
なく、そもそも二重に持たない設計にする)。

---

## 2. 循環 import の回避 ── 関数内 import

`app/ai/graph/nodes.py`(11-3〜11-5)は `app/services/structuring.py` の `EXTRACTORS`/`catalog_entries`/`catalog_ids`/`ground_references` を import する。一方`ProblemStructuringService`(本章)は `app/ai/graph/workflow.py::get_structuring_workflow`
を呼ぶ必要がある。両方をモジュール先頭で import すると:

```text
app.services.structuring → app.ai.graph.workflow → app.ai.graph.nodes → app.services.structuring
```

という循環になる。`get_structuring_workflow` の import を `structure()` メソッド内の**関数内 import**にすることで輪を断つ(2回目以降の import は Python のモジュールキャッシュから返るため、実行時コストは無視できる)。**この問題は「ドメイン非依存の機構
(`EXTRACTORS` 等)を `services/structuring.py` に、サービス(`ProblemStructuringService`)も
同じファイルに」という設計から必然的に生じる**(11-2 と本章が同じファイルを共有しているため)── ファイルを分ければ避けられたが、「1つの problem_type に依存しない Structuring 機構」としてまとめて置く方が読みやすいと判断し、関数内 import で対処する側を選んだ。

---

## 3. リトライ ── Validation 系の失敗はリトライしない

```python
async def _invoke_with_retry(self, invoke, initial_state) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            return await invoke(initial_state)
        except (ProblemValidationError, InfeasibleProblemError):
            raise  # 入力起因の失敗はリトライしても解消しない
        except Exception as exc:
            if _is_quota_error(exc):
                raise RateLimitExceededError(...) from exc
            last_error = exc
            if attempt < MAX_GENERATION_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
    raise GenerationFailedError(...) from last_error
```

旧 `ChatService._invoke_with_retry` との違いは1点: `except (ProblemValidationError,
InfeasibleProblemError): raise` を追加した。`validate_problem`(11-6)が投げるこれらの例外は**入力(LLM の抽出結果)そのものが不正**なことを意味し、同じ入力で再試行しても結果は変わらない ── リトライは Gemini API の一時的な失敗(ネットワーク・レート制限等)にのみ意味がある。Tavily 由来のクォータ判定分岐は削除した(`_is_quota_error` は Gemini の429 だけを見る)。

---

## 4. API 層 ── 薄いルート、専用の「確定して solve」エンドポイントは作らない

```python
# app/api/routes/structure.py(全文)
router = APIRouter(prefix="/structure", tags=["structure"])

@router.post("", response_model=StructuringResponse)
async def structure_problem(
    payload: StructuringRequest, session: SessionDep, redis: RedisDep, current_user: CurrentUserDep,
) -> StructuringResponse:
    service = ProblemStructuringService(session, redis)
    conversation, problem = await service.structure(
        user_id=current_user.id, conversation_id=payload.conversation_id, text=payload.text,
        bypass_rate_limit=current_user.is_superuser,
    )
    return StructuringResponse(
        conversation_id=conversation.id, problem_type=problem.problem_type, problem=problem,
    )
```

サービスを呼ぶ→スキーマに詰めて返すだけ(`solve.py` と同じ設計)。**「確定して solve する」専用エンドポイントは新設しない** ── `StructuringResponse.problem` は `OptimizationProblem`そのものなので、既存 `POST /api/v1/solve` にそのまま渡せる(README「LLM Service はスキーマ経由でのみ Algorithm Engine と接続する」の実演)。UI 側の「確定」ボタンはsolve を直接呼ぶのではなく、既存の該当ドメインページへ遷移する設計にする(11-8/11-9)。

`app/api/routes/__init__.py` の `chat_router` 除外コメントを `structure_router` 登録に置換する。

---

## まとめ

- `ProblemStructuringService` は旧 `ChatService` の骨格を踏襲しつつ、Tavily 分岐を削除しValidation 系例外をリトライ対象から除外した。
- `EXTRACTORS` 等(11-2)とサービス本体を同じファイルに置いたことで生じた循環 import は関数内 import で断つ。
- 新しいエンドポイントは `POST /api/v1/structure` だけ。「確定して solve」は既存
  `POST /api/v1/solve` を UI 側から呼ぶだけで済む(サーバ側の統合は不要)。

## テスト観点(`tests/unit/test_structuring_service.py` / `tests/api/test_structure_api.py` 新規)

> **対象**: `ProblemStructuringService.structure`(unit)、`POST /api/v1/structure` の契約(api)
> **ドライバ**: 各テスト関数。`db_session` フィクスチャ(unit)/ `api` フィクスチャ
> (FakeRedis + インメモリ SQLite、api)
> **スタブ**: `FakeRedis` + `get_structuring_workflow` を差し替えたフェイクワークフロー(`ainvoke` が固定結果 or 例外を返すだけ)。Structuring ワークフロー自体のノード合成は11-6 の `test_structuring_workflow.py` で確認済みのため、ここでは「サービス/API がワークフローの結果をどう扱うか」だけに対象を絞る

| ケース                                                            | 期待                                                          |
| -------------------------------------------------------------- | ----------------------------------------------------------- |
| `structure()`(新規会話)                                            | `Conversation`/`Message`(user→assistant の2件)が作られる           |
| `structure()`(既存 `conversation_id` を指定)                        | 同じ会話を再利用、メッセージが積み増される                                       |
| `structure()`(未知の `conversation_id`)                           | `ConversationNotFoundError`                                 |
| `structure()`(`ProblemValidationError` を送出するフェイクワークフロー)        | 例外がそのまま伝播、リトライされない(呼び出し1回だけ)                                |
| `structure()`(1回目 `RuntimeError`、2回目成功)                        | 2回目の結果で成功(リトライが効く)                                          |
| `structure()`(3回とも `RuntimeError`)                             | `GenerationFailedError`                                     |
| `STRUCTURE_RATE_LIMIT_PER_HOUR=1` で2回連続 `structure()`          | 2回目は `RateLimitExceededError`。`bypass_rate_limit=True` なら通る |
| `POST /api/v1/structure` → 200                                 | 返る `problem` をそのまま `POST /api/v1/solve` に渡せる(200)           |
| `POST /api/v1/structure`(フェイクワークフローが `ProblemValidationError`) | 400                                                         |
| `POST /api/v1/structure`(未知の `conversation_id`)                | 404                                                         |

`uv run pytest tests/unit/test_structuring_service.py tests/api/test_structure_api.py` /
`uvx pyright app/services/structuring.py app/api/routes/structure.py`。

---

次章([Phase-11-8](./Phase-11-8.md))では、作業単位 11-8 ── decitima-ui に
`features/structuring/`(自然言語入力 + 確認カード)を実装する。
