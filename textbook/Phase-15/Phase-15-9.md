# Phase 15-9: LLM構造化 → Travel Planner E2E(作業単位 15-9)

## この章のゴール

6ドメイン共有の入力パターン②(自然言語 → LLM構造化 → 確認カード → 該当ドメインへ遷移 →solve)を Travel Planner で実演する(選定理由は `Phase-15-introduction.md` §7)。本章の核心は E2E シナリオそのものより、**Playwright が本物の Gemini API を呼ばずに決定論的に完走するための設計**。

**この章で作成 / 更新するファイル**: `ui/e2e/travel-structuring.spec.ts`(新規)、
`app/ai/llm/e2e_fixture.py`(新規)、`app/ai/llm/gemini.py`(改訂)、
`app/core/config.py`(改訂、`E2E_TESTING` 追加)、`tests/unit/test_e2e_fixture.py`(新規)。

---

## 1. 設計課題 ── E2Eはpytestのmonkeypatchが使えない

Structuring ワークフロー(Phase 11)は `get_gemini_llm()`(`app/ai/llm/gemini.py`、
`@lru_cache`)を8箇所(`app/ai/graph/nodes.py`・`app/algorithms/llm/*.py`・
`app/services/{explanation,comparison,algorithm_recommendation}.py`)から直接呼ぶ。
pytest の単体テストは `tests/fixtures/fake_llm.py::FakeLLM` を
`monkeypatch.setattr(モジュール, "get_gemini_llm", ...)` で差し替えている
(呼び出し元モジュールの名前空間を書き換える、Phase 12 で確立したパターン)が、
**これはテストプロセス内でしか効かない**。Playwright は `npm run dev` が起動する
本物のサーバープロセスに対して外部から HTTP リクエストを送るだけなので、monkeypatch の出番が無い。

方針: `get_gemini_llm()` 自身が `settings.E2E_TESTING` を見て、true なら
インターフェース互換のフェイクを返す ── **経路の切り替えを呼び出し元でなく生成元1箇所に閉じる**(8箇所の呼び出し元は無改造で済む)。

```python
# app/core/config.py(改訂、抜粋)
# (Phase 15-9) E2E テスト専用フラグ。true のとき get_gemini_llm() は実際の Gemini API を
# 呼ばず、決定論的な固定応答を返すフェイクを返す。既定は false(本番は絶対に有効化しない。
# .env にも書かず E2E 実行時だけ環境変数で渡す)。
E2E_TESTING: bool = False
```

```python
# app/ai/llm/gemini.py(改訂、全文)
@lru_cache
def get_gemini_llm(*, temperature: float = 0.7) -> ChatGoogleGenerativeAI | E2eFakeLLM:
    if settings.E2E_TESTING:
        return E2eFakeLLM()
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL, api_key=settings.GOOGLE_API_KEY, temperature=temperature,
    )
```

## 2. `E2eFakeLLM` ── 対応スキーマを絞り、未対応は明示的に落とす

Travel Planner の E2E シナリオが実際に踏むのは Structuring ワークフローの3スキーマ
(`ProblemTypeClassification`/`ObjectivesConstraintsExtraction`/`TravelDataPatch`)だけ ──
各 Planner Panel が持つ `AlgorithmRecommendationCard`/`ExplanationCard`/`ComparisonCard`用のスキーマは、シナリオがそれらのボタンを押さない限り呼ばれないため対応不要。
**全スキーマ対応の汎用フェイクを先回りで作らない**(進行のルール #17)。

```python
# app/ai/llm/e2e_fixture.py(新規、全文は samples)
_E2E_STRUCTURED_RESPONSES: dict[type[BaseModel], BaseModel] = {
    ProblemTypeClassification: ProblemTypeClassification(problem_type="travel_planning"),
    ObjectivesConstraintsExtraction: ObjectivesConstraintsExtraction(objectives=[], constraints=[]),
    TravelDataPatch: TravelDataPatch(),   # 全フィールド None ── ベース問題をそのまま使う
}

class _E2eStructuredLLM:
    def __init__(self, schema: type[BaseModel]) -> None:
        self._schema = schema

    def _resolve(self) -> BaseModel:
        try:
            return _E2E_STRUCTURED_RESPONSES[self._schema]
        except KeyError as exc:
            raise NotImplementedError(f"E2E フェイクLLMは {self._schema.__name__} に未対応です") from exc

    def invoke(self, _messages: Any) -> BaseModel:
        return self._resolve()

    async def ainvoke(self, _messages: Any) -> BaseModel:
        return self._resolve()
```

`TravelDataPatch` を全フィールド `None` にした理由: E2E が検証したいのはパイプライン全体(分類→抽出→組み立て→検証→遷移→solve)が壊れずに繋がることで、抽出値そのものの妥当性ではない。ベース問題(`base_problems.py`)は既に curated で確実に valid なので、「何も上書きしない」が最も安全な固定応答になる。

## 3. 写経の罠(実測で発覚)── `invoke` と `ainvoke` の両対応が必須

最初の実装は `ainvoke` だけを実装していた。ところが実際に Playwright を走らせると
`POST /api/v1/structure` が **502 Bad Gateway** で落ちた。原因:
`app/ai/graph/nodes.py`(Structuring の分類/抽出ノード)は**同期** `llm.invoke(...)` を
呼ぶが、`app/services/explanation.py`/`comparison.py` は**非同期** `llm.ainvoke(...)` を呼ぶ ── 既存 `tests/fixtures/fake_llm.py::_FakeStructuredLLM` は最初から両方実装していたのに、新規の `E2eFakeLLM` ではそれを見落としていた。`invoke` を実装後に再実行して解消した。

> **写経の罠**: この種のインターフェース不一致は pytest の単体テスト(呼び出し元ごとに別々にモックする)では見つからない ── 実際にサーバープロセスを起動し、ブラウザから一連の操作を通す E2E だからこそ発見できた。README §15 が Unit Test と別に E2E Test を掲げる理由そのものの実例。

## 4. E2E シナリオ

```typescript
// ui/e2e/travel-structuring.spec.ts(新規、全文)
test("login -> structuring -> confirm -> travel planner -> solve", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("example-user@example.com");
  await page.getByLabel("パスワード").fill("sample-user-0123");
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"));

  await page.goto("/optimization/structuring");
  await page.getByLabel("natural-language-input").fill("5万円以内で東京を2日間旅行したい。");
  await page.getByRole("button", { name: "内容を理解する" }).click();

  await expect(page.getByText("AIが理解した条件")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "この条件で最適化する" }).click();

  await page.waitForURL(/\/optimization\/travel-planner/);
  await page.getByRole("button", { name: "プランを作る(Knapsack DP)" }).click();

  await expect(page.getByText(/旅行プラン\(/)).toBeVisible({ timeout: 15000 });
});
```

`natural-language-input`(`NaturalLanguageInputForm` の `aria-label`)・
`AIが理解した条件`(`StructuredProblemCard` の見出し)・「この条件で最適化する」
(確定ボタン)・「プランを作る(Knapsack DP)」(Travel Planner の solve ボタン)は
いずれも既存コンポーネントの既存テキスト/属性で、新しい規約は追加していない。

---

## まとめ

- `get_gemini_llm()` を1箇所改修するだけで、8箇所の呼び出し元を無改造のまま
  E2E 環境で本物の Gemini API を完全に迂回できる設計にした。
- フェイクは E2E シナリオが実際に踏む3スキーマだけに対応を絞り、未対応スキーマは
  `NotImplementedError` で明示的に落とす(誤った値を静かに返さない)。
- `invoke`(同期)と `ainvoke`(非同期)の両対応が必要なことを、実際に Playwright を
  走らせて(502エラーから)発見・修正した。

## テスト観点

`tests/unit/test_e2e_fixture.py`:

> **対象**: `E2eFakeLLM` / `get_gemini_llm`(`E2E_TESTING`分岐)
> **ドライバ**: このテスト関数
> **スタブ不要** ── フェイク自体が対象で、外部依存(実Gemini API)を呼ばないことの確認が目的

| ケース                                                     | 期待                    |
| ------------------------------------------------------- | --------------------- |
| `E2E_TESTING=True` で `get_gemini_llm()`                 | `E2eFakeLLM` を返す      |
| 既知の3スキーマで `with_structured_output(...).ainvoke(...)`    | 固定応答を返す               |
| 既知の3スキーマで `with_structured_output(...).invoke(...)`(同期) | 固定応答を返す(nodes.py の経路) |
| 未対応スキーマ                                                 | `NotImplementedError` |

`ui/e2e/travel-structuring.spec.ts`:

> **対象**: ログイン→自然言語入力→確認→Travel Planner→solve のブラウザ操作フロー全体
> **ドライバ**: Playwright(実ブラウザ、`E2E_TESTING=true` の実サーバー)
> **スタブ**: バックエンド側で `get_gemini_llm()` が `E2eFakeLLM` に切り替わっている
> (Gemini API への実通信は発生しない)

```bash
uv run pytest tests/unit/test_e2e_fixture.py -v
# E2E_TESTING=true でバックエンドを起動してから
npx playwright test e2e/travel-structuring.spec.ts
```

**実測**: 隔離環境(専用 SQLite + 専用 Redis コンテナ、`E2E_TESTING=true` でバックエンドを
別プロセス起動)で実際に実行し、1 passed(約6秒)を確認した(既存の共有 dev 環境
(`decitima-api-backend-1` 等)には一切変更を加えていない)。

---

次章([Phase-15-10](./Phase-15-10.md))では CI/CD ワークフローを組み、ここまでの全チェック
(pytest / performance / ruff / pyright / vitest / eslint / playwright)を GitHub Actions に配線する。
