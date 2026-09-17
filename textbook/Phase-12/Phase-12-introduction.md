# Phase 12 — Algorithm Recommendation(実装フェーズ)導入

作業章(`Phase-12-1.md` 以降)を始める前に、この 1 本で Phase 12 の全体像を掴む。
目的 / パイプライン上の位置 / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト /
次のフェーズ。

> README §9「Algorithm Selection」・§12「Algorithm Recommendation」で計画された、3 段階アルゴリズム選択の「第 2 段(LLM 推薦)」を実装するフェーズ。
> 第 1 段(ルールベース、`services/algorithm_selection.py::select_strategy`)はPhase 4〜9 で完成済み。第 3 段(ベンチマーク実測ベースの自動選択)は未着手のまま将来課題として残す(`benchmark_runs` は現状「記録するだけ」で、選択には使われない)。
> 
> キックオフ確認(3 点、詳細 `q_a.md` Q61):
> 
> | 論点      | 決定                                                  |
> | ------- | --------------------------------------------------- |
> | 出力形状    | 候補リスト + 理由を返す**新エンドポイント**(既存 `/solve` の既定選択には影響しない) |
> | 発火タイミング | **明示的な opt-in アクション**(自動では呼ばない)                     |
> | 対象ドメイン  | Phase 11 と同様、**最初から 6 ドメイン全部**                      |

## 1. このフェーズの目的

README §9 はアルゴリズム選択を 3 段階で高度化する計画を掲げている:

```text
Step 1 (Phase 4〜9 完成済み)   Step 2 (このPhase)              Step 3 (未着手)
問題特性 → ルールで1つ選ぶ     Rule Engine + LLM → 候補リスト   実測データから選ぶ
```

**最大の設計論点**: README §3.2 は「アルゴリズムの最終決定を LLM だけに依存しない」と
明記している。したがって Phase 12 のゴールは「LLM に決めさせる」ことではなく、
**候補と理由を提示し、最終決定は呼び出し側(ユーザー、または将来の自動化)に委ねる**こと。
既存の `/solve` の既定選択(`select_strategy`)は一切変更しない ── Phase 12 は完全に
追加的(additive)なレイヤーとして載る。

すでに完成しているもの / いつ:

| 資産                                                          | 由来        | Phase 12 での役割                              |
| ----------------------------------------------------------- | --------- | ------------------------------------------ |
| `select_strategy`/`get_strategies`(rule-based 選択)           | Phase 4〜9 | 「ルールの既定」として無変更で再利用(第二の消費者)                 |
| `AlgorithmMeta`(name/family/implementation/time_complexity) | Phase 0〜9 | 候補の説明に転記する                                 |
| `get_gemini_llm(...).with_structured_output(Schema)`        | Phase 11  | LLM 推薦の構造化出力に再利用                           |
| `_PROBLEM_TYPE_DESCRIPTIONS` 型の「problem_type → 説明」表         | Phase 11  | `_ALGORITHM_DESCRIPTIONS`(候補 → 説明)として同型で新設 |
| grounding(「LLM 出力は常に信頼しない」)                                 | Phase 11  | 存在しない候補名を黙って無視する形で踏襲                       |

新規 / 中身:

| 資産                                                               | 中身                                                                                                         |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `app/schemas/recommendation.py`                                  | API 契約(`RecommendRequest`/`RecommendationResponse`/`AlgorithmRecommendation`)+ LLM 契約(`LlmRecommendation`) |
| `app/services/algorithm_recommendation.py`                       | `AlgorithmRecommendationService`。rule 呼び出し + LLM 呼び出し + grounding + マージ                                    |
| `POST /api/v1/algorithms/recommend`                              | 既存 `routes/algorithms.py` に追加(新ファイルは作らない)                                                                  |
| UI: `features/optimization/{api,stores,hooks,components}` の推薦カード | 6 ドメイン共通、既存 6 panel に導線を追加                                                                                 |

## 2. パイプライン上の位置 ── 完全に追加的なレイヤー

```text
(既存、無変更)
ユーザー → /structure(Phase 11) → OptimizationProblem → /solve(select_strategy) → CandidateSolution

(Phase 12 で追加。/solve の前後どちらでも呼べる、呼ばなくてもよい)
OptimizationProblem → POST /algorithms/recommend
                         ├─ Rule Engine: select_strategy(既存、無変更) ─┐
                         └─ LLM: get_gemini_llm().with_structured_output ┴→ 候補リスト+理由
                       → ユーザーが確認 → (必要なら) ?algorithm=<name> を /solve に明示指定
```

- 摩擦は最小: `select_strategy`/`get_strategies`/`AlgorithmMeta` は 1 行も変えない。
  `/solve`/`/benchmark` のホットパスにも触れない。
- 完全新規: `app/schemas/recommendation.py`・`app/services/algorithm_recommendation.py`・
  UI の推薦カード一式。
- LangGraph は使わない(Phase 11 との違い)。rule 計算 1 回 + LLM 呼び出し高々 1 回の単純な流れのため、素の async 関数で十分(YAGNI。Phase 9/10 の `SimulationService`/
  `BenchmarkService` と同じ判断)。

## 3. 章一覧(章 = 作業単位)

12-1 → 12-2 → 12-3 は鎖(スキーマ → サービス → ルート)。12-4(UI)は 12-3 に依存する。

| 章                             | トピック                             | 依存          | 主な内容                                                                         |
| ----------------------------- | -------------------------------- | ----------- | ---------------------------------------------------------------------------- |
| [Phase-12-1](./Phase-12-1.md) | スキーマ + 静的説明表                     | Phase 11 まで | `app/schemas/recommendation.py`(新規)。`_ALGORITHM_DESCRIPTIONS`(全 24 strategy) |
| [Phase-12-2](./Phase-12-2.md) | `AlgorithmRecommendationService` | 12-1        | rule 再利用・LLM 呼び出し・grounding・レート制限・失敗時のフォールバック                                |
| [Phase-12-3](./Phase-12-3.md) | ルート配線 + e2e                      | 12-2        | `POST /api/v1/algorithms/recommend`(既存 `routes/algorithms.py` に追加)                |
| [Phase-12-4](./Phase-12-4.md) | UI(推薦カード)                        | 12-3        | `features/optimization/{api,stores,hooks,components}` + 6 panel への導線         |

## 4. この Phase の進め方 ── 実装 = 写経(Phase 1〜11 と同じ)

1. Claude が教材(この導入 + 4 章)とサンプル(`textbook/samples/`)を書く。実コードは
   書かない ── 実装は `decitima-api`/`decitima-ui` にユーザーが写経する。
2. 各章は「この章で作成/更新するファイル」を明記し、責務 1 行 + 非自明な判断を解説する。
3. 章を読み終えたら該当ファイルを写経し、章末のテストを実行して緑を確認してから次の章へ。
4. samples のフル検証は共有 `textbook/samples/` を 1 回 overlay して回す
   (`textbook/samples/README.md`)。今回は backend 510 passed(Phase 11 end の 498 + Phase 12
   新規 12 ── schema 4 / service 6 / api 2)、ui vitest 新規 5 passed(既存 164 は無回帰。
   `Menu.test.tsx` の 1 件失敗は Phase 12 と無関係の既存事象 ── クリーンな decitima-ui HEAD
   単体でも同じく失敗する)。

## 5. テストの階層

| レベル           | 使うもの                                                              | Phase 12 で書くもの                                                                     |
| ------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| スキーマ(純粋)      | 素の pytest                                                         | `test_recommendation_schemas.py`(12-1、型定義の確認) |
| サービス(unit)    | `FakeLLM`(Phase 11-3 で新設、Phase 12 で `ainvoke` 対応を追加)+ `FakeRedis` | `test_algorithm_recommendation_service.py`(rule/LLM マージ・grounding・レート制限・失敗フォールバック) |
| API(e2e)      | `api` fixture(認証込み client)                                        | `test_algorithm_recommendation_api.py`(配線確認 + 既存 `GET /algorithms` の回帰)            |
| UI store/hook | vitest + `vi.mock`                                                | `recommendation-store.test.ts`・`recommend.test.ts`(API 層)                          |

**用語**(初出、以降の章は関係の明記のみ): **SUT**(テスト対象)/ **ドライバ**(テストを
実行するもの)/ **スタブ**(外部依存の代役)。`select_strategy`/`get_strategies` は
純粋(DB 非依存)なのでスタブ不要 ── レイヤー設計の鏡(#14)。

`FakeLLM`(`tests/fixtures/fake_llm.py`)は Phase 11-3 の資産だが、Phase 12 は LangGraph を介さない素の async 関数のため `llm.ainvoke(...)` を直接呼ぶ。既存の同期 `invoke` に加えて`ainvoke` を両クラスに追加した(第二の消費者、後方互換の追加)。

```bash
# decitima-api/backend で
uv run pytest tests/unit/test_recommendation_schemas.py tests/unit/test_algorithm_recommendation_service.py tests/api/test_algorithm_recommendation_api.py

# decitima-ui で
npx vitest run src/features/optimization/api/recommend.test.ts src/features/optimization/stores/recommendation-store.test.ts
```

## 6. Phase 12 のスコープと非スコープ

| Phase 12 でやる                             | 送る先 |
| ---------------------------------------- | --- |
| Rule Engine + LLM の候補リスト + 理由を返す新エンドポイント | ―   |
| 6 ドメイン全部の静的アルゴリズム説明表                     | ―   |
| grounding(存在しない候補名は黙って無視)                | ―   |
| LLM 失敗時のルールのみへのグレースフルデグレード               | ―   |

- **`/solve`/`/benchmark` の既定選択の変更**(rule を LLM で上書きする等)── README
  「LLM 単独では最終決定しない」に反するため**恒久的に非スコープ**。
- **ベンチマーク実測データに基づく自動選択**(README §9 Step 3)── `benchmark_runs` の読み出し側が存在しない。将来の独立した検討課題(着手時期未定)。
- **アルゴリズムの結果の説明**(なぜこの解になったか)── README §13「Result
  Explanation」は Phase 13。
- **候補アルゴリズムの新規追加**(registry への新 strategy 登録)── このフェーズでは
  行わない(既存 24 strategy の説明を書くだけ)。

## 7. Phase 12 実装前チェックリスト

進行のルール #11。行 `12-M` ↔ 章 `Phase-12-M`。

| #    | 作る / 変えるファイル | 主なクラス・関数の責務(1 行) |
| ---- | --- | --- |
| 12-1 | `app/schemas/recommendation.py`(新規)、`tests/unit/test_recommendation_schemas.py`(新規) | `RecommendRequest`/`RecommendationResponse`/`AlgorithmRecommendation`(API 契約)/ `LlmRecommendation`/`LlmAlgorithmComment`(LLM 契約) |
| 12-2 | `app/services/algorithm_recommendation.py`(新規)、`app/core/config.py`(改訂)、`tests/fixtures/fake_llm.py`(改訂)、`tests/unit/test_algorithm_recommendation_service.py`(新規) | `AlgorithmRecommendationService.recommend()`(rule再利用・LLM呼び出し・grounding・マージ・レート制限)/ `_ALGORITHM_DESCRIPTIONS`/`_describe`/`_build_recommendation`/`_recommend_prompt`(私設ヘルパ)/ `RECOMMEND_RATE_LIMIT_PER_HOUR`/`_PER_DAY`(設定フィールド追加)/ `FakeLLM`/`_FakeStructuredLLM` に `ainvoke` を追加(第二の消費者) |
| 12-3 | `app/api/routes/algorithms.py`(改訂)、`tests/api/test_algorithm_recommendation_api.py`(新規) | `recommend_algorithm()`(ルートハンドラ追加、既存 `list_algorithms` はそのまま) |
| 12-4 | `ui/src/lib/api/types.ts`(改訂)、`ui/.../api/recommend.ts`(新規)、`ui/.../stores/recommendation-store.ts`(新規)、`ui/.../hooks/useAlgorithmRecommendation.ts`(新規)、`ui/.../components/AlgorithmRecommendationCard.tsx`(新規)、6 つの既存 Planner Panel(改訂)、テスト一式(`recommend.test.ts`・`recommendation-store.test.ts`) | `AlgorithmRecommendation`/`RecommendationResponse`(型)/ `recommendAlgorithm`(POSTの薄いラッパ)/ `useRecommendationStore`(result/status/error/run/reset、`benchmark-store` と同型)/ `useAlgorithmRecommendation`(storeの薄いラッパ)/ `AlgorithmRecommendationCard`(推薦カードUI、6ドメイン共通)/ 各 Panel への導線1行 |

## 8. サンプルコード ── 共有 `textbook/samples/`

要点:

- **`meta.name` は problem_type をまたいで重複する**(例:`"greedy"` は shift/travel/
  logistics の 3 つの別実装が持つ、`"brute_force"` は route/travel/logistics で 3 つ)。
  `_ALGORITHM_DESCRIPTIONS` のキーは `(problem_type, name)` のタプルにする ── これを`name` 単体キーにすると異なる実装の説明が上書きし合う実バグになる(教材化前の設計検討で発見・修正した点)。
- **候補が 1 件だけなら LLM を呼ばない**(トークン節約)。現行 registry には該当 domain が無い(全 6 ドメインとも 3 件以上)が、将来 problem_type を追加した初期状態で起こり得るため機構として実装・テストする(フェイクで候補リストだけ差し替える。rule #15)。
- **LLM 呼び出しの失敗は例外にしない**(ルールのみの結果にグレースフルデグレードする)。ただし Phase 11-8 の教訓(例外を握りつぶすとログに何も残らない)を踏まえ、
  `logger.warning` は必ず残す。
- **LLM 呼び出しは `ainvoke`**(Phase 11 の LangGraph ノードは同期 `invoke` を
  `run_in_executor` 任せにしていたが、Phase 12 は LangGraph を介さないため自分で非同期呼び出しする。`Runnable` は全て `ainvoke` を持つ)。

検証: backend `uv run pytest` 510 passed(新規 10 unit(schema 4 + service 6)+ 2 api 含む)、`ruff check` /
`uvx pyright` 0 件。ui `npx vitest run` 新規 5 passed・既存 164 無回帰(`tsc --noEmit` /`eslint` 0 件)。`alembic upgrade head` は no-op(新テーブル無し)。

## 9. Phase 12 の成果物

- `textbook/Phase-12/`(導入 + 4 章)
- `textbook/samples/app/schemas/recommendation.py`・`app/services/algorithm_recommendation.py`・
  `app/api/routes/algorithms.py`(改訂)・`app/core/config.py`(改訂)・
  `tests/fixtures/fake_llm.py`(改訂)・`tests/unit/test_recommendation_schemas.py`・
  `tests/unit/test_algorithm_recommendation_service.py`・`tests/api/test_algorithm_recommendation_api.py`
- `textbook/samples/ui/src/lib/api/types.ts`(改訂)・
  `ui/src/features/optimization/{api,stores,hooks,components}` の新規 5 ファイル・
  6 つの既存 Planner Panel(改訂)
- `CLAUDE.md`「### 設計判断・検証知見」に Phase 12 の要約
- `textbook/q_a.md` Q61(キックオフ確認)

## 10. 次のフェーズ

Phase 12 で「候補を提示する」までが揃った。次の Phase 13(Result Explanation)は
「なぜこの解になったか」を LLM に説明させる ── `CandidateSolution.produced_by`(Phase 12 が説明した候補のうちどれが実際に選ばれ、solve されたか)+ `metrics`/`violations` を消費する。
Phase 0 で敷いた説明可能性(NFR-4)の土台がここで回収される。

## 11. 後続 Phase での改訂

- **Phase 13-1**: `_ALGORITHM_DESCRIPTIONS`/`_describe`(本 Phase では本ファイル内の非公開
  定数)を `app/domain/problems/algorithm_catalog.py` へ抽出し `ALGORITHM_DESCRIPTIONS`/
  `describe_algorithm`(公開)に改名した ── Phase 13 の Result Explanation が「他候補との
  違い」の比較材料として2人目の消費者になったため(進行のルール #17)。値は不変、
  `algorithm_recommendation.py` 側は import に置き換わっただけ。詳細 `Phase-13-1.md` §1〜2。
