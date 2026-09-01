# Phase 3-1: 測定コア + Benchmark スキーマ + numpy(作業単位 3-1)

## この章のゴール

ベンチマークの**測定の心臓部**を作る。「任意の callable を N 回まわして実行時間とメモリを
集計する」だけの、ドメインに依存しない関数 `measure_call`。あわせて `POST /benchmark` の
リクエスト・レスポンス型を `schemas/optimization.py` に足し、集計用の `numpy` を依存に追加する。

- `Measurement`(集計結果の dataclass)/ `measure_call[T](fn, runs) -> (T, Measurement)`
- `BenchmarkRequest` / `BenchmarkEntry` / `BenchmarkResponse` / `BenchmarkRunRead`
- `pyproject.toml` に `numpy>=2.0`

**この章で新規作成するファイル**: `app/services/measurement.py`。
**既存ファイルへの変更**: `app/schemas/optimization.py`(`Benchmark*` を追記。現行版は samples)、
`pyproject.toml`(`numpy>=2.0` を dependencies に)。

対応サンプル: `samples/app/services/measurement.py`、`samples/app/schemas/optimization.py`。
テストは `samples/tests/unit/test_measurement.py`。
設計は `Phase-0-5.md` §4(6 指標と測定場所)、`Phase-0-7.md` §3.4(スキーマ)。

---

## 1. `measure_call` ── solve の「外」で測る

`Phase-0-5.md` §4 の「測定を仕込む場所」がそのまま設計になる:

- **操作回数**は `solve()` の**中**でカウントする(Phase 1 の Dijkstra が `metrics["_ops"]` に
  heap pop 数を積んでいる)。
- **実行時間・メモリ**は `solve()` の**外**で測る ── アルゴリズムに計測コードを混ぜない。

```python
# app/services/measurement.py(要点。全文は samples)
@dataclass(frozen=True)
class Measurement:
    runs: int
    elapsed_ms_median: float
    elapsed_ms_p25: float
    elapsed_ms_p75: float
    peak_memory_kb: float          # runs 回の中で最大のピーク


def measure_call[T](fn: Callable[[], T], runs: int) -> tuple[T, Measurement]:
    """fn() を runs 回実行し、最後の戻り値と実測の集計を返す。"""
```

- **1 回目でここで戻り値を確定**する実装にしてある(`runs >= 1` は保証済み。pyright standard の
  「未束縛かもしれない」警告も同時に避けられる)。純粋関数を渡す前提なので戻り値は毎回同じ ──
  「最後の 1 つ」を代表値にする。
- 計測の 1 回分は `_timed_call` に切り出し: `tracemalloc.start()` → `perf_counter` で挟む →
  `tracemalloc.get_traced_memory()` のピーク → `tracemalloc.stop()`。
- **`tracemalloc` はプロセス全体**を追う。ベンチマークは strategy を**直列**に回すので、
  ある strategy の計測中に別の strategy の割当が混ざることはない。

### 1.1 numpy の役割(ここだけ)

```python
arr = np.array(elapsed_ms)
Measurement(
    elapsed_ms_median=float(np.median(arr)),
    elapsed_ms_p25=float(np.percentile(arr, 25)),
    elapsed_ms_p75=float(np.percentile(arr, 75)),
    ...
)
```

numpy は**アルゴリズムの計算には一切使わない**。`runs` 回の実測値(たかだか数十個)を
中央値・四分位に集計するだけ。`Phase-0-9.md` §5 の「依存は必要な Phase まで遅延」に沿って、
Phase 3 で初めて `pyproject.toml` に入る。

> **なぜ中央値か**(平均でなく)。1 回の実行時間は GC・OS スケジューラ・他プロセスで
> 大きく跳ねる。外れ値に強い中央値 + 四分位で「だいたいどのくらい」を掴む(`Phase-0-5.md` §4)。

---

## 2. Benchmark スキーマ(`schemas/optimization.py` への追記)

```python
# app/schemas/optimization.py(追記分。全文は samples)
class BenchmarkRequest(BaseModel):
    problem: OptimizationProblem
    algorithms: list[str] | None = None            # None なら problem_type の全候補
    runs: int = Field(default=3, ge=1, le=20)
    persist: bool = True
    timeout_seconds: float | None = Field(default=None, gt=0)

class BenchmarkEntry(BaseModel):
    algorithm: AlgorithmMeta
    solution_status: str
    metrics: dict[str, float]
    elapsed_ms_median: float
    elapsed_ms_p25: float
    elapsed_ms_p75: float
    peak_memory_kb: float
    operation_count: int | None = None             # metrics["_ops"]。数えていなければ None
    hard_violations: int
    soft_violations: int
    quality_ratio: float | None = None             # Phase 3-4 で埋める

class BenchmarkResponse(BaseModel):
    entries: list[BenchmarkEntry]
    benchmark_id: uuid.UUID | None = None

class BenchmarkRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    problem_type: str
    created_at: datetime
    payload: dict                                  # {"problem": ..., "entries": [...], "runs": N}
```

- `Phase-0-7.md` §3.4 のスケッチからの差分: `hard_violations` / `soft_violations` /
  `quality_ratio`(6 指標の 5・6 を entry に載せるため)、`persist` / `benchmark_id`
  (solve と同じ永続化パターン)。→ `Phase-0-7.md` に「サンプル修正」マーカーを付与。
- `algorithm` フィールドは `AlgorithmMeta`(`GET /algorithms` の `AlgorithmInfo` ではない)──
  ベンチの entry は「その solve を生成した meta そのもの」を返す。`import` を
  `from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution, ConstraintViolation`
  に増やす。

---

## 3. `pyproject.toml` への追記(既存ファイル)

```toml
# [project] の dependencies に 1 行
    "httpx>=0.28.1",
    "numpy>=2.0",          # ← 追加(Phase 3。ベンチマークの集計だけに使う)
```

写経後 `uv sync` で `uv.lock` が更新される。Docker イメージは再ビルド(`Phase-0-9.md` §4)。

---

## 4. まとめ

- `measure_call` = 「callable を N 回まわして時間・メモリを集計」。ドメインを知らない
  (テンプレート還元候補)。
- 時間・メモリは solve の外(`measure_call`)、操作回数は solve の中(`metrics["_ops"]`)。
- numpy は実測値の中央値・四分位だけに使う。Phase 3 で初導入。
- Benchmark スキーマは 4 つ。`BenchmarkEntry` が 6 指標を 1 行に集約する形。

## テスト観点(`samples/tests/unit/test_measurement.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `measure_call`(callable を N 回まわして集計する機構)
> - **ドライバ**: このテスト関数(+ pytest)。フェイクの callable(カウンタ / `time.sleep` /
>   リスト割当 / `lambda: 42`)を渡す
> - **スタブ**: **不要** ── 対象が純粋(渡す fn 以外に外部依存が無い)。fn 自体が
>   「テストダブル」だが、これはスタブでなく**入力**(ドライバ側)

| ケース | 期待 |
| --- | --- |
| カウンタ fn を `runs=5` | fn が 5 回呼ばれる / 戻り値は「最後の 1 つ」 / `m.runs == 5` |
| リスト割当 fn | `elapsed_ms_p25 <= median <= p75` / `peak_memory_kb > 0` |
| `time.sleep(0.005)` を `runs=3` | `elapsed_ms_median >= 4.0`(スリープが中央値に出る) |
| `runs=1` | `p25 == median == p75` |
| `runs=0` | `ValueError` |

`uv run pytest tests/unit/test_measurement.py` / `uvx pyright app/services/measurement.py`。

---

次章([Phase-3-2](./Phase-3-2.md))では、作業単位 3-2 ── 全探索の `BruteForceRouteStrategy` を
作って registry の 2 本目に登録し、「Dijkstra の解は本当に最適か」を裏取りする正解オラクルにする。
