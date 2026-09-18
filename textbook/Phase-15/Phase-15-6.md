# Phase 15-6: キャッシュ層(Solution Explanation)(作業単位 15-6)

## この章のゴール

README §15「Cache」── `SolutionExplanationService.explain()`(Phase 13)を Redis でキャッシュする。Phase 15 で唯一の新規キャッシュ消費者になった経緯(なぜ他の候補は却下したか)を含めて説明する。

**この章で作成 / 更新するファイル**: `app/services/explanation.py`(改訂)、
`tests/fixtures/fake_redis.py`(改訂、get/set追加)、
`tests/unit/test_explanation_cache.py`(新規)。

---

## 1. キャッシュ候補の選定 ── ルール#17「実在の消費者」テスト

キャッシュを追加する前に、「本当にキャッシュが要るか」を判定する。候補を3つ検討した:

| 候補                                               | 却下 / 採用 | 理由                                                                                                                 |
| ------------------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------------------ |
| `BASE_PROBLEMS`(Phase 11、ベース問題カタログ)              | **却下**  | 純粋な Python 辞書、I/Oコストがゼロ。Redis化はネットワーク往復を足すだけで**むしろ遅くなる**                                                           |
| `ALGORITHM_DESCRIPTIONS`(Phase 12/13、静的説明表)      | **却下**  | 同上、純メモリ辞書                                                                                                          |
| `SolutionExplanationService.explain()`(Phase 13) | **採用**  | Gemini API への実際のネットワーク呼び出しを伴う。しかも同じ `solution_id` への再訪問(結果ページの再読込、`ExplanationCard` の再表示)で**毎回同じ入力から同じ出力を再生成している** |

`explain()` が採用に値する決め手は2つ:

1. **`Solution` は永続化後に不変**(`metrics`/`violations`/`produced_by` は `solve()` 時点で確定し、以後変わらない)。LLM への入力(プロンプト)が完全に決定論的なので、
   キャッシュしても古い情報を返すリスクが無い。
2. **`explain()` は明示的に非永続**(`AlgorithmRecommendationService` と同型、DB に結果を書かない設計)── つまり同じ `solution_id` に対して何度呼んでも、毎回 Gemini API を叩き直している。ここにキャッシュを挟めば、実コスト(レイテンシ・API費用・
   `EXPLAIN_RATE_LIMIT_PER_HOUR/DAY` への負荷)を素直に削減できる。

## 2. 実装 ── `solution_id` キーの Redis キャッシュ

```python
# app/services/explanation.py(改訂、抜粋)
_EXPLANATION_CACHE_TTL_SECONDS = 86400  # 24時間(既存のレート制限の日次ウィンドウに揃えた)

def _explanation_cache_key(solution_id: uuid.UUID) -> str:
    return f"explain:{solution_id}"


class SolutionExplanationService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._read = OptimizationReadService(session)
        self._redis = redis   # (追加)キャッシュの読み書きにも使う
        self._rate_limiter = RateLimiter(...)

    async def explain(self, solution_id, *, user_id, bypass_rate_limit=False) -> ExplanationResponse:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))

        # 所有者チェックは必ずキャッシュより先 ── solution_id を知っているだけの
        # 他ユーザーがキャッシュ済みの説明文を読めてしまう事故を防ぐ
        solution_row = await self._read.get_solution(solution_id, user_id=user_id)

        cached = await self._redis.get(_explanation_cache_key(solution_id))
        if cached is not None:
            return ExplanationResponse.model_validate_json(cached)

        problem_row = await self._read.get_problem(solution_row.problem_id, user_id=user_id)
        ...
        try:
            llm_result = await self._invoke_llm(problem, candidate, alternatives_text)
        except Exception as exc:
            logger.warning(...)
            return _fallback_response(...)   # フォールバックはキャッシュしない

        response = ExplanationResponse(...)
        await self._redis.set(
            _explanation_cache_key(solution_id), response.model_dump_json(),
            ex=_EXPLANATION_CACHE_TTL_SECONDS,
        )
        return response
```

3つの設計判断:

- **所有者チェック(`get_solution`)はキャッシュ参照より先**。`Solution.problem_id` から`Problem.user_id` を辿る既存の JOIN(Phase 1)をキャッシュヒット時にも必ず通す ──「速いから」を理由にセキュリティチェックを省略しない。
- **フォールバック応答(LLM失敗時)はキャッシュしない**。次にサービスが復旧したとき、
  正しい説明文を取り直せるようにするため。
- **キャッシュヒット時は `get_problem` を呼ばない**。所有者チェックに要る `Solution` 側のJOIN だけで済むので、キャッシュヒットのパスは DB 負荷も追加で削減できる。

`FakeRedis`(Phase 1、RateLimiter用に incr/expireだけ実装)に `get`/`set` を追加した
(2人目の消費者。`ex` はテストでは記録するだけで実際には失効させない、既存 `expire` と同じ割り切り)。

---

## まとめ

- `SolutionExplanationService.explain()` を Phase 15 で唯一の新規キャッシュ消費者に選んだ
  ── 純メモリ辞書(`BASE_PROBLEMS`/`ALGORITHM_DESCRIPTIONS`)はルール#17の「実在の消費者」テストに落ちる(I/Oコストが無くキャッシュがむしろ遅くする)のに対し、`explain()` はGemini API への実コストのある呼び出しを不変な入力に対して繰り返している。
- 所有者チェックを必ずキャッシュより先に通し、フォールバック応答はキャッシュしない設計で、セキュリティと鮮度の両方を守った。

## テスト観点(`tests/unit/test_explanation_cache.py`)

> **対象**: `SolutionExplanationService.explain` のキャッシュ経路
> **ドライバ**: このテスト関数
> **スタブ**: `FakeRedis`(2回の呼び出しで同一インスタンスを共有 ── ヒット/ミスを観測するため)
> 
> + `FakeLLM`(`structured_sequence` を1件だけ渡し、2回目に本当にLLMへ到達すると
>   フォールバックに落ちる仕組みで再呼び出しの有無を検証)

| ケース                                  | 期待                                         |
| ------------------------------------ | ------------------------------------------ |
| 同じ `solution_id` に2回 `explain()`     | 2回目はLLM由来の応答と同一(フォールバックに落ちていない = キャッシュヒット) |
| LLM呼び出し失敗                            | フォールバック応答を返し、Redisにはキャッシュされない              |
| 別ユーザーが同じ `solution_id` でキャッシュヒットを試みる | `NotFoundError`(所有者チェックがキャッシュより先に効く)       |

```bash
uv run pytest tests/unit/test_explanation_cache.py tests/unit/test_explanation_service.py -v
uv run pytest tests/api/test_explanation_api.py -v   # API層の無回帰確認
```

---

次章([Phase-15-7](./Phase-15-7.md))ではセキュリティ6項目を監査する。
