# Phase 0-2: ドメインモデル ── 共通スキーマ

## この章のゴール

LLM(将来)と Algorithm Engine の間に置く「共通言語」= **共通スキーマ**を設計する。

- `OptimizationProblem` ── 問題定義
- `Objective` ── 目的(何を最小化 / 最大化するか)
- `Constraint` ── 制約(守るべき条件)
- `CandidateSolution` ── 候補解

設計後、Route Planner と Shift Scheduler の両方を実際にこのスキーマで書き下し、
「本当に表現できるか」を確認する。

対応するサンプルコードは `samples/problem_schema.py`(Pydantic スケッチ)。
実装時のファイル分割は §2.5「ファイル構成」を参照。以降の各コードブロックは
先頭に配置先ファイルのパスをコメントで示す。

---

## 1. なぜ「共通スキーマ」が必要なのか

### 1.1 共通スキーマがないとどうなるか

LLM と各アルゴリズムを直接つなぐと、次のような密結合が生まれる。

```
LLM ──「Dijkstra 用の入力」を作る ──▶ Dijkstra 実装
LLM ──「シフト用の入力」を作る   ──▶ バックトラッキング実装
LLM ──「ナップサック用の入力」   ──▶ DP 実装
```

- アルゴリズムを 1 つ足すたびに LLM 側のプロンプト / 変換ロジックを直す。
- アルゴリズムを差し替えると LLM 側も壊れる。
- 「同じ問題を別アルゴリズムで解いて比較」ができない(入力形式が違うから)。

### 1.2 共通スキーマを挟むと

```
LLM ──▶ OptimizationProblem ──▶ [ Dijkstra / A* / BFS ]
                              ──▶ [ 貪欲 / バックトラッキング / CP-SAT ]
```

- LLM の仕事は「`OptimizationProblem` を作る」ただ 1 つ。
- アルゴリズムの仕事は「`OptimizationProblem` を受けて `CandidateSolution` を返す」ただ 1 つ。
- 両者は互いを知らない。間にスキーマがあるだけ。
- 同じ `OptimizationProblem` を複数アルゴリズムに渡せる → 比較 (NFR-3) が自然にできる。

これは一種の **ポート & アダプタ / 依存性逆転**。スキーマという安定した契約に
双方が依存し、互いには依存しない。

---

## 2. 設計方針 ── 「ハイブリッド」型

共通スキーマの型の強さには 3 つの選択肢があった。

| 方針             | 内容                                                   | 問題点                              |
| -------------- | ---------------------------------------------------- | -------------------------------- |
| ジェネリック         | `variables` / `constraints` を `dict` / `list[Any]` に | 型の恩恵ゼロ。実行時まで誤りに気づけず、検証コードが膨らむ    |
| 問題タイプごとに別モデル   | `RouteProblem` / `ShiftProblem` を無関係に定義              | 「共通スキーマ」という設計思想が崩れ、エンジンの汎用化ができない |
| **ハイブリッド(採用)** | 共通の骨格は型付き、問題固有の部分は `data` に型付きで格納                    | やや記述量が増えるが、型安全と汎用性を両立            |

### ハイブリッドの構造

```
OptimizationProblem
├── problem_type : "route_planning" | "shift_scheduling" | ...   ← 判別子(discriminator)
├── objectives   : list[Objective]        ← 全 problem_type 共通の語彙
├── constraints  : list[AnyConstraint]    ← 全 problem_type 共通の語彙(hard / soft)
├── data         : RouteData | ShiftData | ...   ← problem_type 固有・型付き
└── metadata     : dict[str, Any]         ← 任意の補足情報
```

- **`objectives（目的）` と `constraints（制約）` は共通語彙**。「最小化 / 最大化」「hard / soft」という
  概念はどの問題にも共通するので、ここで型付きにする。これが LLM ↔ Algorithm の
  真の「共通言語」。
- **`data` は問題固有**。経路問題の「ノードとエッジ」とシフト問題の「スタッフとスロット」は
  本質的に別物。無理に共通化せず、`problem_type` を判別子にした
  **判別可能ユニオン(discriminated union)** にする。Pydantic v2 の
  `Field(discriminator=...)` で表現できる。

### 2.5 ファイル構成

この章のコードは説明のため 1 まとめに見えるが、**実装時は次のように分割する**
(配置先は Phase 0-3 §2.4 のとおり `app/domain/`。`app/schemas/` は HTTP 境界専用)。

```
app/domain/
├── problems/
│   ├── __init__.py            re-export + __all__
│   ├── problem.py             Objective / ConstraintBase(+サブタイプ)/ GenericConstraint /
│   │                          AnyConstraint / ProblemData(判別可能ユニオン)/ OptimizationProblem
│   ├── route_planner.py       RouteNode / RouteEdge / RouteData        （葉。兄弟を import しない）
│   ├── shift_scheduler.py     Staff / ShiftSlot / ShiftData            （葉）
│   └── network_design.py      NetworkNode / NetworkLink / NetworkDesignData  （葉。Phase 5 / MST）
├── solutions/
│   ├── __init__.py            re-export + __all__
│   ├── solution.py            AlgorithmMeta / ConstraintViolation /
│   │                          SolutionData(判別可能ユニオン)/ CandidateSolution
│   ├── route_planner.py       RouteSolution                            （葉）
│   ├── shift_scheduler.py     ShiftSolution                            （葉）
│   └── network_design.py      NetworkDesignSolution                    （葉。Phase 5 / MST）
├── constraints/               ← Phase 2。kind ごとのチェッカー関数。型は置かない
└── objectives/                ← 重み付き和の評価器。型は置かない
```

> **[Phase 6 で確定 ── 実装済み]** このディレクトリ構成のうち `constraints/` は Phase 2-3、
> `objectives/`(`weighted_sum` = 重み付き和の評価器)は **Phase 6-1 で実装済み**(当初は両方
> Phase 1 の予定だった)。`objectives/` を後ろ倒しにした理由: Phase 1 で registry に載る唯一の
> strategy(Dijkstra)は単一目的で消費者がいないため ── Phase 6 の Shift Scheduler が初の
> 多目的ストラテジーで、その Greedy / Backtracking / B&B が `weighted_sum` の初の消費者になった。
> 詳細は `Phase-6-1.md` / `Phase-1-1.md` §1 / `Phase-1-7.md` §5 / `Phase-2-3.md`。

**依存方向は一方向**: `route_planner.py` / `shift_scheduler.py`(葉)→
`problem.py` / `solution.py` → `__init__.py`。循環しないので `model_rebuild()` は不要。

**ファイル間の import は絶対 import**(`from app.domain.problems.route_planner import RouteData`)。
既存コードの流儀(`app/models/*`、`app/api/routes/__init__.py`)に合わせる。bare import
(`from route_planner import ...`)は実行時に `ModuleNotFoundError` になり、Pylance でも
解決できない。

> **Pylance で first-party の import が赤い場合**: 解析ルートが `decitima-api/backend/`
> になっているか確認する。ワークスペースを `decitima/`(プロジェクトルート)で開くと、
> `app` パッケージは 3 階層下(`decitima-api/backend/app`)にあるため Pylance が
> 見つけられない。対応は `decitima-api/backend/pyproject.toml` に `[tool.pyright]`
> (`include = ["app", "tests"]` / `venvPath = "."` / `venv = ".venv"`)を追加、または
> ワークスペース側 `decitima/.vscode/settings.json` の
> `"python.analysis.extraPaths": ["decitima-api/backend"]`。適用後に
> 「Developer: Reload Window」。

#### 分割 vs 統合の判断

`problem.py` は `ProblemData = Annotated[RouteData | ShiftData, Field(discriminator=...)]`
を組むために `route_planner.py` / `shift_scheduler.py` を import する。この import が
必要になること自体は**分割が間違いという意味ではない**。

- `RouteData` と `ShiftData` が**互いを import しない**(ピアの独立)ことが守れていれば、
  分割は「別問題」という意図を正しく表現できている。
- `ProblemData`(ユニオン)は本質的に「対応する全 problem_type のカタログ」で、
  部品から独立できない。**どこかが両者を import して束ねる必要がある。**
  それを担うのが `problem.py` ── アグリゲータの役割であって、悪い密結合ではない。
- 同じ形はこのリポジトリに既にある: `app/api/routes/__init__.py` が全ルーターを
  `api_router` に集約、`alembic/env.py` が全モデルを import、`registry.py`(Phase 0-4)が
  全 strategy を import。

**判断基準は「一緒に変わるものを同じファイルに」**。`RouteData` は経路モデルが、
`ShiftData` はシフトモデルが変わったとき ── 別の理由で変わるので分割する。
`ProblemData` / `OptimizationProblem` は「対応する問題タイプの集合」が変わったときに
変わるので、それ専用の場所(`problem.py`)に置く。

ユニオンを `__init__.py` に置くのは避ける。`__init__.py` は `OptimizationProblem` も
re-export するため、`problem.py`(その定義元)が `__init__.py` を import すると
`problem.py ↔ __init__.py` の循環になる。

**`__init__.py` は「公開窓口」**。分割したファイルの内訳を利用側に見せないために
re-export する。既存 `app/models/__init__.py` と同じく、ruff の F401(未使用 import)を
避けるため `__all__` を付ける。

```python
# app/domain/problems/__init__.py
from app.domain.problems.problem import (
    AnyConstraint, ConstraintBase, ForbiddenConstraint, GenericConstraint,
    NumericBoundConstraint, Objective, OptimizationProblem, ProblemData,
    RequiredInclusionConstraint, StaffingConstraint,
)
from app.domain.problems.route_planner import RouteData, RouteEdge, RouteNode
from app.domain.problems.shift_scheduler import ShiftData, ShiftSlot, Staff

__all__ = [
    "AnyConstraint", "ConstraintBase", "ForbiddenConstraint", "GenericConstraint",
    "NumericBoundConstraint", "Objective", "OptimizationProblem", "ProblemData",
    "RequiredInclusionConstraint", "RouteData", "RouteEdge", "RouteNode",
    "ShiftData", "ShiftSlot", "Staff", "StaffingConstraint",
]
```

これで利用側は `from app.domain.problems import OptimizationProblem, RouteData` と書け、あとでファイルを分割・統合しても import 文が変わらない。

> **`__init__.py` は必要か?** — サブパッケージには必ず置く。理由:
> (1) `decitima-api` の全パッケージが持っており一貫する。
> (2) pytest / ruff / mypy / Alembic autogenerate が明示的な regular package で
> 予測どおり動く(暗黙の namespace package は "duplicate module" 等の原因)。
> (3) 上記の re-export の置き場所になる。
> Python 3.3+ の「`__init__.py` なし namespace package」は 1 パッケージを複数
> ディレクトリ/配布に分ける特殊用途向けで、アプリ内のサブパッケージには使わない。

---

## 3. `Objective` ── 目的

「何を、どっち方向に良くしたいか」を表す。

```python
# app/domain/problems/problem.py
class Objective(BaseModel):
    sense: Literal["minimize", "maximize"]   # 最小化 or 最大化
    target: str                              # 対象の名前。例: "travel_time", "labor_cost"
    weight: float = 1.0                      # 多目的のときの相対的な重み
    description: str | None = None            # 人間向けの説明(任意)
```

### ポイント

- **`target` は文字列**。「何を測るか」はアルゴリズム側が `target` を見て決める。
  スキーマはメトリクスの計算方法を知らない(知る必要がない)。
- **多目的は `objectives` を複数並べる**。Shift Scheduler は
  `[Objective(minimize, "labor_cost", weight=0.7), Objective(maximize, "day_off_satisfaction", weight=0.3)]`
  のようになる。アルゴリズムは重み付き和 `Σ wᵢ · fᵢ` を最適化する、という約束にする。
- Route Planner は `objectives` が 1 要素だけ。

### なぜ「目的関数そのもの」を持たせないのか

`target: str` ではなく `objective_fn: Callable` を持たせる案もあった。却下した理由:

- スキーマは JSON でシリアライズでき、DB に保存でき、LLM が生成できる必要がある。
  関数はそのどれもできない。
- 「移動時間の計算方法」はエッジ重みの意味を知るアルゴリズム/ドメイン層の責務。
  スキーマに漏らすと責務が混ざる。

---

## 4. `Constraint` ── 制約

「守るべき条件」を表す。ここが最も設計判断の多い部分。

### 4.1 hard と soft を型で区別する

全制約が共有するフィールド(hard/soft の別、ペナルティ、説明)は基底クラスにまとめる。
**判別子 `kind` は基底には置かず、各サブタイプが宣言する**(理由は §4.2)。

```python
# app/domain/problems/problem.py
class ConstraintBase(BaseModel):
    severity: Literal["hard", "soft"] = "hard"  # hard = 絶対 / soft = できれば
    penalty: float | None = None                # soft 違反 1 件あたりのペナルティ
    description: str | None = None
```

- **hard 制約**: 1 つでも破れば解は `INVALID`。Route の「禁止エッジを使わない」、
  Shift の「必要人数を満たす」。
- **soft 制約**: 破っても解は有効だが、ペナルティが目的関数に加算される。
  Shift の「希望休はできれば OFF」。`penalty` はその重み。

この区別は Verification(Phase 0-6)で効いてくる。
「hard 違反 → 即 INVALID」「soft 違反 → 件数を数えて metrics に反映」。

### 4.2 制約の中身 ── サブタイプごとに宣言的データで表す

制約の具体的な内容は、`kind` を判別子にしたサブタイプで表す。
各サブタイプが `kind: Literal[...]` を宣言し、`ConstraintBase` を継承する。
MVP で必要な種類だけ定義する(YAGNI)。

```python
# app/domain/problems/problem.py（つづき）
class NumericBoundConstraint(ConstraintBase):
    kind: Literal["numeric_bound"] = "numeric_bound"
    field: str                    # 対象。例: "total_weight" / "labor_cost"
    operator: Literal["<=", ">=", "==", "<", ">"]   # [Phase 2 でサンプル修正] 当初 op → operator
    value: float

class RequiredInclusionConstraint(ConstraintBase):
    kind: Literal["required_inclusion"] = "required_inclusion"
    items: list[str]              # 必ず含めるもの。例: ["asakusa"] / 必須経由ノード

class ForbiddenConstraint(ConstraintBase):
    kind: Literal["forbidden"] = "forbidden"
    items: list[str]              # 使ってはいけないもの。例: 禁止エッジ ID

class StaffingConstraint(ConstraintBase):
    kind: Literal["staffing"] = "staffing"
    # スロットごとの必要人数は data 側に持つので、ここはフラグ的な意味づけ
```

> **YAGNI 原則**(You Aren't Gonna Need It): 「将来必要になるかもしれない」という
> 予測に基づいて余計な機能・過剰な設計を先回りで作り込まない。制約サブタイプも
> MVP の Route / Shift で実際に使うものだけ定義する。

**なぜ基底 `ConstraintBase` に `kind` を宣言しないのか。** 「基底で `kind: str`、
サブクラスで `kind: Literal[...]` に狭める」という書き方もできるが、これは
**型チェッカー(pyright / Pylance の standard モード)が警告を出す**:
可変フィールドの型は不変(invariant)であるべきで、`str` を `Literal["numeric_bound"]`
に狭める override は「基底型と一致しない」と見なされる(`reportIncompatibleVariableOverride`)。
実行時は Pydantic が正しく動くが、エディタに 4 つ赤線が出て邪魔になる。
基底には共通フィールドだけ持たせ、判別子は各サブタイプが宣言することでこれを避ける。

### 4.3 ad-hoc な制約 ── `GenericConstraint`

専用サブタイプを用意していない `kind` も受けられるようにしておく。
例: Shift の「希望休はできれば OFF」(§7.2)を、専用クラスを作らず
`kind="respect_days_off"` の soft 制約として表したい場合。

```python
# app/domain/problems/problem.py（つづき）
class GenericConstraint(ConstraintBase):
    """専用サブタイプのない ad-hoc な制約。kind は任意の文字列。"""

    kind: str
```

`GenericConstraint` は `kind: str` を持つ唯一のクラス。ここでは基底ではなく
末端のサブタイプなので override 警告は起きない。種類が固まってきたら
専用サブタイプ(`RespectDaysOffConstraint` 等)に昇格させればよい。

**なぜ宣言的データにするのか(関数参照にしないのか)**

- `Objective` と同じ理由: JSON 化・DB 保存・LLM 生成のため。
- 「制約を**表す**データ」と「制約を**チェックする**コード」を分離できる。
  チェッカーは `domain/constraints/` に置き、`kind` でディスパッチする(Phase 0-6)。
  制約の種類が増えてもスキーマとチェッカーが 1 対 1 で追随する。

### 4.4 `AnyConstraint` ── `constraints` の要素型

`OptimizationProblem.constraints` の型を `list[ConstraintBase]` にしてはいけない。
Pydantic は入力の dict を基底 `ConstraintBase` として検証し、`field` / `op` / `value` 等の
**サブタイプ固有フィールドを捨ててしまう**(JSON / LLM 入力のデシリアライズで実害)。

`kind` を見て正しいサブタイプを構築させるには、サブタイプの**ユニオン**を要素型にする。

```python
# app/domain/problems/problem.py（つづき）
from typing import Annotated, TypeAlias

#TypeAlias は既存の型に分かりやすい別名を付けるための明示的な型注釈
#Annotated は「型に追加情報（メタデータ）を付ける」
#TypeAlias で「再利用可能な意味付きの型」に名前を付け、Annotated で「その型に対する Pydantic/FastAPI 用の検証・変換メタデータ」

# constraints の 1 要素の型。左から順に検証を試し、既知サブタイプに
# 当てはまらない kind は GenericConstraint にフォールバックする
AnyConstraint: TypeAlias = Annotated[
    NumericBoundConstraint
    | RequiredInclusionConstraint
    | ForbiddenConstraint
    | StaffingConstraint
    | GenericConstraint,
    Field(union_mode="left_to_right"),
]
```

- **`union_mode="left_to_right"`**: 既定の「smart」モードではなく、左から順に検証する。
  `GenericConstraint`(どんな `kind` でも通る)を末尾に置くことで、専用サブタイプの
  ある `kind` はそちらに、無い `kind` は `GenericConstraint` にマッチする。
- **`: TypeAlias`**: `AnyConstraint` が型エイリアスであることを型チェッカーに明示する。
  `Annotated[...]` に `Field(...)` の呼び出しが入るため、明示しないと Pylance が
  「ただの変数」と解釈して `list[AnyConstraint]` を型として認めないことがある。
- **注意点(サイレント降格)**: `{"kind": "numeric_bound"}` のように必須フィールドが
  欠けた入力は、`NumericBoundConstraint` の検証に失敗して末尾の `GenericConstraint` に
  「降格」して通ってしまう(データ欠落に気づけない)。厳密にエラーにしたいなら
  判別可能ユニオン `Annotated[..., Field(discriminator="kind")]` を使う。ただし
  `GenericConstraint` は `kind` が Literal でないので discriminator ユニオンには
  混ぜられず、ad-hoc な `kind` が使えなくなる。MVP は left_to_right + フォールバックを
  採る。

> **[以降 Phase で修正予定 ── Phase 1-1]** この章のスケッチは Phase 0 時点のまま読んでよい。
> Phase 1-1 での変更: 型エイリアス(`AnyConstraint` / §5.3 の `ProblemData` / §6 の
> `SolutionData` / §8.1 の `ProblemData`)を、当初〈`X: TypeAlias = Annotated[...]`〉→
> 現在〈PEP 695 の `type` 文 `type X = Annotated[...]`〉に変更。理由(解決される問題)〈ruff
> `UP040` が `: TypeAlias` を非推奨。`type` 文なら `Annotated[..., Field(...)]` も pyright /
> Pylance が型として正しく扱う(`: TypeAlias` 明示が不要)。Pydantic 2.13 で判別可能ユニオン・
> `union_mode` も解決(実機確認済み)〉。`decitima-api` の PEP 695 ジェネリクス採用とも一貫。
> 現行版は `textbook/Phase-1/samples/`、詳細は `Phase-1-1.md` §2.1。

### 4.5 Constraint Checker との対応

各 `kind` に対応するチェッカー関数が `app/domain/constraints/` に 1 つある。
詳細は Phase 0-6。

```
NumericBoundConstraint(kind="numeric_bound", field="weekly_work_hours", operator="<=", value=40)
        │
        ▼  Verification が kind を見てディスパッチ
check_numeric_bound(constraint, problem, solution) -> ConstraintViolation | None
```

---

## 5. `data` ── 問題固有ペイロード

`problem_type` を判別子にした判別可能ユニオン。MVP では 2 種類。

### 5.1 Route Planner: `RouteData`

```python
# app/domain/problems/route_planner.py
class RouteNode(BaseModel):
    id: str
    label: str | None = None
    # 座標は A* のヒューリスティック用(任意)
    x: float | None = None
    y: float | None = None

class RouteEdge(BaseModel):
    id: str
    source: str                  # RouteNode.id
    target: str                  # RouteNode.id
    weight: float                # 距離 or 所要時間
    directed: bool = False

class RouteData(BaseModel):
    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str                   # RouteNode.id
    goal: str                    # RouteNode.id
```

### 5.2 Shift Scheduler: `ShiftData`

```python
# app/domain/problems/shift_scheduler.py
class Staff(BaseModel):
    id: str
    name: str | None = None
    hourly_wage: float
    skills: list[str] = []
    available_slot_ids: list[str]        # 勤務可能なスロット
    requested_days_off: list[str] = []    # 希望休の日付(soft 制約と連動)

class ShiftSlot(BaseModel):
    id: str
    day: str                     # "2026-09-01" など
    start_hour: int
    end_hour: int
    required_headcount: int
    required_skills: list[str] = []

class ShiftData(BaseModel):
    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    staff: list[Staff]
    slots: list[ShiftSlot]
    max_weekly_hours: float = 40
    max_consecutive_days: int = 5
```

### 5.3 ユニオンの合成

```python
# app/domain/problems/problem.py（つづき）
from typing import Annotated, Any, TypeAlias

# ↓ 兄弟モジュールは「絶対 import」で参照する（相対 import / bare import は使わない）
from app.domain.problems.route_planner import RouteData
from app.domain.problems.shift_scheduler import ShiftData

ProblemData: TypeAlias = Annotated[
    RouteData | ShiftData,
    Field(discriminator="problem_type"),
]

class OptimizationProblem(BaseModel):
    problem_type: Literal["route_planning", "shift_scheduling"]
    objectives: list[Objective]
    constraints: list[AnyConstraint] = Field(default_factory=list)
    data: ProblemData
    metadata: dict[str, Any] = Field(default_factory=dict)

    # problem_type と data.problem_type の一致は model_validator でチェック(Phase 0-6)
```

新しい問題タイプ(Travel Planner 等)を追加するときは、
`XxxData` を定義して `ProblemData` ユニオンに足すだけ。既存には触れない。

> **import と Pylance のハマりどころ**:
> `from route_planner import RouteData` のような **bare import** は実行時に
> `ModuleNotFoundError: No module named 'route_planner'` になる(§2.5)。さらに
> Pylance では `RouteData` / `ShiftData` が未解決になり、`ProblemData` が有効な型として
> 成立せず、`data: ProblemData` の行に **「型式では変数を使用できません」
> (reportInvalidTypeForm)** が出る。`from app.domain.problems.route_planner import RouteData`
> と絶対 import にする。それでも赤いままなら、Pylance の解析ルートが
> `decitima-api/backend/` になっているか確認する(§2.5 の注記)。
> 
> `ProblemData` / `AnyConstraint` に付けた **`: TypeAlias`** は、`Annotated[..., Field(...)]`
> のように呼び出しを含むエイリアスを Pylance が「型」と認識するための明示。
> `default_factory` は可変デフォルト値(`= []` / `= {}`)の共有を避ける Pydantic の定石。

> **[以降 Phase で修正予定 ── Phase 1-1]** `ProblemData: TypeAlias = Annotated[...]` は
> Phase 1-1 で `type ProblemData = Annotated[...]` に変更(§4.4 の同マーカー参照)。
> `type` 文なら `: TypeAlias` の明示は不要。

---

## 6. `CandidateSolution` ── 候補解

アルゴリズムが返すもの。

```python
# app/domain/solutions/solution.py
class ConstraintViolation(BaseModel):
    constraint_kind: str
    severity: Literal["hard", "soft"]
    message: str
    detail: dict[str, Any] = {}

class AlgorithmMeta(BaseModel):
    name: str                    # "dijkstra"
    family: str                  # "graph" / "optimization" / "scheduling" / "search"
    implementation: str          # "handwritten" / "library:networkx" / "library:ortools"
    time_complexity: str | None = None
    space_complexity: str | None = None

class CandidateSolution(BaseModel):
    problem_ref: uuid.UUID | None = None       # 永続化時は Problem の id。単発は None
    status: Literal["valid", "invalid", "infeasible"]
    assignments: SolutionData                  # problem_type 固有の結果
    metrics: dict[str, float] = {}             # {"travel_time": 95, "labor_cost": 182000}
    violations: list[ConstraintViolation] = []
    produced_by: AlgorithmMeta
```

### `status` の 3 値

| status       | 意味                                             |
| ------------ | ---------------------------------------------- |
| `valid`      | 解が出て、hard 制約をすべて満たしている                         |
| `invalid`    | 解は出たが hard 制約に違反している(アルゴリズムのバグ、または近似アルゴリズムの限界) |
| `infeasible` | そもそも条件を満たす解が存在しない(問題が過制約)                      |

### `assignments`(`SolutionData`)も判別可能ユニオン

```python
# app/domain/solutions/route_planner.py
class RouteSolution(BaseModel):
    problem_type: Literal["route_planning"] = "route_planning"
    path_node_ids: list[str]         # start から goal までのノード列
    path_edge_ids: list[str]
    total_weight: float

# app/domain/solutions/shift_scheduler.py
class ShiftSolution(BaseModel):
    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    # slot_id -> 割り当てられた staff_id のリスト
    assignments: dict[str, list[str]]

# app/domain/solutions/solution.py（route_planner.py / shift_scheduler.py を import する）
SolutionData = Annotated[
    RouteSolution | ShiftSolution,
    Field(discriminator="problem_type"),
]
```

> **[以降 Phase で修正予定 ── Phase 1-1]** `SolutionData` も Phase 1-1 で
> `type SolutionData = Annotated[...]` に統一(§4.4 の同マーカー参照)。`AlgorithmMeta.family`
> は Phase 1-1 で `type AlgorithmFamily = Literal["search", "graph", "optimization",
> "scheduling", "patterns"]` として型付けした(`Phase-0-4.md` §3 と整合。ここの `family: str`
> は Phase 0 時点の記述)。

### `produced_by` が比較可能性の要

同じ `OptimizationProblem` を 3 つのアルゴリズムで解けば、`produced_by` だけが
違う 3 つの `CandidateSolution` が並ぶ。`metrics` を突き合わせれば
「手実装 Dijkstra vs networkx」「貪欲 vs バックトラッキング」の比較が
そのままできる(Phase 3 / Phase 14)。

---

## 7. 検証 ── 2 題材をスキーマで書いてみる

抽象論で終わらせない。実際に書き下す。以下は**スキーマの使用例**(モジュールに
置くコードではなく、問題インスタンスの構築例)。完全なコードは
`samples/route_planner_example.py` と `samples/shift_scheduler_example.py`。

### 7.1 Route Planner

> 「A から E まで最短で行きたい。ただし橋(edge B-D)は工事中で通れない。C は必ず経由する。」

```python
problem = OptimizationProblem(
    problem_type="route_planning",
    objectives=[Objective(sense="minimize", target="total_weight")],
    constraints=[
        ForbiddenConstraint(severity="hard", items=["e_bd"]),         # 橋は通行止め
        RequiredInclusionConstraint(severity="hard", items=["C"]),    # C 必須経由
    ],
    data=RouteData(
        nodes=[RouteNode(id=n) for n in ["A", "B", "C", "D", "E"]],
        edges=[
            RouteEdge(id="e_ab", source="A", target="B", weight=2),
            RouteEdge(id="e_bc", source="B", target="C", weight=3),
            RouteEdge(id="e_bd", source="B", target="D", weight=1),   # 禁止対象
            RouteEdge(id="e_ce", source="C", target="E", weight=4),
            RouteEdge(id="e_de", source="D", target="E", weight=2),
        ],
        start="A",
        goal="E",
    ),
)
```

想定される解:

```python
CandidateSolution(
    status="valid",
    assignments=RouteSolution(
        path_node_ids=["A", "B", "C", "E"],
        path_edge_ids=["e_ab", "e_bc", "e_ce"],
        total_weight=9,
    ),
    metrics={"total_weight": 9},
    violations=[],
    produced_by=AlgorithmMeta(name="dijkstra", family="graph", implementation="handwritten",
                              time_complexity="O((V+E) log V)"),
)
```

**確認**: 単一目的・hard 制約のみ・解はノード列。すべて素直に表現できた。

### 7.2 Shift Scheduler

> 「3 人のスタッフを 2 日 × 2 スロットに割り当てる。各スロット 1 人必要。
> 週 10 時間まで。田中さんは 9/2 が希望休。人件費は最小化したい。」

```python
problem = OptimizationProblem(
    problem_type="shift_scheduling",
    objectives=[
        Objective(sense="minimize", target="labor_cost", weight=0.7),
        Objective(sense="maximize", target="day_off_satisfaction", weight=0.3),
    ],
    constraints=[
        StaffingConstraint(severity="hard"),                                  # 必要人数を満たす
        NumericBoundConstraint(severity="hard", field="weekly_work_hours",
                               operator="<=", value=10),
        # 希望休は soft。専用サブタイプを作らず GenericConstraint で表す
        GenericConstraint(kind="respect_days_off", severity="soft", penalty=5.0),
    ],
    data=ShiftData(
        staff=[
            Staff(id="tanaka", hourly_wage=1200, available_slot_ids=["s1", "s2", "s3", "s4"],
                  requested_days_off=["2026-09-02"]),
            Staff(id="sato",   hourly_wage=1000, available_slot_ids=["s1", "s2", "s3", "s4"]),
            Staff(id="ito",    hourly_wage=1100, available_slot_ids=["s1", "s3"]),
        ],
        slots=[
            ShiftSlot(id="s1", day="2026-09-01", start_hour=9,  end_hour=14, required_headcount=1),
            ShiftSlot(id="s2", day="2026-09-01", start_hour=14, end_hour=19, required_headcount=1),
            ShiftSlot(id="s3", day="2026-09-02", start_hour=9,  end_hour=14, required_headcount=1),
            ShiftSlot(id="s4", day="2026-09-02", start_hour=14, end_hour=19, required_headcount=1),
        ],
        max_weekly_hours=10,
    ),
)
```

想定される解:

```python
CandidateSolution(
    status="valid",
    assignments=ShiftSolution(assignments={
        "s1": ["ito"], "s2": ["sato"], "s3": ["sato"], "s4": ["tanaka"],
    }),
    metrics={"labor_cost": 21500, "day_off_satisfaction": 1.0, "soft_penalty": 0.0},
    violations=[],
    produced_by=AlgorithmMeta(name="backtracking", family="scheduling",
                              implementation="handwritten"),
)
```

**確認**: 多目的(重み付き)・hard と soft の混在・解は割当表。
`respect_days_off` は MVP 時点で専用サブタイプを作らず `GenericConstraint`(§4.3)で
表現した。種類が固まってきたら専用サブタイプに昇格させればよい。

### 7.3 実行して確かめる

`samples/` の 3 ファイル(`problem_schema.py` とその上に組んだ 2 題材)を実際に走らせて、
スキーマが構築でき整合していることを確認する。各ファイル末尾の `if __name__ == "__main__":`
が `assert` で検証し、最後に `... OK: ...` を表示する(想定と違えば `AssertionError` で停止)。

**A. ホストの uv で実行**

```bash
cd decitima-api/backend                      # uv 環境（pydantic 等）を使う
uv run python ../../textbook/Phase-0/samples/problem_schema.py
uv run python ../../textbook/Phase-0/samples/route_planner_example.py
uv run python ../../textbook/Phase-0/samples/shift_scheduler_example.py
```

**B. Docker で実行**(Python 環境を Docker で構築している場合)

`backend` コンテナは `decitima-api/backend` しかマウントしないため、教材の `samples/` を
追加マウントして実行する。

```bash
cd decitima-api                              # docker-compose.yml のある場所。.env を用意済みのこと
docker compose run --rm --no-deps \
  -v "$(pwd)/../textbook/Phase-0/samples:/samples:ro" \
  backend uv run python /samples/route_planner_example.py
```

- `--no-deps`: postgres / redis は起動しない(samples は使わない)
- `--rm`: 実行後にコンテナを破棄
- `-v …:/samples:ro`: 教材の `samples/` を読み取り専用でマウント
- 初回は `backend` イメージのビルドと `.venv` 同期が走る(以降はキャッシュ)

**期待出力**(A / B 共通)

```
problem_schema OK: OptimizationProblem
route_planner_example OK: A -> B -> C -> E (weight=9.0)
shift_scheduler_example OK: labor_cost = 21500.0 / day_off_satisfaction = 1.0
```

**そのほかの確認**

- 構文チェックのみ(環境不要): `python -m py_compile <path>`
- 型チェック(任意、standard): `uvx --with pydantic pyright textbook/Phase-0/samples`

---

## 8. スキーマの拡張ポイント(将来の Phase に向けて)

| 追加したいもの                 | 追加方法                                                                                 | 既存への影響             |
| ----------------------- | ------------------------------------------------------------------------------------ | ------------------ |
| グラフ構造の別問題(MST 等)       | `NetworkDesignData` / `NetworkDesignSolution` を定義しユニオンに追加(§8.1)                      | なし                 |
| Travel Planner(Phase 7) | `TravelData` / `TravelSolution` を定義しユニオンに追加                                          | なし                 |
| 新しい制約種類                 | `ConstraintBase` のサブクラスを定義し `AnyConstraint` に追加、対応するチェッカーを `domain/constraints/` に追加 | なし                 |
| What-if シナリオ(Phase 10)   | `OptimizationProblem` を複製して一部の値を変える。スキーマ自体は不変                                        | なし                 |
| LLM 由来のメタ情報(Phase 11)   | `metadata` に `source="llm"`, `confidence` 等を入れる                                      | なし(`metadata` は自由) |

「共通の骨格は閉じて、問題固有部分は開いておく」── これがハイブリッド設計の狙い。

### 8.1 例: `network_design`(最小全域木)を追加する

「すべての拠点を最小コストで接続する」問題(README §12.6 Network Designer)。
`route_planning` は start→goal の**単一経路**なので、辺集合を返す MST は表現できない。
新しい problem_type を足す。

```python
# app/domain/problems/network_design.py（葉。兄弟を import しない）
class NetworkNode(BaseModel):
    id: str
    label: str | None = None

class NetworkLink(BaseModel):
    id: str
    endpoints: tuple[str, str]        # 無向。接続する 2 ノードの id
    weight: float                     # 敷設コスト / 距離

class NetworkDesignData(BaseModel):
    problem_type: Literal["network_design"] = "network_design"
    nodes: list[NetworkNode]
    links: list[NetworkLink]          # 敷設可能なリンクの候補
```

```python
# app/domain/solutions/network_design.py（葉）
class NetworkDesignSolution(BaseModel):
    problem_type: Literal["network_design"] = "network_design"
    selected_link_ids: list[str]      # 選んだリンクの集合
    total_weight: float
```

`problem.py` / `solution.py` のユニオンに 1 項目ずつ足す(§5.3 と同じ手順):

```python
# app/domain/problems/problem.py
from app.domain.problems.network_design import NetworkDesignData
ProblemData: TypeAlias = Annotated[
    RouteData | ShiftData | NetworkDesignData, Field(discriminator="problem_type")
]
```

> **[以降 Phase で修正予定 ── Phase 1-1 / Phase 4]** 型エイリアスは `type ProblemData =
> Annotated[...]` に変更(§4.4 の同マーカー)。また `network_design` は当初この節のとおり
> 「後から足す拡張例」で、Phase 1-1 のユニオンは route/shift の 2 メンバーで開始する
> (`Phase-1-1.md` §2.2)。実際の追加は **Phase 4**(Kruskal / Prim / Union-Find。
> `Phase-0-4.md` §4 の registry も Phase 4 とコメント済み)。

> **[Phase 5 で確定 ── network_design を追加]** Phase 5-3 でこの節のとおり実装した。
> `NetworkLink.endpoints: tuple[str, str]`(常に無向)/ `NetworkDesignSolution.selected_link_ids` /
> semantic(`check_network_link_endpoints` / `check_network_has_links`)/ `verify_network_structure`
> (純粋述語)+ `forms_spanning_tree`(services が呼ぶ計算)。全域木の「連結 ∧ 非閉路」判定は
> `domain` でなく `SolutionVerificationService` に置いた(`Phase-2-2.md` §3 の切り分け)。
> `alembic upgrade head` は no-op(新テーブルなし)。詳細 `Phase-5-3.md`。

- objective: `Objective(sense="minimize", target="total_weight")`(単一)
- 制約: 全ノードが連結(hard)/ `RequiredInclusionConstraint`(必須リンク)/ `ForbiddenConstraint`(禁止リンク)
- アルゴリズム(Phase 4): `KruskalStrategy`(Union-Find を使う)/ `PrimStrategy`(優先度キューを使う)
- Verification: 全ノード連結 / 閉路なし(辺数 = ノード数 − 1)/ 禁止を含まない / 必須を含む / `total_weight` 整合

既存の `route_planning` / `shift_scheduling` のコードには**一切触れない**。これがハイブリッド設計の
「問題固有部分は開いておく」の効果。

---

## 9. まとめ

- 共通スキーマは LLM と Algorithm Engine を疎結合にするための「契約」。
- **ハイブリッド型**: `objectives` / `constraints` は共通語彙として型付き、
  `data` / `assignments` は `problem_type` 判別子付きの判別可能ユニオン。
- 制約は `ConstraintBase`(共通フィールド)+ `kind` 判別子付きサブタイプ +
  ad-hoc 用 `GenericConstraint`。要素型は `AnyConstraint`(left_to_right ユニオン)。
  チェックロジックは分離して `domain/constraints/` に置く。
- `CandidateSolution` は `status` + `metrics` + `violations` + `produced_by` を必ず持つ。
  `produced_by` が比較可能性(NFR-3)の土台。
- Route Planner と Shift Scheduler を実際に書き下し、両方を無理なく表現できることを確認した。

次章(Phase 0-3)では、このスキーマを中心に据えた `decitima-api` の
**アーキテクチャ**(レイヤー構成とデータフロー)を設計する。
