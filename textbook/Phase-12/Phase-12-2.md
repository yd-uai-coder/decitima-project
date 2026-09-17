# Phase 12-2: `AlgorithmRecommendationService`(作業単位 12-2)

## この章のゴール

Rule Engine(既存 `select_strategy`)と LLM 推薦を合成し、候補アルゴリズム一覧+理由を返す`AlgorithmRecommendationService` を実装する。候補が1件のみの場合・LLM が失敗した場合・LLM が存在しない候補名を返した場合、それぞれの扱いを決めるのがこの章の核。

**この章で作成/更新するファイル**: `app/services/algorithm_recommendation.py`(新規)、
`app/core/config.py`(改訂、レート制限フィールド追加)、
`tests/fixtures/fake_llm.py`(`ainvoke` 追加、改訂)。

---

## 1. 全体の流れ

```python
# app/services/algorithm_recommendation.py(要点)
class AlgorithmRecommendationService:
    def __init__(self, redis: Redis) -> None:
        self._rate_limiter = RateLimiter(
            redis, resource="recommend",
            limits=[
                RateLimit(window_seconds=3600, max_requests=settings.RECOMMEND_RATE_LIMIT_PER_HOUR),
                RateLimit(window_seconds=86400, max_requests=settings.RECOMMEND_RATE_LIMIT_PER_DAY),
            ],
        )

    async def recommend(self, *, user_id, problem, bypass_rate_limit=False) -> RecommendationResponse:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))

        candidates = get_strategies(problem.problem_type)
        if not candidates:
            raise NoAlgorithmError(...)

        rule_preferred = select_strategy(problem).meta.name   # ← 第二の消費者、無変更で再利用

        if len(candidates) == 1:
            ...  # LLM を呼ばず即返す
        try:
            llm_result = await self._invoke_llm(problem, candidates, rule_preferred)
        except Exception as exc:
            logger.warning(...)
            ...  # rule のみで返す
        ...  # grounding + マージ + ソート
```

`VerifyService`(`app/services/verify.py`)と同じ骨格 ── `__init__` で `RateLimiter` を組み立て、メソッド冒頭で `enforce`。永続化しない(DB を触らない)。

## 2. レート制限フィールドの追加(`__init__` を書いたら真っ先に足す)

```python
# app/core/config.py(追記)
# (Phase 12) Algorithm Recommendation のレート制限(単位時間あたりの上限回数)
RECOMMEND_RATE_LIMIT_PER_HOUR: int = 20
RECOMMEND_RATE_LIMIT_PER_DAY: int = 100
```

Phase 11-7 の `STRUCTURE_RATE_LIMIT_PER_HOUR` と全く同じ形。**上の `__init__` が
`settings.RECOMMEND_RATE_LIMIT_PER_HOUR`/`_PER_DAY` を参照するので、この設定を足さずに
`AlgorithmRecommendationService` をインスタンス化すると即座に `AttributeError` になる**
(Phase 11-7 で実際に踏んだ写経漏れと同じ罠 ── `CLAUDE.md` Notes `Phase 11-7` 参照)。
`__init__` を書いたその場で、忘れずにこの2行も足すこと。

## 3. `select_strategy` を無変更で呼ぶことの意味

`rule_preferred = select_strategy(problem).meta.name` は Phase 4〜9 で完成した rule-based selection をそのまま使う。**この関数を Phase 12 のために変更しない** ── 変更すると
`/solve` の既定挙動まで変わってしまい、README「Rule Engine は Step 1 のまま、Step 2 は追加のレイヤー」という設計が崩れる。「第二の消費者が現れても、消費される側は触らない」
好例(進行のルール #17 の逆 ── 触ってよい条件を満たさない場合は触らない)。

## 4. 候補が1件だけなら LLM を呼ばない

```python
# app/services/algorithm_recommendation.py(要点)
if len(candidates) == 1:
    return RecommendationResponse(
        ...,
        recommendations=[_build_recommendation(candidates[0], ...)],
        notes=["候補が1件のみのため LLM は呼び出していません"],
    )
```

現行 registry には該当する problem_type が無い(全 6 ドメインとも 3 件以上登録されている)が、将来 problem_type を追加した直後(strategy がまだ1つしか無い時期)には起こり得る。「今使われていない分岐を書く」ように見えるが、**入力次第で必ず通り得る分岐なのでテストする**(テスト観点参照。フェイクで候補リストだけ差し替えて機構として検証する)。

## 5. LLM 呼び出しの失敗はグレースフルデグレード + ログ

```python
# app/services/algorithm_recommendation.py(要点)
try:
    llm_result = await self._invoke_llm(problem, candidates, rule_preferred)
except Exception as exc:  # noqa: BLE001
    logger.warning("algorithm recommendation LLM call failed: %r", exc)
    return RecommendationResponse(..., notes=["LLM 推薦の呼び出しに失敗したため、ルールベースの結果のみ返しています"])
```

`/structure`(Phase 11)は LLM 呼び出し失敗を `GenerationFailedError`(502)として呼び出し元に伝播させ、リトライもする。Phase 12 は**あえて違う設計**にする ── 推薦は補助機能であり、失敗しても `/solve` 自体は困らない(ユーザーは推薦を見ずに解けばよいだけ)。そのため例外にせず、ルールのみの結果を返して機能を止めない。

ただし Phase 11-8 で学んだ教訓(`CLAUDE.md` Notes)── 例外を握りつぶすとログに何も
残らない ── を踏まえ、`logger.warning` は必ず書く。「補助機能だから静かに失敗してよい」と「原因が分からなくなってよい」は別の話。

## 6. grounding ── 存在しない候補名は黙って無視する

```python
# app/services/algorithm_recommendation.py(要点)
valid_names = {s.meta.name for s in candidates}
rank_by_name = {name: i + 1 for i, name in enumerate(llm_result.ranked_names) if name in valid_names}
comment_by_name = {c.name: c.comment for c in llm_result.comments if c.name in valid_names}
```

`app.services.structuring.ground_references`(Phase 11)と同じ「LLM 出力は常に信頼しない」の踏襲。ただし Phase 11 の `ground_references` は違反があれば `ProblemValidationError` を**送出する**(structuring の出力はそのまま `/solve` に渡る可能性があるため厳格)のに対し、Phase 12 は該当する不正な名前を**除外して notes に記録するだけ**(推薦は表示するだけの補助情報であり、パイプラインを止める理由が無いため)。同じ原則でも、下流への影響度で対応の強さを変える判断。

## 7. マージとソート

```python
# app/services/algorithm_recommendation.py(要点)
recommendations = [_build_recommendation(s, ..., llm_rank=rank_by_name.get(s.meta.name), ...) for s in candidates]
recommendations.sort(key=lambda r: (r.llm_rank is None, r.llm_rank or 0))
```

LLM がランク付けした候補が先頭、ランクの付かなかった候補(grounding で弾かれた、またはLLM がそもそも言及しなかった)は registry 登録順のまま末尾に残る。`sort` の key は「`llm_rank is None` を第一キーにする」定石(`None` は `False`(=0)扱いになり先に来るため、ランクが付いている方が先頭に来る)。

## 8. `FakeLLM` への `ainvoke` 追加(第二の消費者)

Phase 11-3 で作った `FakeLLM`/`_FakeStructuredLLM`(`tests/fixtures/fake_llm.py`)は
同期 `invoke` しか持たなかった。Phase 12 のサービスは LangGraph を介さない素の async関数のため `llm.ainvoke(...)` を直接呼ぶ(11-3〜11-6 のノードは LangGraph が
`run_in_executor` で同期呼び出しを包むため `invoke` のままでよかった)。

```python
# tests/fixtures/fake_llm.py(追記)
async def ainvoke(self, messages: Any) -> AIMessage:  # (Phase 12)
    """invoke の非同期版(結果は同じ)。"""
    return self.invoke(messages)
```

既存の `invoke` は無変更(後方互換)。両クラス(`FakeLLM`/`_FakeStructuredLLM`)に追加する。
Phase 11 のテスト(`test_ai_graph_nodes.py` 等)は `invoke` しか使わないため無改造で
緑のまま(#12.4 のスモークで確認する)。

---

## まとめ

- `AlgorithmRecommendationService` は `VerifyService` と同じ「DB を触らない、レート制限だけ持つ」骨格。
- `select_strategy` は無変更で第二の消費者として呼ぶ。
- 候補1件・LLM失敗・grounding失敗の3ケースをそれぞれ違う強さで扱う(即返す/グレースフルデグレード/除外してnotesに記録)── 「推薦は補助機能」という一貫した方針から導かれる。
- `FakeLLM` に `ainvoke` を追加(既存 `invoke` は無変更)。

## テスト観点(`tests/unit/test_algorithm_recommendation_service.py`)

> **対象**: `AlgorithmRecommendationService.recommend`
> **ドライバ**: このテスト関数
> **スタブ**: `FakeRedis`(`RateLimiter` の incr/expire だけ)+ `FakeLLM`
> (`app.services.algorithm_recommendation.get_gemini_llm` を差し替える)。
> `select_strategy`/`get_strategies` は本物(純粋・DB 非依存なのでスタブ不要)

| ケース                                                   | 期待                                                                                          |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 候補1件(`get_strategies` をフェイクで1件に絞る)                    | LLM 未呼び出し、notes に明記、`is_rule_preferred=True`                                                |
| LLM が `["greedy", "knapsack_dp"]` の順でランク付け            | `rule_preferred="knapsack_dp"` は維持しつつ、`recommendations` は greedy→knapsack_dp→brute_force の順 |
| LLM が存在しない候補名(`"dijkstra"`)を返す                        | `recommendations` から除外、notes に理由が残る                                                         |
| `_invoke_llm` が例外を送出                                  | 例外は伝播せず、rule のみの `recommendations` + notes で返る                                              |
| `RECOMMEND_RATE_LIMIT_PER_HOUR=1` で2回連続 `recommend()` | 2回目は `RateLimitExceededError`。`bypass_rate_limit=True` なら3回連続でも通る                           |

`uv run pytest tests/unit/test_algorithm_recommendation_service.py` /
`uvx pyright app/services/algorithm_recommendation.py tests/fixtures/fake_llm.py
tests/unit/test_algorithm_recommendation_service.py`。

---

次章([Phase-12-3](./Phase-12-3.md))では、作業単位 12-3 ── `POST /api/v1/algorithms/recommend`
のルート配線を実装する。
