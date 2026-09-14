# Phase 10-3: 二分探索による閾値発見(作業単位 10-3)

## この章のゴール

README「Sensitivity Analysis」を実装する。単純な値スイープ(全件評価)に加えて、
**「答えを二分探索する」**(competitive programming で言う *binary search on the answer*)
パターンで、単調な指標について条件を満たす最小のパラメータを O(log n) 回の solve で
見つける `find_threshold` を実装し、`run_simulation` に配線する。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/threshold_search.py`
(新規)、`app/schemas/simulation.py`(`SensitivitySpec`/`SensitivityResult` を追記)、`app/services/simulation.py`(`_set_path`・`_run_sensitivity`・`run_simulation` への配線を追記)、`tests/unit/test_threshold_search.py`(新規)。

---

## 1. 「値を探す」二分探索 vs 「答えを探す」二分探索

Phase 1 の `search/binary_search.py::binary_search` は、**ソート済みの列**から target と等しい要素を探す ── 「値の探索」。ここでの `find_threshold` は、**呼び出し側が渡す整数パラメータ**に対して `evaluate(param)` が単調に変化することを前提に、条件を満たす最小のパラメータを探す ── 「答えを二分探索する」。両者は同じ分割統治の骨格(区間を毎回半分に絞る)を共有するが、探索対象が「既にある列の要素」か「呼び出しごとに計算する値」かが違う。

```python
# app/algorithms/optimization/threshold_search.py(全文。registry には載せない素の純粋関数)
def find_threshold(
    low: int, high: int, evaluate: Callable[[int], float], *, target: float,
    mode: Literal["at_most", "at_least"] = "at_most",
) -> int | None:
    if low > high:
        raise ValueError(f"low({low}) must be <= high({high})")
    satisfies = (lambda v: v <= target) if mode == "at_most" else (lambda v: v >= target)

    if not satisfies(evaluate(high)):
        return None   # 単調性の前提のもとでは、high でも満たさなければ範囲内に答えは無い

    lo, hi = low, high
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if satisfies(evaluate(mid)):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**前提**: `evaluate` は `[low, high]` 上で単調(`mode="at_most"` なら非増加、`"at_least"` なら非減少)。**前提が崩れる入力では、実際の境界とは異なる値を返しうる**(単調性の検証は
`evaluate` を全件呼ぶのと同じコストなので、ここでは検証しない ── 呼び出し側が前提を保証する)。テストでこの「前提が崩れたときの挙動」も明示する(§テスト観点)。

**複雑さ**: 全件スイープは O(high−low) 回の `evaluate`。こちらは O(log(high−low)) 回。
`evaluate` 1 回が「1 回の solve」に相当する Phase 10 では、この差がそのまま「シナリオを何回実行するか」に直結する ── これが本章の核。

---

## 2. `_set_path` ── ドット区切りパスから override を作る

`SensitivitySpec.field_path`(例: `"data.resource_capacity"`)から、`apply_overrides` に渡すoverride dict を組み立てる小さなヘルパ:

```python
# app/services/simulation.py(要点)
def _set_path(path: str, value: Any) -> dict[str, Any]:
    """'data.resource_capacity' → {"data": {"resource_capacity": value}}"""
    result: Any = value
    for key in reversed(path.split(".")):
        result = {key: result}
    return result
```

`field_path` は **dict キーのみのドット区切り**に限る(`data.vehicles.0.capacity_weight` のような list の添字は対象外)── `apply_overrides` の merge patch は list を丸ごと置換するため、要素単位の上書きには向かない(Phase 10-1 §1)。この制約の下で意味のある感度分析の対象は、`ProjectData.resource_capacity`(`int | None`。list に入っていない top-level スカラー)のような「list に入っていないドメインの数値フィールド」に絞られる。

---

## 3. `_run_sensitivity` ── 二分探索と `SimulationService` の橋渡し

```python
# app/services/simulation.py(要点)
async def _run_sensitivity(problem, algorithm, timeout_seconds, spec) -> SensitivityResult | None:
    evaluated: dict[int, float] = {}

    def _evaluate(param: int) -> float:
        merged = apply_overrides(problem, _set_path(spec.field_path, param))
        _, metrics, _ = _solve_once(merged, algorithm)
        value = metrics[spec.target_metric]
        evaluated[param] = value   # 二分探索が実際に訪れた点だけを記録する
        return value

    budget = timeout_seconds * max(1, (spec.high - spec.low + 1).bit_length())
    try:
        threshold = await asyncio.wait_for(
            asyncio.to_thread(find_threshold, spec.low, spec.high, _evaluate, target=spec.threshold, mode=spec.mode),
            budget,
        )
    except (*_SCENARIO_ERRORS, KeyError):
        return None   # MVP の割り切り: 破綻したら比較結果(scenarios)は返しつつ諦める
    return SensitivityResult(threshold_value=threshold, evaluated=evaluated)
```

`find_threshold` 自体は純粋・同期で `app.domain` を一切知らない(§1 のとおり)。「ドメインを知っている `evaluate` を組み立てて渡す」のがこの関数の役目 ── アルゴリズムのプリミティブ(`algorithms/`)とオーケストレーション(`services/`)の分離がそのまま表れている。

`evaluated: dict[int, float]` に**実際に訪れた点だけ**を記録する ── 全件スイープした場合の値と対比することが、分析トラック(Phase 10-5)と UI(Phase 10-6)の両方でこの章の核(「二分探索は全件スイープより少ない solve で済む」)を可視化する材料になる。

`budget`(timeout の余裕)は `max(1, log2(high-low+1))` 回強の solve を想定して timeout を掛け算する ── 1 回の solve の timeout(`SOLVE_TIMEOUT_SECONDS`)をそのまま使うと、二分探索の複数回の solve 合計が収まらない。

**例外は `SimulationResult.sensitivity = None` に落とす**(全体を失敗させない)── 感度分析中に無効なシナリオ(override が invalid)に当たった場合、比較結果(`scenarios`)は返しつつ感度分析だけ諦める。単純だが、README の主眼(比較結果を出すこと)を損なわない割り切り。

`run_simulation` への配線は 1 行:

```python
# app/services/simulation.py(run_simulation の末尾に追記)
sensitivity = None
if request.sensitivity is not None:
    sensitivity = await _run_sensitivity(request.problem, algorithm, timeout_seconds, request.sensitivity)
return SimulationResult(base=base_result, scenarios=scenario_results, sensitivity=sensitivity)
```

---

## まとめ

- `find_threshold` は Phase 1 `binary_search`(値の探索)とは別の応用(答えを二分探索する)。
  複雑さは O(log n) 回の `evaluate` ── 全件スイープの O(n) との対比が本章の核。
- `evaluate` は同期・純粋なドメイン非依存の関数として渡す(`algorithms/` は app.domain を知らない)。ドメインを知っている `evaluate` の組み立てとタイムアウト予算の計算は`services/simulation.py` の責務。
- 単調性の前提が崩れた入力では、実際の境界と異なる値を返しうる ── テストで明示する。

## テスト観点(`tests/unit/test_threshold_search.py`)

> **対象**: `app.algorithms.optimization.threshold_search.find_threshold`
> **ドライバ**: このテスト関数
> **スタブ**: フェイクの `evaluate`(実運用では 1 回の solve に相当する重い呼び出しなので、ユニットテストでは単純な数式に差し替える ── 進行のルール #14「スタブの要否がレイヤー設計の鏡」。`evaluate` を注入可能にした設計そのものがこのテストを軽くしている)

| ケース                    | 期待                                       |
| ---------------------- | ---------------------------------------- |
| `mode="at_most"`(非増加)  | target 以下になる最小の param。呼び出し回数が全件スイープより少ない |
| `mode="at_least"`(非減少) | target 以上になる最小の param                    |
| 範囲内に条件を満たす点が無い         | `None`                                   |
| `low == high`          | その 1 点を返す                                |
| `low > high`           | `ValueError`                             |
| 単調性の前提が崩れた入力           | 決定論的だが、本来の最小点とは異なる値を返しうる(前提の限界を実演)       |

`app/services/simulation.py`(10-3 の追記分)は次章(10-4)のジョブキュー配線テストと合わせて
`tests/unit/test_simulation_service.py` の sensitivity ケースでカバーする(Phase-10-2.md 参照)。

`uv run pytest tests/unit/test_threshold_search.py tests/unit/test_simulation_service.py`。

---

次章([Phase-10-4](./Phase-10-4.md))では、作業単位 10-4 ── `run_simulation` をジョブキュー
(Phase 9-8)経由で非同期実行できるように配線し、`POST /api/v1/simulate` を新設する。
