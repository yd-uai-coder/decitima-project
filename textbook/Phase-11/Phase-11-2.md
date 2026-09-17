# Phase 11-2: ベース問題 + `EXTRACTORS`/`build_overrides`/`ground_references`(作業単位 11-2)

## この章のゴール

Phase 11 の中核機構 ──「LLM はカタログを発明しない。既存のベース問題から引き継ぐ」を実装する。problem_type ごとの「ベース問題」、ドメイン別ディスパッチテーブル `EXTRACTORS`、LLM の抽出結果を`apply_overrides`(Phase 10)に渡せる形へ組み立てる `build_overrides`、そして既存`ProblemValidationService` の穴(id 参照の実在性を検査しない)を塞ぐ `ground_references` を作る。
この章はすべて純粋関数・純粋データで、LLM も DB も一切呼ばない。

**この章で作成するファイル**: `app/domain/problems/base_problems.py`(新規)、
`app/services/structuring.py`(新規、この章の分だけ)、`tests/unit/test_structuring_base_problems.py`・
`tests/unit/test_structuring_overrides.py`(新規)。

---

## 1. ベース問題 ── `tests/fixtures/optimization.py` とは別の資産

```python
# app/domain/problems/base_problems.py(要点)
_TRAVEL_BASE = OptimizationProblem(
    problem_type="travel_planning",
    objectives=[Objective(sense="maximize", target="total_value")],
    data=TravelData(
        places=[
            Place(id="P0", name="宿", value=0, cost=0, duration=0),
            Place(id="P1", name="浅草", value=10, cost=0, duration=2),
            # ... P2〜P4
        ],
        legs=[...],
        budget=15000, time_budget=16, start="P0", preferences={},
    ),
)

BASE_PROBLEMS: dict[str, OptimizationProblem] = {
    "route_planning": _ROUTE_BASE,
    "network_design": _NETWORK_DESIGN_BASE,
    "shift_scheduling": _SHIFT_BASE,
    "travel_planning": _TRAVEL_BASE,
    "project_scheduling": _PROJECT_BASE,
    "logistics_planning": _LOGISTICS_BASE,
}

def get_base_problem(problem_type: str) -> OptimizationProblem:
    """problem_type に対応するベース問題を、呼び出しごとに独立した deep copy で返す。"""
    return BASE_PROBLEMS[problem_type].model_copy(deep=True)
```

**なぜ `tests/fixtures/optimization.py` の `build_*_problem` と共有しないか**(進行のルール#17): 実消費者が違う。テスト用ビルダーはテストの意図(forbidden/required 制約を差し替えて色々なケースを作る)に最適化されており、本番のベース問題(「この problem_type の標準的な既存問題」)とは役割が異なる。片方の変更がもう片方に波及する結合は望ましくない。

**`travel_planning` のベース問題は README §3.1 の例を意識している**: 「5万円以内で東京を2日間旅行したい。浅草には必ず行きたい。」を実演できるよう、`P1` の id/name を「浅草」にしている(11-4 のグラウンディング用プロンプトで `P1: 浅草` という形で LLM に提示される)。

`get_base_problem` は**呼び出しごとに deep copy を返す**(モジュール定数を直接返さない)──呼び出し元(11-3 の `load_base_problem`)がその後 `apply_overrides` で新しい `OptimizationProblem`を作るとはいえ、元の `BASE_PROBLEMS` 定数が誤って書き換えられる事故を型で防ぐ。

---

## 2. `EXTRACTORS` ── `app/algorithms/registry.py` と同型のディスパッチテーブル

```python
# app/services/structuring.py(要点)
EXTRACTORS: dict[str, type[BaseModel] | None] = {
    "route_planning": RouteDataPatch,
    "network_design": None,               # トップレベル・スカラー無し → LLM を呼ばない
    "shift_scheduling": ShiftDataPatch,
    "travel_planning": TravelDataPatch,
    "project_scheduling": ProjectDataPatch,
    "logistics_planning": LogisticsDataPatch,
}
```

`app/algorithms/registry.py::REGISTRY`(problem_type → アルゴリズム候補)と同じ「1行足すだけで拡張できる」設計。`network_design` に `None` を登録しておくことで、11-5 の`extract_domain_data` は「該当スキーマが無ければ LLM を呼ばず空パッチを返す」という分岐を関数内の1箇所に閉じ込められる(グラフの分岐エッジを増やさずに済む ── 11-6 で詳述)。

---

## 3. `build_overrides` ── objectives が空なら「抽出できなかった」とみなす

```python
def build_overrides(
    objectives_patch: list[ExtractedObjective],
    constraints_patch: list[ExtractedConstraint],
    data_patch: dict[str, Any],
) -> dict[str, Any]:
    overrides: dict[str, Any] = {
        "constraints": [c.model_dump(exclude_none=True) for c in constraints_patch]
    }
    if objectives_patch:
        overrides["objectives"] = [o.model_dump() for o in objectives_patch]
    if data_patch:
        overrides["data"] = data_patch
    return overrides
```

**非自明な判断**: `objectives` キーは `objectives_patch` が空なら overrides に含めない。
`apply_overrides`(Phase 10)は JSON Merge Patch なので、キーが無ければそのフィールドはベースの値のまま ── つまり「LLM が目的を1つも抽出できなかった」場合、ベース問題の既定目的(例: travel の「価値を最大化」)が生き残る。**objectives が空欄で消失するのを防ぐ**、この非自明な判断は11-6 の `assemble_problem` が `notes` に記録する。

`constraints` は逆に**常に**キーを含める ── 空リストも「この要求には特別な制約が無い」という正当な意味を持つため、抽出できなかった場合と区別する必要が無い(objectives と非対称な扱いになる理由)。

---

## 4. `catalog_ids` / `ground_references` ── 既存 Validation の穴を塞ぐ

```python
def catalog_ids(problem: OptimizationProblem) -> set[str]:
    """problem.data のカタログが持つ id を全て集める(ドメインごとに isinstance で分岐)。"""
    data = problem.data
    if isinstance(data, RouteData):
        return {n.id for n in data.nodes} | {e.id for e in data.edges}
    if isinstance(data, TravelData):
        return {p.id for p in data.places} | {leg.id for leg in data.legs}
    # ... 他4ドメイン
    return set()


def ground_references(problem: OptimizationProblem, ids: set[str]) -> list[str]:
    """LLM が生成した id 参照(constraints の items、data の単一 id 参照フィールド)が
    カタログに実在するかを確認する。"""
    issues: list[str] = []
    for c in problem.constraints:
        if isinstance(c, (RequiredInclusionConstraint, ForbiddenConstraint)):
            issues.extend(
                f"{c.kind} constraint references unknown id {item!r}"
                for item in c.items if item not in ids
            )
    # route の start/goal、travel の start、logistics の depot_id も同様にチェック
    ...
    return issues
```

**なぜこれが必要か**: 既存 `ProblemValidationService`(Phase 0〜9)は `RequiredInclusionConstraint.
items` 等の id がカタログに実在するかを検査しない ──
`ForbiddenConstraint` の `items` は到達可能性計算(`route_reachable` 等)に使われるだけで、存在チェックはしていない。一方、`RequiredInclusionConstraint.items` を実際に消費するのは
`app/domain/constraints/required_inclusion.py::check_required_inclusion` で、これは解の
`selected_place_ids`/`path_node_ids` のような**id の集合**と突き合わせる。もし LLM が
名前(「浅草」)を id の代わりに出力してしまうと、この突き合わせは常に不一致(missing 扱い)になる ── **黙って要求が無視される**、README「LLM 出力は常に信頼しない」に反する静かな不具合。`ground_references` はこれを検知する最後の砦(11-6 の `validate_problem` で既存 `ProblemValidationError` を使って弾く。新しい例外クラスは増やさない)。

**名前(name/label)は対象外**: `catalog_entries`(11-4 で追加)がプロンプトに `id: name` の対応表を渡すので、LLM は id を選べるはずという契約になっている。`ground_references` はその契約が守られているかだけを見る ── 名前が紛れ込んだ場合は「実在しない id」と同じ扱いで弾く(id と name の両方を許容する設計にはしない。理由は downstream が id でしか突き合わせないため、名前を許すと「グラウンディングは通ったが実際には機能しない」という中途半端な状態を作ってしまう)。

---

## まとめ

- ベース問題(problem_type ごとに1件)が「LLM が埋めないカタログ」の唯一の出所になる。
- `EXTRACTORS` はドメインごとの抽出深さの違いを1つのレジストリで表現する(`network_design`は `None` = LLM を呼ばない)。
- `build_overrides` は「objectives が空なら維持、constraints は常に反映」という非対称な判断を1箇所に集約する。
- `ground_references` は既存 Validation では検知できない「LLM のハルシネーション」を捕まえる
  Phase 11 専用の防御線。新しい例外クラスは増やさない。

## テスト観点(`tests/unit/test_structuring_base_problems.py` / `tests/unit/test_structuring_overrides.py`)

> **対象**: `get_base_problem`/`BASE_PROBLEMS`、`EXTRACTORS`/`build_overrides`/`catalog_ids`/`catalog_ids`/`ground_references`(いずれも純粋関数)
> **ドライバ**: このテスト関数。`ground_references` は Phase 10 の `apply_overrides` と組み合わせ、LLM 無しで「抽出結果 → overrides → マージ済み問題」の一連を再現する
> **スタブ**: 不要 ── 対象・依存(Phase 10 `apply_overrides`)とも純粋

| ケース                                          | 期待                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------- |
| `get_base_problem(pt)` を6種の problem_type で呼ぶ | `problem.problem_type == pt`、既存 `ProblemValidationService().validate()` を通る(回帰) |
| `get_base_problem` を2回呼ぶ                     | 別インスタンス(`is not`)、片方を書き換えても他方・`BASE_PROBLEMS` は不変                               |
| `EXTRACTORS` の6キー                            | `network_design` だけ `None`、他は対応する `*DataPatch` クラス                              |
| `build_overrides([], [], {})`                | `"objectives"` キーを含まない、`"constraints": []`                                      |
| `build_overrides([obj], [], {})`             | `"objectives"` キーを含む                                                            |
| `build_overrides([], [], {"start": "A"})`    | `"data": {"start": "A"}`                                                        |
| `catalog_ids(travel ベース問題)`                  | `"P1"` を含む(id)、`"L..."` で始まる leg id を含む                                         |
| `ground_references`(items=["浅草"]、travel)     | 「浅草」を含む issue(名前は弾かれる)                                                          |
| `ground_references`(items=["P1"]、travel)     | `[]`(実在する id なので issue なし)                                                      |
| `ground_references`(route の start="Z")       | `"start"` を含む issue                                                             |

`uv run pytest tests/unit/test_structuring_base_problems.py tests/unit/test_structuring_overrides.py` /
`uvx pyright app/domain/problems/base_problems.py app/services/structuring.py`。

---

次章([Phase-11-3](./Phase-11-3.md))では、作業単位 11-3 ── `GraphState` の再設計と、
既存(テンプレート由来)の Web検索QAチャットワークフローの全面置き換えに着手する。
