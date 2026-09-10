# Phase 7-5: Greedy + BruteForce オラクル + registry + select + end-to-end(作業単位 7-5)

## この章のゴール

DP(7-2〜7-4)に加えて 2 つの手実装 strategy を作り、`registry` に `"travel_planning"` キーを
新設して端から端まで通す:

- **`GreedyTravelStrategy`** ── 効用 ÷(追加でかかる資源)の比が高い place から詰める。DP と違い**1 つ選ぶたびに実際の巡回コスト・時間を計算し直す**ので、必ず予算・時間内。最適性は保証しない。
- **`BruteForceTravelStrategy`** ── place の部分集合を全列挙し、移動込みで真に最適なプランを返す。
  Phase 3 の `BruteForceRouteStrategy` / Phase 6 の `_brute_force_optimal` と同じ **正解オラクル**。

**この章で作成 / 更新するファイル**:
`app/algorithms/optimization/greedy_travel.py`・`app/algorithms/optimization/brute_force_travel.py`(新規)、
`tests/unit/test_travel_strategies.py`(新規 ── Greedy / BruteForce / registry / select / e2e。
訪問順・DP strategy のテストは 7-4 の `test_travel_common.py`)。
**既存への変更**(現行版は samples): `app/algorithms/registry.py`(`"travel_planning"` に 3 strategy、
冒頭系譜に `改訂 Phase 7`)、`app/services/algorithm_selection.py`(`_preferred_name` に travel 分岐)、
`tests/unit/test_algorithm_selection.py`(travel の select テスト)。

対応サンプル: 上記すべて。設計は README §19、`CLAUDE.md`「アルゴリズム実装方針 — 2 トラック」。

---

## 1. `GreedyTravelStrategy` ── 移動込みで逐次

```python
# app/algorithms/optimization/greedy_travel.py(要点。全文は samples)
class GreedyTravelStrategy:
    meta = AlgorithmMeta(name="greedy", family="optimization", implementation="handwritten", ...)

    def solve(self, problem):
        data, forbidden, required = parse_travel_problem(problem)
        cost_dist, time_dist = all_pairs(data)
        selected = [rid for rid in sorted(required) if rid not in forbidden]
        remaining = [p.id for p in data.places if p.id not in forbidden and p.id not in selected]
        ops = 0

        improved = True
        while improved:
            improved = False
            base = order_and_cost(data, selected, cost_dist, time_dist)
            base_cost, base_time = (base[1], base[2]) if base else (0.0, 0.0)
            best_gain, best_id = 0.0, None
            for pid in remaining:
                ops += 1
                trial = order_and_cost(data, [*selected, pid], cost_dist, time_dist)
                if trial is None:
                    continue
                _, cost, time = trial
                if cost > data.budget or time > data.time_budget:
                    continue                          # 入れると予算 or 時間オーバー
                spent = (cost - base_cost) + (time - base_time)     # 追加でかかる資源
                gain = place_utility(data, pid) / spent if spent > 0 else place_utility(data, pid)
                if gain > best_gain:
                    best_gain, best_id = gain, pid
            if best_id is not None:
                selected.append(best_id); remaining.remove(best_id); improved = True

        return travel_solution(data, selected, cost_dist, time_dist, ops, self.meta)
```

- **効率 = 効用 ÷ 追加でかかる資源**。「その place を足すと巡回コスト・時間が実際にいくら増えるか」を `order_and_cost` で測ってから比を取る ── DP が「place cost だけ」で判断するのと対照的。
- 1 手ごとに予算・時間をチェックして超えないものだけ足すので、**Greedy の解は必ず valid**。
- 貪欲なので最適を外しうる(Knapsack を貪欲で解くと最適でない、の travel 版)。
- `_ops` = place を追加候補として評価した回数。

---

## 2. `BruteForceTravelStrategy` ── 正解オラクル

```python
# app/algorithms/optimization/brute_force_travel.py(要点。全文は samples)
class BruteForceTravelStrategy:
    meta = AlgorithmMeta(name="brute_force", family="optimization", implementation="handwritten",
                         time_complexity="O(2^n * n!)", ...)

    def solve(self, problem):
        data, forbidden, required = parse_travel_problem(problem)
        cost_dist, time_dist = all_pairs(data)
        candidates = [p.id for p in data.places if p.id not in forbidden]
        req = [rid for rid in required if rid in candidates]
        free = [pid for pid in candidates if pid not in req]

        best_ids, best_value, ops = list(req), _plan_value(data, req, cost_dist, time_dist), 0
        for k in range(len(free) + 1):
            for combo in combinations(free, k):
                ops += 1
                ids = [*req, *combo]
                plan = order_and_cost(data, ids, cost_dist, time_dist)
                if plan is None: continue
                visit, cost, time = plan
                if cost > data.budget or time > data.time_budget: continue
                value = sum(place_utility(data, p) for p in visit)
                if value > best_value:
                    best_value, best_ids = value, ids
        return travel_solution(data, best_ids, cost_dist, time_dist, ops, self.meta)
```

- **移動費用も込みで評価する** ── DP の「移動無視の上界」とは違い、これは真の最適
  (`order_and_cost` で巡回順まで最適化してから予算チェック)。
- `O(2ⁿ)` 個の部分集合 × 各部分集合の巡回順最適化。n ≤ 12 くらいまで。registry には載せるが
  ベンチでは小規模のみ(`build_scaled_travel_problem(n_places=6)` のプロパティテスト)。
- Phase 3 の `BruteForceRouteStrategy`(全単純パス列挙)、Phase 5-2 の `_all_spanning_trees`、
  Phase 6 の `_brute_force_optimal` と同じ役割 ── **小規模で厳密解を出し、DP / Greedy の裏取り**。

---

## 3. registry と select_strategy(現行版)

```python
# app/algorithms/registry.py
"travel_planning": [                    # (Phase 7-5)
    KnapsackDpTravelStrategy(),         # 既定(select が返す先頭)
    GreedyTravelStrategy(),
    BruteForceTravelStrategy(),
],

# app/services/algorithm_selection.py::_preferred_name
if problem.problem_type == "travel_planning":     # (Phase 7-5)
    return "knapsack_dp"
```

- Phase 1 以来「registry に新 problem_type キーを足す」のは network(5-4)に続き 2 回目。
  `get_strategies` / `find_strategy` / `all_strategies` は無変更(`REGISTRY.get(pt, [])`)。
- **手実装 strategy を先頭に**(`find_strategy` の `requested` 一致は `next(...)` で先頭を返す)。
  `?algorithm=knapsack_dp` でも `knapsack_dp` でも既定でも DP が当たる。
- `select_strategy` は rule-based(`Phase-0-4.md` §6 の Step 1)── travel は常に `knapsack_dp`。
  「予算が厳しければ Greedy」のような賢い分岐は入れない(学習型は Phase 12)。
- **end-to-end パイプラインが緑になるのはこの章**(registry が埋まるまで `select_strategy` は
  `NoAlgorithmError`。Phase 5-3 → 5-4 の Q35 と同型)。

---

## 4. 「DP == BruteForce(小規模)」プロパティテスト

```python
# tests/unit/test_travel_strategies.py(要点)
def test_brute_force_is_the_oracle_dp_and_greedy_never_beat_it() -> None:
    for seed in range(6):
        problem = build_scaled_travel_problem(n_places=6, seed=seed)
        data = _tdata(problem); cost_dist, time_dist = all_pairs(data)
        best = _real_value(_BRUTE.solve(problem), data, cost_dist, time_dist)   # 移動込みの真値
        assert _real_value(_DP.solve(problem), data, cost_dist, time_dist) <= best + 1e-6
        assert _real_value(_GREEDY.solve(problem), data, cost_dist, time_dist) <= best + 1e-6
```

- **`_real_value`**: solution の `visit_order` で `tour_cost` を回し、予算・時間超過なら `-inf`、
  収まっていれば `total_value`。「DP が主張する価値」でなく「実際に回れるプランの価値」で比較する。
- DP は「移動無視の上界」なので **DP の解が invalid(移動込みで予算超過)なら `_real_value` は
  `-inf`** ── BruteForce に負けて当然。DP の解が valid なら BruteForce 以下(貪欲/DP は真の最適を
  出せないことがある)。
- seed を for ループで振る手書きジェネレータ(hypothesis は使わない ── Phase 3 と同じ判断)。

```python
def test_dp_can_overrun_because_it_ignores_travel_cost() -> None:
    problem = build_travel_problem(budget=20, time_budget=20)     # place 18 + 移動 5 = 23 > 20
    assert SolutionVerificationService().verify(problem, _DP.solve(problem)).status == "invalid"
    assert SolutionVerificationService().verify(problem, _GREEDY.solve(problem)).status == "valid"
```

これが **Phase 7 の教材の核** ── 同じ問題で DP は invalid、Greedy は valid。「DP は速いが移動を
無視する上界、Greedy は移動込みで安全」を 1 テストで見せる。

---

## 5. まとめ

- Greedy = 効用 ÷ 追加資源、1 手ごとに実際の巡回コストで判定 → 必ず valid、最適性なし。
- BruteForce = 部分集合の全列挙、移動込みで真の最適 → 正解オラクル(n ≤ 12)。
- registry に `"travel_planning"` 3 strategy、`select_strategy` に travel → `knapsack_dp`。
  end-to-end が緑になるのはこの章。
- 「DP == BruteForce(小規模)」「DP は invalid・Greedy は valid(移動込み)」で締める。

## テスト観点(`textbook/samples/tests/unit/{test_travel_strategies,test_algorithm_selection}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_travel_strategies.py`**(7-5 ── 訪問順・DP のテストは 7-4 の `test_travel_common.py`)
> 
> - **対象**: `GreedyTravelStrategy` / `BruteForceTravelStrategy` の `solve`、`select_strategy`、
>   `registry["travel_planning"]`、validate→select→solve→verify のパイプライン
> - **ドライバ**: このテスト関数 / fixture。`_tdata` / `_plan` / `_real_value` の型絞りヘルパ。
>   パイプラインは各段を直接呼ぶ(`test_mst_strategies.py` と同じ ── Redis は `SolveService` の
>   関心事で、ここでは扱わない)
> - **スタブ**: **不要** ── strategy / validation / verification はすべて純粋
> 
> **`test_algorithm_selection.py`**(travel 分を追記)
> 
> - **対象**: `select_strategy` の travel 分岐
> - **ドライバ**: このテスト関数。`build_travel_problem`
> - **スタブ**: **不要**

| ケース                                                  | 期待                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| Greedy 解(budget=20)                                  | `status == "valid"` / `total_cost <= budget` / `total_time <= time_budget`     |
| DP 解(budget=20)                                      | Verification 後 `status == "invalid"`(移動分で予算超過)                                 |
| BruteForce vs DP / Greedy(6 seeds、n=6)               | `_real_value(BruteForce) >= _real_value(DP / Greedy)`                          |
| 3 strategy の決定論                                      | `solve(p).model_dump() == solve(p).model_dump()`                               |
| `REGISTRY["travel_planning"]` の名前                    | `["knapsack_dp", "greedy", "brute_force"]`                                     |
| `find_strategy` / `select_strategy` の既定              | `knapsack_dp`                                                                  |
| `select_strategy(problem, "brute_force")`            | `brute_force`                                                                  |
| end-to-end パイプライン                                    | `verified.status == "valid"` / `assignments.problem_type == "travel_planning"` |
| `NumericBoundConstraint(total_cost <= 1, hard)` を付ける | `verified.status == "invalid"`                                                 |

`uv run pytest tests/unit/test_travel_strategies.py tests/unit/test_algorithm_selection.py` /
`uvx pyright app tests`。

---

次章([Phase-7-6](./Phase-7-6.md))では、作業単位 7-6 ── 分析トラック。`analysis/travel_analysis.py`
を Phase 3-8 の `analysis/` に 1 本足し(移設・作り直しなし)、「DP(移動無視の上界)と Greedy
(移動込み)の解の価値がどれだけ食い違うか」「規模を上げると DP が invalid になる割合」を
固定サンプル + notebook で見る。
