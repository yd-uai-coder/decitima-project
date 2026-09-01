# Phase 3-2: 正解オラクル = BruteForce strategy(作業単位 3-2)

## この章のゴール

start→goal の**全単純パスを列挙**して最小重みを選ぶ `BruteForceRouteStrategy` を作る。役割は 2 つ:

1. **正解オラクル** ── Dijkstra が本当に最適解を返しているかを、小さなグラフで裏取りする。
2. **ベンチの 2 本目** ── Dijkstra と実測を並べて「賢いアルゴリズムがどれだけ効くか」を見せる。

- `BruteForceRouteStrategy`(`AlgorithmStrategy` 契約。route_planning 専用)
- `registry.py` の route_planning リストに 2 本目として登録
- `build_scaled_route_problem(n, seed)` fixture(オラクルのプロパティテスト / 入力サイズカーブ用)

**この章で新規作成するファイル**: `app/algorithms/optimization/brute_force.py`。
**既存ファイルへの変更**: `app/algorithms/optimization/__init__.py`(docstring)、
`app/algorithms/registry.py`(import + route_planning に 1 行)、
`tests/fixtures/optimization.py`(`build_scaled_route_problem` を追記。現行版は samples)。

対応サンプル: `samples/app/algorithms/optimization/brute_force.py`。
テストは `samples/tests/unit/test_brute_force_strategy.py`。
設計は README §8(Brute Force = Phase 3 の正解オラクル)、`Phase-0-4.md` §2.4(2 層)。

---

## 1. `BruteForceRouteStrategy`

```python
# app/algorithms/optimization/brute_force.py(要点。全文は samples)
class BruteForceRouteStrategy:
    meta = AlgorithmMeta(
        name="brute_force", family="optimization", implementation="handwritten",
        time_complexity="O(V!)", space_complexity="O(V)",
    )

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        # 1. 隣接リスト構築(forbidden エッジを除外)── dijkstra.build_adjacency を再利用
        # 2. DFS スタックで start→goal の全単純パスを列挙
        #    スタック要素: (node, nodes, edges, visited: frozenset, weight)
        #    goal 到達時: required を全部通っていて weight が最良なら候補更新
        # 3. best が無ければ status="infeasible"、あれば status="valid"
        #    metrics = {"total_weight": best, "_ops": <展開した部分パス数>}
```

- **`family="optimization"`** ── 「全探索」は最適化の技法であって、問題がグラフでも family は
  技法で決める(README §8 も Optimization に分類)。ファイルも `algorithms/optimization/` 配下。
- **`metrics["_ops"]` = DFS スタックの pop 回数**(= 展開した部分パスの数)。Dijkstra の `_ops`
  (heap pop 数)とは**数え方が違う**。両者を並べたときは「内部仕事量」としてだけ読む。
- **枝刈りをあえて入れない** ── 純粋な全探索にすることで「サイズが増えると指数的に爆発する」
  が入力サイズカーブにそのまま出る(3-4)。正しさは「全部見たから最良」で自明。
- `data` が `RouteData` でなければ `TypeError`(registry 経由なら必ず `RouteData`。契約の確認)。

> **Dijkstra と統合しないのはなぜか**(同じ `graph/` に置かない理由も同じ)
> `DijkstraStrategy` と `BruteForceRouteStrategy` は**同じ問題を解く別のアルゴリズム**。
> 変更理由(片方はヒープ最適化、片方は列挙の網羅性)も消費者(前者は主に `SolveService`、
> 後者は主に `BenchmarkService` とオラクルテスト)も別。共有するのは `build_adjacency` だけで、
> それは既に `dijkstra.py` にある関数を import して使う(グラフプリミティブの整理は Phase 4)。

---

## 2. registry への登録(既存ファイルへの追記)

```python
# app/algorithms/registry.py
from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.algorithms.optimization.brute_force import BruteForceRouteStrategy  # ← 追加(Phase 3)

REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [
        DijkstraStrategy(),
        BruteForceRouteStrategy(),   # ← 追加。正解オラクル兼ベンチ対象
        # AStarStrategy(),        ← Phase 4
    ],
    ...
}
```

- **`find_strategy` は `candidates[0]` を返す**ので、`requested` 指定なしの `solve` は今まで
  どおり Dijkstra。全探索を明示的に使いたいときは `?algorithm=brute_force`。
- これは Phase 1-2 の `# ← コメントを外す` パターンとは違い、この章で作るファイルなので
  最初から実行行として足す(#15)。

---

## 3. `build_scaled_route_problem` fixture(既存ファイルへの追記)

```python
# tests/fixtures/optimization.py(追記。全文は samples)
def build_scaled_route_problem(n: int, *, seed: int = 0) -> OptimizationProblem:
    """seed 固定のランダム連結グラフ。連鎖 n0-n1-...-n(n-1) を必ず張って連結性を保証し、
    ランダムな横エッジを n//2 本足す。start = n0, goal = n(n-1)。"""
```

- **連鎖を必ず張る** ので、`start` から `goal` へ必ず 1 本は道がある ── オラクルの
  「Dijkstra も全探索も解を返す」が保証される。
- `n` を振れば入力サイズカーブ(3-4)、`seed` を振ればオラクルのプロパティテスト。
- `random.Random(seed)` を使う ── モジュールグローバルの `random` を汚さず、`seed` で完全再現。

---

## 4. まとめ

- `BruteForceRouteStrategy` = 全単純パス列挙の厳密解。オラクル兼ベンチ対象。
- registry の route_planning に 2 本目。`solve` の既定は Dijkstra のまま。
- `_ops` の数え方はアルゴリズムごとに違う(Dijkstra=heap pop、BruteForce=部分パス展開)。
- `build_scaled_route_problem` が seed / サイズを振れる連結グラフを供給する。

## テスト観点(`samples/tests/unit/test_brute_force_strategy.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `BruteForceRouteStrategy.solve`(+ registry 登録)
> - **ドライバ**: このテスト関数。`build_route_problem` / `build_scaled_route_problem` が入力生成
> - **スタブ**: **不要** ── `solve` は純粋(問題を受けて解を返すだけ、外部依存なし)。
>   `Phase-0-3.md` の純粋レイヤー設計の帰結

| ケース | 期待 |
| --- | --- |
| 制約なし | `total_weight == 5.0`(Dijkstra と同じ最短) |
| `e_bd` 禁止 + `C` 必須 | path `A-B-C-E` / `total_weight == 9.0` / `e_bd` を使わない |
| `e_ce` と `e_de` 禁止 | `status == "infeasible"` |
| 任意の有効グラフ | `metrics["_ops"] > 0` |
| 同じ問題を 2 回 solve | `model_dump()` が完全一致(再現性) |
| `get_strategies("route_planning")` | `"brute_force"` が含まれる |
| **プロパティ**: seed 0〜49 の `build_scaled_route_problem(6, seed)` | `dijkstra.total_weight == brute_force.total_weight`(オラクル一致) |

`uv run pytest tests/unit/test_brute_force_strategy.py` /
`uvx pyright app/algorithms/optimization/brute_force.py`。

---

次章([Phase-3-3](./Phase-3-3.md))では、作業単位 3-3 ── `BenchmarkService` と
`POST /api/v1/benchmark`、そして `benchmark_runs` テーブル(Phase 1 以来の初 ORM 作業)を作る。
