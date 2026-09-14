# Phase 10 — What-if Simulation(実装フェーズ)導入

作業章(`Phase-10-1.md` 以降)を始める前に、この 1 本で Phase 10 の全体像を掴む。
目的 / パイプライン上の位置 / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト /
次のフェーズ。

> **Phase 10 は MVP(Phase 0〜6)完了後の 4 つ目の拡張フェーズ**。README §13/§19「What-ifSimulation」──「意思決定支援レイヤーへ拡張する。条件変更 / 複数シナリオ生成 / Cost・Time・Quality 比較 / Sensitivity Analysis。`POST /simulate`。シナリオ = 一部の値を変えて複製した`OptimizationProblem`。スキーマ自体は不変のまま扱う。全ドメインが出そろった後に置く
> (シミュレーションする対象があるように)」。
> Phase 9 と同様、README の記述はスキーマ・実行モデルまでは確定していない。開始にあたりユーザーに 3 点を確認し、以下の方針で進める(詳細は `textbook/q_a.md` Q53):
> 
> | 論点                   | 決定                                                                            |
> | -------------------- | ----------------------------------------------------------------------------- |
> | 実行モデル                | **非同期(Phase 9-8 のジョブキューを再利用)**。同期版は作らない                                       |
> | override の表現         | **汎用 dict マージ(RFC 7386 JSON Merge Patch 相当)+ Pydantic 再検証**。ドメイン別の名前付きノブは作らない |
> | Sensitivity Analysis | 単純スイープに加え、**二分探索による閾値発見**(`find_threshold`)を追加                                |

---

## 1. このフェーズの目的

README §13「What-if Simulation」── 最適解を1つ提示するだけでなく、**条件を変えた場合に結果がどう変化するか**を比較する。

```text
車両数　配送時間　コスト
5台　　　6.2h　　　¥80,000
4台　　　7.8h　　　¥72,000
3台　　　10.4h　　　¥64,000
```

目的は「最適解は何か?」だけでなく、**「どの条件なら、どの選択をするべきか?」**を支援すること。

Phase 10 は **新しい `problem_type` やドメインアルゴリズムを追加する回ではない**。Phase 4〜9で作った6ドメイン(route_planning / network_design / shift_scheduling / travel_planning /project_scheduling / logistics_planning)の `OptimizationProblem` を「一部の値を変えて複製」し、既存の Validation → アルゴリズム選択 → solve → Verification パイプラインを複数回・非同期に回して比較する**横断オーケストレーション層**。ドメイン固有コードは一切増えない ──
これは6ドメインが揃った今だからこそ書ける、教材として綺麗な「まとめ」の Phase になる(README「全ドメインが出そろった後に置く」の意図そのもの)。

| すでに完成しているもの                                                                   | いつ        |
| ----------------------------------------------------------------------------- | --------- |
| 6 ドメインの `OptimizationProblem` / `select_strategy` / Validation / Verification | Phase 1〜9 |
| ジョブキュー基盤(`arq` + Redis、`POST /jobs` / `GET /jobs/{id}`)                       | Phase 9-8 |
| Phase 3 `BenchmarkService`(1 問題 × 複数アルゴリズムを横並び実測する対称形)                        | Phase 3   |
| 二分探索プリミティブ(値の探索)`search/binary_search.py`                                     | Phase 1   |

Phase 10 で新しく入るもの:

| 新規                                           | 中身                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **`apply_overrides`**                        | `OptimizationProblem` を dict に落として override を深くマージ→再検証する汎用関数(RFC 7386 JSON Merge Patch 相当)。ドメイン非依存      |
| **`SimulationService.run_simulation`**       | base + シナリオ群を実行し比較結果を返す、永続化を持たない純粋なオーケストレーション(Phase 3 BenchmarkService と対称)                             |
| **`find_threshold`**                         | 「答えを二分探索する」プリミティブ。単調な `evaluate` から条件を満たす最小のパラメータを O(log n) で見つける                                       |
| **ジョブキュー配線**                                 | `POST /api/v1/simulate`(新規)。結果のポーリングは既存 `GET /api/v1/jobs/{id}` を再利用(`JobStatusResponse.result` の型を広げる) |
| **分析トラック** `analysis/simulation_analysis.py` | シナリオ比較表・感度分析カーブの集計                                                                                      |
| **Simulation ページ**(decitima-ui)              | `src/features/optimization/simulation/`。シナリオ JSON エディタ + 比較表                                            |

---

## 2. パイプライン上の位置 ── 既存に触れず「複数回まわす層」を足す

```text
POST /api/v1/simulate   { problem: {...}, scenarios: [{label, overrides}, ...], sensitivity?: {...} }
      ▼
JobService.enqueue_simulation()
      ├ (a) レート制限(resource="simulate_submit"。solve/job とは別枠)
      ├ (b) base problem だけ Validation(明らかに無理な base は投入前に弾く)
      ├ (c) Job 行を作成(既存 jobs テーブルを再利用、新テーブルなし)+ commit
      └ (d) arq へ "simulate_job" をエンキュー
      ▼
app/worker.py::simulate_job(ctx, job_id)
      └ SimulationService.run_simulation(request) を呼ぶだけ
             ├ base を solve(Validation→select_strategy→solve→verify)。algorithm 名を固定
             ├ 各シナリオ: apply_overrides → 同じパイプライン。1 件破綻しても他は続行
             │      (invalid_scenario として記録。例外にしない)
             └ sensitivity 指定時: find_threshold で二分探索(O(log n) 回だけ solve)
      ▼
GET /api/v1/jobs/{id}   ← 既存のまま(JobStatusResponse.result の型だけ広げる)
```

**friction は最小**(すべて増分): 新規スキーマ 1 ファイル / 新規サービス 1 ファイル /
新規アルゴリズムプリミティブ 1 ファイル / ジョブキューへの新しい enqueue 経路 1 本 / 既存`JobStatusResponse.result` の型を広げる 1 行。route/network/shift/travel/project/logistics
のドメインロジック・スキーマには一切触れない(README「スキーマ自体は不変」)。

**Phase 9 への改訂が 1 件だけ発生する**: `schemas/job.py::JobStatusResponse.result` はPhase 9-8 時点で `CandidateSolution | None` に固定されていた(重い solve を 1 件だけ非同期化する設計だったため)。simulate ジョブは結果として `SimulationResult`(base/scenarios を持つ)
を返すので、この型を `CandidateSolution | SimulationResult | None` に広げる。**`CandidateSolution`と `SimulationResult` は必須フィールドが重ならない**(前者は status/assignments/produced_by、
後者は base/scenarios)ため、判別用の `kind` タグを持たない素の union でも Pydantic の smartunion がどちらの形か判別できる ── `app/worker.py::solve_job` の書き込み方も既存の`test_jobs_e2e.py` のアサーションも変える必要が無い(進行のルール #12.4 のスモークは「無改造で green のまま」で満たされる、詳細は Phase-10-4)。

---

## 3. 章一覧(章 = 作業単位)

`Phase-10-M.md` = 作業単位 10-M。10-1 → 10-2 → 10-3 → 10-4 は鎖、10-5(分析)は 10-4 の後、
10-6(UI)は 10-4 に依存する。

| 章                             | トピック                                                 | 依存               | 主な内容                                                                                                                                                            |
| ----------------------------- | ---------------------------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-10-1](./Phase-10-1.md) | スキーマ + `apply_overrides`(汎用 override マージ)            | Phase 1〜9 の全ドメイン | `schemas/simulation.py`(`ScenarioOverride`/`SimulationRequest`/`ScenarioResult`/`SimulationResult`)/ `services/simulation.py` の `apply_overrides`・`_deep_merge` |
| [Phase-10-2](./Phase-10-2.md) | `SimulationService.run_simulation`(シナリオ実行オーケストレーション) | 10-1             | `_solve_once` / `_run_scenario` / `_run_one_scenario` / `run_simulation`(base + scenarios)                                                                      |
| [Phase-10-3](./Phase-10-3.md) | 二分探索による閾値発見(「答えを二分探索する」)                             | 10-2             | `algorithms/optimization/threshold_search.py::find_threshold`(新規プリミティブ)/ `_set_path` / `_run_sensitivity` / `SensitivitySpec`・`SensitivityResult`               |
| [Phase-10-4](./Phase-10-4.md) | ジョブキュー配線 + Phase 9 改訂                                | 10-3             | `schemas/job.py`(改訂)/ `services/job.py::enqueue_simulation` / `worker.py::simulate_job` / `api/routes/simulate.py`(新規)                                          |
| [Phase-10-5](./Phase-10-5.md) | 分析トラック拡張                                             | 10-4             | `analysis/loaders.py::load_jobs`(新規、export.py に `jobs` テーブル追加)/ `analysis/simulation_analysis.py`                                                               |
| [Phase-10-6](./Phase-10-6.md) | decitima-ui: Simulation ページ                          | 10-4             | `simulation/{api,stores,hooks,components}` / 既存 `useJobPolling`(Phase 9-9)を再利用                                                                                  |

10-1〜10-5 が decitima-api、10-6 が decitima-ui。順序の理由: **汎用マージ機構(ドメイン知識ゼロ)→ オーケストレーション本体 → アルゴリズム拡張(感度分析)→ 横断インフラ配線 → 分析 →UI**。各章は「その章までのファイルで import 解決」(進行のルール #15)。

---

## 4. この Phase の進め方 ── 実装 = 写経(Phase 1〜9 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-10-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 10 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests,analysis}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §8 の一覧(冒頭系譜コメントに `Phase 10` を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新される既存ファイル(`schemas/job.py`・
   `services/job.py`・`worker.py`・`api/routes/__init__.py`・`analysis/{loaders,export}.py`・
   `ui/src/lib/api/types.ts`・`ui/src/lib/menu-tree.ts`・`ui/src/features/optimization/
   logistics-planner/components/LogisticsPlannerPanel.tsx`)は変更行が `# (Phase 10-<M>)`
   タグ + 旧コードのコメントアウトで示される(進行のルール #12。grep 合言葉:
   `grep -rn "# (Phase 10" textbook/samples`)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §7 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 5. テストの階層

| レベル                      | 使うもの                                   | Phase 10 で書くもの                                                             |
| ------------------------ | -------------------------------------- | -------------------------------------------------------------------------- |
| primitives(純粋・主戦場)       | 素の pytest。DB 不要                        | `apply_overrides`(10-1)/ `find_threshold`(10-3)                            |
| services(純粋・DB/Redis 不要) | 素の pytest                              | `run_simulation`(10-2/10-3。base+scenarios+sensitivity)                     |
| ジョブキュー配線                 | 既存 9-8 と同じフェイクパターン                     | `JobService.enqueue_simulation`(10-4、FakeRedis + フェイク arq プール)             |
| integration              | 実 Postgres + 実 Redis(`-m integration`) | `simulate_job` の e2e(10-4)                                                 |
| analysis(純粋・dev 依存)      | 素の pytest。tmp_path に fake jobs JSONL   | `load_simulation_jobs` / `scenario_comparison` / `sensitivity_curve`(10-5) |
| UI                       | Vitest(node env)                       | `simulation-store` / `simulate` API クライアント(10-6)                           |

**スタブ**: `apply_overrides` / `run_simulation` / `find_threshold` は純粋(DB も Redis も
持たない)。スタブ不要 ── Phase 3 `BenchmarkService` と同じ理由(進行のルール #14)。
**唯一の例外は 10-4**(ジョブキュー配線)── Phase 9-8 と同じく `JobService.enqueue_simulation`
のユニットテストは arq の enqueue をフェイクに差し替える。

```bash
# decitima-api/backend(overlay end 状態 = Phase 9 end + Phase 10 samples)で
uv run pytest
# decitima-ui で
npx vitest run src/features/optimization/simulation
```

---

## 6. Phase 10 のスコープと非スコープ

| Phase 10 でやる                                                                      | 送る先                                                                                                                          |
| --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 汎用 override マージ(`apply_overrides`)/ `SimulationService` / `POST /api/v1/simulate` | ―                                                                                                                            |
| 二分探索による閾値発見(単一の数値フィールドを対象)                                                        | ―                                                                                                                            |
| 分析トラック拡張 / Simulation ページ(シナリオ JSON エディタ + 比較表)                                   | ―                                                                                                                            |
| ―                                                                                 | **ドメイン別のシナリオビルダー UI**(車両数スライダー等)── 汎用 dict override の設計方針(README「スキーマ自体は不変」)に沿い、JSON テキストエディタで統一する。専用フォームは需要が出た Phase で個別に追加 |
| ―                                                                                 | **`simulation_runs` のような専用永続化テーブル** ── Phase 9-8 の `jobs` テーブル(JSONB payload)で足りる(進行のルール #17。実消費者無しの新テーブルは見送り)               |
| ―                                                                                 | **感度分析の多変数化**(2 変数以上を同時に振る tornado chart 全体)── 単一フィールドの二分探索が最初の一歩。複数変数の感度分析は需要が出た Phase で `threshold_search.py` を拡張          |
| ―                                                                                 | **tornado chart の描画コンポーネント**(グラフ描画)── 10-6 は比較表 + テキスト要約まで。グラフ化は `analysis/plots.py` パターンの UI 移植として需要が出た Phase で追加           |

---

## 7. Phase 10 実装前チェックリスト

進行のルール #11。行 `10-M` ↔ 章 `Phase-10-M`。

| #    | 作る / 変えるファイル                                                                                                                                                                                                                                         | 主なクラス・関数の責務(1 行)                                                                                                                                                    |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 10-1 | `app/schemas/simulation.py`(新規)、`app/services/simulation.py`(新規、この章の分だけ)、`tests/unit/test_simulation_overrides.py`(新規)                                                                                                                               | `ScenarioOverride`/`SimulationRequest`/`ScenarioResult`/`SimulationResult`(スキーマ)/ `apply_overrides`(dict マージ→再検証)/ `_deep_merge`(RFC 7386 JSON Merge Patch)         |
| 10-2 | `app/services/simulation.py`(この章の分を追記)、`tests/unit/test_simulation_service.py`(新規)                                                                                                                                                                   | `_solve_once`(Validation→select→solve→verify を1回)/ `_run_scenario`(timeout 監視)/ `_run_one_scenario`(1件破綻を invalid_scenario として拾う)/ `run_simulation`(base+scenarios) |
| 10-3 | `app/algorithms/optimization/threshold_search.py`(新規)、`app/schemas/simulation.py`(`SensitivitySpec`/`SensitivityResult` 追記)、`app/services/simulation.py`(`_set_path`・`_run_sensitivity`・sensitivity 配線を追記)、`tests/unit/test_threshold_search.py`(新規) | `find_threshold`(二分探索で条件を満たす最小のパラメータ)/ `_set_path`(ドット区切りパスから override dict を作る)/ `_run_sensitivity`                                                                |
| 10-4 | `app/schemas/job.py`(改訂)、`app/services/job.py`(`enqueue_simulation` 追加)、`app/worker.py`(`simulate_job` 追加)、`app/api/routes/simulate.py`(新規)、`app/api/routes/__init__.py`・`app/core/config.py`(現行版)                                                   | `JobResult`(union の広げ)/ `JobService.enqueue_simulation`/ `simulate_job(ctx, job_id)`/ `POST /api/v1/simulate`                                                       |
| 10-5 | `analysis/loaders.py`(`load_jobs` 追加)、`analysis/export.py`(`jobs` テーブル追加)、`analysis/simulation_analysis.py`(新規)、`tests/analysis/test_simulation_analysis.py`(新規)                                                                                     | `load_jobs`(汎用)/ `load_simulation_jobs`・`scenario_comparison`・`sensitivity_curve`(simulate 専用の整形)                                                                   |
| 10-6 | `ui: simulation/{api,stores,hooks,components}`(新規)、`app/(pages)/optimization/simulation/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)、`logistics-planner/components/LogisticsPlannerPanel.tsx`(現行版、型ガード追加)                                    | `submitSimulation` / `useSimulationStore` / `useSimulation`(`useJobPolling` 再利用)/ `SimulationPanel` / `ScenarioComparisonTable` / `ScenariosJsonEditor`             |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)(Phase 10 end 状態)。各ファイル
冒頭の `# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は §7 の実装前チェックリスト参照。overlay 検証手順は [`textbook/samples/README.md`](../samples/README.md)。

要点:

- `apply_overrides` は Pydantic の判別可能ユニオン検証にただ乗りするだけで、6 ドメインのどれに対しても動く ── ドメイン別の override コードを 1 行も書かない(README「スキーマ自体は不変」への最も忠実な実装)。
- `SimulationService` は Phase 3 `BenchmarkService` と対称(Benchmark = 同じ問題×違うアルゴリズム、Simulation = 同じアルゴリズム×違う問題)だが、**永続化を持たない**(session/redis 依存が無い、Phase 10 で初めての「素の async 関数」サービス)。
- `find_threshold` は Phase 1 `binary_search`(値の探索)とは別の応用(「答えを二分探索する」、競技プログラミングの binary search on the answer)。単調性の前提が崩れた場合の挙動もテストで明示する。
- ジョブキューは Phase 9-8 の `jobs` テーブルをそのまま再利用 ── **DB マイグレーションなし**。
  `JobStatusResponse.result` の型を広げるだけで、`solve_job` の書き込み方も既存テストも無改造。
- UI は Phase 4-8 / 5-5 / 6-8 / 7-7 / 8-7 / 9-9 と違い、単一の problem_type を持つ画面ではない
  (base problem はどのドメインでもよい)── シナリオ入力を JSON テキストエディタに統一することで、ドメイン別の専用フォームを増やさずに済ませている。

検証: Phase 9 end 状態に Phase 10 samples を overlay し `uv run pytest` / `ruff` /
`uvx pyright`(Phase 10 分 0 errors)。`alembic upgrade head` は no-op(新テーブルなし)。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run` / `npx eslint`。

---

## 9. Phase 10 の成果物

- **textbook**: この `Phase-10/` 一式(導入 + `Phase-10-1`〜`10-6` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/schemas/simulation.py`・
  `app/services/simulation.py`・`app/algorithms/optimization/threshold_search.py`・
  `app/api/routes/simulate.py`(新規)/ `app/schemas/job.py`・`app/services/job.py`・
  `app/worker.py`・`app/api/routes/__init__.py`・`app/core/config.py`(現行版)/
  `analysis/loaders.py`・`analysis/export.py`・`analysis/simulation_analysis.py`(新規)/ `tests/**`
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/simulation/**` /
  `src/app/(pages)/optimization/simulation/page.tsx` /
  `src/lib/api/types.ts`・`src/lib/menu-tree.ts`・
  `src/features/optimization/logistics-planner/components/LogisticsPlannerPanel.tsx`(現行版)
- **既存 Phase 教材への「後続 Phase での改訂」1 行**(`Phase-9-introduction.md` に
  `JobStatusResponse.result` の型を広げた旨)
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 10 要点**(経緯は `textbook/q_a.md` Q53)
- **`textbook/samples/README.md` の「最終検証」スタンプ**を Phase 10 に更新

---

## 10. 次のフェーズ

Phase 10 完了で、Phase 4〜9 の6ドメインが**意思決定支援層**として横断的に比較可能になる ──
「最適解は何か」から「どの条件なら、どの選択をするべきか」への一歩。新しいドメインスキーマは
増えず、既存の型システム(判別可能ユニオン + Pydantic 再検証)と横断インフラ(ジョブキュー)を
そのまま「複数回まわす」ことで実現した。

その先は README §20 の拡張順 ── **LLM(Phase 11〜13、Natural Language → Structured Problem /
Algorithm Recommendation / Result Explanation)→ LLM vs Algorithm Benchmark(Phase 14)→
Production(Phase 15)**。Phase 10 で作った `apply_overrides` / `SimulationResult` は、
Phase 13「Result Explanation」が「シナリオ比較の説明文生成」に応用できる土台になる。
