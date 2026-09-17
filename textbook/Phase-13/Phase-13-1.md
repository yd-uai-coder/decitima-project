# Phase 13-1: スキーマ + アルゴリズムカタログの共有化(作業単位 13-1)

## この章のゴール

`POST /api/v1/solutions/{solution_id}/explain` の API 契約(`ExplanationResponse`)と、LLMの構造化出力契約(`LlmExplanation`)を定義する。あわせて、Phase 12 の `_ALGORITHM_DESCRIPTIONS`(`algorithm_recommendation.py` 内の非公開定数)を `app/domain/problems/algorithm_catalog.py`
へ抽出し、Phase 13 の2人目の消費者として使えるようにする ── この章の核は**共通化の判断**。

**この章で作成/更新するファイル**: `app/schemas/explanation.py`(新規)、
`app/domain/problems/algorithm_catalog.py`(新規、Phase 12 から抽出)、
`app/services/algorithm_recommendation.py`(改訂、import に変更)、
`tests/unit/test_explanation_schemas.py`(新規)、`tests/unit/test_algorithm_catalog.py`(新規)。

---

## 1. `_ALGORITHM_DESCRIPTIONS` を共有化してよいか ── 進行のルール #17 で判定する

Phase 12 の `_ALGORITHM_DESCRIPTIONS`(`(problem_type, meta.name) → 説明文` の辞書)は、当時`algorithm_recommendation.py` の中に非公開定数として置かれていた。Phase 13 は「他の候補との違い」を説明する材料として同じデータを必要とする。ここで進行のルール #17 の判定基準
「この共通化を今駆動している実在の消費者は何か」に当てはめると:

- 駆動している消費者: `SolutionExplanationService`(13-2、この Phase の実在の実装)
- 「将来たぶん使うかも」ではなく、**今この章で書くコードが実際に import する**

この基準を満たすので共有化を実施する。式・値そのものは Phase 12 から一切変えず、置き場と公開範囲だけを変える(Q38 の `shift_metrics.py` 抽出と同型)。

```python
# app/domain/problems/algorithm_catalog.py
"""registry に登録された全アルゴリズムの静的な1行説明。

Phase 12 では `algorithm_recommendation.py` 内の非公開定数(`_ALGORITHM_DESCRIPTIONS`)
だった。Phase 13-1 で `SolutionExplanationService` が2人目の消費者になったため公開モジュール
へ抽出した(進行のルール #17)。値は Phase 12 から不変。
"""

ALGORITHM_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("route_planning", "dijkstra"): "非負辺の単一始点最短路。手実装、既定の選択。",
    # ...(全24エントリ、内容は Phase 12 のまま)
}


def describe_algorithm(problem_type: str, name: str) -> str:
    """静的説明表から1行説明を引く。未登録なら空文字(緩いフォールバック)。"""
    return ALGORITHM_DESCRIPTIONS.get((problem_type, name), "")
```

置き場は `app/domain/problems/`(domain 層)── `AlgorithmMeta` や `OptimizationProblem` と同じく「純粋なデータ・型・事実」を置く層であり、`app/services/algorithm_recommendation.py`
(services 層)からも `app/services/explanation.py`(13-2、services 層)からも import できる
(services → domain は許可された依存方向)。`app/algorithms/registry.py` を import しない純粋データなので、domain 層のまま置いてよい(`domain → algorithms` 禁止に抵触しない)。

## 2. 命名規約 ── 2人目の消費者を得た瞬間に「先頭 `_`」を外す

CLAUDE.md の命名規約(先頭アンダースコアは「モジュール外から import させない内部部品」の印)に従い、`_ALGORITHM_DESCRIPTIONS`/`_describe` は **公開**モジュールへ移す際に`ALGORITHM_DESCRIPTIONS`/`describe_algorithm` へ改名する。これは Phase 6 の
`_CHECKERS`(モジュール内)→ Phase 2 の `CHECKERS`(domain の公開レジストリになったので`_` を外した)と同じ判断の型 ──「この名前を外から使ってよいか」という設計判断そのもの。

`algorithm_recommendation.py` 側は削除 + import に置き換えるだけ:

```python
# app/services/algorithm_recommendation.py(改訂、要点)
# (Phase 13-1) アルゴリズムの静的説明表(旧 `_ALGORITHM_DESCRIPTIONS`)は
# `app.domain.problems.algorithm_catalog` に抽出した。値は不変。
from app.domain.problems.algorithm_catalog import describe_algorithm

# ...
description=describe_algorithm(problem_type, strategy.meta.name),  # 旧 _describe(...)
```

呼び出し箇所(`_build_recommendation`/`_recommend_prompt`)はそのまま `describe_algorithm(...)`
に置き換えるだけで、既存 `test_algorithm_recommendation_service.py` は**無改造のまま**再実行して緑になる ── これが進行のルール #12.4「リファクタの写経ミス検知スモーク」。

> **写経の罠**: 抽出後、`algorithm_recommendation.py` に `_ALGORITHM_DESCRIPTIONS`/`_describe`
> の定義を消し忘れたまま新しい import を追加すると、pyright は警告しないが(未使用のprivate 定数は許容される設定)、ruff の F401/F811 が反応する。両方消してから import を足すこと。

## 3. スキーマ ── API 契約と LLM 契約を同じファイルに置く(Phase 12 と同じ流儀)

```python
# app/schemas/explanation.py
from pydantic import BaseModel, Field
import uuid


class LlmExplanation(BaseModel):
    """LLM の構造化出力全体(README §13 の説明対象5項目そのまま)。"""

    why_this_solution: str  # なぜこの解になったか
    key_constraints: str  # どの制約が重要だったか
    algorithm_rationale: str  # どのアルゴリズムを使ったか、その特徴
    alternatives_comparison: str  # 他の候補アルゴリズムとの違い
    improvement_notes: str  # 改善余地


class ExplanationResponse(BaseModel):
    """POST /api/v1/solutions/{solution_id}/explain のレスポンス。"""

    solution_id: uuid.UUID
    problem_type: str
    algorithm_name: str
    why_this_solution: str
    key_constraints: str
    algorithm_rationale: str
    alternatives_comparison: str
    improvement_notes: str
    notes: list[str] = Field(default_factory=list)
```

`LlmExplanation` の5フィールドは README §13 の説明対象5項目に1:1対応する。
`ExplanationResponse` はそれを `solution_id`/`problem_type`/`algorithm_name`(どの解を説明したか)と `notes`(LLM失敗時の補足)で包む ── Phase 12 の `RecommendRequest`/`RecommendationResponse`と `LlmRecommendation` の関係と同型。`ExplanationResponse` にはリクエストスキーマが無い
(`solution_id` は URL パスパラメータで渡るため、body は空)。

---

## まとめ

- `_ALGORITHM_DESCRIPTIONS` は Phase 13 が2人目の消費者になったため
  `app/domain/problems/algorithm_catalog.py` へ抽出し、`ALGORITHM_DESCRIPTIONS`/`describe_algorithm`(公開)に改名した(進行のルール #17)。値は不変。
- `algorithm_recommendation.py` は import に置き換えるだけ。既存テストは無改造で緑(#12.4 のスモーク)。
- `app/schemas/explanation.py` は Phase 12 と同じ「API契約 + LLM契約 同一ファイル」パターン。
  5フィールドは README §13 の説明対象5項目に1:1対応する。

## テスト観点(`tests/unit/test_algorithm_catalog.py` / `tests/unit/test_explanation_schemas.py`)

> **対象**: `describe_algorithm`/`ALGORITHM_DESCRIPTIONS`(カタログ)/ `LlmExplanation`・`ExplanationResponse`(スキーマ)
> **ドライバ**: このテスト関数
> **スタブ不要 ── 対象が純粋(副作用なし)で外部依存を呼ばないため**

| ケース                                                                    | 期待                                                    |
| ---------------------------------------------------------------------- | ----------------------------------------------------- |
| `describe_algorithm("route_planning", "dijkstra")`                     | Phase 12 と同じ説明文が返る                                    |
| `describe_algorithm("route_planning", "no_such_algorithm")`            | 空文字(緩いフォールバック)                                        |
| `all_strategies()` の全 `(problem_type, name)`                           | `ALGORITHM_DESCRIPTIONS.keys()` の部分集合になっている(1対1対応の維持) |
| `LlmExplanation.model_validate({"why_this_solution": "x"})`(他4フィールド省略) | `ValidationError`(5フィールドすべて必須)                        |
| `ExplanationResponse(...)`(`notes` 省略)                                 | `notes == []`                                         |

`uv run pytest tests/unit/test_algorithm_catalog.py tests/unit/test_explanation_schemas.py
tests/unit/test_algorithm_recommendation_service.py`(最後は #12.4 のスモーク、無改造)。
`uvx pyright app/domain/problems/algorithm_catalog.py app/schemas/explanation.py
app/services/algorithm_recommendation.py`。

---

次章([Phase-13-2](./Phase-13-2.md))では、作業単位 13-2 ── `SolutionExplanationService`
(DB読み取り・比較材料の組み立て・LLM呼び出し・フォールバック)を実装する。
