# Phase 6-7: OR-Tools CP-SAT トラック + 分析(作業単位 6-7)

## この章のゴール

手実装が破綻する規模のために、**同じ `AlgorithmStrategy` 契約・同じ `ShiftSolution`** の裏でOR-Tools CP-SAT を動かす `OrToolsCpSatShiftStrategy` を作る。違うのは `implementation="library:ortools"`と、中身が CP-SAT の探索であること(`CLAUDE.md`「アルゴリズム実装方針 — 2 トラック」)。

そして `analysis/shift_analysis.py` で「手実装が破綻して CP-SAT に切り替えるべき規模」を実測する。

**この章で新規作成するファイル**: `app/algorithms/scheduling/ortools_cpsat.py`、
`analysis/shift_analysis.py`、`analysis/data/sample_shift_runs.jsonl`、
`analysis/notebooks/shift_explore.ipynb`、`tests/unit/test_ortools_cpsat_shift.py`、
`tests/unit/test_shift_strategies.py`、`tests/analysis/test_shift_analysis.py`。
**既存ファイルへの変更**(現行版は samples): `tests/unit/test_registry.py`、
`tests/unit/test_solve_service.py`、`tests/api/test_solve_api.py`
(「未登録 problem_type」テストを「registry キーを空にして候補ゼロ」に)。
**既存テンプレートへの追記**: `app/algorithms/registry.py`(CP-SAT のコメントを外す)、
`pyproject.toml`(`[project].dependencies` に `ortools`)。

対応サンプル: 上記(registry / pyproject は差分)。設計は README §8、`Phase-0-4.md` §5.3、`Phase-3-8.md`。

---

## 1. `ortools` を依存に追加

```toml
# pyproject.toml の [project].dependencies に 1 行
dependencies = [
  # ...
  "networkx>=3.3",
  "numpy>=2.0",
  "ortools",       # ← Phase 6。Phase 8/9 で再利用
]
```

`uv add ortools`(または上記を書いて `uv sync`)。`ortools` は `library:*` トラックが `POST /solve` /`/benchmark` のリクエスト経路で動くので **runtime 依存**(numpy / pandas の dev 依存とは違う。README §8 の境界表)。

> OR-Tools（Google OR-Tools）**は、Pythonから使える**数理最適化・組合せ最適化のためのライブラリ。
> **「制約を満たしながら最適な答えを探す」** ような問題に強い。

---

## 2. `OrToolsCpSatShiftStrategy` ── モデリング

```python
# app/algorithms/scheduling/ortools_cpsat.py(要点。全文は samples)
from ortools.sat.python import cp_model

class OrToolsCpSatShiftStrategy:
    meta = AlgorithmMeta(name="cp_sat", family="scheduling", implementation="library:ortools", ...)

    def solve(self, problem):
        data = parse_shift_problem(problem)
        model = cp_model.CpModel()
        # x[s, t] bool ── eligible な (staff, slot) だけ変数を作る
        x = {(st.id, slot.id): model.new_bool_var(...) for slot in data.slots for st in elig[slot.id]}
        for slot in data.slots:
            model.add(sum(x[st.id, slot.id] for st in elig[slot.id]) == slot.required_headcount)
        for st in data.staff:
            model.add(sum(x[st.id, s.id] * int(slot_hours(s)) for s ...) <= int(data.max_weekly_hours))
        # works_on_day[s, d] = その日どれかに入ったか(add_max_equality)。連続 (max+1) 日窓で Σ ≤ max
        model.minimize(_objective(model, problem, data, x, work_day))

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1     # 決定論
        solver.parameters.random_seed = 0
        status = solver.solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return shift_solution(None, data=data, ops=None, meta=self.meta)   # 実行不能
        assignments = {tid: [sid for (sid, t), v in x.items() if t == tid and solver.value(v)] ...}
        return shift_solution(assignments, data=data, ops=None, meta=self.meta)
```

- **`_ops` を出さない**(`ops=None` → `operation_count = None`)── 仕事がソルバーの中。
  「ライブラリトラックは操作回数を出せない」= 2 トラック比較の論点(`Phase-0-4.md`、README §8)。
- **目的の線形化**(`_objective`):
  - `labor_cost`(minimize)→ `+ w · Σ x·wage·hours`(整数線形)
  - `day_off_satisfaction`(maximize)→ 希望休違反 `works_on_day[s, off_day]` を `+ (w/希望休数)` で最小化
    (`satisfaction = 1 − 違反/希望休数` なので、違反を減らす = 満足度を上げる)
  - `hour_variance`(minimize)→ CP-SAT は二乗を嫌うので **勤務時間の spread(max − min)** を代理に最小化。
    **手実装は本物の分散でスコアするので、両者の最適が完全一致しないことがある** ── 教材の観察点(ライブラリはモデルの表現力に合わせて目的を近似する)。
  - weight(小数)は `_SCALE=1000` で整数係数にする。
- **決定論**: `num_search_workers=1` + `random_seed` 固定 → `test_deterministic_same_input_same_output`
  (route の `library:networkx` と同じ purity テスト)も緑。

---

## 3. registry 最終形

```python
# app/algorithms/registry.py(CP-SAT のコメントを外す ── 最終形)
from app.algorithms.scheduling.ortools_cpsat import OrToolsCpSatShiftStrategy

REGISTRY["shift_scheduling"] = [
    GreedyShiftStrategy(),
    BacktrackingShiftStrategy(),
    BranchAndBoundShiftStrategy(),
    OrToolsCpSatShiftStrategy(),          # ← 有効化
]
```

**この 1 行で `POST /solve` の全経路が shift で通る** ── validate → `select_strategy` → solve → verify が、候補が入って初めて end-to-end で緑になる。`test_shift_strategies.py::test_shift_end_to_end_pipeline` が
それを 1 本で確認する(Phase 5-3 → 5-4 の `test_network_design_end_to_end_pipeline` と同型 ── #15 / Q35)。

### 「未登録 problem_type」テストの後追い修正(#16)

Phase 5 までは `shift_scheduling` を「registry に何も無い problem_type」の例に使っていた(`test_registry.py` / `test_solve_service.py` / `test_solve_api.py`)。
Phase 6 で全 problem_type にstrategy が付いたので、「registry キーを空にして候補ゼロ → `NoAlgorithmError` / 400」に書き換える:

```python
def test_select_strategy_no_candidates_raises(monkeypatch):
    monkeypatch.setitem(REGISTRY, "shift_scheduling", [])
    with pytest.raises(NoAlgorithmError):
        select_strategy(build_shift_problem())
```

3 ファイルとも Phase 6 samples に現行版を置き、Phase 1 samples 側にマーカー(#12.2 A)。

---

## 4. `analysis/shift_analysis.py`

Phase 3-8 で作った `analysis/` に **1 モジュール足すだけ**(移設・作り直しなし。`Phase-3-8.md` の型):

```python
# analysis/shift_analysis.py(要点。全文は samples)
def load_shift_benchmark_runs(path) -> pd.DataFrame:   # + size 列(スタッフ数 × スロット数)
def by_size(df) -> pd.DataFrame:                        # size × (algorithm, implementation) の中央値
def handwritten_vs_cpsat(df) -> pd.DataFrame:           # 厳密な手実装(BT/B&B)と CP-SAT の speedup
def crossover_size(df) -> float | None:                 # CP-SAT がはじめて手実装より速くなる size
def pareto_front(df) -> pd.DataFrame:                   # labor_cost(小)× day_off_satisfaction(大)の非支配
```

- **`handwritten_vs_cpsat` は Greedy を除く**(`_EXACT_HANDWRITTEN = ("backtracking", "branch_and_bound")`)
  ── Greedy は多項式時間だが解が最適でない。「破綻」を見るのは厳密な手実装だけ。
- `analysis/` は app から切り離した dev トラック(pandas / matplotlib は `[dependency-groups].analysis`。
  `app` からは import しない)。`analysis/data/sample_shift_runs.jsonl` は固定サンプル
  (実データは `python -m analysis.export benchmark_runs ...` で作れる)。
- notebook(`shift_explore.ipynb`)はサンプルデータで完結し `nbconvert --execute` で回る。

---

## 5. まとめ

- `OrToolsCpSatShiftStrategy` = 同契約・同 `ShiftSolution` の裏で CP-SAT。`_ops` なし。
- 目的は整数線形式に(hour_variance は spread で代理 ── 手実装と最適が完全一致しないことがある)。
- `num_search_workers=1` + `random_seed` で決定論 → purity テスト緑。
- registry 最終形。end-to-end パイプラインはここで緑。「未登録 problem_type」テストを現行版に。
- `analysis/shift_analysis.py` で crossover(切り替え点)と Pareto を実測。

## テスト観点(`samples/tests/unit/{test_ortools_cpsat_shift,test_shift_strategies}.py` / `tests/analysis/test_shift_analysis.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_ortools_cpsat_shift.py`** ── 対象 = `OrToolsCpSatShiftStrategy.solve`。スタブ不要
> (`num_search_workers=1` + `random_seed` で決定論)。
> 
> **`test_shift_strategies.py`** ── 対象 = registry の 4 strategy の一致 + フルパイプライン。
> ドライバ = `@parametrize`。end-to-end は registry が埋まるこの章で初めて緑(#15)。
> 
> **`test_shift_analysis.py`** ── 対象 = DataFrame → DataFrame の純粋関数(`analysis/` は app から切り離し)。

| ケース                                                                    | 期待                                                                       |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| CP-SAT の `meta.implementation`                                         | `"library:ortools"`                                                      |
| CP-SAT で例題を解く                                                          | verify 後 `valid` / `labor_cost == 20000` / `day_off_satisfaction == 1.0` |
| CP-SAT の `_ops`                                                        | metrics に無い                                                              |
| 実行不能な問題                                                                | `status == "infeasible"`                                                 |
| CP-SAT 同入力 → 同出力                                                       | `model_dump()` が一致                                                       |
| 4 strategy(BT/B&B/CP-SAT は厳密)                                          | verify 後 `labor_cost` / `day_off_satisfaction` / 最適スコアが一致                |
| `test_shift_end_to_end_pipeline`                                       | validate→select(`"backtracking"`)→solve→verify で `valid`                 |
| `by_size` / `handwritten_vs_cpsat` / `crossover_size` / `pareto_front` | ロング表 / speedup / 交差 size / 非支配点                                          |

`uv run pytest tests/unit/test_ortools_cpsat_shift.py tests/unit/test_shift_strategies.py tests/analysis/test_shift_analysis.py` /
`uvx pyright app/algorithms/scheduling`。

---

次章([Phase-6-8](./Phase-6-8.md))では、作業単位 6-8 ── Shift Scheduler ページ(decitima-ui)。
Phase 4-8 / 5-5 と同型で、スタッフとスロットを編集 → シフト表を可視化、4 アルゴリズムを横並び比較する。
`types.ts` / `menu-tree.ts` に shift アームを足す。
