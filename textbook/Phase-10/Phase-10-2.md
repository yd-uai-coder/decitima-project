# Phase 10-2: `SimulationService.run_simulation`(作業単位 10-2)

## この章のゴール

前章の `apply_overrides` を使って、base problem + シナリオ群を**実際に解いて**比較結果を組み立てる。Phase 3 `BenchmarkService` と対称な設計であること、そして
「1 シナリオの破綻が全体を止めない」ことを実装する。

**この章で更新するファイル**: `app/services/simulation.py`(前章の続き。`_solve_once` /
`_run_scenario` / `_run_one_scenario` / `run_simulation` を追加)。
新規: `tests/unit/test_simulation_service.py`。

---

## 1. Phase 3 `BenchmarkService` との対称性

|             | Phase 3 `BenchmarkService`    | Phase 10 `SimulationService`              |
| ----------- | ----------------------------- | ----------------------------------------- |
| 何を固定し、何を振るか | 問題を固定、**アルゴリズム**を振る           | アルゴリズムを固定、**問題**を振る                       |
| 問い          | どのアルゴリズムが速い/良いか               | 条件を変えたら結果がどう変わるか                          |
| 永続化         | `benchmark_runs` テーブルに保存      | **無し**(結果はジョブキューの `Job.payload` に保持。10-4) |
| 依存          | `session`(DB)/ `redis`(レート制限) | **無し** ── 純粋な async 関数                    |

`BenchmarkService` はサービス層の**トランザクション境界**(永続化・レート制限)を持つクラスだが、`SimulationService`(実体は `run_simulation` という 1 関数)は**それらを持たない**。
レート制限は投入側(`JobService.enqueue_simulation`、10-4)が既に済ませており、`run_simulation`はジョブキューのワーカープロセス内から呼ばれる純粋なオーケストレーションに徹する(`solve_job` が `SolveService.solve` を呼ぶのと対応する構造だが、`SimulationService` 自体はクラスにせず素の関数で足りる ── 状態を持つ理由が無いため)。

---

## 2. 1 回の solve をまとめる `_solve_once`

```python
# app/services/simulation.py(要点)
def _solve_once(problem: OptimizationProblem, algorithm: str | None) -> tuple[SolutionStatus, dict[str, float], str]:
    """Validation → アルゴリズム選択 → solve → Verification を1回通す(同期・純粋)。"""
    _validation.validate(problem)
    strategy = select_strategy(problem, algorithm)
    raw = strategy.solve(problem)
    verified = _verification.verify(problem, raw)
    return verified.status, verified.metrics, strategy.meta.name
```

`SolveService.solve`(Phase 1)のライフサイクル(a)〜(e)から、レート制限(a)と永続化(f)/(g)を除いた部分そのもの。永続化を持たない理由は §1 のとおり。`_validation` / `_verification` はモジュールレベルでインスタンス化する(状態を持たないサービスなので、呼び出しごとに作り直す必要が無い)。

**戻り値の型**に注意 ── `SolutionStatus`(`Literal["valid","invalid","infeasible"]`、
`domain/solutions/solution.py`)を使う。ここを素の `str` にすると、`ScenarioResult(status=...)`に渡すときに pyright が `Literal` を要求してエラーになる(実際に一度そうなり、`str` から`SolutionStatus` に直した。写経の罠 ── 戻り値の型注釈を素の `str` にしない)。

---

## 3. timeout 監視と「1 件破綻しても続行する」ループ

```python
# app/services/simulation.py(要点)
async def _run_scenario(problem, algorithm, timeout_seconds):
    return await asyncio.wait_for(asyncio.to_thread(_solve_once, problem, algorithm), timeout_seconds)


async def _run_one_scenario(problem, scenario, algorithm, timeout_seconds) -> ScenarioResult:
    try:
        merged = apply_overrides(problem, scenario.overrides)
        status, metrics, algo_name = await _run_scenario(merged, algorithm, timeout_seconds)
    except _SCENARIO_ERRORS as exc:
        return ScenarioResult(label=scenario.label, status="invalid_scenario", error=str(exc))
    return ScenarioResult(label=scenario.label, status=status, metrics=metrics, algorithm_name=algo_name)
```

`_SCENARIO_ERRORS` は「1 件だけ invalid として拾う」対象の例外の一覧 ──
`pydantic.ValidationError` / `ValueError`(`apply_overrides` 由来)、
`ProblemValidationError` / `InfeasibleProblemError`(Semantic Validation 由来)、
`NoAlgorithmError`(固定したアルゴリズムがこの override では該当しない)、
`TimeoutError`(solve が長すぎる)。README「どの条件なら、どの選択をするべきか」を支援するという Phase 10 の目的そのものが、「一部のシナリオが無効/実行不能である」という結果を**それ自体 1 つの有用な情報**として扱う設計を要求する ── だから例外を伝播させて全体を止めるのではなく、1 件だけ `invalid_scenario` として記録して他のシナリオは続行する。

> パラメータ名を `timeout` でなく `timeout_seconds` にしている点に注意 ── `ruff` の`flake8-async`(ASYNC109)が「`async def` の引数に `timeout` という名前を使うと`asyncio.timeout()` コンテキストマネージャを使うべき」と警告するため、既存`SolveRequest.timeout_seconds` と同じ命名に揃えた(挙動は変えず lint を通す)。

---

## 4. `run_simulation`(base + scenarios)

```python
# app/services/simulation.py(要点。sensitivity 部分は 10-3 で追加)
async def run_simulation(request: SimulationRequest, *, timeout_seconds: float | None = None) -> SimulationResult:
    timeout_seconds = timeout_seconds or request.timeout_seconds or settings.SOLVE_TIMEOUT_SECONDS

    base_status, base_metrics, base_algorithm = await _run_scenario(
        request.problem, request.algorithm, timeout_seconds
    )
    algorithm = request.algorithm or base_algorithm   # 全シナリオに固定
    base_result = ScenarioResult(label="base", status=base_status, metrics=base_metrics, algorithm_name=base_algorithm)

    scenario_results = [
        await _run_one_scenario(request.problem, scenario, algorithm, timeout_seconds)
        for scenario in request.scenarios
    ]
    return SimulationResult(base=base_result, scenarios=scenario_results, sensitivity=None)
```

`algorithm = request.algorithm or base_algorithm` が「アルゴリズム固定」の核心 ── base を自動選択で解いた**その結果の名前**を、以降の全シナリオの `select_strategy` に明示的に渡す。
これにより、シナリオごとに違うアルゴリズムが選ばれて比較が歪む(例: 負の重みを持つようにoverride したら route の既定選択が `bellman_ford` に切り替わる、等)ことを避ける。ただしoverride 後の問題がその固定アルゴリズムに対応していない場合は `NoAlgorithmError` が飛び、`_run_one_scenario` が `invalid_scenario` として拾う ── それ自体が「この条件ではこのアルゴリズムは使えない」という有用な結果になる。

---

## まとめ

- `SimulationService`(実体は `run_simulation`)は Phase 3 `BenchmarkService` と対称だが、永続化を持たない素の async 関数。
- 1 シナリオの破綻は例外にせず `status="invalid_scenario"` として記録し、他のシナリオは続行する。
- アルゴリズムは base の自動選択結果を全シナリオに固定し、フェアな比較にする。

## テスト観点(`tests/unit/test_simulation_service.py`)

> **対象**: `app.services.simulation.run_simulation`
> **ドライバ**: このテスト関数(pytest-asyncio)
> **スタブ不要** ── Validation / アルゴリズム選択 / 各 strategy.solve / Verification は
> すべて本物(純粋)。Phase 3 `BenchmarkService` のテストと同じ理由(進行のルール #14)

| ケース                    | 期待                                      |
| ---------------------- | --------------------------------------- |
| override 無しのシナリオ       | base と同じ metrics                        |
| goal を変えるなどの実 override | base と異なる metrics                       |
| 存在しないノードへの override    | 該当シナリオだけ `invalid_scenario`、他のシナリオは続行   |
| algorithm 未指定          | base の自動選択結果(例: `dijkstra`)が全シナリオに固定される |

`uv run pytest tests/unit/test_simulation_service.py`。

---

次章([Phase-10-3](./Phase-10-3.md))では、作業単位 10-3 ── Sensitivity Analysis に
二分探索を応用した `find_threshold` を実装し、`run_simulation` に配線する。
