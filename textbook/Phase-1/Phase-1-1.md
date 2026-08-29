# Phase 1-1: 共通スキーマの実装(作業単位 1-1)

## この章のゴール

Phase 0-2 で設計した共通スキーマ ── `OptimizationProblem` / `Constraint` / `Objective` /
`CandidateSolution` ── を `app/domain/` に **型として実装**する。

- `app/domain/problems/` と `app/domain/solutions/` へのファイル分割
- 葉モジュールとアグリゲータ、`__init__.py` の re-export
- Phase 0 スケッチからの変更点: PEP 695 `type` 文、`network_design` は Phase 4 送り
- Input Validation の一部(Pydantic `Field` 制約、`model_validator`)
- 既に書き始めているコードとの差分

**この章で新規作成するファイル**:
`app/domain/problems/{problem,route_planner,shift_scheduler,__init__}.py`(§2 / §4)、
`app/domain/solutions/{solution,route_planner,shift_scheduler,__init__}.py`(§3 / §4)。

対応サンプル: `samples/app/domain/problems/*.py`, `samples/app/domain/solutions/*.py`。
テストは `samples/tests/unit/test_problem_schema.py`。
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
> ストラテジー(Phase 5 の Shift Scheduler)を実装するときに追加する。`Phase-0-2.md` §2.5 /
> `Phase-0-3.md` §2.3 の「Phase 1」表記には `[Phase 1 改訂]` マーカーを付けた。

**依存方向は一方向**: 葉(`route_planner.py` / `shift_scheduler.py`)→
アグリゲータ(`problem.py` / `solution.py`)→ `__init__.py`。葉は互いを import しない。
循環しないので `model_rebuild()` は不要。

**import は絶対 import**(`from app.domain.problems.route_planner import RouteData`)。
bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` になり、
Pylance でも解決できない(`Phase-0-2.md` の Pylance ハマりどころ)。

---

## 2. アグリゲータ ── `problem.py`

> aggregate：集約する

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
`Phase-1-introduction.md` §10 の実装前チェックリスト 1-1 は **「route / shift の 2 problem_type。`network_design` は Phase 4」**
と決めている。Phase 1 では:

- `OptimizationProblem.problem_type` は `Literal["route_planning", "shift_scheduling"]`
- `ProblemData` / `SolutionData` は 2 メンバー
- `app/domain/problems/network_design.py` は作らない

Phase 4 での足し方は §6。

### 2.3 問題の葉モジュール(`route_planner.py` / `shift_scheduler.py`)

問題タイプ固有のデータ形。**葉は兄弟(互いの problem_type)を import しない**。
値域は Pydantic の `Field` に寄せる(`Phase-0-6.md` §2.2「Input Validation は Pydantic に」)。

> `Field` の引数: `ge`=以上 / `gt`=より大きい / `le`=以下 / `lt`=より小さい。

```python
# app/domain/problems/route_planner.py ── Route Planner のグラフ(全文は samples)
class RouteNode(BaseModel):
    id: str
    label: str | None = None
    x: float | None = None            # 座標は A*(Phase 4)のヒューリスティック用で任意
    y: float | None = None

class RouteEdge(BaseModel):
    id: str
    source: str                       # 端点ノードの id
    target: str
    weight: float = Field(ge=0)       # 距離 / 所要時間。負の重みは弾く(Dijkstra の前提)
    directed: bool = False            # False なら source <-> target の双方向

class RouteData(BaseModel):
    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str                        # 出発ノードの id
    goal: str                         # 目標ノードの id
```

```python
# app/domain/problems/shift_scheduler.py ── Shift Scheduler(型のみ。解くのは Phase 5。全文は samples)
class Staff(BaseModel):
    id: str
    name: str | None = None
    hourly_wage: float = Field(ge=0)
    skills: list[str] = Field(default_factory=list)
    available_slot_ids: list[str] = Field(default_factory=list)   # 勤務可能なスロット id
    requested_days_off: list[str] = Field(default_factory=list)   # 希望休(soft 制約と連動)

class ShiftSlot(BaseModel):
    id: str
    day: str                          # "2026-09-01" など
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    required_headcount: int = Field(ge=1)
    required_skills: list[str] = Field(default_factory=list)

class ShiftData(BaseModel):
    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    staff: list[Staff]
    slots: list[ShiftSlot]
    max_weekly_hours: float = 40
    max_consecutive_days: int = 5
```

`OptimizationProblem` を受け取った時点で Pydantic が走るので、型・値域チェックの多くは
「スキーマを定義した時点で完了」する。スロットの `end_hour > start_hour` のような
フィールド間チェックは Phase 2(`model_validator` を足す)。

---

## 3. 解 ── `solutions/`(アグリゲータ + 葉)

### 3.1 アグリゲータ `solution.py`

`AlgorithmMeta` / `ConstraintViolation` / `SolutionData` ユニオン / `CandidateSolution`。
`solutions/route_planner.py` / `shift_scheduler.py`(§3.2)を絶対 import で束ねる。
全文は `samples/app/domain/solutions/solution.py`。

```python
# app/domain/solutions/solution.py
type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns"]
type SolutionStatus = Literal["valid", "invalid", "infeasible"]

class ConstraintViolation(BaseModel):        # Verification が見つけた違反 1 件
    constraint_kind: str
    severity: Literal["hard", "soft"]
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)

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

### 3.2 解の葉モジュール(`solutions/route_planner.py` / `shift_scheduler.py`)

problem_type ごとの解の形。`data`(問題)の葉と対になる。

```python
# app/domain/solutions/route_planner.py
class RouteSolution(BaseModel):
    problem_type: Literal["route_planning"] = "route_planning"
    path_node_ids: list[str]     # 経由順のノード id 列(start で始まり goal で終わる)
    path_edge_ids: list[str]     # 使用したエッジ id 列。不変条件: len = len(path_node_ids) - 1
    total_weight: float          # path_edge_ids の weight 合計

# app/domain/solutions/shift_scheduler.py ── 型のみ。解を作るのは Phase 5
class ShiftSolution(BaseModel):
    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    assignments: dict[str, list[str]]     # slot_id -> [staff_id, ...]
```

- `RouteSolution` の 3 フィールドは Verification([Phase-1-6](./Phase-1-6.md) §3)がすべて照合する
  ── 「`path_edge_ids` が隣接ノード対を結ぶ」「`total_weight` = エッジ weight 合計」など。
- `ShiftSolution` は Phase 1 では**型を用意するだけ**。`Greedy` / `Backtracking` で実際に割当を
  作るのは Phase 5。`SolutionData` ユニオンに載せておくことで、Phase 5 は葉を足すだけで済む。

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

# app/domain/solutions/__init__.py も同じ形
from app.domain.solutions.route_planner import RouteSolution
from app.domain.solutions.shift_scheduler import ShiftSolution
from app.domain.solutions.solution import (
    AlgorithmFamily, AlgorithmMeta, CandidateSolution, ConstraintViolation,
    SolutionData, SolutionStatus,
)

__all__ = ["AlgorithmFamily", "AlgorithmMeta", "CandidateSolution", ...]
```

**「定義」と「re-export」は別物** ── ユニオン(`ProblemData` / `AnyConstraint` /
`SolutionData`)の**定義**は `problem.py` / `solution.py` に置き、`__init__.py` はそれを
**re-export** するだけ(`OptimizationProblem` や `RouteData` を re-export しているのと同じ)。
import は一方向 `__init__.py → problem.py → 葉` なので循環しない。
もし**定義**を `__init__.py` に置くと、`OptimizationProblem`(定義元 `problem.py`)が
`ProblemData` のために `from app.domain.problems import ...` と書かざるを得ず、
`__init__.py` は `OptimizationProblem` を `problem.py` から re-export するので
`problem.py ↔ __init__.py` の循環になる(`Phase-0-2.md` §2.5)。

利用側は `from app.domain.problems import OptimizationProblem, RouteData` と書ける。

---

## 5. 拡張ポイント ── Phase 4 で `network_design` を足す

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

## 6. テスト観点(`samples/tests/unit/test_problem_schema.py`)

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

## 7. まとめ

- 共通スキーマは `app/domain/problems/` と `app/domain/solutions/` に分割。葉 → アグリゲータ →
  `__init__.py` の一方向依存。絶対 import。
- Phase 0 スケッチからの変更: `: TypeAlias` → `type` 文、`network_design` は Phase 4 送り。
- Input Validation は Pydantic の `Field` と `model_validator` に寄せる。
- 書きかけコードは samples で置き換える(`Constraint` 未定義・`uuid` 欠落等を解消)。

次章([Phase-1-2](./Phase-1-2.md))では、作業単位 1-2 ── `AlgorithmStrategy` プロトコルと
`registry` を実装する。
