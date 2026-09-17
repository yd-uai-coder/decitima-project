# Phase 11-3: `GraphState` 再設計 + `classify_problem_type`/`load_base_problem` ノード(作業単位 11-3)

## この章のゴール

テンプレート由来の Web検索QAチャットワークフロー(`app/ai/graph/`)を、Structuring
ワークフロー用に**全面書き換え**する起点。`GraphState` を再設計し、最初の2ノード
(`classify_problem_type`/`load_base_problem`)を実装する。同時に、キックオフ決定
「Web検索QA機能は廃止する」に基づき、不要になった `app/ai/tools/tavily.py`・
`app/schemas/generation.py` を削除する。

**この章で作成/更新するファイル**: `app/ai/graph/state.py`・`app/ai/graph/nodes.py`(全面書換)、`tests/fixtures/fake_llm.py`(新規、既存テスト内定義の切り出し)、
`tests/unit/test_ai_graph_nodes.py`(全面書換)。
**削除するファイル**: `app/ai/tools/tavily.py`、`app/schemas/generation.py`。

---

## 1. 既存(テンプレート由来)の何を捨て、何を残すか

| 資産                                                                                                                                                    | 処遇                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `app/ai/graph/state.py`(`messages`/`needs_search`/`search_query`/`search_results`/`evaluation`/`answer`)                                              | 全面書換(本章)                               |
| `app/ai/graph/nodes.py`(`draft_response`/`web_search`/`evaluate_search_results`/`generate_final_answer`/`finalize_without_search`/`decide_to_search`) | 全面書換(本章〜11-6 にわたり6関数に置換)               |
| `app/ai/graph/workflow.py`(`build_chat_workflow`/`get_chat_workflow`)                                                                                 | 全面書換(11-6)                             |
| `app/ai/llm/gemini.py`(`get_gemini_llm`)                                                                                                              | **無改造で再利用** ── `temperature` を指定して呼ぶだけ |
| `app/ai/tools/tavily.py`                                                                                                                              | **削除**(本章)                             |
| `app/schemas/generation.py`(`FinalAnswer`)                                                                                                            | **削除**(本章)                             |

`get_gemini_llm(*, temperature: float = 0.7) -> ChatGoogleGenerativeAI` は Structured Outputにも通常の invoke にも使えるプロセス内キャッシュ付きクライアントで、DeciTima 固有の変更が不要 ── キックオフ決定「Gemini を継続」がそのまま活きる。

---

## 2. `GraphState` の再設計

```python
# app/ai/graph/state.py(全文)
class GraphState(TypedDict):
    text: str                                  # ユーザーの自然言語入力
    problem_type: str | None                   # classify_problem_type の出力
    base_problem: OptimizationProblem | None    # load_base_problem の出力(ベース問題の複製)
    objectives_patch: list[ExtractedObjective]  # extract_objectives_constraints の出力
    constraints_patch: list[ExtractedConstraint]
    data_patch: dict[str, Any]                  # extract_domain_data の出力
    notes: list[str]                            # assemble_problem が付ける注記
    problem: OptimizationProblem | None         # assemble_problem の出力(validate_problem が検証)
```

以前の `messages: Annotated[list[BaseMessage], add_messages]` は削除した。Structuring は**単一ターンの決定的パイプライン**(分岐なし)であり、LangGraph 内部でチャット履歴を持ち回る必要が無い。会話としての記録は DB の `Conversation`/`Message`(既存モデル)に外出しする(11-7)。

---

## 3. `classify_problem_type` ── Structured Output で誤答不能にする

```python
# app/ai/graph/nodes.py(要点)
def classify_problem_type(state: GraphState) -> dict:
    """自然言語から problem_type を分類する(Structured Output、Literal[6種]で誤答不能)。"""
    llm = get_gemini_llm(temperature=0).with_structured_output(ProblemTypeClassification)
    prompt = _classify_prompt(state["text"])
    result = cast(ProblemTypeClassification, llm.invoke([HumanMessage(content=prompt)]))
    return {"problem_type": result.problem_type}
```

`ProblemTypeClassification.problem_type` は `Literal[6種]` なので、Structured Output が6つ以外の値を返すこと自体が型として不可能 ── README「分類」を最も単純な形で満たす。

**写経の罠**: `llm.invoke(...)` の戻り値は langchain の型定義上 `dict | BaseModel` にしかnarrowing されない(`with_structured_output` の一般的な戻り型)。`result:
ProblemTypeClassification = llm.invoke(...)` のように変数注釈で直接代入すると pyright が`reportAssignmentType` を出す(`app/ai` を pyright ignore していた旧テンプレートではこの問題が隠れていた)。`cast(ProblemTypeClassification, ...)` で明示的に narrowing する ──
これは「Gemini が `with_structured_output` で指定したスキーマ以外を返すことは実運用上無い」という契約への意図的な信頼であり、`tests/unit/test_auth_service.py` の
`cast(Redis, FakeRedis())` と同じ考え方。

---

## 4. `load_base_problem` ── 純粋、LLM 呼び出しなし

```python
def load_base_problem(state: GraphState) -> dict:
    """problem_type からベース問題を複製して読み込む(純粋、LLM 呼び出しなし)。"""
    problem_type = state["problem_type"]
    assert problem_type is not None  # classify_problem_type が必ず先に走る
    return {"base_problem": get_base_problem(problem_type)}
```

`assert problem_type is not None` は「グラフの実行順序が保証する前提」を型チェッカーに伝える定番パターン(`state["problem_type"]` を直接 narrowing できないため、一度ローカル変数に束ねてから assert する)。11-2 で作った `get_base_problem`(純粋関数)をそのまま呼ぶだけ。

---

## 5. `FakeLLM` の切り出し + スキーマ記録機能

```python
# tests/fixtures/fake_llm.py(全文)
class FakeLLM:
    def __init__(self, content: str | None = None, structured: BaseModel | None = None) -> None:
        self._content = content
        self._structured = structured
        self.structured_output_calls: list[type[BaseModel]] = []

    def invoke(self, _messages: Any) -> AIMessage:
        return AIMessage(content=self._content)

    def with_structured_output(self, schema: type[BaseModel]) -> _FakeStructuredLLM:
        self.structured_output_calls.append(schema)  # 11-5 の検証で使う
        return _FakeStructuredLLM(self._structured)
```

以前は `tests/unit/test_ai_graph_nodes.py` にクラス定義が直接埋め込まれていたが、複数のテストファイルから使うため切り出した。`with_structured_output(schema)` が呼ばれるたびに`schema` を記録する機能を追加した ── 11-5 で「ドメインごとに正しいスキーマでディスパッチされたか」を検証するのに使う。Web検索QA用の `FakeSearchTool` は Tavily の廃止に伴い持ち越さない。

---

## まとめ

- テンプレート由来のチャットワークフローを Structuring 用に置き換える最初の一歩。
  `GraphState` は8フィールドの決定的パイプライン用に再設計し、以前の分岐用フィールド
  (`needs_search` 等)は全廃した。
- `classify_problem_type` は Structured Output の `Literal` 型で分類を「誤答不能」にする。
- `with_structured_output().invoke()` の戻り型は `cast()` で narrowing する ── Phase 11 で
  `app/ai` の型債務(旧 pyright ignore)を解消する具体的な手立て。
- `FakeLLM` を独立ファイルに切り出し、スキーマ記録機能を先読みで足しておく(11-5 で使う)。

## テスト観点(`tests/unit/test_ai_graph_nodes.py`)

> **対象**: `app.ai.graph.nodes.classify_problem_type`/`load_base_problem`
> **ドライバ**: このテスト関数
> **スタブ**: `classify_problem_type` は `FakeLLM`(外部依存の必須スタブ)。
> `load_base_problem` は純粋(`get_base_problem` を呼ぶだけ)なのでスタブ不要

各ノードは `GraphState`(全キー必須の TypedDict)を受け取るため、テストでは
`_INITIAL_STATE`(全キーを埋めた雛形)を土台に `{**_INITIAL_STATE, "text": ...}` で
上書きする(1ノードのテストで関係するキーだけ書きたいが、TypedDict は部分 dict を
受け付けないため)。

| ケース                                                      | 期待                                                                           |
| -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `classify_problem_type`(FakeLLM が `travel_planning` を返す) | `{"problem_type": "travel_planning"}`                                        |
| `_classify_prompt("dummy")`                              | 6つの problem_type を1つも取りこぼさず含む(私設ヘルパの回帰)                                      |
| `load_base_problem({"problem_type": "route_planning"})`  | `base_problem.problem_type == "route_planning"`、`BASE_PROBLEMS` の実体とは別インスタンス |

`uv run pytest tests/unit/test_ai_graph_nodes.py` /
`uvx pyright app/ai/graph/state.py app/ai/graph/nodes.py tests/fixtures/fake_llm.py
tests/unit/test_ai_graph_nodes.py`(`app/ai` は本章で pyright ignore リストから外れる)。

---

次章([Phase-11-4](./Phase-11-4.md))では、作業単位 11-4 ── `extract_objectives_constraints`
ノード(ドメイン非依存の1スキーマで目的・制約を抽出する)を実装する。
