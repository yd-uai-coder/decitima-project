# Phase 8-1: トポロジカルソート(DFS)プリミティブ + 理論(作業単位 8-1)

## この章のゴール

工程管理は「タスクを依存関係の順に並べる」から始まる ── 先行タスクが全部終わってからでないと次に進めない。この「全辺 u→v で u が v より前」の並び順が **トポロジカルソート**。
CPM(8-2)の前進パスはこの順で、後退パスは逆順で走る。

この章ではトポロジカルソートを **DFS(深さ優先探索)の後行順の反転** で書く
(README §19「Phase 1 の DFS が Topological Sort の土台になる」)。あわせて **閉路検出**
(DAG でなければ順序は存在しない)と、**Kahn 法**(入次数ベース)との違いを押さえる。

> **トポロジカルソート** ── 有向非巡回グラフ(DAG)の頂点を、すべての有向辺で「元 → 先」になるよう一列に並べること。1 つとは限らない(並行タスクは順不同)。
> **back edge(後退辺)** ── DFS の探索中、まだ探索が終わっていない(スタック上の)頂点へ戻る辺。これがあれば閉路がある。

**この章で作成 / 更新するファイル**:
`app/algorithms/graph/topological.py`(新規)、`tests/unit/test_topological_sort.py`(新規)。
既存ファイルへの変更は無い ── この章は完全に自己完結する。`topological_sort` は
**`ProjectData`(8-3 の葉)を import しない** ── 生の隣接辞書 `Mapping[str, Iterable[str]]` を取る。
`ProjectData` から辞書を組むのは `project_common.build_successors`(8-4)/ `validation.py`(8-3)の仕事。

対応サンプル: `textbook/samples/app/algorithms/graph/topological.py`、
`textbook/samples/tests/unit/test_topological_sort.py`。設計は README §19 Phase 8、CLRS 22 章。

---

## 1. DFS 後行順の反転 ── 「自分の後続を全部片付けてから自分を記録」

```python
# app/algorithms/graph/topological.py(要点。全文は samples)
type Successors = Mapping[str, Iterable[str]]  # node -> 後続 node 群。全 node が key の前提

class CyclicGraphError(Exception):
    """依存グラフに閉路があり、トポロジカル順が存在しない。"""

def topological_sort(successors: Successors) -> list[str]:
    color: dict[str, int] = {}          # 0=未訪問 / 1=探索中(灰)/ 2=完了(黒)
    order: list[str] = []

    def _visit(node: str) -> None:
        color[node] = 1
        for nxt in sorted(successors.get(node, ())):   # 近傍は id 昇順 → 決定論
            state = color.get(nxt, 0)
            if state == 1:                              # 灰へ戻る辺 = back edge = 閉路
                raise CyclicGraphError(f"cycle detected via edge into {nxt!r}")
            if state == 0:
                _visit(nxt)
        color[node] = 2
        order.append(node)                             # 帰りがけ(後行順)に積む

    for node in sorted(successors):
        if color.get(node, 0) == 0:
            _visit(node)
    return order[::-1]                                  # 反転してトポロジカル順に
```

- **なぜ「後行順の反転」でうまくいくか**: `_visit(A)` は A の全後続の `_visit` が終わってから`order.append(A)` する。だから `order` の中では「後続ほど先に、A は後に」並ぶ。最後に反転すれば「A ほど先に、後続は後に」= トポロジカル順。
  
  > 先行順(行きがけ)のDFS と 後行順(帰りがけ)のDFSは結果が異なる。
  > ※感覚的に「逆の反転だから同じ」のように思えるが違う
- **3 色(白 / 灰 / 黒)** ── 白 = まだ見ていない、灰 = 探索スタックに載っている(自分の子孫を探索中)、黒 = 完了。灰の頂点へ戻る辺が back edge(閉路)。黒へ戻る辺は「合流」で問題ない。
  Phase 1 の `dfs_preorder` は `visited` の 2 状態だったが、閉路検出には 3 色が要る。
- **決定論**: 開始頂点を `sorted(successors)`、近傍を `sorted(...)` で辿る。同じ DAG は毎回同じ順。
  ただし **「辞書順」ではない** ── 先に深く潜った頂点ほど後行順で早く確定し、反転で後ろに回る。
  `A -> {B, C}` は `[A, C, B]` を返す(B から先に潜って B が先に黒になり、反転で末尾へ)。

計算量: 時間 **O(V + E)**(各頂点 1 回訪問、各辺 1 回走査)、空間 O(V)(色 + 再帰スタック)。

```python
def has_cycle(successors: Successors) -> bool:
    """validation.py の hard ゲート用 ── 例外でなく bool。"""
    try:
        topological_sort(successors)
    except CyclicGraphError:
        return True
    return False

def successors_from_edges(nodes, edges) -> dict[str, list[str]]:
    """(node 群, (from, to) 辺群)から隣接辞書。孤立 node も後続だけの node も key に含める。"""
```

> **`has_cycle` を分ける理由**: `topological_sort` は「順を返す or 例外」だが、Validation は「閉路があるか?」の **bool** が欲しくて `SemanticIssue` を組み立てる。
> route の `route_reachable`/ network の `all_nodes_connected` が bool を返して `validation.py` が判定するのと同じ形(`Phase-2-2.md` §3)。`validation.py` への配線は 8-3。

---

## 2. Kahn 法(入次数ベース)との対比

DFS 版のほかに、**入次数(そのノードへ入ってくる辺の数)が 0 のノードをキューで剥がしていく**方法がある(Kahn のアルゴリズム)。

```text
入次数 0 のノードをキューに入れる
  取り出す → 出力に追加 → その後続の入次数を 1 減らす → 0 になったらキューへ
出力が V 個に届かなければ閉路がある(入次数が 0 にならないノードが残る)
```

| 観点   | DFS 版(本章の実装)        | Kahn 法                                |
| ---- | ------------------- | ------------------------------------- |
| 出力順  | 後行順の反転(先に潜った枝が末尾)   | キューの順(ソートしたキューなら辞書順 = A, B, C)        |
| 閉路検出 | 灰へ戻る back edge      | 出力数 < V(入次数が減りきらないノードが残る)             |
| 実装   | 再帰(深い DAG で再帰上限に注意) | 反復(キュー)。再帰しない                         |
| 直感   | 「深く行って戻ってくる」        | **「今すぐ着手できるタスクのキュー」** ── 工程管理の実務感覚に近い |

本プロジェクトは README の「**Phase 1 の DFS が土台**」に忠実に **DFS 版を採用**する。Kahn 法は「今できるタスクのキュー」という工程管理の直感に近く、CPM の前進パスを Kahn のキュー順で一体化して書くこともできる ── が、本章では DFS 版 1 本に絞り、CPM(8-2)は `topological_sort` の
結果を受け取る形にする(関心の分離)。

> **DFS を選んだのは README 準拠 + 教材の連続性が主な理由で、技術的な優位ではない。** 依存 DAG が
> 大規模化する工程管理では、反復で再帰上限に当たらず・CPM 前進パスと融合でき・辞書順を出せる
> Kahn 法の方が適する面がある。**Kahn 法ベースへの置換はプロジェクト完成後（Phase 15 以降）の
> 検討課題として記録している**(`q_a.md` Q46 / `CLAUDE.md`「### 設計判断・検証知見」→
> 「未ルール化の確定事項」)。`has_cycle` / `successors_from_edges` の公開シグネチャは Kahn 版でも
> 不変にできるので、置換時の影響は `topological.py` + テスト + 本章 §1/§2 に閉じる。

---

## 3. まとめ

- トポロジカルソート = DFS 後行順の反転。3 色で back edge(閉路)を検出。近傍 id 昇順で決定論。
  出力は「辞書順」ではない点に注意。O(V + E)。
- `has_cycle` は同じ探索を bool 化したもの(Validation の hard ゲート用)。
- `successors_from_edges` は「辺リスト → 隣接辞書(全 node が key)」の小道具。
- この章は `topological.py` + テストだけ ── 既存ファイルに触れず自己完結。`ProjectData` を
  受ける配線(`build_successors` / validation の閉路ゲート)は 8-3 / 8-4。

## テスト観点(`textbook/samples/tests/unit/test_topological_sort.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `topological_sort` / `has_cycle` / `successors_from_edges`(すべて純粋関数)
> - **ドライバ**: このテスト関数。`_succ` ヘルパ((from, to) 辺リスト → 隣接辞書)で直接入力、
>   `_respects` ヘルパで「全辺が守られているか」を検査
> - **スタブ**: **不要** ── 純粋で外部依存を呼ばない(`Phase-0-3.md` の純粋レイヤー)

| ケース                    | 期待                                          |
| ---------------------- | ------------------------------------------- |
| 直鎖 A→B→C→D             | `["A", "B", "C", "D"]`                      |
| ダイヤ A→{B,C}→D          | 全辺を守る(`_respects`)/ 先頭 A・末尾 D               |
| 孤立ノード / 後続だけのノード       | 出力に含まれる(`successors_from_edges` が key に入れる) |
| `A -> {C, B}`(近傍順)     | `["A", "C", "B"]`(DFS 後行順の反転。辞書順ではない)       |
| 閉路 A→B→C→A             | `CyclicGraphError`                          |
| `has_cycle`(閉路あり / なし) | `True` / `False`(例外を投げない)                   |
| 自己ループ A→A              | `has_cycle` が `True`                        |

`uv run pytest tests/unit/test_topological_sort.py` / `uvx pyright app/algorithms/graph`。

---

次章([Phase-8-2](./Phase-8-2.md))では、作業単位 8-2 ── Critical Path Method。トポロジカル順を
使って前進パス(最早開始 / 終了)、逆順で後退パス(最遅開始 / 終了)、そこから余裕(slack)と
クリティカルパス、全体所要(makespan)を求める。`cpm` も生の dict を取る純粋関数で、`ProjectData`
(8-3)にはまだ触れない。
