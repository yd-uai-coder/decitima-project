# analysis/ ── 分析トラック

> **[以降 Phase で修正予定 ── Phase 4-6]** Phase 4-6 で `route_benchmark.py`(Route Benchmark の
> size / density 別集計)と `plots.plot_handwritten_vs_library` を追加する。この README の
> 現行版は `textbook/Phase-4/samples/analysis/README.md`。

`benchmark_runs` / `solutions` に貯まった実測を pandas で集計・可視化する。
**`app/` からは import されない**(`tests/` と同じく app の「上」)。

## 依存

`pyproject.toml` の `[dependency-groups].analysis`(`pandas` / `matplotlib`)。runtime には入れない。

```bash
uv sync --group analysis
uv run --with jupyter jupyter lab   # notebook を触るとき(jupyter はロックしない)
```

## 使い方

```bash
# 1. DB からエクスポート(一方向。API とは別プロセス)
uv run python -m analysis.export benchmark_runs analysis/data/benchmark_runs.jsonl
uv run python -m analysis.export solutions      analysis/data/solutions.jsonl --user <uuid>

# 2. 読んで集計
uv run python -c "
from analysis.loaders import load_benchmark_runs
from analysis.benchmark_report import by_algorithm
df = load_benchmark_runs('analysis/data/benchmark_runs.jsonl')
print(by_algorithm(df))
"

# 3. notebook(固定サンプルで完結。DB 不要)
uv run --with jupyter jupyter nbconvert --execute --to notebook \
  analysis/notebooks/benchmark_explore.ipynb
```

## モジュール

| ファイル | 役割 |
| --- | --- |
| `db.py` | 分析専用の独立 async エンジン(`session_scope`)。`analysis/` の唯一の DB 接点 |
| `export.py` | `benchmark_runs` / `solutions` → JSONL。`dump_rows(session, ...)` が純粋部分、`export_table` が CLI ラッパ |
| `loaders.py` | JSONL → `pd.DataFrame`(`load_benchmark_runs` は「(run, algorithm) 1 行」に展開) |
| `benchmark_report.py` | `by_algorithm` / `input_size_curve` / `regression`(DataFrame → DataFrame の純粋関数) |
| `plots.py` | `plot_comparison` / `plot_input_size_curve`(matplotlib。`savefig` はしない) |
| `data/` | エクスポート生成物(gitignore)+ `sample_benchmark_runs.jsonl`(notebook / テスト用の固定スナップショット) |

## ロードマップ(このトラックは多 Phase の背骨)

| Phase | 追加するもの |
| --- | --- |
| **3(この単位)** | benchmark 分析 ── `benchmark_report.py` / `plots.py` |
| 4 | Route Benchmark(Dijkstra / Bellman-Ford / A* / networkx をサイズ・密度別に) |
| 5 | 手実装 vs OR-Tools の破綻境界・多目的 Pareto ── `analysis/shift_analysis.py` |
| 9 | Sensitivity Analysis(パラメータを振ったシナリオ表・tornado 図)── `analysis/sensitivity.py` |
| 11 | 蓄積 benchmark から「問題特徴 → 最適アルゴリズム」の決定表を導出 |
| 13 | LLM vs Algorithm の実験フレームワーク ── `analysis/experiment.py`(`load_solutions` を使う) |
| 14 | CI での性能ベンチ実行 → 履歴 DataFrame → 回帰検知(`regression`) |

## やらないこと

- **入力アダプタ**(CSV / Excel → `OptimizationProblem`)は別レイヤー(`app/adapters/`、runtime
  依存)。Phase 6(スタッフ名簿)/ 7(タスク一覧)/ 8(車両・配送)で必要になったら追加する。
- `analysis/` を `app/` から import すること。分析は常に「結果を後から読む」側。
