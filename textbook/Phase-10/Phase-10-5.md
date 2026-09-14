# Phase 10-5: 分析トラック拡張(作業単位 10-5)

## この章のゴール

succeeded な simulate ジョブ(`jobs` テーブル)を JSONL にエクスポートし、pandas で
シナリオ横並びの比較表と感度分析カーブを取り出す。`analysis/` は `app` から切り離したdev トラック(Phase 3-8 で確立、`Phase-3-8.md`)── コア層・solve/verify/simulate の
リクエスト経路には一切影響しない。

**この章で作成 / 更新するファイル**: `analysis/loaders.py`(`load_jobs` を追加)、
`analysis/export.py`(`jobs` テーブルを `_TABLES` に追加)、`analysis/simulation_analysis.py`(新規)、`tests/analysis/test_simulation_analysis.py`(新規)。

---

## 1. `jobs` テーブルを汎用にエクスポート ── `load_jobs`

Phase 3 の `export.py::_TABLES` は元々 `benchmark_runs` / `solutions` の 2 テーブルだけを知っていた。`_row_to_dict` / `dump_rows` はテーブル非依存(`row.__table__.columns` を汎用に読む)ので、`jobs` を増やすのに既存コードは 1 行も変えない:

```python
# analysis/export.py(要点。追加分のみ)
from app.models.job import Job  # (Phase 10-5)

_TABLES: dict[str, type[Base]] = {
    "benchmark_runs": BenchmarkRun,
    "solutions": Solution,
    "jobs": Job,  # (Phase 10-5)
}
```

`analysis/loaders.py` に、`load_benchmark_runs` / `load_solutions`(Phase 3)と対になる`load_jobs` を追加する:

```python
# analysis/loaders.py(要点)
def load_jobs(path: str | Path) -> pd.DataFrame:
    """列: job_id / created_at / problem_type / status / request / result / error。
    request/result はジョブ種別(solve か simulate か)で形が違うため、生の dict のまま
    列に保持し、種別ごとの整形は呼び出し側に委ねる。"""
    ...
```

`request`/`result` を dict のまま持つ点が `load_benchmark_runs`(entries を pandas の行にまで正規化する)との違い ── `jobs` テーブルは solve/simulate 共用なので、この共通ローダの時点でどちらか一方の形に決め打ちしない。ドメイン(ジョブ種別)ごとの整形は 2 人目の呼び出し側が担う、という判断は Phase 4-1「グラフプリミティブは汎用、ドメイン別の組み立ては呼び出し側」と同じ構造。

---

## 2. simulate ジョブだけを展開する `simulation_analysis.py`

```python
# analysis/simulation_analysis.py(要点。全文は samples)
def load_simulation_jobs(path: str | Path) -> pd.DataFrame:
    """succeeded な simulate ジョブだけを「(job, scenario) 1 行」の flat DataFrame に展開する。
    base も scenario_label="base" として含める。solve ジョブ、未完了の simulate ジョブは
    含めない(result に base/scenarios が無いことで判別する)。"""
    jobs = load_jobs(path)
    rows = []
    for _, job in jobs.iterrows():
        result = job["result"]
        if not result or "base" not in result or "scenarios" not in result:
            continue
        for scenario in [{"label": "base", **result["base"]}, *result["scenarios"]]:
            row = {"job_id": job["job_id"], ..., "scenario_label": scenario["label"], ...}
            for k, v in (scenario.get("metrics") or {}).items():
                row[f"metric.{k}"] = v
            rows.append(row)
    return pd.DataFrame(rows)


def scenario_comparison(df: pd.DataFrame, job_id: str, *, metric: str) -> pd.DataFrame:
    """1 ジョブに絞って scenario_label × metric を並べた比較表(README の
    「車両数・配送時間・コスト」表と同じ形)。base を先頭に固定する。"""
    ...


def sensitivity_curve(path: str | Path, job_id: str) -> pd.DataFrame:
    """1 ジョブの sensitivity.evaluated(二分探索が実際に訪れた点)を param 昇順の
    DataFrame にする。sensitivity が無ければ空。"""
    ...
```

`load_jobs` を「solve/simulate 共用の汎用ローダ」、`load_simulation_jobs` を「simulate 専用の展開」に分けたのは、`load_benchmark_runs`(Phase 3)が担っていた責務を 2 段に割った形 ──
汎用の列取り出しと、ドメイン(ジョブ種別)ごとの正規化は別の関数にする、という Phase 3 以来の分析トラックの流儀(`travel_analysis.py` が `load_benchmark_runs` を呼んで travel 専用の列を足すのと同型)。

`sensitivity_curve` は Phase 10-3 の `SensitivityResult.evaluated`(二分探索が**実際に訪れた点**だけの dict)をそのまま DataFrame 化する ── 全件スイープした場合の点数(仮に`low..high` を全部評価したら何点になるか)と比較することで、「二分探索は全件スイープより少ない solve で済む」という Phase 10-3 の核をデータで示せる。

---

## まとめ

- `jobs` テーブルへのエクスポート対応は `export.py::_TABLES` に 1 行足すだけ(既存コード無変更)。
- `load_jobs`(汎用)と `load_simulation_jobs`(simulate 専用の展開)を分離 ── Phase 3以来の分析トラックの流儀を継承。
- コア層(`app/`)は `analysis/` から一切 import されない(Phase 3 の設計方針を継続)。

## テスト観点(`tests/analysis/test_simulation_analysis.py`)

> **対象**: ファイル → DataFrame / DataFrame → DataFrame の純粋関数
> **ドライバ**: このテスト関数(pytest の `tmp_path` に fake な jobs JSONL を書く)
> **スタブ不要** ── `analysis/` は app から切り離した純粋レイヤー(`Phase-3-8.md`)

| ケース                           | 期待                        |
| ----------------------------- | ------------------------- |
| succeeded な simulate ジョブ      | base + 各シナリオが 1 行ずつに展開される |
| solve ジョブ / 未完了の simulate ジョブ | 行に含まれない(空 DataFrame)      |
| `scenario_comparison`         | base が先頭に固定される            |
| `sensitivity_curve`           | evaluated の点を param 昇順で返す |
| sensitivity 未指定のジョブ           | 空 DataFrame               |

`uv run pytest tests/analysis/test_simulation_analysis.py`。

---

次章([Phase-10-6](./Phase-10-6.md))では、作業単位 10-6 ── decitima-ui に Simulation
ページを追加し、既存 `useJobPolling`(Phase 9-9)を再利用してシナリオ比較表を表示する。
