# Phase 1-3: 探索プリミティブ ── Linear / Binary Search・BFS・DFS(作業単位 1-3)

## この章のゴール

README §8「アルゴリズムは単独で実装せず、実際の問題解決機能の内部で利用する」を
体現する **アルゴリズム・プリミティブ** を 4 つ実装する。

- `app/algorithms/search/{linear_search,binary_search,bfs,dfs}.py`
- プリミティブは registry に載せない素の純粋関数。入力は**素のデータ構造**
  (ソート済み列・隣接リスト)で、`OptimizationProblem` は知らない
- 計算量、境界ケース、再現性
- BFS は [Phase-1-6](./Phase-1-6.md) の route Validation で到達可能性オラクルとして再利用する

**この章で新規作成するファイル**: `app/algorithms/search/{linear_search,binary_search,bfs,dfs}.py`。

対応サンプル: `samples/app/algorithms/search/*.py`、
テストは `samples/tests/unit/test_search_primitives.py`。計算量は `Phase-0-5.md` §2.1。

---

## 1. プリミティブとストラテジーの違い(`Phase-0-4.md` §2.4 再掲)

| | AlgorithmStrategy | アルゴリズム・プリミティブ(この章) |
| --- | --- | --- |
| 役割 | 問題まるごとを解く | 部品・技法。ストラテジーの内部や別の計算で使う |
| シグネチャ | `solve(problem) -> CandidateSolution` に統一 | それぞれ自然な形。`binary_search(seq, target) -> int` |
| 置き場所 | `app/algorithms/{graph,optimization,scheduling}/` | `app/algorithms/{search,patterns}/` |
| `registry` | 載る | **載らない** |
| `AlgorithmMeta` | 持つ | 不要(素の関数) |

Phase 1 では BFS / DFS も **プリミティブ**として実装する(`route_planning` を BFS 単体で解く
`problem_type` は無い)。registry に載るのは Dijkstra だけ([Phase-1-4](./Phase-1-4.md))。

---

## 2. Linear Search / Binary Search

```python
# app/algorithms/search/linear_search.py
def linear_search[T](seq: Sequence[T], target: T) -> int:
    """先頭から走査。target と等しい最初の添字、無ければ -1。時間 O(n) / 空間 O(1)。"""
    for i, value in enumerate(seq):
        if value == target:
            return i
    return -1
```

```python
# app/algorithms/search/binary_search.py
class _Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...   # other: Any で int/str/float が満たせる

def binary_search[C: _Comparable](seq: Sequence[C], target: C) -> int:
    """**昇順ソート済み** の seq から target の添字。無ければ -1。O(log n) / O(1)。"""
    lo, hi = 0, len(seq) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2            # 桁溢れを避ける書き方
        if seq[mid] == target:
            return mid
        if seq[mid] < target:                # 右半分に絞る
            lo = mid + 1
        else:                                # 左半分に絞る
            hi = mid - 1
    return -1
```

- **PEP 695 ジェネリクス**(`def linear_search[T](...)`)を使う。`decitima-api` の
  `CRUDRepository[ModelType: Base]` と同じ流儀。ruff `UP047` に沿う。
- `_Comparable.__lt__(self, other: Any)` の `Any` がポイント。`object` にすると
  組み込み型(`int.__lt__(self, other: int)`)が満たせず pyright が怒る。
- 前提(昇順)の確認用に `is_sorted_ascending[C: _Comparable](seq) -> bool` も置く
  (テストや assert で使う。「分割統治」= 探索範囲を毎回半分にする、の前提)。

---

## 3. BFS ── 無重み最短経路・到達可能性

隣接リストは `Mapping[str, Iterable[str]]`(node_id → 隣接 node_id)。

```python
# app/algorithms/search/bfs.py
from collections import deque

AdjacencyList = Mapping[str, Iterable[str]]

def bfs_distances(adjacency: AdjacencyList, start: str) -> dict[str, int]:
    """start からの各ノードへの最短ホップ数。到達不能なノードは含めない。"""
    distances = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in adjacency.get(node, ()):
            if nxt not in distances:        # 初回訪問が最短(BFS の性質)
                distances[nxt] = distances[node] + 1
                queue.append(nxt)
    return distances

def reachable_nodes(adjacency, start) -> set[str]:
    """start から到達できるノード集合。route Validation の連結性チェックに使う。"""
    return set(bfs_distances(adjacency, start))

def bfs_shortest_path(adjacency, start, goal) -> list[str] | None:
    """start→goal の無重み最短経路(ノード列)。到達不能なら None。
    parent 辞書を goal から辿って復元する。"""
    ...
```

- `bfs_distances` の「未訪問なら距離確定」が BFS の核。キューが FIFO だから初回訪問が最短。
- `reachable_nodes` を [Phase-1-6](./Phase-1-6.md) の `ProblemValidationService` が
  「禁止エッジ除去後に goal へ到達できるか」に使う。

---

## 4. DFS ── 経路の有無・訪問順(再帰)

```python
# app/algorithms/search/dfs.py
def dfs_preorder(adjacency: AdjacencyList, start: str) -> list[str]:
    """深さ優先で訪問したノードを行きがけ順に返す。"""
    visited: set[str] = set()
    order: list[str] = []

    def _visit(node: str) -> None:
        visited.add(node)
        order.append(node)
        for nxt in adjacency.get(node, ()):
            if nxt not in visited:
                _visit(nxt)                 # 再帰(README §8 の Recursion)

    _visit(start)
    return order

def dfs_has_path(adjacency, start, goal) -> bool:
    """start から goal へ到達できるか(経路の存在のみ。最短性は問わない)。"""
    ...
```

DFS は無重みでも「最短」を保証しない(それは BFS)。連結判定・経路の有無・順序づけ向き。
Phase 5 の Backtracking、Phase 7 のトポロジカルソートの下地でもある。

---

## 5. テスト観点(`samples/tests/unit/test_search_primitives.py`)

> **テスト対象 / ドライバ / スタブ**(進行ルール #14):
> - **対象**: 探索プリミティブ 4 種(`linear_search` / `binary_search` / `bfs` / `dfs`)
> - **ドライバ**: テスト関数(ソート済み列・隣接リストなど素のデータ構造を直接渡す)
> - **スタブ**: **不要**(純粋関数。フィクスチャすら要らない)

`Phase-0-9.md` §1.1: 「正常系 / 空入力 / 単一要素 / 到達不能 / 既知の最短距離と一致」。

- `binary_search`: 先頭・末尾・中間・不在・単一要素 `[42]`・空 `[]`
- ソート済み入力で `binary_search` と `linear_search` の結果が一致
- `bfs_distances` が既知のホップ数と一致 / `path` の長さ = 距離
- `start == goal` は `[start]` / 到達不能は `None`・`reachable_nodes` は `{start}`
- `dfs_preorder` が到達可能ノードを全部含む / `dfs_has_path` の真偽
- 単一ノード

すべて純粋関数。DB もフィクスチャも不要。1 テスト 1ms 未満で、入力を変えて何千でも回せる。

---

## 6. まとめ

- 探索 4 種はプリミティブ ── registry に載せず、入力は素のデータ構造。
- PEP 695 ジェネリクス。`_Comparable.__lt__(self, other: Any)` の `Any` に注意。
- BFS の `reachable_nodes` は Phase 1 の route Validation で再利用する。
- DFS は最短を保証しない。連結判定・経路の有無向き。
- テストは純粋関数テスト(主戦場)。境界ケースを厚く。

次章([Phase-1-4](./Phase-1-4.md))では、作業単位 1-4 ── これらを内部で使う
`DijkstraStrategy` を実装する。
