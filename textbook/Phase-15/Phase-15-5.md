# Phase 15-5: 非同期処理チューニング(arqワーカー)(作業単位 15-5)

## この章のゴール

`app/worker.py::WorkerSettings`(Phase 9-8)は同時実行ジョブ数(`max_jobs`)を明示していない
── arq 既定の10のまま。README §15「非同期処理」。solve_job/simulate_job が CPU バウンドな計算を GIL 下で実行することを踏まえ、実測して適切な値を決める。

**この章で作成 / 更新するファイル**: `app/core/config.py`(改訂、`WORKER_MAX_JOBS` 追加)、`app/worker.py`(改訂、`WorkerSettings.max_jobs` 明示)、`tests/unit/test_worker.py`(改訂)。

---

## 1. 実測 ── 同時実行数を増やしてもスループットは伸びない(GIL の壁)

`solve_job` は `SolveService.solve`(Phase 1)を呼び、内部で
`asyncio.to_thread(strategy.solve, problem)` によって CPU バウンドな計算をスレッドへ逃がす。
しかし CPython(本プロジェクトが使う標準ビルド、`sys._is_gil_enabled()` で確認済み)では**GIL(Global Interpreter Lock)がスレッド間の純粋な Python 実行を直列化する** ──複数スレッドを立てても CPU バウンドな仕事は並列化されない。

`ThreadPoolExecutor` で同時実行数を振りながら、中規模の knapsack DP(cells=1,000,000、単発0.51秒)を同時実行して壁時計時間を測った:

| 同時実行数 | 壁時計時間  | ジョブあたり平均 |
| ----- | ------ | -------- |
| 1     | 0.415秒 | 0.415秒   |
| 3     | 1.534秒 | 0.511秒   |
| 5     | 2.771秒 | 0.554秒   |
| 10    | 6.448秒 | 0.645秒   |

**壁時計時間はほぼ同時実行数に比例して伸びる**(10並列で単発の約10.4倍)── スレッドを
増やしても集約スループットは改善せず、個々のジョブが GIL 競合でわずかに遅くなるだけ。
これは Phase 11-9 の実インシデント(`asyncio.wait_for` のタイムアウトは裏スレッドを
止めない ── ゾンビ化した計算が GIL を専有し後続の無関係な `/solve` まで巻き込んで連鎖する)と根が同じ問題であり、`max_jobs` を大きくするほど「同時に走るゾンビ候補」が増えることを意味する。

## 2. 結論 ── `max_jobs` を arq 既定(10)から控えめな値へ、env 変数化

真の並列化が起きない以上、`max_jobs` を増やす利点は限定的(DB I/O 待ちの重なりなど、CPU バウンドでない部分でのみ多少の overlap がある)。一方、大きすぎる `max_jobs` はGIL競合による個々のジョブの体感遅延を増やし、`SOLVE_TIMEOUT_SECONDS` ぎりぎりのジョブを押し出してタイムアウトさせるリスクを高める。VPS のコア数は環境によって異なるため、ハードコードではなく `Settings` に載せて env で調整できるようにし、既定値は控えめな **4** にした:

```python
# app/core/config.py(改訂、抜粋)
# (Phase 15-5) arq ワーカーの同時実行ジョブ数(WorkerSettings.max_jobs)。
# solve_job は CPU バウンドな solve() を GIL 下で実行するため、同時実行数を増やしても
# 真の並列化はされない(実測は `Phase-15-5.md`)。arq 既定の 10 は I/O バウンドな
# ワークロード向けの値で、この worker には過大 ── VPS の実コア数に応じて調整する前提で
# env 変数化し、既定値は控えめな 4 にする。
WORKER_MAX_JOBS: int = 4
```

```python
# app/worker.py(改訂、抜粋)
class WorkerSettings:
    ...
    # (Phase 15-5)
    # arq 既定の max_jobs=10 のまま(明示未設定)。
    # solve_job/simulate_job は CPU バウンドな計算を GIL 下で実行するため、同時実行数を
    # 増やしても真の並列化はされず、GIL 競合で個々のジョブが遅くなるだけと実測で判明。
    # VPS の実コア数に応じて調整できるよう env 変数化し、既定値は控えめな 4 にする。
    max_jobs = settings.WORKER_MAX_JOBS
```

> **投機的な最適化をしない**: `multiprocessing`ベースのワーカーへの作り替え(真の並列化を得る唯一の方法)は、この章のスコープ(既存 arq ワーカーの設定チューニング)を大きく超える実装変更であり、実在の消費者(具体的なスループット不足の報告)が無い限り見送る(進行のルール #17)。

---

## まとめ

- `solve_job`/`simulate_job` は CPU バウンドな計算を GIL 下で実行するため、arq の
  `max_jobs` を増やしても真の並列化はされないことを実測で確認した(10並列で単発の
  約10.4倍の壁時計時間 ── ほぼ直列と同じ)。
- `max_jobs` を `Settings.WORKER_MAX_JOBS`(既定4)として env 変数化し、arq 既定の
  10 から控えめな値に変更した。大きすぎる同時実行数は Phase 11-9 のゾンビ化リスクを増幅するため。

## テスト観点(`tests/unit/test_worker.py`)

> **対象**: `WorkerSettings.max_jobs`
> **ドライバ**: このテスト関数
> **スタブ不要** ── 設定値の配線を確認するだけの純粋な参照チェック

| ケース                       | 期待                               |
| ------------------------- | -------------------------------- |
| `WorkerSettings.max_jobs` | `settings.WORKER_MAX_JOBS` と一致する |

```bash
uv run pytest tests/unit/test_worker.py -v
```

---

次章([Phase-15-6](./Phase-15-6.md))では `SolutionExplanationService` に Redis キャッシュを
導入する ── Phase 15 で唯一の新規キャッシュ層。
