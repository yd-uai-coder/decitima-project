# Phase 7-2: Knapsack DP ── `knapsack_2d`(2 次元 0/1)(作業単位 7-2)

## この章のゴール

「予算・時間内で効用の合計が最大になる訪問地の部分集合を選ぶ」は **0/1 ナップサック**。各アイテムは「入れる / 入れない」の 2 択、容量は **予算と時間の 2 つ**。これをボトムアップ DP で解く純粋関数 `knapsack_2d` を書く。**この章はプリミティブ + DP 理論だけ ── 7-1(Floyd-Warshall)と同じく完全に自己完結する**。`TravelData` を受ける `KnapsackDpTravelStrategy` は、ドメイン葉(7-3)と `travel_common`(7-4)が揃う **7-4** で `knapsack.py` に追加する。

### 代表的なナップサック問題

| 種類            | 特徴                  |
| ------------- | ------------------- |
| **0/1ナップサック** | 各アイテムを最大1回だけ使う      |
| **完全ナップサック**  | 同じアイテムを何個でも使える      |
| **有界ナップサック**  | アイテムごとに使用可能数が決まっている |
| **分数ナップサック**  | アイテムを分割して入れられる      |

**移動コストは DP に入れない**(README「Floyd-Warshall は前処理」)。DP の解は「移動を無視した上界」── 巡回順と移動費用の計上は 7-4 で `travel_common.order_and_cost` が行う。

**この章で作成 / 更新するファイル**:
`app/algorithms/optimization/knapsack.py`(新規 ── `type Item` + `knapsack_2d` のみ。
`KnapsackDpTravelStrategy` は 7-4)、`tests/unit/test_knapsack.py`(新規 ── 純粋 4 ケース)。
**既存ファイルへの変更なし ── この章は自己完結する**。

対応サンプル: `textbook/samples/app/algorithms/optimization/knapsack.py`(冒頭の `# (Phase 7-4)`
より上だけ)、`textbook/samples/tests/unit/test_knapsack.py`。設計は README §19 Phase 7、CLRS 16.2 / 演習。

---

## 1. `knapsack_2d` ── 2 次元容量のボトムアップ DP

```python
# app/algorithms/optimization/knapsack.py(要点。全文は samples)
type Item = tuple[int, int, float]   # (容量Aの消費, 容量Bの消費, 価値)。A/B は非負整数

def knapsack_2d(items: list[Item], cap_a: int, cap_b: int) -> list[int]:
    """容量 (cap_a, cap_b) の 0/1 ナップサック。価値最大の添字リストを返す。"""
    if cap_a < 0 or cap_b < 0:
        return []
    dp = [[0.0] * (cap_b + 1) for _ in range(cap_a + 1)]           # dp[a][b] = (a,b) までの最大価値
    take = [[[False] * len(items) for _ in range(cap_b + 1)] for _ in range(cap_a + 1)]  # 復元用

    for idx, (wa, wb, value) in enumerate(items):
        for a in range(cap_a, wa - 1, -1):        # ← 降順が 0/1 の要(下記)
            for b in range(cap_b, wb - 1, -1):
                cand = dp[a - wa][b - wb] + value
                if cand > dp[a][b]:
                    dp[a][b] = cand
                    take[a][b] = list(take[a - wa][b - wb])
                    take[a][b][idx] = True

    chosen = take[cap_a][cap_b]
    return [i for i, t in enumerate(chosen) if t]
```

**要点**:

- **状態** `dp[a][b]` =「容量 (a, b) までで得られる最大価値」。1 アイテムずつ「使わない
  (`dp[a][b]` のまま)/ 使う(`dp[a-wa][b-wb] + value`)」の良い方で更新。
- **容量を降順に見る**のが 0/1(各アイテムを高々 1 回)の肝。昇順にすると `dp[a-wa][b-wb]` が「このアイテムを既に使った後の値」になり、同じアイテムを何度も詰める(= 無制限ナップサック)。
- **復元** `take[a][b]` = その状態に至ったときのアイテム採否リスト。`dp` の更新と同時に「どれを採ったか」も引き継ぐ。省メモリにするなら `dp` だけ持って後ろ向きに辿るが、教材では採否を明示的に持って「DP は表 + 決定の記録」であることを見せる。
- 計算量: 時間・空間ともに **O(n · A · B)**。**擬多項式** ── A, B は容量の *数値* に比例する。

---

## 2. グリッド解像度の落とし穴

`knapsack_2d` は容量を整数の配列添字にする。実際のコスト(旅行なら place の `cost` / `duration`)は
float なので、**整数グリッドに載せ替える**必要がある。向きが肝:

```python
# float の容量・消費を整数グリッドに(呼び出し側の一般形。travel での具体は 7-4)
cap = math.floor(capacity)       # 容量は切り捨て(グリッドを小さめに)
w   = math.ceil(item_weight)     # 消費は切り上げ(容量オーバーを避ける保守側)
```

- **切り上げ / 切り捨ての向きを揃える** ── 消費は多めに(`ceil`)、容量は少なめに(`floor`)
  見積もれば、DP が「入る」と言った組み合わせは実数でも容量内。逆向きにすると DP が超過の組を選びうる。
- **グリッドが粗いと最適を外す** ── `weight=2.5` を `3` に丸めると、本当は 2 個入るのに 1 個しか入らない
  判定になることがある。解像度を上げる(`× 10` して整数化)と配列が 10 倍に膨れる ──
  **擬多項式の代償**。教材ではこのトレードオフを明示(実務では「予算の単位を 100 円にする」等で制御)。
- **単体で容量を超えるアイテムは DP に入れない**(`if w > cap: continue`)。
- travel での適用(`data.budget → cap_a` / `p.cost → wa`、必須 place の後付け)は 7-4 の
  `KnapsackDpTravelStrategy.solve` で ── そこは `TravelData`(7-3)が要るのでこの章では書かない。

---

## 3. まとめ

- `knapsack_2d` = 2 次元容量(例: 予算 × 時間)の 0/1 ナップサック。容量を **降順**に見る。
  `take[][][]` で採否を復元。O(n · A · B) の擬多項式。
- float の容量・消費は整数グリッドに載せる ── 消費は `ceil`、容量は `floor`(保守側)。
  解像度と配列サイズのトレードオフを明示。
- この章は `knapsack.py`(`type Item` + `knapsack_2d`)+ テストだけ ── 既存ファイルに触れず自己完結。
  Travel への適用(`KnapsackDpTravelStrategy`)は 7-4。

## テスト観点(`textbook/samples/tests/unit/test_knapsack.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `knapsack_2d`(純粋関数)
> - **ドライバ**: このテスト関数。素のタプルリスト `(wa, wb, value)` を直接渡す
> - **スタブ**: **不要** ── 純粋で外部依存を呼ばない(`Phase-0-3.md` の純粋レイヤー)

| ケース                                                  | 期待                             |
| ---------------------------------------------------- | ------------------------------ |
| item0(2,3,10)/ item1(3,2,12)/ item2(4,4,15)、cap(5,5) | `{0, 1}`(価値 22 > item2 単体 15)   |
| 時間が厳しい cap(10, 2)                                    | `[1]` のみ                        |
| cap(0,0) / cap(-1,5)                                 | `[]`                            |
| 同じアイテムを 2 回取れば価値 20、cap(5,5)                         | `[0]` のみ(0/1 なので 1 回)           |

> **この章のテストは 4 本とも素のタプルリストで即緑** ── fixture も `TravelData` も import しない。
> `KnapsackDpTravelStrategy` のテストは 7-4 で `test_travel_common.py` に入る。

`uv run pytest tests/unit/test_knapsack.py` / `uvx pyright app/algorithms/optimization`。

---

次章([Phase-7-3](./Phase-7-3.md))では、作業単位 7-3 ── `travel_planning` を判別可能ユニオンに
配線する。`TravelData` / `TravelSolution` を 1 メンバーずつ足し、`semantic` / `structure` /
制約チェッカーに travel の分岐を入れる(`verification` の巡回コスト検算は `travel_common` が
要るので 7-4)。route / network / shift には一切触れない。
