# Phase 9-6: PuLP で使用台数最小化の MILP を解く(作業単位 9-6)

## この章のゴール

産業ソルバートラック(README §8「実装方針」の 2 トラック方針)を Phase 9 に導入する。
手実装 4 strategy(9-3〜9-5)はいずれも「総移動距離の最小化」を目的にしていたが、
`PulpMilpLogisticsStrategy` は README §12.5 の評価項目「車両稼働率」に対応する
**別の目的関数 ── 使用台数の最小化** を、PuLP(CBC バックエンド)で厳密に解く。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/pulp_logistics.py`(新規)、
`tests/unit/test_pulp_logistics.py`(新規)。`pulp` を `[project].dependencies` に追加
(`uv add pulp`。Phase 6-7 で `ortools` を追加したのと同じ手順)。既存ファイルへの変更は無い。

---

## 1. スコープの決定 ── 「割当だけ MILP、経路順序は TSP 近似に委譲」

README Phase 9 節は「MILP 化する場合は `pulp` / `scipy` を追加」とだけ書いており、何を MILP
化するかは決めていない。フル CVRP を MILP で定式化する(劣周回除去制約を伴う経路変数)ことも
できるが、変数が爆発しやすく教材としてのコストに見合わない(進行のルール #17 の判定基準
「今この Phase を駆動する実在の消費者は何か」に照らし、教材が要求するのは「2 トラックの比較」
であって「フル CVRP の MILP 定式化」ではない)。

そこで **「配送先→車両の割当」だけを MILP にし、割当後の巡回順序は既存の
`optimize_waypoint_order`(TSP 近似)に委譲する**。これは Phase 8 の
`OrToolsCpSatProjectStrategy` が「CPM は依存関係だけ、資源は CP-SAT」と役割分担したのと同じ
設計判断 ── **MILP が担うのは組合せ構造の一部だけ**で、既存プリミティブを再利用できるところは
再利用する。

---

## 2. ビンパッキング MILP ── 「使用台数の最小化」

```python
# app/algorithms/optimization/pulp_logistics.py(要点。全文は samples)
x = {(v.id, d.id): pulp.LpVariable(...) for v in vehicles for d in deliveries}  # 割当
y = {v.id: pulp.LpVariable(...) for v in vehicles}                              # 使用フラグ

prob += pulp.lpSum(y.values())                                    # 目的: Σ y[v] を最小化

for d in deliveries:
    prob += pulp.lpSum(x[v.id, d.id] for v in vehicles) == 1       # 各配送先はちょうど1台

for v in vehicles:
    prob += pulp.lpSum(x[v.id, d.id] * d.demand_weight for d in deliveries) <= v.capacity_weight * y[v.id]
    prob += pulp.lpSum(x[v.id, d.id] * d.demand_volume for d in deliveries) <= v.capacity_volume * y[v.id]
    for d in deliveries:
        prob += x[v.id, d.id] <= y[v.id]                           # 使わない車両には割り当てない

prob.solve(pulp.PULP_CBC_CMD(msg=False))
```

- 古典的な **ビンパッキング問題**の MILP 定式化(容量 = ビンの大きさ、配送先 = 荷物)。
  `y[v]` が「この車両を使うかどうか」のフラグで、`x[v][d] <= y[v]` が「使わない車両には
  何も積めない」を保証する。
- 手実装 4 strategy はどれも明示的に「使用台数」を最小化しようとはしていない(容量が許す限り
  何台使っても構わない)。PuLP は**この点で手実装と質的に異なる保証**を持つ ── 3 台目の
  車両が使えても、容量的に 2 台で足りるなら必ず 2 台に収める(スタンドアロン検証で確認済み)。
- 決定論: CBC は同一入力に対し安定した**最適値**を返す(MILP は目的関数値が一意。解が複数
  タイになる場合の変数の選び方まではソルバー内部の探索順序に依存するが、`vehicles_used` や
  `total_distance` のような報告指標は安定する)。OR-Tools CP-SAT のような `random_seed` 固定は
  不要 ── `msg=False` でログを静音化するだけ。
- `_ops` は出さない(2 トラック比較の観察点として、仕事はソルバーの中にある)。

---

## 3. まとめ

- PuLP は「距離」でなく「**台数**」を最小化する、他の 4 strategy とは異なる目的関数を持つ ──
  2 トラック比較(README §8)が「同じ問題を違う切り口で最適化する」ことまで示せる好例になる。
- 経路順序は 9-2 の `route_for_vehicle`(TSP 近似)にそのまま委譲 ── MILP 層と TSP 層が
  疎結合なので、将来フル CVRP の MILP 化に発展させる余地も残る(スコープ外として明示)。

## テスト観点(`textbook/samples/tests/unit/test_pulp_logistics.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
>
> - **対象**: `PulpMilpLogisticsStrategy.solve`
> - **ドライバ**: このテスト関数。`build_logistics_problem`(9-1)で入力生成
> - **スタブ**: **不要** ── strategy は純粋関数(CBC はプロセス内で完結する組み込みソルバー、
>   外部プロセス・ネットワークを使わない)

| ケース | 期待 |
| --- | --- |
| 例題を解く | `status == "valid"`、`implementation == "library:pulp"`、`_ops` 無し |
| 3 台目の余裕があっても | `vehicles_used == 2.0`(容量的に必要な最小台数) |
| 割当の網羅性 | 全配送先がちょうど1回ずつ登場 |
| Verification を通す | `status == "valid"`、violation 無し(容量・距離とも整合) |
| 車両が小さすぎる | `status == "infeasible"` |

`uv run pytest tests/unit/test_pulp_logistics.py` / `uvx pyright app/algorithms/optimization`。

---

次章([Phase-9-7](./Phase-9-7.md))では、作業単位 9-7 ── `registry.py` に 5 strategy を登録し、
`select_strategy` に既定分岐を足して end-to-end パイプラインを通す。`build_scaled_logistics_problem`
を使ったプロパティテストで、`brute_force` を正解オラクルに `quality_ratio` を比較する。
