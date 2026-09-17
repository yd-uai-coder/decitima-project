# Phase 12-1: スキーマ + 静的アルゴリズム説明表(作業単位 12-1)

## この章のゴール

`POST /api/v1/algorithms/recommend` の API 契約(`RecommendRequest`/`RecommendationResponse`/
`AlgorithmRecommendation`)と、LLM の構造化出力契約(`LlmRecommendation`)を定義する。
両方とも振る舞いを持たない純粋な Pydantic モデルであり、この章では実装ファイルを作るだけで
テストは書かない(12-2 のサービステストがインスタンス化を通じて間接的に検証する)。

**この章で作成するファイル**: `app/schemas/recommendation.py`(新規)、
`tests/unit/test_recommendation_schemas.py`(新規)。

---

## 1. なぜ2種類のスキーマを1ファイルに同居させるか

`app/schemas/structuring.py`(Phase 11)の流儀を踏襲し、**API 契約**(HTTP でやり取りする形)
と **LLM 契約**(`with_structured_output()` に渡す形)を同じファイルに置く。理由は Phase 11 と
同じ:2つは別の関心事に見えて「LLM 推薦という1つの機能の入出力」という単位で一緒に変わるため
(設計判断の型「一緒に変わるものを同じファイルに」)。

```python
# app/schemas/recommendation.py
from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.problems.problem import OptimizationProblem


class RecommendRequest(BaseModel):
    """POST /api/v1/algorithms/recommend のリクエスト。構造化済みの問題をそのまま渡す
    (`/verify` の `VerifyRequest` と同じ「DB を介さず body でそのまま受け取る」設計)。"""

    problem: OptimizationProblem
```

`RecommendRequest` は `/verify` の `VerifyRequest`(`problem: OptimizationProblem` +
`solution: CandidateSolution`)と同型の「構造化済みデータをそのまま body で受け取る」設計。
DB を介さないので `conversation_id` のような永続化の概念を持たない。

## 2. `AlgorithmRecommendation` / `RecommendationResponse`

```python
# app/schemas/recommendation.py(つづき)
class AlgorithmRecommendation(BaseModel):
    name: str
    family: str
    implementation: str
    time_complexity: str | None = None
    description: str
    is_rule_preferred: bool
    llm_rank: int | None = None
    llm_comment: str | None = None


class RecommendationResponse(BaseModel):
    problem_type: str
    rule_preferred: str
    recommendations: list[AlgorithmRecommendation]
    notes: list[str] = Field(default_factory=list)
```

`name`/`family`/`implementation`/`time_complexity` は既存 `AlgorithmMeta`
(`app/domain/solutions/solution.py`)からの転記。既存 `AlgorithmInfo`
(`app/schemas/optimization.py`、`GET /algorithms` が使う)と field 名が似ているが、
`AlgorithmInfo.problem_types: list[str]`(複数 problem_type にまたがる集約)は今回の文脈(単一問題に対する推薦)に合わないため、無理に共有せず別モデルとして定義する
(進行のルール #17: 構造が似ているだけでは共有理由にならない ── フィールドの意味が違う)。

`is_rule_preferred`/`llm_rank`/`llm_comment` が Phase 12 の新規概念:

- `is_rule_preferred`: 既存 `select_strategy` が選ぶ名前と一致するか
- `llm_rank`: LLM のおすすめ順(1 が最推奨)。LLM 未呼び出し/失敗時は `None`
- `llm_comment`: LLM が付けた一言。同上の理由で `None` になり得る

## 3. LLM 契約 ── `LlmRecommendation`

```python
# app/schemas/recommendation.py(つづき)
class LlmAlgorithmComment(BaseModel):
    name: str
    comment: str


class LlmRecommendation(BaseModel):
    ranked_names: list[str]
    comments: list[LlmAlgorithmComment]
```

`ranked_names`/`comments` の `name` は grounding 前(存在しない候補名を含み得る)。
存在確認は 12-2 の `AlgorithmRecommendationService.recommend()` が行う(スキーマ自体は検証しない ── Phase 11 の `TravelDataPatch` 等と同じ「スキーマは形、意味の検証はサービス層」という役割分担)。

## 4. `_ALGORITHM_DESCRIPTIONS` のキー設計(12-2 の前提として重要)

12-2 で実装する静的説明表は、**`meta.name` 単体ではなく `(problem_type, meta.name)` のタプルをキーにする**。理由は registry の実データを見ると分かる:

| name                 | 登場する problem_type                                            |
| -------------------- | ------------------------------------------------------------ |
| `"greedy"`           | shift_scheduling / travel_planning / logistics_planning(3実装) |
| `"brute_force"`      | route_planning / travel_planning / logistics_planning(3実装)   |
| `"branch_and_bound"` | shift_scheduling / logistics_planning(2実装)                   |
| `"knapsack_dp"`      | travel_planning / logistics_planning(2実装)                    |
| `"cp_sat"`           | shift_scheduling / project_scheduling(2実装)                   |

`name` だけをキーにすると、例えば `"greedy"` の説明が travel 用の文言で shift 用を
上書きしてしまう ── これは教材化前の設計検討で実際に見つけて直した箇所であり、
「一見グローバルに見える識別子が実はドメインごとに別物」というよくある罠の実例。

---

## まとめ

- API 契約(`RecommendRequest`/`RecommendationResponse`/`AlgorithmRecommendation`)と
  LLM 契約(`LlmRecommendation`/`LlmAlgorithmComment`)を Phase 11 と同じ流儀で1ファイルに同居させた。
- `AlgorithmRecommendation` は既存 `AlgorithmInfo` と似て見えるが、`problem_types` の意味が合わないため無理に共有しない。
- `_ALGORITHM_DESCRIPTIONS`(12-2)のキーは `(problem_type, name)` にする ── `name` 単体はドメインをまたいで重複するため。

## テスト観点(`tests/unit/test_recommendation_schemas.py`)

> **対象**: `app.schemas.recommendation` の各 BaseModel(型定義のみ)
> **ドライバ**: このテスト関数
> **スタブ不要 ── 対象が純粋なデータ定義で外部依存を呼ばないため**(用語初出:
> SUT=テスト対象、ドライバ=テストを実行するもの、スタブ=外部依存の代役)

| ケース | 期待 |
| --- | --- |
| `RecommendRequest(problem=build_travel_problem())` | `request.problem.problem_type == "travel_planning"` |
| `AlgorithmRecommendation(...)`(`llm_rank`/`llm_comment` 省略) | 両方とも `None` がデフォルト |
| `RecommendationResponse(...)`(`notes` 省略) | `notes == []` |
| `LlmRecommendation(ranked_names=[...], comments=[...])` | 値がそのまま保持される |

`uv run pytest tests/unit/test_recommendation_schemas.py` /
`uvx pyright app/schemas/recommendation.py tests/unit/test_recommendation_schemas.py`。

---

次章([Phase-12-2](./Phase-12-2.md))では、作業単位 12-2 ── `AlgorithmRecommendationService`
(rule 再利用・LLM 呼び出し・grounding・マージ)を実装する。
