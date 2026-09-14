# Phase 9-6: PuLP で使用台数最小化の MILP を解く(作業単位 9-6)

## この章のゴール

産業ソルバートラック(README §8「実装方針」の 2 トラック方針)を Phase 9 に導入する。
手実装 4 strategy(9-3〜9-5)はいずれも「総移動距離の最小化」を目的にしていたが、
`PulpMilpLogisticsStrategy` は README §12.5 の評価項目「車両稼働率」に対応する
**別の目的関数 ── 使用台数の最小化** を、PuLP(CBC バックエンド)で厳密に解く。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/pulp_logistics.py`(新規)、
`tests/unit/test_pulp_logistics.py`(新規)。`pulp` を `[project].dependencies` に追加(`uv add pulp`。Phase 6-7 で `ortools` を追加したのと同じ手順)。既存ファイルへの変更は無い。

---

## 1. スコープの決定 ── 「割当だけ MILP、経路順序は TSP 近似に委譲」

README Phase 9 節は「MILP 化する場合は `pulp` / `scipy` を追加」とだけ書いており、何を MILP化するかは決めていない。フル CVRP を MILP で定式化する(劣周回除去制約を伴う経路変数)こともできるが、変数が爆発しやすく教材としてのコストに見合わない(進行のルール #17 の判定基準
「今この Phase を駆動する実在の消費者は何か」に照らし、教材が要求するのは「2 トラックの比較」であって「フル CVRP の MILP 定式化」ではない)。

そこで **「配送先→車両の割当」だけを MILP にし、割当後の巡回順序は既存の
`optimize_waypoint_order`(TSP 近似)に委譲する**。これは Phase 8 の
`OrToolsCpSatProjectStrategy` が「CPM は依存関係だけ、資源は CP-SAT」と役割分担したのと同じ設計判断 ── **MILP が担うのは組合せ構造の一部だけ**で、既存プリミティブを再利用できるところは再利用する。

> MILP:Mixed-Integer Linear Programming（混合整数線形計画法）
> 一部の変数を整数に限定した、線形な最適化問題
> 例）工場A・Bで商品を何個作れば利益が最大になるか

**発展 ── 実務なら「フルCVRPのMILP化」が理想形か**(教材のスコープではないが、後学のために)上の「経路順序そのものの MILP 化(劣周回除去制約を伴うフル CVRP)はスコープ外」という判断は、単に教材のコストを抑えるためだけではない。フル MILP 化は**理論上は最も完全な定式化だが、実務で採用される「理想形」とは言えない**。

- **劣周回除去制約(subtour elimination)の扱いにくさ** ── 古典的な DFJ(Dantzig-Fulkerson-Johnson)制約は全部分集合ぶん必要で指数個になる(実務では「解いて劣周回が見つかったら制約を追加する」lazy constraint / cutting plane が必須)。多項式サイズの MTZ(Miller-Tucker-Zemlin)制約は書けるが LP 緩和が弱く収束が遅い。
- **スケールの壁** ── 商用ソルバー(Gurobi/CPLEX)を使っても素朴なフル MILP で厳密に解けるのはせいぜい数十〜100 件程度。実務が要求する「数百〜数千件を秒〜分オーダーで」には全く届かない。

規模・要求ごとの実務の使い分け:

| 規模・要求                 | 実務の手法                                                                                                                                   |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 小規模(〜数十件)、厳密解が欲しい     | フル MILP(劣周回除去 + lazy constraint)                                                                                                        |
| 中〜大規模、厳密解が欲しい         | **分枝価格法(branch-and-price)** ── 列生成で経路を動的生成しながら分枝限定。研究レベルの実装難度                                                                           |
| 実務の主流(数百〜数千件、秒〜分オーダー) | **メタヒューリスティクス** ── 構築法(Clarke-Wright saving法等)+ 局所探索(2-opt / 大規模近傍探索)。`ortools.constraint_solver` の **Routing ライブラリ**(CP-SAT とは別物)がこの系統 |

実データ(交通状況・需要)自体に誤差がある以上、「理論上の最適解」より「速く出て現場で使える解」の価値が高い、という実務判断も背景にある。

`PulpMilpLogisticsStrategy` が採った「割当だけ MILP、経路順序は TSP 近似に委譲」という設計は、単なる教材上の簡略化ではなく、Fisher & Jaikumar(1981)の**cluster-first-route-second**(一般化割当問題で車両→配送先を決め、各車両内は別途 TSP で解く)という、実務でも通用する古典的な分解法そのものである。

> 後続 Phase・興味があれば: `ortools.constraint_solver`(pywrapcp)の Routing ライブラリで同じ fixture を解き、`pulp_milp` / 手実装 4 strategy と比較する発展課題が考えられる(README §12.5 の評価に「配送時間」「遅延リスク」を足すなら、時間窓つき VRP になりRouting ライブラリの出番がより明確になる)。

---

## 2. ビンパッキング MILP ── 「使用台数の最小化」

```python
# app/algorithms/optimization/pulp_logistics.py(要点。全文は samples)
x = {(v.id, d.id): prob.add_variable(...) for v in vehicles for d in deliveries}  # 割当
y = {v.id: prob.add_variable(...) for v in vehicles}                              # 使用フラグ

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
  `y[v]` が「この車両を使うかどうか」のフラグで、`x[v][d] <= y[v]` が「使わない車両には何も積めない」を保証する。
- 手実装 4 strategy はどれも明示的に「使用台数」を最小化しようとはしていない(容量が許す限り何台使っても構わない)。PuLP は**この点で手実装と質的に異なる保証**を持つ ── 3 台目の車両が使えても、容量的に 2 台で足りるなら必ず 2 台に収める(スタンドアロン検証で確認済み)。
- 決定論: CBC は同一入力に対し安定した**最適値**を返す(MILP は目的関数値が一意。解が複数タイになる場合の変数の選び方まではソルバー内部の探索順序に依存するが、`vehicles_used` や`total_distance` のような報告指標は安定する)。OR-Tools CP-SAT のような `random_seed` 固定は不要 ── `msg=False` でログを静音化するだけ。
- `_ops` は出さない(2 トラック比較の観察点として、仕事はソルバーの中にある)。
- **変数は `pulp.LpVariable(...)` でなく `prob.add_variable(...)` で作る**(PuLP 3 系で前者は非推奨
  ── `DeprecationWarning`。生成と同時にモデルへ紐付く新しい書き方に統一)。**ソルバーは`PULP_CBC_CMD` のまま使う** ── PuLP は移行先として `COIN_CMD` を案内する
  `DeprecationWarning` を出すが、現行の配布版(3.3.2)では `COIN_CMD()` の既定 path は文字列 `"cbc"` 固定(PATH 頼み)で、`pulp[cbc]` を入れても自動では拾わない(`pulp.
  LpSolverDefault` も中身は `PULP_CBC_CMD` のまま)。切り替えると `PulpSolverError: cannot execute cbc` で即失敗するため、**この警告は現時点では実害の無い既知の事象として許容する**
  (zero-warning にする裏技はあるが非公開の内部モジュールに依存するため非推奨。詳細 `q_a.md` Q50)。

> pulp.LpProblem は、「最適化問題そのもの」を作るためのクラス
>         # オブジェクト名："logistics_bin_packing",
>         # 最適化方向：最小化(LpMinimize)
> 
> prob.add_variable(...)はLpVariable オブジェクトを作成する。
>          # LpVariable オブジェクトは
>                {name(名):"y_{v.id}", cat(カテゴリー):Binary -> 0/1]}
> solve関数でLpVariableに値が設定される。
> 
> pulp.lpSum(...)は線形式の作成- > 目的関数や制約を設定する

---

## 3. まとめ

- PuLP は「距離」でなく「**台数**」を最小化する、他の 4 strategy とは異なる目的関数を持つ ──2 トラック比較(README §8)が「同じ問題を違う切り口で最適化する」ことまで示せる好例になる。
- 経路順序は 9-2 の `route_for_vehicle`(TSP 近似)にそのまま委譲 ── MILP 層と TSP 層が疎結合なので、将来フル CVRP の MILP 化に発展させる余地も残る(スコープ外として明示)。

## テスト観点(`textbook/samples/tests/unit/test_pulp_logistics.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `PulpMilpLogisticsStrategy.solve`
> - **ドライバ**: このテスト関数。`build_logistics_problem`(9-1)で入力生成
> - **スタブ**: **不要** ── strategy は純粋関数(CBC はプロセス内で完結する組み込みソルバー、
>   外部プロセス・ネットワークを使わない)

| ケース              | 期待                                                               |
| ---------------- | ---------------------------------------------------------------- |
| 例題を解く            | `status == "valid"`、`implementation == "library:pulp"`、`_ops` 無し |
| 3 台目の余裕があっても     | `vehicles_used == 2.0`(容量的に必要な最小台数)                              |
| 割当の網羅性           | 全配送先がちょうど1回ずつ登場                                                  |
| Verification を通す | `status == "valid"`、violation 無し(容量・距離とも整合)                      |
| 車両が小さすぎる         | `status == "infeasible"`                                         |

`uv run pytest tests/unit/test_pulp_logistics.py` / `uvx pyright app/algorithms/optimization`。

---

次章([Phase-9-7](./Phase-9-7.md))では、作業単位 9-7 ── `registry.py` に 5 strategy を登録し、
`select_strategy` に既定分岐を足して end-to-end パイプラインを通す。`build_scaled_logistics_problem`
を使ったプロパティテストで、`brute_force` を正解オラクルに `quality_ratio` を比較する。
