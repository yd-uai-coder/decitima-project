# Phase 1-2: 共通スキーマの実装(作業単位 1-1)

## この章のゴール

Phase 0-2 で設計した共通スキーマ ── `OptimizationProblem` / `Constraint` / `Objective` /
`CandidateSolution` ── を `app/domain/` に **型として実装**する。

- `app/domain/problems/` と `app/domain/solutions/` へのファイル分割
- 葉モジュールとアグリゲータ、`__init__.py` の re-export
- Phase 0 スケッチからの変更点: PEP 695 `type` 文、`network_design` は Phase 4 送り
- Input Validation の一部(Pydantic `Field` 制約、`model_validator`)
- 既に書き始めているコードとの差分

対応サンプル: `samples/app/domain/**`、テストは `samples/tests/unit/test_problem_schema.py`。
設計の背景は `Phase-0-2.md`(特に §2.5 ファイル構成、§4 制約、§4.4 `AnyConstraint`)。

---

## 1. ファイル構成

`Phase-0-2.md` §2.5 のとおり、**「一緒に変わるものを同じファイルに」** で分割する。

```text
app/domain/
├── problems/
│   ├── __init__.py          re-export + __all__(公開窓口)
│   ├── problem.py           Objective / ConstraintBase(+ サブタイプ)/ GenericConstraint /
│   │                        AnyConstraint / ProblemData ユニオン / OptimizationProblem
│   ├── route_planner.py     RouteNode / RouteEdge / RouteData        (葉。兄弟を import しない)
│   └── shift_scheduler.py   Staff / ShiftSlot / ShiftData            (葉)
├── solutions/
│   ├── __init__.py          re-export + __all__
│   ├── solution.py          AlgorithmMeta / ConstraintViolation / SolutionData ユニオン /
│   │                        CandidateSolution
│   ├── route_planner.py     RouteSolution                            (葉)
│   └── shift_scheduler.py   ShiftSolution                            (葉)
```

> `app/domain/objectives/`(多目的の重み付き和の評価器)は **Phase 1 では作らない**。
> Phase 1 で registry に載る `DijkstraStrategy` は単一目的で消費者がいないため。初の多目的
> ストラテジー(Phase 5 の Shift Scheduler)を実装するときに追加する。`Phase-0-2.md` §3 /
> `Phase-0-3.md` §2.3 の「Phase 1」表記はこの回で Phase 5 扱いに訂正した。

**依存方向は一方向**: 葉(`route_planner.py` / `shift_scheduler.py`)→
アグリゲータ(`problem.py` / `solution.py`)→ `__init__.py`。葉は互いを import しない。
循環しないので `model_rebuild()` は不要。

**import は絶対 import**(`from app.domain.problems.route_planner import RouteData`)。
bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` になり、
Pylance でも解決できない(`Phase-0-2.md` の Pylance ハマりどころ)。

---

## 2. アグリゲータ ── `problem.py`

葉を絶対 import で束ね、ユニオンを組む。全文は `samples/app/domain/problems/problem.py`。要点:

```python
# app/domain/problems/problem.py
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.problems.route_planner import RouteData      # 葉を絶対 import
from app.domain.problems.shift_scheduler import ShiftData


class ConstraintBase(BaseModel):
    """全サブタイプ共通のフィールドだけ。判別子 kind は各サブタイプが宣言する。"""
    severity: Literal["hard", "soft"] = "hard"
    penalty: float | None = None
    description: str | None = None


class ForbiddenConstraint(ConstraintBase):
    kind: Literal["forbidden"] = "forbidden"   # ← 判別子はサブタイプ側
    items: list[str]

# ... NumericBoundConstraint / RequiredInclusionConstraint / StaffingConstraint / GenericConstraint


# constraints の1要素の型。左から順に検証、未知 kind は末尾の GenericConstraint にフォールバック
type AnyConstraint = Annotated[
    NumericBoundConstraint | RequiredInclusionConstraint | ForbiddenConstraint
    | StaffingConstraint | GenericConstraint,
    Field(union_mode="left_to_right"),
]

# problem_type を判別子にした判別可能ユニオン
type ProblemData = Annotated[RouteData | ShiftData, Field(discriminator="problem_type")]


class OptimizationProblem(BaseModel):
    problem_type: Literal["route_planning", "shift_scheduling"]
    objectives: list[Objective]
    constraints: list[AnyConstraint] = Field(default_factory=list)
    data: ProblemData
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _problem_type_matches_data(self) -> "OptimizationProblem":
        # トップの problem_type と data.problem_type の不一致を早期に弾く(Input Validation)
        if self.problem_type != self.data.problem_type:
            raise ValueError("problem_type does not match data.problem_type")
        return self
```

### 2.1 Phase 0 スケッチからの変更 ①: `: TypeAlias` → `type` 文

`Phase-0-2.md` §4.4 では `AnyConstraint: TypeAlias = Annotated[...]` と書いていた。Phase 1 では
**PEP 695 の `type` 文**(`type AnyConstraint = Annotated[...]`)に変える。

- ruff の `UP040` が `: TypeAlias` を非推奨とし、`type` 文を推奨する。
- `type` 文は「これは型エイリアス」という宣言そのものなので、pyright は
  `Annotated[..., Field(...)]` を確実に型として扱う(`: TypeAlias` が必要だった理由が消える)。
- Pydantic v2(2.13+)は `type` 文の判別可能ユニオン・`union_mode` を正しく解決する
  (samples で実機確認済み)。

`decitima-api` は既に PEP 695 ジェネリクス(`CRUDRepository[ModelType: Base]`)を使っており一貫する。

### 2.2 Phase 0 スケッチからの変更 ②: `network_design` は Phase 4

Phase 0 の `samples/problem_schema.py` はユニオンに `NetworkDesignData`(MST 用)を含めていたが、
`phase-0-index.md` の 1-1 は **「MVP は route / shift の 2 つ。`network_design` の型は Phase 4 で足す」**
と決めている。Phase 1 では:

- `OptimizationProblem.problem_type` は `Literal["route_planning", "shift_scheduling"]`
- `ProblemData` / `SolutionData` は 2 メンバー
- `app/domain/problems/network_design.py` は作らない

Phase 4 での足し方は §6。

### 2.3 `Field` 制約(Input Validation の一部)

`Phase-0-6.md` §2.2「Input Validation は Pydantic に寄せる」。葉モデルに値域を付ける:

```python
# app/domain/problems/route_planner.py
class RouteEdge(BaseModel):
    weight: float = Field(ge=0)          # 負の重みは弾く(Dijkstra の前提)

# app/domain/problems/shift_scheduler.py
class ShiftSlot(BaseModel):
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    required_headcount: int = Field(ge=1)
```

`OptimizationProblem` を受け取った時点で Pydantic が走るので、型・値域チェックの多くは
「スキーマを定義した時点で完了」する。スロットの `end_hour > start_hour` のような
フィールド間チェックは Phase 2(`model_validator` を足す)。

---

## 3. 解 ── `solution.py`

`AlgorithmMeta` / `ConstraintViolation` / `SolutionData` ユニオン / `CandidateSolution`。
全文は `samples/app/domain/solutions/solution.py`。

```python
# app/domain/solutions/solution.py
type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns"]
type SolutionStatus = Literal["valid", "invalid", "infeasible"]

class AlgorithmMeta(BaseModel):
    name: str                       # "dijkstra"
    family: AlgorithmFamily         # app/algorithms/ の 5 サブパッケージと 1 対 1
    implementation: str             # "handwritten" / "library:networkx" ...
    time_complexity: str | None = None
    space_complexity: str | None = None

type SolutionData = Annotated[RouteSolution | ShiftSolution, Field(discriminator="problem_type")]

class CandidateSolution(BaseModel):
    problem_ref: uuid.UUID | None = None    # 永続化時は Problem.id、単発は None
    status: SolutionStatus
    assignments: SolutionData
    metrics: dict[str, float] = Field(default_factory=dict)   # {"total_weight": 9}。_ops 等も可
    violations: list[ConstraintViolation] = Field(default_factory=list)
    produced_by: AlgorithmMeta              # 比較可能性(NFR-3)/ 説明可能性(NFR-4)の土台
```

`family` を `Literal` にしておくと、`app/algorithms/` のサブパッケージ名(`search` / `graph` /
`optimization` / `scheduling` / `patterns`)以外を弾ける。

---

## 4. `__init__.py` ── 公開窓口

分割ファイルの内訳を利用側に見せない。既存 `app/models/__init__.py` と同じく
明示 import + `__all__`(ruff F401 対策)。

```python
# app/domain/problems/__init__.py
from app.domain.problems.problem import (
    AnyConstraint, ConstraintBase, ForbiddenConstraint, GenericConstraint,
    NumericBoundConstraint, Objective, OptimizationProblem, ProblemData,
    RequiredInclusionConstraint, StaffingConstraint,
)
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff

__all__ = ["AnyConstraint", "ConstraintBase", ...]  # 全 export 名
```

**ユニオン(`ProblemData` / `AnyConstraint`)を `__init__.py` に置かない**。
`__init__.py` は `OptimizationProblem` も re-export するため、その定義元の `problem.py` が
`__init__.py` を import すると循環する(`Phase-0-2.md` §2.5)。

利用側は `from app.domain.problems import OptimizationProblem, RouteData` と書ける。

---

## 5. 既に書き始めたコードとの差分

`app/domain/problems/` には未コミットの書きかけがある。samples が正。主な差分:

| 箇所 | 現状 | samples(正) |
| --- | --- | --- |
| `problems/__init__.py` | `Constraint` を import(未定義)→ `ImportError` | `ConstraintBase` を import。`GenericConstraint` も `__all__` に |
| `problem.py` の `problem_type` | `Literal[...]` が 2 値だがユニオンは 3 メンバー | ユニオンも 2 メンバー(`network_design` は Phase 4) |
| `problem.py` の型エイリアス | `AnyConstraint: TypeAlias = ...` | `type AnyConstraint = ...` |
| `problem.py` の一致チェック | なし | `model_validator` で `problem_type == data.problem_type` |
| `solutions/solution.py` | `import uuid` 欠落 / `SolutionData` 未定義 / 末尾に迷子コメント | `uuid` を import、`SolutionData` ユニオンを定義、葉 2 ファイルを作成 |
| `solutions/route_planner.py` `solutions/shift_scheduler.py` | 未作成 | `RouteSolution` / `ShiftSolution` |
| `network_design.py`(problems / solutions) | problems 側に作成済み | Phase 1 では削除(Phase 4 で復活) |

写経は「samples の該当ファイルで置き換える」。書きかけは残さない。

---

## 6. 拡張ポイント ── Phase 4 で `network_design` を足す

`Phase-0-2.md` §8.1 のとおり、既存に触れず追加できる:

```python
# app/domain/problems/network_design.py(葉。新規)
class NetworkDesignData(BaseModel):
    problem_type: Literal["network_design"] = "network_design"
    nodes: list[NetworkNode]
    links: list[NetworkLink]

# app/domain/problems/problem.py(ユニオンに 1 項目)
from app.domain.problems.network_design import NetworkDesignData
type ProblemData = Annotated[
    RouteData | ShiftData | NetworkDesignData, Field(discriminator="problem_type")
]
```

`OptimizationProblem.problem_type` の `Literal` にも `"network_design"` を足す。
`route_planning` / `shift_scheduling` のコードには一切触れない ── これがハイブリッド設計の狙い。

---

## 7. テスト観点(`samples/tests/unit/test_problem_schema.py`)

- `build_route_problem()` / `build_shift_problem()`(`tests/fixtures/optimization.py`)で
  各サブタイプが正しく構築される
- discriminated union が `problem_type` で正しいサブモデルを選ぶ(`isinstance` で確認)
- 既知 kind の dict → 専用サブタイプ、未知 kind → `GenericConstraint` フォールバック
- 負のエッジ weight は `ValidationError`
- `problem_type != data.problem_type` は `ValidationError`
- `CandidateSolution` は `produced_by` 必須
- `model_dump(mode="json")` → `model_validate` で往復して等価

`uv run pytest tests/unit/test_problem_schema.py` と、可能なら `uvx pyright app/domain`
(standard, 0 errors)。

---

## 8. まとめ

- 共通スキーマは `app/domain/problems/` と `app/domain/solutions/` に分割。葉 → アグリゲータ →
  `__init__.py` の一方向依存。絶対 import。
- Phase 0 スケッチからの変更: `: TypeAlias` → `type` 文、`network_design` は Phase 4 送り。
- Input Validation は Pydantic の `Field` と `model_validator` に寄せる。
- 書きかけコードは samples で置き換える(`Constraint` 未定義・`uuid` 欠落等を解消)。

次章([Phase-1-3](./Phase-1-3.md))では、作業単位 1-2 ── `AlgorithmStrategy` プロトコルと
`registry` を実装する。
