# Phase 11 — LLM Problem Structuring(実装フェーズ)導入

作業章(`Phase-11-1.md` 以降)を始める前に、この 1 本で Phase 11 の全体像を掴む。
目的 / パイプライン上の位置 / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト /
次のフェーズ。

> **Phase 11 は MVP(Phase 0〜6)完了後、What-if Simulation(Phase 10)に続く 5 つ目の拡張フェーズであり、README §19「Phase 順序の原則」で言う「LLM はここで初めて登場する」その当のフェーズ**。README §20「LLM Problem Structuring」──「自然言語を問題定義へ変換する。
> Natural Language → LLM → Structured Problem → Validation。LLM はここで初めて登場する 
> ──決定論的エンジンが信頼できるようになって初めて前段に置く。
> LLM 出力は常に信頼しない
>  ──必ず Validation Layer を通す。既存の LangGraph 構造化出力パターンを流用する」。
> Phase 9/10 と同様、README の記述は実装方針(LLM プロバイダ・既存資産の扱い・対応ドメインの範囲・確認UIの要否)までは確定していない。開始にあたりユーザーに 4 点を確認し、以下の方針で進める(詳細は `textbook/q_a.md` Q59):
> 
> | 論点                                 | 決定                                                                                                                                                                           |
> | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | LLM プロバイダ                          | **既存の Gemini(`langchain_google_genai`)を継続**。切り替えない                                                                                                                           |
> | 既存チャット機能(Web検索QA、Tavily)           | **DeciTima 用に全面作り替え**。Web検索QA機能は廃止し、既存資産(GraphState/nodes/workflow の骨格、`Conversation`/`Message` モデル、`ChatService`/`ConversationRepository` の骨格、`FakeLLM` テストパターン)は土台として再利用する |
> | 対応 problem_type の範囲                | **6ドメイン全部**(route_planning/shift_scheduling/network_design/travel_planning/project_scheduling/logistics_planning)に最初から対応する                                                   |
> | Human-in-the-loop 確認UI(README §11) | **Phase 11 内で確認UIまで作る**(自然言語入力 → 確認カード → 確定 → 既存プランナーへ遷移)                                                                                                                    |

---

## 1. このフェーズの目的

README §3「LLM の役割」の核心テーゼ ──

> LLM は本システムの**計算エンジンではありません**。LLM に最適解を計算させない。LLM は「曖昧な要求の理解・構造化・説明」だけを担当し、経路探索・DP・スケジューリング・制約判定・数値最適化はすべて決定論的な Algorithm Engine が担当する。

Phase 0〜10 で「決定論的なアルゴリズム・検証エンジン」(6ドメインの `AlgorithmStrategy` +`ProblemValidationService` + `SolutionVerificationService`)を固め終えた今、Phase 11 で**初めて LLM が登場する**。パイプラインは:

```text
自然言語
  ↓
LLM(Gemini、Structured Output)
  ↓
Structured Problem(OptimizationProblem)
  ↓
Validation(既存 Phase 0〜9 の Semantic Validation + Phase 11 のグラウンディング検査)
```

**最大の設計論点 ── グラフ構造ドメインの非対称性**: `travel_planning`/`shift_scheduling` は自然言語1文から `objectives`/`constraints` に加えトップレベルのスカラー(予算・期間など)まで比較的直接抽出できるが、`route_planning`/`network_design`/`project_scheduling`/
`logistics_planning` は「ノード・エッジ・タスク」というカタログ構造そのものを1文の自然言語からLLM に発明させるのは非現実的(実際には既存の地図・タスク一覧が前提)。Phase 11 はこれを

> **LLM が埋めてよいのは objectives・constraints・data のトップレベル・スカラー/辞書フィールドまで。カタログ(list)フィールドは常に既存の「ベース問題」から引き継ぐ**

という1つの原則で6ドメイン共通に扱う(質的な二分法ではなく、埋められるフィールド数のグラデーション)。機構は Phase 10 で作った `apply_overrides`(RFC 7386 JSON Merge Patch +Pydantic 再検証)を**第二の消費者**として再利用する。

| すでに完成しているもの                                                                             | いつ                               |
| --------------------------------------------------------------------------------------- | -------------------------------- |
| 6 ドメインの `OptimizationProblem` / `select_strategy` / Validation / Verification           | Phase 1〜9                        |
| `apply_overrides`(汎用 dict マージ + Pydantic 再検証)                                           | Phase 10                         |
| Gemini クライアント(`app/ai/llm/gemini.py`)/ Structured Output パターン(`with_structured_output`) | テンプレート由来(Phase 0〜10 は route 無効化) |
| `Conversation`/`Message` モデル・`ConversationRepository`                                   | テンプレート由来(Phase 0〜10 は実消費者なし)     |

Phase 11 で新しく入るもの:

| 新規                                                               | 中身                                                                                                                                                                                                 |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **抽出・分類スキーマ**                                                    | `ProblemTypeClassification` / `ObjectivesConstraintsExtraction` / ドメイン別 `*DataPatch` (`app/schemas/structuring.py`)                                                                                |
| **ベース問題**                                                        | problem_type ごとの「既存問題」(`app/domain/problems/base_problems.py`)。カタログの引き継ぎ元                                                                                                                                  |
| **`EXTRACTORS` レジストリ / `build_overrides` / `ground_references`** | ドメイン別ディスパッチ・overrides 組み立て・グラウンディング検査(`app/services/structuring.py`)                                                                                                                               |
| **Structuring ワークフロー**                                           | `classify_problem_type → load_base_problem → extract_objectives_constraints → extract_domain_data → assemble_problem → validate_problem` の一直線パイプライン(`app/ai/graph/{state,nodes,workflow}.py`、全面書換) |
| **`ProblemStructuringService`**                                  | 会話記録・レート制限・リトライを取りまとめるサービス(`app/services/structuring.py`)。旧 `ChatService` を置き換える                                                                                                                   |
| **`POST /api/v1/structure`**                                     | 自然言語 → `OptimizationProblem`。返る `problem` はそのまま `POST /api/v1/solve` に渡せる                                                                                                                          |
| **Structuring ページ**(decitima-ui)                                 | `src/features/structuring/`。自然言語入力 → 確認カード → 確定 → 既存プランナーへ遷移(共有 `pending-problem-store`)                                                                                                           |

---

## 2. パイプライン上の位置 ── 既存の6ドメインには一切触れない

```text
POST /api/v1/structure   { text: "5万円以内で東京を2日間旅行したい。浅草には必ず行きたい。" }
      ▼
ProblemStructuringService.structure()
      ├ (a) レート制限(resource="structure")
      ├ (b) 会話取得/作成(Conversation/Message、初めての実消費者)
      └ (c) Structuring ワークフローを呼ぶ
             ▼
      classify_problem_type       LLM(Gemini、Structured Output)。problem_type を分類
             ▼
      load_base_problem           純粋。ベース問題を複製(カタログの引き継ぎ元)
             ▼
      extract_objectives_constraints   LLM。objectives/constraints をドメイン非依存の1スキーマで抽出
             ▼
      extract_domain_data         LLM(EXTRACTORS レジストリでディスパッチ)。data のトップレベル・
                                   スカラーだけ抽出(network_design は LLM を呼ばない)
             ▼
      assemble_problem            純粋。overrides を組み立て apply_overrides(Phase 10)でマージ
             ▼
      validate_problem            既存 Semantic Validation + グラウンディング検査(新設)
      ▼
POST /api/v1/solve へそのまま渡せる OptimizationProblem
```

**friction は最小**(すべて増分): 新規スキーマ 1 ファイル / 新規ドメインファイル 1 つ(ベース問題)
/ 新規サービス機構 1 ファイル / `app/ai/` の全面書換(1 セット)/ `POST /structure` 1 本。
route/network/shift/travel/project/logistics の**ドメインスキーマ・アルゴリズム・Validation本体には一切触れない**(既存の `RouteData`/`TravelData`/…/`ProblemValidationService` は無改造)。

**既存資産の全面作り替えが 1 件だけ発生する**: テンプレート由来の `app/ai/`(Gemini + LangGraph

+ Tavily の Web検索QAチャットワークフロー)は Phase 11 のキックオフ決定により DeciTima 用に
  全面書き換える。`app/ai/tools/tavily.py`・`app/services/chat.py`・`app/api/routes/chat.py`・
  `app/schemas/generation.py` は削除、`Conversation`/`Message` モデル・`ConversationRepository`
  は無改造のまま初めて実消費者を得る(既存マイグレーションのまま、新規マイグレーション不要)。

---

## 3. 章一覧(章 = 作業単位)

`Phase-11-M.md` = 作業単位 11-M。11-1 → 11-2 → 11-3 → 11-4 → 11-5 → 11-6 → 11-7 は鎖、11-8(UI)は 11-7 に依存、11-9(UI 配線)は 11-8 に依存する。

| 章                             | トピック                                                               | 依存                | 主な内容                                                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------ | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-11-1](./Phase-11-1.md) | 抽出・分類スキーマ(純粋 Pydantic)                                             | Phase 0〜10 の全ドメイン | `app/schemas/structuring.py`(`ProblemTypeClassification`/`ExtractedObjective`/`ExtractedConstraint`/`ObjectivesConstraintsExtraction`/6ドメインの `*DataPatch`/`StructuringRequest`/`StructuringResponse`)                                  |
| [Phase-11-2](./Phase-11-2.md) | ベース問題 + `EXTRACTORS`/`build_overrides`/`ground_references`         | 11-1              | `app/domain/problems/base_problems.py`(新規)/ `app/services/structuring.py`(この章の分だけ)                                                                                                                                                             |
| [Phase-11-3](./Phase-11-3.md) | `GraphState` 再設計 + `classify_problem_type`/`load_base_problem` ノード | 11-2              | `app/ai/graph/{state,nodes}.py`(全面書換、旧6関数削除)/ `tests/fixtures/fake_llm.py`(新規、切り出し)/ 削除: `app/ai/tools/tavily.py`・`app/schemas/generation.py`                                                                                          |
| [Phase-11-4](./Phase-11-4.md) | `extract_objectives_constraints` ノード + `catalog_entries`           | 11-3              | `app/ai/graph/nodes.py`(追記)/ `app/services/structuring.py`(`catalog_entries` 追記)                                                                                                                                                       |
| [Phase-11-5](./Phase-11-5.md) | `extract_domain_data` ノード(ドメイン別ディスパッチ)                             | 11-2, 11-4        | `app/ai/graph/nodes.py`(追記)                                                                                                                                                                                                            |
| [Phase-11-6](./Phase-11-6.md) | `assemble_problem`/`validate_problem` ノード + ワークフロー組み立て             | 11-1〜11-5         | `app/ai/graph/nodes.py`(追記)/ `app/ai/graph/workflow.py`(全面書換)                                                                                                                                                                          |
| [Phase-11-7](./Phase-11-7.md) | サービス層 + API層(既存 ChatService/chat.py の置換)                           | 11-6              | `app/services/structuring.py`(`ProblemStructuringService` 追記、完成)/ `app/api/routes/structure.py`(新規)/ `app/api/routes/__init__.py`・`app/core/config.py`・`app/schemas/chat.py`(現行版)/ 削除: `app/services/chat.py`・`app/api/routes/chat.py` |
| [Phase-11-8](./Phase-11-8.md) | UI: 自然言語入力 + 確認カード + 確定用共有ストア                                      | 11-7              | `ui/src/features/structuring/**`(新規)/ `ui/src/features/optimization/stores/pending-problem-store.ts`・`hooks/usePendingProblemHydration.ts`(新規、共有)/ `lib/api/types.ts`・`lib/menu-tree.ts`(現行版)                                          |
| [Phase-11-9](./Phase-11-9.md) | UI: 6ドメインページへの確定連携配線                                               | 11-8              | 6プランナーの Panel コンポーネント(現行版、各1行)                                                                                                                                                                                                         |

11-1〜11-7 が decitima-api、11-8〜11-9 が decitima-ui。順序の理由: **型を固める(スキーマ)→カタログの引き継ぎ元(ベース問題)+ ドメイン非依存の機構 → ワークフローをノード単位で積む(分類 → 抽出 → 抽出 → 組み立て/検証)→ サービス・API 配線 → UI**。各章は「その章までのファイルで import 解決」(進行のルール #15)。

---

## 4. この Phase の進め方 ── 実装 = 写経(Phase 1〜10 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-11-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 11 end 状態、実 `app/` `src/` ツリー鏡写し +
   絶対 import)。
2. `textbook/samples/{app,tests}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。この Phase の写経対象は §8 の一覧(冒頭系譜コメントに `Phase 11` を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。`app/ai/{state,nodes,workflow}.py` は旧6関数を全廃した全面書換なので、**既存の実装を丸ごと置き換える**(他 Phase の「旧コードをコメントアウト+タグ付き追記」ではなく、テンプレート由来コードそのものが不要になるため)。
   `app/ai/tools/tavily.py`・`app/services/chat.py`・`app/api/routes/chat.py`・
   `app/schemas/generation.py` は**削除する**(rsync ベースの overlay では消えないため、`textbook/samples/README.md` に一時的な `rm` 手順を追記済み。写経先の実リポジトリでも同じ4ファイルを削除する)。それ以外の更新ファイル(`app/api/routes/__init__.py`・`app/core/config.py`・`app/schemas/chat.py`)は変更行が `# (Phase 11-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12。grep 合言葉: `grep -rn "# (Phase 11" textbook/samples`)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §7 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 5. テストの階層

| レベル         | 使うもの                                      | Phase 11 で書くもの                                                                                       |
| ----------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| スキーマ(純粋)    | 素の pytest                                 | `app/schemas/structuring.py` の型定義(11-1)                                                              |
| ドメイン機構(純粋)  | 素の pytest                                 | ベース問題・`EXTRACTORS`/`build_overrides`/`catalog_ids`/`catalog_entries`/`ground_references`(11-2, 11-4) |
| LLM 呼び出しノード | `FakeLLM`(`with_structured_output` をスタブ化) | `classify_problem_type`/`extract_objectives_constraints`/`extract_domain_data`(11-3〜11-5)            |
| ワークフロー合成    | `FakeLLM` を複数箇所に差し込み                      | `build_structuring_workflow().ainvoke(...)`(11-6、初めての end-to-end)                                    |
| サービス層       | `db_session` + `FakeRedis` + フェイクワークフロー   | `ProblemStructuringService.structure`(11-7)                                                          |
| API 契約      | `api` フィクスチャ(FakeRedis + インメモリ SQLite)    | `POST /api/v1/structure`(11-7)                                                                       |
| UI ストア      | Vitest(node env)、`vi.mock` で API 層をモック    | `structuring-store`/`pending-problem-store`(11-8)                                                    |
| UI フック      | Vitest(jsdom env)、`renderHook`            | `usePendingProblemHydration`(11-8)                                                                   |

**スタブの要否がレイヤー設計の鏡になる好例(#14)**: `extract_domain_data` は同じ関数でも
ドメインによってスタブの要否が変わる ── `network_design` は `EXTRACTORS` に該当スキーマが
無いため LLM を**呼ばない**、これ自体がテスト対象になり、そのケースだけスタブ不要。

```bash
# decitima-api/backend(overlay end 状態 = Phase 10 end + Phase 11 samples)で
uv run pytest
# decitima-ui で
npx vitest run src/features/structuring src/features/optimization/stores src/features/optimization/hooks
```

---

## 6. Phase 11 のスコープと非スコープ

| Phase 11 でやる                                                  | 送る先                                                                                                                    |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 自然言語 → `problem_type` 分類 + objectives/constraints 抽出(6ドメイン共通) | ―                                                                                                                      |
| data のトップレベル・スカラー抽出(ドメインごとに 0〜4 フィールド)                        | ―                                                                                                                      |
| ベース問題 + `apply_overrides` によるカタログの引き継ぎ                        | ―                                                                                                                      |
| グラウンディング検査(id 参照のハルシネーション検知)                                  | ―                                                                                                                      |
| `POST /api/v1/structure` + 確認UI(README §11 Human-in-the-loop) | ―                                                                                                                      |
| ―                                                             | **アルゴリズム推薦**(Rule Engine + LLM でアルゴリズム候補を出す)── README §9/§12「Algorithm Recommendation」は Phase 12                       |
| ―                                                             | **結果説明**(solve 結果を自然言語で説明する)── README §13「Result Explanation」は Phase 13                                                |
| ―                                                             | **カタログそのものの生成/編集**(ノード追加・エッジ追加を LLM にやらせる)── ベース問題に無い地点への言及は確認カード上で「認識できませんでした」として提示するに留め、追加は既存プランナー UI(JSON エディタ)で人間が行う |
| ―                                                             | **複数テンプレートからの自動選択**(problem_type 内で複数ベース問題を持ち LLM に選ばせる)── ベース問題は problem_type ごとに1件のみ。将来必要になれば Phase 12「候補から選ぶ」機構との親和性が高い |

---

## 7. Phase 11 実装前チェックリスト

進行のルール #11。行 `11-M` ↔ 章 `Phase-11-M`。

| #    | 作る / 変えるファイル                                                                                                                                                                                                                                                                                                       | 主なクラス・関数の責務(1 行)                                                                                                                                                                                              |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11-1 | `app/schemas/structuring.py`(新規)、`tests/unit/test_structuring_schemas.py`(新規)                                                                                                                                                                                                                                      | `ProblemTypeClassification`/`ExtractedObjective`/`ExtractedConstraint`/`ObjectivesConstraintsExtraction`(抽出スキーマ)/ `RouteDataPatch`等5クラス(ドメイン別 data パッチ)/ `StructuringRequest`/`StructuringResponse`(API スキーマ) |
| 11-2 | `app/domain/problems/base_problems.py`(新規)、`app/services/structuring.py`(新規、この章の分だけ)、`tests/unit/test_structuring_base_problems.py`・`tests/unit/test_structuring_overrides.py`(新規)                                                                                                                                                 | `BASE_PROBLEMS`/`get_base_problem`(6ドメインのベース問題)/ `EXTRACTORS`(problem_type→パッチスキーマのレジストリ)/ `build_overrides`(抽出結果→overrides dict)/ `catalog_ids`/`ground_references`(グラウンディング検査)                                |
| 11-3 | `app/ai/graph/state.py`・`app/ai/graph/nodes.py`(全面書換)、`tests/fixtures/fake_llm.py`(新規)、`tests/unit/test_ai_graph_nodes.py`(全面書換)、削除: `app/ai/tools/tavily.py`・`app/schemas/generation.py`                                                                                                                          | `GraphState`(再設計、8フィールド)/ `classify_problem_type`(LLM分類)/ `load_base_problem`(純粋、ベース問題読み込み)/ `FakeLLM`(スキーマ記録機能付き)                                                                                              |
| 11-4 | `app/ai/graph/nodes.py`(追記)、`app/services/structuring.py`(`catalog_entries` 追記)                                                                                                                                                                                                                                    | `extract_objectives_constraints`(LLM抽出)/ `_objectives_prompt`/ `catalog_entries`(id,name ペアの一覧、プロンプト用)                                                                                                        |
| 11-5 | `app/ai/graph/nodes.py`(追記)                                                                                                                                                                                                                                                                                        | `extract_domain_data`(`EXTRACTORS` ディスパッチ)/ `_data_prompt`                                                                                                                                                    |
| 11-6 | `app/ai/graph/nodes.py`(追記)、`app/ai/graph/workflow.py`(全面書換)、`tests/unit/test_structuring_workflow.py`(新規)                                                                                                                                                                                                         | `assemble_problem`(overrides組み立て+マージ)/ `validate_problem`(Validation+グラウンディング)/ `build_structuring_workflow`/`get_structuring_workflow`                                                                       |
| 11-7 | `app/services/structuring.py`(`ProblemStructuringService` 追記、完成)、`app/api/routes/structure.py`(新規)、`app/api/routes/__init__.py`・`app/core/config.py`・`app/schemas/chat.py`(現行版)、`tests/unit/test_structuring_service.py`・`tests/api/test_structure_api.py`(新規)、削除: `app/services/chat.py`・`app/api/routes/chat.py` | `ProblemStructuringService`(会話記録・レート制限・リトライ)/ `POST /api/v1/structure`                                                                                                                                        |
| 11-8 | `ui/src/features/structuring/**`(新規)、`ui/src/features/optimization/stores/pending-problem-store.ts`・`hooks/usePendingProblemHydration.ts`(新規、共有)、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)、テスト一式                                                                                                                  | `submitStructuring`/`useStructuringStore`/`useStructuring`/`NaturalLanguageInputForm`/`StructuredProblemCard`/`domainSummaries.ts`/ `usePendingProblemStore`/`usePendingProblemHydration`                     |
| 11-9 | 6プランナーの Panel コンポーネント(現行版、各1行)                                                                                                                                                                                                                                                                                     | `usePendingProblemHydration(problemType, setProblem)` の呼び出しを1行追加                                                                                                                                              |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)(Phase 11 end 状態)。各ファイル
冒頭の `# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は §7 の実装前チェック
リスト参照。overlay 検証手順は [`textbook/samples/README.md`](../samples/README.md)。

要点:

- **グラフ構造ドメインの非対称性は「ベース問題 + apply_overrides」で一元的に解決する** ──
  ドメインごとに実装方針を変えるのではなく、6ドメイン共通の1つの機構(LLM は
  objectives/constraints/data のトップレベルだけ、カタログはベース問題から)に落とす。
  `EXTRACTORS` に該当スキーマが無いドメイン(`network_design`)は自然に LLM 呼び出しがスキップされる ── レジストリ駆動設計の良い副産物。
- **グラウンディング検査(`ground_references`)は既存 Validation の穴を塞ぐ新設機構** ──
  `ProblemValidationService` は `RequiredInclusionConstraint.items` 等の id 参照がカタログに実在するかを検査しない(到達可能性等の計算にしか使わない)。LLM が名前(「浅草」)を id の代わりに出力してしまうと、downstream(`solution_element_ids`)は
  id で突き合わせるため黙って無視される ── これを検知する最後の砦。新しい例外クラスは増やさず既存 `ProblemValidationError` を再利用する。
- **循環 import に注意**: `app/ai/graph/nodes.py` は `app/services/structuring.py` の`EXTRACTORS`/`catalog_entries`/`catalog_ids`/`ground_references` を import し、`app/services/structuring.py::ProblemStructuringService` は
  `app/ai/graph/workflow.py::get_structuring_workflow` を呼ぶ。モジュール先頭で互いに import すると循環するため、`get_structuring_workflow` の import は
  `ProblemStructuringService.structure()` 内の関数内 import にして輪を断つ。
- **`with_structured_output()` の戻り型は `dict | BaseModel`**(langchain の型定義がそこまで絞り込めない)。`cast(SpecificSchema, llm.invoke(...))` で明示的に narrowing する(テンプレート由来コードが `app/ai` を pyright ignore していた理由の1つ。Phase 11 でignore を解消する)。
- UI は新しい solve ビューアを作らず、既存の6ドメインページ(Phase 4〜9)を再利用する。確定(README §11「この条件で最適化する」)は共有 `pending-problem-store` に問題を置いて該当ページへ `router.push` するだけ ── 各ページ側は `usePendingProblemHydration` を1行呼ぶだけで受け取る(`useJobPolling` と同じ「problem_type に依存しない共通フック」の設計方針)。

検証: Phase 10 end 状態に Phase 11 samples を overlay し `uv run pytest`(576 passed / 6
deselected)/ `ruff` / `uvx pyright app tests`(0 errors、`app/ai` と
`test_ai_graph_nodes.py` を pyright ignore リストから削除)。`alembic upgrade head` はno-op(新テーブルなし)。decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(64 passed)/ `npx eslint`。

---

## 9. Phase 11 の成果物

- **textbook**: この `Phase-11/` 一式(導入 + `Phase-11-1`〜`11-9` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/schemas/structuring.py`・
  `app/domain/problems/base_problems.py`・`app/services/structuring.py`・
  `app/ai/graph/{state,nodes,workflow}.py`(全面書換)・`app/api/routes/structure.py`(新規)/
  `app/api/routes/__init__.py`・`app/core/config.py`・`app/schemas/chat.py`(現行版)/
  `tests/**`。削除: `app/ai/tools/tavily.py`・`app/services/chat.py`・
  `app/api/routes/chat.py`・`app/schemas/generation.py`
- **decitima-ui の実装**(ユーザーが写経): `src/features/structuring/**` /
  `src/features/optimization/stores/pending-problem-store.ts`・
  `src/features/optimization/hooks/usePendingProblemHydration.ts` /
  `src/app/(pages)/optimization/structuring/page.tsx` /
  `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)/ 6プランナー Panel(現行版、各1行)
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 11 要点**(経緯は `textbook/q_a.md` Q59)
- **`Phase-10-introduction.md`「次のフェーズ」への1行追記**(`apply_overrides` の第二消費者)
- **`textbook/samples/README.md` の「最終検証」スタンプ**を Phase 11 に更新

---

## 10. 次のフェーズ

Phase 11 完了で、README パイプライン図の最初の矢印(自然言語 → LLM → Structured Problem →Validation)が実装される。LLM は「理解・構造化」だけを担当し、実際の計算(Algorithm Engine)とは `OptimizationProblem` というスキーマ経由でのみ繋がる ── README の核心テーゼ「LLM に最適解を計算させない」を体現した実装になる。

その先は README §20 の拡張順 ── **Phase 12(Algorithm Recommendation。Rule Engine + LLM でアルゴリズム候補を推薦する。Phase 0 で設計した3段階セレクションの「第2段」)→ Phase 13(Result Explanation。solve 結果を自然言語で説明する。Phase 11 の `ProblemStructuringService`の会話記録パターン、Phase 10 の `SimulationResult` が「シナリオ比較の説明文生成」に応用できる
土台になる)→ Phase 14(LLM vs Algorithm Benchmark)→ Phase 15(Production)**。

---

## 11. 後続 Phase での改訂

- **Phase 15-2**: `app/services/algorithm_selection.py::_MAX_KNAPSACK_DP_CELLS`(Phase 11-9で
  導入した travel_planning の knapsack_dp 規模ガード)を実測に基づき 2,000,000 → 4,000,000 に
  緩和した。実測の過程で、このガードが実際には `POST /solve` の既定選択だけを保護し、
  `POST /benchmark`(`get_strategies` で全候補を回すため対象外)は保護していなかったことが
  判明 ── Phase 11-9 のコメントの前提誤りを Phase 15 で修正した。Phase 11-9 の実インシデント
  規模(budget=100,000, n=5, time_budget=16 → cells=8,000,000)は新閾値でも引き続きガード
  される(詳細 `Phase-15-2.md`)。
