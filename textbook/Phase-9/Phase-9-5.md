# Phase 9-5: BranchAndBoundLogisticsStrategy(作業単位 9-5)

## この章のゴール

`greedy`(貪欲、速いが最適とは限らない)と `brute_force`(厳密だが指数時間)の中間 ──
配送先→車両の割当を **DFS + 分枝限定** で探索し、小〜中規模なら全探索と同じ最適解に、
規模が大きければノード予算で打ち切って anytime に振る舞う。Phase 6 の
`BranchAndBoundShiftStrategy` のノード予算パターン(`_MAX_NODES`)の 2 人目の消費者。

**この章で作成 / 更新するファイル**: `app/algorithms/optimization/branch_and_bound_logistics.py`
(新規)、`tests/unit/test_branch_and_bound_logistics.py`(新規)。既存ファイルへの変更は無い。

---

## 1. 下界 ── 「これまでに確定した距離」

```python
# app/algorithms/optimization/branch_and_bound_logistics.py(要点。全文は samples)
if confirmed >= self.best_total:
    return  # 確定距離は単調非減少 ── 下界が現最良以上なら枝刈り
```

Phase 6 の `BranchAndBoundShiftStrategy` は「残りスロットを最安スタッフで埋めた場合」という楽観推定を下界に使った。Phase 9 では**より単純な下界**を使う ── 「これまでに確定した距離」そのもの。これが安全(admissible)である理由:

> Floyd-Warshall が返す距離は三角不等式を満たす(定義上、最短距離だから)。ある車両に配送先を1 件追加すると、その車両の最適な巡回距離は**単調に非減少**になる(訪問すべき点が増えれば、最適巡回は同じか長くなることはあっても短くなることは無い)。したがって「今確定している合計距離」は、これから確定する分を足した最終的な合計距離を**絶対に上回らない** ──
> 安全な下界(admissible)である。

ただし緩い(将来のコストを 0 と見積もる保守的な下界)── 残りの配送先の位置を全く見ないので、枝刈りの効きは `_lower_bound`(Phase 6)ほど強くない。**より tight な下界**(残りをデポからの片道距離の総和で見積もる、等)は経路の共有を過小評価しかねず、admissible 性を保証するには慎重な議論が要る ── 発展課題として残す(教材としては「安全だが緩い下界から始め、必要なら締める」という順序を明示する)。

---

## 2. apply/undo パターン ── Phase 6 と同じ形

```python
old_distance = distances[vehicle.id]
buckets[vehicle.id].append(delivery.id)
distances[vehicle.id] = new_distance
self._recurse(i + 1, buckets, distances, confirmed - old_distance + new_distance)
buckets[vehicle.id].pop()
distances[vehicle.id] = old_distance
```

配送先を 1 件ずつ、どの車両に入れるかを DFS で試す。容量オーバーになる車両は
`capacity_ok` で即座に弾き、回れない(`route_for_vehicle` が `None`)車両も弾く。
選んだ後は `distances[vehicle.id]` を更新して再帰し、戻ってきたら **undo**(Phase 6 の
`_apply(..., sign=-1)` と同じ発想、ここでは値を退避して代入し直すだけ)。

`_MAX_NODES = 200_000` は Phase 6 と同じ値・同じ意味(決定論的なノード予算。壁時計を見ない
── `solve` は純粋関数の契約を守る、`Phase-0-5.md` §5.1)。打ち切り時は `metrics["_truncated"]`。

---

## 3. まとめ

- 下界は「確定距離」1 本だけ ── シンプルだが correctness は保証される(小〜中規模で
  `brute_force` オラクルと必ず一致することをプロパティテストで確認)。
- `_MAX_NODES` + `_truncated` は Phase 6 のパターンをそのまま踏襲(コピーではなく再利用 ──
  値も意味も同じ)。
- これで手実装 4 strategy(`knapsack_dp` / `greedy` / `branch_and_bound` / `brute_force`)が
  揃った。次章で産業ソルバー(PuLP)を足す。

## テスト観点(`textbook/samples/tests/unit/test_branch_and_bound_logistics.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `BranchAndBoundLogisticsStrategy.solve`
> - **ドライバ**: このテスト関数。`build_logistics_problem` / `build_scaled_logistics_problem`
>   (9-1)で入力生成
> - **スタブ**: **不要** ── strategy は純粋関数

| ケース                                   | 期待                       |
| ------------------------------------- | ------------------------ |
| 例題の手計算との突き合わせ                         | `total_distance == 21.0` |
| 決定論                                   | 同じ入力 → 完全に同じ出力           |
| `brute_force` オラクルとの一致(規模 5、seed 0〜3) | 誤差 1e-6 未満で一致            |
| 容量の再チェック                              | どの車両も申告済みの容量を超えない        |

`uv run pytest tests/unit/test_branch_and_bound_logistics.py` /
`uvx pyright app/algorithms/optimization`。

---

次章([Phase-9-6](./Phase-9-6.md))では、作業単位 9-6 ── PuLP(MILP)で「使用台数を最小化する」
ビンパッキング問題を解く産業ソルバートラック `PulpMilpLogisticsStrategy`。`pulp` を`[project].dependencies` に新規追加する。
