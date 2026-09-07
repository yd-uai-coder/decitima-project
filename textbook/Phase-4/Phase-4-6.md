# Phase 4-6: Route Benchmark 分析(`analysis/` を育てる)(作業単位 4-6)

## この章のゴール

Phase 3-8 で作った分析トラック `analysis/`(pandas / matplotlib、dev 依存、`app/` から切り離し)に
**1 モジュール足す**。移設も作り直しもしない ── `analysis/` は Phase 4/6/10/12/14/15 が
同じ器に積んでいく多 Phase の背骨(`Phase-3-8.md`)。

Phase 4 が足すのは「route_planning の benchmark をサイズ・密度別に回して、手実装トラックと
`library:networkx` トラックの**交差点**(どの size で library が手実装より速くなるか)を出す」モジュール。

- `analysis/route_benchmark.py` ── `load_route_benchmark_runs` / `by_size` / `handwritten_vs_library` / `crossover_size`
- `analysis/plots.py` に `plot_handwritten_vs_library` を追加(現行版)
- `build_scaled_route_problem` に `density` パラメータ(既定は Phase 3 と同じ本数)
- 固定サンプル `analysis/data/sample_route_benchmark_runs.jsonl` + notebook

**この章で新規作成するファイル**: `analysis/route_benchmark.py`、
`analysis/data/sample_route_benchmark_runs.jsonl`、`analysis/notebooks/route_benchmark.ipynb`、
`tests/analysis/test_route_benchmark.py`。
**既存ファイルへの変更**(現行版は samples): `analysis/plots.py`、`analysis/README.md`、
`analysis/data/.gitignore`、`tests/fixtures/optimization.py`(`density`)。

対応サンプル: 上記すべて。設計は `Phase-3-8.md`、`Phase-0-5.md` §3.1(OSM 規模)、`Phase-0-9.md` Q19。

---

## 1. `build_scaled_route_problem` に `density`(既存ファイルへの追記)

```python
# tests/fixtures/optimization.py(要点。全文は samples)
def build_scaled_route_problem(n: int, *, seed: int = 0, density: float = 0.5) -> OptimizationProblem:
    # 連鎖 n0-n1-...-n(n-1) を必ず張り(連結性保証)、横エッジを int(n * density) 本足す。
    # density=0.5(既定)なら Phase 3 と同じ本数(n // 2)── 既存のプロパティテストは不変。
```

- **既定値 `density=0.5` で Phase 3 と完全に同じ挙動**(`int(n * 0.5) == n // 2`、RNG の呼び出し
  順も同じ)。`test_brute_force_strategy.py` の seed 0〜49 プロパティテストは緑のまま。
- 密度を上げると経路の選択肢が増え、Dijkstra と全探索の差が広がる。

> **[以降 Phase で修正予定 ── Phase 4-2 / 4-6 / 5-3]** ── この fixture ファイルは 4-2
> (`allow_negative` / 負辺 fixture)と 4-6(`density`)、Phase 5-3(`build_network_problem` 系の
> network fixture)で書き換える。Phase 3 を読む時点では Phase 3 samples の版で写経してよい。

---

## 2. `route_benchmark.py`

```python
# analysis/route_benchmark.py(要点。全文は samples)
def load_route_benchmark_runs(path) -> pd.DataFrame:
    """load_benchmark_runs に size(ノード数)・density((エッジ数 - (n-1)) / n)の列を足す。"""

def by_size(df, *, value="elapsed_ms_median") -> pd.DataFrame:
    """size × (algorithm, implementation) で median 集約したロング表。"""

def handwritten_vs_library(df, *, metric="elapsed_ms_median") -> pd.DataFrame:
    """同名アルゴリズムの handwritten と library:* を size ごとに横並び + speedup 列。
       speedup = handwritten / library。> 1 なら library が速い。"""

def crossover_size(df, *, metric="elapsed_ms_median") -> dict[str, float | None]:
    """アルゴリズムごとに『library がはじめて handwritten より速くなる size』。無ければ None。"""
```

- **DataFrame → DataFrame の純粋関数**(`benchmark_report.py` と同じ設計)。DB は触らない ──
  入力は `load_benchmark_runs`(Phase 3)が返す flat DataFrame + size/density 列。
- `analysis/` は **ruff のみ**(pyright の include は `["app", "tests"]` のまま ── pandas の型は
  standard で騒がしい)。`tests/analysis/` は `tests/` 配下なので pyright 対象。

### 何が見えるか(サンプルデータでの実測)

| size | handwritten dijkstra (ms) | library:networkx (ms) | speedup |
| --- | --- | --- | --- |
| 8 | 0.15 | 0.35 | 0.44 |
| 32 | 0.20 | 0.86 | 0.23 |
| 128 | 1.27 | 3.35 | 0.38 |

**MVP 規模(〜数百ノード)では手実装が勝つ** ── networkx はグラフオブジェクトの構築に
Python レベルのオーバーヘッドがあり、pure-Python の heapq Dijkstra がそれを上回る。
`crossover_size` はこの範囲で `None`(交差しない)。ライブラリが効いてくるのは
`Phase-0-5.md` §3.1 が言う OSM 規模(10⁶ ノード)── DeciTima の MVP はそこまで行かない。
**これが「手実装をやめてライブラリに切り替える点」を実測で示す**という 2 トラック設計の目的
(`Phase-0-9.md` Q19)。Phase 6 の Shift ではこの交差点がずっと手前に来る。

---

## 3. notebook + 固定サンプル

- `analysis/data/sample_route_benchmark_runs.jsonl` ── 実 `BenchmarkService` を
  size 8/16/32/64/128 × density 2 種で回して `dump_rows` した 10 run 分(BruteForce は
  大サイズで爆発するので `algorithms=["dijkstra","bellman_ford","a_star"]` でフィルタ)。
- `analysis/notebooks/route_benchmark.ipynb` ── この固定サンプルで完結。`nbconvert --execute` で
  CI 実行(`PYTHONPATH=. MPLBACKEND=Agg`)。
- `analysis/data/.gitignore` に `!sample_route_benchmark_runs.jsonl` を追加(生成物は追跡しない、
  固定サンプルだけ許可)。

---

## 4. まとめ

- `analysis/` に `route_benchmark.py` を 1 本追加(移設・作り直しなし)。
- `build_scaled_route_problem` に `density`(既定は Phase 3 と同じ挙動)。
- `handwritten_vs_library` / `crossover_size` で「手実装 vs library の交差点」を出す。
- MVP 規模では手実装が勝つ ── これが 2 トラック設計の「切り替え点を実測で示す」目的。

## テスト観点(`samples/tests/analysis/test_route_benchmark.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `by_size` / `handwritten_vs_library` / `crossover_size`(DataFrame → DataFrame の純粋関数)、
>   `load_route_benchmark_runs`(file → DataFrame)、`plot_handwritten_vs_library`(→ Figure)
> - **ドライバ**: このテスト関数。`_fake_df()`(手書きの最小 DataFrame)+ 固定サンプル JSONL
> - **スタブ**: **不要** ── `analysis/` は app から切り離した純粋レイヤー(`Phase-3-8.md`)。
>   plot は `matplotlib.use("Agg")` でヘッドレス

| ケース | 期待 |
| --- | --- |
| `by_size(_fake_df())` | `(algorithm, size)` でソートされたロング表 |
| `handwritten_vs_library` | `speedup == handwritten / library` |
| library が size 100 で初めて速い `_fake_df` | `crossover_size == {"dijkstra": 100.0}` |
| library が常に遅い | `crossover_size == {"dijkstra": None}` |
| 固定サンプル JSONL | `load_route_benchmark_runs` に `size` / `density` 列、`library:networkx` エントリを含む |
| `plot_handwritten_vs_library` | `matplotlib.figure.Figure` を返す |

`PYTHONPATH=. uv run pytest tests/analysis/test_route_benchmark.py` /
`PYTHONPATH=. MPLBACKEND=Agg uv run --with jupyter --with nbconvert --with ipykernel jupyter nbconvert --execute analysis/notebooks/route_benchmark.ipynb`。

---

次章([Phase-4-7](./Phase-4-7.md))からは decitima-ui。作業単位 4-7 ── グラフ(ノード + エッジ)を
描く手描き SVG コンポーネント `GraphCanvas`、JSON 入力エリア `ProblemJsonEditor`、
route の solve API 層を作る。`GraphCanvas` はドメイン非依存なので Phase 5 の Network Designer も
そのまま使う。
