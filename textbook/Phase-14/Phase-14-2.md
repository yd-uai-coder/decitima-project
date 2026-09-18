# Phase 14-2: LLM Only 戦略(グラフ系)(作業単位 14-2)

## この章のゴール

`route_planning` と `network_design` の `LlmOnly*Strategy` を実装する。**この Phase の設計の核**を初めて実地で確認する章 ── LLM に既存の `RouteSolution`/`NetworkDesignSolution`と全く同じスキーマを出力させ、変換コードなしで既存 `SolutionVerificationService` にそのまま通す。

**この章で作成/更新するファイル**: `app/algorithms/llm/route_llm.py`・`network_llm.py`(新規)、`tests/unit/test_llm_only_strategies.py`(新規、route/network 分)。

---

## 1. `LlmOnlyRouteStrategy` ── プロンプトは「ノード/エッジのカタログ + start/goal」

```python
# app/algorithms/llm/route_llm.py(新規、全文)
def _prompt(problem: OptimizationProblem, data: RouteData) -> str:
    nodes = "\n".join(f"- {n.id}: {n.label or n.id}" for n in data.nodes)
    edges = "\n".join(
        f"- {e.id}: {e.source} <-> {e.target}"
        f"(重み {e.weight}{'、一方通行(source→target)' if e.directed else ''})"
        for e in data.edges
    )
    return (
        "次の経路探索問題を解いてください。start から goal まで、下記に実在するノード id・"
        "エッジ id だけを使って経路を1つ構築してください。\n\n"
        f"ノード:\n{nodes}\n\nエッジ:\n{edges}\n\n"
        f"start={data.start} / goal={data.goal}\n\n"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}\n\n"
        "total_weight は実際に選んだエッジの重みの合計と矛盾しないよう正しく計算してください。"
    )


class LlmOnlyRouteStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(RouteData, problem.data)
        # strip_problem_type: 判別子は LLM に見せない(§4 参照)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(RouteSolution)
        )
        # invoke: 同期呼び出し(ComparisonService が asyncio.to_thread の中で呼ぶ前提)
        # cast: with_structured_output().invoke() の戻り型は dict | BaseModel にしか
        # narrowing されない(Phase 11 の既知の型債務と同じ理由)
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = RouteSolution(
            problem_type="route_planning", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

- **出力スキーマは `RouteSolution`(Phase 1、無変更)そのもの** ── `path_node_ids`・
  `path_edge_ids`・`total_weight` の3フィールドを LLM に直接埋めさせる。新しい「LLM 用の解形式」は作らない(`problem_type` だけは §4 の理由で見せない)。
- `with_structured_output(...)` は Phase 11〜13 で確立したパターン
  (`get_gemini_llm(...).with_structured_output(Schema)`)をそのまま流用する。違いは`.invoke()`(同期)を使う点 ── `AlgorithmStrategy.solve` は同期メソッドの契約であり、14-5 の `ComparisonService` が `asyncio.to_thread` の中で呼ぶ前提のため、ここで`async`/`ainvoke` にする必要が無い(既に別スレッドにいるので同期呼び出しでイベントループを塞がない)。
- `status="valid"` は仮の値 ── `AlgorithmStrategy.solve` の契約どおり「検証はしない」(Phase 1 の設計そのまま)。実際の valid/invalid は `SolutionVerificationService.verify()`
  が構造検証で確定する。
- `raw.model_dump(exclude={"problem_type"})`: `raw` は `strip_problem_type(RouteSolution)`
  が動的生成した「`problem_type` を持たない型」のインスタンスなので、本来 `exclude` は
  無くても壊れない。それでも明示するのは、テスト(`FakeLLM`)が `structured=` に
  `problem_type` 込みの完成した `RouteSolution` を渡すため ── `exclude` が無いと
  `RouteSolution(problem_type="route_planning", **raw.model_dump())` が
  `problem_type` を二重に渡すことになり `TypeError` になる(実運用とテストの両方で
  安全に動く形にする)。

## 2. `LlmOnlyNetworkStrategy` ── 全域木の「形」を LLM に選ばせる

```python
# app/algorithms/llm/network_llm.py(新規、要点)
def _prompt(problem: OptimizationProblem, data: NetworkDesignData) -> str:
    nodes = "\n".join(f"- {n.id}: {n.label or n.id}" for n in data.nodes)
    links = "\n".join(
        f"- {link.id}: {link.endpoints[0]} - {link.endpoints[1]}(コスト {link.weight})"
        for link in data.links
    )
    return (
        "次のネットワーク設計問題(最小全域木)を解いてください。下記に実在するリンク id"
        "だけを使い、全ての拠点を1つの木で(閉路を作らずに)接続するリンクの集合を選んで"
        "ください。\n\n"
        f"拠点:\n{nodes}\n\nリンク候補:\n{links}\n\n"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}\n\n"
        "total_weight は実際に選んだリンクのコスト合計と矛盾しないよう正しく計算してください。"
    )


class LlmOnlyNetworkStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(NetworkDesignData, problem.data)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(NetworkDesignSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = NetworkDesignSolution(
            problem_type="network_design", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

`route_llm.py` と同型 ── 差はプロンプトが伝えるドメイン語彙(ノード/エッジ → 拠点/リンク)と出力スキーマ(`RouteSolution` → `NetworkDesignSolution`)だけ。**「全域木になっているか」(連結 ∧ 非閉路)は LLM に自己申告させず、既存 `SolutionVerificationService` の
`_verify_spanning_tree`(`connectivity.forms_spanning_tree` を呼ぶ、Phase 5-3)がそのまま判定する** ── ここでも「LLM は判定しない、既存の検証コードが判定する」原則が効く。

## 3. 「嘘」を既存の検証コードが捕まえることを確認する

`RouteSolution` は `total_weight` を自己申告フィールドとして持つ。LLM が構造(経路)は正しく選べても、合計値の暗算を間違える(またはでたらめな値を返す)ことは十分あり得る。
このケースを実際にテストで再現し、既存 `structure.py::verify_route_structure` が
確実に検出することを確認する:

```python
# tests/unit/test_llm_only_strategies.py(要点)
def test_route_llm_only_lie_about_total_weight_is_caught(monkeypatch):
    problem = build_route_problem()
    lying_solution = RouteSolution(
        path_node_ids=["A", "B", "D", "E"],
        path_edge_ids=["e_ab", "e_bd", "e_de"],
        total_weight=100,  # 実際のエッジ合計は 5
    )
    monkeypatch.setattr(route_llm, "get_gemini_llm", lambda **_: FakeLLM(structured=lying_solution))

    candidate = LlmOnlyRouteStrategy().solve(problem)
    verified = SolutionVerificationService().verify(problem, candidate)

    assert verified.status == "invalid"
    assert any(v.constraint_kind == "route_structure" for v in verified.violations)
```

`FakeLLM`(Phase 11-3 起源)は `structured=` に固定の応答を1つ渡すだけの単純なスタブ ──
LLM 呼び出しをテスト対象のモジュール名前空間(`route_llm.get_gemini_llm`)で monkeypatch するのは Phase 12/13 と全く同じ手順(モジュールが違うだけ)。

## 4. 実際に Gemini を呼んで初めて判明した罠 ── `problem_type` が LLM に見えてしまう

`test_llm_only_strategies.py` が全て green になったので、実際に `POST /api/v1/compare` を
本物の Gemini で叩いたところ、**6ドメイン全ての LLM Only 試行が例外なく失敗した**:

```text
OutputParserException('Failed to parse RouteSolution from completion
{"problem_type": "shortest_path", "path_node_ids": ["A", "B", "D", "E"], ...}.
Got: 1 validation error for RouteSolution
problem_type
  Input should be 'route_planning' [type=literal_error, input_value='shortest_path', ...]
```

LLM は `path_node_ids`/`total_weight` は正しく埋めているのに、`problem_type` にだけ
無関係な値(`"shortest_path"`)を生成していた。原因を実測で特定した:

1. `RouteSolution.problem_type: Literal["route_planning"] = "route_planning"` を
   `.model_json_schema()` で JSON Schema 化すると、Pydantic v2 は単一値の `Literal` を
   **`"const": "route_planning"`** というキーワードで表現する(`uv run python -c
   "from app.domain.solutions.route_planner import RouteSolution;
   print(RouteSolution.model_json_schema())"` で実測)。
2. `get_gemini_llm(...).with_structured_output(Schema)` は既定で `method="json_schema"`
   を使い、`schema.model_json_schema()` の結果をほぼそのまま `response_json_schema` として
   Gemini API に渡す。**Gemini API 側のスキーマ形式(`types.Schema`)は `enum` はサポート
   するが `const` に対応するフィールドを持たない**。
3. 結果、`"const"` 制約は Gemini 側で静かに無視され、`problem_type` が「自由記述可能な
   文字列フィールド」として LLM に見えてしまう。LLM はもっともらしい別の値を生成し、
   戻ってきた JSON を `RouteSolution` に検証し直す段階(`PydanticOutputParser`)で
   `literal_error` になる。

**これは6ドメイン共通の問題** ── `RouteSolution`/`ShiftSolution`/… は全て
`problem_type: Literal[...] = "..."` という同型の判別子フィールドを持つため、
route で見つかったこの罠は network/shift/travel/project/logistics にもそのまま当てはまる。
`FakeLLM` を使うユニットテストは固定値をそのまま返すだけなので発見できず、**実運用の
LLM 呼び出しで初めて顕在化する**、という種類の問題だった(進行のルール #9 のとおり
検証で見つけた問題は反映してから次に進む)。

対処は 14-1 で追加した `strip_problem_type`(`app/algorithms/llm/common.py`)── `problem_type`
は元々 Verification が判別に使うためだけのフィールドで、LLM が「決める」情報ではない
(README「LLM に最適解を計算させない」の精神にも合う)ため、LLM に渡す構造化出力スキーマ
から動的に除外し、`solve()` 側で固定値を足し戻す。既存6スキーマをそのまま使うという
Phase 14 の設計判断そのものは変えていない。

---

## まとめ

- `LlmOnlyRouteStrategy`/`LlmOnlyNetworkStrategy` は「`strip_problem_type()` で判別子を
  除いたスキーマへの `with_structured_output()` + 同期 `invoke()` + `problem_type` を
  足し戻す」という数行のクラスで済む。設計の重さは Phase 14-1 の土台(既存検証の再利用
  という発見)にすでに前借りされている。
- LLM の自己申告する派生値(`total_weight`)の誤りは、既存の構造検証がそのまま検出する ──
  Algorithm と全く同じ検証コードで LLM 解を検証できることを最初のドメインで確認した。
- `problem_type`(判別子)は LLM に見せてはいけない ── ユニットテストでは検出できず、
  実運用の LLM 呼び出しで初めて分かった Gemini 構造化出力の制限。

## テスト観点(`tests/unit/test_llm_only_strategies.py`)

> **対象**: `LlmOnlyRouteStrategy.solve` / `LlmOnlyNetworkStrategy.solve`
> **ドライバ**: このテスト関数
> **スタブ**: `FakeLLM`(`app.algorithms.llm.route_llm`/`network_llm` の `get_gemini_llm` を
> それぞれ monkeypatch)。`SolutionVerificationService`(Phase 1〜9、無変更)はスタブ不要 ──
> 対象が純粋な検証ロジックで外部依存を呼ばないため。

| ケース                                | 期待                                                     |
| ---------------------------------- | ------------------------------------------------------ |
| route: 正しい経路 + 正しい total_weight    | `verify()` の結果が `status == "valid"`、`violations == []` |
| route: 正しい経路 + 嘘の total_weight     | `status == "invalid"`、`route_structure` 違反を検出          |
| network: 正しい全域木 + 正しい total_weight | `status == "valid"`、`violations == []`                 |
| いずれも                               | `strategy.meta.family == "llm"`(Phase 14-1 の拡張が効いている)  |

```bash
uv run pytest tests/unit/test_llm_only_strategies.py -k "route or network"
uvx pyright app/algorithms/llm/route_llm.py app/algorithms/llm/network_llm.py tests/unit/test_llm_only_strategies.py
```

---

次章([Phase-14-3](./Phase-14-3.md))では、作業単位 14-3 ──
スケジューリング系2ドメイン(shift_scheduling / project_scheduling)を実装する。
