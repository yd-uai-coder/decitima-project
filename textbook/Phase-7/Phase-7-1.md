# Phase 7-1: Floyd-Warshall プリミティブ + DP 理論(作業単位 7-1)

## この章のゴール

Travel Planner は「訪問地を選ぶ」→「選んだ地を回る順を決める」の 2 段。後段の「巡回順」を決めるには、**どの 2 地点の間も最短でいくらか**が要る。leg(移動区間)は隣り合う place しか繋がないので、間接的に経由した最短距離を先に求めておく ── それが **Floyd-Warshall**(全点対最短経路)。

この章では Floyd-Warshall を手実装の三重ループで書き、あわせて **動的計画法(DP)の考え方**(部分問題 / 最適部分構造 / ボトムアップ vs メモ化 / 擬多項式)を押さえる。
7-2 の Knapsack DP、7-4 の訪問順、この後のすべてがこの上に乗る。

> **動的計画法(DP)**：大きな問題を「小さな問題」に分解し、同じ小問題を何度も計算しないように結果を保存して、効率よく解くアルゴリズム手法
> **ナップサック問題**：限られた容量や予算などの制約の中で、選択するものの価値を最大化する問題

**この章で作成 / 更新するファイル**:
`app/algorithms/graph/floyd_warshall.py`(新規)、`tests/unit/test_floyd_warshall.py`(新規)。
既存ファイルへの変更は無い ── この章は完全に自己完結する(`floyd_warshall` は
`adjacency.py` の `Adjacency` 型だけに依存。`TravelData` を受ける `build_leg_adjacency` は
7-3 で葉が生まれてから 7-4 で `adjacency.py` に追加する)。

対応サンプル: `textbook/samples/app/algorithms/graph/floyd_warshall.py`、
`textbook/samples/tests/unit/test_floyd_warshall.py`。設計は README §19 Phase 7、CLRS 25 章。

---

## 1. Floyd-Warshall ── 「k を経由してよいことにすると縮むか」

```python
# app/algorithms/graph/floyd_warshall.py(要点。全文は samples)
type AllPairs = dict[str, dict[str, float]]   # dist[a][b] = a→b の最短(到達不能は math.inf)

def floyd_warshall(adjacency: Adjacency) -> AllPairs:
    nodes = list(adjacency)
    dist: AllPairs = {a: {b: (0.0 if a == b else math.inf) for b in nodes} for a in nodes}

    for a, edges in adjacency.items():
        for nxt, _edge_id, weight in edges:
            if weight < dist[a][nxt]:      # 平行辺は軽い方
                dist[a][nxt] = weight

    for k in nodes:                        # k を「中継してよい点」に加える
        for i in nodes:
            if dist[i][k] == math.inf:
                continue                    # i から k に行けないなら k 経由は無意味
            for j in nodes:
                through_k = dist[i][k] + dist[k][j]
                if through_k < dist[i][j]:
                    dist[i][j] = through_k
    return dist
```

- **これも DP**。部分問題は「中継に使ってよい点を `{最初の k 個}` に限ったときの i→j 最短」。`k` を 1 つ増やすたびに「k を経由するか / しないか」の 2 択で更新する ── Knapsack の「アイテムを使うか / 使わないか」と同じ形。
- **`math.inf` で初期化**。到達不能を「無限大」で表すと `min` / `+` がそのまま使える
  (`inf + x == inf`)。`dist[a][a] = 0.0`。
- **平行辺**(同じ 2 点を結ぶ複数 leg)は軽い方を採用 ── 最短経路では重い方は絶対に使わない。
  `nx.Graph` が平行辺を持てない問題(Phase 4 の既知事象)と同じ判断。
- **numpy を使わない**(README §8「コア層に数値ライブラリを入れない」)。訪問候補は数十のオーダーで、密行列でも O(V³) は一瞬。手実装で計算量とループの意味を説明できることが優先。

計算量: 時間 **O(V³)**、空間 O(V²)。V = 訪問候補地の数。

> **訪問順の前処理に使う `build_leg_adjacency`(`TravelData` → 移動 cost の隣接リスト)は
> この章では作らない。** `TravelData` は 7-3 で生まれる葉なので、`adjacency.py` にその
> import を足すのは 7-4(`travel_common.all_pairs` が最初の消費者)。7-1 の `floyd_warshall`
> は `adjacency.py` の `Adjacency` 型だけを使い、テストは素の隣接リスト(`_adj` ヘルパ)を
> 渡す ── だからこの章は既存ファイルに触れず自己完結する(進行のルール #15)。

---

## 2. DP の考え方 ── 7-2 以降の共通言語

| 用語         | 意味                             | Travel Planner での例                                     |
| ---------- | ------------------------------ | ------------------------------------------------------ |
| **部分問題**   | 元問題を小さくしたもの。答えを表に貯める           | 「予算 a・時間 b までで最初の i 個の place から得られる最大効用」               |
| **最適部分構造** | 部分問題の最適解を組み合わせると全体の最適解になる      | place i を入れる最適解 = 「i を除いた (a−cost, b−dur) の最適解」+ i の効用 |
| **重複部分問題** | 同じ部分問題が何度も現れる ── だから表に貯める価値がある | (a, b) の状態は place を変えながら何度も参照される                       |
| **ボトムアップ** | 小さい部分問題から表を埋める(ループ)            | `knapsack_2d` の三重ループ                                   |
| **メモ化**    | トップダウン再帰 + 計算済みをキャッシュ          | 今回は使わない(ボトムアップの方が状態遷移が見える)                             |
| **擬多項式**   | 入力の「値」に比例(桁数でなく)               | O(n · budget · time) ── 予算を 10 倍にすると表も 10 倍            |

**貪欲(Phase 5)との違い**: 貪欲は「その場の最善」を選んで戻らない(MST は cut property がそれを正当化した)。DP は「あとで良い方を選べるように全部の部分解を覚えておく」。Knapsack は貪欲だと最適を外す(効率の良い順に詰めても、容量ぴったりの組み合わせを逃す)ので DP が要る。

---

## 3. まとめ

- Floyd-Warshall = 全点対最短。「中継に使ってよい点を k 個に限る」を k で回す DP。三重ループ、`math.inf` 初期化、平行辺は軽い方。numpy なし。O(V³)。
- この章は `floyd_warshall.py` + テストだけ ── 既存ファイルに触れず自己完結。
  `TravelData` を受ける `build_leg_adjacency` は 7-4。
- DP の語彙(部分問題 / 最適部分構造 / ボトムアップ / 擬多項式)は 7-2 以降で使い続ける。

## テスト観点(`textbook/samples/tests/unit/test_floyd_warshall.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `floyd_warshall`(純粋関数)
> - **ドライバ**: このテスト関数。`_adj` ヘルパ(素の無向辺リスト → 隣接リスト)で直接入力
> - **スタブ**: **不要** ── 純粋で外部依存を呼ばない(`Phase-0-3.md` の純粋レイヤー)

| ケース                    | 期待                                                       |
| ---------------------- | -------------------------------------------------------- |
| 直接辺 A-B=3 / B-C=4      | `dist["A"]["B"] == 3` / `dist["A"]["A"] == 0`            |
| A-B=10 / A-C=1 / C-B=1 | `dist["A"]["B"] == 2`(C 経由)/ 無向なので `dist["B"]["A"] == 2` |
| 2 つの島(A-B と C-D)       | `dist["A"]["C"] == math.inf`                             |
| 平行辺(A-B に 5 と 2)       | `dist["A"]["B"] == 2`(軽い方)                               |

> **この章のテストは 4 本とも `_adj` ベースで即緑** ── fixture も `TravelData` も import
> しない。`build_leg_adjacency` のテストは 7-4 で `test_travel_strategies.py` に入る。

`uv run pytest tests/unit/test_floyd_warshall.py` / `uvx pyright app/algorithms/graph`。

---

次章([Phase-7-2](./Phase-7-2.md))では、作業単位 7-2 ── Knapsack DP。予算 × 時間の 2 次元
0/1 ナップサックを `knapsack_2d` としてボトムアップで書き、`KnapsackDpTravelStrategy` が
place を「選ぶ」ところまでを実装する(移動コストはまだ入れない ── それは 7-4)。
