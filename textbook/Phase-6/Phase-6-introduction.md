# Phase 6 — Shift Scheduler(実装フェーズ)導入

作業章(`Phase-6-1.md` 以降)を始める前に、この 1 本で Phase 6 の全体像を掴む。
目的 / パイプライン上の位置 / アルゴリズムの 2 層・2 トラック / 進め方 / テスト /
スコープ / 章一覧 / 実装前チェックリスト / 次のフェーズ。

> **Phase 6 は MVP(Phase 0〜6)の総仕上げ**。README §19 の設計のポイント ──「意図的に MVP の
> 最後に置く。組合せ探索という新パラダイム + 多目的 + hard / soft 混在を一度に導入する」。

---

## 1. このフェーズの目的

README §12.2 Shift Scheduler ── スタッフの勤務シフトを、**多目的**(人件費最小化 / 希望休最大化 /
勤務時間均等化)の重み付き和で、**hard 制約**(必要人数 / 週勤務時間上限 / 最大連続勤務日数 /
勤務可能時間 / 必要スキル)を守りながら最適化する。問題タイプは **Constraint Optimization**。

**Phase 6 は「アルゴリズムを書くだけ」の Phase**。理由:

| すでに完成しているもの | いつ | 章 |
| --- | --- | --- |
| `ShiftData` / `Staff` / `ShiftSlot` / `ShiftSolution` スキーマ | Phase 1(凍結)+ Phase 2-1(model_validator) | ── |
| `problem_type` の判別可能ユニオン(shift は 3 メンバーの 1 つ) | Phase 1 / Phase 5-3 で 3 メンバーに | ── |
| Semantic Validation(`check_shift_*` 4 本) | Phase 2-2 | ── |
| Verification(`verify_shift_structure` 5 チェック + `check_staffing`) | Phase 2-3 / 2-4 | ── |
| `POST /solve` `/verify` `/benchmark`(problem_type で汎用ディスパッチ) | Phase 1〜3 | ── |

Phase 6 で新しく入るもの:

| 新規                                                                        | 中身                                                                                               |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **重み付き和の評価器** `domain/objectives/weighted_sum.py`                        | Phase 1 から先送りされた宿題。`Σ wᵢ·orient(metricᵢ)` を minimize 向きに。初の多目的ストラテジーの消費者                        |
| **shift metrics の集約** `domain/solutions/shift_metrics.py`                  | `labor_cost` / `day_off_satisfaction` / `hour_variance` の**計算**を 1 箇所に。検証器と 4 strategy が共有(値が drift しない)。型 `Assignment` は `shift_scheduler.py` に置く(6-1 現行版) |
| **スケジューリング・プリミティブ** `patterns/{sliding_window,difference_array}.py`      | 連続勤務日数の逐次判定 / 時間帯別の在籍人数(imos 法)                                                                  |
| **手実装トラック** `scheduling/{common,greedy,backtracking,branch_and_bound}.py` | Greedy(速いが hard 違反も)/ Backtracking(小規模で最適)/ B&B(下界で枝刈り + 決定論的 anytime)                        |
| **産業ソルバートラック** `scheduling/ortools_cpsat.py`                             | OR-Tools CP-SAT。`implementation="library:ortools"`。実規模でも現実的な時間                                    |
| **分析** `analysis/shift_analysis.py`                                       | 手実装が破綻する規模 / CP-SAT への切り替え点(crossover)/ 多目的 Pareto フロント                                         |
| **Shift Scheduler ページ**(decitima-ui)                                     | `src/features/optimization/shift-scheduler/`。シフト表の可視化。Phase 4-8 / 5-5 と同型                        |

---

## 2. パイプライン上の位置 ── 既存に触れず「解き方」だけ足す

Phase 1 で決めたとおり(`Phase-0-7.md`)、shift も **`POST /api/v1/solve` に `problem_type` 付きの
`OptimizationProblem` を渡すだけ**。

```text
POST /api/v1/solve   { problem_type: "shift_scheduling", data: { staff, slots }, objectives: [...] }
      ▼
SolveService.solve()
      ├ (b) ProblemValidationService.validate   ← SEMANTIC_CHECKS["shift_scheduling"](Phase 2 完成)
      ├ (c) select_strategy(problem)             ← rule-based: shift → backtracking(6-3 で足す 1 行)
      ├ (d) BacktrackingShiftStrategy.solve       ← 新 registry キー "shift_scheduling"
      │         多目的の重み付き和で候補割当を採点(weighted_sum、6-1)
      ├ (e) SolutionVerificationService.verify   ← verify_shift_structure(Phase 2 完成。+ hour_variance)
      └ (f) 永続化 ── **新テーブルなし**(hybrid JSONB。`alembic upgrade head` は no-op)
```

**friction は最小**(すべて増分): objectives 評価器の新設 / `patterns` と `scheduling` の新ファイル /
`registry` の 1 キー / `select_strategy` の 1 分岐 / `verify_shift_structure` に metric 1 本 /
`pyproject.toml` に `ortools` 1 行。route / network のロジックには一切触れない。

唯一の後追い修正: Phase 5 まで「未登録 problem_type」の例に使っていた shift に strategy が付くので、
その 3 テスト(`test_registry` / `test_solve_service` / `test_solve_api`)を「registry キーを空にして
候補ゼロ」に書き換える(#16)。

---

## 3. アルゴリズムの 2 層 × 2 トラック

**2 層**(`Phase-0-4.md` §2.4):

|         | AlgorithmStrategy(registry に載る)                                        | アルゴリズム・プリミティブ(載らない)                                    |
| ------- | --------------------------------------------------------------------- | ---------------------------------------------------- |
| Phase 6 | `Greedy` / `Backtracking` / `BranchAndBound` / `OrToolsCpSat` (shift) | `sliding_window` / `difference_array` / `weighted_sum` |

**2 トラック**(`CLAUDE.md`「アルゴリズム実装方針 — 2 トラック」):

| strategy | implementation | 振る舞い |
| --- | --- | --- |
| `GreedyShiftStrategy` | `handwritten` | 速いが hard 制約を破ることがある(`status=invalid` candidate) |
| `BacktrackingShiftStrategy` | `handwritten` | 小規模なら最適。規模が増えると最悪 O(kⁿ) |
| `BranchAndBoundShiftStrategy` | `handwritten` | Backtracking + 下界で枝刈り。ノード予算超過で最良解 + `_truncated` |
| `OrToolsCpSatShiftStrategy` | `library:ortools` | 実規模でも現実的。`_ops` を出さない(仕事がソルバーの中) |

**`_ops` の扱い**: Greedy = 割当試行、Backtracking = 展開ノード、B&B = ノード + 下界計算。
**単位が違うので割り算しない**。CP-SAT は `_ops` なし(`operation_count = None`)。

**中心的課題**(`Phase-0-5.md` §3.2 / README §19): バックトラッキング / B&B は最悪指数時間。
教材の小例(3×2×2)は一瞬、小規模店舗(8×7×3)は秒〜十数秒、中規模(20×7×3)は**現実的に
終わらない → CP-SAT 必須**。この破綻点と切り替えを 6-6 で実測し、6-7 で CP-SAT を用意する。

---

## 4. 章一覧(章 = 作業単位)

`Phase-6-M.md` = 作業単位 6-M。

| 章 | トピック | 依存 | 主な内容 |
| --- | --- | --- | --- |
| [Phase-6-1](./Phase-6-1.md) | 重み付き和の評価器 ── `objectives/`(Phase 1 からの宿題) | Phase 2 | `weighted_sum` / `shift_metrics.py`(新設・集約)/ `hour_variance` / `shift_scheduler.py`・`structure.py` 現行版 |
| [Phase-6-2](./Phase-6-2.md) | スケジューリング・プリミティブ ── Sliding Window / Difference Array | 6-1 | `sliding_window.py`(連続勤務日数の逐次判定)/ `difference_array.py`(imos 法) |
| [Phase-6-3](./Phase-6-3.md) | Greedy ── 速いが hard 違反もある | 6-2 | `scheduling/{common,greedy}.py` / registry 配線 / `select_strategy` の shift 分岐 / `build_scaled_shift_problem` |
| [Phase-6-4](./Phase-6-4.md) | Backtracking ── 小規模で最適 | 6-3 | `scheduling/backtracking.py`(DFS + 枝刈り + weighted_sum スコア) |
| [Phase-6-5](./Phase-6-5.md) | Branch and Bound ── 下界で枝刈り + 決定論的 anytime | 6-4 | `scheduling/branch_and_bound.py`(可容な下界 / ノード予算 / `_truncated`) |
| [Phase-6-6](./Phase-6-6.md) | 手実装の破綻 ── 計算量と実測(理論 + オラクル) | 6-3, 6-4, 6-5 | `test_shift_breakdown.py`(全列挙オラクル / 破綻シナリオ)。**実装ファイルなし** |
| [Phase-6-7](./Phase-6-7.md) | OR-Tools CP-SAT トラック + 分析 | 6-6 | `scheduling/ortools_cpsat.py` / `ortools` 依存 / registry 最終形 / `analysis/shift_analysis.py` / end-to-end パイプライン |
| [Phase-6-8](./Phase-6-8.md) | Shift Scheduler ページ(decitima-ui) | Phase 4-8 | `shift-scheduler/{api,stores,hooks,components}` / `ShiftGrid` / `types.ts`・`menu-tree.ts` に shift アーム |

6-1〜6-7 が decitima-api、6-8 が decitima-ui。順序の理由: **採点機構(objectives)→ 部品(primitives)
→ 速い近似(Greedy)→ 厳密(Backtracking)→ 枝刈り(B&B)→ なぜ破綻するか → 産業ソルバー → UI**。

registry の作法(進行のルール #15): `registry.py` の `"shift_scheduling"` キーは 6-3 で Greedy だけ、
6-4 で Backtracking、6-5 で B&B、6-7 で CP-SAT を段階的にコメント解除する。各章がそのぶんのテストを持つ。
end-to-end パイプライン(validate→select→solve→verify)が緑になるのは registry が埋まる 6-7。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜5 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-6-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 6 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests,analysis,alembic,scripts}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §8 の一覧(冒頭系譜コメントに当該 Phase を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新されるファイルは変更行が
   `#(Phase 6-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12)。以前の章に残る
   「`registry.py` の該当行をコメントアウトして出荷 / 現行版を新 samples に置く」等の記述は、
   Phase 毎に samples フォルダがあった時代(Step 2 以前)の運用の記録。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §9 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル | 使うもの | Phase 6 で書くもの |
| --- | --- | --- |
| primitives(純粋・主戦場) | 素の pytest。DB 不要 | `weighted_sum` / `max_consecutive_days` / `run_length_at` / `range_add` |
| domain(純粋) | 素の pytest | `shift_metrics` の集約(検証器経由で `test_verification_service.py` が pin)/ `verify_shift_structure` の `hour_variance` |
| algorithms(strategy) | 素の pytest | `Greedy` / `Backtracking` / `B&B` / `CP-SAT` の `solve`。全列挙オラクルで裏取り(6-6) |
| 4 strategy の一致 | 素の pytest(`@parametrize`) | `test_shift_strategies.py`(labor_cost / day_off_satisfaction / 最適スコア) |
| サービス層 | `db_session`(SQLite)+ `FakeRedis` | `select_strategy` の shift 分岐 / SolveService の shift ケース |
| API | `httpx.AsyncClient` + 依存差し替え | `POST /solve` の shift 「候補ゼロ → 400」 |
| 分析トラック | 素の pytest(pandas) | `analysis/shift_analysis.py`(`by_size` / `crossover_size` / `pareto_front`) |
| UI | Vitest + jsdom / node env | shift-scheduler store |

**スタブ**: 手実装 strategy は純粋(スタブ不要)。CP-SAT も `num_search_workers=1` + `random_seed`
固定で決定論的 ── purity テスト(同入力 → 同出力)が緑。

```bash
# decitima-api/backend(overlay end 状態 = Phase 5 end + Phase 6 samples + ortools)で
uv run pytest      # 271 passed, 2 deselected
# decitima-ui で
npx vitest run src/features/optimization   # 17 passed
```

---

## 7. Phase 6 のスコープと非スコープ

| Phase 6 でやる | 送る先 |
| --- | --- |
| 重み付き和の評価器 / Sliding Window / Difference Array | ― |
| Greedy / Backtracking / Branch and Bound(手実装)/ OR-Tools CP-SAT | ― |
| 3 目的(人件費 / 希望休 / 勤務時間均等化)の重み付き和 | ― |
| `analysis/shift_analysis.py`(破綻境界 + Pareto) | ― |
| Shift Scheduler ページ(サンプル選択 + JSON エディタ + シフト表可視化) | ― |
| ― | **weighted_sum の正規化**(基準解比 / min-max)── スケール差の落とし穴は明示するが実装は将来 |
| ― | **入力アダプタ**(スタッフ名簿 Excel → `OptimizationProblem`)── `app/adapters/`、Phase 6+ で需要が出たら |
| ― | **B&B の壁時計 anytime**(スレッドを止めて途中解を返す)── 純粋性 + MVP の割り切りで見送り。ノード予算で代替 |
| ― | **CP-SAT の hour_variance を厳密な分散で**(二乗を扱う)── spread(max−min)で代理。教材の観察点 |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)（Phase 6 end 状態）。各ファイル冒頭の
`# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は **この Phase が作成 / 更新するファイル**
（= この Phase での写経対象。冒頭系譜に当該 Phase を含むもの）。overlay 検証手順は
[`textbook/samples/README.md`](../samples/README.md)。

`textbook/samples/README.md` の「Phase 6 で作る / 変えるもの」表を参照。要点:

- `app/domain/objectives/` は Phase 1 で一度作って撤回、Phase 6 で初の消費者(shift strategy)を得て復活。
- `app/algorithms/scheduling/common.py` は route の `segments.py` / network の `mst.py` と同じ「共通足回り」。
- `analysis/` は Phase 3-8 で作った器に **1 モジュール足すだけ**(移設・作り直しなし)。
- UI は Phase 4-8 / 5-5 の Route Planner / Network Designer と同型の 3 スライス目。

検証: Phase 5 end 状態に Phase 6 samples を overlay し `uv run pytest`(**271 passed, 2 deselected**)/
`ruff` / `uvx pyright`(Phase 6 分 0 errors)/ `alembic upgrade head`(新テーブルなし)/ notebook 実行。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(**17 passed**)/ `npx eslint`。

---

## 9. Phase 6 実装前チェックリスト

進行のルール #11。行 `6-M` ↔ 章 `Phase-6-M`。

| # | 作る / 変えるファイル | 主なクラス・関数の責務(1 行) |
| --- | --- | --- |
| 6-1 | `domain/objectives/{__init__,weighted_sum}.py`(新規)、`domain/solutions/shift_metrics.py`(新規・集約)、`domain/solutions/{shift_scheduler,structure}.py`(現行版)、`tests/unit/{test_weighted_sum,test_verification_service}.py` | `weighted_sum(objectives, metrics) -> float`(minimize 向きスカラー)/ `shift_metrics.assignment_metrics`(labor_cost / day_off_satisfaction / hour_variance を 1 箇所で計算 ── 検証器と 4 strategy が共有)/ `verify_shift_structure` はそれを呼ぶだけに / `shift_scheduler.py` に `type Assignment`(共有語彙。両レイヤーが循環なしで届く葉) |
| 6-2 | `algorithms/patterns/{sliding_window,difference_array}.py`(新規)、`tests/unit/test_scheduling_primitives.py` | `max_consecutive_days` / `run_length_at`(逐次の連続日数判定)/ `range_add`(imos 法の区間加算)。registry 非搭載の純粋関数 |
| 6-3 | `algorithms/scheduling/{common,greedy}.py`(新規)、`registry.py`(Greedy)、`services/algorithm_selection.py`(現行版)、`tests/fixtures/optimization.py`(現行版)、`tests/unit/{test_greedy_shift,test_algorithm_selection}.py` | `parse_shift_problem` / `eligible_staff` / `score`(weighted_sum 呼び)/ `respects_hard` / `shift_solution` / `GreedyShiftStrategy`(tightness 順に最安割当)/ `_preferred_name` の shift → `"backtracking"` / `build_scaled_shift_problem(n_staff, n_days, seed)` |
| 6-4 | `algorithms/scheduling/backtracking.py`(新規)、`registry.py`(Backtracking)、`tests/unit/test_backtracking_shift.py` | `BacktrackingShiftStrategy`(スロット順の DFS、週時間 + 連続日数で枝刈り、葉で weighted_sum スコア、最良保持) |
| 6-5 | `algorithms/scheduling/branch_and_bound.py`(新規)、`registry.py`(B&B)、`tests/unit/test_branch_and_bound_shift.py` | `BranchAndBoundShiftStrategy`(= Backtracking + `_lower_bound` の可容下界で枝刈り + `_MAX_NODES` 予算超過で最良解 + `metrics["_truncated"]`) |
| 6-6 | `tests/unit/test_shift_breakdown.py`(新規。実装なし) | `_brute_force_optimal`(全割当の全列挙オラクル。小規模専用)/ 3 手実装が小規模で最適と一致 / 破綻シナリオ表 |
| 6-7 | `algorithms/scheduling/ortools_cpsat.py`(新規)、`analysis/shift_analysis.py`(新規)、`analysis/data/sample_shift_runs.jsonl`、`analysis/notebooks/shift_explore.ipynb`、`registry.py`(CP-SAT)、`pyproject.toml`(`ortools`)、`tests/unit/{test_ortools_cpsat_shift,test_shift_strategies}.py`、`tests/analysis/test_shift_analysis.py`、`tests/unit/{test_registry,test_solve_service}.py`・`tests/api/test_solve_api.py`(現行版) | `OrToolsCpSatShiftStrategy`(x[s,t] bool / 人数・週時間・連続日数制約 / weighted_sum を整数線形式に。決定論設定)/ `load_shift_benchmark_runs` / `by_size` / `handwritten_vs_cpsat` / `crossover_size` / `pareto_front` |
| 6-8 | `ui: shift-scheduler/{api,stores,hooks,components,sample-problems.ts}`(新規)、`app/(pages)/optimization/shift-scheduler/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)、`route-planner`・`network-designer` の store test(現行版) | `solveShift` / `compareShift` / `useShiftSchedulerStore` / `ShiftSchedulerPanel` / `ShiftGrid`(スロット行 × 割当スタッフ、人数不足は赤)/ `types.ts` に shift アーム / ページは SSG + `RequireAuth` |

---

## 10. Phase 6 の成果物

- **textbook**: この `Phase-6/` 一式(導入 + `Phase-6-1`〜`6-8` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/domain/objectives/**` / `app/domain/solutions/shift_metrics.py`(新規)/
  `app/algorithms/patterns/{sliding_window,difference_array}.py` /
  `app/algorithms/scheduling/**` / `app/domain/solutions/{shift_scheduler,structure}.py`(現行版)/
  `app/services/algorithm_selection.py`(現行版)/ `analysis/shift_analysis.py` / `tests/**` / `registry.py` + `pyproject.toml` への追記
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/shift-scheduler/**` /
  `src/app/(pages)/optimization/shift-scheduler/page.tsx` / `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)
- **Phase 1 / 2 / 3 / 4 / 5 教材への「以降 Phase で修正予定 ── Phase 6-1 / 6-3」マーカー**(shift_scheduler / structure / fixtures / algorithm_selection)
- **`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の objectives マーカー**を「Phase 6 で確定 ── 実装済み」に
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 6 要点**(経緯は `textbook/q_a.md` Q36)

---

## 11. 次のフェーズ

Phase 6 完了で **MVP(Phase 0〜6)が完成**する ── route_planning / network_design / shift_scheduling の
3 problem_type が端から端まで通り、手実装トラックと産業ソルバートラックが同じ契約で並び、
Benchmark と `analysis/` で「いつ切り替えるべきか」を実測できる。

その先は README §20 の拡張順 ── **Travel Planner(Phase 7、Knapsack DP)→ Project Manager(Phase 8、
Critical Path)→ Logistics(Phase 9)→ Simulation(Phase 10)→ LLM(Phase 11〜13)→
LLM vs Algorithm Benchmark(Phase 14)**。`analysis/` は Phase 14 の実験フレームワークまで育つ。
