# Phase 11-1: 抽出・分類スキーマ(作業単位 11-1)

## この章のゴール

Phase 11 全体で使う Structured Output 用の Pydantic スキーマを、LLM もサービスもワークフローも一切使わない**純粋な型定義**として先に固める。Phase 10-1(`apply_overrides` 用スキーマ)やPhase 0(`OptimizationProblem` そのもの)と同じ「まず型を固める」章。

**この章で作成するファイル**: `app/schemas/structuring.py`(新規)、
`tests/unit/test_structuring_schemas.py`(新規)。

---

## 1. なぜ「LLM向け簡易スキーマ」を別に作るのか

既存の `AnyConstraint`(`app/domain/problems/problem.py`)は5サブタイプの判別可能ユニオンで、各サブタイプは異なるフィールド集合を持つ(`NumericBoundConstraint` は `field`/`operator`/`value`、`RequiredInclusionConstraint`/`ForbiddenConstraint` は `items`、等)。LLM のStructured Output は「1つの固定スキーマ」を渡す必要があり、実行時に判別可能ユニオンをそのまま渡すことはできない。そこで `ExtractedConstraint` という**全サブタイプのフィールドを1つに平らにした簡易スキーマ**を用意し、`kind` で判別する:

```python
# app/schemas/structuring.py(要点)
class ExtractedConstraint(BaseModel):
    """AnyConstraint の全サブタイプのフィールドを1つに平らにした LLM向け簡易スキーマ。
    kind で判別し、model_dump(exclude_none=True) がそのまま AnyConstraint の
    discriminated union に再パースできる形にする(専用の変換関数を書かない)。"""

    kind: Literal["forbidden", "numeric_bound", "required_inclusion", "staffing", "generic"]
    severity: Literal["hard", "soft"] = "hard"
    penalty: float | None = None
    description: str | None = None
    items: list[str] | None = None       # forbidden / required_inclusion 用
    field: str | None = None             # numeric_bound 用
    operator: Literal["<=", ">=", "==", "<", ">"] | None = None
    value: float | None = None
```

**非自明な判断**: `model_dump(exclude_none=True)` を呼ぶと、LLM が触れなかったフィールド(None のまま)が dict から消える。`AnyConstraint` の各サブタイプは自分が使わないフィールドを持たないため、この dict はそのまま `left_to_right` union の再パースに使える ── 専用の「ExtractedConstraint → 具体的な Constraint サブタイプ」変換関数を書かずに済む(11-2 の`build_overrides` がこれをそのまま利用する)。

---

## 2. `ExtractedObjective` ── `Objective` と同型

```python
class ExtractedObjective(BaseModel):
    """Objective と同型。model_dump() がそのまま Objective の初期化引数になる。"""

    sense: Literal["minimize", "maximize"]
    target: str
    weight: float = 1.0
    description: str | None = None
```

`Objective` をそのまま Structured Output のスキーマにできない理由は無い(構造が同じ)が、「LLM が返すスキーマ」と「ドメインの正スキーマ」を型として分離しておくことで、将来ドメイン側の `Objective` にフィールドを足しても LLM 抽出契約を壊さない(疎結合)。

---

## 3. ドメイン別 Data Patch ── 実フィールドの確認

各 `*DataPatch` は対応する `*Data`(`app/domain/problems/*.py`)の**トップレベル・スカラーだけ**を Optional で抜き出したもの。カタログ(list)フィールドは含めない(11-2 のベース問題が引き継ぐ)。実フィールドは既存コードを確認して決める:

| ドメイン               | `*Data` のトップレベル・スカラー                                                                      | Patch                                     |
| ------------------ | ----------------------------------------------------------------------------------------- | ----------------------------------------- |
| route_planning     | `start: str`、`goal: str`、`allow_negative: bool`                                           | `RouteDataPatch`                          |
| travel_planning    | `budget: float`、`time_budget: float`、`start: str \| None`、`preferences: dict[str, float]` | `TravelDataPatch`                         |
| shift_scheduling   | `max_weekly_hours: float`、`max_consecutive_days: int`                                     | `ShiftDataPatch`                          |
| project_scheduling | `resource_capacity: int \| None`                                                          | `ProjectDataPatch`                        |
| logistics_planning | `depot_id: str`                                                                           | `LogisticsDataPatch`                      |
| network_design     | (トップレベル・スカラー無し)                                                                           | Patch クラス無し(11-2 の `EXTRACTORS` で `None`) |

```python
class RouteDataPatch(BaseModel):
    start: str | None = None
    goal: str | None = None
    allow_negative: bool | None = None

class TravelDataPatch(BaseModel):
    budget: float | None = None
    time_budget: float | None = None
    start: str | None = None
    preferences: dict[str, float] | None = None

class ShiftDataPatch(BaseModel):
    max_weekly_hours: float | None = None
    max_consecutive_days: int | None = None

class ProjectDataPatch(BaseModel):
    resource_capacity: int | None = None

class LogisticsDataPatch(BaseModel):
    depot_id: str | None = None
```

全フィールド Optional にする理由: LLM が要求文から読み取れなかったフィールドは
「触れない」(= None のまま)ことを表現するため。`model_dump(exclude_unset=True)`(11-5 の`extract_domain_data` が使う)で、LLM が実際に設定したフィールドだけが overrides に乗る。

---

## 4. Structuring API のリクエスト/レスポンス

```python
class StructuringRequest(BaseModel):
    text: str
    conversation_id: uuid.UUID | None = None

class StructuringResponse(BaseModel):
    conversation_id: uuid.UUID
    problem_type: ProblemTypeLiteral
    problem: OptimizationProblem      # そのまま POST /api/v1/solve に渡せる
    notes: list[str] = Field(default_factory=list)
```

`problem: OptimizationProblem` ── README「LLM Service はスキーマ経由でのみ Algorithm Engineと接続する」を体現する1行。`notes` は抽出時の非自明な判断(例: 「目的を抽出できず既定値を使用した」)を人間に伝える補助情報(11-6 の `assemble_problem` が付ける)。

---

## まとめ

- LLM が Structured Output で扱えるのは「平らな1スキーマ」だけ ── 判別可能ユニオンは`ExtractedConstraint` のような簡易スキーマに平らにし、`kind` で判別・再パースする。
- ドメイン別 `*DataPatch` は各 `*Data` のトップレベル・スカラーだけを Optional で写す。network_design のようにトップレベル・スカラーを持たないドメインは Patch クラス自体を作らない(11-2 で `EXTRACTORS` に `None` を登録する伏線)。
- 全フィールド Optional + `exclude_unset=True` で「LLM が触れなかったフィールド」を区別できるようにする ── これが11-6 の「LLM が埋めてよいのはここまで」という設計原則を型レベルで支える。

## テスト観点(`tests/unit/test_structuring_schemas.py`)

> **対象**: `app.schemas.structuring` の各 `BaseModel`(型定義のみ)
> **ドライバ**: このテスト関数
> **スタブ**: 不要 ── 対象が純粋なデータ定義で外部依存を呼ばないため(#14)

| ケース                                                                                                            | 期待                                                                                                              |
| -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `ProblemTypeClassification(problem_type="unknown_type")`                                                       | `ValidationError`(6種の Literal 以外は型として弾かれる)                                                                      |
| `Objective(**ExtractedObjective(...).model_dump())`                                                            | 正しく `Objective` が構築できる                                                                                          |
| `ExtractedConstraint(kind="required_inclusion", items=["A"])` を `constraints=[...]` に渡した `OptimizationProblem` | `problem.constraints[0]` が `RequiredInclusionConstraint` のインスタンス(`numeric_bound`/`forbidden`/`staffing` も同様に検証) |
| `ExtractedConstraint(kind="staffing").model_dump(exclude_none=True)`                                           | `{"kind": "staffing", "severity": "hard"}`(未設定フィールドが現れない)                                                       |
| 各 `*DataPatch()`(何も指定しない)                                                                                      | `model_dump(exclude_unset=True) == {}`                                                                          |
| `RouteDataPatch(start="X")`                                                                                    | `model_dump(exclude_unset=True) == {"start": "X"}`                                                              |
| `StructuringRequest`/`StructuringResponse` の構築                                                                 | 正常に構築できる                                                                                                        |

`uv run pytest tests/unit/test_structuring_schemas.py` / `uvx pyright app/schemas/structuring.py`。

---

次章([Phase-11-2](./Phase-11-2.md))では、作業単位 11-2 ── problem_type ごとの「ベース問題」
と、`EXTRACTORS` レジストリ・`build_overrides`・`ground_references` を実装する。
