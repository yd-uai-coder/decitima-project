# Phase 0-4: Algorithm Engine 設計

## この章のゴール

`app/algorithms/` の心臓部を設計する。

- `AlgorithmStrategy` インターフェース ── すべてのアルゴリズムが従う契約
- `registry` ── 問題タイプからアルゴリズム候補を引く仕組み
- 2 トラック(手実装 / 産業ソルバー)を同じ契約に載せる方法
- アルゴリズム選択のロジック(Phase 0 では rule-based まで)
- Route Planner と Shift Scheduler を実際にこの契約に当てはめる

対応サンプル: `samples/algorithm_strategy.py`, `samples/route_planner_example.py`,
`samples/shift_scheduler_example.py`。

---

## 1. なぜインターフェースを 1 つに統一するのか

DeciTima は README 8 節のとおり多くのアルゴリズムを持つ予定:
BFS / DFS / Dijkstra / Bellman-Ford / A* / 貪欲法 / 動的計画法 / ナップサック /
バックトラッキング / 分枝限定法 / 全探索 / Kruskal / Prim / ...

このうち **問題まるごとを解く** ものを、**バラバラのシグネチャ**で実装すると:

```python
def dijkstra(graph, start, goal) -> list[str]: ...
def backtracking_shift(staff, slots, constraints) -> dict: ...
def knapsack(items, capacity) -> list: ...
```

- `SolveService` はアルゴリズムごとに呼び出し方を分岐しないといけない。
- ベンチマーク(Phase 3)は「同じ入力を全アルゴリズムに渡す」ができない。
- 手実装 Dijkstra と networkx 版を差し替えるのに呼び出し側を直す必要がある。

**問題まるごとを解くアルゴリズムが同じ `solve(problem) -> solution` に従えば**、これらが消える。
呼び出し側は「`AlgorithmStrategy` を 1 つ受け取って `.solve()` を呼ぶ」だけ。

---

## 2. `AlgorithmStrategy` インターフェース

Python の `typing.Protocol` で定義する(継承を強制しない構造的部分型)。

```python
# app/algorithms/base.py
from typing import Protocol, runtime_checkable

# @runtime_checkableはその Protocol を isinstance() や issubclass() で実行時チェックできるようにするもの
@runtime_checkable
class AlgorithmStrategy(Protocol):
    """1つのアルゴリズムが満たす契約。problem を受けて candidate solution を返す。"""

    meta: AlgorithmMeta

    def solve(self, problem: OptimizationProblem) -> CandidateSolution: ...
```

### 2.1 なぜ `Protocol` か(抽象基底クラス ABC ではなく)

|            | `Protocol`                    | `ABC`(継承)                        |
| ---------- | ----------------------------- | -------------------------------- |
| 実装側の書き方    | 継承不要。`meta` と `solve` を持てば OK | `class X(AlgorithmStrategy)` と書く |
| 産業ソルバーのラップ | networkx を薄く包むクラスにそのまま適用しやすい  | 同上だが継承の縛りが増える                    |
| テスト        | フェイク実装をその場で作れる                | フェイクも継承が要る                       |

DeciTima は「手実装」「ライブラリのラッパー」「テスト用フェイク」の 3 種類が
同じ契約を満たす必要がある。継承を強制しない `Protocol` が素直。

### 2.2 `solve` の中身は「純粋」

- 入力: `OptimizationProblem` だけ。
- 出力: `CandidateSolution` だけ。
- **DB・ネットワーク・時刻・グローバル状態に触れない。**
- 乱数を使うアルゴリズム(局所探索など)は `problem.metadata["seed"]` から seed を取る。

これにより「同じ problem → 必ず同じ solution」(NFR-1 再現性)が成立し、
ユニットテストが DB なしで書ける(Phase 0-9)。

### 2.3 `solve` は検証しない

`solve` の責務は「解を作る」ことだけ。**その解が制約を満たすかの判定はしない。**
判定は Verification(Phase 0-6)が別途行う。

理由:

- 近似アルゴリズム(貪欲法など)は hard 制約を破った解を返すことがある。
  それを「解けなかった」ではなく「`status` を後で `invalid` にする候補」として
  扱いたい。
- 「解の生成」と「解の検査」を同じ関数に入れると、どちらのバグか切り分けにくい。

ただし `solve` が「解が存在しない」と判断できた場合(グラフが非連結で goal に
到達不能など)は `status="infeasible"` の `CandidateSolution` を返してよい。


### 2.4 Strategy と アルゴリズム・プリミティブ ── 2 層に分ける

DeciTima のアルゴリズムは 2 種類ある。すべてを `AlgorithmStrategy` にしようとしない。

|                 | AlgorithmStrategy(ストラテジー)                                                          | アルゴリズム・プリミティブ                                                                                    |
| --------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 役割              | **問題まるごと**を解く                                                                      | **部品・技法**。ストラテジーの内部や別の計算で使う                                                                      |
| シグネチャ           | `solve(problem: OptimizationProblem) -> CandidateSolution` に統一                     | それぞれ自然な形。`binary_search(seq, target) -> int` など                                                  |
| 例               | Dijkstra / Bellman-Ford / A* / 貪欲法 / DP / バックトラッキング / 分枝限定法 / 全探索 / Kruskal / Prim | 二分探索 / ツーポインタ / スライディングウィンドウ / 累積和 / 差分法 / ハッシュ探索 / Union-Find / Floyd-Warshall(距離行列)/ 再帰 / 分割統治 |
| 置き場所            | `app/algorithms/{graph,optimization,scheduling}/`                                  | `app/algorithms/{search,patterns}/`(および `graph/` の一部)                                            |
| `registry`      | 載る(problem_type → 候補)                                                              | **載らない**                                                                                         |
| `AlgorithmMeta` | 持つ(`produced_by` に記録)                                                              | 不要(素の関数)                                                                                         |

README 8 節「アルゴリズムは単独で実装せず、実際の問題解決機能の内部で利用する」を具体化したのがこの 2 層。プリミティブは「単独で実装するが、`solve` の中から呼ばれて初めて意味を持つ」。

例:

- `KruskalStrategy.solve()`(ストラテジー)が `union_find`(プリミティブ)を内部で使う。
- Phase 6 の Travel Planner のストラテジーが `floyd_warshall`(プリミティブ、全点対距離行列)を
  前処理に使い、その上で DP / 貪欲で訪問順を決める。
- Shift の連続時間帯の在籍人数チェックに `difference_array`(プリミティブ)を使う。

**テスト**(Phase 0-9): どちらも純粋関数なので DB 不要の高速な unit test。プリミティブは
入力のバリエーションを大量に流せる。

---

## 3. `AlgorithmMeta` ── アルゴリズムの素性

```python
# app/domain/solutions/solution.py（Phase 0-2 §6 で定義済み。ここは再掲）
class AlgorithmMeta(BaseModel):
    name: str                # "dijkstra"
    family: Literal["search", "graph", "optimization", "scheduling", "patterns"]
    implementation: str      # "handwritten" / "library:networkx" / "library:ortools"
    time_complexity: str | None = None    # "O((V+E) log V)"
    space_complexity: str | None = None
```

- `CandidateSolution.produced_by` にコピーされ、解と一緒に永続化される。
- Phase 3 のベンチマークは `name` と `implementation` で結果をグルーピングする。
- `time_complexity` は Phase 0-5 で埋める理論値。実測は Phase 3。

---

## 4. `registry` ── 問題タイプ → アルゴリズム候補

```python
# app/algorithms/registry.py
REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [
        DijkstraStrategy(),
        AStarStrategy(),
        # NetworkxShortestPath(),   ← Phase 4 で networkx 導入時に追加
    ],
    "shift_scheduling": [
        GreedyShiftStrategy(),
        BacktrackingShiftStrategy(),
        # BranchAndBoundShiftStrategy(),
        # OrToolsCpSatShiftStrategy(),   ← Phase 5 で ortools 導入時に追加
    ],
    "network_design": [           # ← Phase 4（MST）
        KruskalStrategy(),        #   内部で Union-Find（プリミティブ）を使う
        PrimStrategy(),           #   内部で優先度キューを使う
    ],
}


def get_strategies(problem_type: str) -> list[AlgorithmStrategy]:
    """problem_type に対応するアルゴリズム候補を返す。未登録なら空リスト。"""
    return REGISTRY.get(problem_type, [])
```

### 4.1 registry があると何が嬉しいか

- `SolveService` は `problem.problem_type` を registry に渡すだけ。
  どのアルゴリズムがあるか知らなくていい。
- **Phase 3 のベンチマーク**: `for s in get_strategies(pt): s.solve(problem)` を回して
  metrics を並べるだけ。
- 新アルゴリズムの追加は registry に 1 行足すだけ。既存コードに触れない
  (オープン・クローズドの原則)。

### 4.2 registry のエントリはステートレスに

`DijkstraStrategy()` をモジュールロード時に 1 回だけ生成してリストに入れている。
これは `solve` が純粋(インスタンス状態を持たない)だから安全。
`lru_cache` 的なキャッシュを持たせたくなったら、それは `solve` の外(サービス層)に置く。

---

## 5. 2 トラックを同じ契約に載せる

### 5.1 手実装トラック

```python
# app/algorithms/graph/dijkstra.py
class DijkstraStrategy:
    """優先度キューを用いた手実装のダイクストラ法。学習・再現性の説明用。"""

    meta = AlgorithmMeta(
        name="dijkstra", family="graph", implementation="handwritten",
        time_complexity="O((V+E) log V)", space_complexity="O(V)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        # problem.data は RouteData。heapq で最短経路を求める（Phase 1 で実装）
        ...
```

### 5.2 産業ソルバートラック

```python
# app/algorithms/graph/networkx_shortest.py   ← Phase 4
class NetworkxShortestPath:
    """networkx の shortest_path をラップ。実規模・実務向けの参照実装。"""

    meta = AlgorithmMeta(
        name="dijkstra", family="graph", implementation="library:networkx",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        # RouteData → nx.Graph に変換 → nx.shortest_path → RouteSolution に戻す
        ...
```

- `name` は同じ `"dijkstra"`、`implementation` だけ違う。
- Phase 3 のベンチマークで「`dijkstra / handwritten` と `dijkstra / library:networkx`」の
  実行時間・メモリを並べられる。「手で書くと何倍遅いのか」「どのサイズで逆転するのか」を
  実測で示せる ── これ自体が学習教材でありポートフォリオになる。

### 5.3 Shift Scheduler での 2 トラック

| strategy                    | implementation  | 想定される振る舞い                                       |
| --------------------------- | --------------- | ----------------------------------------------- |
| `GreedyShiftStrategy`       | handwritten     | 速いが hard 制約を破ることがある(`status=invalid` candidate) |
| `BacktrackingShiftStrategy` | handwritten     | 小規模なら最適。規模が増えると指数的に遅くなる                         |
| `OrToolsCpSatShiftStrategy` | library:ortools | 実規模でも現実的な時間。Phase 5 で導入                         |

---

## 6. アルゴリズム選択(Phase 0 では rule-based まで)

README 9 節はアルゴリズム選択を 3 段階で高度化する計画。

| Step | 方法                                  | いつ            |
| ---- | ----------------------------------- | ------------- |
| 1    | **Rule Based** ── 問題特性から決める         | Phase 4/5 で実装 |
| 2    | LLM Recommendation ── LLM に候補を挙げさせる | Phase 11      |
| 3    | Benchmark-based ── 実測データから選ぶ        | Phase 3 の蓄積後  |

### Phase 0 で設計しておくのは Step 1 の枠だけ

```python
# app/algorithms/registry.py（つづき）
def select_strategy(problem: OptimizationProblem,
                    requested: str | None = None) -> AlgorithmStrategy:
    """rule-based のアルゴリズム選択。requested 指定があれば最優先。"""
    candidates = get_strategies(problem.problem_type)
    if not candidates:
        raise NoAlgorithmError(problem.problem_type)

    # ① 明示指定があればそれを尊重する
    if requested is not None:
        for s in candidates:
            if s.meta.name == requested:
                return s
        raise NoAlgorithmError(requested)

    # ② rule: 問題特性で選ぶ（例）
    #    - route_planning でヒューリスティック用座標があれば A*、なければ Dijkstra
    #    - shift_scheduling でスロット数が小さければ Backtracking、大きければ Greedy
    return _rule_based_pick(problem, candidates)
```

- MVP では `_rule_based_pick` は素朴でよい(候補の先頭を返す等)。
- 「複数アルゴリズムで解いて比較」は Phase 3 の別ユースケース。solve の既定は 1 つ。

---

## 7. 検証 ── 2 題材を契約に当てはめる

### 7.1 Route Planner

```
OptimizationProblem(problem_type="route_planning", data=RouteData(...))
        │
        ▼  select_strategy → DijkstraStrategy
DijkstraStrategy.solve(problem):
    1. problem.data（RouteData）から隣接リストを作る
    2. ForbiddenConstraint の items にあるエッジを除外
    3. RequiredInclusionConstraint があれば「start→必須ノード→goal」に分割して解く
    4. heapq でダイクストラ
    5. RouteSolution(path_node_ids, path_edge_ids, total_weight) を組み立てる
    6. CandidateSolution(status="valid", assignments=..., metrics={"total_weight": ...},
                          produced_by=self.meta) を返す
```

**確認**: `solve` の入出力は `OptimizationProblem` と `CandidateSolution` だけ。
制約(禁止エッジ・必須経由)は `problem.constraints` から読む。契約に収まる。

### 7.2 Shift Scheduler

```
OptimizationProblem(problem_type="shift_scheduling", data=ShiftData(...),
                    objectives=[minimize labor_cost 0.7, maximize day_off_sat 0.3])
        │
        ▼  select_strategy → BacktrackingShiftStrategy
BacktrackingShiftStrategy.solve(problem):
    1. スロットを順に見て、割当可能なスタッフを試す（再帰）
    2. NumericBoundConstraint（週40h）を枝刈りに使う
    3. StaffingConstraint（必要人数）を満たしたら次のスロットへ
    4. 全スロット埋まったら、objectives の重み付き和でスコア計算
       （labor_cost と day_off_satisfaction を metrics に）
    5. 最良スコアの割当を ShiftSolution に
    6. CandidateSolution(status="valid" or "invalid", metrics=..., produced_by=self.meta)
```

**確認**: 多目的の重み付き和は `solve` の内部で `problem.objectives` を見て計算する。
soft 制約(希望休)違反は metrics の `soft_penalty` に反映し、`violations` にも積む。
これも契約に収まる。

---

## 8. まとめ

- アルゴリズムは 2 層。**問題まるごとを解く**ものは `AlgorithmStrategy` プロトコル
  (`meta` + `solve(problem) -> solution`)に従い registry に載る。**部品・技法**は
  アルゴリズム・プリミティブとして素の純粋関数で実装し、ストラテジーの内部で使う(§2.4)。
- `solve` は純粋関数。DB も時刻も乱数(seed 経由を除く)も触らない。検証もしない。
>（追記）
> 純粋関数とは「同じ入力を与えれば必ず同じ出力を返し、外部の状態を変更しない関数」
- `registry` が problem_type → 候補アルゴリズムのマップを持つ。追加は 1 行。
- 手実装と産業ソルバーは `implementation` だけ違う同一契約の別クラス。
  ベンチマーク・比較がそのまま「手実装 vs ソルバー」比較になる。
- アルゴリズム選択は Phase 0 では rule-based の枠だけ設計。LLM 推薦は Phase 11。

次章(Phase 0-5)では、これらアルゴリズムの**計算量**を整理し、
「手実装がどの規模で破綻するか」「Phase 3 で何を測るか」を設計する。
