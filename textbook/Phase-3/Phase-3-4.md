# Phase 3-4: 入力サイズ別カーブ + 解の品質 + GET /benchmarks/{id}(作業単位 3-4)

## この章のゴール

6 指標の残り 2 つを仕上げる ── **入力サイズ別カーブ**(指標 4)と**解の品質**(指標 5)。
あわせて `GET /api/v1/benchmarks/{id}` で保存済みのベンチ実行を読めるようにする。

- `BenchmarkEntry.quality_ratio` を `BenchmarkService` が埋める仕組み(`_annotate_quality_ratio`)
- 入力サイズを振って操作回数の伸びを見るテスト
- `GET /api/v1/benchmarks/{id}`(所有者スコープ)

**この章で新規作成するファイル**: なし(テストのみ)。
**既存ファイルへの変更**:
`app/api/routes/benchmark.py`(GET ハンドラを 1 本追加)、
`app/services/optimization_read.py`(`get_benchmark_run` ── 3-3 の現行版に含まれている)、
`app/services/benchmark.py`(`_annotate_quality_ratio` ── 3-3 の現行版に含まれている。この章は解説)。
**テスト**: `samples/tests/unit/test_benchmark_curve.py`(新規)、
`samples/tests/api/test_benchmark_api.py`(GET のケースを追加 ── 3-3 の現行版に含まれている)。

設計は `Phase-0-5.md` §4(指標 4・5)、`Phase-0-7.md` §2(GET エンドポイント)。

---

## 1. 解の品質 ── `quality_ratio`

「速いけど最適でない解」と「遅いけど最適な解」を同じ土俵で比べるための指標。
各 entry の目的関数値を、**その run 中の最良値**で割る。

```python
# app/services/benchmark.py の末尾(要点。全文は samples)
def _annotate_quality_ratio(problem, entries) -> None:
    objective = problem.objectives[0]            # 第 1 目的(route なら total_weight を minimize)
    target = objective.target
    values = [e.metrics[target] for e in entries
              if e.solution_status == "valid" and target in e.metrics]
    if not values:
        return
    best = min(values) if objective.sense == "minimize" else max(values)
    for e in entries:
        if e.solution_status == "valid" and target in e.metrics:
            e.quality_ratio = e.metrics[target] / best
```

- **基準は「オラクルの値」ではなく「run 中の最良値」** ── 全探索(オラクル)が entries に
  含まれていれば実質オラクル比になるし、含まれていなくても「一番良かったやつとの比」として
  意味を持つ。
- minimize なら `1.0` が最良、`1.2` は「最良より 20% 悪い」。maximize は最大値が基準。
- `target` が `metrics` に無い / valid な解が 1 つも無い entry は `None` のまま。
- `BenchmarkEntry` は通常の `BaseModel`(frozen でない)なので、構築後に `e.quality_ratio = ...`
  で代入してよい。

---

## 2. 入力サイズ別カーブ

「サイズ n を振って操作回数を再測定し、曲線を描く」(`Phase-0-5.md` §4 指標 4)。
Phase 3 の `POST /benchmark` は**1 問題ぶん**を測る ── サイズを振るのは**ドライバ**の仕事
(テスト、あるいは UI が n を変えて何度も叩く)。

テストは `build_scaled_route_problem` でサイズを振り、strategy を直に回して `_ops` の伸びを見る:

```python
# tests/unit/test_benchmark_curve.py(要点。全文は samples)
def test_brute_force_ops_grow_much_faster_than_dijkstra() -> None:
    sizes = [4, 6, 8, 10]
    dijkstra_ops = [_DIJKSTRA.solve(build_scaled_route_problem(n, seed=1)).metrics["_ops"] for n in sizes]
    brute_ops    = [_BRUTE.solve(build_scaled_route_problem(n, seed=1)).metrics["_ops"] for n in sizes]
    assert brute_ops[-1] > dijkstra_ops[-1]
    assert brute_ops[-1] / brute_ops[0] > dijkstra_ops[-1] / max(dijkstra_ops[0], 1.0)
```

- `BenchmarkService` を通さず strategy を直に回す ── カーブの本質は「サイズ vs 操作回数」
  だけなので、DB もレート制限も要らない。
- **`_ops` の絶対値は比べない**(数え方が違う)。「同じアルゴリズムの `_ops` がサイズwith
  どう伸びるか」の**傾き**を比べる。全探索は指数的、Dijkstra は多項式的。
- UI 側(3-6)の `InputSizeCurveChart` は対数 y 軸でこの差を 1 枚に描く。

---

## 3. `GET /api/v1/benchmarks/{id}`

```python
# app/services/optimization_read.py に追加(全文は samples)
async def get_benchmark_run(self, benchmark_id, *, user_id) -> BenchmarkRun:
    row = await self._session.get(BenchmarkRun, benchmark_id)
    if row is None or row.user_id != user_id:
        raise NotFoundError(f"benchmark run {benchmark_id} not found")
    return row
```

```python
# app/api/routes/benchmark.py に追加
@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkRunRead)
async def get_benchmark_run(benchmark_id: uuid.UUID, session: SessionDep, current_user: CurrentUserDep):
    row = await OptimizationReadService(session).get_benchmark_run(benchmark_id, user_id=current_user.id)
    return BenchmarkRunRead.model_validate(row)
```

- `get_problem` と同型 ── 他ユーザーの行は `NotFoundError`(404)。「存在しない」扱いで
  所有者以外に情報を漏らさない(Phase 1-7 の owner スコープ方針)。
- パスは `POST /benchmark`(動詞)+ `GET /benchmarks/{id}`(リソース)で `Phase-0-7.md` §2 に
  合わせる。ルーターは prefix なしで両方を明示パスで持つ(`solutions.py` と同じ流儀)。

---

## 4. まとめ

- `quality_ratio` = 目的値 / run 中の最良値。速さと最適性を同じ土俵に乗せる。
- 入力サイズカーブはドライバ(テスト / UI)がサイズを振って作る。`_ops` は傾きで比べる。
- `GET /benchmarks/{id}` は `get_problem` と同型の所有者スコープ読み出し。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - `test_benchmark_curve.py`: **対象** = `DijkstraStrategy` / `BruteForceRouteStrategy`(純粋)。
>   **ドライバ** = テスト関数 + `build_scaled_route_problem`。**スタブ不要**。
> - `test_benchmark_api.py`(GET 分): **対象** = `GET /benchmarks/{id}` + `OptimizationReadService`。
>   **ドライバ** = `httpx.AsyncClient`。**スタブ** = `get_db` → SQLite。
> - `test_benchmark_service.py`(quality_ratio 分): 対象 = `_annotate_quality_ratio` 経由の
>   `BenchmarkService.run`。スタブ = `FakeRedis` のみ。

| ケース | 期待 |
| --- | --- |
| n ∈ [4,6,8,10] で `_ops` を掃引 | 最大サイズで brute_force が dijkstra を大きく上回る / brute の伸び率 > dijkstra の伸び率 |
| 全サイズで両者の解 | `total_weight` が一致(オラクル)→ `quality_ratio == 1.0` |
| 制約なし route を benchmark | `all(e.quality_ratio == 1.0)` |
| 目的が metrics に無い | `quality_ratio is None` |
| `POST` → `GET /benchmarks/{id}` | 200 / `payload["runs"]` が一致 |
| 他ユーザーの id を `GET` | 404 |
| 存在しない id を `GET` | 404 |

`uv run pytest tests/unit/test_benchmark_curve.py tests/api/test_benchmark_api.py`。

---

次章([Phase-3-5](./Phase-3-5.md))から decitima-ui。作業単位 3-5 ── 初の
`src/features/optimization/` を立ち上げ、`apiFetch` 経由の benchmark 呼び出しと Zustand ストアを作る。
