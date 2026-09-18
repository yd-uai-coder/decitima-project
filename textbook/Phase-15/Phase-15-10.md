# Phase 15-10: CI/CD ワークフロー(作業単位 15-10)

## この章のゴール

`.github/workflows/` がどちらのリポジトリにも無い(README §15 が挙げる
「GitHub → GitHub Actions → Docker → VPS」の実質的なギャップ)ので新設する。加えて、Phase 3-8 で「Phase 15 の CI 回帰検知用」として先行実装されていた
`analysis/benchmark_report.py::regression()` を初めて実際に配線する。

**この章で作成 / 更新するファイル**: `.github/workflows/backend-ci.yml`・`ui-ci.yml`(新規)、
`scripts/ci_regression_check.py`(新規)、`analysis/data/ci_baseline_benchmark_runs.jsonl`
(新規)、`tests/unit/test_ci_regression_check.py`(新規)。

---

## 1. `analysis/benchmark_report.py::regression()` を初めて配線する

Phase 3-8 の `regression(baseline, current, *, metric="elapsed_ms_median")` は
「同一アルゴリズムの baseline → current の変化率(ratio / pct_change)」を返す純粋関数として先行実装されていた(docstring に「Phase 15 の CI 回帰検知用」と明記)。CI で使うには「baseline」「current」の2つの `benchmark_runs` 形式 DataFrame を用意する必要がある ──
本格的な `BenchmarkService`(DB・Redis 依存)を CI で毎回動かすのは重いので、代表的な
(problem, strategy) の組を直接 `measure_call`(Phase 3)で実測する軽量スクリプトを書いた:

```python
# scripts/ci_regression_check.py(要点。全文は samples)
_TARGETS = [
    ("route_planning", DijkstraStrategy()),
    ("travel_planning", KnapsackDpTravelStrategy()),
    ("project_scheduling", CpmScheduleStrategy()),
]
_REGRESSION_RATIO_THRESHOLD = 3.0  # CI ランナーのノイズを吸収しつつ明確な劣化は検知する

def main() -> int:
    entries = [_measure_one(pt, strategy) for pt, strategy in _TARGETS]
    # benchmark_runs と同じ形の JSONL を組み立てて書き出す
    ...
    baseline = load_benchmark_runs(_BASELINE_PATH)
    current = load_benchmark_runs(_CURRENT_PATH)
    diff = regression(baseline, current)
    regressed = diff[diff["ratio"] > _REGRESSION_RATIO_THRESHOLD]
    return 1 if not regressed.empty else 0
```

閾値は3倍(3.0)── `measure_call` は中央値を取るため単発の外れ値には強いが、GitHub Actionsの共有ランナーは実行環境ごとの絶対性能差が大きい。ゆるすぎず、O(n)→O(n²) のような明確な計算量の劣化(数倍〜数十倍の悪化)は検知できる大きさに設定した。

**実測で動作確認**: ベースライン(3アルゴリズムの想定値)に対し、実際に3アルゴリズムを
測定 → `regression()` で比較 → 全て閾値内で exit 0、続けてベースラインの1件を意図的に1/1000 に書き換えて再実行 → dijkstra の ratio が119倍になり exit 1 になることを確認した。

```
  algorithm  baseline   current      ratio   pct_change
        cpm     1.800  2.539967   1.411093    41.109278
   dijkstra     0.001  0.119156 119.156030 11815.602954   ← 閾値超過を検知
knapsack_dp    85.000 83.552725   0.982973    -1.702676

回帰検知: 閾値(3.0倍)を超えたアルゴリズムがあります
```

## 2. `backend-ci.yml` ── lint/型/テスト/性能回帰/Dockerビルド

```yaml
# .github/workflows/backend-ci.yml(要点。全文は samples)
jobs:
  lint-and-test:
    steps:
      - run: uv sync --locked --group analysis
      - run: uv run ruff check app tests analysis
      - run: uv run ruff format --check app tests analysis
      - run: uvx pyright app tests
      - run: uv run pytest                          # 既定(unit/api/analysis)
      - run: uv run pytest -m performance            # 大規模入力テスト(Phase 15-1〜15-3)
      - run: uv run python -m scripts.ci_regression_check   # 性能回帰チェック(本章)
  docker-build:
    steps:
      - run: docker build --target runtime -t decitima-api-backend:ci .
```

`-m performance` を既定実行と別ステップに分けたのは、性能テストが数十秒かかりうるため(既定の unit/api/analysis テストは数秒で終わる)── 失敗の切り分けもしやすくなる。

## 3. `ui-ci.yml` ── lint/型/vitest/E2E/build

```yaml
# .github/workflows/ui-ci.yml(要点。全文は samples)
jobs:
  lint-and-test:
    steps:
      - run: npx tsc --noEmit
      - run: npm run lint
      - run: npm run test
      - run: npm run build
  e2e:
    services: { postgres: ..., redis: ... }
    steps:
      - run: npx playwright install --with-deps chromium
      - name: decitima-api を E2E_TESTING=true で起動
        run: |
          uv sync --locked
          uv run alembic upgrade head
          uv run python -m scripts.seed
          uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
      - run: npx playwright test
```

`e2e` ジョブは decitima-api を別リポジトリからチェックアウトし、`E2E_TESTING=true` で起動する(Phase 15-9 で設計した LLM フェイク経路。本物の Gemini API を CI から呼ばない)。
`scripts/seed.py`(既存)で固定テストユーザーを作り、Playwright のログインシナリオが使う。

### 追補(ユーザー写経で発覚)── `analysis` の import はモジュール先頭でなく `main()` 内に

`scripts/ci_regression_check.py` はモジュール先頭で `analysis.benchmark_report`/
`analysis.loaders`(pandas 依存)を import していたが、これだと pandas 未導入の環境で`tests/unit/test_ci_regression_check.py`(このモジュールを import するだけの単体テスト、pandas を使わない `_measure_one`/`_TARGETS` だけを見る)まで collection エラーになる
── `tests/unit/` にあるためこのテストは 15-1 追補の `analysis` マーカーの対象外
(`tests/analysis/` 配下のみ自動付与)。`main()` 内のローカル import に変更して解消した(実際に `analysis` 実行に要る箇所だけが pandas に依存する形に絞る)。

---

## まとめ

- `.github/workflows/backend-ci.yml`・`ui-ci.yml` を新設し、README §15「GitHub Actions」の
  ギャップを埋めた。
- `analysis/benchmark_report.py::regression()`(Phase 3-8)を初めて実消費者に接続した ──
  代表3アルゴリズムを `measure_call` で実測し、コミット済みベースラインとの比率が閾値(3倍)を超えたら CI を失敗させる。実測で正常系・異常系(閾値超過)の両方を確認した。
- UI の E2E ジョブは decitima-api を `E2E_TESTING=true` で起動し、本物の LLM 呼び出しを避ける設計にした(詳細 15-9)。

## テスト観点(`tests/unit/test_ci_regression_check.py`)

> **対象**: `_measure_one`(実測1件の組み立て)/ `_TARGETS`(対象一覧)/
> `_REGRESSION_RATIO_THRESHOLD`(閾値定数)
> **ドライバ**: このテスト関数
> **スタブ不要** ── 対象の strategy はいずれも純粋(DB/Redis/LLM を呼ばない)

| ケース                           | 期待                                                             |
| ----------------------------- | -------------------------------------------------------------- |
| `_TARGETS`                    | route_planning/travel_planning/project_scheduling の3つを横断する     |
| `_measure_one(pt, strategy)`  | `algorithm.name`/`elapsed_ms_median`/`peak_memory_kb` を持つ辞書を返す |
| `_REGRESSION_RATIO_THRESHOLD` | 1.0 より大きい(小さいと常に「回帰」扱いになる)                                     |

```bash
uv run pytest tests/unit/test_ci_regression_check.py -v
uv run python -m scripts.ci_regression_check   # 実際に回帰チェックを走らせる(analysisグループ要)
```

---

次章([Phase-15-11](./Phase-15-11.md))ではデプロイ Runbook を整備する ── 監査でもう1つの
見落としが見つかる。
