# Phase 5-4: MST ストラテジー ── Kruskal / Prim (+ networkx)(作業単位 5-4)

## この章のゴール

5-3 で配線した `network_design` を実際に解く。最小全域木の 2 大アルゴリズム:

- **Kruskal** ── リンクを weight 昇順に見て、閉路を作らないものだけ採用(`UnionFind` を使う)
- **Prim** ── 木を 1 ノードずつ育て、木の外へ出る最小リンクを取り続ける(優先度キュー)
- **networkx MST** ── `nx.minimum_spanning_tree`。別実装オラクル + 2 トラック比較

そして `registry` に `"network_design"` キーを新設する ── Phase 1 以来はじめて registry に新しい problem_type が加わる。

**この章で新規作成するファイル**: `app/algorithms/graph/{mst,kruskal,prim,networkx_mst}.py`。
**既存ファイルへの変更**: `app/algorithms/registry.py`(`"network_design"` キー + 3 本)。

対応サンプル: `samples/app/algorithms/graph/{mst,kruskal,prim,networkx_mst}.py`。
テストは `samples/tests/unit/test_mst_strategies.py`(**5-3 から移設した
`test_network_design_end_to_end_pipeline` を含む** ── validate→select→solve→verify のフルパイプラインは registry が埋まるこの章で初めて green。#15)、`samples/tests/unit/test_algorithm_selection.py`。
設計は README §12.6、`Phase-0-4.md` §2.4(`KruskalStrategy` が `union_find` を使う典型例)、`Phase-5-1.md`(`UnionFind` の実装)、`Phase-5-2.md`(なぜ weight 昇順の貪欲で最適になるか)。

---

## 1. `mst.py` ── MST 共通の足回り

route 3 strategy に `segments.py` があったように、MST 3 strategy にも共通部分がある:

```python
# app/algorithms/graph/mst.py(要点。全文は samples)
def parse_network_problem(problem) -> tuple[NetworkDesignData, set[str], set[str]]:
    # (data, 使えないリンク id, 必須リンク id)

def resolve_required(data, forbidden, required) -> tuple[list[NetworkLink], UnionFind] | None:
    # 必須リンクを先に採用し、それらで union 済みの UnionFind を返す。
    # 必須リンクが「候補に無い / 使えない指定と矛盾 / 必須同士で閉路」なら None(infeasible)

def mst_solution(selected: list[NetworkLink] | None, ops, meta) -> CandidateSolution:
    # selected=None → infeasible。ops=None(ライブラリ)なら "_ops" を入れない
```

- **必須リンクの扱いを共通化** ── Kruskal も Prim も「必須リンクを先に木に入れ、残りを普通に」。
  `resolve_required` が必須リンクを検証して UnionFind を初期化する。

---

## 2. `KruskalStrategy`

```python
# app/algorithms/graph/kruskal.py(要点。全文は samples)
class KruskalStrategy:
    meta = AlgorithmMeta(name="kruskal", family="graph", implementation="handwritten",
        time_complexity="O(E log E)", space_complexity="O(V)")

    def solve(self, problem):
        data, forbidden, required = parse_network_problem(problem)
        resolved = resolve_required(data, forbidden, required)
        if resolved is None:
            return mst_solution(None, 0, self.meta)      # 必須リンクが矛盾
        selected, uf = resolved
        need = max(len(data.nodes) - 1, 0)
        for link in sorted(残りの候補, key=lambda l: l.weight):   # weight 昇順
            if len(selected) == need: break
            a, b = link.endpoints
            if uf.union(a, b):                           # False なら閉路 → スキップ
                selected.append(link)
        if len(selected) != need:
            return mst_solution(None, ops, self.meta)    # 全拠点を繋げなかった
        return mst_solution(selected, ops, self.meta)
```

- **`union_find.py`(プリミティブ)を `KruskalStrategy.solve`(ストラテジー)が使う典型**(`Phase-0-4.md` §2.4 の例そのもの)。`uf.union(a, b)` の戻り値だけで閉路判定が済む。
- **`_ops` = union を試みた回数**。Prim の `_ops`(heap pop 数)とは単位が違う。
- 選んだリンクが `V-1` 本に届かなければ非連結 → `infeasible`(Validation で連結性は
  弾いているはずだが、forbidden との組み合わせで実行時に非連結になることもある)。

---

## 3. `PrimStrategy`

```python
# app/algorithms/graph/prim.py(要点。全文は samples)
class PrimStrategy:
    meta = AlgorithmMeta(name="prim", family="graph", implementation="handwritten",
        time_complexity="O(E log V)", space_complexity="O(V)")

    def solve(self, problem):
        adjacency = build_link_adjacency(data, forbidden)
        in_tree = {必須リンクの端点} | {最初のノード}
        heap = [(weight, link_id, 到達先) for 木から出るリンク]   # 優先度キュー
        while heap and len(selected) < need:
            w, lid, v = heapq.heappop(heap); ops += 1
            if v in in_tree: continue                    # 別ルートで先に木へ入った
            in_tree.add(v); selected.append(link_by_id[lid])
            for 新しく木から出るリンク: heapq.heappush(heap, ...)
```

- Kruskal が「辺を大局的に軽い順」、Prim は「今の木から出る辺のうち最小」。同じ MST を違う順で組み立てる ── 総コストは必ず一致する(MST の一意性は重みが全て異なるとき、一致しなくても総コストは同じ)。
- **`_ops` = heap pop 数**。

---

## 4. `NetworkxMST`

```python
# app/algorithms/graph/networkx_mst.py(要点)
class NetworkxMST:
    meta = AlgorithmMeta(name="kruskal", family="graph", implementation="library:networkx", ...)
    def solve(self, problem):
        # 必須リンクは weight を一時的に最小以下に下げて「必ず選ばれる」ようにしてから
        # nx.minimum_spanning_tree → id で元のリンクに戻す。_ops は積まない。
```

- `name="kruskal"`(networkx の MST は内部で Kruskal 系)、`implementation="library:networkx"`。
  手実装 Kruskal との「同じアルゴリズムの 手実装 vs ライブラリ」比較。
- **必須リンクの強制**は networkx に直接の仕組みが無いので、重みを下駄で下げて必ず選ばせる→ id で元に戻す。この「ライブラリの制約対応は一手間かかる」ことも 2 トラック比較の観察点。

---

## 5. registry の配線 ── 新しい problem_type キー

```python
# app/algorithms/registry.py
from app.algorithms.graph.kruskal import KruskalStrategy
from app.algorithms.graph.prim import PrimStrategy
from app.algorithms.graph.networkx_mst import NetworkxMST

REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [ ... ],
    "shift_scheduling": [ ... ],
    "network_design": [            # ← Phase 5-4 で新設
        KruskalStrategy(),
        PrimStrategy(),
        NetworkxMST(),
    ],
}
```

- `get_strategies` / `all_strategies` / `find_strategy` は**変更不要** ── `REGISTRY.get(problem_type, [])`
  で新キーも自然に引ける。「新アルゴリズムの追加は 1 行」= オープン・クローズドの原則。
- `select_strategy`(route 分岐は 4-5、network_design 分岐は 5-3)は network_design のとき
  `_preferred_name` が `"kruskal"` を返すので、自動選択の既定は Kruskal。
- ベンチ(`POST /benchmark`)は network_design を投げると Kruskal / Prim / networkx が横並びで走る。
- **この 1 行(registry キー)で `POST /solve` の全経路が network で通る** ── 5-3 で配線したvalidate → `select_strategy` → solve → verify が、候補が入って初めて end-to-end で緑になる。
  `test_mst_strategies.py::test_network_design_end_to_end_pipeline`(5-3 から移設)がそれを 1 本で確認する(5-3 状態では `select_strategy` が `NoAlgorithmError`)。

---

## 6. まとめ

- Kruskal = weight 昇順 + `UnionFind` で閉路回避。Prim = 優先度キューで木を育てる。総コストは一致。
- `mst.py` に共通足回り(`parse_network_problem` / `resolve_required` / `mst_solution`)。
- `NetworkxMST` は別実装オラクル。必須リンクは重みの下駄で強制。
- `registry` に `"network_design"` キーを新設 ── `get_strategies` 等は無変更。
- `_ops` の単位(Kruskal=union 試行、Prim=heap pop)はアルゴリズムごとに違う。

## テスト観点(`samples/tests/unit/test_mst_strategies.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `KruskalStrategy` / `PrimStrategy` / `NetworkxMST` の `solve`。加えて
>   `test_network_design_end_to_end_pipeline` は `ProblemValidationService` → `select_strategy` →
>   `solve` → `SolutionVerificationService` のフルパイプライン(5-3 から移設)
> - **ドライバ**: このテスト関数(`@pytest.mark.parametrize` で 3 strategy を回す)。
>   `build_network_problem` / `build_disconnected_network_problem` が入力生成
> - **スタブ**: **不要** ── 純粋(networkx も決定論的)。end-to-end も DB / Redis を触らない

| ケース                                         | 期待                                                      |
| ------------------------------------------- | ------------------------------------------------------- |
| 例題(既知 MST コスト 10)                           | 3 strategy とも `total_weight == 10.0` / 選択リンク数 == V-1    |
| 必須 `L_ac` + 禁止 `L_bc`                       | 選択に `L_ac` を含み `L_bc` を含まない(3 strategy とも)              |
| 孤立ノードあり                                     | 3 strategy とも `status == "infeasible"`                  |
| 必須リンクが閉路を作る指定                               | `status == "infeasible"`                                |
| 手実装 vs library                              | 手実装は `metrics["_ops"]` あり、networkx は無し                  |
| validate → select → solve → verify(network) | `status == "valid"` / `metrics["total_weight"] == 10.0` |

`uv run pytest tests/unit/test_mst_strategies.py` / `uvx pyright app/algorithms/graph`。

---

次章([Phase-5-5](./Phase-5-5.md))では、作業単位 5-5 ── Network Designer ページ。Phase 4-8 の
Route Planner と同型で、MST 結果を `GraphCanvas` に(選んだリンクは実線、候補は破線)描き、
Kruskal / Prim / networkx を横並び比較する。`types.ts` と `menu-tree.ts` に network アームを足す。
