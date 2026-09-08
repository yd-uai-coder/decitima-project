# Phase 6 samples ── 実装の初期状態(単一の真実源)

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文(`Phase-6-*.md`)は要点の抜粋だけ、動くコードはここ。

**Phase 6 = Shift Scheduler(組合せ最適化 ── MVP の総仕上げ)**。Phase 6 は **Phase 5 end 状態の
上に重ねる**。schema / Semantic Validation / Verification は Phase 1〜2 で完成しているので、Phase 6 は
**アルゴリズムを書くだけ**。判別ユニオンにも shift は既にいる(配線ゼロ)。

## `samples/` に置くもの

- Phase 6 で **新規に作る** ファイル:
  - `app/domain/objectives/{__init__,weighted_sum}.py` ── 重み付き和の評価器(Phase 1 からの宿題)
  - `app/domain/solutions/shift_metrics.py` ── shift 解の metrics 計算を集約した公開 leaf(検証器と 4 strategy が共有)
  - `app/algorithms/patterns/{sliding_window,difference_array}.py` ── スケジューリング・プリミティブ
  - `app/algorithms/scheduling/{common,greedy,backtracking,branch_and_bound,ortools_cpsat}.py`
  - `analysis/shift_analysis.py` + `analysis/data/sample_shift_runs.jsonl` + `analysis/notebooks/shift_explore.ipynb`
  - shift-scheduler UI 一式(`features/optimization/shift-scheduler/**` + ページ)
  - `tests/unit/test_{weighted_sum,scheduling_primitives,greedy_shift,backtracking_shift,branch_and_bound_shift,shift_breakdown,ortools_cpsat_shift,shift_strategies}.py`
  - `tests/analysis/test_shift_analysis.py`
- Phase 1〜5 のファイルを Phase 6 が **書き換える** もの(現行版):
  - `app/domain/solutions/shift_scheduler.py` ── `type Assignment = dict[str, list[str]]` を追加、`assignments: Assignment` に(共有語彙。挙動不変。#17)
  - `app/domain/solutions/structure.py` ── metrics 計算を `shift_metrics.py` に移設、`verify_shift_structure` はそれを呼ぶだけに(`hour_variance` 追加)
  - `app/services/algorithm_selection.py` ── `_preferred_name` に shift 分岐(→ `"backtracking"`)
  - `app/algorithms/patterns/__init__.py`(docstring)、`app/algorithms/scheduling/__init__.py`(docstring)、
    `app/domain/objectives/__init__.py`(新規 = 現行版)
  - `tests/fixtures/optimization.py` ── `build_scaled_shift_problem` + `build_shift_problem(with_hour_variance=...)`
  - `tests/unit/test_verification_service.py` ── hour_variance のケース
  - `tests/unit/test_algorithm_selection.py` ── shift 選択のケース
  - `tests/unit/test_registry.py` / `tests/unit/test_solve_service.py` / `tests/api/test_solve_api.py`
    ── 「未登録 problem_type」テストを「registry キーを空にして候補ゼロ」に(全 problem_type に strategy が付いた)
  - `ui/src/lib/api/types.ts` ── `ShiftData` / `ShiftSolution` / union / `CandidateSolution` に shift アーム
  - `ui/src/lib/menu-tree.ts` ── Optimization に shift エントリ
  - `ui/src/features/optimization/{network-designer,route-planner}/stores/*.test.ts`
    ── `.assignments.total_weight` → `.metrics.total_weight`(shift 解には total_weight が無い)

## `samples/` に置かないもの(既存テンプレートファイルへの追記 → 各章に差分で示す)

- `app/algorithms/registry.py` ── `"shift_scheduling"` に 4 strategy(6-3 で Greedy、6-4 で Backtracking、
  6-5 で B&B、6-7 で CP-SAT を段階的にコメント解除。進行のルール #15)
- `pyproject.toml` ── `[project].dependencies` に `ortools`(6-7)

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `analysis/**` | `decitima-api/backend/analysis/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `ui/src/**` | `decitima-ui/src/**` |

## Phase 6 で作る / 変えるもの(作業単位)

| 単位 | samples の中心ファイル | 既存への変更 | 章 |
| --- | --- | --- | --- |
| 6-1 | `app/domain/objectives/{__init__,weighted_sum}.py`、`app/domain/solutions/shift_metrics.py`、`tests/unit/test_weighted_sum.py` | `app/domain/solutions/shift_scheduler.py`(現行版 = `type Assignment`)、`app/domain/solutions/structure.py`(現行版 = metrics を shift_metrics に移設 + `hour_variance`)、`tests/unit/test_verification_service.py`(現行版) | Phase-6-1 |
| 6-2 | `app/algorithms/patterns/{sliding_window,difference_array}.py`、`tests/unit/test_scheduling_primitives.py` | `app/algorithms/patterns/__init__.py`(docstring) | Phase-6-2 |
| 6-3 | `app/algorithms/scheduling/{common,greedy}.py`、`tests/unit/test_greedy_shift.py` | `registry.py`(Greedy 配線)、`app/services/algorithm_selection.py`(現行版)、`tests/fixtures/optimization.py`(現行版 = `build_scaled_shift_problem` 系)、`tests/unit/test_algorithm_selection.py`(現行版) | Phase-6-3 |
| 6-4 | `app/algorithms/scheduling/backtracking.py`、`tests/unit/test_backtracking_shift.py` | `registry.py`(Backtracking 配線) | Phase-6-4 |
| 6-5 | `app/algorithms/scheduling/branch_and_bound.py`、`tests/unit/test_branch_and_bound_shift.py` | `registry.py`(B&B 配線) | Phase-6-5 |
| 6-6 | `tests/unit/test_shift_breakdown.py`(理論 + 全列挙オラクル) | ── (実装ファイルなし) | Phase-6-6 |
| 6-7 | `app/algorithms/scheduling/ortools_cpsat.py`、`analysis/shift_analysis.py`、`analysis/data/*`、`analysis/notebooks/*`、`tests/unit/{test_ortools_cpsat_shift,test_shift_strategies}.py`、`tests/analysis/test_shift_analysis.py` | `registry.py`(CP-SAT 配線)、`pyproject.toml`(`ortools`)、`tests/unit/{test_registry,test_solve_service}.py`・`tests/api/test_solve_api.py`(現行版) | Phase-6-7 |
| 6-8 | `ui: features/optimization/shift-scheduler/{api,stores,hooks,components,sample-problems.ts}`、`app/(pages)/optimization/shift-scheduler/page.tsx` | `ui/src/lib/{api/types.ts,menu-tree.ts}`(現行版)、`ui/.../route-planner`・`network-designer` の store test(現行版) | Phase-6-8 |

## 既存テンプレートファイルへの追記(samples には含めない)

| 既存ファイル | 追記内容 | 章 |
| --- | --- | --- |
| `app/algorithms/registry.py` | `"shift_scheduling": [GreedyShiftStrategy(), BacktrackingShiftStrategy(), BranchAndBoundShiftStrategy(), OrToolsCpSatShiftStrategy()]` を段階的に有効化 | 6-3 §3 / 6-4 §4 / 6-5 §4 / 6-7 §4 |
| `pyproject.toml` | `[project].dependencies` に `ortools`(numpy / networkx の隣) | 6-7 §3 |

## 既存 Phase samples 側のマーカー(進行のルール #12)

- `Phase-1/samples/app/domain/solutions/shift_scheduler.py`
  ── `[以降 Phase で修正予定 ── Phase 6-1]`(`type Assignment` エイリアスを追加。共有語彙。挙動不変)
- `Phase-2/samples/app/domain/solutions/structure.py`(+ Phase 5 samples の同ファイル)
  ── `[以降 Phase で修正予定 ── Phase 6-1]`(metrics 計算ヘルパを `shift_metrics.py` に抽出 + `hour_variance` 追加。hard/soft の 5+1 チェックと `_longest_consecutive_run` は不変)
- `Phase-2〜5/samples/tests/fixtures/optimization.py` ── `[以降 Phase で修正予定 ── Phase 6-3]`(`build_scaled_shift_problem`)
- `Phase-4/5 samples/app/services/algorithm_selection.py` ── `[以降 Phase で修正予定 ── Phase 6-3]`(shift 分岐)
- `Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の objectives マーカー ── `[Phase 6 で確定 ── 実装済み]`

`grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で一覧できる。

## 検証(overlay)

### backend ── **Phase 5 end 状態**の上に重ねる

```bash
# 1. Phase 4 route-end + Phase 5 samples で「Phase 5 end 状態」を作る(clean な problem.py で
#    ForbiddenConstraint 二重定義を解消)。手順は Phase-5 samples/README.md。
# 2. その上に Phase 6 samples を重ねる
rsync -a textbook/Phase-6/samples/app/      <work>/app/
rsync -a textbook/Phase-6/samples/tests/    <work>/tests/
rsync -a textbook/Phase-6/samples/analysis/ <work>/analysis/
#  + registry.py に "shift_scheduling": [Greedy, Backtracking, B&B, CP-SAT]
#  + pyproject.toml に ortools
uv pip install --python .venv/bin/python ortools

uv run pytest                          # 271 passed, 2 deselected
uv run ruff check  --config pyproject.toml <phase 6 files>   # All checks passed
uv run ruff format --check --config pyproject.toml <phase 6 files>
uvx pyright app tests                  # Phase 6 分は 0 errors
uv run alembic upgrade head            # 新テーブルなし(hybrid JSONB)
jupyter nbconvert --to notebook --execute analysis/notebooks/shift_explore.ipynb   # 完走
```

### ui ── decitima-ui に重ねる

```bash
rsync -a textbook/Phase-5/samples/ui/src/ <work-ui>/src/    # Phase 5 UI end 状態
rsync -a textbook/Phase-6/samples/ui/src/ <work-ui>/src/    # shift アーム / shift-scheduler

npx tsc --noEmit                       # clean
npx vitest run src/features/optimization   # 17 passed(shift-scheduler store 4 + 既存)
npx eslint src/features/optimization src/lib/api/types.ts src/lib/menu-tree.ts \
  'src/app/(pages)/optimization'        # clean
```

(注: `src/components/layout/Menu.test.tsx` は Phase 3 以前から失敗しているテンプレートのテスト rot。
Phase 6 の変更とは無関係で件数は増えない。)
