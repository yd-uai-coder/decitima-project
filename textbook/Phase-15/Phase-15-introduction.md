# Phase 15 — Production(最終フェーズ)導入

作業章(`Phase-15-1.md` 以降)を始める前に、この 1 本で Phase 15 の全体像を掴む。
目的 / パイプライン上の位置づけ / 章一覧 / 進め方 / テスト / スコープ / 実装前チェックリスト /サンプルコード一覧 / 成果物 / 次のフェーズ。

> **Phase 15 は README §20 の Phase 順序で最後にあたるフェーズ**。README §15「Production」──
> 「実サービスとして公開できる品質へ仕上げる」。Phase 0〜14(MVP + LLM層6フェーズ)で6ドメインのアルゴリズム・検証・LLM層がすべて揃った今、Testing / Performance / Security /Deployment の4本柱で仕上げる。
> 
> 開始にあたりユーザーに4点を確認し、以下の方針で進める:
> 
> | 論点                     | 決定                                                                            |
> | ---------------------- | ----------------------------------------------------------------------------- |
> | Deployment(VPS/Vercel) | **教材化のみ**。CI/CD・Dockerfile監査・デプロイRunbookを作るが実インフラは作らない                        |
> | E2E(Playwright)        | **代表2ドメインのみ**(Route Planner + Travel Planner)。他4ドメインは同型なので省略                  |
> | 負荷テストツール(locust/k6)    | **見送る**。既存 `measure_call`/`BenchmarkService`(Phase 3)によるアルゴリズムレベルの大規模入力テストに絞る |
> | 4本柱のカバー範囲              | **すべて今回カバー**。Security/Deployment は監査中心で軽め、Testing/Performance は新規構築中心         |

---

## 1. このフェーズの目的

README §15 の原文:

> **目的:実サービスとして公開できる品質へ仕上げる**
> 
> - Testing: Unit / Integration / API / E2E / Algorithm / Constraint Test
> - Performance: Algorithm Benchmark / DB Query Optimization / 非同期処理 / Cache / 大規模入力テスト
> - Security: Authentication / Authorization / Input Validation / Rate Limit / CORS / Secret Management
> - Deployment: GitHub → GitHub Actions → Docker → VPS(API)、Next.js → Vercel(UI)
> 
> **設計のポイント**: セキュリティ・インフラの多く(認証・レート制限・CORS・Docker・CI)はテンプレートが既に足場を提供しており、作り直さず再利用する。

Phase 0〜14 の間、いくつかの項目が「Phase 15 で検討」として明示的に先送りされてきた。
Phase 15 の役割の半分は **これまでの積み残しの回収** でもある:

| 積み残し項目                                                   | 出所             | 本 Phase での扱い                               |
| -------------------------------------------------------- | -------------- | ------------------------------------------ |
| `_MAX_KNAPSACK_DP_CELLS`(travel の knapsack_dp ガード)の実測見直し | Phase 11-9     | 15-2 で実測再検証                                |
| `logistics_planning` の knapsack_dp に同型ガードが必要か            | Phase 11-9     | 15-2 で実測、**不要と判断**(理由は §6)                 |
| `topological_sort`(DFS)を Kahn 法へ置換すべきか                   | Phase 8-1(Q46) | 15-3 で実測 ──**置換が必要と判明**(理由は §6)            |
| `analysis/benchmark_report.py::regression()` の CI 配線     | Phase 3-8      | 15-10 で配線                                  |
| travel_planning のカタログ固定問題の再設計                            | Phase 11-10    | **本 Phase の対象外**(Phase 15 完走後に再検討、と既に確定済み) |

## 2. アーキテクチャ ── 「新しい層を足さない」フェーズ

Phase 15 は Phase 4〜14 のように新しい `problem_type` やレイヤーを追加しない。既存レイヤーの**性質**(速さ・堅牢さ・観測可能性)を上げるフェーズなので、位置づけは横方向:

```text
routes → services ─┬→ domain            ← 変更なし(15-6のみ services を薄く改訂)
                   ├→ algorithms        ← 15-2(ガード値)/ 15-3(topological_sort)
                   └→ repositories → models   ← 15-4(監査のみ、変更なし)
                                    ↑
                              app/worker.py    ← 15-5(WorkerSettings)
                                    ↑
                         tests/performance/**  ← 15-1 新設(横断的なテスト基盤)
                                    ↑
                    .github/workflows/** / Dockerfile監査 / Runbook   ← 15-10 / 15-11
```

## 3. 章一覧(章 = 作業単位)

依存関係: `15-1 → {15-2, 15-3, 15-4}(並行)`、`15-4 → 15-6`、`15-3 → 15-5`、
`{15-7, 15-8} は 15-1 と並行着手可`、`15-8 → 15-9`、`15-10 は 15-2〜15-7・15-9 が揃ってから`、`15-11 は 15-10 の後`。

| 章                               | トピック                                  | 依存              | 主な内容                                                                                            |
| ------------------------------- | ------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------- |
| [Phase-15-1](./Phase-15-1.md)   | 性能テスト基盤 + Testing階層監査                 | なし              | `tests/performance/`新設(`generators.py`/`conftest.py`)、`performance` マーカー追加。README§15の6テスト種別の監査表 |
| [Phase-15-2](./Phase-15-2.md)   | 性能ガード実測(travel/logistics knapsack_dp) | 15-1            | `_MAX_KNAPSACK_DP_CELLS` 再測定・改訂、logistics ガード要否の実測判断                                            |
| [Phase-15-3](./Phase-15-3.md)   | `topological_sort` 大規模実測 → Kahn法へ置換   | 15-1            | DFS版の再帰上限クラッシュを実測で確認、Kahn法(反復)へ置換                                                               |
| [Phase-15-4](./Phase-15-4.md)   | DBクエリ最適化監査                            | 15-1            | `EXPLAIN ANALYZE` による実測監査、追加インデックス不要と結論                                                         |
| [Phase-15-5](./Phase-15-5.md)   | 非同期処理チューニング(arqワーカー)                  | 15-3            | `WorkerSettings.max_jobs` の明示設定 + スループット実測                                                      |
| [Phase-15-6](./Phase-15-6.md)   | キャッシュ層(Solution Explanation)          | 15-4            | `SolutionExplanationService.explain()` の Redis キャッシュ化                                           |
| [Phase-15-7](./Phase-15-7.md)   | セキュリティ監査 + ドキュメント化                    | なし(15-1と並行可)    | 6項目(Authn/Authz/Validation/RateLimit/CORS/Secret)の監査、`SECURITY.md`                              |
| [Phase-15-8](./Phase-15-8.md)   | Playwright セットアップ + Route Planner E2E | なし(15-1と並行可)    | Playwright導入、直接入力→solveのE2Eシナリオ                                                                 |
| [Phase-15-9](./Phase-15-9.md)   | LLM構造化 → Travel Planner E2E           | 15-8            | 自然言語入力→確認カード→solveのE2Eシナリオ                                                                      |
| [Phase-15-10](./Phase-15-10.md) | CI/CD ワークフロー                          | 15-2〜15-7, 15-9 | GitHub Actions(backend-ci.yml / ui-ci.yml)、回帰チェックの配線                                            |
| [Phase-15-11](./Phase-15-11.md) | デプロイRunbook + プロジェクト完走                | 15-10           | 既存Docker資産の監査、VPS/Vercel手順書、Phase 15まとめ                                                         |

15-1〜15-7, 15-10(backend側)は `decitima-api`、15-8/15-9 は `decitima-ui`、
15-10/15-11 は両リポジトリ + インフラ文書にまたがる。

## 4. この Phase の進め方 ── 実装 = 写経(Phase 1〜14 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-15-*.md`)は要点の抜粋だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 15 end 状態)。
2. `textbook/samples/{app,tests}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/**` → `decitima-ui/…` へファイル単位で写経・改変。
3. 既存ファイルの改訂は「旧コードをコメントアウト + `# (Phase 15-M)` タグ付きで追記」
   (進行のルール #12)。grep 合言葉: `grep -rn "# (Phase 15" textbook/samples`。
4. **本 Phase は「実測してから直す」章が多い**(15-2/15-3/15-4)。各章は実測手順そのものを教材化する ── これは README が繰り返し強調する「決定論的・検証可能」という設計思想の総仕上げでもある。実装中の疑問は Claude に相談し、教材と samples に還流させる(#8/#9)。

**着手前に §7 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

## 5. テストの階層

| レベル          | 使うもの                                                            | Phase 15 で書くもの                                                          |
| ------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 大規模入力(性能)    | 素の pytest、`performance` マーカー(既定実行から除外)                          | `tests/performance/**`(15-1〜15-3)                                       |
| アルゴリズム単体     | 素の pytest                                                       | `test_topological_sort.py` 改訂(15-3)                                     |
| サービス層(キャッシュ) | `db_session` + `FakeRedis`                                      | `test_explanation_cache.py`(15-6)                                       |
| ワーカー         | 素の pytest(純粋関数部分)+ integration(実 arq、既存 `test_jobs_e2e.py` 再実行) | `WorkerSettings` の設定値テスト(15-5)                                          |
| E2E          | Playwright(実ブラウザ、実バックエンド)                                       | `e2e/route-planner.spec.ts`・`e2e/travel-structuring.spec.ts`(15-8/15-9) |
| CI           | GitHub Actions(実行環境)                                            | `.github/workflows/{backend-ci,ui-ci}.yml`(15-10)                       |

**用語(初出 Phase 12 で定義済み、以降は関係の明記のみ)**: SUT(テスト対象)/ ドライバ(テストを駆動するもの)/ スタブ(テストダブル)。

```bash
# decitima-api/backend(overlay end 状態)で
uv run pytest                       # 既定実行(performance/integration を除外)
uv run pytest -m performance        # 大規模入力テストのみ(時間がかかる)
# decitima-ui で
npx playwright test
```

## 6. 実測で判明した結論(教材の核)

**この Phase の核心は「実測してから直す」という手順そのもの** ── README が一貫して掲げる「決定論的・検証可能」という設計思想を、コードだけでなくプロジェクト運営そのものに適用する。
結論は一方向(緩和)には倒れず、緩和・現状維持・実際の不具合修正・見落とし発見の**4通り**が実際に出た。

- **`_MAX_KNAPSACK_DP_CELLS`(travel)は実測の結果、緩和できる ── ただし計測方法そのものに
  誤りがあった**。`_MAX_KNAPSACK_DP_CELLS` が実際に保護しているのは `POST /solve` の既定選択(素の1回呼び出し)だけで、`POST /benchmark`(`get_strategies` で全候補を回す)は保護していなかったことが判明 ── Phase 11-9 のコメントの前提誤り。さらに `measure_call`(`tracemalloc`計装)は `knapsack_2d` のような大量の小オブジェクト割当を行うアルゴリズムで**10倍以上の見かけの遅さ**を生む(4,000,000セルで素の1.84秒 vs 計装ありで20.6秒)ことも発見した。
  `POST /solve` の実経路(素の呼び出し)基準で再計測し、閾値を2,000,000→4,000,000へ緩和。
  Phase 11-9 の実インシデント(cells=8,000,000)は引き続きガードされる(詳細 15-2)。
- **`logistics_planning` の knapsack_dp には対応するガードが不要と判明した**。理由は速度でなく**攻撃面の違い**: `LogisticsDataPatch`(Phase 11 の LLM抽出スキーマ)は `depot_id` しか公開しておらず、`capacity_weight`/`capacity_volume` は LLM が触れない(常にベース問題の固定カタログ由来)。travel の `budget`/`time_budget` は `TravelDataPatch` で LLM が自由に埋められるスカラーであり、これが Phase 11-9 の実インシデントを生んだ根本原因だった(詳細 15-2)。
- **`topological_sort`(DFS版)は大規模な線形依存チェーンで実際にクラッシュする**。
  線形チェーン(T0→T1→…→T(n-1))で n≈999 から Python既定の再帰上限(1000)に達し
  `RecursionError` で `solve()` 全体が落ちる。Phase 8-1 の理論章が「反復で再帰上限に当たらない」とKahn法の利点を予告していた通りの結果が、Phase 15 の実測で具体的に確認された ──
  **これは投機的リファクタではなく、実測で実証された不具合の修正**(進行のルール #17 の「実在の消費者」テストに Phase 15 自身の大規模入力テストという形で具体的に答えられる)。
  `has_cycle`/`successors_from_edges` のシグネチャは不変のまま Kahn 法(入次数キュー)へ置換した(詳細 15-3)。
- **DBクエリは既存インデックスで十分**。20,000件のproblem + 1問題あたり5,000件のsolution(実運用よりかなり大きい想定)でも `get_solution`/`list_solutions_for_problem` はともに数ミリ秒で完了(実測は 15-4)。新規インデックスは追加しない。
- **CPU バウンドな arq ジョブは同時実行数を増やしても真の並列化はされない**(CPython の GIL)。10並列で単発の約10.4倍の壁時計時間になることを実測で確認し、`max_jobs` を arq既定の10から4に下げた(詳細 15-5)。
- **本番 `docker-compose.prod.yml` に `worker` サービスが無い見落としを発見した**。
  `POST /jobs`/`POST /simulate` は受理されるが処理されず無応答のまま、という実害のあるギャップ ── テンプレート資産だけでなく DeciTima 固有の追加分の本番反映漏れも監査対象になることを示した(詳細 15-11)。

## 7. Phase 15 のスコープと非スコープ

| Phase 15 でやる                              | Phase 15 でやらない(理由)                                                                                        |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 大規模入力での実測 + ガード値の再検証(travel/logistics)    | **travel_planning のカタログ再設計**(Phase 11-10)── Phase 15完走後に要件を再検討する、と既に確定済み                                  |
| `topological_sort` の実測 + 必要なら Kahn法へ置換    | **メタヒューリスティクス**(焼きなまし法等)── 独立した未着手課題、本Phaseと無関係(Q49)                                                      |
| DBクエリ監査、非同期ワーカーのチューニング                    | **locust/k6等のHTTPレベル負荷テストツール導入**── ユーザー確認により見送り。アルゴリズムレベルの大規模入力テストに絞る                                     |
| Solution Explanation のキャッシュ導入(1つの現実的な消費者) | **BASE_PROBLEMS/ALGORITHM_DESCRIPTIONS等のキャッシュ化**── 純メモリ辞書でI/Oコストが無く、Redis化はむしろ遅くなる(ルール#17の「実在の消費者」を満たさない) |
| Security 6項目の監査 + `SECURITY.md`           | **認証方式・レート制限アルゴリズムの作り直し**── テンプレート資産をそのまま再利用(README §15設計のポイント)                                           |
| Playwright導入 + 代表2ドメイン(Route/Travel)のE2E  | **残り4ドメイン(network/shift/project/logistics)のE2E**── ユーザー確認により「同型なので省略」と明記のみ                                |
| CI/CDワークフロー(GitHub Actions)の新設            | **実際のVPS契約・ドメイン取得・Vercelアカウント連携**── ユーザー確認により教材化のみ(Dockerfile/compose/Runbookの整備に留める)                     |

## 8. Phase 15 実装前チェックリスト

進行のルール #11。行 `15-M` ↔ 章 `Phase-15-M`。

| #     | 作る / 変えるファイル                                                                                                                                                                                     | 主なクラス・関数の責務(1行)                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| 15-1  | `tests/performance/generators.py`・`conftest.py`(新規)、`pyproject.toml`(`performance` マーカー追記)。**追補**: `tests/analysis/conftest.py`(新規)、`pyproject.toml`(`analysis` マーカー追記)                                                                                                       | `linear_chain_successors`(topological用の最悪形状生成)/ 既存 `build_scaled_*` フィクスチャを `budget`/`time_budget` 引数で拡張利用する薄いラッパー / **追補**: analysis依存群未導入環境でのcollection中断を防ぐ    |
| 15-2  | `app/services/algorithm_selection.py`(改訂)、`tests/fixtures/optimization.py`(`build_scaled_travel_problem` に `budget`/`time_budget` 引数追加)、`tests/performance/test_algorithm_selection_perf.py`(新規) | `_MAX_KNAPSACK_DP_CELLS` 実測再検証(2,000,000→4,000,000)/ logistics ガード不要の実測確認                                             |
| 15-3  | `app/algorithms/graph/topological.py`(改訂、Kahn法へ置換)、`tests/unit/test_topological_sort.py`(改訂)、`tests/performance/test_topological_perf.py`(新規)                                                    | `topological_sort`(反復・入次数キュー版)/ `has_cycle`/`successors_from_edges`(シグネチャ不変)                                          |
| 15-4  | (コード変更なし。監査結果は本章 + `CLAUDE.md` Notes に記録)                                                                                                                                                        | `EXPLAIN ANALYZE` による `get_solution`/`list_solutions_for_problem` の実測監査                                               |
| 15-5  | `app/worker.py`・`app/core/config.py`(改訂、`WORKER_MAX_JOBS`)                                                                                                                                       | `WorkerSettings.max_jobs` 明示設定 + 複数ジョブ同時投入時のスループット実測                                                                  |
| 15-6  | `app/services/explanation.py`・`tests/fixtures/fake_redis.py`(改訂、get/set追加)、`tests/unit/test_explanation_cache.py`(新規)                                                                            | `SolutionExplanationService.explain()` の Redis キャッシュ(`solution_id` キー、TTL付き)                                          |
| 15-7  | `textbook/samples/SECURITY.md`(新規)、`app/core/config.py`(改訂、CORS_ORIGINS監査結果次第)                                                                                                                   | Authn/Authz/Validation/RateLimit/CORS/Secret の6項目監査表                                                                  |
| 15-8  | `ui/playwright.config.ts`・`ui/package.json`(新規、初出Phase15)、`ui/e2e/route-planner.spec.ts`(新規)                                                                                                     | ログイン→Route Planner直接入力→solveのE2Eシナリオ                                                                                  |
| 15-9  | `ui/e2e/travel-structuring.spec.ts`(新規)、`app/ai/llm/e2e_fixture.py`(新規)、`app/ai/llm/gemini.py`(初出Phase15、改訂)、`app/core/config.py`(改訂、`E2E_TESTING`)、`tests/unit/test_e2e_fixture.py`(新規)         | `get_gemini_llm()`のE2E用フェイク経路(`E2eFakeLLM`)、自然言語入力→確認カード→solveのE2Eシナリオ                                                |
| 15-10 | `.github/workflows/backend-ci.yml`・`ui-ci.yml`(新規)、`scripts/ci_regression_check.py`・`analysis/data/ci_baseline_benchmark_runs.jsonl`(新規)                                                         | lint/pyright/pytest/Dockerビルド(backend)、lint/vitest/playwright/build(ui)、`regression()`(Phase 3-8)を初めて配線した性能回帰チェックstep |
| 15-11 | `textbook/samples/docker-compose.prod.yml`(新規、初出Phase15。`worker`サービス追加)、`textbook/samples/DEPLOYMENT.md`(新規)                                                                                     | 既存Docker資産の監査(`worker`サービス欠落を発見・修正)+ VPS/Vercelデプロイ手順書(教材のみ、実インフラなし)                                                  |

## 9. サンプルコード一覧 ── 共有 `textbook/samples/`

要点:

- **本 Phase の実測は全て本物の環境で行った**(架空の数字ではない)── `uv run python` での`knapsack_2d` 直接計測、`topological_sort` の `RecursionError` 再現、稼働中の`decitima-api` dev環境(docker compose)の PostgreSQL に対する実 `EXPLAIN ANALYZE`(トランザクション内で大量の合成データを投入し `ROLLBACK` で復元、実データへの影響なし)。
- **ガード値の再チューニングと Kahn法置換は対照的な結論になった** ── travel/logisticsは「measured, still safe, keep or relax」、topological_sortは「measured, actually breaks,must fix」。同じ「実測してから判断する」手順が、Phase によって「現状維持」と「修正」の両方の結論に至ることを Phase 15 は両方の実例で示す。
- `SolutionExplanationService` のキャッシュは、他の2つの静的辞書(`BASE_PROBLEMS`/`ALGORITHM_DESCRIPTIONS`)が rule #17 の「実在の消費者」テストに落ちる比較対象として15-6 で明示的に検討される。

検証: 全11章完了後、`textbook/samples/` を `decitima-api/backend`・`decitima-ui` のクリーンな複製に1回 overlay し、`uv run pytest`(**639 passed** ── 既定636 + performance限定3)/`ruff check`・`ruff format --check`(`app/services/errors.py` の pre-existing 債務のみ、Phase 15 の新規/改訂ファイルは全て clean)/ `uvx pyright app tests`(**0 errors**)/`alembic upgrade head`(既存no-op)/ decitima-ui側 `npx tsc --noEmit`(clean)/ 既存`npx vitest run`(src/ 無変更につき既存回帰なし)/ `npx eslint`(clean)/`npx playwright test`(**2 passed**、うち1本は隔離環境で実行し共有dev環境は無変更)を確認した(詳細は各章末と `textbook/samples/README.md` の最終検証ログ)。

## 10. Phase 15 の成果物

- `textbook/Phase-15/`(この導入 + `Phase-15-1`〜`15-11`)
- `textbook/samples/` の更新一式(§8 のファイル一覧)
- `Phase-11-introduction.md`・`Phase-13-introduction.md`・`Phase-9-introduction.md`・`Phase-8-introduction.md`/`Phase-8-1.md` への「後続 Phase での改訂」節追加
- ルート `CLAUDE.md`「### 設計判断・検証知見」への Phase 15 要点追記
- `textbook/q_a.md` への質問ログ追記
- `textbook/samples/README.md` の「最終検証」スタンプ更新

## 11. 次のフェーズ ── プロジェクトの完走

README §20 の Phase 0〜15 がこれで完走する。これ以降に明確な「次の Phase」は無い。
開発ポリシーが定義する CL(Curriculum Loop)開発の締めくくりとして、
`textbook/appendix/cl-development-retrospective.md` に **プロジェクト完走の振り返り**(15-11 で追記)を残す。

明確に「独立した将来課題」として記録され、着手時期未定のまま残るもの:

- **travel_planning のカタログ再設計**(Phase 11-10)── Phase 15完走を待っていた再検討
- **メタヒューリスティクス**(焼きなまし法・タブーサーチ・遺伝的アルゴリズム)による
  複数手法比較教材(Q49)── 新 Phase 1本相当の規模、着手時期未定
- 本 Phase で見送った項目(§7 非スコープ列)── 実VPS/Vercelデプロイ、HTTPレベル負荷テスト、残り4ドメインのE2E
