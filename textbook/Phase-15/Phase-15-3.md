# Phase 15-3: `topological_sort` 大規模実測 → Kahn法へ置換(作業単位 15-3)

## この章のゴール

`app/algorithms/graph/topological.py`(Phase 8-1、DFSベース)を大規模な依存グラフで実測し、`Phase-8-1.md` §2 が予告していた「反復で再帰上限に当たらない」というKahn法の利点が実際に問題になるかを確認する。**結論: なる**。DFS版は実際にクラッシュするため、`has_cycle`/`successors_from_edges` のシグネチャを保ったまま Kahn 法(入次数キュー)へ置換する。

**この章で作成 / 更新するファイル**: `app/algorithms/graph/topological.py`(改訂、
DFS→Kahn法)、`tests/unit/test_topological_sort.py`(改訂、出力順アサーションの更新)、`tests/performance/test_topological_perf.py`(新規)。

---

## 1. 実測 ── 線形依存チェーンで DFS 版は本当にクラッシュするか

`tests/performance/generators.py::linear_chain_successors`(Phase 15-1)で
T0→T1→…→T(n-1) の一直線 DAG を作り、`topological_sort`(DFS版)に通す:

```python
# 使い捨てスクリプト(実測用)
import sys
from app.algorithms.graph.topological import topological_sort

def linear_chain(n):
    return {f"T{i}": [f"T{i+1}"] if i < n - 1 else [] for i in range(n)}

print("recursion limit:", sys.getrecursionlimit())
for n in [900, 990, 995, 999, 1000, 5000]:
    try:
        topological_sort(linear_chain(n))
        print(n, "OK")
    except RecursionError as e:
        print(n, "RecursionError")
```

実測結果:

| n       | 結果                   |
| ------- | -------------------- |
| 900     | OK                   |
| 990     | OK                   |
| 995     | OK                   |
| **999** | **`RecursionError`** |
| 1000    | `RecursionError`     |
| 5000    | `RecursionError`     |

Python既定の再帰上限(`sys.getrecursionlimit()` = 1000)に対し、`_visit` の再帰は
1ノードにつき1段深くなる(線形チェーンなので枝分かれによる再帰の分散が起きない) ──
n≈999 から確実に `RecursionError` で `solve()` 全体がクラッシュする。project_scheduling で数百〜数千規模の直列工程(建設・製造のような逐次依存の強いプロジェクト)は非現実的ではない。**これは投機的な最適化ではなく、実測で再現できる実際の不具合**であり、`Phase-8-1.md` の「Kahn法ベースへの置換はプロジェクト完成後(Phase 15以降)の検討課題」が正式にトリガーされた(進行のルール #17 ──「今駆動している、実在の消費者」は Phase 15 自身の大規模入力テストという形で具体的に答えられる)。

## 2. Kahn 法へ置換 ── 公開シグネチャは不変

`Phase-8-1.md` §2 の対比表がすでに Kahn 法の仕組みを説明済み:「入次数0のノードをキューへ→取り出して出力→後続の入次数を1減らす→0になったらキューへ」を反復するだけで、**再帰を一切使わない**。

```python
# app/algorithms/graph/topological.py(改訂、要点。全文は samples)
def topological_sort(successors: Successors) -> list[str]:
    nodes = sorted(successors)
    indegree: dict[str, int] = dict.fromkeys(nodes, 0)
    for node in nodes:
        for nxt in successors.get(node, ()):
            indegree[nxt] = indegree.get(nxt, 0) + 1

    queue: list[str] = [n for n in nodes if indegree[n] == 0]
    heapq.heapify(queue)          # id昇順に取り出すため優先度付きキューを使う

    order: list[str] = []
    while queue:
        node = heapq.heappop(queue)
        order.append(node)
        for nxt in sorted(successors.get(node, ())):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(queue, nxt)

    if len(order) != len(nodes):
        raise CyclicGraphError(...)   # 入次数が0に届かないノードが残る = 閉路
    return order
```

> **samples の実態**: `textbook/samples/app/algorithms/graph/topological.py` では、
> 進行のルール #12 どおり **旧 DFS 版の関数本体を `# (Phase 8-1)` タグ付きでまるごと
> コメントアウトして残し**、その直後に `# (Phase 15-3)` タグ付きで上記 Kahn 版を追記している
> (削除ではなく置換の記録)。後から Phase 8 時点のコードを読み返せるようにするため。

`has_cycle`/`successors_from_edges` は無改造。`cpm`(Phase 8-2)は `topological_sort` の戻り値(`list[str]`)を順に処理するだけで、DFS由来の特定の順序には依存していない ──
`tests/unit/test_critical_path.py`・`test_cpm_strategy.py`・`test_project_strategies.py`・
`test_cpsat_project.py` を含む project_scheduling 関連60テストが無改造のまま全て緑になることを確認した(次節)。

**観測可能な変化が1つある**: 出力順が「DFS後行順の反転」から「id昇順キューの取り出し順」に変わり、**辞書順になる**(`Phase-8-1.md` §2 の対比表どおり)。CPM の計算結果(makespan・クリティカルパス・slack)には影響しないが、`test_deterministic_neighbour_order` がDFS固有の出力(`["A", "C", "B"]`)を直接アサートしていたため、この1テストだけ更新が要る。

```python
# tests/unit/test_topological_sort.py(改訂)
def test_deterministic_neighbour_order() -> None:
    # (Phase 8-1)
    # succ = _succ(["A", "B", "C"], [("A", "C"), ("A", "B")])
    # assert topological_sort(succ) == ["A", "C", "B"]
    # (Phase 15-3) Kahn法(入次数の昇順キュー)に置換 ── 出力は辞書順になった。
    succ = _succ(["A", "B", "C"], [("A", "C"), ("A", "B")])
    assert topological_sort(succ) == ["A", "B", "C"]
    assert _respects(topological_sort(succ), [("A", "C"), ("A", "B")])
```

> **写経の罠**: この置換は「アルゴリズムを変えたのに既存テストが1つも落ちない」ことを期待しがちだが、**出力順という観測可能な挙動が変わった以上、それを直接アサートしていたテストは意図的に更新するのが正しい**。「全テストが無改造で緑」を目指すのではなく、「公開契約(`has_cycle`/`successors_from_edges` のシグネチャ、`cpm` の計算結果)が不変であること」を目指す。

## 3. なぜ回帰しないと確信できるか ── 60テストの再実行

`topological_sort` を直接 import しているのは `cpm`(Phase 8-2)1箇所だけ(`grep` で確認)。
project_scheduling に関わる既存テスト一式(`test_topological_sort.py`・`test_critical_path.py`・`test_cpm_strategy.py`・`test_project_common.py`・`test_project_scheduling.py`・`test_project_strategies.py`・`test_cpsat_project.py`、計60件)を overlay 上で再実行し、
1件の更新(§2)を除き無改造のまま全て緑であることを確認した。

---

## まとめ

## テスト観点

`tests/unit/test_topological_sort.py`:

> **対象**: `topological_sort`(Kahn法版)/ **ドライバ**: 各テスト関数 / **スタブ不要**(純粋関数)

`tests/performance/test_topological_perf.py`:

> **対象**: `topological_sort` / **ドライバ**: このテスト関数 + `measure` フィクスチャ(Phase 15-1)
> **スタブ不要**(純粋関数)

| ケース              | 期待                                                      |
| ---------------- | ------------------------------------------------------- |
| n=50,000 の線形チェーン | `RecursionError` を出さず、`["T0", "T1", ..., "T49999"]` を返す |
| 同上の実行時間(3回、中央値)  | 1秒未満(O(V+E) なので反復コストは小さい)                               |

```bash
uv run pytest tests/unit/test_topological_sort.py -v
uv run pytest tests/unit/test_critical_path.py tests/unit/test_cpm_strategy.py \
  tests/unit/test_project_common.py tests/unit/test_project_scheduling.py \
  tests/unit/test_project_strategies.py tests/unit/test_cpsat_project.py -v   # 無回帰確認(60 passed)
uv run pytest tests/performance/test_topological_perf.py -v -m performance
```

---

次章([Phase-15-4](./Phase-15-4.md))では DB クエリを実測監査する ── こちらは「実測の結果、
現状維持でよい」という、15-2 と同じ側の結論になる。
