# Phase 11-4: `extract_objectives_constraints` ノード(作業単位 11-4)

## この章のゴール

README「Constraint/Objective Extraction」の本体。全 problem_type 共通の1スキーマでobjectives/constraints を抽出するノードを実装する。同時に、プロンプトへ埋め込む
「カタログの (id, name) 一覧」を作る `catalog_entries` を追加する ── これが
`ground_references`(11-2)の第一防衛線になる。

**この章で作成/更新するファイル**: `app/ai/graph/nodes.py`(追記)、
`app/services/structuring.py`(`catalog_entries` 追記)。

---

## 1. `catalog_entries` ── プロンプト用の (id, name) ペア

```python
# app/services/structuring.py(追記)
def catalog_entries(problem: OptimizationProblem) -> list[tuple[str, str | None]]:
    """problem.data の「主要な名前付きエンティティ」を (id, name または label) のペアで
    返す。extract_objectives_constraints のプロンプトに埋め込み、LLM に「id で参照する」
    ことを徹底させるために使う(catalog_ids と違い、edge/leg/segment のような無名の
    関係エンティティは含めない ── 人間が自然言語で名指しするのは大抵ノード側のため)。"""
    data = problem.data
    if isinstance(data, RouteData):
        return [(n.id, n.label) for n in data.nodes]
    if isinstance(data, TravelData):
        return [(p.id, p.name) for p in data.places]
    # ... network_design/shift_scheduling/project_scheduling/logistics_planning も同様
    return []
```

`catalog_ids`(11-2)との違い: `catalog_ids` は「grounding 検査の対象」として edge/leg/segment まで含む広い集合(set)だが、`catalog_entries` は「人間が自然言語で名指ししそうな主要エンティティ」だけを (id, name) のペア(list of tuple、プロンプトの表示順を保つ)で返す。
役割が違うため、共通化を無理強いしない(進行のルール #17 の判定基準「今この章を駆動する実在の消費者は何か」に照らすと、両者の消費先が違うので分けるのが自然)。

---

## 2. `_objectives_prompt` ── grounding の第一防衛線

```python
# app/ai/graph/nodes.py(追記)
def _objectives_prompt(text: str, base_problem: OptimizationProblem) -> str:
    """objectives/constraints 抽出用プロンプトを組み立てる。base_problem のカタログを
    (id, name)で埋め込み、「制約で要素を参照するときは必ず id を使う」ことを徹底させる
    (grounding の第一防衛線。最後の砦は services/structuring.py::ground_references)。"""
    catalog_lines = "\n".join(
        f"- {id_}" + (f": {name}" if name else "") for id_, name in catalog_entries(base_problem)
    )
    return (
        "以下はユーザーの自然言語の要求です。目的(objectives)と制約(constraints)を"
        "抽出してください。制約で特定の要素を参照する場合は、必ず下記の id を使ってください"
        "(名前ではなく id)。該当する id が無ければ、その要素についての制約は生成しないで"
        "ください。\n\n"
        f"利用可能な id 一覧:\n{catalog_lines}\n\nユーザーの要求:\n{text}"
    )
```

「浅草には必ず行きたい」という要求文に対し、プロンプトには `- P1: 浅草` という行が含まれる。
LLM はこれを見て `RequiredInclusionConstraint(items=["P1"])`(id)を返すことが期待できる ──
とはいえ、これは**プロンプトによる誘導**であって型による保証ではない。LLM が契約を破って
`items=["浅草"]`(name)を返す可能性は残るため、11-6 の `validate_problem` が
`ground_references` で最終確認する(二段構え)。

---

## 3. `extract_objectives_constraints`

```python
def extract_objectives_constraints(state: GraphState) -> dict:
    """objectives/constraints をドメイン非依存の1スキーマで抽出する(README「Constraint/
    Objective Extraction」の本体)。全 problem_type 共通で満たす部分。"""
    llm = get_gemini_llm(temperature=0).with_structured_output(ObjectivesConstraintsExtraction)
    base_problem = state["base_problem"]
    assert base_problem is not None  # load_base_problem が必ず先に走る
    prompt = _objectives_prompt(state["text"], base_problem)
    result = cast(ObjectivesConstraintsExtraction, llm.invoke([HumanMessage(content=prompt)]))
    return {"objectives_patch": result.objectives, "constraints_patch": result.constraints}
```

11-1 で定義した `ObjectivesConstraintsExtraction`(`objectives`/`constraints` の2フィールド)を1回の Structured Output 呼び出しでまとめて取得する ── objectives と constraints を別々のLLM 呼び出しに分けない(1 リクエストで両方を抽出する方がコスト・レイテンシの観点で有利で、文脈上どちらも同じ要求文から読み取るため分割する理由が無い)。

---

## まとめ

- `catalog_entries` は `catalog_ids` とは別の目的(プロンプト表示 vs grounding 検査)を持つ、意図的に分けた関数。
- プロンプトに (id, name) の対応表を埋め込むことが grounding の**第一防衛線**。型による保証ではないため、11-6 で `ground_references` による**最後の砦**と組み合わせる二段構え。
- objectives と constraints は1回の Structured Output でまとめて抽出する。

## テスト観点(`tests/unit/test_ai_graph_nodes.py` 追記 / `tests/unit/test_structuring_overrides.py` 追記)

> **対象**: `extract_objectives_constraints`、`catalog_entries`
> **ドライバ**: このテスト関数
> **スタブ**: `extract_objectives_constraints` は `FakeLLM`(必須)。`catalog_entries` は純粋なので不要

| ケース                                                                         | 期待                                                                 |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `_objectives_prompt("dummy", travel ベース問題)`                                 | `"P1"` と `"浅草"` の両方を含む(私設ヘルパの回帰)                                   |
| `extract_objectives_constraints`(FakeLLM が objectives 1件・constraints 1件を返す) | `result["objectives_patch"]`/`result["constraints_patch"]` がそのまま返る |
| `catalog_entries(travel ベース問題)`                                             | `("P1", "浅草")` を含む                                                 |
| `catalog_entries(route ベース問題)`                                              | 5件、全て `(str, str \| None)`                                         |

`uv run pytest tests/unit/test_ai_graph_nodes.py tests/unit/test_structuring_overrides.py` /
`uvx pyright app/ai/graph/nodes.py app/services/structuring.py`。

---

次章([Phase-11-5](./Phase-11-5.md))では、作業単位 11-5 ── `extract_domain_data` ノード
(`EXTRACTORS` レジストリでドメイン別にディスパッチする data 抽出)を実装する。
