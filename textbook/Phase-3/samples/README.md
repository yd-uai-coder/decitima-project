# Phase 3 samples ── 実装の初期状態(単一の真実源)

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文(`Phase-3-*.md`)は要点の抜粋だけ、動くコードはここ。ユーザーはここから
`decitima-api/backend/app/` `tests/` と `decitima-ui/src/` へ **ファイル単位で写経・改変** する。

**`samples/` に置くもの**:
- Phase 3 で **新規に作る** ファイル
- Phase 1 / 2 のファイルを Phase 3 が **書き換える** もの(現行版をここに置く)

**`samples/` に置かないもの**（既存テンプレートファイルへの追記 → 各章に差分で示す）:
- backend: `app/core/config.py` / `app/api/routes/__init__.py` / `app/models/__init__.py` /
  `alembic/env.py` / `app/algorithms/registry.py` / `pyproject.toml`
- ui: `src/lib/api/types.ts` と `src/lib/menu-tree.ts` は **現行版を samples に同梱**
  (追記だが全体を写す方が安全 ── Phase 1 の教訓)

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `alembic/versions/*.py` | `decitima-api/backend/alembic/versions/` |
| `analysis/**` | `decitima-api/backend/analysis/**`(3-7) |
| `ui/src/**` | `decitima-ui/src/**` |

## Phase 3 で作る / 変えるもの(作業単位)

| 単位 | samples の中心ファイル | 既存への変更 | 章 |
| --- | --- | --- | --- |
| 3-1 | `app/services/measurement.py`、`tests/unit/test_measurement.py` | `app/schemas/optimization.py`(`Benchmark*` 追加・現行版同梱)、`pyproject.toml`(`numpy>=2.0`) | Phase-3-1 |
| 3-2 | `app/algorithms/optimization/brute_force.py`、`app/algorithms/optimization/__init__.py`、`tests/unit/test_brute_force_strategy.py` | `app/algorithms/registry.py`(import + route_planning に 1 行)、`tests/fixtures/optimization.py`(`build_scaled_route_problem`・現行版同梱) | Phase-3-2 |
| 3-3 | `app/services/benchmark.py`、`app/api/routes/benchmark.py`、`app/repositories/benchmark.py`、`alembic/versions/d4f1a9c2b8e7_add_benchmark_runs_table.py`、`tests/unit/test_benchmark_service.py`、`tests/unit/test_benchmark_repository.py`、`tests/api/test_benchmark_api.py`、`tests/integration/test_benchmark_persistence.py` | `app/models/optimization.py`(`BenchmarkRun`・現行版同梱)、`app/services/optimization_read.py`(`get_benchmark_run`・現行版同梱)、`app/core/config.py`、`app/api/routes/__init__.py`、`app/models/__init__.py`、`alembic/env.py` | Phase-3-3 |
| 3-4 | `tests/unit/test_benchmark_curve.py` | `app/api/routes/benchmark.py`(GET ハンドラ ── 現行版に同梱)、`tests/api/test_benchmark_api.py`(GET ケース ── 現行版に同梱) | Phase-3-4 |
| 3-5 | `ui/src/features/optimization/{api/benchmark.ts,stores/benchmark-store.ts,hooks/useBenchmark.ts,sample-problems.ts}`、`ui/src/features/optimization/stores/benchmark-store.test.ts`、`ui/src/features/optimization/api/benchmark.test.ts` | `ui/src/lib/api/types.ts`(現行版同梱) | Phase-3-5 |
| 3-6 | `ui/src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx`、`ui/src/features/optimization/components/*.tsx`、`ui/src/app/(pages)/optimization/benchmark/page.tsx`、`ui/src/components/ui/charts/GroupedBarChart.test.tsx` | `ui/src/lib/menu-tree.ts`(現行版同梱) | Phase-3-6 |
| 3-7 | `analysis/{__init__,db,export,loaders,benchmark_report,plots}.py`、`analysis/{README.md,data/.gitignore,data/sample_benchmark_runs.jsonl,notebooks/benchmark_explore.ipynb}`、`tests/analysis/{test_loaders,test_benchmark_report,test_plots,test_export}.py` | `pyproject.toml`(`[dependency-groups].analysis` + ruff `src`/`known-first-party` に `analysis`)、`.gitignore` | Phase-3-7 |

## 既存テンプレートファイルへの追記(samples には含めない)

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `pyproject.toml` | `[project].dependencies` に `"numpy>=2.0"` → `uv sync` | Phase-3-1 §3 |
| `app/algorithms/registry.py` | `BruteForceRouteStrategy` の import + `route_planning` リストに 1 行 | Phase-3-2 §2 |
| `app/core/config.py` | `class Settings` に `BENCHMARK_RATE_LIMIT_PER_HOUR/DAY` | Phase-3-3 §4 |
| `app/api/routes/__init__.py` | `benchmark_router` の import と `include_router` | Phase-3-3 §4 |
| `app/models/__init__.py` | `BenchmarkRun` を import、`__all__` に追加 | Phase-3-3 §4 |
| `alembic/env.py` | `from app.models import BenchmarkRun, ...` | Phase-3-3 §4 |
| `pyproject.toml` | `[dependency-groups]` に `analysis = ["pandas>=2.2", "matplotlib>=3.9"]`。`[tool.ruff].src` と `[tool.ruff.lint.isort].known-first-party` に `analysis` を追加 | Phase-3-7 §7 |
| `.gitignore` | `analysis/data/*` を無視し `.gitignore` と `sample_benchmark_runs.jsonl` だけ許可 | Phase-3-7 §7 |

## Phase 1 / Phase 2 samples 側の 「以降 Phase で修正予定」/「サンプル修正」マーカー(進行のルール #12)

Phase 3 が書き換えた以前の Phase のファイルは、以前の `samples/` 側にコード本体をそのまま残し
(スナップショット)、docstring 直後にマーカーを付けて現行版へ誘導する:

- `textbook/Phase-1/samples/app/models/optimization.py` ── `# [以降 Phase で修正予定 ── Phase 3-3]`
  (`BenchmarkRun` 追加。現行版 `textbook/Phase-3/samples/app/models/optimization.py`)
- `textbook/Phase-1/samples/app/services/optimization_read.py` ──
  `# [以降 Phase で修正予定 ── Phase 3-3]`(`get_benchmark_run` 追加)
- `textbook/Phase-2/samples/app/schemas/optimization.py` ──
  `# [以降 Phase で修正予定 ── Phase 3-1]`(`Benchmark*` 追加)
- `textbook/Phase-2/samples/tests/fixtures/optimization.py` ──
  `# [以降 Phase で修正予定 ── Phase 3-2]`(`build_scaled_route_problem` 追加)

`grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で全変更点を一覧できる。

## 検証(overlay)

### backend

samples は実 `app/` ツリー鏡写しで `from app...` / `from tests...` の絶対 import を使うため、
単体では import が解決しない。**Phase 2 end 状態**の `decitima-api/backend` に Phase 3 samples を
重ねて検証する:

```bash
# 1. Phase 2 end 状態(= 現在の decitima-api/backend の作業ツリー)を複製、.venv をリンク
rsync -a --exclude '.venv' --exclude '.git' decitima-api/backend/ <work>/
ln -s <abs>/decitima-api/backend/.venv <work>/.venv

# 2. Phase 3 samples を重ねる
rsync -a textbook/Phase-3/samples/app/      <work>/app/
rsync -a textbook/Phase-3/samples/tests/    <work>/tests/
rsync -a textbook/Phase-3/samples/alembic/  <work>/alembic/
rsync -a textbook/Phase-3/samples/analysis/ <work>/analysis/   # 3-7
#    + 上記「既存テンプレートファイルへの追記」を適用
#    + pyproject の numpy / analysis グループ / ruff の src・known-first-party
#    + uv pip install --python .venv/bin/python 'numpy>=2.0' 'pandas>=2.2' 'matplotlib>=3.9'

# 3. 実行
uv run pytest                              # 165 passed, 3 deselected(3-7 の analysis 14 件を含む)
uv run ruff check app tests analysis       # All checks passed
uv run ruff format --check app tests analysis
uvx pyright app tests                      # 0 errors(analysis/ は ruff のみ ── pyright include 外)
DATABASE_URL="sqlite+aiosqlite:///./x.db" REDIS_URL=... JWT_SECRET_KEY=... \
  uv run alembic upgrade head              # benchmark_runs が生える
uv run --with jupyter jupyter nbconvert --execute --to notebook --stdout \
  analysis/notebooks/benchmark_explore.ipynb > /dev/null   # sample データで完走
```

### ui

```bash
rsync -a --exclude 'node_modules' --exclude '.next' --exclude '.git' decitima-ui/ <work-ui>/
ln -s <abs>/decitima-ui/node_modules <work-ui>/node_modules
rsync -a textbook/Phase-3/samples/ui/src/ <work-ui>/src/

cd <work-ui>
npx tsc --noEmit                           # clean
npx vitest run src/features/optimization src/components/ui/charts/GroupedBarChart.test.tsx
                                           # 8 passed(Phase 3 の追加分)
npx eslint src/features/optimization src/components/ui/charts src/lib/menu-tree.ts \
  src/lib/api/types.ts 'src/app/(pages)/optimization/benchmark/page.tsx'   # clean
```

(注: `src/components/layout/Menu.test.tsx` は Phase 3 以前から失敗しているテンプレートの
テスト rot。Phase 3 の変更とは無関係で、件数は増えない。)

型注意(`decitima-api/CLAUDE.md`): pyright standard。`measure_call` は PEP 695 ジェネリクス
(`def measure_call[T](...)`)。`asyncio.to_thread(measure_call, partial(strategy.solve, problem), runs)`
で strategy を固定(ループ変数キャプチャを避ける)。

3-7 注意: `analysis/` は **ruff のみ**(pyright `include` は `["app", "tests"]` のまま ──
pandas の型は standard で騒がしく、`app/ai` と同じ割り切り)。`tests/analysis/` は `tests/` 配下
なので pyright 対象(0 errors)。`analysis` を ruff の `src` / `known-first-party` に足すと
`from analysis.X import ...` が first-party としてソートされる。`jupyter` はロックせず
`uv run --with jupyter`。sample の `analysis/data/sample_benchmark_runs.jsonl` は実際に
`BenchmarkService` を回して `dump_rows` した 3 run 分。
