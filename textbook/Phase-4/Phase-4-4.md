# Phase 4-4: 複数必須経由地の順序最適化(小 TSP)(作業単位 4-4)

## この章のゴール

Phase 1 の Dijkstra は必須経由を「与えられた順」で通していた(`_waypoints`)。
2 点以上の必須経由があると、**どの順で回るか**で総距離が変わる ── これは小さな
巡回セールスマン問題(TSP)。README §19 が「Phase 1 から先送りしてここで扱う」と決めていた。

`graph/waypoints.py` 自体は **4-1 で作成済み**(`segments.py` / `dijkstra.py` が import するため)。
samples は end 状態 = 全順列版なので、この章で写経するファイルは増えない ── ここでは
`optimize_waypoint_order` の**中身**(全順列で最小コスト順を選ぶ)を深掘りし、2 点以上の TSP を
テストする。

- `graph/waypoints.py` の `optimize_waypoint_order` ── `m ≤ 8`(`_MAX_EXACT`)なら訪問順の**全順列**を
  試し、区間距離の和が最小の順を選ぶ。それより多ければ「与えられた順」(近似は Phase 7 Travel Planner)
- Dijkstra / Bellman-Ford / A* が自動でこの恩恵を受ける(`plan_route` 経由なので変更不要)

**この章で新規作成するファイル**: なし(`waypoints.py` / `segments.py` は 4-1 で最終形まで作成済み)。
**既存ファイルへの変更**: `samples/tests/unit/test_route_strategies.py` に経由順最適化セクションを追加
(4-2 で作ったファイル)。実装コードはこの章では触らない ── 主眼は「全順列で最適順を選ぶ」挙動の
理解とテスト。

対応サンプル: `samples/app/algorithms/graph/{waypoints,segments}.py`。
テストは `samples/tests/unit/test_route_strategies.py`(経由順最適化セクション)。
設計は `Phase-0-5.md` §5.3、README §19 Phase 4。

---

## 1. `optimize_waypoint_order`

```python
# app/algorithms/graph/waypoints.py(要点。全文は samples)
_MAX_EXACT = 8   # 経由地がこの数以下なら全順列。9! ≈ 36 万でここに線を引く
type SegmentCost = Callable[[str, str], float | None]   # (a, b) -> 最短距離。到達不能なら None

def optimize_waypoint_order(start, goal, required, cost: SegmentCost) -> list[str] | None:
    waypoints = _dedup(required)                       # 重複と start/goal との重複を畳む
    if not waypoints:
        return _collapse([start, goal])
    if len(waypoints) > _MAX_EXACT:
        return _collapse([start, *waypoints, goal])    # 多すぎる → 与えられた順
    best_order, best_total = None, inf
    for perm in permutations(waypoints):
        seq = [start, *perm, goal]
        total, ok = 0.0, True
        for a, b in pairwise(seq):
            d = cost(a, b)
            if d is None: ok = False; break            # この順では区間 a→b が繋がらない
            total += d
        if ok and total < best_total:
            best_total, best_order = total, seq
    return None if best_order is None else _collapse(best_order)
```

- **区間の最短距離そのものは計算しない** ── `cost(a, b)` 関数として呼び出し側(strategy)が渡す。
  `optimize_waypoint_order` は「順列を回して和を比べる」だけの純粋なロジックで、
  グラフアルゴリズム(Dijkstra / A*)に依存しない。これがテストしやすさの鍵
  (`cost` にフェイクの距離表を渡せる)。
- **`_MAX_EXACT = 8`** ── 8! = 40320 通りの順列 × 各 9 区間。区間コストは `_SegmentCache` が
  メモ化するので、実際に走る Dijkstra は「経由地ペアの数」= 高々 (m+2)² 回だけ。
  
  > メモ化にあたる部分はsegments.pyの_SegmentCacheクラス
- **どの順でも start→…→goal が繋がらなければ `None`** → strategy が `infeasible` を返す。

> optimize_waypoint_order関数の第四引数は 
> cost: SegmentCost 
> そして、
> type SegmentCost = Callable[[str, str], float | None]
> 
> だからcostは関数オブジェクトの参照を意味する。
> 
> cost関数の実行はoptimize_waypoint_order関数内の
>         for a, b in pairwise(seq):
>             d = cost(a, b)
> で行われる。
> 引数costとして受け取った関数の第一引数にa, 第二引数にbを渡して関数を実行。
> つまり、このcost関数はoptimize_waypoint_orderの呼び出し元(caller)が用意して、実引数として渡す必要がある。尚、そのcost関数の引数と戻り値の型は
> type SegmentCost = Callable[[str, str], float | None]
> として定義されている。※型ヒントであり、強制はされない。
> 
> その例が、test_route_strategies.pyにある。
>     def cost(a: str, b: str) -> float | None:
>         return abs(positions[a] - positions[b])
>     order = optimize_waypoint_order("start", "goal", ["A", "B"], cost)

---

## 2. `plan_route` への配線

```python
# app/algorithms/graph/segments.py(要点)
def plan_route(start, goal, required, segment_fn) -> tuple[Segment | None, int]:
    cache = _SegmentCache(segment_fn)                            # 区間を 1 度だけ解いてメモ化
    order = optimize_waypoint_order(start, goal, required, cache.weight)
    if order is None:
        return None, cache.ops
    # order に沿って区間を連結(cache.segment はメモから返す)
    for a, b in pairwise(order):
        seg = cache.segment(a, b)
        if seg is None: return None, cache.ops
        node_ids.extend(seg.node_ids if not node_ids else seg.node_ids[1:])
        edge_ids.extend(seg.edge_ids); total += seg.weight
    return Segment(node_ids, edge_ids, total), cache.ops
```

- `_SegmentCache.weight(a, b)` を `cost` として渡す ── 順序探索中に引いた区間結果はそのまま連結フェーズでも使える(二重計算しない)。
  
  > 引数costの考え方は先述のoptimize_waypoint_order関数と同じ。
  > 型ヒントは
  > type SegmentFn = Callable[[str, str], tuple["Segment | None", int]]
  > ※SegmentCost戻り値の型が違う
- **Dijkstra / Bellman-Ford / A* は 1 行も変えない** ── 全部 `plan_route` を呼んでいる(4-1 で
  そう配線した)ので、`optimize_waypoint_order` が順序最適化する時点で 3 strategy すべてが
  自動で恩恵を受ける。この章はその挙動をテストで固める。

---

## 3. Phase 1 マーカーの「で確定」化

`Phase-0-5.md` §5.3、`Phase-1-4.md`、Phase 1 samples の `dijkstra.py` の
「順序最適化(小さな TSP)は Phase 4」コメントを、`[Phase 4 で確定 ── optimize_waypoint_order]`
マーカーに置き換える(旧計画が実現したことの記録。進行のルール #12.2 C 相当)。

**TSP の近似(m が大きいとき)は Phase 4 では扱わない** ── Phase 7 の Travel Planner が
Floyd-Warshall(全点対距離)を前処理に使って DP / 貪欲で訪問順を決める、そのテーマ。
`optimize_waypoint_order` は `m > 8` で素直に「与えられた順」を返し、そこに前方依存を作らない。

---

## 4. まとめ

- 2 点以上の必須経由 = 小さな TSP。`optimize_waypoint_order` が `m ≤ 8` で全順列を試す。
- 区間距離は `cost` 関数で外から注入 ── `optimize_waypoint_order` はグラフを知らない純粋ロジック。
- `_SegmentCache` が区間を 1 度だけ解いてメモ化(順序探索と連結で共有)。
- Dijkstra / Bellman-Ford / A* は `plan_route` 経由なので**無変更**で恩恵を受ける。

## テスト観点(`samples/tests/unit/test_route_strategies.py` の経由順セクション)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `optimize_waypoint_order`(純粋ロジック)/ 各 strategy 経由の統合挙動
> - **ドライバ**: このテスト関数
> - **スタブ**: `cost` に**フェイクの距離関数**を渡す(位置の差の絶対値を返すだけ)──
>   `optimize_waypoint_order` を実グラフ無しでテストできるのがこの設計の狙い

| ケース                                          | 期待                                   |
| -------------------------------------------- | ------------------------------------ |
| 1D 直線で経由地 A(遠) B(近)                          | `["start", "B", "A", "goal"]` に並べ替わる |
| どの区間も繋がらない(`cost` が常に None)                  | `None`                               |
| 経由地 9 個(`> _MAX_EXACT`)                      | 与えられた順のまま                            |
| 実グラフで必須 `["B","C"]` と `["C","B"]` を別々に solve | 同じ最短総距離                              |

`uv run pytest tests/unit/test_route_strategies.py -k waypoint` /
`uvx pyright app/algorithms/graph/waypoints.py`。

---

次章([Phase-4-5](./Phase-4-5.md))では、作業単位 4-5 ── `networkx` を産業ソルバートラック兼
検証オラクルとして導入し、`select_strategy` を「問題特性で使うアルゴリズムを決める」rule-based にする。
