# Phase 13-3: ルート配線 + e2e(作業単位 13-3)

## この章のゴール

`SolutionExplanationService`(13-2 で完成)を
`POST /api/v1/solutions/{solution_id}/explain` として公開する。新しいルートファイルは作らず、
既存 `routes/solutions.py` に追記する判断の理由がこの章の核(Phase 12 の
`routes/algorithms.py` への追記と同じ判断)。

**この章で作成/更新するファイル**: `app/api/routes/solutions.py`(改訂、追記)。

---

## 1. 新しいファイルを作らず既存 `routes/solutions.py` に追加する

`explain` は「solutions」という**既存の操作対象に対する追加の操作**でしかない。CLAUDE.md の
「`api/routes`/`services` は操作(エンドポイント群/ユースケース)で割る」という既存判断に従い、
新ファイルを作らず `GET /solutions/{id}` と同じ `routes/solutions.py` に追記する(Phase 12 が
`recommend` を `routes/algorithms.py` に足した判断と同型):

```python
# app/api/routes/solutions.py(追記。既存 get_solution/get_problem/list_problem_solutions はそのまま)
from app.api.deps import CurrentUserDep, RedisDep, SessionDep
from app.schemas.explanation import ExplanationResponse
from app.services.explanation import SolutionExplanationService

# ...(既存 GET "/solutions/{solution_id}" 等はそのまま)...

@router.post("/solutions/{solution_id}/explain", response_model=ExplanationResponse)
async def explain_solution(
    solution_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep, redis: RedisDep
) -> ExplanationResponse:
    """保存済みの解を自然言語で説明する(LLM、補助機能。永続化しない)。"""
    service = SolutionExplanationService(session, redis)
    return await service.explain(
        solution_id, user_id=current_user.id, bypass_rate_limit=current_user.is_superuser,
    )
```

`GET /solutions/{id}` は `SessionDep` のみだったが、`explain` は LLM 呼び出しのレート制限に
`RedisDep` も要る(`POST /algorithms/recommend` と同じ形)。`app/api/routes/__init__.py` は
変更不要 ── `solutions_router` は既にルーター集約に登録済み(Phase 1)なので、このファイルに
追加したルートは自動的に有効になる。

`settings.EXPLAIN_RATE_LIMIT_PER_HOUR`/`_PER_DAY` は 13-2 で `config.py` に追加済み
(`SolutionExplanationService.__init__` が参照するため、サービス本体と同じ章で足した ──
`Phase-13-2.md` §2 参照)。この章では触らない。

## 2. `POST` にする理由(`GET /solutions/{id}` との違い)

`explain` は解のデータを変更しないので一見 `GET` でもよさそうだが、LLM 呼び出しを伴い
副作用(レート制限カウンタの消費・外部 API 課金)があるため、`POST /algorithms/recommend`・
`POST /simulate`・`POST /verify` と同じ「読み取り専用だが実行アクションである」エンドポイント
群の慣例に揃えて `POST` にする。パスは `/solutions/{solution_id}/explain` ── 「ある solution
に対する操作」であることをパスで表現する(REST のサブリソース的な形。`jobs/{id}` に対する
アクションが無いのは Phase 9 では単純な状態取得のみだったため。ここでは explain という
明確な「アクション」があるので動詞をパスに含める)。

---

## まとめ

- 新しいエンドポイントは `POST /api/v1/solutions/{solution_id}/explain` だけ。新ファイルは
  作らず既存 `routes/solutions.py` に追記する。
- `app/api/routes/__init__.py` は無改造(ルーター登録は Phase 1 で完了済み)。
- レート制限設定は 13-2 で既に足してあるので、この章はルート配線だけに専念する。

## テスト観点(`tests/api/test_explanation_api.py`)

> **対象**: `POST /api/v1/solutions/{solution_id}/explain` の契約
> **ドライバ**: `api` フィクスチャ(認証込み client)
> **スタブ**: `FakeLLM`(`app.services.explanation.get_gemini_llm` を差し替え)

サービス層の振る舞い(LLM呼び出し・フォールバック・レート制限)は 13-2 の unit テストで
確認済みのため、ここでは「API として正しく配線されているか」「既存 `GET /solutions/{id}`
を壊していないか」「404 が伝播するか」だけに対象を絞る(`test_algorithm_recommendation_api.py`
と同じ役割分担)。

| ケース | 期待 |
| --- | --- |
| `POST /solve` で解を永続化 → `POST /solutions/{id}/explain`(FakeLLM が5項目を返す) | 200、`solution_id`/`algorithm_name` が一致、`key_constraints` に制約への言及が反映される |
| 存在しない `solution_id` で `POST /solutions/{id}/explain` | 404 |
| `GET /solutions/{id}`(この章の追記後) | 200(1-7 の既存エンドポイントへの回帰が無いことの確認) |

```bash
uv run pytest tests/unit/test_explanation_service.py tests/api/test_explanation_api.py
uvx pyright app/api/routes/solutions.py
```

overlay 検証(backend 全体): `uv run pytest` 602 passed / `ruff check app tests analysis` /
`ruff format --check app tests analysis` / `uvx pyright app tests` いずれも 0 件
(`app/services/errors.py` の pre-existing 債務は対象外)。`alembic upgrade head` は no-op
(新テーブル無し)。

---

次章([Phase-13-4](./Phase-13-4.md))では、作業単位 13-4 ── decitima-ui に説明カードを実装し、
6つの既存 Planner Panel へ導線を配線する。
