# Phase 9 — Logistics Optimizer(実装フェーズ)導入

作業章(`Phase-9-1.md` 以降)を始める前に、この 1 本で Phase 9 の全体像を掴む。
目的 / パイプライン上の位置 / アルゴリズムの 2 層 × 2 トラック / 進め方 / テスト / スコープ /
章一覧 / 実装前チェックリスト / 次のフェーズ。

> **Phase 9 は MVP(Phase 0〜6)完了後の 3 つ目の拡張フェーズ**。README §12.5 / §19 の設計のポイント ──「複数アルゴリズムを組み合わせた総合最適化。Vehicle / Delivery モデル、Capacity Constraint、Route ptimization(Dijkstra/A*)+ Packing Optimization(DP) + Delivery Order Optimization(Greedy/TSP)+ 複合的な Constraint Verification」。
> README の記述は他 Phase より薄く、`problem_type` 名やスキーマは未確定だった(Phase 8 開始時の相談ログ Q45 と同型の状況)。開始にあたりユーザーに 3 点を確認し、以下の方針で進める
> (詳細は `textbook/q_a.md` Q48):
> 
> | 論点              | 決定                                                  |
> | --------------- | --------------------------------------------------- |
> | 車両モデルのスコープ      | **複数車両(CVRP: Capacitated Vehicle Routing Problem)** |
> | 産業ソルバートラック      | **PuLP(MILP)**。scipy は不採用                           |
> | ジョブキュー(非同期実行基盤) | **導入する**(README「ここが候補地点」を実行に移す)                     |

---

## 1. このフェーズの目的

README §12.5 Logistics Optimizer ── 1 つのデポ(depot)から複数の車両が出発し、複数の配送先(delivery stop)を分担して回ってデポに戻る。各車両には容量(重量・体積)があり、各配送先には需要(重量・体積)がある。**Phase 4〜8 で個別に習得したアルゴリズムを 1 つの問題で組み合わせる**
── 経路探索(Dijkstra/A* → 全点対最短路の前処理は Floyd-Warshall)+ 積載判定(Knapsack DP)+配送順序(TSP 近似)+ 制約充足の探索(Branch and Bound)。問題タイプは **Graph + Optimizationの複合**。

> **CVRP(Capacitated Vehicle Routing Problem)** ── 複数車両で複数拠点を分担して回る配送計画問題に、車両ごとの積載容量の上限を加えたもの。「配送先→車両の割当」(ビンパッキング)と「車両ごとの巡回順」(TSP)の 2 段構造を持つ NP 困難な組合せ最適化問題。

| すでに完成しているもの                                                               | いつ                                                    |
| ------------------------------------------------------------------------- | ----------------------------------------------------- |
| 判別可能ユニオンの仕組み(problem_type ごとに `data` / `assignments` を切り替え)               | Phase 1 / Phase 5-3・7-3・8-3 で新 problem_type を足した手順が雛形 |
| Semantic Validation / 構造検証のレジストリ(`SEMANTIC_CHECKS` / `structural_verify`) | Phase 2 / Phase 5-3・7-3・8-3                           |
| Floyd-Warshall(全点対最短路)`graph/floyd_warshall.py`                           | Phase 7-1                                             |
| Knapsack DP(2 次元容量)`optimization/knapsack.py::knapsack_2d`                | Phase 7-2                                             |
| 訪問順最適化(TSP 厳密 + 近似)`graph/waypoints.py::optimize_waypoint_order`          | Phase 4-1・7-4                                         |
| Branch and Bound のノード予算パターン(`_MAX_NODES` + `_truncated`)                  | Phase 6-5                                             |
| 産業ソルバートラックを `[project].dependencies` に追加する手順                              | Phase 6-7(OR-Tools)/ 本 Phase(PuLP)                    |

Phase 9 で新しく入るもの:

| 新規                                              | 中身                                                                                                                                                           |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`logistics_planning` problem_type**           | `LogisticsData`(nodes / segments / depot / vehicles / deliveries)/ `LogisticsSolution`(車両ごとの訪問順 `VehicleRoute` の集まり)。判別可能ユニオンに 1 メンバー(Phase 5-3・7-3・8-3 と同型) |
| **`logistics_common.py` 共通足回り**                 | `travel_common.py` / `project_common.py` と同型。デポ↔配送先の全点対距離(Floyd-Warshall の再利用)/ 容量判定 / 1 台分の巡回順+距離(TSP の再利用)                                                 |
| **手実装 strategy 4 本**                            | `knapsack_dp`(容量だけで詰める上界)/ `greedy`(挿入コストを都度計算)/ `branch_and_bound`(確定距離を下界に分枝限定)/ `brute_force`(全割当×全順列の正解オラクル)                                             |
| **産業ソルバートラック** `optimization/pulp_logistics.py` | `PulpMilpLogisticsStrategy`(PuLP + CBC。使用台数最小化のビンパッキング MILP。経路順序は既存の TSP 近似に委譲)                                                                              |
| **ジョブキュー基盤**(problem_type 非依存)                  | `arq` + Redis。`POST /api/v1/jobs` / `GET /api/v1/jobs/{id}`。既存の同期 `POST /api/v1/solve` は無変更で併存                                                               |
| **Logistics Optimizer ページ**(decitima-ui)        | `src/features/optimization/logistics-planner/`。車両ルートを `GraphCanvas` で色分け表示、ジョブポーリング UI                                                                       |

---

## 2. パイプライン上の位置 ── 既存に触れず「解き方」だけ足す

`Phase-0-7.md` のとおり、logistics も **`POST /api/v1/solve` に `problem_type` 付きの
`OptimizationProblem` を渡すだけ**(重い MILP は 9-8 の `POST /api/v1/jobs` でも実行できる)。

```text
POST /api/v1/solve   { problem_type: "logistics_planning", data: { depot_id, nodes, segments, vehicles, deliveries }, objectives: [...] }
      ▼
SolveService.solve()
      ├ (b) ProblemValidationService.validate   ← SEMANTIC_CHECKS["logistics_planning"](9-1 で追加)
      │        + デポから全配送先への到達可能性(logistics_deliveries_reachable。route の到達可能性 /
      │          network の連結性 / project の非巡回性と同じ「計算ゲート」の 5 例目)
      ├ (c) select_strategy(problem)             ← 既定 "knapsack_dp"(9-7 で足す 1 分岐)
      ├ (d) KnapsackDpLogisticsStrategy.solve     ← 新 registry キー "logistics_planning"
      │        knapsack_2d(容量だけの上界)→ optimize_waypoint_order(車両ごとの TSP)→ logistics_solution
      ├ (e) SolutionVerificationService.verify    ← verify_logistics_structure(9-1)+ 容量・距離の検算(9-2)
      └ (f) 永続化 ── **新テーブルなし**(hybrid JSONB。`alembic upgrade head` は no-op)
```

**friction は最小**(すべて増分): 葉モジュール 2 本の新設 / ユニオンに 1 メンバー /
`semantic` に 3 チェック / `structure` に 1 arm / `validation` に到達可能性ゲート 1 本(9-1)/`verification` に容量・距離の検算 1 本(9-2)/ `registry` の 1 キー / `select_strategy` の 1 分岐
(9-7)。route / network / shift / travel / project のロジックには一切触れない。
`constraints/elements.py` も**変更不要** ── logistics 解は全配送先を実施するので
`forbidden` / `required_inclusion` は非該当(未知の解型 → `None` → チェッカー素通し。Phase 8 と同型)。

ジョブキューだけは例外的に **problem_type に依存しない横断インフラ**(9-8)。既存の同期経路は1 バイトも変えない。

---

## 3. アルゴリズムの 2 層 × 2 トラック(`Phase-0-4.md` §2.4)

|         | AlgorithmStrategy(registry に載る)                                                                                                                             | アルゴリズム・プリミティブ(載らない)                                                                                                         |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Phase 9 | `KnapsackDpLogisticsStrategy` / `GreedyLogisticsStrategy` / `BranchAndBoundLogisticsStrategy` / `BruteForceLogisticsStrategy` / `PulpMilpLogisticsStrategy` | `floyd_warshall`(7-1 再利用)/ `knapsack_2d`(7-2 再利用)/ `optimize_waypoint_order`(4-1・7-4 再利用)/ `logistics_deliveries_reachable` |

`AlgorithmMeta.family` は **`"optimization"`** を再利用(Literal の変更なし。travel が
`"optimization"` を再利用したのと同じ判断)。

| strategy           | implementation | 振る舞い                                                                                                                                 |
| ------------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `knapsack_dp`      | handwritten    | 車両を 1 台ずつ、`knapsack_2d` で残り配送先から容量に収まる部分集合を選ぶ(価値は均一 1.0 ── **台数を最大化する上界。実際の移動距離は見ない**)。選んだ後に TSP 近似で巡回順・実距離を決める                      |
| `greedy`           | handwritten    | 配送先を 1 件ずつ、実際に挿入したときの距離増分が最小になる車両へ足す。**容量オーバーの候補は最初から除外するので必ず valid**                                                                |
| `branch_and_bound` | handwritten    | 配送先→車両の割当を DFS + 分枝限定で探索。下界 = 「これまでに確定した距離」(単調非減少 ── 安全だが緩い)。ノード予算 `_MAX_NODES` で打ち切り `metrics["_truncated"]`                        |
| `brute_force`      | handwritten    | 配送先→車両の全割当 × 各車両内の全順列を尽くす(小規模専用の正解オラクル)                                                                                              |
| `pulp_milp`        | library:pulp   | 「配送先をちょうど 1 台に割り当て、容量を守りつつ**使用台数を最小化する**」ビンパッキング MILP を CBC で解く。経路順序そのものの MILP 化(劣周回除去制約を伴うフル CVRP)はスコープ外 ── 割当後の巡回順は既存の TSP 近似に委譲する |

**教材の核**: Phase 7 の「Knapsack DP は **place cost だけ**で詰める = 『移動費用を無視した上界』」、Phase 8 の「`cpm` は **依存だけ**を見て詰める = 『資源を無視した下界』」に続く 3 つ目の変奏 ──Phase 9 の `knapsack_dp` は「**容量だけ**を見て詰める = 『移動距離を無視した上界』」。台数当たりの搭載数は最大化できても、選んだ組合せが地理的に離れていれば移動距離で `greedy` / `branch_and_bound`
/ `brute_force` に劣ることがある(`quality_ratio` で検証。9-7 のプロパティテスト)。
容量そのものは厳密に守るので travel/project と違って `invalid` にはならない ── **「制約は守るが質で劣る」という Phase 7/8 とは違う種類の上界**であることを教材で明示する。

`pulp_milp` は「距離」ではなく「**使用台数**」を最小化する、他の 4 strategy とは異なる目的関数を持つ ── README §12.5 の評価項目「車両稼働率」に対応する産業ソルバーの役割分担。

**`_ops` の単位**: `knapsack_dp` = DP セル更新回数、`greedy` = 挿入候補を評価した回数、
`branch_and_bound` = 展開ノード数、`brute_force` = 評価した割当の数。**単位が違うので割り算しない**
(`CLAUDE.md` 命名規約)。`pulp_milp` は `_ops` を出さない。

---

## 4. 章一覧(章 = 作業単位)

`Phase-9-M.md` = 作業単位 9-M。9-1〜9-7 は鎖(9-1 → … → 9-7)、9-8(ジョブキュー)は
problem_type に依存しない横断インフラで 9-7 の後、9-9(UI)は 9-7・9-8 の両方に依存する。

| 章                           | トピック                                                                     | 依存        | 主な内容                                                                                                                                                                                                                        |
| --------------------------- | ------------------------------------------------------------------------ | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-9-1](./Phase-9-1.md) | `logistics_planning` の配線(schema union + semantic + structure + 到達可能性ゲート) | Phase 7-1 | 葉 2 本 / ユニオン / `semantic.py` 3 チェック / `structure.py` 1 arm(純粋述語)/ `graph/adjacency.py::build_logistics_adjacency` / `graph/reachability.py::logistics_deliveries_reachable` / `validation.py` のゲート / fixture                |
| [Phase-9-2](./Phase-9-2.md) | `logistics_common.py` 共通足回り + Verification                               | 9-1       | `parse_logistics_problem` / `all_pairs`(Floyd-Warshall 再利用)/ `capacity_ok` / `route_for_vehicle`(TSP 再利用)/ `route_distance`(与えられた順の検算用)/ `logistics_solution` / `verification._verify_logistics_routes`(新規、`# (Phase 9-2)`) |
| [Phase-9-3](./Phase-9-3.md) | `KnapsackDpLogisticsStrategy`(主力)                                        | 9-2       | `optimization/knapsack_dp_logistics.py`(新規)。`knapsack_2d` の 2 人目の消費者                                                                                                                                                        |
| [Phase-9-4](./Phase-9-4.md) | `GreedyLogisticsStrategy` + `BruteForceLogisticsStrategy`(オラクル)          | 9-2       | `optimization/greedy_logistics.py` / `optimization/brute_force_logistics.py`(新規)                                                                                                                                            |
| [Phase-9-5](./Phase-9-5.md) | `BranchAndBoundLogisticsStrategy`                                        | 9-2       | `optimization/branch_and_bound_logistics.py`(新規)。Phase 6-5 のノード予算パターンの 2 人目の消費者                                                                                                                                             |
| [Phase-9-6](./Phase-9-6.md) | PuLP で使用台数最小化の MILP を解く                                                  | 9-5       | `optimization/pulp_logistics.py`(新規)。`pulp` を `[project].dependencies` に追加                                                                                                                                                  |
| [Phase-9-7](./Phase-9-7.md) | registry + select + end-to-end + プロパティテスト                                | 9-6       | `registry.py`(5 strategy)/ `algorithm_selection.py`(既定 `knapsack_dp`)/ `build_scaled_logistics_problem` を使った 5 者比較(`brute_force` をオラクルに `quality_ratio`)                                                                    |
| [Phase-9-8](./Phase-9-8.md) | ジョブキュー基盤(problem_type 非依存の横断インフラ)                                        | 9-7       | `models/job.py` / `repositories/job.py` / `services/job.py` / `worker.py` / `api/routes/jobs.py`(新規)/ `docker-compose.yml` に `worker` サービス / alembic migration                                                              |
| [Phase-9-9](./Phase-9-9.md) | decitima-ui: Logistics Optimizer ページ + 車両ルート可視化 + ジョブポーリング               | 9-7, 9-8  | `logistics-planner/{api,stores,hooks,components,sample-problems.ts}` / `GraphCanvas` を車両ごとの色分けで再利用 / ジョブポーリング hook                                                                                                          |

9-1〜9-8 が decitima-api、9-9 が decitima-ui。順序の理由: **ドメイン配線(problem_type の葉、新規プリミティブは無いのでいきなり配線から始まる)→ 共通足回り → 手実装 strategy 4 本 → 産業ソルバー → registry + プロパティテスト → 横断インフラ(ジョブキュー)→ UI**。各章は「その章までのファイルで import 解決」(進行のルール #15。Q41 / Q42 の教訓)。

registry の作法(進行のルール #15): `registry.py` の `"logistics_planning"` キーは 9-7 で5 strategy をまとめて有効化する。end-to-end パイプライン(validate→select→solve→verify)が緑になるのは 9-7。9-3〜9-6 の strategy テストは `Strategy().solve(problem)` を直接呼ぶ。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜8 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-9-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 9 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §9 の一覧(冒頭系譜コメントに `Phase 9` を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新されるファイルは変更行が
   `# (Phase 9-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12。
   grep 合言葉: `grep -rn "# (Phase 9" textbook/samples`)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §9 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル                  | 使うもの                               | Phase 9 で書くもの                                                                                                                                      |
| -------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| primitives(純粋・主戦場)   | 素の pytest。DB 不要                    | `build_logistics_adjacency` / `logistics_deliveries_reachable`(9-1)/ `logistics_common` の各関数(9-2)                                                  |
| domain(純粋)           | 素の pytest                          | `LogisticsData` / `LogisticsSolution` の判別可能ユニオン / `SEMANTIC_CHECKS["logistics_planning"]` / `verify_logistics_structure` / `structural_verify` の番人 |
| algorithms(strategy) | 素の pytest                          | knapsack_dp / greedy / branch_and_bound / brute_force / pulp_milp の `solve`                                                                        |
| 5 strategy の比較       | 素の pytest(`for seed`)              | `test_logistics_strategies.py`(brute_force をオラクルに `quality_ratio`、pulp_milp は vehicles_used が最小)                                                   |
| サービス層                | 直接呼ぶ(`test_mst_strategies.py` と同型) | validate→select→solve→verify のパイプライン                                                                                                               |
| ジョブキュー               | **フェイクが必要な最初の章**(9-8)              | `JobService.enqueue` の arq エンキューをフェイク、実ワーカーは integration テスト                                                                                       |
| UI                   | Vitest(node env)                   | logistics-planner store                                                                                                                            |

**スタブ**: strategy / validation / verification は純粋(DB を持たない)。スタブ不要。
**唯一の例外が 9-8**(ジョブキュー)── 外部プロセス(worker)を伴うため、`JobService` の
ユニットテストは arq の enqueue をフェイクに差し替える。「スタブの要否がレイヤー設計の鏡」
(進行のルール #14)を体現する好例として、Phase 9 で初めてスタブが要る章になる。

```bash
# decitima-api/backend(overlay end 状態 = Phase 8 end + Phase 9 samples)で
uv run pytest
# decitima-ui で
npx vitest run src/features/optimization/logistics-planner
```

---

## 7. Phase 9 のスコープと非スコープ

| Phase 9 でやる                                                                     | 送る先                                                                                                                                                                            |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `logistics_planning` problem_type / CVRP(複数車両・容量制約)/ 手実装 4 strategy + PuLP MILP | ―                                                                                                                                                                              |
| ジョブキュー基盤(`arq` + Redis。`POST /api/v1/jobs` / `GET /api/v1/jobs/{id}`)           | ―                                                                                                                                                                              |
| Logistics Optimizer ページ(車両ルート可視化 + ジョブポーリング)                                    | ―                                                                                                                                                                              |
| ―                                                                               | **時間窓(time window)** ── 配送先ごとの訪問可能時間帯。README に明記が無く、資源プロファイル(imos)との統合は Phase 10 以降で需要が出たら                                                                                     |
| ―                                                                               | **経路順序そのものの MILP 化**(劣周回除去制約を伴うフル CVRP)── PuLP は割当(ビンパッキング)だけ。フル MILP 化は需要が出た Phase で `pulp_logistics.py` を拡張                                                                  |
| ―                                                                               | **複数デポ**(multi-depot VRP)── `depot_id` は単数のまま。必要になった Phase で `LogisticsData` を拡張                                                                                               |
| ―                                                                               | **analysis トラック**(`logistics_analysis.py` + notebook)── Phase 8 の前例どおり後続 Phase 送り                                                                                              |
| ―                                                                               | **既存 problem_type の非同期化**(route/shift/network/travel/project を `/jobs` 経由にする)── 9-8 のジョブキューは横断インフラとして用意するが、既存 5 problem_type の呼び出し側(UI)は同期 `/solve` のまま。両立を実演するのは logistics のみ |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)(Phase 9 end 状態)。各ファイル冒頭の
`# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は §9 の実装前チェックリスト参照。
overlay 検証手順は [`textbook/samples/README.md`](../samples/README.md)。

要点:

- `optimization/logistics_common.py` は travel の `travel_common.py` / project の
  `project_common.py` と同じ「共通足回り」── 5 strategy は「配送先→車両の割当」の決め方だけが違う(knapsack_dp=容量DP / greedy=挿入コスト / branch_and_bound=分枝限定 / brute_force=全列挙 /
  pulp_milp=ビンパッキングMILP)。巡回順の確定・距離計算はここに集約(数値の drift 防止)。
- `floyd_warshall` / `knapsack_2d` / `optimize_waypoint_order` は Phase 7 の実装を **1 バイトも変えず** 2 人目の消費者として再利用する ── Phase 9 に新規プリミティブがほぼ無い理由。
- ジョブキューは `arq`(Redis ベース・asyncio ネイティブ)。既存の `redis.asyncio.Redis` 共有プール
  (`app/infrastructure/redis.py`)をそのまま使う ── 新規に sync Redis クライアントを増やさない。
- UI は Phase 4-8 / 5-5 / 6-8 / 7-7 / 8-7 と同型の 6 スライス目。`GraphCanvas` を車両ごとの色分け線で再利用する(ドメイン非依存のチャートの 3 人目の消費者)。

検証: Phase 8 end 状態に Phase 9 samples を overlay し `uv run pytest` / `ruff` / `uvx pyright`(Phase 9 分 0 errors)/ `alembic upgrade head`(`jobs` テーブルのマイグレーションが適用される)/`docker compose up --build` で `worker` サービスが起動すること。decitima-ui に overlay し`npx tsc --noEmit` / `npx vitest run` / `npx eslint`。

---

## 9. Phase 9 実装前チェックリスト

進行のルール #11。行 `9-M` ↔ 章 `Phase-9-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                                                                                                                                                                                                                                           | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9-1 | `app/domain/problems/logistics.py`・`app/domain/solutions/logistics.py`(新規)、`tests/unit/test_logistics_planning.py`(新規)。既存への変更(現行版は samples): `app/domain/problems/{problem,__init__,semantic}.py`・`app/domain/solutions/{solution,__init__,structure}.py`・`app/algorithms/graph/{adjacency,reachability}.py`・`app/services/validation.py`・`tests/fixtures/optimization.py`。**`verification.py` は 9-2** | `LogisticsNode` / `RoadSegment` / `Vehicle` / `DeliveryStop` / `LogisticsData`(`model_validator` で depot・端点実在・id 一意・自己ループ禁止)/ `VehicleRoute` / `LogisticsSolution` / `check_logistics_vehicles_exist` + `check_logistics_capacity_feasible` + `check_logistics_fleet_capacity_covers_demand` / `verify_logistics_structure`(純粋述語 ── 配送先の重複なき全網羅・vehicle_id 実在・distance 合計整合)/ `build_logistics_adjacency` / `logistics_deliveries_reachable` / `validation` の到達可能性ゲート |
| 9-2 | `app/algorithms/optimization/logistics_common.py`(新規)、`tests/unit/test_logistics_common.py`(新規)、`app/services/verification.py`(`_verify_logistics_routes` 追加、`# (Phase 9-2)`)                                                                                                                                                                                                                          | `parse_logistics_problem` / `all_pairs`(Floyd-Warshall 再利用)/ `capacity_ok` / `route_for_vehicle`(TSP 再利用で 1 台分の最適順+距離)/ `route_distance`(与えられた順の距離。検算専用)/ `logistics_solution` / `infeasible_logistics_solution`。`_verify_logistics_routes`(容量再チェック + 距離再計算)                                                                                                                                                                                                          |
| 9-3 | `app/algorithms/optimization/knapsack_dp_logistics.py`(新規)、`tests/unit/test_knapsack_dp_logistics.py`(新規)                                                                                                                                                                                                                                                                                              | `KnapsackDpLogisticsStrategy`(車両ごとに `knapsack_2d` で容量に収まる部分集合を選び TSP で巡回順を決める。`_ops` = DP セル更新回数)                                                                                                                                                                                                                                                                                                                                                                     |
| 9-4 | `app/algorithms/optimization/{greedy_logistics,brute_force_logistics}.py`(新規)、`tests/unit/test_greedy_and_brute_force_logistics.py`(新規)                                                                                                                                                                                                                                                                | `GreedyLogisticsStrategy`(挿入距離増分が最小の車両へ 1 件ずつ)/ `BruteForceLogisticsStrategy`(全割当 × 全順列。正解オラクル)                                                                                                                                                                                                                                                                                                                                                                       |
| 9-5 | `app/algorithms/optimization/branch_and_bound_logistics.py`(新規)、`tests/unit/test_branch_and_bound_logistics.py`(新規)                                                                                                                                                                                                                                                                                    | `BranchAndBoundLogisticsStrategy`(下界 = 確定距離。`_MAX_NODES` で打ち切り `_truncated`)                                                                                                                                                                                                                                                                                                                                                                                          |
| 9-6 | `app/algorithms/optimization/pulp_logistics.py`(新規)、`tests/unit/test_pulp_logistics.py`(新規)。`pulp` を `[project].dependencies` に追加                                                                                                                                                                                                                                                                      | `PulpMilpLogisticsStrategy`(`x[v][d]` + `y[v]` のビンパッキング MILP。`minimize(Σy[v])`。`_ops` なし)                                                                                                                                                                                                                                                                                                                                                                             |
| 9-7 | `app/algorithms/registry.py`・`app/services/algorithm_selection.py`・`tests/unit/{test_algorithm_selection,test_logistics_strategies}.py`(現行版)、`tests/fixtures/optimization.py`(`build_scaled_logistics_problem` 追加)                                                                                                                                                                                     | `registry["logistics_planning"]` = `[knapsack_dp, greedy, branch_and_bound, brute_force, pulp_milp]` / `_preferred_name` の logistics → 既定 `"knapsack_dp"`                                                                                                                                                                                                                                                                                                             |
| 9-8 | `app/models/job.py`・`app/repositories/job.py`・`app/services/job.py`・`app/worker.py`・`app/api/routes/jobs.py`(新規)、`alembic/versions/`(新規 migration)、`docker-compose.yml`(現行版、`worker` サービス追加)、`pyproject.toml`(`arq` 追加)                                                                                                                                                                                | `Job`(id/user_id/problem_type/status/payload の hybrid JSONB)/ `JobRepository` / `JobService.enqueue`・`get_status` / `solve_job(ctx, job_id)`(ワーカー関数。`SolveService.solve` を再利用)                                                                                                                                                                                                                                                                                        |
| 9-9 | `ui: logistics-planner/{api,stores,hooks,components,sample-problems.ts}`(新規)、`app/(pages)/optimization/logistics-planner/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)                                                                                                                                                                                                                          | `solveLogistics` / `submitLogisticsJob` / `pollJob` / `useLogisticsPlannerStore` / `LogisticsPlannerPanel`(車両ごとに色分けした `GraphCanvas`)/ `types.ts` に logistics アーム                                                                                                                                                                                                                                                                                                      |

---

## 10. Phase 9 の成果物

- **textbook**: この `Phase-9/` 一式(導入 + `Phase-9-1`〜`9-9` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/algorithms/optimization/{logistics_common,knapsack_dp_logistics,greedy_logistics,brute_force_logistics,branch_and_bound_logistics,pulp_logistics}.py`(新規)/
  `app/domain/problems/logistics.py`・`app/domain/solutions/logistics.py`(新規)/
  `app/models/job.py`・`app/repositories/job.py`・`app/services/job.py`・`app/worker.py`・
  `app/api/routes/jobs.py`(新規)/
  `app/domain/**`・`app/services/{validation,verification,algorithm_selection}.py`・
  `app/algorithms/{registry,graph/{adjacency,reachability}}.py`・`docker-compose.yml`・
  `pyproject.toml`(現行版)/ `tests/**`
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/logistics-planner/**` /
  `src/app/(pages)/optimization/logistics-planner/page.tsx` /
  `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)
- **既存 Phase 教材への「後続 Phase での改訂」1 行**(`Phase-1-1.md` の判別ユニオンに
  logistics_planning、`Phase-2-introduction.md` に「計算 / 述語」の 5 例目、`Phase-6-introduction.md`
  の B&B ノード予算パターンの 2 人目の消費者、`Phase-7-introduction.md` の
  Floyd-Warshall / knapsack_2d / optimize_waypoint_order の 2 人目の消費者、`Phase-0-2.md` §8.1)
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 9 要点**(経緯は `textbook/q_a.md` Q48)
- **`textbook/samples/README.md` の「最終検証」スタンプ**を Phase 9 に更新

---

## 11. 次のフェーズ

Phase 9 完了で **6 つ目の problem_type `logistics_planning`** が端から端まで通る。Phase 4〜8 で個別に習得したアルゴリズム(グラフ探索・DP・貪欲法・分枝限定法)を 1 つの複合問題(CVRP)で組み合わせ、産業ソルバートラックに PuLP(MILP)を新規追加し、MVP 以来 YAGNI で見送ってきたジョブキュー(非同期実行基盤)を初めて導入した。

その先は README §20 の拡張順 ── **Simulation(Phase 10、What-if。全ドメインが出そろった後に条件変更・複数シナリオ生成・Cost/Time/Quality 比較・Sensitivity Analysis)→ LLM(Phase 11〜13、Natural Language → Structured Problem / Algorithm Recommendation / Result Explanation)→
LLM vs Algorithm Benchmark(Phase 14)→ Production(Phase 15)**。

---

## 12. 後続 Phase での改訂

- **Phase 10-4**: `app/schemas/job.py::JobStatusResponse.result` の型を `CandidateSolution | None`
  から `CandidateSolution | SimulationResult | None` に広げた ── simulate ジョブ(Phase 10)の
  結果も既存の `GET /api/v1/jobs/{id}` で返せるようにするため。両型の必須フィールドが重ならない
  ため discriminator タグは不要、`app/worker.py::solve_job` の書き込み方・既存テストは無改造
  (詳細 `Phase-10-4.md`、経緯 `q_a.md` Q53)。
