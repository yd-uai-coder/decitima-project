# Phase 13 — Result Explanation(実装フェーズ)導入

作業章(`Phase-13-1.md` 以降)を始める前に、この 1 本で Phase 13 の全体像を掴む。
目的 / パイプライン上の位置 / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト /次のフェーズ。

> README §13「Result Explanation」で計画された、Algorithm Engine が計算した結果を人間に説明する機能を実装するフェーズ。LLM 層(Phase 11 構造化 → Phase 12 推薦 → **Phase 13 説明**→ Phase 14 比較)の 3 番目。
> 
> キックオフ確認(3 点、詳細 `q_a.md` Q62):
> 
> | 論点      | 決定                                                                  |
> | ------- | ------------------------------------------------------------------- |
> | 対象データ   | **永続化済み `Solution` を id 指定**(`POST /api/v1/solutions/{id}/explain`) |
> | 他候補との違い | **Phase 12 の静的説明表を比較材料にする**(他アルゴリズムを再 solve しない)                    |
> | 永続化     | **しない**(Phase 9 Simulation・Phase 12 Recommendation と同じステートレス設計)     |

## 1. このフェーズの目的

README §13 はこのフェーズの目的を一言で定義する:

```text
Algorithm Result
     ↓
    LLM
     ↓
Explanation
```

**説明対象(5項目)**: なぜこの解になったか / どの制約が重要だったか / どのアルゴリズムを
使ったか / 他の候補との違い / 改善余地。

**最大の設計論点**: README §0「LLM に最適解を計算させない」の徹底は Phase 13 でも変わらない。
LLM は `CandidateSolution` が既に持つ検証済みの事実(`produced_by`/`metrics`/`violations`)を**narrate(説明)するだけ**で、新しい計算・判定は一切行わない。この点は README 設計のポイント2行目にも明記されている:

> すべての `CandidateSolution` が必ず持つ `produced_by` + `metrics` + `violations` を消費する
> ── Phase 0 で敷いた説明可能性(NFR-4)の土台がここで回収される。

すでに完成しているもの / いつ:

| 資産                                                        | 由来        | Phase 13 での役割           |
| --------------------------------------------------------- | --------- | ----------------------- |
| `CandidateSolution`(`produced_by`/`metrics`/`violations`) | Phase 0〜1 | 説明の元データ(NFR-4 の回収)      |
| `OptimizationReadService.get_solution`/`get_problem`      | Phase 1   | 所有者スコープ付きの永続化データ読み取り    |
| `_ALGORITHM_DESCRIPTIONS`(静的説明表)                          | Phase 12  | 「他候補との違い」の比較材料(2人目の消費者) |
| `get_gemini_llm(...).with_structured_output(Schema)`      | Phase 11  | LLM 説明生成の構造化出力に再利用      |
| グレースフルデグレード + `logger.warning` の型                         | Phase 12  | LLM 失敗時、機械的な要約にフォールバック  |

新規 / 中身:

| 資産                                                               | 中身                                                        |
| ---------------------------------------------------------------- | --------------------------------------------------------- |
| `app/domain/problems/algorithm_catalog.py`                       | Phase 12 の `_ALGORITHM_DESCRIPTIONS` を抽出・公開した共有モジュール      |
| `app/schemas/explanation.py`                                     | API 契約(`ExplanationResponse`)+ LLM 契約(`LlmExplanation`)   |
| `app/services/explanation.py`                                    | `SolutionExplanationService`。DB 読み取り + LLM 呼び出し + フォールバック |
| `POST /api/v1/solutions/{solution_id}/explain`                   | 既存 `routes/solutions.py` に追加(新ファイルは作らない)                  |
| UI: `features/optimization/{api,stores,hooks,components}` の説明カード | 6 ドメイン共通、既存 6 panel に導線を追加                                |

## 2. パイプライン上の位置 ── 「他候補との違い」は再計算しない

```text
(既存、無変更)
ユーザー → /solve(persist: true) → 永続化された Problem/Solution

(Phase 13 で追加。永続化済みの解があればいつでも呼べる、呼ばなくてもよい)
POST /solutions/{solution_id}/explain
  ├─ OptimizationReadService: 所有者スコープ付きで Problem/Solution を読む(既存、無変更)
  ├─ app.domain.problems.algorithm_catalog: 同じ problem_type の他候補の説明を引く(再 solve しない)
  └─ LLM: get_gemini_llm().with_structured_output(LlmExplanation) → 5項目の説明文
```

- **他候補を実際に solve し直さない**。Phase 12 の静的説明表をそのまま比較材料に使う ──
  追加の計算コストなしで README の説明対象5項目を揃えられる(キックオフ確認の2点目)。
- **唯一の新規設計判断**: Phase 12 の `_ALGORITHM_DESCRIPTIONS`(`algorithm_recommendation.py`
  内の非公開定数)が Phase 13 で2人目の消費者を得る。`app/domain/problems/algorithm_catalog.py`
  へ抽出し、命名規約(「先頭 `_` = 非公開」)に従って `ALGORITHM_DESCRIPTIONS`(公開)に改名する
  ── 進行のルール #17「この共通化を今駆動している実在の消費者は何か」に Phase 13 が具体名で答えられるケース。Phase 12 コードへの遡及変更なので進行のルール #12 の記録が伴う(詳細 13-1)。
- LangGraph は使わない(Phase 12 と同じ判断)。DB 読み取り 1 回 + LLM 呼び出し高々 1 回の単純な流れのため、素の async 関数で十分。

## 3. 章一覧(章 = 作業単位)

13-1 → 13-2 → 13-3 は鎖(スキーマ+カタログ共有化 → サービス → ルート)。13-4(UI)は 13-3 に依存する。

| 章                             | トピック                         | 依存          | 主な内容                                                                                                                                         |
| ----------------------------- | ---------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-13-1](./Phase-13-1.md) | スキーマ + アルゴリズムカタログの共有化        | Phase 12 まで | `app/schemas/explanation.py`(新規)、`app/domain/problems/algorithm_catalog.py`(新規、Phase 12 から抽出)、`app/services/algorithm_recommendation.py`(改訂) |
| [Phase-13-2](./Phase-13-2.md) | `SolutionExplanationService` | 13-1        | DB 読み取り・比較材料の組み立て・LLM 呼び出し・レート制限・フォールバック                                                                                                     |
| [Phase-13-3](./Phase-13-3.md) | ルート配線 + e2e                  | 13-2        | `POST /api/v1/solutions/{solution_id}/explain`(既存 `routes/solutions.py` に追加)                                                                 |
| [Phase-13-4](./Phase-13-4.md) | UI(説明カード)                    | 13-3        | `features/optimization/{api,stores,hooks,components}` + 6 panel への導線                                                                         |

## 4. この Phase の進め方 ── 実装 = 写経(Phase 1〜12 と同じ)

1. Claude が教材(この導入 + 4 章)とサンプル(`textbook/samples/`)を書く。実コードは
   書かない ── 実装は `decitima-api`/`decitima-ui` にユーザーが写経する。
2. 各章は「この章で作成/更新するファイル」を明記し、責務 1 行 + 非自明な判断を解説する。
3. 章を読み終えたら該当ファイルを写経し、章末のテストを実行して緑を確認してから次の章へ。
4. samples のフル検証は共有 `textbook/samples/` を 1 回 overlay して回す
   (`textbook/samples/README.md`)。今回は backend `uv run pytest` 602 passed(新規 14 ──
   catalog 3 / schema 2 / service 5 / api 3、+ Phase 12 既存テストの無改造再実行1式)、`ruff check` / `ruff format --check` / `uvx pyright` いずれも 0 件(既存 `app/services/errors.py` の pre-existing 債務は対象外)。ui `npx tsc --noEmit` clean、`npx vitest run` 77
   passed(既存回帰なし)、`npx eslint` 0 件。`alembic upgrade head` は no-op(永続化しない設計のため新テーブル無し)。

## 5. テストの階層

| レベル           | 使うもの                                                 | Phase 13 で書くもの                                                       |
| ------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| カタログ(純粋)      | 素の pytest                                            | `test_algorithm_catalog.py`(13-1、抽出後も値が不変であること・registry との1対1対応)     |
| スキーマ(純粋)      | 素の pytest                                            | `test_explanation_schemas.py`(13-1、型定義の確認)                           |
| サービス(unit)    | `FakeLLM` + `FakeRedis` + `SolveService`(実データを1件永続化) | `test_explanation_service.py`(LLM成功/失敗フォールバック/404/レート制限)             |
| API(e2e)      | `api` fixture(認証込み client)                           | `test_explanation_api.py`(配線確認 + 既存 `GET /solutions/{id}` の回帰)       |
| UI store/hook | vitest + `vi.mock`                                   | `explanation-store.test.ts`・`explain.test.ts`・`solve.test.ts`(API 層) |

**用語**(Phase 12 で初出、以降は関係の明記のみ): SUT(テスト対象)/ ドライバ(テストを
実行するもの)/ スタブ(外部依存の代役)。

## 6. Phase 13 のスコープと非スコープ

| Phase 13 でやる                                                        |
| ------------------------------------------------------------------- |
| 永続化済み解を id 指定で自然言語に説明する新エンドポイント                                     |
| README §13 の説明対象5項目(なぜこの解か / どの制約が重要か / どのアルゴリズムか / 他候補との違い / 改善余地) |
| LLM 失敗時、metrics/violations から直接組み立てる機械的なフォールバック                     |
| Phase 12 静的説明表の共有モジュールへの抽出(2人目の消費者に伴う共通化)                           |

- **説明結果の永続化**(`Solution.payload` への保存等)── キックオフ確認で見送り。
  必要になれば独立した検討課題(着手時期未定)。
- **他アルゴリズムの実 solve による比較**── Phase 12 の静的説明表で代替する。実測比較が要る場合は Phase 3 `benchmark_runs` を読む設計への拡張として将来検討する。
- **README §14「LLM vs Algorithm Comparison」**── Phase 13 は「1つの解を説明する」だけで、複数手法の実測比較(制約遵守率・最適性・再現性・実行時間・エラー率)は Phase 14。
- **候補アルゴリズムの新規追加**(registry への新 strategy 登録)── このフェーズでは行わない。

## 7. Phase 13 実装前チェックリスト

進行のルール #11。行 `13-M` ↔ 章 `Phase-13-M`。

| #    | 作る / 変えるファイル                                                                                                                                                                                                                                                                                      | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                   |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 13-1 | `app/domain/problems/algorithm_catalog.py`(新規、Phase 12 から抽出)、`app/schemas/explanation.py`(新規)、`app/services/algorithm_recommendation.py`(改訂、import に変更)、`tests/unit/test_algorithm_catalog.py`(新規)、`tests/unit/test_explanation_schemas.py`(新規)                                                   | `ALGORITHM_DESCRIPTIONS`/`describe_algorithm`(公開カタログ)/ `ExplanationResponse`(API契約)/ `LlmExplanation`(LLM契約)                                                                                                                                       |
| 13-2 | `app/services/explanation.py`(新規)、`app/core/config.py`(改訂、レート制限フィールド追加)                                                                                                                                                                                                                           | `SolutionExplanationService.explain()`(DB読み取り・比較材料組み立て・LLM呼び出し・フォールバック)/ `_alternatives_text`/`_explain_prompt`/`_fallback_response`(私設ヘルパ)/ `EXPLAIN_RATE_LIMIT_PER_HOUR`/`_PER_DAY`(設定フィールド追加)                                                   |
| 13-3 | `app/api/routes/solutions.py`(改訂)、`tests/api/test_explanation_api.py`(新規)                                                                                                                                                                                                                         | `explain_solution()`(ルートハンドラ追加、既存 `get_solution`/`get_problem`/`list_problem_solutions` はそのまま)                                                                                                                                                     |
| 13-4 | `ui/src/lib/api/types.ts`(改訂)、`ui/.../api/{solve,explain}.ts`(新規)、`ui/.../stores/explanation-store.ts`(新規)、`ui/.../hooks/useSolutionExplanation.ts`(新規)、`ui/.../components/ExplanationCard.tsx`(新規)、6 つの既存 Planner Panel(改訂)、テスト一式(`solve.test.ts`・`explain.test.ts`・`explanation-store.test.ts`) | `ExplanationResponse`(型)/ `persistSolve`/`explainSolution`(POSTの薄いラッパ)/ `useExplanationStore`(result/status/error/run/reset、`recommendation-store` と同型)/ `useSolutionExplanation`(storeの薄いラッパ)/ `ExplanationCard`(説明カードUI、6ドメイン共通)/ 各 Panel への導線1行 |

## 8. サンプルコード ── 共有 `textbook/samples/`

要点:

- **`_ALGORITHM_DESCRIPTIONS` → `ALGORITHM_DESCRIPTIONS` への抽出は値を一切変えない**
  ── 置き場と公開範囲だけが変わる(Q38 `shift_metrics.py` 抽出と同型)。既存
  `test_algorithm_recommendation_service.py` を無改造のまま再実行することが、進行のルール
  #12.4 の「リファクタの写経ミス検知スモーク」に当たる。
- **「他の候補との違い」は registry を引き直さない**── `ALGORITHM_DESCRIPTIONS` のキー
  (`(problem_type, name)`)を `problem_type` でフィルタするだけで、採用アルゴリズム以外の説明文が揃う。追加の計算コストゼロ。
- **LLM 呼び出しの失敗は例外にしない**(Phase 12 と同じグレースフルデグレード)。ただし推薦と違い、説明は「ナラティブそのものが価値」の機能のため、フォールバックはmetrics/violations から直接組み立てた機械的な要約にする(Phase 12 の「ルールのみで返す」
  に対応)。`logger.warning` は必ず残す(Phase 11-8 の教訓)。
- **UI 側は「永続化つき solve → explain」の2段階**── 各 Planner Panel の「解く」は
  `persist: false`(探索的な試行を DB に残さない既存方針、Phase 4 以来無変更)のため、説明カードは押下時に専用の `persistSolve`(`persist: true`)を呼んでから `explain` する。
  既存の「解く」ボタンの挙動には一切触れない。

検証: backend `uv run pytest` 602 passed(新規 14 ── catalog 3 / schema 2 / service 5 /
api 3、既存 Phase 12 テスト無改造で再実行して回帰なしを確認)、`ruff check` / `ruff format --check` / `uvx pyright` いずれも 0 件(`app/services/errors.py` の pre-existing 債務はsamples の対象外)。ui `npx tsc --noEmit` clean、`npx vitest run` 77 passed(既存回帰なし)、`npx eslint` 0 件。`alembic upgrade head` は no-op(新テーブル無し)。

## 9. Phase 13 の成果物

- `textbook/Phase-13/`(導入 + 4 章)
- `textbook/samples/app/domain/problems/algorithm_catalog.py`・`app/schemas/explanation.py`・
  `app/services/explanation.py`・`app/services/algorithm_recommendation.py`(改訂)・
  `app/api/routes/solutions.py`(改訂)・`app/core/config.py`(改訂)・
  `tests/unit/test_algorithm_catalog.py`・`tests/unit/test_explanation_schemas.py`・
  `tests/unit/test_explanation_service.py`・`tests/api/test_explanation_api.py`
- `textbook/samples/ui/src/lib/api/types.ts`(改訂)・
  `ui/src/features/optimization/{api,stores,hooks,components}` の新規 5 ファイル・
  6 つの既存 Planner Panel(改訂)
- `CLAUDE.md`「### 設計判断・検証知見」に Phase 13 の要約 + Phase 12 への遡及記録
- `textbook/q_a.md` Q62(キックオフ確認)

## 10. 次のフェーズ

Phase 13 で「結果を説明する」までが揃った。次の Phase 14(LLM vs Algorithm Comparison)はLLM 単独と「LLM → Validation → Algorithm → Verification」パイプラインを同じ問題で実測比較する
── README「プロジェクトの核心的な検証テーマ」。評価軸は制約遵守率・最適性・再現性・実行時間・エラー率・検証可能性。Phase 13 の `SolutionExplanationService` がそのまま「比較結果の説明文生成」に応用できる土台になる(Phase 10 introduction §後述の Simulation と同じ関係)。
