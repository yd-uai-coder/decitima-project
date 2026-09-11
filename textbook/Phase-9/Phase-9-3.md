# Phase 9-3: KnapsackDpLogisticsStrategy(作業単位 9-3)

## この章のゴール

Phase 9 の主力 strategy。`knapsack_2d`(Phase 7-2)を配送計画に適用する ── 車両を1台ずつ、
残っている配送先から「容量(重量×体積)に収まる部分集合」を DP で選び、
`logistics_common.route_for_vehicle`(9-2)で巡回順と実距離を確定する。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/knapsack_dp_logistics.py`
(新規)、`tests/unit/test_knapsack_dp_logistics.py`(新規)。既存ファイルへの変更は無い ──
9-2 までのファイルだけで完結する。

---

## 1. 価値を均一 1.0 にする理由 ── 「容量だけで詰める上界」

```python
# app/algorithms/optimization/knapsack_dp_logistics.py(要点。全文は samples)
items.append((wa, wb, 1.0))  # 価値均一 ── 台数当たりの搭載数を最大化(距離は無視)
```

Phase 7 の Knapsack DP は「place の value」を価値にして効用を最大化した。Phase 9 では
「効用」に相当する自然な量が無い(全配送先を運ぶのが前提で、選ぶかどうかの余地は無い)。
そこで**価値を全アイテム均一 1.0** にする ── これは「1台の車両に**できるだけ多くの配送先を
詰め込む**」という、容量制約下のビンパッキングの貪欲な近似になる。**移動距離は一切見ない**
── これが Phase 7「移動費用を無視した上界」、Phase 8「資源を無視した下界」に続く、Phase 9 の
教材の核「**容量だけを見て詰める = 移動距離を無視した上界**」である。

容量そのものは `knapsack_2d` が厳密に守るので、選んだ組合せが容量を超えることは無い
(travel/project と違って `invalid` にはならない)。ただし選んだ組合せが地理的に離れていれば、
台数当たりの搭載数は最大でも移動距離では損をすることがある ── `greedy`(9-4)は 1 件ずつ
実際の距離増分を見て詰めるので、しばしばこちらの方が効率が良い。9-7 のプロパティテストで
`brute_force` を正解オラクルに `quality_ratio` を比較する。

---

## 2. 車両ごとのループ ── 単体で載らない配送先は事前に除く

```python
for vehicle in data.vehicles:
    if not remaining:
        break
    cap_a, cap_b = math.floor(vehicle.capacity_weight), math.floor(vehicle.capacity_volume)
    items, kept_ids = [], []
    for did in list(remaining):
        d = remaining[did]
        wa, wb = math.ceil(d.demand_weight), math.ceil(d.demand_volume)
        if wa > cap_a or wb > cap_b:
            continue  # 単体でこの車両に載らない
        items.append((wa, wb, 1.0)); kept_ids.append(did)
    picked_idx = set(knapsack_2d(items, cap_a, cap_b))
    chosen = [kept_ids[i] for i in range(len(kept_ids)) if i in picked_idx]
    ...
    for did in chosen:
        del remaining[did]
if remaining:
    return infeasible_logistics_solution(self.meta)   # 車両を使い切っても運びきれない
```

- 容量を整数グリッド化するときの向きは Phase 7 と同じ ── **需要は切り上げ(`ceil`)、容量は
  切り捨て(`floor`)**(保守側に丸める。小数の需要が実際より多く見積もられることはあっても、
  少なく見積もられて容量オーバーになることは無い)。
- 車両を使い切ってもまだ `remaining` が残っていれば `infeasible`(9-1 の semantic チェックは
  「明らかに無理」だけを弾く粗い必要条件だったので、ここで初めて「地理的な組合せとしても
  無理」なケースを検出できる)。

---

## 3. まとめ

- `knapsack_2d` の 2 人目の消費者。シグネチャ・実装は Phase 7-2 から**1バイトも変えない**。
- 「価値均一 = 台数最大化 = 移動距離を無視した上界」が Phase 9 の教材の核。
- 容量は厳密に守るので `invalid` にはならない(Phase 7/8 との違い)── 質の劣化は
  `quality_ratio` で示す(9-7)。

## テスト観点(`textbook/samples/tests/unit/test_knapsack_dp_logistics.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
>
> - **対象**: `KnapsackDpLogisticsStrategy.solve`
> - **ドライバ**: このテスト関数。`build_logistics_problem`(9-1)で入力生成
> - **スタブ**: **不要** ── strategy は `OptimizationProblem -> CandidateSolution` の純粋関数

| ケース | 期待 |
| --- | --- |
| 例題を解く | `status == "valid"`、`produced_by.name == "knapsack_dp"` |
| 同じ入力を2回解く | 完全に同じ `CandidateSolution`(決定論) |
| 例題の手計算との突き合わせ | `{P1,P2}` + `{P3}`、`total_distance == 21.0` |
| 容量の再チェック | どの車両も申告済みの容量を超えない |
| 車両1台だけ(合計需要 > 容量) | `status == "infeasible"` |

`uv run pytest tests/unit/test_knapsack_dp_logistics.py` / `uvx pyright app/algorithms/optimization`。

---

次章([Phase-9-4](./Phase-9-4.md))では、作業単位 9-4 ── `GreedyLogisticsStrategy`(実際の
挿入距離増分を都度計算する、必ず valid な貪欲法)と `BruteForceLogisticsStrategy`
(全割当×全順列を尽くす、小規模専用の正解オラクル)を実装する。
