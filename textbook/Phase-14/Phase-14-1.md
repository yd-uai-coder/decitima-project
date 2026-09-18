# Phase 14-1: `family` 拡張 + 共通プロンプト部品(作業単位 14-1)

## この章のゴール

LLM Only 戦略を `AlgorithmStrategy` Protocol に完全準拠させるための土台を作る。
`AlgorithmMeta.family` に `"llm"` を追加し(Phase 1 への遡及)、6ドメイン共通で使う
プロンプト部品(目的・制約の自然言語化)と、6クラス共通の `AlgorithmMeta` インスタンスを`app/algorithms/llm/common.py` にまとめる。

**この章で作成/更新するファイル**: `app/domain/solutions/solution.py`(改訂)、
`app/algorithms/llm/__init__.py`・`app/algorithms/llm/common.py`(新規)。

---

## 1. `AlgorithmMeta.family` は「サブパッケージと1対1」── 破らずに拡張する

`app/domain/solutions/solution.py` のコメントは元々こう宣言していた:

```python
# AlgorithmMeta.family は app/algorithms/ の 5 サブパッケージと 1 対 1
type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns"]
```

LLM Only 戦略も `AlgorithmStrategy` Protocol(`meta: AlgorithmMeta` + `solve()`)を満たす以上、この不変条件を破らずに位置づける必要がある。選択肢は2つ:

1. 既存の5つのどれかに間借りする(例: `"optimization"`)── しかし LLM は手実装でも
   ライブラリラッパーでもなく、性質が全く違う。どのサブパッケージにも属さない。
2. **6つ目のサブパッケージ `app/algorithms/llm/` を新設し、`family` に `"llm"` を足す**。

進行のルール #17 の判定基準(「この共通化を今駆動している実在の消費者は何か」)は今回
「拡張してよいか」の形で問われるが、考え方は同じ ── 「この Phase の実装(14-2〜14-4 の6クラス)が具体的に必要としているか」に Yes と答えられるので、2 を選ぶ。

```python
# app/domain/solutions/solution.py(改訂)
# AlgorithmMeta.family は app/algorithms/ のサブパッケージと 1 対 1
# (Phase 1〜9)
# type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns"]
# (Phase 14-1) "llm"(app/algorithms/llm/)を追加。REGISTRY には登録しない比較専用の戦略だが、
# 契約(AlgorithmStrategy)上は他の family と同格であることを型で表す。
type AlgorithmFamily = Literal["search", "graph", "optimization", "scheduling", "patterns", "llm"]


class AlgorithmMeta(BaseModel):
    name: str
    family: AlgorithmFamily  # (Phase 14-1) 直接 Literal を書いていた箇所を型エイリアス参照に統一
    implementation: str
    ...
```

> **写経の罠**: `AlgorithmMeta.family` は元々 `type AlgorithmFamily` と**同じ Literal を直接書き下していた**(型エイリアスは定義されていたが使われていなかった)。Phase 14-1 で`family` の型を追加するとき、両方を同時に直さないと(`AlgorithmFamily` だけ直して`AlgorithmMeta.family` の Literal を直し忘れる)、`LlmOnly*Strategy` のインスタンス化で`family="llm"` が pydantic のバリデーションエラーになる(値が Literal の候補に無い)。

**登録先(`REGISTRY`)を触らないことが重要**: `app/algorithms/registry.py` の `REGISTRY` 辞書は無変更のまま(Phase 12 の `select_strategy`・Phase 3 の `BenchmarkService` は無改造で動く)。
LLM Only 戦略は 14-5 の `ComparisonService` が専用の辞書(`_LLM_ONLY_STRATEGIES`)で直接インスタンス化する ── `/solve` の既定選択には一切影響しない。

## 2. `app/algorithms/llm/` パッケージの新設

```python
# app/algorithms/llm/__init__.py(新規、全文)
"""LLM Only 戦略(README §14「LLM vs Algorithm Comparison」)。

`app/algorithms/` の6つ目のサブパッケージ(`AlgorithmMeta.family = "llm"` と1対1)。
ここに置く戦略は `AlgorithmStrategy` Protocol を満たすが、本番 `REGISTRY` には登録しない ──
`/solve` の既定選択に一切影響させず、`app/services/comparison.py::ComparisonService` が
比較専用に直接インスタンス化する。
"""
```

`app/algorithms/optimization/__init__.py`・`scheduling/__init__.py` と同じ「パッケージdocstring だけを持つ `__init__.py`」形式(進行のルール #7)。

## 3. 共通プロンプト部品 ── 目的・制約は6ドメイン共通の形を持つ

```python
# app/algorithms/llm/common.py(新規、全文)
from app.domain.problems.problem import (
    ForbiddenConstraint, GenericConstraint, NumericBoundConstraint,
    OptimizationProblem, RequiredInclusionConstraint, StaffingConstraint,
)
from app.domain.solutions.solution import AlgorithmMeta

LLM_ONLY_META = AlgorithmMeta(name="llm_only", family="llm", implementation="llm")


def render_objectives(problem: OptimizationProblem) -> str:
    return (
        "\n".join(f"- {o.sense} {o.target}(重み {o.weight})" for o in problem.objectives)
        or "(目的なし)"
    )


def render_constraints(problem: OptimizationProblem) -> str:
    if not problem.constraints:
        return "(制約なし)"
    lines: list[str] = []
    for c in problem.constraints:
        if isinstance(c, NumericBoundConstraint):
            lines.append(f"- [{c.severity}] {c.field} {c.operator} {c.value}")
        elif isinstance(c, RequiredInclusionConstraint):
            lines.append(f"- [{c.severity}] 必ず含める: {c.items}")
        elif isinstance(c, ForbiddenConstraint):
            lines.append(f"- [{c.severity}] 使用禁止: {c.items}")
        elif isinstance(c, StaffingConstraint):
            lines.append(f"- [{c.severity}] 各スロットの必要人数を満たす")
        elif isinstance(c, GenericConstraint):
            lines.append(f"- [{c.severity}] {c.kind}: {c.description or '(説明なし)'}")
    return "\n".join(lines)
```

`OptimizationProblem.objectives`/`constraints` は `problem.py`(Phase 1〜9)が定義する共通の型付き語彙 ── `AnyConstraint` の判別可能ユニオンを `isinstance` で分岐する形は、Phase 11 の `structuring.py::catalog_ids`/`ground_references` と同じパターン(データ側のユニオンは各ドメインの葉が持つが、目的・制約は最初から共通)。

**`LLM_ONLY_META` を6クラス共通の1インスタンスにする理由**: `AlgorithmRecommendationService`
(Phase 12)は `_ALGORITHM_DESCRIPTIONS` を `(problem_type, meta.name)` のタプルキーにして「`meta.name` が problem_type をまたいで重複する」問題を解決した(例: `"greedy"` がshift/travel/logistics の3実装で重複)。LLM Only 戦略は**そもそも `REGISTRY`/説明カタログのどちらにも登録しない**ため、この衝突は起きない ── `_LLM_ONLY_STRATEGIES`(14-5)は`problem_type` をキーにした単純な dict で足りる。

ドメインごとのカタログ化(id/name の列挙)は各 `*_llm.py`(14-2〜14-4)の担当 ──
Phase 11 の `catalog_entries` が「ドメインごとに形が違う `problem.data` を分岐する」ことを共通モジュールでなく `structuring.py` 自身に置いたのと同じ判断(分岐そのものは共通化しない、分岐した後の自然言語化のフォーマットだけ揃える)。

## 4. `strip_problem_type` ── 実際に Gemini を呼んで初めて判明した罠への対処

14-2〜14-4 を書いた時点では気づかず、実運用で `POST /api/v1/compare` を叩いて初めて
6ドメイン全滅で発覚した問題への対処を、共通ヘルパとしてここに追加する(詳細な事象・原因は
`Phase-14-2.md` §4 で扱う。以下は結論だけ先に示す)。

```python
# app/algorithms/llm/common.py(追記)
from typing import Any

from pydantic import BaseModel, create_model


def strip_problem_type(schema: type[BaseModel]) -> type[BaseModel]:
    """LLM に渡す構造化出力スキーマから判別子フィールド problem_type を除く。

    `Literal[...] = "..."` のような単一値フィールドは Pydantic の JSON Schema では
    `"const"` になるが、Gemini の構造化出力(`response_json_schema`)は `const` を
    サポートしないため制約が失われ、LLM が任意の文字列を埋めてしまう
    (実測: `RouteSolution` で `"shortest_path"` のような無関係な値を生成)。
    最初から見せず、各 `*_llm.py` の `solve()` 側で固定値を足し戻す。
    """
    # fields: Any にしておく ── create_model の **kwargs 展開はキーワードごとに違う型
    # (str/tuple/ConfigDict 等)を取るため、動的な dict を渡すと pyright が静的に解決できない
    # (Pydantic 公式でも既知の制限)。動的生成そのものが目的の関数なので Any で割り切る。
    fields: dict[str, Any] = {
        name: (field.annotation, field)
        for name, field in schema.model_fields.items()
        if name != "problem_type"
    }
    return create_model(f"{schema.__name__}Llm", **fields)
```

- `problem_type` は元々 `SolutionData` の判別可能ユニオン(Phase 1)がどの具象型かを
  判定するためだけのフィールドで、LLM が「決める」情報ではない(README「LLM に最適解を
  計算させない」の精神にも合う)。**既存6スキーマをそのまま使う(新スキーマを作らない)**
  という Phase 14 の設計判断は変えず、LLM に見せる一時的な派生スキーマだけを
  `create_model` で動的生成する。

---

## まとめ

- `AlgorithmMeta.family` に `"llm"` を追加(Phase 1 solution.py への遡及、進行のルール #12)。
  型エイリアスとフィールドの Literal 二重管理を統一し、`REGISTRY` には触れない。
- `app/algorithms/llm/` を6つ目のサブパッケージとして新設し、6クラス共通の
  `LLM_ONLY_META`・`render_objectives`・`render_constraints`・`strip_problem_type` を
  `common.py` に置く。
- `strip_problem_type` は実際に Gemini を呼んで初めて必要と分かったヘルパ ── ユニット
  テストの `FakeLLM` は固定値をそのまま返すだけなので発見できない類の問題(詳細は
  `Phase-14-2.md` §4)。

## テスト観点

この章はドメイン非依存の共通部品のみで、単独では検証しにくい(`LLM_ONLY_META`/
`render_objectives`/`render_constraints`/`strip_problem_type` は 14-2 の
`LlmOnlyRouteStrategy` のテストが間接的に最初の消費者になる)── **スタブ不要 ── 対象が純粋(副作用なし)で外部依存を呼ばないため**。専用テストファイルは置かず、14-2 の `test_llm_only_strategies.py` が実質的な第一テストになる(進行のルール #15 の「章が作る全ファイルをその章のテストが1度は importする」は 14-2 まで含めて満たす設計 ── `common.py` は 14-1 単独では消費者を持たない純粋なライブラリコードのため)。

```bash
uv run python -c "
from app.algorithms.llm.common import LLM_ONLY_META, strip_problem_type
from app.domain.solutions.route_planner import RouteSolution
print(LLM_ONLY_META)
print(list(strip_problem_type(RouteSolution).model_fields.keys()))  # problem_type が無いことを確認
"
uvx pyright app/domain/solutions/solution.py app/algorithms/llm/common.py
```

---

次章([Phase-14-2](./Phase-14-2.md))では、作業単位 14-2 ──
グラフ系2ドメイン(route_planning / network_design)の `LlmOnly*Strategy` を実装する。
