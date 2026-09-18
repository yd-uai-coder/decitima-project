# Phase 14-6: ルート配線 + e2e(作業単位 14-6)

## この章のゴール

`POST /api/v1/compare` を新設し、`api_router` に配線する。既存ルートへの影響が無いことをe2e で確認する。

**この章で作成/更新するファイル**: `app/api/routes/comparison.py`(新規)、
`app/api/routes/__init__.py`(改訂)、`tests/api/test_comparison_api.py`(新規)。

---

## 1. なぜ新ファイルか ── 「Algorithm 同士の比較」と「LLM vs Algorithm の比較」は別の操作

`app/api/routes/benchmark.py`(Phase 3)は既に `POST /api/v1/benchmark`(複数アルゴリズムを横並び実測)を持つ。Phase 14 は一見似ているが:

- Benchmark は「同じ Algorithm Engine の中の複数実装」を比較する(全て決定論的、
  全て `REGISTRY` 登録済み)。
- Compare は「Algorithm Engine」と「LLM」という**性質の異なる2つの経路**を比較する(片方は非決定論的、`REGISTRY` に登録しない)。

Phase 9 の `routes/jobs.py`(ジョブキューという新しい横断的関心事)・Phase 11 の
`routes/structure.py`(LLM が初めて構造化問題を作る)と同じ判断基準で、**新しい操作対象には新しいファイル**を割り当てる(CLAUDE.md「操作で割る」既存方針)。

## 2. ルート本体 ── 薄いラッパ、GET は無い

```python
# app/api/routes/comparison.py(新規、全文)
router = APIRouter(tags=["comparison"])


@router.post("/compare", response_model=ComparisonResponse)
async def compare_llm_vs_algorithm(
    payload: ComparisonRequest,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> ComparisonResponse:
    """同一問題を Algorithm 経路と LLM Only 経路の両方で解き、6軸で比較する。"""
    return await ComparisonService(redis).compare(
        user_id=current_user.id,
        request=payload,
        bypass_rate_limit=current_user.is_superuser,
    )
```

`SessionDep` を要らない ── `ComparisonService` は DB を一切触らない(Phase 10
`routes/simulate.py`・Phase 12 `routes/algorithms.py::recommend` と同じ「永続化しない補助エンドポイント」の形)。`GET /compare/{id}` のような読み出しエンドポイントも無い(永続化しないので読み出す対象が存在しない)。

## 3. `api_router` への配線

```python
# app/api/routes/__init__.py(改訂)
from app.api.routes.comparison import router as comparison_router  # (Phase 14-6)
...
api_router.include_router(benchmark_router)
api_router.include_router(comparison_router)  # (Phase 14-6)
```

`benchmark_router` の直後に置く ── 「比較」という操作のファミリーとして隣接させる
(実際の URL パスは重ならない: `/benchmark` と `/compare`)。

## 4. e2e ── 配線の確認に対象を絞る

```python
# tests/api/test_comparison_api.py(新規、要点)
async def test_compare_route_returns_both_paths(api, monkeypatch) -> None:
    client, _user = api
    _patch_llms(monkeypatch)  # route_llm.get_gemini_llm と comparison.get_gemini_llm を差し替え
    problem = build_route_problem()

    resp = await client.post(
        "/api/v1/compare", json={"problem": problem.model_dump(mode="json"), "llm_runs": 2},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["algorithm_used"]["name"] == "dijkstra"
    assert len(body["llm_results"]) == 2
    assert body["metrics"]["constraint_compliance_rate_llm"] == 1.0


async def test_compare_rejects_llm_runs_out_of_range(api, monkeypatch) -> None:
    ...
    resp = await client.post(
        "/api/v1/compare", json={"problem": problem.model_dump(mode="json"), "llm_runs": 50},
    )
    assert resp.status_code == 422  # ComparisonRequest.llm_runs は Field(le=20)


async def test_solve_route_still_works_after_compare_added(api) -> None:
    """既存 POST /solve への配線を壊していないことの回帰確認。"""
    ...
```

サービス層の振る舞い(集計・エラー率・フォールバック)は `test_comparison_service.py`
(14-5)で確認済みのため、ここでは「API として正しく配線されているか」「既存ルートを
壊していないか」「リクエストバリデーションが効くか」だけに対象を絞る
(`test_explanation_api.py`/`test_algorithm_recommendation_api.py` と同じ役割分担)。

---

## まとめ

- `POST /api/v1/compare` は Benchmark とは別ファイル ── 比較対象・目的が異なる新しい操作。
- e2e はサービス層のロジックを再テストせず、配線と回帰確認だけに絞る。

## テスト観点(`tests/api/test_comparison_api.py`)

> **対象**: `POST /api/v1/compare`
> **ドライバ**: `api` fixture(認証込み client)
> **スタブ**: `FakeLLM`(`app.algorithms.llm.route_llm.get_gemini_llm`・
> `app.services.comparison.get_gemini_llm` を monkeypatch)

| ケース                                          | 期待                                                        |
| -------------------------------------------- | --------------------------------------------------------- |
| route を Algorithm(dijkstra)+ LLM Only(2回)で比較 | 200、`algorithm_used.name == "dijkstra"`、`llm_results` が2件 |
| `llm_runs=50`(上限20超過)                        | 422(Pydantic バリデーション)                                     |
| 既存 `POST /solve`                             | 引き続き200(回帰なし)                                             |

```bash
uv run pytest tests/api/test_comparison_api.py
uvx pyright app/api/routes/comparison.py app/api/routes/__init__.py
```

overlay 検証: `test_comparison_api.py` **3 passed**。backend 全体
`uv run pytest` **621 passed / 6 deselected**(既存602件は無改造で再実行し回帰なし)。

---

次章([Phase-14-7](./Phase-14-7.md))では、作業単位 14-7 ──
UI(比較カード)を実装し、6 Planner Panel に導線を追加する。
