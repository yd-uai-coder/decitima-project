# Phase 15-2: 性能ガード実測(travel/logistics knapsack_dp)(作業単位 15-2)

## この章のゴール

`_MAX_KNAPSACK_DP_CELLS`(Phase 11-9 で導入)を実測で再検証し、`logistics_planning` に同型のガードが必要かを実測で判断する。README §15「Algorithm Benchmark」「大規模入力テスト」の中核章。**実測の過程で、Phase 11-9 のガードの前提そのものに誤りがあったことが分かった** ──
この章の核心はガード値の調整より、その発見と正しい再設計にある。

**この章で作成 / 更新するファイル**: `tests/fixtures/optimization.py`(改訂、
`build_scaled_travel_problem` に `budget`/`time_budget` 引数追加)、
`app/services/algorithm_selection.py`(改訂、閾値見直し)、
`tests/performance/test_algorithm_selection_perf.py`(新規)。

---

## 1. 発見 ── `_MAX_KNAPSACK_DP_CELLS` は `POST /benchmark` を一切保護していない

`_MAX_KNAPSACK_DP_CELLS` は `app/services/algorithm_selection.py::_preferred_name` の中だけで
参照される。この関数を呼ぶのは `select_strategy`(`POST /solve` がアルゴリズム未指定のとき使う既定選択)だけ。一方 `BenchmarkService.run()`(`POST /benchmark`)を読むと:

```python
# app/services/benchmark.py(抜粋、既存コード)
strategies = get_strategies(problem.problem_type)   # ← select_strategy を経由しない
...
solution, measurement = await asyncio.wait_for(
    asyncio.to_thread(measure_call, partial(strategy.solve, problem), request.runs),
    timeout,
)
```

`get_strategies` は `problem_type` に登録された**全ストラテジー**を返す ──
`_MAX_KNAPSACK_DP_CELLS` にもガードにも一切触れない。つまり Phase 11-9 のコメント
「/benchmark の runs=3 逐次実行でも SOLVE_TIMEOUT_SECONDS(10秒)に収まる規模に制限する」は、**このガードが実際には保護していないエンドポイントを根拠にしていた**。ガード自体が効いているのは `POST /solve` の既定選択だけで、`POST /solve` は `strategy.solve(problem)` を`measure_call` を介さず **素の1回呼び出し**で実行する(`app/services/solve.py`)。

## 2. さらなる発見 ── `measure_call` の `tracemalloc` 計装は10倍以上の見かけの遅さを生む

`POST /benchmark` が実際にどれだけ遅いかを実測するため、`knapsack_2d` を
`measure_call`(`tracemalloc` 計装あり)経由と素の `time.perf_counter`(計装なし)経由の両方で計った(cells=4,000,000、n=5・cap_a=50000・cap_b=16):

| 計測方法                                                            | 時間     |
| --------------------------------------------------------------- | ------ |
| 素の `time.perf_counter`(`POST /solve` が実際に経験する経路)                | 約1.84秒 |
| `tracemalloc` 計装あり(`measure_call`、`POST /benchmark` が実際に経験する経路) | 約20.6秒 |

**約11倍の差**。原因は `knapsack_2d` の復元用配列 `take`(`(cap_a+1)×(cap_b+1)×アイテム数`の3次元 bool リスト)への `take[a][b] = list(take[a - wa][b - wb])` という**大量の小さなリストコピー**にある ── `tracemalloc` は Python の全メモリ割り当てを個別に追跡するため、割り当て回数が多いアルゴリズムほど計装コストが跳ね上がる。

> **写経の罠**: 「実測してから直す」つもりで `measure_call` を使ってナイーブに計測すると、計測対象が実際に使う経路(`POST /solve` の素の1回呼び出し)と異なる経路
> (`POST /benchmark` の `tracemalloc` 計装あり)を混同する。本章の最初のドラフトはまさにこのミスを犯し、`test_cells_at_current_threshold_fits_benchmark_timeout` が
> 「83秒 < 10秒」で落ちた ── **意図した「怖い数字」ではなく、計測方法そのものが対象の実行経路と食い違っていたバグ**だった。対策: 何を計る前にも「この値は実際どの経路
> (`POST /solve`? `POST /benchmark`?)で使われるか」を確認する。

## 3. 結論と対応

- **`_MAX_KNAPSACK_DP_CELLS` の再計算は「素の1回呼び出し」基準でよい**(`POST /solve` が実際に経験する経路のため)。2,000,000セル(約0.86秒)→ 4,000,000セル(約1.84秒)へ緩和 ──
  `SOLVE_TIMEOUT_SECONDS`(10秒)に対して単発なら十分な余裕がある。
  Phase 11-9 の実インシデント規模(budget=100,000, n=5, time_budget=16 → cells=8,000,000)は引き続きガードされる(greedy にフォールバック)。
- **`POST /benchmark` は knapsack_dp を含む問題では別のリスクを抱えたままである** ──
  ガードは効かず、`tracemalloc` 計装により大規模な travel/logistics 問題で
  `SOLVE_TIMEOUT_SECONDS`(既定タイムアウト)を超える可能性がある。ただし
  `BenchmarkRequest.timeout_seconds` は既に呼び出し側が明示指定できる
  (`timeout = request.timeout_seconds or settings.SOLVE_TIMEOUT_SECONDS`)ため、コード変更ではなく**運用上の注意点**として記録する(`SECURITY.md` でなく本章と
  `CLAUDE.md` Notes に残す ── 性能の話であってセキュリティの話ではないため)。
  `knapsack_2d` 自体のアルゴリズム改修(`take` 配列のコピーを減らす等)は、この章の
  スコープ(ガード値の再検証)を超える実装変更であり、実在の消費者(具体的な障害)が
  無い限り見送る(進行のルール #17)。

```python
# app/services/algorithm_selection.py(改訂)
# (Phase 11-9)
# knapsack_dp は O(places数×floor(budget)×floor(time_budget)) の擬多項式。
# 実測(cap_a=15000,cap_b=16,n=5→0.74秒 / cap_a=100000,cap_b=16,n=5→5.23秒)から、
# /benchmark の runs=3 逐次実行でも SOLVE_TIMEOUT_SECONDS(10秒)に収まる規模に制限する
# (暫定閾値。Phase 15 の性能テストで見直す可能性あり)。
# _MAX_KNAPSACK_DP_CELLS = 2_000_000
# (Phase 15-2) 実測の結果、このガードが実際に保護するのは POST /solve の既定選択
# (measure_call/tracemalloc を経由しない素の1回呼び出し)のみと判明 ──
# POST /benchmark は get_strategies() で全候補を回すためこのガードの対象外(別課題、
# `Phase-15-2.md` §3 参照)。POST /solve 基準で再計測(cells=2,000,000→約0.86秒 /
# cells=4,000,000→約1.84秒、SOLVE_TIMEOUT_SECONDS=10秒 に十分な余裕)し、閾値を緩和。
# Phase 11-9 の実インシデント(budget=100,000, n=5, time_budget=16 → cells=8,000,000)は
# 引き続き閾値を超え greedy にフォールバックするため、修正は安全。
_MAX_KNAPSACK_DP_CELLS = 4_000_000
```

`tests/fixtures/optimization.py::build_scaled_travel_problem` は `budget`/`time_budget`が既定20に固定されていて、この規模の問題を作れなかった ── 引数化する(既定値は不変、既存の全呼び出し元は無改造で動く):

```python
# tests/fixtures/optimization.py(改訂)
def build_scaled_travel_problem(
    n_places: int, seed: int = 0, *, budget: float = 20, time_budget: float = 20
) -> OptimizationProblem:
    ...  # 本文は不変、TravelData の budget/time_budget を引数から渡すだけ
```

## 4. logistics_planning にガードは要らない ── 攻撃面が違う

`logistics_planning` も既定で `knapsack_dp`(`KnapsackDpLogisticsStrategy`)を使うが、travel と同型のガードは付けない。理由は速度ではなく **LLM がどこまで値を埋められるか**という攻撃面の違い:

```python
# app/schemas/structuring.py(Phase 11、抜粋)
class TravelDataPatch(BaseModel):
    budget: float | None = None
    time_budget: float | None = None
    ...

class LogisticsDataPatch(BaseModel):
    depot_id: str | None = None   # capacity_weight/capacity_volume はここに無い
```

Phase 11 の設計原則(「LLM が埋めてよいのはトップレベル・スカラーまで、カタログは
ベース問題から引き継ぐ」)により、`Vehicle.capacity_weight`/`capacity_volume` は
**常にベース問題の固定カタログ由来**で、自然言語からの抽出対象になっていない。
travel の `budget`/`time_budget` は逆に `TravelDataPatch` で LLM が自由に埋められる
スカラーであり、これが Phase 11-9 の実インシデント(LLM が「10万円以内」を
`budget=100000` と抽出した)を生んだ根本原因だった。

実測でも裏付ける ── 現実的な容量範囲(トラックの重量・体積として数十〜数百)では
cells は travel のような桁に届かない(いずれも素の呼び出しで計測):

| n(残り配送先) | 容量(重量×体積) | cells     | 実行時間   |
| -------- | --------- | --------- | ------ |
| 20       | 50×50     | 50,000    | 0.009秒 |
| 50       | 100×100   | 500,000   | 0.12秒  |
| 100      | 200×200   | 4,000,000 | 1.26秒  |

n=100・容量200×200という、ベース問題より大幅に大きい規模でも新閾値(4,000,000)未満に収まる。この結論は **ルール#17「実在の消費者」テストの応用** でもある ──
「LLM が logistics の capacity を将来埋められるようになったら」という仮定でガードを
先回りして実装するのは投機的リファクタであり、現時点では見送る。

---

## まとめ

- **`_MAX_KNAPSACK_DP_CELLS` は `POST /solve` の既定選択だけを保護し、`POST /benchmark` は
  一切保護していないことが実測の過程で判明した**(Phase 11-9 のコメントの前提誤り)。
- `POST /solve` が実際に経験する経路(素の1回呼び出し)を基準に再計測し、閾値を
  2,000,000 → 4,000,000 に緩和した。Phase 11-9 の実インシデント規模は引き続きガードされる。
- `POST /benchmark` 側のリスク(`tracemalloc` 計装による約11倍の見かけの遅さ)は、
  既存の `BenchmarkRequest.timeout_seconds` で呼び出し側が対処できるため、コード変更は
  見送り運用上の注意点として記録する。
- `logistics_planning` には同型ガードを追加しない ── LLM が capacity を触れないという
  スキーマ設計上の制約により、travel と同じリスクが存在しないことを実測で確認した。
- `build_scaled_travel_problem` を `budget`/`time_budget` 引数化した(既存呼び出しは無改造)。

## テスト観点(`tests/performance/test_algorithm_selection_perf.py`)

> **対象**: `knapsack_2d`(DP本体)/ `_MAX_KNAPSACK_DP_CELLS`(定数)
> **ドライバ**: このテスト関数(素の `time.perf_counter`、`measure_call` は使わない ──
> `POST /solve` が実際に経験する経路を再現するため)
> **スタブ不要** ── `knapsack_2d` は純粋関数

| ケース                                    | 期待                                               |
| -------------------------------------- | ------------------------------------------------ |
| cells = 現行閾値(4,000,000)ちょうど、素の1回呼び出し   | 時間 < `SOLVE_TIMEOUT_SECONDS / 2`(5秒。他オーバーヘッドの余地) |
| Phase 11-9 の実インシデント規模(cells=8,000,000) | 依然として閾値超過(greedy にフォールバックする条件を満たす)               |

```bash
uv run pytest tests/performance/test_algorithm_selection_perf.py -v -m performance
uv run pytest tests/unit/test_algorithm_selection.py -v   # 既存の分岐テストが無回帰か確認
```

---

次章([Phase-15-3](./Phase-15-3.md))では、`topological_sort` を同じ「実測してから判断する」
手順にかけるが、結論は逆になる ── DFS 実装は大規模な線形依存チェーンで実際にクラッシュする。
