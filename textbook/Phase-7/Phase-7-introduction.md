# Phase 7 — Travel Planner(実装フェーズ)導入

作業章(`Phase-7-1.md` 以降)を始める前に、この 1 本で Phase 7 の全体像を掴む。
目的 / パイプライン上の位置 / アルゴリズムの 2 層 / 進め方 / テスト / スコープ / 章一覧 /
実装前チェックリスト / 次のフェーズ。

> **Phase 7 は MVP(Phase 0〜6)完了後、最初の拡張フェーズ**。README §19 の設計のポイント ──
> 「Dynamic Programming を実問題へ適用する。Knapsack DP で訪問地の部分集合を選び、
> Floyd-Warshall で前処理した全点対距離を使って巡回順を決める」。

---

## 1. このフェーズの目的

README §12.3 Travel Planner ── 予算・時間・訪問候補地・好みから、**効用(訪れる価値)の重み付き合計が最大**になる旅行プランを組む。「どの場所を選ぶか」= **0/1 ナップサック**、「選んだ場所をどの順で回るか」= 小さな **TSP**。問題タイプは **Constrained Optimization**。**Phase 7 の新規はアルゴリズムと 1 つの problem_type だけ**:

> **TSP：Traveling Salesman Problem（巡回セールスマン問題）**
> 複数の地点をすべて1回ずつ訪問して、出発地点に戻ってくるルートのうち、最も短いものを求める問題

| すでに完成しているもの                                                               | いつ                                                 |
| ------------------------------------------------------------------------- | -------------------------------------------------- |
| 判別可能ユニオンの仕組み(problem_type ごとに `data` / `assignments` を切り替え)               | Phase 1 / Phase 5-3 で network を追加した手順が雛形           |
| Semantic Validation / 構造検証のレジストリ(`SEMANTIC_CHECKS` / `structural_verify`) | Phase 2 / Phase 5-3                                |
| `POST /solve` `/verify` `/benchmark`(problem_type で汎用ディスパッチ)              | Phase 1〜3                                          |
| `forbidden` / `required_inclusion` / `numeric_bound` チェッカー(kind ベース)      | Phase 2                                            |
| `optimize_waypoint_order`(必須経由地の訪問順。`SegmentCost` コールバックの seam)           | Phase 4-1(`_MAX_EXACT` 超えは「与えられた順」= Phase 7 送りの宿題) |
| `analysis/` の器(benchmark をオフライン集計)                                        | Phase 3-8                                          |

Phase 7 で新しく入るもの:

| 新規                                                               | 中身                                                                                                                                       |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **`travel_planning` problem_type**                               | `TravelData`(places / legs / budget / time_budget / start / preferences)/ `TravelSolution`。判別可能ユニオンに 1 メンバー(Phase 5-3 と同型)               |
| **Floyd-Warshall プリミティブ** `graph/floyd_warshall.py`              | 全点対最短距離。手実装の三重ループ(numpy なし)。「選んだ訪問地を回る順」を決める前処理                                                                                          |
| **Knapsack DP** `optimization/knapsack.py`                       | `knapsack_2d`(予算 × 時間の 2 次元 0/1 ナップサック、ボトムアップ、擬多項式)+ `KnapsackDpTravelStrategy`                                                          |
| **手実装トラック** `optimization/{greedy_travel,brute_force_travel}.py` | Greedy(効用/コスト比、移動込みで逐次)/ BruteForce(部分集合の全列挙オラクル ── Phase 3/6 と同じ役割)                                                                     |
| **共通足回り** `optimization/travel_common.py`                        | `parse_travel_problem` / `place_utility` / `order_and_cost`(Floyd-Warshall + `optimize_waypoint_order`)/ `tour_cost` / `travel_solution` |
| **m > 8 の訪問順近似** `graph/waypoints.py`(改訂)                        | Phase 4 の宿題を回収 ── 最近傍法 + 2-opt。`optimize_waypoint_order` のシグネチャは不変                                                                       |
| **分析** `analysis/travel_analysis.py`                             | DP(移動無視の上界)と Greedy(移動込み)の解の差 / 規模別で DP が invalid になる割合                                                                                  |
| **Travel Planner ページ**(decitima-ui)                              | `src/features/optimization/travel-planner/`。プラン + 巡回順を `GraphCanvas` で。Phase 4-8 / 5-5 / 6-8 と同型                                         |

---

## 2. パイプライン上の位置 ── 既存に触れず「解き方」だけ足す

`Phase-0-7.md` のとおり、travel も **`POST /api/v1/solve` に `problem_type` 付きの
`OptimizationProblem` を渡すだけ**。

```text
POST /api/v1/solve   { problem_type: "travel_planning", data: { places, legs, budget, time_budget }, objectives: [...] }
      ▼
SolveService.solve()
      ├ (b) ProblemValidationService.validate   ← SEMANTIC_CHECKS["travel_planning"](7-3 で追加)
      │        ※ route / network と違い「計算」のゲートは無い ── 訪問順は strategy の仕事
      ├ (c) select_strategy(problem)             ← rule-based: travel → knapsack_dp(7-5 で足す 1 行)
      ├ (d) KnapsackDpTravelStrategy.solve        ← 新 registry キー "travel_planning"
      │        place を DP で選ぶ → Floyd-Warshall + optimize_waypoint_order で巡回順・総コスト
      ├ (e) SolutionVerificationService.verify   ← verify_travel_structure(7-3)+ tour_cost の検算(7-4)
      └ (f) 永続化 ── **新テーブルなし**(hybrid JSONB。`alembic upgrade head` は no-op)
```

**friction は最小**(すべて増分): 葉モジュール 2 本の新設 / ユニオンに 1 メンバー /
`semantic` に 3 チェック / `structure` に 1 arm / `verification` に travel の検算 1 本(7-4)/
`constraints/elements.py`(新規・共有ヘルパ)に travel arm 1 つ + `forbidden` /
`required_inclusion` はそれを呼ぶだけに(私設ヘルパの重複を解消。7-3。#17)/
`adjacency.py` に `build_leg_adjacency` / `waypoints.py` の m > 8 分岐 / `registry` の 1 キー /
`select_strategy` の 1 分岐。route / network / shift のロジックには一切触れない。

---

## 3. アルゴリズムの 2 層(`Phase-0-4.md` §2.4)

|         | AlgorithmStrategy(registry に載る)                                                  | アルゴリズム・プリミティブ(載らない)                                                            |
| ------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Phase 7 | `KnapsackDpTravelStrategy` / `GreedyTravelStrategy` / `BruteForceTravelStrategy` | `floyd_warshall` / `build_leg_adjacency` / `optimize_waypoint_order`(m > 8 近似) |

`AlgorithmMeta.family` は **`"optimization"`** を再利用(network_design が `"graph"` を再利用したのと
同じ。Literal の変更なし)。3 strategy とも `implementation="handwritten"`。

**Floyd-Warshall は Strategy ではない** ── 「問題まるごとを解く」のでなく「訪問順を決める前処理」。
Phase 5 の Union-Find / `connectivity.py` と同じ「プリミティブ」層(registry 非搭載の素の純粋関数)。

**`_ops` の単位**: Knapsack DP = DP セルの更新回数、Greedy = place を追加候補として評価した回数、
BruteForce = 評価した部分集合の数。**単位が違うので割り算しない**(`CLAUDE.md` 命名規約)。

**教材の核**: Knapsack DP は **place の cost / duration だけ**で詰める ──「移動費用を無視した
上界」。実際に巡回して起点に戻る移動分を足すと予算・時間を超えることがあり、Verification が
hard 違反で `invalid` にする。Greedy は 1 つ選ぶたびに実際の巡回コストで判定するので必ず予算内。
この差を 7-6 の `analysis/travel_analysis.py` で並べる(README「プラン比較」)。

---

## 4. 章一覧(章 = 作業単位)

`Phase-7-M.md` = 作業単位 7-M。

| 章                           | トピック                                                                                    | 依存        | 主な内容                                                                                                                                                                        |
| --------------------------- | --------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-7-1](./Phase-7-1.md) | Floyd-Warshall プリミティブ + DP 理論                                                           | Phase 4   | `graph/floyd_warshall.py`(新規、`Adjacency` 型だけに依存 ── 自己完結)/ DP のボトムアップ・メモ化・擬多項式(理論)                                                                                           |
| [Phase-7-2](./Phase-7-2.md) | Knapsack DP ── `knapsack_2d`(2 次元 0/1)                                                  | 7-1       | `optimization/knapsack.py`(新規 ── `type Item` + `knapsack_2d` のみ、純粋・自己完結)/ グリッド解像度の落とし穴                                                                                    |
| [Phase-7-3](./Phase-7-3.md) | `travel_planning` の配線(schema union + semantic + structure + constraints)              | 7-2       | 葉 2 本 / ユニオン / `semantic.py` 3 チェック / `structure.py` 1 arm(純粋述語)/ `constraints/elements.py`(新規・共有)+ チェッカー 2 本の重複解消 + travel arm。写経順序リスト付き。`verification` の巡回コスト検算は 7-4(`travel_common` 依存) |
| [Phase-7-4](./Phase-7-4.md) | 訪問順 + `travel_common` + DP strategy(Floyd-Warshall 注入 / m > 8 近似)                       | 7-3       | `travel_common.py`(新規・全関数)/ `adjacency.py` に `build_leg_adjacency` / `waypoints.py` 改訂(最近傍 + 2-opt)/ `KnapsackDpTravelStrategy` を `knapsack.py` に追加 / `verification._verify_travel_plan`(7-3 から移設) |
| [Phase-7-5](./Phase-7-5.md) | Greedy + BruteForce オラクル + registry + select + end-to-end                               | 7-4       | `optimization/{greedy_travel,brute_force_travel}.py` / `registry.py`(3 strategy)/ `algorithm_selection.py` / 「DP == BruteForce(小規模)」プロパティテスト                                |
| [Phase-7-6](./Phase-7-6.md) | analysis ── `travel_analysis.py` + notebook(プラン比較)                                      | 7-5       | `analysis/travel_analysis.py`(`load_travel_benchmark_runs` / `by_size` / `dp_vs_greedy` / `invalid_rate_by_size`)/ `sample_travel_runs.jsonl` / `travel_explore.ipynb`      |
| [Phase-7-7](./Phase-7-7.md) | Travel Planner ページ(decitima-ui)                                                         | Phase 4-8 | `travel-planner/{api,stores,hooks,components,sample-problems.ts}` / `TravelPlanCanvas` / `types.ts`・`menu-tree.ts` に travel アーム                                             |

7-1〜7-6 が decitima-api、7-7 が decitima-ui。順序の理由: **プリミティブ(Floyd-Warshall /
knapsack_2d、純粋・自己完結)→ ドメイン配線(problem_type の葉)→ アルゴリズム糊(travel_common +
DP strategy + 巡回コスト検算)→ オラクル + registry → 分析 → UI**。各章は「その章までのファイルで
import 解決」(進行のルール #15。Q41 / Q42 で 7-2〜7-4 の前方参照を是正)。

registry の作法(進行のルール #15): `registry.py` の `"travel_planning"` キーは 7-5 で 3 strategy をまとめて有効化する。end-to-end パイプライン(validate→select→solve→verify)が緑になるのは 7-5。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜6 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-7-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 7 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests,analysis}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §9 の一覧(冒頭系譜コメントに `Phase 7` を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新されるファイルは変更行が
   `# (Phase 7-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12。
   grep 合言葉: `grep -rn "# (Phase 7" textbook/samples`)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §9 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル                  | 使うもの                               | Phase 7 で書くもの                                                                                                |
| -------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| primitives(純粋・主戦場)   | 素の pytest。DB 不要                    | `floyd_warshall` / `build_leg_adjacency` / `knapsack_2d` / `optimize_waypoint_order` の m > 8 近似              |
| domain(純粋)           | 素の pytest                          | `TravelData` / `TravelSolution` の判別可能ユニオン / `SEMANTIC_CHECKS["travel_planning"]` / `verify_travel_structure` |
| algorithms(strategy) | 素の pytest                          | DP / Greedy / BruteForce の `solve`。BruteForce を正解オラクルに小規模で裏取り(7-5)                                           |
| 3 strategy の比較       | 素の pytest(`for seed`)              | `test_travel_strategies.py`(DP は移動無視の上界 / Greedy は valid / BruteForce ≥ 両者)                                  |
| サービス層                | 直接呼ぶ(`test_mst_strategies.py` と同型) | validate→select→solve→verify のパイプライン                                                                         |
| 分析トラック               | 素の pytest(pandas)                  | `analysis/travel_analysis.py`                                                                                |
| UI                   | Vitest(node env)                   | travel-planner store                                                                                         |

**スタブ**: strategy / validation / verification はすべて純粋(DB を持たない)。スタブ不要。

```bash
# decitima-api/backend(overlay end 状態 = Phase 6 end + Phase 7 samples)で
uv run pytest      # 343 passed, 4 deselected
# decitima-ui で
npx vitest run src/features/optimization   # travel-planner store 4 本を含む
```

---

## 7. Phase 7 のスコープと非スコープ

| Phase 7 でやる                                                                              | 送る先                                                                                                                 |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `travel_planning` problem_type / Floyd-Warshall / Knapsack DP(2 次元)/ Greedy / BruteForce | ―                                                                                                                   |
| 訪問順の最適化(m ≤ 8 全順列、m > 8 最近傍 + 2-opt)── Phase 4 の宿題(Q27)                                  | ―                                                                                                                   |
| `analysis/travel_analysis.py`(DP vs Greedy / invalid 率)                                  | ―                                                                                                                   |
| Travel Planner ページ(サンプル選択 + JSON エディタ + プラン可視化)                                          | ―                                                                                                                   |
| ―                                                                                        | **産業ソルバートラック**(OR-Tools でルート最適化)── networkx / OR-Tools は既に依存にあるが、travel は手実装 DP が学習の主役。実規模の TSP は Phase 9 Logistics |
| ―                                                                                        | **preferences の学習 / LLM による好み抽出** ── Phase 11〜13(LLM)                                                               |
| ―                                                                                        | **時間帯・営業時間の制約**(place ごとの開閉時間)── 需要が出た Phase で `TravelData` に追加                                                     |
| ―                                                                                        | **入力アダプタ**(観光地一覧の CSV → `OptimizationProblem`)── `app/adapters/`、Phase 8/9 送り                                       |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)(Phase 7 end 状態)。各ファイル冒頭の
`# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は §9 の実装前チェックリスト参照。
overlay 検証手順は [`textbook/samples/README.md`](../samples/README.md)。

要点:

- `app/algorithms/optimization/travel_common.py` は route の `segments.py` / network の `mst.py` と
  同じ「共通足回り」── 3 strategy は「訪問地の選び方」だけが違う。
- `analysis/` は Phase 3-8 で作った器に **1 モジュール足すだけ**(移設・作り直しなし)。
- UI は Phase 4-8 / 5-5 / 6-8 の Route Planner / Network Designer / Shift Scheduler と同型の 4 スライス目。

検証: Phase 6 end 状態に Phase 7 samples を overlay し `uv run pytest`(**343 passed, 4 deselected**)/
`ruff` / `uvx pyright`(Phase 7 分 0 errors)/ `alembic upgrade head`(新テーブルなし)/ notebook 4 本実行。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(travel store 4 本)/ `npx eslint`。

---

## 9. Phase 7 実装前チェックリスト

進行のルール #11。行 `7-M` ↔ 章 `Phase-7-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7-1 | `app/algorithms/graph/floyd_warshall.py`(新規)、`tests/unit/test_floyd_warshall.py`(新規)。既存ファイルへの変更なし ── 自己完結                                                                                                                                                                                                                                                                                                                                                                                                     | `floyd_warshall(adjacency) -> AllPairs`(全点対最短、三重ループ、`math.inf` 初期化、平行辺は軽い方。`adjacency.py` の `Adjacency` 型だけに依存)                                                                                                                                                        |
| 7-2 | `app/algorithms/optimization/knapsack.py`(新規 ── `type Item` + `knapsack_2d` のみ)、`tests/unit/test_knapsack.py`(新規 ── 純粋 4 ケース)。既存ファイルへの変更なし ── 自己完結                                                                                                                                                                                                                                                                                                                | `knapsack_2d(items, cap_a, cap_b) -> list[int]`(2 次元 0/1、ボトムアップ、容量を降順、`take[][][]` で復元、擬多項式 O(n·A·B))                                                                                                               |
| 7-3 | `app/domain/problems/travel_planner.py`・`app/domain/solutions/travel_planner.py`・`app/domain/constraints/elements.py`(新規)、`app/domain/problems/{problem,__init__,semantic}.py`・`app/domain/solutions/{solution,__init__,structure}.py`・`app/domain/constraints/{forbidden,required_inclusion}.py`(現行版)、`tests/fixtures/optimization.py`(現行版 ── `build_travel_problem` / `build_scaled_travel_problem` / `build_travel_solution`)、`tests/unit/test_travel_planning.py`、`tests/unit/test_constraint_checkers.py`(現行版)。**`verification.py` は 7-4** | `Place` / `TravelLeg` / `TravelData`(`model_validator` で leg 端点 / start / preferences キーの実在)/ `TravelSolution` / `SEMANTIC_CHECKS["travel_planning"]` 3 本 / `verify_travel_structure`(純粋述語 ── `total_cost` フィールドの範囲は見る、巡回積み直しはしない)/ `solution_element_ids(solution, *, aspect)`(forbidden / required_inclusion が共有する解 → 要素 id 集合。route のみ nodes/edges を分岐)+ チェッカー 2 本を呼び出しだけに |
| 7-4 | `app/algorithms/optimization/travel_common.py`(新規・全関数)、`tests/unit/test_travel_common.py`(新規)、`app/algorithms/graph/adjacency.py`(`build_leg_adjacency` 追加、`# (Phase 7-4)`)、`app/algorithms/graph/waypoints.py`(現行版 ── m > 8 分岐)、`app/algorithms/optimization/knapsack.py`(`KnapsackDpTravelStrategy` 追加、`# (Phase 7-4)`)、`app/services/verification.py`(`_verify_travel_plan` 追加、`# (Phase 7-4)`)、`tests/unit/test_route_strategies.py`(現行版)                                                 | `travel_common`: `parse_travel_problem` / `place_utility` / `travel_solution`(`order_and_cost` が `None` → `status="infeasible"`)/ `all_pairs`(FW×2)/ `order_and_cost`(anchor 閉路)/ `tour_cost`(申告順の検算)。`build_leg_adjacency(data, forbidden_leg_ids) -> Adjacency`。`_approx_best`(最近傍 + 2-opt。`None` セマンティクスは `_exact_best` と同じ)。`KnapsackDpTravelStrategy`(place cost/duration を整数グリッド → DP)。`_verify_travel_plan`(`tour_cost` で総費用を検算、hard)                  |
| 7-5 | `app/algorithms/optimization/{greedy_travel,brute_force_travel}.py`(新規)、`tests/unit/test_travel_strategies.py`(新規 ── Greedy/BruteForce/registry/select/e2e)、`app/algorithms/registry.py`・`app/services/algorithm_selection.py`(現行版)、`tests/unit/test_algorithm_selection.py`(現行版)                                                                                                                                                                                                                                                                                             | `GreedyTravelStrategy`(効用/(追加でかかる資源)比で逐次、移動込み判定)/ `BruteForceTravelStrategy`(部分集合の全列挙オラクル)/ `registry["travel_planning"]` 3 strategy / `_preferred_name` の travel → `"knapsack_dp"`                                                                                    |
| 7-6 | `analysis/travel_analysis.py`(新規)、`analysis/data/sample_travel_runs.jsonl`、`analysis/data/.gitignore`(現行版)、`analysis/notebooks/travel_explore.ipynb`、`tests/analysis/test_travel_analysis.py`                                                                                                                                                                                                                                                                                                                 | `load_travel_benchmark_runs`(size = place 数)/ `by_size` / `dp_vs_greedy`(gap)/ `invalid_rate_by_size`(DP が移動無視で崩れる割合)                                                                                                                                                  |
| 7-7 | `ui: travel-planner/{api,stores,hooks,components,sample-problems.ts}`(新規)、`app/(pages)/optimization/travel-planner/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)                                                                                                                                                                                                                                                                                                                                       | `solveTravel` / `compareTravel` / `useTravelPlannerStore` / `TravelPlannerPanel` / `TravelPlanCanvas`(選んだ地を強調、巡回順を実線、候補 leg を破線、invalid は赤)/ `types.ts` に travel アーム / ページは SSG + `RequireAuth`                                                                        |

---

## 10. Phase 7 の成果物

- **textbook**: この `Phase-7/` 一式(導入 + `Phase-7-1`〜`7-7` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/algorithms/graph/floyd_warshall.py`(新規)/
  `app/algorithms/optimization/{knapsack,travel_common,greedy_travel,brute_force_travel}.py`(新規)/
  `app/domain/problems/travel_planner.py`・`app/domain/solutions/travel_planner.py`(新規)/
  `app/algorithms/graph/{adjacency,waypoints}.py`・`app/domain/**`・`app/services/{verification,algorithm_selection}.py`・
  `app/algorithms/registry.py`(現行版)/ `analysis/travel_analysis.py` / `tests/**`
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/travel-planner/**` /
  `src/app/(pages)/optimization/travel-planner/page.tsx` / `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)
- **Phase 1 / 4 教材への「後続 Phase での改訂」1 行**(`Phase-1-1.md` の判別ユニオンに travel_planning、
  `Phase-4-4.md` / `Phase-4-introduction.md` の「近似は Phase 7」に「Phase 7-4 で実装 ✅」)
- **`Phase-0-2.md` §8.1 の introduction 改訂節**に travel_planning 追加を 1 行
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 7 要点**(経緯は `textbook/q_a.md` Q40。
  章順写経で崩れる前方参照の是正は Q41 / Q42、`elements.py` 共通化は Q43)

---

## 11. 次のフェーズ

Phase 7 完了で **4 つ目の problem_type `travel_planning`** が端から端まで通る。DP という新しい
アルゴリズムパラダイム(部分問題の最適解を積み上げる)を実問題に適用し、Floyd-Warshall で
前処理した全点対距離を使って「選択 → 巡回順」の 2 段構えを実装した。

その先は README §20 の拡張順 ── **Project Manager(Phase 8、Critical Path / トポロジカルソート)→
Logistics(Phase 9、実規模 TSP・OR-Tools)→ Simulation(Phase 10)→ LLM(Phase 11〜13)→
LLM vs Algorithm Benchmark(Phase 14)**。`analysis/` は Phase 14 の実験フレームワークまで育つ。
