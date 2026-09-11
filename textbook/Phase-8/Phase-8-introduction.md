# Phase 8 — Project Manager(実装フェーズ)導入

作業章(`Phase-8-1.md` 以降)を始める前に、この 1 本で Phase 8 の全体像を掴む。
目的 / パイプライン上の位置 / アルゴリズムの 2 層 × 2 トラック / 進め方 / テスト / スコープ /
章一覧 / 実装前チェックリスト / 次のフェーズ。

> **Phase 8 は MVP(Phase 0〜6)完了後の 2 つ目の拡張フェーズ**。README §12.4 / §19 の
> 設計のポイント ──「Graph / Scheduling を工程管理へ適用する。Task / Dependency / DAG モデル、
> Topological Sort、Critical Path、スケジュール生成、ガントチャート。資源平準化に
> Difference Array(imos 法)プリミティブ。Phase 1 の DFS が Topological Sort の土台になる」。

---

## 1. このフェーズの目的

README §12.4 Project Manager ── タスク(所要時間つき)とその依存関係から、全体を最短で終えるスケジュールを組み、完了予定・クリティカルパス・ガントチャートを出す。「先行タスクを必ず前に」= **トポロジカルソート**、「どこを詰めても全体が縮まない律速経路」= **Critical Path Method(CPM)**。資源(人・機材)に上限を付けると **RCPSP(resource-constrained project scheduling)** ── NP 困難。問題タイプは **Graph + Scheduling**。

> **DAG:Directed Acyclic Graph(有向非巡回グラフ)** ── 向きのある辺だけで、どこから
> 出発しても元に戻れないグラフ。依存関係(A の後に B)は自然に DAG になる。閉路があると
> 「A の後に B、B の後に A」となり実行順が定義できない。
> **Critical Path(クリティカルパス)** ── プロジェクトの所要時間(makespan)と同じ長さの、
> 余裕ゼロのタスクの連なり。ここが 1 日延びると全体が 1 日延びる。

| すでに完成しているもの                                                               | いつ                                                |
| ------------------------------------------------------------------------- | ------------------------------------------------- |
| 判別可能ユニオンの仕組み(problem_type ごとに `data` / `assignments` を切り替え)               | Phase 1 / Phase 5-3・7-3 で新 problem_type を足した手順が雛形 |
| Semantic Validation / 構造検証のレジストリ(`SEMANTIC_CHECKS` / `structural_verify`) | Phase 2 / Phase 5-3・7-3                           |
| `POST /solve` `/verify` `/benchmark`(problem_type で汎用ディスパッチ)              | Phase 1〜3                                         |
| `numeric_bound` チェッカー(kind ベース ── `metrics[field]` を読む)                   | Phase 2                                           |
| Difference Array(imos 法)`patterns/difference_array.py::range_add`         | Phase 6(時間帯別の在籍人数)                                |
| DFS プリミティブ `search/dfs.py`                                                | Phase 1                                           |
| OR-Tools CP-SAT を `[project].dependencies` に                              | Phase 6-7(Shift Scheduler)                        |
| networkx を runtime 依存に(手実装グラフの検証オラクル)                                     | Phase 4                                           |

Phase 8 で新しく入るもの:

| 新規                                                            | 中身                                                                                                                                                               |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`project_scheduling` problem_type**                         | `ProjectData`(tasks / dependencies / resource_capacity)/ `ProjectSolution`(task_order / schedule / critical_path / makespan)。判別可能ユニオンに 1 メンバー(Phase 5-3・7-3 と同型) |
| **Topological Sort プリミティブ** `graph/topological.py`            | DFS 後行順の反転 + gray/black で閉路検出。`has_cycle`(validation 用)/ `successors_from_edges`(辺 → 隣接)。registry 非搭載                                                            |
| **CPM プリミティブ** `scheduling/critical_path.py`                  | 前進 / 後退パス → ES/EF/LS/LF/slack/makespan/critical_path。生の dict を取る(`ProjectData` を知らない)。registry 非搭載                                                               |
| **資源プロファイル** `scheduling/project_common.py::resource_profile` | Difference Array(Phase 6)の 2 人目の消費者 ── 各タスクの `[start, finish)` に demand を区間加算 → 時刻別の資源使用量                                                                        |
| **手実装トラック** `scheduling/{cpm,priority_list}.py`               | `cpm`(資源無視 = makespan の下界)/ `priority_list`(余裕の少ない順の貪欲 SGS。資源 feasible だが最適とは限らない)                                                                               |
| **産業ソルバートラック** `scheduling/ortools_project.py`                | `OrToolsCpSatProjectStrategy`(CP-SAT の interval var + `add_cumulative` で RCPSP を厳密に。決定論 = `num_search_workers=1` + `random_seed`)                                |
| **別実装オラクル** `scheduling/networkx_project.py`                  | `NetworkxCpmStrategy`(`nx.topological_sort` + 前進 / 後退パス。非制約 CPM の makespan / クリティカルパスの裏取り)                                                                       |
| **Project Manager ページ**(decitima-ui)                          | `src/features/optimization/project-planner/`。依存 DAG を `GraphCanvas`、スケジュールを新規 `GanttCanvas` で。Phase 4-8 / 7-7 と同型                                                |

---

## 2. パイプライン上の位置 ── 既存に触れず「解き方」だけ足す

`Phase-0-7.md` のとおり、project も **`POST /api/v1/solve` に `problem_type` 付きの
`OptimizationProblem` を渡すだけ**。

```text
POST /api/v1/solve   { problem_type: "project_scheduling", data: { tasks, dependencies, resource_capacity }, objectives: [...] }
      ▼
SolveService.solve()
      ├ (b) ProblemValidationService.validate   ← SEMANTIC_CHECKS["project_scheduling"](8-3 で追加)
      │        + 依存 DAG の閉路検出(topological.has_cycle。route の到達可能性・network の連結性と同じ「計算ゲート」)
      ├ (c) select_strategy(problem)             ← rule-based: 資源制約あり → priority_list / なし → cpm(8-6 で足す 1 分岐)
      ├ (d) CpmScheduleStrategy.solve            ← 新 registry キー "project_scheduling"
      │        topological_sort → cpm(前進 / 後退パス)→ project_solution
      ├ (e) SolutionVerificationService.verify   ← verify_project_structure(8-3)+ 資源プロファイルの検算(8-4)
      └ (f) 永続化 ── **新テーブルなし**(hybrid JSONB。`alembic upgrade head` は no-op)
```

**friction は最小**(すべて増分): 葉モジュール 2 本の新設 / ユニオンに 1 メンバー /
`semantic` に 2 チェック / `structure` に 1 arm / `validation` に閉路ゲート 1 本(8-3)/
`verification` に資源プロファイルの検算 1 本(8-4)/ `patterns/difference_array.py` は**無変更で再利用** /`registry` の 1 キー / `select_strategy` の 1 分岐(8-6)。route / network / shift / travel のロジックには一切触れない。`constraints/elements.py` も**変更不要** ── project 解は全タスクを実施するので `forbidden` / `required_inclusion` は非該当(未知の解型 → `None` → チェッカー素通し)。

---

## 3. アルゴリズムの 2 層 × 2 トラック(`Phase-0-4.md` §2.4)

|         | AlgorithmStrategy(registry に載る)                                                                                | アルゴリズム・プリミティブ(載らない)                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Phase 8 | `CpmScheduleStrategy` / `PriorityListScheduleStrategy` / `OrToolsCpSatProjectStrategy` / `NetworkxCpmStrategy` | `topological_sort` / `has_cycle` / `cpm`(前進 / 後退パス)/ `resource_profile`(imos) |

`AlgorithmMeta.family` は **`"scheduling"`** を再利用(Literal の変更なし。travel が `"optimization"` を
再利用したのと同じ)。

| strategy        | implementation   | 振る舞い                                                                                                        |
| --------------- | ---------------- | ----------------------------------------------------------------------------------------------------------- |
| `cpm`           | handwritten      | 資源を無視して各タスクを最早開始(ES)に置く ── **「資源が無限なら何日で終わるか」の下界**。capacity がきついと Verification が資源超過 hard 違反で `invalid` にする |
| `priority_list` | handwritten      | 余裕(slack)の少ない順に、先行完了以降で資源 capacity を超えない最早時刻へ置く(serial SGS)。**常に資源 feasible。ただし makespan は最適とは限らない**        |
| `cp_sat`        | library:ortools  | CP-SAT の interval var + `add_cumulative`。**RCPSP を厳密に最小化**。priority_list より良い(か同じ)                          |
| `cpm_nx`        | library:networkx | `nx.topological_sort` で非制約 CPM を再計算 ── 手実装 `cpm` の makespan / クリティカルパスの裏取り。`_ops` なし                        |

**教材の核**: Phase 7 の「Knapsack DP は **place cost だけ**で詰める =『移動費用を無視した上界』」と対になる ── Phase 8 の `cpm` は「**依存だけ**を見て詰める =『資源を無視した下界』」。実際の資源capacity を足すと超過し、Verification が `invalid` にする。資源を守った feasible な解は `priority_list`(貪欲なので最適でないことがある)、厳密な最適は `cp_sat`。fixture では **cpm=8(invalid) / priority_list=10 / cp_sat=9**。これが README「手実装をやめて産業ソルバーに切り替える点を知っている」
(§8)を工程管理で再演したもの ── Phase 6 の「手実装探索が破綻 → CP-SAT」と同じ骨。

**`_ops` の単位**: トポロジカルソート = 呼び出し側 strategy が数えるノード訪問数、CPM = 辺の緩和回数(前進 + 後退)、priority_list = 開始時刻をずらして資源をプローブした回数。**単位が違うので割り算しない**
(`CLAUDE.md` 命名規約)。library トラック(cp_sat / cpm_nx)は `_ops` を出さない。

---

## 4. 章一覧(章 = 作業単位)

`Phase-8-M.md` = 作業単位 8-M。厳密な鎖 8-1 → … → 8-6、8-7(UI)は Phase 4-8 に依存。

| 章                           | トピック                                                                  | 依存        | 主な内容                                                                                                                                                              |
| --------------------------- | --------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-8-1](./Phase-8-1.md) | トポロジカルソート(DFS)プリミティブ + 理論(Kahn 法との対比 / 閉路検出)                          | Phase 4   | `graph/topological.py`(新規、`Adjacency` を知らない ── 生の隣接だけ。自己完結)/ DFS 後行順の反転、gray/black、`has_cycle`、`successors_from_edges`                                            |
| [Phase-8-2](./Phase-8-2.md) | Critical Path Method(CPM)プリミティブ                                       | 8-1       | `scheduling/critical_path.py`(新規 ── generic dict を取る、自己完結)/ 前進パス(ES/EF)→ 後退パス(LS/LF)→ slack → クリティカルパス復元、makespan、「資源無視の下界」                                       |
| [Phase-8-3](./Phase-8-3.md) | `project_scheduling` の配線(schema union + semantic + structure + 閉路ゲート) | 8-2       | 葉 2 本 / ユニオン / `semantic.py` 2 チェック / `structure.py` 1 arm(純粋述語)/ `validation.py` の閉路ゲート(`has_cycle`)/ fixture。写経順序リスト付き。`verification` の資源検算は 8-4                |
| [Phase-8-4](./Phase-8-4.md) | 資源プロファイル(imos の 2 人目)+ `cpm` / `priority_list` strategy               | 8-3       | `project_common.py`(新規・共通足回り)/ `cpm.py` / `priority_list.py`(新規)/ `verification._verify_project_resources`(新規、`# (Phase 8-4)`)/ 「cpm は資源超過で invalid」の実演           |
| [Phase-8-5](./Phase-8-5.md) | OR-Tools CP-SAT で RCPSP を厳密に解く                                        | 8-4       | `scheduling/ortools_project.py`(新規)/ interval var + `add_cumulative` + `minimize(makespan)` / 決定論設定 / priority_list との比較                                          |
| [Phase-8-6](./Phase-8-6.md) | registry + select + `cpm_nx` オラクル + end-to-end                        | 8-5       | `scheduling/networkx_project.py`(新規)/ `registry.py`(4 strategy)/ `algorithm_selection.py`(資源制約あり → priority_list)/ 3 者比較のプロパティテスト                                 |
| [Phase-8-7](./Phase-8-7.md) | Project Manager ページ(decitima-ui)                                      | Phase 4-8 | `project-planner/{api,stores,hooks,components,sample-problems.ts}` / `GanttCanvas`(新規・ドメイン非依存)/ DAG は `GraphCanvas` 再利用 / `types.ts`・`menu-tree.ts` に project アーム |

8-1〜8-6 が decitima-api、8-7 が decitima-ui。順序の理由: **プリミティブ(topological_sort / cpm、純粋・自己完結)→ ドメイン配線(problem_type の葉)→ 資源機構 + 手実装 strategy 2 本 → 産業ソルバー → registry + オラクル + e2e → UI**。各章は「その章までのファイルで import 解決」
(進行のルール #15。Q41 / Q42 の教訓)── `topological_sort` / `cpm` はどちらも `ProjectData`(8-3)をimport しない生の関数なので、8-1 / 8-2 は 8-3 に前方依存しない。

registry の作法(進行のルール #15): `registry.py` の `"project_scheduling"` キーは 8-6 で4 strategy をまとめて有効化する。end-to-end パイプライン(validate→select→solve→verify)が緑になるのは 8-6。8-4 / 8-5 の strategy テストは `Strategy().solve(problem)` を直接呼ぶ。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜7 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-8-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 8 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §9 の一覧(冒頭系譜コメントに `Phase 8` を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新されるファイルは変更行が
   `# (Phase 8-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12。
   grep 合言葉: `grep -rn "# (Phase 8" textbook/samples`)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §9 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル                  | 使うもの                               | Phase 8 で書くもの                                                                                                                                |
| -------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| primitives(純粋・主戦場)   | 素の pytest。DB 不要                    | `topological_sort` / `has_cycle` / `cpm`(統合スモーク込み)/ `resource_profile`                                                                       |
| domain(純粋)           | 素の pytest                          | `ProjectData` / `ProjectSolution` の判別可能ユニオン / `SEMANTIC_CHECKS["project_scheduling"]` / `verify_project_structure` / `structural_verify` の番人 |
| algorithms(strategy) | 素の pytest                          | cpm / priority_list / cp_sat / cpm_nx の `solve`。cpm_nx を非制約 CPM のオラクルに(8-6)                                                                  |
| 4 strategy の比較       | 素の pytest(`for seed`)              | `test_project_strategies.py`(cpm = 下界 / priority_list = feasible / cp_sat ≤ priority_list / cpm_nx == cpm)                                   |
| サービス層                | 直接呼ぶ(`test_mst_strategies.py` と同型) | validate→select→solve→verify のパイプライン、資源超過で invalid                                                                                           |
| UI                   | Vitest(node env)                   | project-planner store                                                                                                                        |

**スタブ**: strategy / validation / verification はすべて純粋(DB を持たない)。スタブ不要。

```bash
# decitima-api/backend(overlay end 状態 = Phase 7 end + Phase 8 samples)で
uv run pytest      # 405 passed, 4 deselected
# decitima-ui で
npx vitest run src/features/optimization/project-planner   # store 4 本
```

---

## 7. Phase 8 のスコープと非スコープ

| Phase 8 でやる                                                                                | 送る先                                                                                      |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| `project_scheduling` problem_type / Topological Sort / CPM / RCPSP(priority_list + CP-SAT) | ―                                                                                        |
| 資源プロファイル(imos)/ 資源上限 hard 制約 / 資源超過で `invalid`                                             | ―                                                                                        |
| Project Manager ページ(ガントチャート + 依存 DAG + サンプル選択 + JSON エディタ)                                 | ―                                                                                        |
| ―                                                                                          | **analysis トラック**(`project_analysis.py` + notebook)── 需要が出た Phase 送り                     |
| ―                                                                                          | **小数の所要時間** ── 整数時間単位に限定(imos グリッドが綺麗、README「完了予定日」も日単位)。必要になった Phase で ceil/floor グリッド化 |
| ―                                                                                          | **開始 / 終了の日付**(カレンダー)── domain は t=0 起点の整数。「完了予定日」= UI 側で `start_date + makespan`        |
| ―                                                                                          | **リソースの種類別**(人 / 機材を別枠)/ **タスク分割・中断** ── 需要が出た Phase で `ProjectData` を拡張                 |
| ―                                                                                          | **LLM による工程の構造化** ── Phase 11〜13(LLM)                                                    |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)(Phase 8 end 状態)。各ファイル冒頭の
`# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は §9 の実装前チェックリスト参照。
overlay 検証手順は [`textbook/samples/README.md`](../samples/README.md)。

要点:

- `scheduling/project_common.py` は route の `segments.py` / travel の `travel_common.py` と同じ
  「共通足回り」── 4 strategy は「開始時刻の決め方」だけが違う(cpm=ES / priority_list=貪欲 /
  cp_sat=ソルバー / cpm_nx=ES)。solution の組み立てはここに集約(数値の drift 防止)。
- `patterns/difference_array.py::range_add` は Phase 6 のまま **1 バイトも変えない** ── 2 人目の
  消費者(`resource_profile`)。「区間加算 → 1 回の累積和」= imos の再利用。
- UI は Phase 4-8 / 5-5 / 6-8 / 7-7 と同型の 5 スライス目。`GanttCanvas` は `GraphCanvas` と並ぶ
  ドメイン非依存のチャート(テンプレート還元候補)。

検証: Phase 7 end 状態に Phase 8 samples を overlay し `uv run pytest`(**405 passed, 4 deselected**)/
`ruff` / `uvx pyright`(Phase 8 分 0 errors)/ `alembic upgrade head`(新テーブルなし)。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(project store 4 本)/ `npx eslint`。

---

## 9. Phase 8 実装前チェックリスト

進行のルール #11。行 `8-M` ↔ 章 `Phase-8-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                                                                                                                                                                                   | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 8-1 | `app/algorithms/graph/topological.py`(新規)、`tests/unit/test_topological_sort.py`(新規)。既存ファイルへの変更なし ── 自己完結                                                                                                                                                                                                                                       | `topological_sort(successors) -> list[str]`(DFS 後行順の反転、gray/black で `CyclicGraphError`、近傍 id 昇順で決定論)/ `has_cycle(successors) -> bool`(validation 用 ── 例外にしない)/ `successors_from_edges(nodes, edges)`(孤立 node も key に)                                                                                                                                                                                                                                                 |
| 8-2 | `app/algorithms/scheduling/critical_path.py`(新規)、`tests/unit/test_critical_path.py`(新規)。既存ファイルへの変更なし ── 自己完結                                                                                                                                                                                                                                   | `cpm(durations, successors) -> CpmResult`(前進パスで ES/EF、makespan、後退パスで LS/LF、slack、`relaxations`)/ `critical_chain(...)`(slack 0 を `EF[p]==ES[s]` 辺で 1 本に、複数あれば id 昇順)/ `CpmResult`(frozen dataclass)。`topological_sort` にだけ依存 ── `ProjectData` を知らない                                                                                                                                                                                                                   |
| 8-3 | `app/domain/problems/project_manager.py`・`app/domain/solutions/project_manager.py`(新規)、`tests/unit/test_project_scheduling.py`(新規)、`app/domain/problems/{problem,__init__,semantic}.py`・`app/domain/solutions/{solution,__init__,structure}.py`・`app/services/validation.py`・`tests/fixtures/optimization.py`(現行版)。**`verification.py` は 8-4** | `ProjectTask`(duration>0・resource≥0)/ `TaskDependency`(predecessor→successor)/ `ProjectData`(`model_validator` で端点実在・id 一意・自己依存禁止。**閉路は見ない**)/ `ScheduledTask`(task_id/start/finish/slack)/ `ProjectSolution` / `check_project_has_tasks` + `check_project_resource_capacity` / `verify_project_structure`(純粋述語 ── 順列 / `finish==start+dur` / 依存 / critical=slack0 / makespan)/ `validation` の閉路ゲート(`successors_from_edges` → `has_cycle` → `InfeasibleProblemError`) |
| 8-4 | `app/algorithms/scheduling/{project_common,cpm,priority_list}.py`(新規)、`tests/unit/{test_project_common,test_cpm_strategy}.py`(新規)、`app/services/verification.py`(`_verify_project_resources` 追加、`# (Phase 8-4)`)。`patterns/difference_array.py` は**無変更**                                                                                       | `project_common`: `parse_project_problem` / `build_successors` / `build_durations` / `resource_profile(schedule, demands)`(imos)/ `peak_resource` / `project_solution(data, starts, cpm_result, meta, *, ops)` / `infeasible_project_solution`。`CpmScheduleStrategy`(ES に置く。`_ops` = relaxations)/ `PriorityListScheduleStrategy`(LS 昇順の貪欲 SGS。`_ops` = 資源プローブ)。`_verify_project_resources`(imos で積み直し peak > capacity を hard)                                        |
| 8-5 | `app/algorithms/scheduling/ortools_project.py`(新規)、`tests/unit/test_cpsat_project.py`(新規)。`ortools` は Phase 6-7 で依存済み ── pyproject 変更なし                                                                                                                                                                                                        | `OrToolsCpSatProjectStrategy`(interval var / `start[succ] >= end[pred]` / `add_cumulative(intervals, demands, capacity)` / `minimize(max(end))`。`num_search_workers=1` + `random_seed=0` で決定論。slack / critical_path は手実装 `cpm` から供給。`_ops` なし)                                                                                                                                                                                                                        |
| 8-6 | `app/algorithms/scheduling/networkx_project.py`(新規)、`tests/unit/test_project_strategies.py`(新規)、`app/algorithms/registry.py`・`app/services/algorithm_selection.py`・`tests/unit/test_algorithm_selection.py`(現行版)                                                                                                                               | `NetworkxCpmStrategy`(`nx.topological_sort` + 前進 / 後退パス。非制約 CPM のオラクル。`_ops` なし)/ `registry["project_scheduling"]` = `[cpm, priority_list, cp_sat, cpm_nx]`(手実装先頭)/ `_preferred_name` の project → 資源制約あり `"priority_list"` / なし `"cpm"`                                                                                                                                                                                                                               |
| 8-7 | `ui: project-planner/{api,stores,hooks,components,sample-problems.ts}`(新規)、`ui: components/ui/charts/GanttCanvas.tsx`(新規)、`app/(pages)/optimization/project-planner/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)                                                                                                                       | `solveProject` / `compareProject` / `useProjectPlannerStore` / `ProjectPlannerPanel` / `ProjectGanttView`(DAG は `GraphCanvas`、スケジュールは `GanttCanvas`、クリティカルは赤、資源超過は赤メッセージ)/ `GanttCanvas`(`{id,start,end,slack?,highlight?}[]` を取るタイムラインバー)/ `types.ts` に project アーム / ページは SSG + `RequireAuth`                                                                                                                                                                       |

---

## 10. Phase 8 の成果物

- **textbook**: この `Phase-8/` 一式(導入 + `Phase-8-1`〜`8-7` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/algorithms/graph/topological.py`(新規)/
  `app/algorithms/scheduling/{critical_path,project_common,cpm,priority_list,ortools_project,networkx_project}.py`(新規)/
  `app/domain/problems/project_manager.py`・`app/domain/solutions/project_manager.py`(新規)/
  `app/domain/**`・`app/services/{validation,verification,algorithm_selection}.py`・`app/algorithms/registry.py`(現行版)/ `tests/**`
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/project-planner/**` /
  `src/components/ui/charts/GanttCanvas.tsx` / `src/app/(pages)/optimization/project-planner/page.tsx` /
  `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)
- **既存 Phase 教材への「後続 Phase での改訂」1 行**(`Phase-1-1.md` の判別ユニオンに project_scheduling、
  `Phase-2-introduction.md` に「計算 / 述語」の 4 例目、`Phase-6-introduction.md` に imos の 2 人目の消費者、
  `Phase-0-2.md` §8.1)
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 8 要点**(経緯は `textbook/q_a.md` Q45)
- **`textbook/samples/README.md` の「最終検証」スタンプ**を Phase 8 に更新

---

## 11. 次のフェーズ

Phase 8 完了で **5 つ目の problem_type `project_scheduling`** が端から端まで通る。トポロジカルソート(DFS)と Critical Path Method(前進 / 後退パス)という 2 つの新しいグラフ・スケジューリングプリミティブを実装し、資源制約つきのスケジューリング(RCPSP)で「手実装の貪欲が最適を外す → CP-SAT に切り替える」を工程管理で再演した。Difference Array(Phase 6)は 2 人目の消費者を得た。

その先は README §20 の拡張順 ── **Logistics(Phase 9、Vehicle / Delivery モデル、Capacity Constraint、Route + Packing + 配送順の複合最適化。実規模で `pulp` / `scipy` を足すか判断、ジョブキューもここで検討)→ Simulation(Phase 10、What-if)→ LLM(Phase 11〜13)→ LLM vs Algorithm Benchmark(Phase 14)**。
