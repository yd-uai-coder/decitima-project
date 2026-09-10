# Phase 7-6: analysis ── `travel_analysis.py` + notebook(プラン比較)(作業単位 7-6)

## この章のゴール

Phase 3-8 で作った `analysis/`(app から切り離した dev トラック。pandas / matplotlib は dev 依存)に
**1 モジュール足すだけ**(移設・作り直しなし ── Phase 4-6 の `route_benchmark.py`、Phase 6-7 の
`shift_analysis.py` と同じ)。travel_planning の benchmark を「訪問候補数(規模)別」に回した
`benchmark_runs` を読み、

- **Knapsack DP(移動を無視した上界)と Greedy(移動込み)で解の価値がどれだけ食い違うか**(`dp_vs_greedy`)
- **規模・予算を変えると DP が予算超過(invalid)になる割合**(`invalid_rate_by_size`)

を固定サンプル + notebook で見る。

**この章で作成 / 更新するファイル**:
`analysis/travel_analysis.py`(新規)、`analysis/data/sample_travel_runs.jsonl`(固定サンプル)、
`analysis/data/.gitignore`(現行版 ── `!sample_travel_runs.jsonl` を追加)、
`analysis/notebooks/travel_explore.ipynb`(新規)、`tests/analysis/test_travel_analysis.py`(新規)。

対応サンプル: 上記すべて。設計は `Phase-3-8.md`、`decitima-api/CLAUDE.md`「分析トラック」節。

---

## 1. `travel_analysis.py` ── DataFrame → DataFrame の純粋関数

```python
# analysis/travel_analysis.py(要点。全文は samples)
def load_travel_benchmark_runs(path) -> pd.DataFrame:
    """load_benchmark_runs(Phase 3)に size 列(= place 数)を足す。travel_planning に絞る。"""

def by_size(df, *, value="elapsed_ms_median") -> pd.DataFrame:
    """size × algorithm で value を median 集約したロング表。"""

def dp_vs_greedy(df, *, value="metrics.total_value") -> pd.DataFrame:
    """size ごとに knapsack_dp と greedy の指標を横並べ、gap(dp − greedy)。
    DP の total_value は「移動を無視した上界」なので Greedy 以上になりがち。
    ただし DP の解は移動込みだと invalid のことがある ── それは次の関数で。"""

def invalid_rate_by_size(df) -> pd.DataFrame:
    """size × algorithm で『invalid だった run の割合』。DP が規模・予算で崩れるのを見る。"""
```

- `analysis/` は `app` から import しない一方向(`Phase-3-8.md`)。`app.services.benchmark` が
  吐いた JSONL(`benchmark_runs` の payload)を pandas で読むだけ。
- `load_travel_benchmark_runs` は JSONL を 2 回読む ── `load_benchmark_runs`(共通、Phase 3)で
  entry ごとの flat 表にし、生 JSONL からもう一度 `payload.problem.data.places` の数を拾って
  `size` 列を付ける(`route_benchmark` / `shift_analysis` と同じパターン)。
- **`dp_vs_greedy` の `gap`** は「DP が移動を無視するとどれだけ楽観的に見えるか」の目安。
  DP が invalid でも `metrics.total_value` は「DP が主張した価値」なので表には出る ──
  「幻の価値」と「実際に回れるプランの価値」の差。

---

## 2. 固定サンプル `sample_travel_runs.jsonl`

- 実 `BenchmarkService` を SQLite で回し、`analysis.export.dump_rows` した 5 run 分。
  `build_scaled_travel_problem(n_places=5,6,7,9,12)` × 予算ゆるめ / きつめの組で、
  `algorithms=["knapsack_dp","greedy","brute_force"]`(n ≤ 7)/ `["knapsack_dp","greedy"]`(n ≥ 9)。
- 中身の狙い(生成時に確認):
  - 予算ゆるめ(5, 7 places): DP valid、価値は BruteForce == Greedy と一致(オラクル一致)。
  - 予算きつめ(6, 9 places): DP invalid(移動無視)、Greedy valid だが価値は下がる。
  - 大きめゆるめ(12 places): DP invalid(閉路の移動費用が積む)、Greedy valid。
- `analysis/data/.gitignore` は `*` で全部無視 + 固定サンプルだけ `!` で許可(生成物は追跡しない)。

---

## 3. notebook `travel_explore.ipynb`

`analysis/data/sample_travel_runs.jsonl` で完結(ライブ DB 不要)。`MPLBACKEND=Agg` で
`nbconvert --execute` が CI で回る(`samples/README.md` の手順、4 本目)。セル構成:

1. `load_travel_benchmark_runs` → size / algorithm / solution_status / total_value の一覧
2. `by_size(df)` ── 規模別の中央値実行時間(BruteForce は n ≤ 7 まで)
3. `dp_vs_greedy(df)` ── DP が主張する価値 vs Greedy の実価値、`gap`
4. `invalid_rate_by_size(df)` ── DP が予算を超えて invalid になる割合(Greedy は常に 0)

---

## 4. まとめ

- `analysis/` に `travel_analysis.py` を 1 本追加(移設・作り直しなし ── Phase 4-6 / 6-7 と同じ)。
- `dp_vs_greedy`(価値の gap)/ `invalid_rate_by_size`(DP が移動無視で崩れる割合)が Phase 7 の
  教材の核(DP = 移動無視の上界 / Greedy = 移動込みで安全)を数字で見せる。
- 固定サンプル + notebook で CI 完結。

## テスト観点(`textbook/samples/tests/analysis/test_travel_analysis.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `by_size` / `dp_vs_greedy` / `invalid_rate_by_size` / `load_travel_benchmark_runs`
>   ── すべて DataFrame → DataFrame の純粋関数
> - **ドライバ**: このテスト関数。`_fake_df()`(size × algorithm を振った最小の flat DataFrame)+
>   固定サンプル `sample_travel_runs.jsonl`
> - **スタブ**: **不要** ── `analysis/` は app から切り離した純粋レイヤー(`Phase-3-8.md`)

| ケース | 期待 |
| --- | --- |
| `by_size(_fake_df())` | 列 `[size, algorithm, elapsed_ms_median]` / size 昇順 |
| `dp_vs_greedy(_fake_df())` size=6 | `knapsack_dp == 35` / `greedy == 13` / `gap == 22` |
| `invalid_rate_by_size(_fake_df())` | DP: size 5 → 0.0、size 6 → 1.0 / Greedy: 全部 0.0 |
| `load_travel_benchmark_runs(sample)` | 空でない / `size` 列あり / `{knapsack_dp, greedy}` を含む |
| 固定サンプルの DP invalid 率 | max == 1.0、min == 0.0(規模・予算で崩れるケースと崩れないケースの両方を含む) |

`uv run pytest tests/analysis/test_travel_analysis.py` /
`PYTHONPATH=$PWD jupyter nbconvert --execute analysis/notebooks/travel_explore.ipynb`。

---

次章([Phase-7-7](./Phase-7-7.md))では、作業単位 7-7 ── decitima-ui に 4 つ目の最適化画面を足す
(Phase 4-8 / 5-5 / 6-8 と同型)。訪問候補・予算・時間・好みを編集 →「プランを作る」で Knapsack DP の
結果を `GraphCanvas` で可視化(選んだ地を強調、巡回順を実線、候補 leg を破線、invalid は赤)、
「比較」で DP / Greedy / BruteForce を横並び実測する。
