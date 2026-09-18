# Phase 14-4: LLM Only 戦略(最適化系)(作業単位 14-4)

## この章のゴール

`travel_planning` と `logistics_planning` の `LlmOnly*Strategy` を実装する。この2ドメインは既存の `SolutionVerificationService` が**移動コストを Floyd-Warshall で再計算して検算する**
(Phase 7-4 の `_verify_travel_plan`、Phase 9-2 の `_verify_logistics_routes`)── LLM が「選択」だけでなく「巡回コストの暗算」も申告する必要があり、6ドメイン中もっとも検算が厳しく効く2つ。これで6ドメイン全ての `LlmOnly*Strategy` が揃う。

**この章で作成/更新するファイル**: `app/algorithms/llm/travel_llm.py`・`logistics_llm.py`(新規)、`tests/unit/test_llm_only_strategies.py`(travel/logistics 分を追記)。

---

## 1. `LlmOnlyTravelStrategy` ── 予算・時間内で価値最大化 + 巡回コストの検算

```python
# app/algorithms/llm/travel_llm.py(新規、要点)
def _prompt(problem: OptimizationProblem, data: TravelData) -> str:
    places = "\n".join(
        f"- {p.id}: {p.name or p.id}(価値 {p.value}、費用 {p.cost}、所要時間 {p.duration}、"
        f"好み係数 {data.preferences.get(p.id, 1.0)})"
        for p in data.places
    )
    legs = "\n".join(
        f"- {leg.id}: {leg.endpoints[0]} <-> {leg.endpoints[1]}"
        f"(移動費用 {leg.travel_cost}、移動時間 {leg.travel_time})"
        for leg in data.legs
    )
    start_line = f"、起点 {data.start}" if data.start else ""
    return (
        "次の旅行プラン問題を解いてください。予算・時間予算の範囲内で、好み加重の価値の合計"
        "(total_value)が最大になるよう訪問する place を選び(selected_place_ids)、その"
        f"巡回順(visit_order)を決めてください{start_line}。\n\n"
        f"訪問候補:\n{places}\n\n移動区間:\n{legs}\n\n"
        f"予算 {data.budget}、時間予算 {data.time_budget}\n\n"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}\n\n"
        "total_value / total_cost / total_time は実際に選んだ内容・移動と矛盾しないよう"
        "正しく計算してください。"
    )


class LlmOnlyTravelStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(TravelData, problem.data)
        # strip_problem_type: 判別子は LLM に見せない(Phase-14-2.md §4 の事象への対処)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(TravelSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = TravelSolution(
            problem_type="travel_planning", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

Phase 7 の教材の核は「DP は移動費用を無視した上界」だった ── `KnapsackDpTravelStrategy` はplace の cost/duration だけで詰め込み、移動分の予算超過を Verification が `invalid` にすることがある。LLM Only 戦略でも全く同じ検証(`_verify_travel_plan`、Floyd-Warshall で`visit_order` の実際の巡回コストを再計算し `total_cost`/`total_time` と突き合わせる)が適用される ── **LLM が移動コストを軽視する傾向を持つかどうかも、この Phase の実測で初めて分かる**。

## 2. `LlmOnlyLogisticsStrategy` ── 容量制約 + デポ発着の巡回距離の検算

```python
# app/algorithms/llm/logistics_llm.py(新規、要点)
def _prompt(problem: OptimizationProblem, data: LogisticsData) -> str:
    nodes = "\n".join(f"- {n.id}: {n.label or n.id}" for n in data.nodes)
    segments = "\n".join(
        f"- {s.id}: {s.source} <-> {s.target}"
        f"(距離 {s.distance}{'、一方通行(source→target)' if s.directed else ''})"
        for s in data.segments
    )
    vehicles = "\n".join(
        f"- {v.id}: 重量容量 {v.capacity_weight}、体積容量 {v.capacity_volume}"
        for v in data.vehicles
    )
    deliveries = "\n".join(
        f"- {d.id}: ノード {d.node_id}、需要(重量 {d.demand_weight} / 体積 {d.demand_volume})"
        for d in data.deliveries
    )
    return (
        "次の配送計画問題(CVRP)を解いてください。デポ(id=" + data.depot_id + ")から出発し、"
        "各配送先をちょうど1台の車両に(容量を超えない範囲で)割り当て、各車両の訪問順"
        "(stop_ids)を決めてください。使わない車両は routes に含めないでください。\n\n"
        f"ノード:\n{nodes}\n\n道路区間:\n{segments}\n\n車両:\n{vehicles}\n\n配送先:\n{deliveries}\n\n"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}\n\n"
        "各 route の distance、および total_distance(全 route の distance 合計)は、"
        "デポ発 → 訪問順 → デポ着の実際の道のりと矛盾しないよう正しく計算してください。"
    )


class LlmOnlyLogisticsStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(LogisticsData, problem.data)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(LogisticsSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = LogisticsSolution(
            problem_type="logistics_planning", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

`_verify_logistics_routes`(Phase 9-2)は容量チェック(`capacity_ok`)と距離の検算
(`route_distance`、Floyd-Warshall)の両方を行う。プロンプトで「使わない車両は routes に含めない」と明記しているのは、structure.py::verify_logistics_structure` が
「全配送先が重複なくちょうど1台に割り当て済みか」を検査するため ── 空の
`VehicleRoute(vehicle_id=..., stop_ids=[], distance=0)` を含めると `stop_ids` は空でも
`vehicle_id` の重複無しチェック自体は通るが、無駄な車両を使ったように見える(既存
`build_logistics_problem` の正解も2台のみ使う構成)。

## 3. テストは fixture の既知オラクル値をそのまま使う

```python
# tests/unit/test_llm_only_strategies.py(要点)
def test_logistics_llm_only_solves_to_valid(monkeypatch):
    problem = build_logistics_problem()
    solution = LogisticsSolution(
        routes=[
            VehicleRoute(vehicle_id="V1", stop_ids=["P1", "P2"], distance=9),
            VehicleRoute(vehicle_id="V2", stop_ids=["P3"], distance=12),
        ],
        total_distance=21,
    )
    ...
```

`tests/fixtures/optimization.py::build_logistics_problem` のコメントに「5 strategy が一致して 21 を出すはずの最小例」と明記されている値(Phase 9 で `knapsack_dp`/`greedy`/`branch_and_bound`/`brute_force`/`pulp_milp` の全てが一致することを確認済み)をそのままLLM Only の「正解」としても使う ── 新しい正解を手計算する必要が無い(travel も同様、既存 `build_travel_problem` は空の訪問でも valid になる形にして手計算を避けた、Phase-14-2.md 参照の「テストで検証したい対象を絞る」原則)。

---

## まとめ

- これで6ドメイン全ての `LlmOnly*Strategy` が揃った。実装パターンは
  「ドメインのカタログを自然言語化 → `strip_problem_type()` した既存Solution型への
  `with_structured_output()` → 同期 `invoke` → `problem_type` を足し戻して
  `CandidateSolution` に詰める」で完全に共通(`strip_problem_type` の必要性は
  `Phase-14-2.md` §4 で実運用検証から判明した)。
- travel/logistics は移動コストの検算(Floyd-Warshall)が既存 Verification に含まれるため、「選択は正しいが移動コストの申告が甘い」という LLM 特有の失敗モードを最も検出しやすい2ドメインになっている。

## テスト観点(`tests/unit/test_llm_only_strategies.py`)

> **対象**: `LlmOnlyTravelStrategy.solve` / `LlmOnlyLogisticsStrategy.solve`
> **ドライバ**: このテスト関数
> **スタブ**: `FakeLLM`(`app.algorithms.llm.travel_llm`/`logistics_llm` の `get_gemini_llm`
> をそれぞれ monkeypatch)。

| ケース                                            | 期待                                     |
| ---------------------------------------------- | -------------------------------------- |
| travel: 何も訪問しない最小解(予算・時間を使わない)                 | `status == "valid"`、`violations == []` |
| logistics: fixture の既知オラクル値(total_distance=21) | `status == "valid"`、`violations == []` |

```bash
uv run pytest tests/unit/test_llm_only_strategies.py
uvx pyright app/algorithms/llm tests/unit/test_llm_only_strategies.py
```

overlay 検証(6ドメイン分まとめて): `test_llm_only_strategies.py` **7 passed**
(6ドメインの valid ケース + route の「嘘」ケース1件)。

---

次章([Phase-14-5](./Phase-14-5.md))では、作業単位 14-5 ──
6戦略を横断する `ComparisonService`(集計・ナレーション生成)を実装する。
