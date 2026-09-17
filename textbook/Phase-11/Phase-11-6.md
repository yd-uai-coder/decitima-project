# Phase 11-6: `assemble_problem`/`validate_problem` ノード + ワークフロー組み立て(作業単位 11-6)

## この章のゴール

Structuring ワークフローの最後の2ノードを実装し、`build_structuring_workflow` で
6ノードを一直線に繋ぐ。ここで初めて「自然言語 → 検証済み `OptimizationProblem`」のパイプラインが end-to-end で動くようになる。

**この章で作成/更新するファイル**: `app/ai/graph/nodes.py`(追記、6関数が揃い完成)、
`app/ai/graph/workflow.py`(全面書換)。

---

## 1. `assemble_problem` ── overrides を組み立てて `apply_overrides` でマージ

```python
# app/ai/graph/nodes.py(追記)
def assemble_problem(state: GraphState) -> dict:
    """objectives_patch/constraints_patch/data_patch を overrides dict に変換し、
    `apply_overrides`(Phase 10)でベース問題にマージする。objectives_patch が空なら
    (`build_overrides` の判断で)ベースの objectives を維持する ── 抽出失敗で目的が
    空欄消失するのを防ぐ非自明な判断なので、その旨を notes に記録する。"""
    base_problem = state["base_problem"]
    assert base_problem is not None  # load_base_problem が必ず先に走る
    overrides = build_overrides(
        state["objectives_patch"], state["constraints_patch"], state["data_patch"]
    )
    notes: list[str] = []
    if not state["objectives_patch"]:
        notes.append(
            "目的(objectives)を要求文から抽出できなかったため、ベース問題の既定目的を使用しました"
        )
    return {"problem": apply_overrides(base_problem, overrides), "notes": notes}
```

11-2 で作った `build_overrides` と Phase 10 の `apply_overrides` を繋ぐだけの薄いノード。
「objectives が空なら維持する」という判断そのものは `build_overrides` 側(11-2)に既に
入っているため、ここでの責務は「その判断が起きたことを人間に伝える `notes` を作る」ことに
限定される(責務の分離 ── マージのロジックと、ユーザー向けメッセージの生成を混ぜない)。

---

## 2. `validate_problem` ── 既存 Validation + グラウンディング検査の二段

```python
def validate_problem(state: GraphState) -> dict:
    """Semantic Validation(既存、Phase 0〜9)+ グラウンディング検査(Phase 11 専用)を通す。
    NG は例外をそのまま呼び出し元へ伝播させる(state に error フィールドを持たせない ──
    app/services/solve.py と同じ方針)。"""
    problem = state["problem"]
    base_problem = state["base_problem"]
    assert problem is not None  # assemble_problem が必ず先に走る
    assert base_problem is not None  # load_base_problem が必ず先に走る

    ProblemValidationService().validate(problem)

    issues = ground_references(problem, catalog_ids(base_problem))
    if issues:
        raise ProblemValidationError("; ".join(issues))
    return {}
```

**二段構えの検証**: (1) 既存 `ProblemValidationService`(Phase 0〜9 の Semantic Validation

+ 到達可能性等の計算検査)を**無改造**で呼ぶ ── route の start/goal がカタログに実在する
  かはここで既に検査される。(2) その上で `ground_references`(11-2)が、既存 Validation が
  見ていない「constraints の items が実在するか」を追加で確認する。**NG は state に書かず
  例外をそのまま投げる** ── `app/services/solve.py::SolveService.solve` と同じ設計方針
  (LangGraph のノードが例外を投げると、そのままワークフロー呼び出し元(11-7 の
  `ProblemStructuringService`)まで伝播する)。

---

## 3. `build_structuring_workflow` ── 一直線のパイプライン

```python
# app/ai/graph/workflow.py(全文)
def build_structuring_workflow() -> CompiledStateGraph:
    workflow = StateGraph(GraphState)

    workflow.add_node("classify_problem_type", classify_problem_type)
    workflow.add_node("load_base_problem", load_base_problem)
    workflow.add_node("extract_objectives_constraints", extract_objectives_constraints)
    workflow.add_node("extract_domain_data", extract_domain_data)
    workflow.add_node("assemble_problem", assemble_problem)
    workflow.add_node("validate_problem", validate_problem)

    workflow.add_edge(START, "classify_problem_type")
    workflow.add_edge("classify_problem_type", "load_base_problem")
    workflow.add_edge("load_base_problem", "extract_objectives_constraints")
    workflow.add_edge("extract_objectives_constraints", "extract_domain_data")
    workflow.add_edge("extract_domain_data", "assemble_problem")
    workflow.add_edge("assemble_problem", "validate_problem")
    workflow.add_edge("validate_problem", END)

    return workflow.compile()


@lru_cache
def get_structuring_workflow() -> CompiledStateGraph:
    return build_structuring_workflow()
```

以前の `build_chat_workflow` は `decide_to_search` による条件分岐エッジ(検索する/しない)を持っていたが、Structuring ワークフローには**条件分岐エッジが1つも無い**。ドメインごとの違いは全て `extract_domain_data`(11-5)の内部で吸収されているため、グラフの形は6ドメイン共通で一直線 ── 11-5 で述べた「グラフの分岐 vs 関数内のディスパッチ」の違いがここに現れる。

---

## まとめ

- `assemble_problem`/`validate_problem` で6ノードが揃い、`build_structuring_workflow` が
  初めて「通しで動くパイプライン」を組み立てる。
- Validation は「既存の Semantic Validation」+「新設のグラウンディング検査」の二段構え。
  例外は state に書かず、そのまま呼び出し元へ伝播させる(state に error フィールドを
  持たせない設計)。
- ワークフローに条件分岐エッジは無い ── ドメイン差は `extract_domain_data` 内部だけで
  吸収する。

## テスト観点(`tests/unit/test_ai_graph_nodes.py` 追記 / `tests/unit/test_structuring_workflow.py` 新規)

> **対象**: `assemble_problem`/`validate_problem`(単体)、
> `build_structuring_workflow().ainvoke(...)`(合成、初めての end-to-end)
> **ドライバ**: このテスト関数(ワークフロー合成テストは pytest-asyncio、
> `asyncio_mode = "auto"`)
> **スタブ**: `assemble_problem`/`validate_problem` は純粋(`apply_overrides`・
> `ProblemValidationService` はいずれも純粋)なのでスタブ不要。ワークフロー合成テストは
> `classify_problem_type`/`extract_objectives_constraints`/`extract_domain_data` の3箇所で
> 呼ばれる `get_gemini_llm` を、呼び出し順に異なる `FakeLLM` を返す関数に monkeypatch する
> (Fake の差し込みポイントが複数ノードにまたがる ── 単体テストとの違い)

| ケース                                                       | 期待                                                                                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `assemble_problem`(objectives/constraints/data の3パッチを与える) | `problem` に全て反映、`notes == []`                                                                                       |
| `assemble_problem`(objectives_patch が空)                   | `problem.objectives == base.objectives`、`notes` に注記が付く                                                              |
| `validate_problem`(無改造のベース問題)                             | `{}`(例外なし)                                                                                                          |
| `validate_problem`(constraints に `items=["浅草"]` を混入)      | `ProblemValidationError`                                                                                            |
| ワークフロー全体(README §3.1 の travel 例)                          | `problem.problem_type == "travel_planning"`、`problem.data.budget == 50000`、`problem.constraints[0].items == ["P1"]` |
| ワークフロー全体(network_design)                                  | FakeLLM を2つしか渡さなくても完走(3つ目の data 抽出で LLM を呼ばないため)                                                                    |
| ワークフロー全体(存在しない id を参照する constraints)                      | `ProblemValidationError` がワークフロー全体を通しても伝播する                                                                         |

`uv run pytest tests/unit/test_ai_graph_nodes.py tests/unit/test_structuring_workflow.py` /
`uvx pyright app/ai/graph/nodes.py app/ai/graph/workflow.py`。

---

次章([Phase-11-7](./Phase-11-7.md))では、作業単位 11-7 ── サービス層
(`ProblemStructuringService`)と API 層(`POST /api/v1/structure`)を実装し、旧 `ChatService`/
`chat.py` を置き換える。
