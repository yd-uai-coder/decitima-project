# Phase 14 — LLM vs Algorithm Comparison(実装フェーズ)導入

作業章(`Phase-14-1.md` 以降)を始める前に、この 1 本で Phase 14 の全体像を掴む。
目的 / パイプライン上の位置 / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト / 次のフェーズ。

> README §14「LLM vs Algorithm Comparison」── LLM 層(Phase 11 構造化 → Phase 12 推薦 →Phase 13 説明 → **Phase 14 比較**)の最後、そして README が「プロジェクトの核心的な検証
> テーマ」と呼ぶフェーズ。同一問題を「LLM Only」と「LLM → Validation → Algorithm →Verification」の両方で解き、実測で比較する。
> 
> キックオフ確認(4 点、詳細 `q_a.md` Q63):
> 
> | 論点               | 決定                                                                                |
> | ---------------- | --------------------------------------------------------------------------------- |
> | 対象 problem_type  | **6ドメイン全部**(Phase 11/12 と同様)                                                      |
> | LLM Only の実装方式   | **`AlgorithmStrategy` 準拠ラッパー**(`meta.implementation="llm"`)。本番 `REGISTRY` には登録しない |
> | 比較する Algorithm 側 | **既定選択(`select_strategy`)の1本のみ**                                                  |
> | 再現性の測定 / 永続化     | **LLM を N 回再実行 + 結果は非永続**                                                         |

## 1. このフェーズの目的

README §14 はこのフェーズの目的を一言で定義する:

```text
LLM Only
```

と、

```text
LLM
 ↓
Validation
 ↓
Algorithm
 ↓
Verification
```

を比較する。

**評価軸(6 つ)**: 制約遵守率 / 最適性 / 再現性 / 実行時間 / エラー率 / 検証可能性。

**設計のポイント(README 原文)**:

> プロジェクトの核心的な検証テーマ。同一データで「LLM Only」と「LLM → Validation →Algorithm → Verification」パイプラインを比較する。示したいのは「AI を使う」ではなく
> **「AI と決定論的アルゴリズムをどう組み合わせるか」**。

## 2. この Phase の設計を単純化した発見 ── 「同じ検証コードで検証できる」

Phase 14 最大の設計論点は「LLM に直接解かせた出力を、どうやって Algorithm の出力と対等に比較するか」だった。既存コードを調査した結果、次の事実が見つかり、設計を大きく単純化できた:

`SolutionVerificationService`(Phase 1〜9)の構造検証(`app/domain/solutions/structure.py`)は、
6 ドメイン全てで**申告された派生値(total_weight / total_value / makespan /
total_distance)を生の構造から必ず再計算し、食い違えば hard violation にする**
(「strategy が嘘をついている」検出。例: `verify_route_structure` の
`total_weight != edge sum` チェック)。

これはもともと「手実装 Algorithm が自己申告する数値が正しいか」を検証するための仕組みだが、**LLM に既存の `RouteSolution`/`ShiftSolution`/…と全く同じ Pydantic スキーマを`with_structured_output()` で出力させれば、変換コードを一切書かずに同じ検証を通せる**。
これにより:

- 新しい「LLM 用の解スキーマ」は要らない(既存 6 スキーマをそのまま再利用)。
- LLM の出力と Algorithm の出力は**全く同じ検証コード**で判定される ── 比較が公平になる。
- 「検証可能性」という抽象的な評価軸を、「LLM の出力も同じ Verification に通せる」という
  具体的な事実で実演できる。

## 3. アーキテクチャ

### 3.1 `AlgorithmMeta.family` の拡張

`family: Literal["search","graph","optimization","scheduling","patterns"]` は
「`app/algorithms/` の5サブパッケージと1対1」という不変条件を持つ。LLM Only 戦略も同じ契約(`AlgorithmStrategy` Protocol)を満たす以上、この不変条件を破らずに位置づけるため、**6つ目のサブパッケージ `app/algorithms/llm/` を新設し、`family` に `"llm"` を追加**した
(Phase 1 `app/domain/solutions/solution.py` への遡及、進行のルール #12)。

### 3.2 `app/algorithms/llm/` ── `LlmOnly*Strategy`(ドメインごとに6本)

各戦略は `AlgorithmStrategy` Protocol を満たすだけの薄いクラス:

```python
class LlmOnlyRouteStrategy:
    meta = LLM_ONLY_META  # AlgorithmMeta(name="llm_only", family="llm", implementation="llm")

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(RouteData, problem.data)
        # strip_problem_type: 判別子は LLM に見せない(下記「実運用で判明した罠」参照)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(RouteSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = RouteSolution(
            problem_type="route_planning", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

- **本番 `REGISTRY`(`app/algorithms/registry.py`)には登録しない**。`/solve` の既定選択
  (`select_strategy`)に一切影響させない ── `ComparisonService` が比較専用に直接
  インスタンス化する(Phase 12 の「既存 `/solve` には触れない」判断と同じ)。
- 出力スキーマは既存の `RouteSolution`/`ShiftSolution`/`NetworkDesignSolution`/
  `TravelSolution`/`ProjectSolution`/`LogisticsSolution` をそのまま使う(新スキーマなし)。
- プロンプトは Phase 11 の `catalog_entries`(id/name カタログを渡して grounding させる)と同じ狙い ── 「実在する id だけを使わせる」。6ドメイン共通の目的/制約の自然言語化は
  `app/algorithms/llm/common.py` に1本化する。
- **失敗時のリトライ・グレースフルデグレードをしない** ── Structuring(最大3回リトライ)/Recommendation・Explanation(LLM失敗時に代替結果を返す)とは逆の判断。Phase 14 は「生の」LLM 信頼性を測ることが目的なので、失敗を隠すと計測(エラー率)が歪む。例外はそのまま `ComparisonService` に伝播させる。

**実運用で判明した罠(実際に Gemini を呼んで初めて発覚)**: `RouteSolution` 等の
`problem_type: Literal[...] = "..."`(判別子フィールド)をそのまま LLM に見せると、
6ドメイン全ての試行が `literal_error` で失敗した。Pydantic v2 は単一値の `Literal` を
JSON Schema の `"const"` で表現するが、Gemini の構造化出力(`response_json_schema`)は
`const` をサポートせず、制約が黙って無視されて LLM が任意の値(実測: `"shortest_path"`)を
生成してしまう。`FakeLLM` を使うユニットテストは固定値をそのまま返すだけなので発見できず、
本物の LLM 呼び出しで初めて顕在化した。対処として `app/algorithms/llm/common.py` に
`strip_problem_type()`(`create_model` で判別子を除いた派生スキーマを動的生成)を追加し、
`solve()` 側で固定値を足し戻す(詳細は `Phase-14-2.md` §4)。

### 3.3 `ComparisonService`(新規、素の async 関数群。LangGraph 不使用)

Phase 9/10/12/13 と同じ判断基準(DB 読み取りなし・LLM 呼び出しは高々数回・単純な直線フロー)。

```text
POST /api/v1/compare
  ├─ レート制限(resource="compare")
  ├─ Validation(solve/benchmark と同じ)
  ├─ Algorithm 経路: select_strategy() で1本 → 1回 solve → verify
  ├─ LLM Only 経路: LlmOnly*Strategy を llm_runs 回 → 各回 solve(例外は捕捉)→ verify
  ├─ 集計(6軸のうち5軸を数値化)
  └─ 任意のナレーション生成(Phase 13 SolutionExplanationService と同型。失敗時は
     グレースフルデグレード ── ここだけは Phase 12/13 と同じ方針)
```

**「測定」と「その説明」で信頼性要件を変える**という、この Phase 固有の設計判断:

| 対象                    | リトライ | 失敗時のフォールバック           | 理由                                 |
| --------------------- | ---- | --------------------- | ---------------------------------- |
| LLM Only の実行(6軸の元データ) | なし   | なし(例外を記録して先へ進む)       | 生の信頼性を測ることが目的。隠すと計測が歪む             |
| 比較結果のナレーション(補助的な要約文)  | なし   | あり(metrics を機械的に文字列化) | 「narrate すること」自体が価値。Phase 13 と同じ判断 |

- **最適性の集計は `metrics` と `assignments` の両方を見る**: route/network/travel/project/
  logistics は目的の対象(`total_weight` 等)が `CandidateSolution.metrics` ではなく
  `solution.assignments` 側のフィールドにある(shift だけは `structural_verify` が
  `assignment_metrics()` で `metrics` に積む)。`_objective_metrics()` がこの非対称を吸収し、全ドメインで `optimality_avg_quality_ratio_llm` を計算できるようにする。
- **再現性は「構造のハッシュ」で数える**: `assignments` を JSON 化してハッシュ化した
  `structure_hash` を `RunOutcome` に持たせ、成功した LLM 試行の中で何種類の構造が出たかを数える(妥当性とは独立の指標 ── invalid な解でも「同じ構造を繰り返し返しているか」は測れる)。
- **制約遵守率の分母は「成功した試行数」**: 例外で落ちた回は「制約を破った」のではなく「解自体を出せなかった」ので、遵守率でなくエラー率側に反映する。

### 3.4 エンドポイント

新規 `app/api/routes/comparison.py`(`POST /api/v1/compare`)── 「Algorithm 同士を比較するBenchmark」とは対象・目的が異なる新しい操作のため新ファイルにする(Phase 9 `routes/jobs.py`・Phase 11 `routes/structure.py` と同じ判断)。永続化しない(GET エンドポイントは無い、Phase 10 Simulation・Phase 12 Recommendation と同型)。

### 3.5 UI

`AlgorithmRecommendationCard`(Phase 12)・`ExplanationCard`(Phase 13)に続く3つ目の横断コンポーネント `ComparisonCard`。6軸の集計値を小さな表で、ナレーションをテキストで表示する。
6 Planner Panel すべてに同じ形で追加する。

## 4. 章一覧(章 = 作業単位)

14-1 → (14-2, 14-3, 14-4 は並行して読める) → 14-5 → 14-6 → 14-7 の鎖。

| 章                             | トピック                    | 依存          | 主な内容                                                                                    |
| ----------------------------- | ----------------------- | ----------- | --------------------------------------------------------------------------------------- |
| [Phase-14-1](./Phase-14-1.md) | `family` 拡張 + 共通プロンプト部品 | Phase 13 まで | `app/domain/solutions/solution.py`(改訂)、`app/algorithms/llm/__init__.py`・`common.py`(新規) |
| [Phase-14-2](./Phase-14-2.md) | LLM Only 戦略(グラフ系)       | 14-1        | `route_llm.py` / `network_llm.py`                                                       |
| [Phase-14-3](./Phase-14-3.md) | LLM Only 戦略(スケジューリング系)  | 14-1        | `shift_llm.py` / `project_llm.py`                                                       |
| [Phase-14-4](./Phase-14-4.md) | LLM Only 戦略(最適化系)       | 14-1        | `travel_llm.py` / `logistics_llm.py`                                                    |
| [Phase-14-5](./Phase-14-5.md) | `ComparisonService`     | 14-2〜14-4   | `app/schemas/comparison.py`・`app/services/comparison.py`(新規)                            |
| [Phase-14-6](./Phase-14-6.md) | ルート配線 + e2e             | 14-5        | `app/api/routes/comparison.py`(新規)、`routes/__init__.py`・`core/config.py`(改訂)            |
| [Phase-14-7](./Phase-14-7.md) | UI(比較カード)               | 14-6        | `features/optimization/{api,stores,hooks,components}` + 6 Panel への導線                    |

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜13 と同じ)

1. Claude が教材(この導入 + 7章)とサンプル(`textbook/samples/`)を書く。実コードは
   書かない ── 実装は `decitima-api`/`decitima-ui` にユーザーが写経する。
2. 各章は「この章で作成/更新するファイル」を明記し、責務1行 + 非自明な判断を解説する。
3. 章を読み終えたら該当ファイルを写経し、章末のテストを実行して緑を確認してから次の章へ。
4. samples のフル検証は共有 `textbook/samples/` を1回 overlay して回す
   (`textbook/samples/README.md`)。今回は backend `uv run pytest` **621 passed / 6
   deselected**(新規19 ── llm_only strategies 7 / comparison schemas 4 / comparison
   service 5 / comparison api 3。既存 602 件は無改造で再実行し回帰なし)、`ruff check` /`ruff format --check` はいずれも新規コード側 0 件(`app/services/errors.py` の
   pre-existing 債務は対象外)、`uvx pyright` 0 件。ui `npx tsc --noEmit` clean、
   `npx vitest run` **新規6件 passed**(既存回帰なし。`Menu.test.tsx` の1件は Phase 13時点から存在する pre-existing の環境依存失敗で本 Phase と無関係)、`npx eslint .` 0 件。
   `alembic upgrade head` は no-op(永続化しない設計のため新テーブル無し)。

## 6. テストの階層

| レベル               | 使うもの                                                                                         | Phase 14 で書くもの                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| LLM Only 戦略(unit) | `FakeLLM`(各ドメインモジュールの `get_gemini_llm` を monkeypatch)                                        | `test_llm_only_strategies.py`(14-2/14-3/14-4。6ドメイン + 「嘘」を検証が捕まえる1ケース)                              |
| サービス(unit)        | `FakeLLM` + `FakeRedis` + 実 `select_strategy`/`SolutionVerificationService`(フェイク不要 ── 純粋・既存) | `test_comparison_schemas.py`(14-5、純粋)・`test_comparison_service.py`(14-5、集計/エラー率/再現性/フォールバック/レート制限) |
| API(e2e)          | `api` fixture(認証込み client)                                                                   | `test_comparison_api.py`(14-6、配線確認 + 既存 `POST /solve` の回帰)                                         |
| UI store/api      | vitest + `vi.mock`                                                                           | `compare.test.ts`・`comparison-store.test.ts`(14-7)                                                 |

**用語**(Phase 12 で初出、以降は関係の明記のみ): SUT(テスト対象)/ ドライバ(テストを
実行するもの)/ スタブ(外部依存の代役)。

**集約の機構のテストはフェイクで行う**(進行のルール #15): `_LLM_ONLY_STRATEGIES` の
ディスパッチそのものは `ComparisonService` の unit テストが実際の6戦略を通して間接的に検証する(6ドメイン専用の「フェイク戦略」を新設するより、既存の `LlmOnlyRouteStrategy` を
`FakeLLM` で駆動する方が実装と乖離しない)。

## 7. Phase 14 のスコープと非スコープ

| Phase 14 でやる                                                            |
| ----------------------------------------------------------------------- |
| 「LLM Only」経路の実装(6ドメイン、既存解スキーマの再利用)                                      |
| README §14 の6評価軸のうち5軸の数値集計 + 検証可能性の定性的な説明                               |
| 決定論的アルゴリズム(既定選択1本)との実測比較                                                |
| 比較結果の LLM ナレーション(Phase 13 `SolutionExplanationService` と同型のグレースフルデグレード) |

- **登録済み全アルゴリズムとの比較**(Phase 3 `BenchmarkService` 型の横並び)── キックオフ確認で見送り。既定選択の1本のみと比較する(README 図の単一 Algorithm ボックスに忠実)。
- **比較結果の永続化**── キックオフ確認で見送り。Phase 9 Simulation・Phase 12
  Recommendation と同じステートレス設計。必要になれば独立した検討課題(着手時期未定)。
- **LLM Only 戦略のプロンプト改善・few-shot 化**── 教材の主眼は「同じ検証コードで比較する仕組み」であって「LLM の精度を上げる」ことではない。実測結果を見て改善するかはユーザー判断。
- **README §15(Production)の性能・セキュリティ強化**── 引き続き Phase 15 の範囲。

## 8. Phase 14 実装前チェックリスト

進行のルール #11。行 `14-M` ↔ 章 `Phase-14-M`。

| #    | 作る/変えるファイル                                                                                                                                                                                                                            | 主なクラス・関数の責務(1行)                                                                                                                                                                                        |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 14-1 | `app/domain/solutions/solution.py`(改訂、`AlgorithmFamily` に `"llm"` 追加)、`app/algorithms/llm/__init__.py`・`common.py`(新規)                                                                                                                | `LLM_ONLY_META`(6クラス共通の `AlgorithmMeta`)/ `render_objectives`・`render_constraints`(目的・制約の自然言語化)/ `strip_problem_type`(判別子を除いた LLM 出力用スキーマの動的生成、実運用検証で判明した罠への対処)                                                                                                        |
| 14-2 | `app/algorithms/llm/route_llm.py`・`network_llm.py`(新規)、`tests/unit/test_llm_only_strategies.py`(新規、route/network 分)                                                                                                                   | `LlmOnlyRouteStrategy`・`LlmOnlyNetworkStrategy`(`AlgorithmStrategy` 準拠、REGISTRY 非登録)                                                                                                                   |
| 14-3 | `app/algorithms/llm/shift_llm.py`・`project_llm.py`(新規)、`test_llm_only_strategies.py`(shift/project 分を追記)                                                                                                                              | `LlmOnlyShiftStrategy`・`LlmOnlyProjectStrategy`                                                                                                                                                        |
| 14-4 | `app/algorithms/llm/travel_llm.py`・`logistics_llm.py`(新規)、`test_llm_only_strategies.py`(travel/logistics 分を追記)                                                                                                                        | `LlmOnlyTravelStrategy`・`LlmOnlyLogisticsStrategy`                                                                                                                                                     |
| 14-5 | `app/schemas/comparison.py`・`app/services/comparison.py`(新規)、`app/core/config.py`(改訂、レート制限フィールド追加)、`tests/fixtures/fake_llm.py`(改訂、`structured_sequence` 追加)、`tests/unit/test_comparison_schemas.py`・`test_comparison_service.py`(新規) | `ComparisonService.compare()`(2経路の実行・集計・ナレーション)/ `_run_once`・`_aggregate`・`_objective_metrics`・`_structure_hash`・`_narrate`・`_fallback_narrative`(私設ヘルパ)/ `COMPARE_RATE_LIMIT_PER_HOUR`・`_PER_DAY`     |
| 14-6 | `app/api/routes/comparison.py`(新規)、`app/api/routes/__init__.py`(改訂)、`tests/api/test_comparison_api.py`(新規)                                                                                                                            | `compare_llm_vs_algorithm()`(ルートハンドラ)                                                                                                                                                                  |
| 14-7 | `ui/src/lib/api/types.ts`(改訂)、`ui/.../api/compare.ts`・`stores/comparison-store.ts`・`hooks/useComparison.ts`・`components/ComparisonCard.tsx`(新規)、6 つの既存 Planner Panel(改訂)、`compare.test.ts`・`comparison-store.test.ts`(新規)             | `ComparisonResponse` 等(型)/ `compareLlmVsAlgorithm`(POST の薄いラッパ)/ `useComparisonStore`(result/status/error/run/reset)/ `useComparison`(store の薄いラッパ)/ `ComparisonCard`(比較結果 UI、6ドメイン共通)/ 各 Panel への導線1行 |

## 9. サンプルコード ── 共有 `textbook/samples/`

要点:

- **`app/algorithms/llm/` は Phase 12 の `AlgorithmRecommendationService`・Phase 13 の
  `SolutionExplanationService` と同じ「LLM 呼び出しモジュール単位で `get_gemini_llm` を
  monkeypatch する」テスト方針をそのまま踏襲**できる(呼び出し元がドメイン別ファイルに
  分かれているだけで、パターン自体は変わらない)。
- **`_objective_metrics` が本 Phase 唯一の非自明な発見**: 目的の対象値が `metrics` と
  `assignments` のどちらにあるかはドメインによって違う(shift だけ `metrics`)。この差異は
  Phase 6-1 の「shift の metrics 計算は shift_metrics.py に集約」という設計の副産物であり、
  Phase 14 で初めて「全ドメイン共通で目的値を1箇所から引く」ことが要求されて顕在化した。
- **`FakeLLM` の `structured_sequence` 拡張は既存呼び出しと完全後方互換**(`structured=`
  のみ渡す既存テストは無改造で動く)。N 回の呼び出しで異なる結果・例外を返す必要があるのは
  Phase 14 が最初(進行のルール #17 ── 今駆動している実在の消費者は `test_comparison_service.py`)。
- **UI 側は Phase 12/13 と全く同じ形**(`persist` は不要 ── `/compare` は `/benchmark` や
  `/recommend` と同じく素の `OptimizationProblem` を受けるので、Phase 13 のような
  「solve してから explain する」2段階は無い)。
- **`strip_problem_type` は実際に Gemini を呼んで初めて必要と分かった**(詳細
  `Phase-14-2.md` §4)。`FakeLLM` によるユニットテストだけでは検出できない種類の問題 ──
  「モックでは決して顕在化しないインテグレーションの落とし穴」を Phase 14 で最初に踏んだ
  実例として、進行のルール #9(検証で見つけた問題は反映してから次に進む)がそのまま効いた。

検証: backend `uv run pytest` **621 passed / 6 deselected**(新規19、既存602件は無改造で
再実行し回帰なし)、`ruff check` / `ruff format --check` は新規コード側0件、`uvx pyright`
0件(`app/services/errors.py` の pre-existing 債務は samples の対象外)。ui `npx tsc
--noEmit` clean、`npx vitest run` 新規6件 passed(既存回帰なし、`Menu.test.tsx` の
pre-existing 失敗1件は無関係)、`npx eslint .` 0件。`alembic upgrade head` は no-op。
`strip_problem_type` 追加後も上記件数・0件は変わらない(コメント/ロジック追加のみで
既存テストは無改造のまま green)。

## 10. Phase 14 の成果物

- `textbook/Phase-14/`(導入 + 7章)
- `textbook/samples/app/domain/solutions/solution.py`(改訂)・
  `app/algorithms/llm/{__init__,common,route_llm,network_llm,shift_llm,project_llm,
  travel_llm,logistics_llm}.py`(新規)・`app/schemas/comparison.py`・
  `app/services/comparison.py`(新規)・`app/api/routes/comparison.py`(新規)・
  `app/api/routes/__init__.py`・`app/core/config.py`(改訂)・
  `tests/fixtures/fake_llm.py`(改訂)・
  `tests/unit/{test_llm_only_strategies,test_comparison_schemas,test_comparison_service}.py`・
  `tests/api/test_comparison_api.py`(新規)
- `textbook/samples/ui/src/lib/api/types.ts`(改訂)・
  `ui/src/features/optimization/{api/compare,stores/comparison-store,
  hooks/useComparison,components/ComparisonCard}.{ts,tsx}`(新規)・
  `api/compare.test.ts`・`stores/comparison-store.test.ts`(新規)・
  6つの既存 Planner Panel(改訂)
- `CLAUDE.md`「### 設計判断・検証知見」に Phase 14 の要約
- `textbook/q_a.md` Q63(キックオフ確認)

## 11. 次のフェーズ

Phase 14 で「LLM 単独 vs 決定論的アルゴリズム」の実測比較までが揃い、README §0〜14 が
描いた MVP 以降の拡張フェーズが一区切りする。次の Phase 15(Production)は、この
プロジェクト全体を実サービスとして公開できる品質へ仕上げるフェーズ ──
Testing(Unit/Integration/API/E2E/Algorithm/Constraint)・Performance(ベンチマーク・
DBクエリ最適化・非同期処理・キャッシュ・大規模入力)・Security・Deployment
(GitHub Actions → Docker → VPS、UI は Vercel)。多くはテンプレートが既に足場を提供しており
作り直さず再利用する方針(README §15 設計のポイント)。Phase 11-9 で暫定導入した
`_MAX_KNAPSACK_DP_CELLS` の閾値見直しなど、これまでの Notes に残した「Phase 15 で検討」
項目もここで回収する。
