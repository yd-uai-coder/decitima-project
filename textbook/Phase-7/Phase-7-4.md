# Phase 7-4: 訪問順 + travel_common + DP strategy(Floyd-Warshall 注入 / m > 8 近似)(作業単位 7-4)

## この章のゴール

7-2 の `knapsack_2d` は「どの place を選ぶか」だけ。7-3 でドメイン葉(`TravelData` / `TravelSolution`)が揃った。この章で **選んだ place を回る順** を決め、DP strategy を完成させる:

1. `travel_common.py`(**新規・全関数**)── `parse_travel_problem` / `place_utility` / `travel_solution`に加え、`all_pairs`(Floyd-Warshall × 2 で全点対距離)/ `order_and_cost` / `tour_cost`。
2. `build_leg_adjacency`(`adjacency.py` に追加)── `TravelData` → 移動 cost の隣接リスト。`all_pairs` が使う。
3. `optimize_waypoint_order` の **m > 8 分岐**を「与えられた順」から **最近傍法 + 2-opt** の近似に差し替える ── Phase 4-1 が `_MAX_EXACT` 超えを明示的に Phase 7 送りにした宿題(Q27)の回収。
4. `KnapsackDpTravelStrategy`(`knapsack.py` に追加)── `knapsack_2d` を `TravelData` に適用し、`travel_solution` 経由で巡回順・総コストまで返す。
5. `verification.py::_verify_travel_plan`(**7-3 から移設**)── 申告 total_cost / total_time を`tour_cost` で検算。`travel_common` が要るのでこの章。

**この章で作成 / 更新するファイル**:
新規 `app/algorithms/optimization/travel_common.py`(全関数)、新規 `tests/unit/test_travel_common.py`。
既存への追記: `app/algorithms/graph/adjacency.py`(`build_leg_adjacency`、冒頭系譜に `改訂 Phase 7`)、
`app/algorithms/graph/waypoints.py`(m > 8 分岐、`改訂 Phase 7`)、
`app/algorithms/optimization/knapsack.py`(`KnapsackDpTravelStrategy` を追加、`# (Phase 7-4)`)、
`app/services/verification.py`(`_verify_travel_plan` を追加、`# (Phase 7-4)`)、
`tests/unit/test_route_strategies.py`(現行版 ── m > 8 のテストを近似版に差し替え)。

対応サンプル: 上記すべて。設計は `Phase-4-1.md` §「waypoints」、`Phase-0-5.md` §5.3、README §19。

---

## 1. `optimize_waypoint_order` の m > 8 分岐(`waypoints.py` 現行版)

```python
# app/algorithms/graph/waypoints.py(要点。全文は samples)
if len(waypoints) <= _MAX_EXACT:         # _MAX_EXACT = 8。9! ≈ 36 万で線を引く
    best_order = _exact_best(start, goal, waypoints, cost)
else:
    # (Phase 7-4) 多すぎるので厳密は諦め、最近傍 + 2-opt の近似で順を決める。
    # 従来(〜Phase 5)はここで「与えられた順」をそのまま返していた。
    best_order = _approx_best(start, goal, waypoints, cost)
```

```python
def _approx_best(start, goal, waypoints, cost) -> list[str] | None:
    # --- 最近傍法: start から「未訪問で一番近い経由地」を繰り返し選ぶ ---
    remaining = set(waypoints); order = []; current = start
    while remaining:
        nxt = min(remaining, key=lambda w: _inf_if_none(cost(current, w)))
        if cost(current, nxt) is None:
            break                        # どこにも繋がらない ── 2-opt に回す
        order.append(nxt); remaining.discard(nxt); current = nxt
    if remaining:
        order.extend(remaining)          # 繋がらなかった分は末尾(2-opt が並べ替える)

    # --- 2-opt: 区間 [i, j] を反転して総和が縮むなら採用。改善が止まるまで ---
    seq = [start, *order, goal]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(seq) - 2):
            for j in range(i + 1, len(seq) - 1):
                cand = seq[:i] + seq[i:j+1][::-1] + seq[j+1:]
                if _path_total(cand, cost) < _path_total(seq, cost):  # None 扱いは samples 参照
                    seq = cand; improved = True
    return seq if _path_total(seq, cost) is not None else None
```

- **最近傍法**: O(m²)。貪欲に「今いる場所から一番近い未訪問」を選ぶ。単純だが最悪ケースで最適の 2 倍近くになりうる ── だから 2-opt で仕上げる。
- **2-opt**: 経路の 2 辺を選んで間を反転する局所探索。「交差した経路をほどく」操作。改善が止まるまで回す。O(m²) × 反復回数。局所最適で止まる(大域最適の保証はない ── 近似)。
- **`optimize_waypoint_order` のシグネチャは不変** ── route の 3 strategy(Dijkstra / Bellman-Ford / A*)は `plan_route` 経由でこれを呼ぶので**無変更で m > 8 に対応**できる。実際に必須経由地を9 個以上渡す route 問題は稀だが、`Phase-4-4.md` の宿題として正しく塞ぐ。
- **区間の最短距離は呼び出し側が `cost` 関数で注入** ── `optimize_waypoint_order` はグラフを知らない純粋なロジック(順列 / 局所探索を回すだけ)。フェイクの距離表でテストできる。
- **`None` を返す条件は両分岐で同じ** ── どの順に並べても区間 `cost(a, b)` が `None`(不通)なら、`_exact_best`(全順列を試した確定判定)も `_approx_best`(最終 seq が繋がらない)も `None`。本コードベースの `cost` は全点対距離 / 最短経路由来なので `cost is None ⟺ a, b が別の連結成分` ── `{anchor} ∪ 経由地` が 1 成分に収まらないときだけ両者とも `None`(成分内なら初期 seq がそのまま繋がるので `_approx_best` は `None` を返せない)。

---

## 2. `build_leg_adjacency`(`adjacency.py` に追加)

Floyd-Warshall(7-1)は `Adjacency` を受ける。その `Adjacency` を `TravelData` から作るのが
`build_leg_adjacency`。`TravelData` は 7-3 で生まれた葉なので、この import をここで足す:

```python
# app/algorithms/graph/adjacency.py(追加。全文は samples)
from app.domain.problems.travel_planner import TravelData   # ← module top に追加  # (Phase 7-4)

def build_leg_adjacency(data: TravelData, forbidden_leg_ids: set[str]) -> Adjacency:
    """TravelData から移動 cost の重み付き隣接リストを作る。leg は常に無向、重みは travel_cost。"""
    adjacency: Adjacency = {place.id: [] for place in data.places}
    for leg in data.legs:
        if leg.id in forbidden_leg_ids:
            continue
        a, b = leg.endpoints
        adjacency.setdefault(a, []).append((b, leg.id, leg.travel_cost))
        adjacency.setdefault(b, []).append((a, leg.id, leg.travel_cost))
    return adjacency
```

- `Adjacency`(= `dict[str, list[tuple[str, str, float]]]`)は Phase 4-1 で `adjacency.py` に定義済み。
  route の `build_adjacency` / network の `build_link_adjacency` と**関心事(グラフの作り方)が同じ**
  なので同居させる(`Phase-2-2.md` §3 / `Phase-5-3.md` §3.1 と同じ判断)。
- leg は常に無向 → 両端に `(相手, leg_id, travel_cost)` を張る。移動 **時間** 側の隣接は
  次の §3 で `travel_common._time_adjacency` として別に作る(`travel_time` を重みにする)。
- **`adjacency.py` は route の Dijkstra / Bellman-Ford / A* / BruteForce / `reachability` /
  network の `build_link_adjacency` も import 元にする**。`travel_planner.py` はこの章の時点で
  7-3 の写経が済んでいるので、この import 行を足しても collection は緑のまま
  (7-1 でこれを足すと 7-3 まで写経していないので既存テストごと赤 ── だから 7-4)。

---

## 3. `travel_common.py` を新規作成 ── パース + Floyd-Warshall 前処理

`TravelData` / `TravelSolution`(7-3)が揃ったので、strategy 共通の足回りをファイルごと作る
(route の `segments.py` / network の `mst.py` と同じ位置づけ)。`parse_travel_problem`(制約 items の
収集)/ `place_utility`(好み加重の効用)/ `travel_solution`(`CandidateSolution` の組み立て)に加え、
Floyd-Warshall 前処理:

```python
# app/algorithms/optimization/travel_common.py(要点。全文は samples)
def all_pairs(data: TravelData) -> tuple[AllPairs, AllPairs]:
    """(移動費用の全点対距離, 移動時間の全点対距離)。strategy が 1 度計算して使い回す。"""
    cost_dist = floyd_warshall(build_leg_adjacency(data, set()))    # §2
    time_dist = floyd_warshall(_time_adjacency(data, set()))        # travel_time 側の隣接
    return cost_dist, time_dist

def order_and_cost(data, selected_ids, cost_dist, time_dist) -> tuple[list[str], float, float] | None:
    """選んだ place を回る順(閉路)と、place cost/duration + 移動 cost/time の合計。
    どの順でも全部を繋げないなら None。data.start があればそこを anchor にし必ず含める。"""
    sel = list(dict.fromkeys(selected_ids))
    if data.start is not None and data.start not in sel:
        sel = [data.start, *sel]
    if not sel:
        return [], 0.0, 0.0
    anchor = data.start if data.start in sel else sel[0]
    rest = [p for p in sel if p != anchor]
    tour = optimize_waypoint_order(anchor, anchor, rest, lambda a, b: _finite(cost_dist[a][b]))
    if tour is None:
        return None
    visit = tour[:-1] if len(tour) > 1 and tour[0] == tour[-1] else tour
    return visit, *tour_cost(data, visit, cost_dist, time_dist)

def tour_cost(data, visit, cost_dist, time_dist) -> tuple[float, float]:
    """*与えられた順* visit を回る閉路(最後に出発地へ戻る)の総費用・総時間。順は再最適化しない
    ── Verification(§5 `_verify_travel_plan`)が strategy の申告した順のコストを検算するのに使う。"""
```

- **`optimize_waypoint_order(anchor, anchor, rest, ...)`** ── start と goal を同じ anchor にすると「anchor から出て全部回って anchor に戻る」閉路(TSP そのもの)になる。route の「start→goal の片道」を anchor=start=goal で閉路に転用する、という使い方。
- **`_finite`**: `cost_dist[a][b]` が `math.inf`(到達不能)のとき `optimize_waypoint_order` へは`None` を渡す
   ── waypoints の `SegmentCost` 契約は「到達不能は None」。
- **どの順でも繋げないとき** ── `optimize_waypoint_order` が `None` → `order_and_cost` が `None` → `travel_solution` が `status="infeasible"`(空解)。travel は route の `route_reachable` / network の連結性ゲートに当たる Validation の計算ゲートを持たない(`Phase-7-3.md` §3)ので、DP が到達不能な place 集合を選ぶと**ここで初めて** infeasible になる。Greedy / BruteForce は 1 手ごとに実際の巡回コストで判定するのでこの経路に入らない。
- **移動 *時間* 側の隣接** `_time_adjacency` は `build_leg_adjacency` と同型だが重みを `travel_time`にする。`build_leg_adjacency` を「costパラメータ付き」に一般化しなかったのは、route / network の`build_adjacency` / `build_link_adjacency` が引数を増やさない形で揃っているため(足並み優先)。
- `all_pairs` は strategy が `solve` の頭で 1 回だけ呼び、DP / Greedy / BruteForce の全評価で使い回す ── Floyd-Warshall は O(V³) なので毎回やり直さない。

---

## 4. `KnapsackDpTravelStrategy` を `knapsack.py` に追加

`knapsack_2d`(7-2)を `TravelData` に適用する。`data.budget → cap_a` / `p.cost → wa`(§7-2 の
グリッド解像度)、必須 place の後付け、そして `travel_solution` 経由で `order_and_cost` を通す:

```python
# app/algorithms/optimization/knapsack.py(冒頭 `# (Phase 7-4)` より下。全文は samples)
class KnapsackDpTravelStrategy:
    def solve(self, problem):
        data, forbidden, required = parse_travel_problem(problem)     # travel_common
        cost_dist, time_dist = all_pairs(data)                        # Floyd-Warshall × 2
        cap_a, cap_b = math.floor(data.budget), math.floor(data.time_budget)
        items = [(ceil(p.cost), ceil(p.duration), place_utility(data, p.id)) for p in ...]
        picked = set(knapsack_2d(items, cap_a, cap_b))
        selected = [...] + [rid for rid in sorted(required) if ...]   # 必須は後付け
        return travel_solution(data, selected, cost_dist, time_dist, ops, self.meta)
        #   travel_solution → order_and_cost で巡回順・総コスト → CandidateSolution
```

- `travel_solution` は `order_and_cost` を呼ぶ ── 回れないなら `status="infeasible"`、回れれば`status="valid"`(予算・時間の hard 判定は Verification)。
- **DP は place cost/duration だけで選んだ** → `order_and_cost` が足す移動分で `total_cost` が予算を超えることがある。その解も `status="valid"` で返し、§5 の `_verify_travel_plan` +`verify_travel_structure` の予算チェック(7-3 §4)が hard 違反 → `invalid` にする。
  **「strategy は嘘をつかず素直に返す、判定は Verification」**(`Phase-0-6.md` の役割分担)。

---

## 5. `verification.py::_verify_travel_plan` ── 申告コストの検算(7-3 から移設)

```python
# app/services/verification.py(追加。要点。全文は samples)
from app.algorithms.optimization.travel_common import all_pairs, tour_cost   # (Phase 7-4)

# (Phase 7-4)
def _verify_travel_plan(problem, solution) -> list[ConstraintViolation]:
    """申告した total_cost / total_time が実際の巡回コストと合うか。
    Floyd-Warshall で全点対距離を出し直し、solution.visit_order の順(再最適化しない)で
    place + 移動のコストを積んで比べる。ズレたら strategy が嘘をついている(hard)。"""
    if not (isinstance(problem.data, TravelData) and isinstance(solution.assignments, TravelSolution)):
        return []
    cost_dist, time_dist = all_pairs(problem.data)
    real_cost, real_time = tour_cost(problem.data, solution.assignments.visit_order, cost_dist, time_dist)
    # abs(real_cost - claimed) > 1e-6 → travel_structure hard violation(total_time も同様)
```

- **なぜ 7-3 でなく 7-4 か** ── `all_pairs` / `tour_cost` は `travel_common`(この章)にある。7-3 で
  この import を足すと `travel_common` が無く、`verification.py` を import する `solve.py` /
  `benchmark.py` / 約 8 テストの collection が全崩れ(進行のルール #15。Q42)。
- `structural_verify` の直後に `_verify_spanning_tree`(network)と並んで呼ばれる ── 「domain の
  純粋述語 + services のグラフ計算」を合わせて違反リストを作る(`Phase-5-3.md` §5 と同じ構造)。
- **`tour_cost` は `visit_order` を再最適化しない** ── strategy が「この順で回った」と言った
  コストが正しいかの検算。順の最適化は strategy 側の `order_and_cost`。

---

## 6. まとめ

- `optimize_waypoint_order` の m > 8 を「与えられた順」→ 最近傍法 + 2-opt に(Phase 4 の宿題)。
  シグネチャ不変なので route の 3 strategy は無変更で恩恵。
- `build_leg_adjacency`(`TravelData` → 移動 cost の隣接リスト)を `adjacency.py` に追加 ──
  route / network のビルダーと同居。7-3 で葉が生まれた後なので import が解決する。
- `all_pairs`(Floyd-Warshall × 2)→ `order_and_cost`(anchor 閉路)→ `tour_cost`(申告順の検算)。
- DP に配線 ── DP は移動無視で選ぶ、`order_and_cost` が移動を足す、超過は Verification が弾く。
- `order_and_cost` の `None`(= どの順でも繋げない)→ `status="infeasible"`。
  `_exact_best` / `_approx_best` は同じトリガー(`{anchor} ∪ 経由地` が 1 成分に収まらない)で `None`。
- `_verify_travel_plan` は `travel_common` が要るのでこの章(7-3 でなく ── #15 / Q42)。

## テスト観点(`textbook/samples/tests/unit/{test_travel_common,test_route_strategies}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_travel_common.py`**(この章の第一テスト・新規)
> 
> - **対象**: `build_leg_adjacency`、`travel_common.all_pairs` / `order_and_cost` / `tour_cost`、
>   `KnapsackDpTravelStrategy.solve`(valid 経路 + **到達不能な選択 → infeasible 経路**)、
>   `verification._verify_travel_plan`
> - **ドライバ**: このテスト関数。`build_travel_problem` fixture(7-3)、`_tdata` / `_plan` で型を絞る
> - **スタブ**: **不要** ── いずれも純粋(strategy は `OptimizationProblem` → `CandidateSolution`、
>   verification は DB を持たない)
> 
> **`test_route_strategies.py`**(現行版 = m > 8 のテストを近似版に差し替え)
> 
> - **対象**: `optimize_waypoint_order` の m > 8 分岐(`_approx_best`)── 近似の質 + **全区間不通 → `None` 経路**
> - **ドライバ**: このテスト関数。`cost` はテスト内のフェイク距離関数(グラフ非依存)
> - **スタブ**: **不要**(純粋関数)。`cost` フェイクがドライバ側の入力生成
> - **公開挙動の変化**(#16): Phase 4〜5 は `assert order == ["s", *required, "g"]`(与えられた順)。
>   Phase 7-4 から「全経由地を訪れ、与えられた順より悪くない」に緩める。docstring に before → after

| ケース                                      | 期待                                                                             |
| ---------------------------------------- | ------------------------------------------------------------------------------ |
| `build_leg_adjacency`(無向)                | L01 が P0↔P1 両向きに、重み = `travel_cost`                                            |
| `build_leg_adjacency`(forbidden)         | 外した leg の相手が隣接に現れない                                                            |
| `order_and_cost(["P1", "P3"])`           | `set(visit) == {"P0", "P1", "P3"}`(start=P0 が anchor)/ 総コスト・時間 > 0             |
| `order_and_cost` と `tour_cost` の総和       | 一致(同じ visit・同じ距離表)                                                             |
| leg を全部外した data で `order_and_cost`       | `None`(P0 以外どこにも行けない)                                                          |
| `KnapsackDpTravelStrategy.solve`         | `status == "valid"` / `produced_by.name == "knapsack_dp"` / 予算をきつくすると place 数減 |
| leg 全外し + `required=["P1"]` で `.solve`   | `status == "infeasible"` / `selected_place_ids == []`(DP は P1 を含む選択を返すが繋げない) |
| `_verify_travel_plan`(正直な DP 解 / 嘘をついた解) | 前者は violation なし、後者は `travel_structure` hard で `invalid`                       |
| m > 8(一様コスト 1.0)`test_route_strategies`  | 全経由地 + start + goal を訪れる / 重複なし / start 始まり goal 終わり                           |
| m > 8(非一様コスト)`test_route_strategies`     | 近似の総距離 `<=` 与えられた順の総距離                                                         |
| m > 8 かつ全区間不通 `test_route_strategies`     | `optimize_waypoint_order` が `None`(`_approx_best` も `_exact_best` と同じ)          |

`uv run pytest tests/unit/test_travel_common.py tests/unit/test_route_strategies.py` /
`uvx pyright app/algorithms app/services`。

---

次章([Phase-7-5](./Phase-7-5.md))では、作業単位 7-5 ── Greedy(効用/コスト比、移動込みで逐次)
と BruteForce(部分集合の全列挙オラクル)を実装し、`registry` に `"travel_planning"` キーを新設、
`select_strategy` に travel 分岐を足す。「DP == BruteForce(小規模)」のプロパティテストで
end-to-end を締める。
