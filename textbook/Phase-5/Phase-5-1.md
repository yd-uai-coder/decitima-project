# Phase 5-1: Union-Find(素集合データ構造)の深掘り(作業単位 5-1)

## この章のゴール

Kruskal(5-4)の心臓部 ── **Union-Find(素集合 / DSU: Disjoint Set Union)** を実装する。
「この 2 要素は同じグループか」「2 つのグループを 1 つにする」を、ならし **O(α(n)) ≒ O(1)** で行う。

- `graph/union_find.py` ── `UnionFind` クラス(`find` / `union` / `connected` / `group_count` / `groups`)
- 2 つの最適化: **経路圧縮**(find のたびに木を平らにする)+ **ランク合併**(低い木を高い木に繋ぐ)
- **`union` が bool を返す**設計 ── 「すでに同じグループ」= その辺は閉路を作る、を Kruskal が使う

> **Kruskal法（クラスカル法）**は、グラフから**最小全域木（Minimum Spanning Tree: MST）**を求めるアルゴリズム
> すべての頂点をつなぎながら、**辺の重みの合計を最小**にしたい場合に使う。

**この章で新規作成するファイル**: `app/algorithms/graph/union_find.py`。

対応サンプル: `samples/app/algorithms/graph/union_find.py`。テストは `samples/tests/unit/test_union_find.py`。
設計は `Phase-0-4.md` §2.4(Strategy とプリミティブの 2 層 ── `UnionFind` は下の層)。

---

## 1. なぜ Union-Find か ── Kruskal （クラスカル法）から逆算する

Kruskal は「辺を weight 昇順に見て、**閉路を作らない辺だけ**採用する」。ここで必要なのは「この辺 (a, b) を足すと閉路ができるか?」= 「a と b はすでに同じ連結成分にいるか?」の判定。

素朴には毎回 BFS/DFS で連結性を確かめられるが、辺 1 本ごとに O(V+E) かかって全体 O(E·(V+E))。
Union-Find なら 1 回の判定+合併がならし O(1) で、Kruskal 全体が **O(E log E)**(ソートが支配的)になる。

**route の連結性(`connectivity.py`)は Union-Find を使わない**理由: あちらは「与えられた隣接リスト全体で 1 つに繋がっているか」を 1 回 BFS するだけ。Union-Find が効くのは「辺を 1 本ずつ足しながら、その都度連結性が知りたい」という Kruskal 特有の使い方のとき。

---

## 2. データ構造 ── 森(forest)で集合を表す

各集合を**根つき木**で表し、`_parent[x]` が x の親を指す(根は自分自身を指す)。
「x の属する集合の代表」= x から親を辿った先の**根**。

```python
# app/algorithms/graph/union_find.py(要点。全文は samples)
class UnionFind:
    def __init__(self, elements: Iterable[str]) -> None:
        self._parent: dict[str, str] = {e: e for e in elements}   # 最初は全員が自分の根
        self._rank: dict[str, int] = dict.fromkeys(self._parent, 0)  # 木の高さの上界
```

- **`_rank[x]`** は「x を根とする木の高さの上界」。合併のとき**どちらをどちらにぶら下げるか**を決めるためだけに使う(厳密な高さではない ── 経路圧縮で実際の高さは下がるが rank は据え置く)。
- id は文字列(`"A"` / `"L_ab"`)。`dict` ベースなので任意の hashable が使える。

---

## 3. `find` ── 根を返す + 経路圧縮

```python
def find(self, x: str) -> str:
    root = x
    while self._parent[root] != root:      # まず根を見つける
        root = self._parent[root]
    while self._parent[x] != root:         # 経路圧縮: 通り道を全部根の直下へ
        self._parent[x], x = root, self._parent[x]
    return root
```

- **経路圧縮(path compression)**: `find(x)` の道中で通ったノードを**すべて根に直結**させる。次回同じノードを引くと 1 ホップで根に着く。
- 2 パス実装(まず根を探し、次に付け替え)。再帰でも書けるが、深い木でスタック超過を避けるためループにする。
- **戻り値は代表元(根の id)**。同じ集合なら誰から呼んでも同じ根が返る ── これが `connected` の基盤。

---

## 4. `union` ── 合併 + ランク、そして **bool を返す**

```python
def union(self, a: str, b: str) -> bool:
    ra, rb = self.find(a), self.find(b)
    if ra == rb:
        return False                       # ← すでに同じ集合 = この辺は閉路を作る
    if self._rank[ra] < self._rank[rb]:
        ra, rb = rb, ra                    # 低い木を高い木にぶら下げる
    self._parent[rb] = ra
    if self._rank[ra] == self._rank[rb]:
        self._rank[ra] += 1                # 同じ高さ同士を繋いだときだけ +1
    return True
```

- **ランク合併(union by rank)**: 低い木を高い木の下に付けると、木の高さが伸びにくい。
  経路圧縮と併用すると、m 回の操作の総計が **O(m·α(n))**(α は逆アッカーマン関数。現実の n では4 以下 = 実質定数)。
- **戻り値の bool が設計の肝**:
  - `True` ── 実際に 2 つの集合を合併した(この辺は木に採用してよい)
  - `False` ── a と b はすでに同じ集合(この辺を足すと**閉路**)
    Kruskal は `if uf.union(a, b): selected.append(link)` と書くだけで閉路回避が済む(`CLAUDE.md` の「命名: `metrics["_ops"]`」と同じく、戻り値に意味を持たせる設計判断)。

`union` を試みた回数が Kruskal の `_ops`(`Phase-5-4.md`)── 「内部の仕事量」の診断指標。

---

## 5. `connected` / `group_count` / `groups` ── 消費側の窓口

```python
def connected(self, a, b) -> bool:  return self.find(a) == self.find(b)
def group_count(self) -> int:       return len({self.find(x) for x in self._parent})
def groups(self) -> list[set[str]]: ...   # 根ごとにノードを bucket
```

- **`connected`** は `route_reachable` の Union-Find 版に見えるが、用途が違う ── Kruskal の内部状態を外から覗くテスト用 + 「必須リンクで初期化済みの uf」を作る `resolve_required`(5-4)で使う。
- **`group_count() == 1`** ⟺ 全ノードが連結。Kruskal の途中で「あと何本繋げば全域木か」の判断に。
- **`groups()`** は主にテストの可視化用(`test_union_find.py` の経路圧縮確認)。

---

## 6. まとめ

- Union-Find = 森で素集合を表し、`find`(根 + 経路圧縮)/ `union`(ランク合併)でならし O(α(n))。
- **`union` の bool 戻り値**が Kruskal の閉路判定そのもの ── `False` = その辺は閉路を作る。
- route の連結性は 1 回 BFS で足りるので Union-Find を使わない。効くのは「辺を 1 本ずつ足しながら都度連結性を問う」Kruskal 特有の使い方。
- registry には載らない **プリミティブ**(`Phase-0-4.md` §2.4 の 2 層の下側)。消費者は Kruskal と
  `resolve_required`。

## テスト観点(`samples/tests/unit/test_union_find.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `UnionFind`(純粋クラス。副作用も外部依存も無い)
> - **ドライバ**: このテスト関数。`UnionFind([...])` を直接組み立てて `union` / `find` を呼ぶ
> - **スタブ**: **不要** ── 完全に自己完結した値の操作

| ケース                                 | 期待                                                       |
| ----------------------------------- | -------------------------------------------------------- |
| `union("a","b")` → `union("b","c")` | `connected("a","c")` が True、`connected("a","d")` は False |
| 既に同じグループへの `union`                  | `False` を返す(Kruskal の閉路判定)                               |
| `find` を数回呼んで経路圧縮                   | `groups()` が正しいグループ分け、`group_count()` が一致                |
| `union` を対称に呼ぶ                      | `find("p") == find("r")`、`connected` は順序に依らない            |

`uv run pytest tests/unit/test_union_find.py` / `uvx pyright app/algorithms/graph/union_find.py`。

---

次章([Phase-5-2](./Phase-5-2.md))では、作業単位 5-2 ── **なぜ「軽い辺から貪欲」で最小全域木が
得られるのか**。cut property(切除性)と交換論法を、小グラフの全域木を全列挙して実測で確かめる。
