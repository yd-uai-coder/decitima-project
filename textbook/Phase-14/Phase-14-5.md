# Phase 14-5: `ComparisonService`(作業単位 14-5)

## この章のゴール

6つの `LlmOnly*Strategy`(14-2〜14-4)と既定選択の Algorithm を同じ問題で走らせ、
README §14 の6評価軸のうち5軸を数値集計し、任意でナレーションを生成する
`ComparisonService` を実装する。**「測定そのもの」と「その説明文」で信頼性要件(リトライ・フォールバックの有無)を変える**という、この Phase 固有の設計判断がこの章の核。

**この章で作成/更新するファイル**: `app/schemas/comparison.py`・`app/services/comparison.py`
(新規)、`app/core/config.py`(改訂、レート制限フィールド追加)、
`tests/fixtures/fake_llm.py`(改訂、`structured_sequence` 追加)、
`tests/unit/test_comparison_schemas.py`・`test_comparison_service.py`(新規)。

---

## 1. API 契約(`app/schemas/comparison.py`)

```python
# app/schemas/comparison.py(新規、要点)
class ComparisonRequest(BaseModel):
    problem: OptimizationProblem
    algorithm: str | None = None  # 指定なければ rule-based 選択(select_strategy と同じ)
    llm_runs: int = Field(default=5, ge=1, le=20)  # LLM Only を再実行する回数(再現性測定)


class RunOutcome(BaseModel):
    status: str | None = None  # 例外で失敗した回は None
    metrics: dict[str, float] = Field(default_factory=dict)
    hard_violations: int = 0
    soft_violations: int = 0
    elapsed_ms: float = 0.0
    error: str | None = None  # 例外メッセージ(成功した回は None)
    structure_hash: str | None = None  # 再現性の集計用(assignments の要約ハッシュ)


class ComparisonMetrics(BaseModel):
    constraint_compliance_rate_algorithm: float
    constraint_compliance_rate_llm: float
    optimality_avg_quality_ratio_llm: float | None
    reproducibility_distinct_solutions_llm: int
    execution_time_ms_algorithm: float
    execution_time_ms_llm_median: float
    error_rate_llm: float


class ComparisonNarrative(BaseModel):
    summary: str
    constraint_compliance_note: str
    optimality_note: str
    reproducibility_note: str
    verifiability_note: str  # 6軸目「検証可能性」は数値化せずここで定性的に説明する


class ComparisonResponse(BaseModel):
    problem_type: str
    algorithm_used: AlgorithmMeta
    algorithm_result: RunOutcome
    llm_results: list[RunOutcome]
    metrics: ComparisonMetrics
    narrative: ComparisonNarrative | None = None
    notes: list[str] = Field(default_factory=list)
```

`RunOutcome` は Algorithm(1件)・LLM Only(`llm_runs` 件)の両方を同じ形で表す共通の
「1回分の実行結果」── `BenchmarkEntry`(Phase 3)と似た役割だが、`quality_ratio` の代わりに生の `metrics` を持たせる(最適性の比較は `ComparisonMetrics` 側で Algorithm と LLM を横断して計算するため、`RunOutcome` 単体には比率を持たせない)。

`structure_hash` を生の `assignments` の代わりに持たせる理由: `llm_runs` は最大20まで許容するため、6ドメインの中で最も大きい `LogisticsSolution`/`ProjectSolution` を20件分そのまま返すとレスポンスが不必要に膨らむ。再現性の集計(「何種類の構造が出たか」)にはハッシュで十分。

## 2. `ComparisonService` の骨格 ── Phase 9/10/12/13 と同じ「素の async 関数」判断

```python
# app/services/comparison.py(新規、要点)
_LLM_ONLY_STRATEGIES: dict[str, AlgorithmStrategy] = {
    "route_planning": LlmOnlyRouteStrategy(),
    "network_design": LlmOnlyNetworkStrategy(),
    "shift_scheduling": LlmOnlyShiftStrategy(),
    "travel_planning": LlmOnlyTravelStrategy(),
    "project_scheduling": LlmOnlyProjectStrategy(),
    "logistics_planning": LlmOnlyLogisticsStrategy(),
}


class ComparisonService:
    def __init__(self, redis: Redis) -> None:
        self._validation = ProblemValidationService()
        self._verification = SolutionVerificationService()
        self._rate_limiter = RateLimiter(
            redis, resource="compare",
            limits=[
                RateLimit(window_seconds=3600, max_requests=settings.COMPARE_RATE_LIMIT_PER_HOUR),
                RateLimit(window_seconds=86400, max_requests=settings.COMPARE_RATE_LIMIT_PER_DAY),
            ],
        )

    async def compare(self, *, user_id, request, bypass_rate_limit=False) -> ComparisonResponse:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))

        problem = request.problem
        self._validation.validate(problem)

        llm_strategy = _LLM_ONLY_STRATEGIES.get(problem.problem_type)
        if llm_strategy is None:
            raise NoAlgorithmError(f"no llm_only strategy for {problem.problem_type!r}")

        algorithm = select_strategy(problem, request.algorithm)
        algorithm_result = await self._run_once(algorithm, problem)
        llm_results = [await self._run_once(llm_strategy, problem) for _ in range(request.llm_runs)]

        metrics = _aggregate(problem, algorithm_result, llm_results)
        narrative = await self._narrate(problem, algorithm, algorithm_result, llm_results, metrics)

        return ComparisonResponse(
            problem_type=problem.problem_type, algorithm_used=algorithm.meta,
            algorithm_result=algorithm_result, llm_results=llm_results,
            metrics=metrics, narrative=narrative,
        )
```

`_LLM_ONLY_STRATEGIES` は `problem_type` をキーにした単純な dict ── Phase 12 の
`_ALGORITHM_DESCRIPTIONS` のような `(problem_type, name)` タプルキーは不要(このリストは`REGISTRY` と違い、1 problem_type につき1戦略しか持たないため。14-1 で触れた通り`meta.name` の衝突はそもそも起きない)。**`REGISTRY` を経由しない**(`get_strategies`/`find_strategy` を呼ばない)ことが、「本番 `/solve` の既定選択に一切影響しない」ことのコードレベルの保証になっている。

`algorithm = select_strategy(problem, request.algorithm)` は Phase 1〜11 の既存関数を無変更で呼ぶ(第n の消費者)── README 図の「Algorithm」ボックスが指すのは、常に「今の DeciTima が実際に `/solve` で使う既定選択」であるべきだから。

## 3. `_run_once` ── 「生の信頼性」を測るので握りつぶさない

```python
# app/services/comparison.py(要点)
async def _run_once(self, strategy: AlgorithmStrategy, problem: OptimizationProblem) -> RunOutcome:
    start = time.perf_counter()
    try:
        solution = await asyncio.wait_for(
            asyncio.to_thread(strategy.solve, problem), settings.SOLVE_TIMEOUT_SECONDS
        )
    except Exception as exc:  # noqa: BLE001 ── 生の信頼性を測る対象。記録して先へ進む
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.warning("comparison run failed for %s: %r", strategy.meta.name, exc)
        return RunOutcome(status=None, elapsed_ms=elapsed_ms, error=repr(exc))

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    verified = self._verification.verify(problem, solution)
    hard = sum(1 for v in verified.violations if v.severity == "hard")
    soft = sum(1 for v in verified.violations if v.severity == "soft")
    return RunOutcome(
        status=verified.status, metrics=_objective_metrics(problem, verified),
        hard_violations=hard, soft_violations=soft, elapsed_ms=elapsed_ms,
        structure_hash=_structure_hash(verified),
    )
```

`asyncio.wait_for(asyncio.to_thread(strategy.solve, problem), settings.SOLVE_TIMEOUT_SECONDS)`
は `BenchmarkService`(Phase 3)の `measure_call` 呼び出しと同じ骨格 ── ただし Phase 14 は`measure_call`(複数回実行して中央値・四分位を取る、Phase 3 の numpy 集計)をそのまま使わない。理由: `measure_call` は「同じ入力に対して毎回同じ結果を返す純粋関数」を前提に最後の1回の結果を代表値として返す(Phase 3 のコメント参照)。LLM Only はこの前提(決定論性)を満たさない ── **`llm_runs` 回のそれぞれが独立した観測データ**であり、「代表値1つ」に潰してはいけない。そのため `_run_once` を自前で書き、`llm_runs` 回ループで呼ぶ(Algorithm 側は決定論的なので1回で十分 ── この非対称自体が README の「再現性」を測るという目的に対応する)。

Structuring(`MAX_GENERATION_ATTEMPTS = 3` でリトライ)・Recommendation/Explanation
(LLM失敗時に代替結果を返す)とは逆に、**ここでは例外を握りつぶさず `RunOutcome` に記録するだけ**。理由は導入の §3.3 の表の通り ── 「生の信頼性を測る」という目的そのものが、成功率を人為的に底上げする仕組みと両立しないため。

## 4. `_objective_metrics` ── 目的値は `metrics` と `assignments` のどちらにあるか

Phase 14-3 で触れた通り、目的の対象値(`total_weight`/`total_value`/`makespan`/
`total_distance`)は route/network/travel/project/logistics では **`assignments` 側の
フィールド**にあり(`CandidateSolution.metrics` には乗らない)、shift だけは
`structural_verify` が `assignment_metrics()` で `metrics` に積む(Phase 6-1)。
「最適性」を全ドメイン共通で集計するには、この非対称を吸収するヘルパが要る:

```python
# app/services/comparison.py(要点)
def _objective_metrics(problem: OptimizationProblem, solution: CandidateSolution) -> dict[str, float]:
    """目的の対象値を metrics に補う(route/network/travel/project/logistics は
    assignments 側のフィールドにあり、metrics には乗らないため)。"""
    resolved = dict(solution.metrics)
    for o in problem.objectives:
        if o.target in resolved:
            continue
        value = getattr(solution.assignments, o.target, None)
        if isinstance(value, int | float):
            resolved[o.target] = float(value)
    return resolved
```

> **設計の発見**: 当初は `verified.metrics` をそのまま `RunOutcome.metrics` に詰めていたが、route を使ったサービステスト(`test_compare_all_llm_runs_match_algorithm`)で
> `optimality_avg_quality_ratio_llm` が常に `None` になる不具合が overlay 検証で発覚した。
> 原因は上記の非対称 ── `RouteSolution.total_weight` は `metrics` に無い。`_run_once` の中で `_objective_metrics` を挟むことで解消した(進行のルール #9 のとおり、検証で見つけた
> 問題は反映してから次に進む)。**「最適性を集計する」という Phase 14 で初めて生まれた要求が、既存6ドメインの metrics/assignments の置き場の違いを初めて可視化した**
> 例(進行のルール #17 の「今駆動している実在の消費者」がここでも効いている)。

## 5. `_aggregate` ── 5軸の集計。分母の選び方が非自明

```python
# app/services/comparison.py(要点)
def _aggregate(problem, algorithm_result, llm_results) -> ComparisonMetrics:
    attempts = len(llm_results)
    ok = [r for r in llm_results if r.error is None]
    valid = [r for r in ok if r.status == "valid"]

    target = problem.objectives[0].target if problem.objectives else None
    sense = problem.objectives[0].sense if problem.objectives else "minimize"
    algo_value = algorithm_result.metrics.get(target) if target else None

    ratios: list[float] = []
    if target is not None and algo_value not in (None, 0):
        for r in valid:
            v = r.metrics.get(target)
            if v is None:
                continue
            if sense == "minimize":
                ratios.append(v / algo_value)
            elif v != 0:
                ratios.append(algo_value / v)

    distinct = len({r.structure_hash for r in ok if r.structure_hash is not None})

    return ComparisonMetrics(
        constraint_compliance_rate_algorithm=1.0 if algorithm_result.status == "valid" else 0.0,
        # 分母は「成功した試行数」(ok)── 例外で落ちた回は「制約を破った」のではなく
        # 「解自体を出せなかった」ので、遵守率でなく error_rate_llm 側に反映する。
        constraint_compliance_rate_llm=(len(valid) / len(ok)) if ok else 0.0,
        optimality_avg_quality_ratio_llm=(sum(ratios) / len(ratios)) if ratios else None,
        reproducibility_distinct_solutions_llm=distinct,
        execution_time_ms_algorithm=algorithm_result.elapsed_ms,
        execution_time_ms_llm_median=(
            median([r.elapsed_ms for r in llm_results]) if llm_results else 0.0
        ),
        error_rate_llm=((attempts - len(ok)) / attempts) if attempts else 0.0,
    )
```

- **`optimality_avg_quality_ratio_llm` は 1.0 = Algorithm と同等**、値が大きいほど LLM が劣ることを表す(`BenchmarkService._annotate_quality_ratio` の「値 / 最良値」と同じ発想を「最良値 = Algorithm の値」に固定した形。minimize なら `llm値 / algo値`、maximize なら`algo値 / llm値` ── どちらも「LLM が悪化するほど比が大きくなる」向きに揃える)。
- **再現性(`distinct`)は `ok`(成功した試行)を分母にし、`valid` に絞らない** ──
  「妥当性」と「再現性」は独立した指標という設計判断。invalid な解を繰り返し返す LLM も、常に同じ invalid な解を返すなら再現性は高い(distinct=1)。
- **`ratios` の計算対象は `valid` に限る** ── invalid な解の metrics を最適性の平均に
  混ぜると、"制約を守っていないのにたまたま良い数値" が最適性を過大評価してしまう。

> **写経の罠(2つ目)**: `constraint_compliance_rate_llm` の分母を最初 `attempts`
> (全試行数、エラー含む)にしていたところ、`test_compare_counts_llm_exceptions_as_errors`
> (2回中1回エラー、残り1回は valid)で `0.5` が返り、期待値 `1.0`(エラーを除いた
> 「成功した試行のうちの遵守率」)と食い違った。`ComparisonMetrics` docstring の「valid件数 / 成功した試行数」という定義に忠実に `len(ok)` へ直して解消 ── **コメントに書いた仕様とコードの実装がズレるのは、テストが仕様を具体的な数値で固定して初めて検出できる**、という進行のルール #14(テストダブルの要否がレイヤー設計の鏡)と同じ精神の実例。

## 6. `_structure_hash` ── 再現性の集計に使う要約

```python
# app/services/comparison.py(要点)
def _structure_hash(solution: CandidateSolution) -> str:
    payload = json.dumps(solution.assignments.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]
```

`assignments`(判別可能ユニオンの具象型、例 `RouteSolution`)を JSON 化してハッシュ化するだけ ── ドメインごとの分岐を書かない(`model_dump(mode="json")` はどの具象型でも同じインターフェースで呼べるため、Pydantic の多態性をそのまま使う)。

## 7. ナレーション生成 ── ここだけ Phase 12/13 と同じグレースフルデグレード

```python
# app/services/comparison.py(要点)
async def _narrate(self, problem, algorithm, algorithm_result, llm_results, metrics) -> ComparisonNarrative:
    prompt = _narrate_prompt(problem, algorithm, algorithm_result, llm_results, metrics)
    try:
        llm = get_gemini_llm(temperature=0).with_structured_output(ComparisonNarrative)
        result = await llm.ainvoke([HumanMessage(content=prompt)])
        return cast(ComparisonNarrative, result)
    except Exception as exc:  # noqa: BLE001 ── ナレーションは補助。失敗しても数値結果は返す
        logger.warning("comparison narrative LLM call failed: %r", exc)
        return _fallback_narrative(metrics)
```

`_narrate_prompt` は Phase 13 `_explain_prompt` と同じ原則 ── **検証済みの数値(metrics/violations/実測値)をそのまま渡し、LLM には narrate だけをさせる**(README「LLM に最適解を計算させない」の徹底)。`ainvoke` を使うのは、この呼び出しだけが
`ComparisonService.compare`(async メソッド)から直接呼ばれ、`asyncio.to_thread` を
経由しないため(Phase 12/13 と同じ判断)。

`_fallback_narrative` は Phase 13 `_fallback_response` と同型 ── metrics の数値を
そのまま文字列化するだけの機械的な要約。

## 8. `FakeLLM` の拡張 ── N回の呼び出しで異なる結果・例外を返す

```python
# tests/fixtures/fake_llm.py(改訂、要点)
class FakeLLM:
    def __init__(
        self, content=None, structured=None,
        structured_sequence: list[BaseModel | Exception] | None = None,  # (Phase 14)
    ) -> None:
        ...
        self._structured_sequence = structured_sequence

    def with_structured_output(self, schema):
        self.structured_output_calls.append(schema)
        return _FakeStructuredLLM(self._structured, self._structured_sequence)


class _FakeStructuredLLM:
    def __init__(self, structured, sequence=None):
        self._structured = structured
        self._sequence = sequence

    def invoke(self, _messages):
        if self._sequence is not None:
            item = self._sequence.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return self._structured
```

`structured=` のみを渡す既存の呼び出し(Phase 11〜13 のテスト)は無改造で動く
(`_sequence` が `None` のときは従来どおり固定値を返す)。`structured_sequence` を使う
最初の消費者は本章の `test_compare_mixed_valid_and_lying_runs`/
`test_compare_counts_llm_exceptions_as_errors`(進行のルール #17)。

## 9. レート制限フィールド

```python
# app/core/config.py(追記)
# (Phase 14) LLM vs Algorithm Comparison のレート制限(単位時間あたりの上限回数)。
# 1 リクエストで LLM を最大 llm_runs(既定5、上限20)回呼ぶため Benchmark と同程度に絞る
COMPARE_RATE_LIMIT_PER_HOUR: int = 10
COMPARE_RATE_LIMIT_PER_DAY: int = 50
```

`BENCHMARK_RATE_LIMIT_PER_HOUR`(Phase 3)と同じ値 ── 1リクエストが複数回の重い処理(Benchmark は複数アルゴリズム、Compare は複数回の LLM 呼び出し)を伴う点が共通するため。

---

## まとめ

- `ComparisonService` は Phase 9/10/12/13 と同じ「素の async 関数」判断だが、
  `measure_call`(Phase 3)を再利用せず `_run_once` を自前で書く ── LLM Only の
  非決定論性が「複数回実行して代表値1つに潰す」という `measure_call` の前提と
  相容れないため。
- 「測定」にはリトライもフォールバックも無し、「ナレーション」にはある ── 同じ
  Phase の中で信頼性要件を意図的に変える設計判断。
- `_objective_metrics`(metrics/assignments の非対称吸収)と `_aggregate` の分母選択(`ok` 基準)は、どちらもテスト駆動で発見・修正した(進行のルール #9)。

## テスト観点(`tests/unit/test_comparison_schemas.py` / `test_comparison_service.py`)

> **対象**: `ComparisonRequest`/`RunOutcome`/`ComparisonMetrics`(スキーマ、純粋)/
> `ComparisonService.compare`(サービス)
> **ドライバ**: このテスト関数
> **スタブ**: `FakeRedis`(`RateLimiter` の incr/expire だけ)+ `FakeLLM`
> (`app.algorithms.llm.route_llm.get_gemini_llm` と `app.services.comparison.get_gemini_llm`
> をそれぞれ差し替える ── 前者は LLM Only 経路、後者はナレーション生成)。Algorithm 経路は
> 実装済みの `select_strategy`(dijkstra)をそのまま使う ── スタブ不要(純粋・既存)。

| ケース                                               | 期待                                                                   |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| LLM が毎回 Algorithm と同じ正しい解を返す                      | 制約遵守率100%/100%、`optimality≈1.0`、`distinct=1`、`error_rate=0`          |
| 3回中1回だけ `total_weight` を偽った解                      | `constraint_compliance_rate_llm ≈ 2/3`、`distinct=2`                  |
| 2回中1回が例外                                          | `error_rate_llm=0.5`、`constraint_compliance_rate_llm` はエラーを除いた1/1で計算 |
| ナレーション用 LLM 呼び出しが失敗                               | 数値結果はそのまま返り、`narrative.summary` に機械的フォールバック文言                        |
| `COMPARE_RATE_LIMIT_PER_HOUR=1` で2回連続 `compare()` | 2回目は `RateLimitExceededError`                                        |

```bash
uv run pytest tests/unit/test_comparison_schemas.py tests/unit/test_comparison_service.py
uvx pyright app/schemas/comparison.py app/services/comparison.py app/core/config.py tests/fixtures/fake_llm.py
```

overlay 検証: `test_comparison_schemas.py` **4 passed**、`test_comparison_service.py`
**5 passed**。

---

次章([Phase-14-6](./Phase-14-6.md))では、作業単位 14-6 ──
`POST /api/v1/compare` のルート配線 + e2e を実装する。
