# Phase 13-2: `SolutionExplanationService`(作業単位 13-2)

## この章のゴール

永続化済みの `Solution`(id 指定)を読み取り、README §13 の説明対象5項目を LLM に narrate
させる `SolutionExplanationService` を実装する。「他候補との違い」を再 solve せずに組み立てる
方法と、LLM 失敗時のフォールバックの設計がこの章の核。

**この章で作成/更新するファイル**: `app/services/explanation.py`(新規)、
`app/core/config.py`(改訂、レート制限フィールド追加)。

---

## 1. 全体の流れ

```python
# app/services/explanation.py(要点)
class SolutionExplanationService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._read = OptimizationReadService(session)
        self._rate_limiter = RateLimiter(
            redis, resource="explain",
            limits=[
                RateLimit(window_seconds=3600, max_requests=settings.EXPLAIN_RATE_LIMIT_PER_HOUR),
                RateLimit(window_seconds=86400, max_requests=settings.EXPLAIN_RATE_LIMIT_PER_DAY),
            ],
        )

    async def explain(self, solution_id, *, user_id, bypass_rate_limit=False) -> ExplanationResponse:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))

        solution_row = await self._read.get_solution(solution_id, user_id=user_id)
        problem_row = await self._read.get_problem(solution_row.problem_id, user_id=user_id)
        candidate = CandidateSolution.model_validate(solution_row.payload)
        problem = OptimizationProblem.model_validate(problem_row.payload)
        alternatives_text = _alternatives_text(problem.problem_type, candidate.produced_by.name)

        try:
            llm_result = await self._invoke_llm(problem, candidate, alternatives_text)
        except Exception as exc:
            logger.warning("solution explanation LLM call failed: %r", exc)
            return _fallback_response(solution_id, problem, candidate)

        return ExplanationResponse(
            solution_id=solution_id, problem_type=problem.problem_type,
            algorithm_name=candidate.produced_by.name, **llm_result.model_dump(),
        )
```

`AlgorithmRecommendationService`(Phase 12)と同じ骨格 ──`__init__` で `RateLimiter` を組み立て、
メソッド冒頭で `enforce`。ただし Phase 12 は DB を一切触らなかったのに対し、Phase 13 は
`OptimizationReadService`(Phase 1、既存)経由の**読み取り**を持つ(このサービス自体は書き込まない
── キックオフ確認の3点目「永続化しない」)。

## 2. レート制限フィールドの追加(`__init__` を書いたら真っ先に足す)

```python
# app/core/config.py(追記)
# (Phase 13) Result Explanation のレート制限(単位時間あたりの上限回数)
EXPLAIN_RATE_LIMIT_PER_HOUR: int = 20
EXPLAIN_RATE_LIMIT_PER_DAY: int = 100
```

Phase 12 の `RECOMMEND_RATE_LIMIT_PER_HOUR` と全く同じ形。この設定を足さずに
`SolutionExplanationService` をインスタンス化すると `AttributeError` になる(Phase 11-7・
Phase 12-2 で繰り返し踏まれた写経漏れと同じ罠)。`__init__` を書いたその場で足すこと。

## 3. 永続化済みデータの読み取り ── 既存 `OptimizationReadService` を無変更で再利用

```python
# app/services/explanation.py(要点)
solution_row = await self._read.get_solution(solution_id, user_id=user_id)
problem_row = await self._read.get_problem(solution_row.problem_id, user_id=user_id)
candidate = CandidateSolution.model_validate(solution_row.payload)
problem = OptimizationProblem.model_validate(problem_row.payload)
```

`OptimizationReadService.get_solution`/`get_problem`(Phase 1、`app/api/routes/solutions.py`
の `GET /solutions/{id}` が既に使っている)を**第三の消費者**として無変更で呼ぶ。所有者スコープ
(他ユーザーの解は `NotFoundError` → 404)もここでまとめて効く ── Phase 13 が独自に認可判定を
書く必要はない。`Solution.payload`/`Problem.payload` は生の `dict` なので、`CandidateSolution`/
`OptimizationProblem` に `model_validate` して型付きで扱う(`GET /solutions/{id}` は逆に
`payload: dict` のまま返す ── クライアント側での再解釈を前提にした設計。Phase 13 はサーバー側
でこの dict を型付きに戻して LLM プロンプトを組み立てる必要があるため、ここで初めて
`model_validate` する)。

## 4. 「他候補との違い」── registry を引き直さず辞書を絞るだけ

```python
# app/services/explanation.py(要点)
def _alternatives_text(problem_type: str, used_name: str) -> str:
    """採用アルゴリズム以外の、同じ problem_type の候補の説明を並べる(比較材料)。"""
    others = {
        name: desc
        for (pt, name), desc in ALGORITHM_DESCRIPTIONS.items()
        if pt == problem_type and name != used_name
    }
    if not others:
        return "他に登録された候補アルゴリズムはありません。"
    return "\n".join(f"- {name}: {desc}" for name, desc in others.items())
```

Phase 12 の `AlgorithmRecommendationService._recommend_prompt` は `get_strategies(problem_type)`
で registry から `AlgorithmStrategy` オブジェクトを引き直していたが、Phase 13 は
`AlgorithmStrategy` そのもの(`time_complexity` 等)を必要としない ──
「比較材料としての説明文」さえあればよいため、`ALGORITHM_DESCRIPTIONS` の辞書キーを
`problem_type` でフィルタするだけで済む。**registry への依存(`app.algorithms.registry` の
import)が一切無い** ── キックオフ確認の2点目(「他アルゴリズムを再 solve しない」)の直接的な
帰結であり、Phase 12 より単純な実装になる。

## 5. プロンプト ── LLM には narrate だけをさせる

```python
# app/services/explanation.py(要点)
def _explain_prompt(problem, candidate, alternatives_text) -> str:
    violations_text = "\n".join(
        f"- [{v.severity}] {v.constraint_kind}: {v.message}" for v in candidate.violations
    ) or "違反なし"
    metrics_text = ", ".join(f"{k}={v}" for k, v in candidate.metrics.items()) or "(metrics なし)"
    return (
        f"次の最適化問題(problem_type={problem.problem_type})に対して"
        f"「{candidate.produced_by.name}」アルゴリズムが返した解を、利用者向けに日本語で説明してください。\n\n"
        f"採用アルゴリズム: {candidate.produced_by.name}({describe_algorithm(...)})\n"
        f"解のステータス: {candidate.status}\n"
        f"metrics: {metrics_text}\n"
        f"制約違反:\n{violations_text}\n"
        f"目的: {[o.target for o in problem.objectives]}\n\n"
        f"他の候補アルゴリズム:\n{alternatives_text}"
    )
```

`metrics`/`violations` は Verification が既に検証済みの事実としてそのままプロンプトに渡す ──
LLM に「並べ替え・計算」をさせず「説明」だけをさせる(README「LLM に最適解を計算させない」の
徹底。Phase 12 の `_recommend_prompt` も同じ原則だったが、Phase 13 では「検証済みの数値を
一切改変せず伝える」という形でさらに直接的に効く)。

## 6. LLM 呼び出しの失敗 ── 「ナラティブが価値そのもの」なので機械的フォールバックにする

```python
# app/services/explanation.py(要点)
def _fallback_response(solution_id, problem, candidate) -> ExplanationResponse:
    metrics_text = ", ".join(f"{k}={v}" for k, v in candidate.metrics.items()) or "(metrics なし)"
    violations_text = "; ".join(
        f"[{v.severity}] {v.message}" for v in candidate.violations
    ) or "違反なし"
    return ExplanationResponse(
        solution_id=solution_id, problem_type=problem.problem_type,
        algorithm_name=candidate.produced_by.name,
        why_this_solution=f"metrics: {metrics_text}",
        key_constraints=violations_text,
        algorithm_rationale=describe_algorithm(problem.problem_type, candidate.produced_by.name),
        alternatives_comparison="LLM 呼び出しに失敗したため比較文は生成されていません",
        improvement_notes="LLM 呼び出しに失敗したため改善提案は生成されていません",
        notes=["LLM 説明生成に失敗したため、機械的な要約のみ返しています"],
    )
```

Phase 12 は LLM が失敗しても「ルールのみの推薦」という**別の、それ自体価値のある応答**を返せた
(rule-based selection は元々 LLM と独立に機能する)。Phase 13 の Result Explanation は
「narrate すること」自体が価値なので、LLM が失敗すると代わりに narrate できるものが無い。
そこで `_fallback_response` は**検証済みの生データ(metrics/violations)をそのまま文字列化する
だけ**の機械的な要約にする ── ナラティブは失うが、solve/verify が検証した事実そのものは
正確に伝える。「補助機能だから静かに失敗してよい」と「原因が分からなくなってよい」は別の話
(Phase 11-8 の教訓)なので `logger.warning` は必ず残す(Phase 12 と同じパターン)。

---

## まとめ

- `SolutionExplanationService` は `AlgorithmRecommendationService` と同じ「レート制限だけ
  持つ、それ自体は書き込まない」骨格だが、`OptimizationReadService` 経由の**読み取り**を持つ
  点が異なる。
- 「他候補との違い」は `ALGORITHM_DESCRIPTIONS` を `problem_type` でフィルタするだけ ──
  registry への依存が無く、Phase 12 より単純。
- LLM 失敗時のフォールバックは「ルールのみで返す」(Phase 12)ではなく「metrics/violations
  をそのまま文字列化する」(Phase 13)── 機能の性質(ナラティブ自体が価値かどうか)で
  フォールバックの設計を変える判断。

## テスト観点(`tests/unit/test_explanation_service.py`)

> **対象**: `SolutionExplanationService.explain`
> **ドライバ**: このテスト関数
> **スタブ**: `FakeRedis`(`RateLimiter` の incr/expire だけ)+ `FakeLLM`
> (`app.services.explanation.get_gemini_llm` を差し替える)。永続化済みの Problem/Solution は
> `SolveService.solve`(Phase 1、無変更)で実際に1件作る ── フェイクの `CandidateSolution` を
> 手組みするより、実データで説明サービスを検証できる(`OptimizationReadService` はスタブ不要
> ── 対象が実 DB セッションで完結し、外部 API を呼ばないため)。

| ケース | 期待 |
| --- | --- |
| LLM が5項目を返す | `result.algorithm_name`/`why_this_solution` 等に LLM の値がそのまま反映、`notes == []` |
| `_invoke_llm` が例外を送出 | 例外は伝播せず、`metrics`/`violations` から組み立てた機械的な要約 + `notes` に失敗を明記 |
| 存在しない `solution_id` | `NotFoundError` |
| `EXPLAIN_RATE_LIMIT_PER_HOUR=1` で2回連続 `explain()` | 2回目は `RateLimitExceededError`。`bypass_rate_limit=True` なら3回連続でも通る |

`uv run pytest tests/unit/test_explanation_service.py`。
`uvx pyright app/services/explanation.py tests/unit/test_explanation_service.py`。

---

次章([Phase-13-3](./Phase-13-3.md))では、作業単位 13-3 ──
`POST /api/v1/solutions/{solution_id}/explain` のルート配線を実装する。
