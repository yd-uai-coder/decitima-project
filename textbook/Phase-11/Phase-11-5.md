# Phase 11-5: `extract_domain_data` ノード(作業単位 11-5)

## この章のゴール

`EXTRACTORS` レジストリ(11-2)を使い、problem_type に応じて data のトップレベル・スカラーを抽出する。`network_design` のように該当スキーマが無いドメインは LLM を一切呼ばない ──
「グラフの分岐」ではなく「関数内のレジストリ参照」でドメイン差を吸収する、という Phase 11の設計判断を体現する章。

**この章で作成/更新するファイル**: `app/ai/graph/nodes.py`(追記)。

---

## 1. `_data_prompt` ── `_objectives_prompt` と同じ grounding の徹底

```python
# app/ai/graph/nodes.py(追記)
def _data_prompt(text: str, base_problem: OptimizationProblem) -> str:
    """data のトップレベル・スカラー抽出用プロンプトを組み立てる(§ _objectives_prompt と
    同じ grounding の徹底)。"""
    catalog_lines = "\n".join(
        f"- {id_}" + (f": {name}" if name else "") for id_, name in catalog_entries(base_problem)
    )
    return (
        "以下はユーザーの自然言語の要求です。指定されたスキーマのフィールドのうち、"
        "要求文から読み取れるものだけを埋めてください。読み取れないフィールドは触れずに"
        "そのままにしてください。id を書く場合は必ず下記の一覧から選んでください。\n\n"
        f"利用可能な id 一覧:\n{catalog_lines}\n\nユーザーの要求:\n{text}"
    )
```

「読み取れないフィールドは触れずにそのままにしてください」── これが 11-1 の
`*DataPatch` が全フィールド Optional である理由と対になっている。LLM に「無理に埋めない」ことを明示的に指示する。

---

## 2. `extract_domain_data` ── レジストリ駆動でドメイン差を吸収

```python
def extract_domain_data(state: GraphState) -> dict:
    """`EXTRACTORS` レジストリで problem_type に応じた Data Patch スキーマへディスパッチする。
    パッチスキーマが無い(= トップレベル・スカラーを持たない)ドメインは LLM を呼ばず
    空 dict を返す(network_design)。"""
    problem_type = state["problem_type"]
    assert problem_type is not None  # classify_problem_type が必ず先に走る
    schema = EXTRACTORS.get(problem_type)
    if schema is None:
        return {"data_patch": {}}

    base_problem = state["base_problem"]
    assert base_problem is not None  # load_base_problem が必ず先に走る
    llm = get_gemini_llm(temperature=0).with_structured_output(schema)
    prompt = _data_prompt(state["text"], base_problem)
    patch = cast(BaseModel, llm.invoke([HumanMessage(content=prompt)]))
    return {"data_patch": patch.model_dump(exclude_unset=True)}
```

**教材の核**: `if schema is None: return {"data_patch": {}}` の1行が、Phase 11 全体の設計判断「LLM が埋めてよいのはドメインごとに0〜4フィールド」を最も直接的に表現している。
6ドメイン共通の1つの関数でありながら、`network_design` のケースだけ**LLM を一度も呼ばない**── ワークフローの構造(LangGraph のエッジ)を変えずに、ノード内部の1回の辞書参照だけで実現できる。これは「グラフの分岐」(条件付きエッジ)と「関数内のディスパッチ」(通常のif 文)を区別する良い教材ポイント ── Structuring ワークフロー全体(11-6)は一直線のパイプラインのままで、ドメインごとの違いはここに閉じ込められる。

`patch.model_dump(exclude_unset=True)` ── LLM が実際に設定したフィールドだけを dict にする(11-1 の設計、11-2 の `build_overrides` が `data_patch` として受け取る)。

---

## まとめ

- ドメインごとの「data 抽出の深さの違い」を、ワークフローの構造(エッジ)ではなく
  1つのノード内のレジストリ参照で吸収する。
- `network_design` は LLM を呼ばない唯一のケース ── これ自体がテストの主役になる
  (テスト観点参照)。
- `_data_prompt` は `_objectives_prompt` と同じ grounding の考え方(id 一覧を埋め込む)を踏襲する。

## テスト観点(`tests/unit/test_ai_graph_nodes.py` 追記)

> **対象**: `extract_domain_data`
> **ドライバ**: このテスト関数(6ドメイン分パラメトライズ)
> **スタブ**: `FakeLLM`(5ドメイン分は必須)。**`network_design` だけはスタブ不要** ──
> 「LLM を呼ばないこと」自体がテスト対象になるため(レイヤー設計の鏡 ── #14 の狙いそのもの)

| ケース                                                                                                  | 期待                                                                                                                                        |
| ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 5ドメイン(route/shift/travel/project/logistics)それぞれで `extract_domain_data` を呼ぶ                           | `FakeLLM.structured_output_calls == [対応する *DataPatch クラス]`(正しいスキーマでディスパッチされたことを確認)、`result == {"data_patch": {}}`(何も設定していない Patch を返した場合) |
| `TravelDataPatch(budget=50000)` を返す FakeLLM で `extract_domain_data`(travel)                          | `result == {"data_patch": {"budget": 50000}}`                                                                                             |
| `network_design` で `extract_domain_data` を呼ぶ(`get_gemini_llm` が呼ばれたら `AssertionError` を送出するダミーに差し替え) | 例外が起きず `result == {"data_patch": {}}` を返す(LLM が呼ばれなかったことの直接証拠)                                                                            |
| `_data_prompt("dummy", travel ベース問題)`                                                                | `"P1"`/`"浅草"` を含む(私設ヘルパの回帰)                                                                                                               |

`uv run pytest tests/unit/test_ai_graph_nodes.py` / `uvx pyright app/ai/graph/nodes.py`。

---

次章([Phase-11-6](./Phase-11-6.md))では、作業単位 11-6 ── `assemble_problem`/
`validate_problem` ノードと、ワークフロー全体の組み立て(`build_structuring_workflow`)を
実装する。ここで初めて「通しで動くパイプライン」が完成する。
