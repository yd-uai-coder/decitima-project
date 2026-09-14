# Phase 9-4: GreedyLogisticsStrategy + BruteForceLogisticsStrategy(作業単位 9-4)

## この章のゴール

`knapsack_dp`(9-3)と対になる 2 本 ── **実際の移動距離を見ながら詰める貪欲法** と
**全割当を尽くす正解オラクル**。どちらも `logistics_common.route_for_vehicle`(9-2)を
繰り返し呼ぶだけで、新しいプリミティブは要らない。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/{greedy_logistics,
brute_force_logistics}.py`(新規)、`tests/unit/test_greedy_and_brute_force_logistics.py`(新規)。
既存ファイルへの変更は無い。

---

## 1. `GreedyLogisticsStrategy` ── 実消費を見ながら詰める

```python
# app/algorithms/optimization/greedy_logistics.py(要点。全文は samples)
for delivery in sorted(data.deliveries, key=lambda d: d.id):
    best_vehicle, best_increase = None, float("inf")
    for vehicle in data.vehicles:
        trial_stops = [...現在の割当 + この配送先...]
        if not capacity_ok(vehicle, trial_stops):
            continue                                    # 容量オーバーは最初から除外
        _, distance = route_for_vehicle(data.depot_id, trial_stops, dist)
        increase = distance - current_distance[vehicle.id]
        if increase < best_increase:
            best_increase, best_vehicle = increase, vehicle.id
    if best_vehicle is None:
        return infeasible_logistics_solution(self.meta)
    assignment[best_vehicle].append(delivery.id)
```

- 配送先を1件足すたびに `route_for_vehicle` を呼び直す ── **常に実際の巡回順・距離**で判断するので、`knapsack_dp` と違って「容量に収まるが遠回り」を見逃さない。
- 容量オーバーの候補を**最初から**除外するので、`knapsack_dp` のように「車両を使い切っても積み残る」ことはあっても、途中の割当がいつでも valid であることは保証される(travel の `GreedyTravelStrategy` と同じ「実消費を見ながら詰める」設計思想)。

---

## 2. `BruteForceLogisticsStrategy` ── 全割当 × 全順列の正解オラクル

```python
# app/algorithms/optimization/brute_force_logistics.py(要点。全文は samples)
for choice in product(range(len(vehicles)), repeat=len(deliveries)):
    buckets = {...choice に従って配送先を車両へ振り分け...}
    total = sum(route_for_vehicle(...).distance for vehicle が使う場合)
    if 全車両が容量・到達可能性を満たし total が最小なら記録
```

- `itertools.product(range(len(vehicles)), repeat=len(deliveries))` で「配送先ごとにどの車両か」を全通り試す(vehicles^n_deliveries 通り)。各割当について、車両ごとに`route_for_vehicle` で実際の巡回距離を計算し、合計が最小のものを選ぶ ── **移動距離も込みで評価する真の最適**。
- Phase 3/7 の `brute_force` と同じ位置づけ:小規模 fixture 専用の正解オラクル。
  9-7 の `quality_ratio`(`brute_force` を基準に他 4 strategy の総距離を比較)が使う。

---

## 3. まとめ

- 2 本とも `logistics_common.route_for_vehicle` を再利用するだけで、`knapsack_2d` のような新しいプリミティブは不要 ── Phase 9 の strategy はほぼ「配送先→車両の割当ロジック」の違いに集約される。
- `greedy` は**必ず valid**(容量オーバーを踏まない設計)。`brute_force` は**必ず最適**
  (指数時間なので小規模専用)。両者の間に `knapsack_dp`(高速だが移動距離を見ない)と`branch_and_bound`(9-5、下界つきの厳密探索)が位置する。

## テスト観点(`textbook/samples/tests/unit/test_greedy_and_brute_force_logistics.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `GreedyLogisticsStrategy.solve` / `BruteForceLogisticsStrategy.solve`
> - **ドライバ**: このテスト関数。`build_logistics_problem`(9-1)で入力生成
> - **スタブ**: **不要** ── いずれも純粋関数

| ケース                        | 期待                                           |
| -------------------------- | -------------------------------------------- |
| greedy が例題を解く              | `status == "valid"`、`total_distance == 21.0` |
| greedy は容量を超えない            | 全 route で weight/volume が capacity 以内        |
| greedy: 車両1台だけ             | `status == "infeasible"`                     |
| brute_force が例題を解く         | `total_distance == 21.0`(唯一の実行可能解と一致)        |
| brute_force は決定論的          | 同じ入力 → 完全に同じ出力                               |
| brute_force は容量を超えない       | 全 route で weight/volume が capacity 以内        |
| greedy ≥ brute_force(オラクル) | greedy の総距離が真の最適を下回ることはない                    |

`uv run pytest tests/unit/test_greedy_and_brute_force_logistics.py` /
`uvx pyright app/algorithms/optimization`。

---

次章([Phase-9-5](./Phase-9-5.md))では、作業単位 9-5 ── `BranchAndBoundLogisticsStrategy`。
配送先→車両の割当を DFS + 分枝限定で探索し、Phase 6 のノード予算パターン(`_MAX_NODES`)を2 人目の消費者として再利用する。
