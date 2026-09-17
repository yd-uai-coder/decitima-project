# Phase 12-3: ルート配線 + e2e(作業単位 12-3)

## この章のゴール

`AlgorithmRecommendationService`(12-2 で完成)を `POST /api/v1/algorithms/recommend` として公開する。新しいルートファイルは作らず、既存 `routes/algorithms.py` に追記する判断の理由がこの章の核。

**この章で作成/更新するファイル**: `app/api/routes/algorithms.py`(改訂、追記)。

---

## 1. 新しいファイルを作らず既存 `routes/algorithms.py` に追加する

Phase 11 の `/structure` は新しい問題領域(LLM Problem Structuring 全体)だったので
`routes/structure.py` を新設したが、Phase 12 の推薦エンドポイントは「algorithms」という**既存の操作対象に対する追加の操作**でしかない。CLAUDE.md の「`api/routes`/`services` は操作(エンドポイント群/ユースケース)で割る」という既存判断に従い、新ファイルを作らず
`GET /algorithms` と同じ `routes/algorithms.py` に追記する:

```python
# app/api/routes/algorithms.py(追記。既存 list_algorithms はそのまま)
from app.api.deps import CurrentUserDep, RedisDep
from app.schemas.recommendation import RecommendationResponse, RecommendRequest
from app.services.algorithm_recommendation import AlgorithmRecommendationService

# ...(既存 GET "" はそのまま)...

@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_algorithm(
    payload: RecommendRequest,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> RecommendationResponse:
    """構造化済み問題に対し、候補アルゴリズムと推薦理由(ルール + LLM)を返す。
    /solve の既定選択には影響しない。"""
    service = AlgorithmRecommendationService(redis)
    return await service.recommend(
        user_id=current_user.id,
        problem=payload.problem,
        bypass_rate_limit=current_user.is_superuser,
    )
```

`/verify` と同型で `SessionDep` は要らない(DB を触らないため)。`app/api/routes/__init__.py`
は変更不要 ── `algorithms_router` は既にルーター集約に登録済み(Phase 1)なので、
このファイルに追加したルートは自動的に有効になる。

`settings.RECOMMEND_RATE_LIMIT_PER_HOUR`/`_PER_DAY` は 12-2 で `config.py` に追加済み(`AlgorithmRecommendationService.__init__` が参照するため、サービス本体と同じ章で足した ── `Phase-12-2.md` §2 参照)。この章では触らない。

---

## まとめ

- 新しいエンドポイントは `POST /api/v1/algorithms/recommend` だけ。新ファイルは作らず既存 `routes/algorithms.py` に追記する(「algorithms」という同じ操作対象のため)。
- `app/api/routes/__init__.py` は無改造(ルーター登録は Phase 1 で完了済み)。
- レート制限設定は 12-2 で既に足してあるので、この章はルート配線だけに専念する。

## テスト観点(`tests/api/test_algorithm_recommendation_api.py`)

> **対象**: `POST /api/v1/algorithms/recommend` の契約
> **ドライバ**: `api` フィクスチャ(認証込み client)
> **スタブ**: `FakeLLM`(`app.services.algorithm_recommendation.get_gemini_llm` を差し替え)

サービス層の振る舞い(rule/LLM のマージ・grounding・レート制限)は 12-2 の unit テストで確認済みのため、ここでは「API として正しく配線されているか」「既存 `GET /algorithms` を壊していないか」だけに対象を絞る。

| ケース                                                                            | 期待                                                                               |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `POST /api/v1/algorithms/recommend`(travel_planning、FakeLLM が knapsack_dp を推薦) | 200、`rule_preferred="knapsack_dp"`、`is_rule_preferred=True`、`llm_comment` が反映される |
| `GET /api/v1/algorithms`(この章の追記後)                                              | 200(1-7 の既存エンドポイントへの回帰が無いことの確認)                                                  |

```bash
uv run pytest tests/unit/test_algorithm_recommendation_service.py tests/api/test_algorithm_recommendation_api.py
uvx pyright app/api/routes/algorithms.py
```

overlay 検証(backend 全体): `uv run pytest tests/unit tests/api` 510 passed /
`ruff check app tests` 0 件 / `uvx pyright` 0 件。`alembic upgrade head` は no-op
(新テーブル無し)。

---

次章([Phase-12-4](./Phase-12-4.md))では、作業単位 12-4 ── decitima-ui に推薦カードを実装し、
6つの既存 Planner Panel へ導線を配線する。
