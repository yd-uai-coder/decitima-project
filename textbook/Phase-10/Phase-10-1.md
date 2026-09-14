# Phase 10-1: スキーマ + `apply_overrides`(作業単位 10-1)

## この章のゴール

「シナリオ = 一部の値を変えて複製した `OptimizationProblem`」(README)を、**ドメインを1 つも知らない汎用関数**として実装する。6 ドメイン(route/network/shift/travel/project/logistics)のどの `OptimizationProblem` を渡しても同じ関数で override が効くことを、複数domain の fixture で確認する。

**この章で作成するファイル**: `app/schemas/simulation.py`(新規)、`app/services/simulation.py`(新規。この章では `apply_overrides` / `_deep_merge` の分だけ)、
`tests/unit/test_simulation_overrides.py`(新規)。

依存は一方向 ── `app/services/simulation.py` が `app/schemas/simulation.py` を import する。以下もこの順(schema → service)で説明する。

---

## 1. スキーマ ── override / 比較結果の型

```python
# app/schemas/simulation.py(要点。全文は samples)
class ScenarioOverride(BaseModel):
    label: str
    overrides: dict[str, Any] = Field(default_factory=dict)


class SimulationRequest(BaseModel):
    problem: OptimizationProblem
    algorithm: str | None = None          # None なら base で自動選択した名前を全シナリオに固定
    scenarios: list[ScenarioOverride] = Field(min_length=1)
    sensitivity: SensitivitySpec | None = None   # 10-3 で追加。この章では常に None
    timeout_seconds: float | None = Field(default=None, gt=0)


class ScenarioResult(BaseModel):
    label: str
    status: Literal["valid", "invalid", "infeasible", "invalid_scenario"]
    metrics: dict[str, float] = Field(default_factory=dict)
    algorithm_name: str | None = None
    error: str | None = None              # invalid_scenario のときだけ入る


class SimulationResult(BaseModel):
    base: ScenarioResult
    scenarios: list[ScenarioResult]
    sensitivity: SensitivityResult | None = None   # 10-3 で追加
```

`ScenarioResult.status` に既存 3 種(`valid`/`invalid`/`infeasible`)へ **`invalid_scenario`を追加**している点に注意 ── これは「解として無効」ではなく「シナリオそのものが破綻した(override が不正、到達不能等)」を表す第 4 の状態。次章 `run_simulation` がこの状態を使う。

`algorithm: str | None = None` ── 未指定なら **base problem に対して自動選択した名前を全シナリオに固定する**(次章で実装)。これにより「条件だけを変え、アルゴリズム選択の揺れを比較に混ぜない」フェアな比較になる。

---

## 2. なぜ「汎用 dict マージ」なのか

シナリオの override をどう表現するか、2 つの設計が考えられた:

| 案               | 内容                                                                                                      | トレードオフ                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| A. 汎用 dict マージ  | `overrides: dict[str, Any]` を base problem の JSON 表現に深くマージし、`OptimizationProblem.model_validate` で再検証する | 型安全性は Pydantic の再検証に委ねる(override 自体は unsafe だが結果は必ず検証済み)。ドメイン別コードが増えない |
| B. ドメイン別の名前付きノブ | `route: edge_weight_multiplier`、`shift: staff_count` のように各ドメインで「変更可能なパラメータ」を明示的に定義する                    | 型安全・意図が明確だが、6 ドメイン分の定義コードが要り、後続ドメイン追加のたびに追記が発生する                       |

README は「シナリオ = 一部の値を変えて複製した `OptimizationProblem`。**スキーマ自体は不変**」と明記しており、A のほうが忠実 ── ドメインスキーマに 1 行も触れずに済む。B は型安全性で優るが、Phase 10 の本質(「既存の6ドメインを横断してオーケストレーションする」)からすると、ドメイン別コードを増やす B は主旨に反する。**A を採用する**。

上の `ScenarioOverride.overrides` フィールドがこの決定をそのまま体現している ── 型は素の `dict[str, Any]` であり、ドメインごとの型定義を持たない。

override の適用は次の 2 段(JSON Merge Patch、[RFC 7386](https://www.rfc-editor.org/rfc/rfc7386)相当):

1. `problem.model_dump(mode="json")` で base problem を dict にする。
2. `overrides` を再帰的にマージする ── dict 同士だけ再帰、list やスカラーは丸ごと置換、値が `None` ならそのキーを削除する(RFC 7386 の仕様どおり)。

```python
# app/services/simulation.py(要点。全文は samples)
def apply_overrides(problem: OptimizationProblem, overrides: dict[str, Any]) -> OptimizationProblem:
    if "problem_type" in overrides:
        raise ValueError("scenario overrides must not change problem_type")
    merged = _deep_merge(problem.model_dump(mode="json"), overrides)
    return OptimizationProblem.model_validate(merged)


def _deep_merge(base: Any, patch: Any) -> Any:
    if not isinstance(patch, dict):
        return patch
    result = dict(base) if isinstance(base, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

`problem_type` の変更は明示的に禁止する ── ドメインを跨いだシナリオ(「route を network に変える」)は意味を持たないため。実は禁止しなくても、`data.problem_type` だけを変えずにトップの `problem_type` だけ変えれば `OptimizationProblem._problem_type_matches_data`
(Phase 1 の `model_validator`)が不一致を検出して弾いてくれる。ただし**両方**を書き換えて「別ドメインへの完全な差し替え」を通すことも理論上できてしまうため、意図を明確にするガードとして先頭で弾く。

**Validation は呼ばない** ── `apply_overrides` は純粋な型検証(Pydantic)だけを行い、
Semantic Validation(到達可能性チェック等)は次章 `run_simulation` の責務にする。これは既存の Validation(問題の妥当性)と Verification(解の制約充足)の分離(`Phase-0-*.md`)と
同じ切り分けで、「マージして型として妥当か」と「アルゴリズムに渡してよいか」を分けている。

---

## まとめ

- override は RFC 7386 JSON Merge Patch 相当の汎用 dict マージ + Pydantic 再検証(`apply_overrides`)。
  ドメイン別の override コードは 1 行も無い。
- `problem_type` の変更は明示的に禁止(意図を明確にするガード。実質的には型システムも守っている)。
- Validation(Semantic Validation)はこの章の責務ではない ── 次章 `run_simulation` に委ねる。

## テスト観点(`tests/unit/test_simulation_overrides.py`)

> **対象**: `app.services.simulation.apply_overrides`(純粋関数)
> **ドライバ**: このテスト関数(既存 fixture の複数 problem_type を使い、ドメイン非依存であることを確認する)
> **スタブ不要** ── 対象が純粋(副作用なし)で外部依存を呼ばないため

| ケース                                               | 期待                                         |
| ------------------------------------------------- | ------------------------------------------ |
| route の `data.goal` をスカラー上書き                      | override 後の値に変わり、元の problem は不変            |
| project の `data.resource_capacity` を上書き(別 domain) | ドメイン非依存で同じ関数が動く                            |
| `data.edges` を丸ごと置換                               | list は要素マージせず丸ごと置換される(RFC 7386 の仕様)        |
| `problem_type` を変えようとする                           | `ValueError`                               |
| 構造的に無効な override(存在しない型の値)                        | `pydantic.ValidationError`(例外にせず拾うのは次章の責務) |

`uv run pytest tests/unit/test_simulation_overrides.py` / `uvx pyright app/schemas/simulation.py app/services/simulation.py`。

---

次章([Phase-10-2](./Phase-10-2.md))では、作業単位 10-2 ── `apply_overrides` を使って
base + シナリオ群を実際に解き、比較結果を組み立てる `SimulationService.run_simulation` を
実装する。
