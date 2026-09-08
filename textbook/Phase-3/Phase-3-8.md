# Phase 3-8: 分析トラック `analysis/`(pandas 導入)(作業単位 3-8)

## この章のゴール

`benchmark_runs` に貯まった実測を **pandas で集計・可視化する土台**を作る。
これは Phase 3 限定でなく、Phase 4/6/10/12/14/15 が同じ `analysis/` に足していく**多 Phase の
背骨**(ロードマップは `analysis/README.md`)。3-8 はその起点。

- `analysis/` パッケージ(`app/` から import されない。`tests/` と同じ「app の上」)
- DB との結合は **エクスポート → ファイル読み**の一方向のみ(decitima-ui の `src/db/` と同型)
- テスト可能な純粋関数中心: `loaders`(file→DataFrame)/ `benchmark_report`(DataFrame→DataFrame)
- 依存は `[dependency-groups].analysis`(`pandas` / `matplotlib`)── **runtime には入れない**

**この章で作成 / 更新するファイル**:
`analysis/{__init__,db,export,loaders,benchmark_report,plots}.py`、
`analysis/data/.gitignore`、`analysis/data/sample_benchmark_runs.jsonl`、
`analysis/notebooks/benchmark_explore.ipynb`、`analysis/README.md`。
**既存ファイルへの変更**(差分。samples に含めない):
`pyproject.toml`(`[dependency-groups].analysis` + ruff の `src` / `known-first-party` に
`analysis`)、`.gitignore`(`analysis/data/` の生成物)。

対応サンプル: `textbook/samples/analysis/**`。テストは `textbook/samples/tests/analysis/`
(`test_loaders.py` / `test_benchmark_report.py` / `test_plots.py` / `test_export.py`)。
設計は「pandas 相談」(Notes Q18)、`Phase-0-3.md` §6(分析の置き場)、`Phase-0-9.md` §5(依存)。

---

## 1. なぜコア層に入れないか

- **`app/domain/` `app/algorithms/`** は純粋レイヤー(stdlib + Pydantic のみ)。pandas を入れると
  契約が壊れ、「手実装でアルゴリズムを示す」(§21)という軸とも衝突し、純粋関数テスト
  (<1ms × 数千件)が重くなる。
- **`solve` / `verify` / `benchmark` のリクエスト経路**はデータが小さく、3-1 で入れた numpy が
  中央値・分位をカバー済み。リクエストごとに DataFrame を作るのは純粋なオーバーヘッド。
- pandas は **結果を後から読む側**(分析トラック)に置く。`analysis/ → app/` の import は可
  (`app.models` / `app.core.config`)、`app/ → analysis/` は禁止。

---

## 2. DB との縫い目 = エクスポート

DB は async 専用。分析は API とは別プロセスで単発の読み取りしかしないので、その場で
エンジンを作って dispose する:

```python
# analysis/db.py(全文は samples)
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            yield session
    finally:
        await engine.dispose()
```

### `session_scope()` と `app/core/database.py::get_db()` の違い

見た目は似ているが役割が正反対。混同しないように:

| | `app/core/database.py::get_db` | `analysis/db.py::session_scope` |
| --- | --- | --- |
| 呼ぶのは | **FastAPI**(`Depends(get_db)` → `SessionDep`) | **自分のコード**(`async with session_scope() as s:`) |
| `@asynccontextmanager` | **付けない** ── FastAPI が「`yield` を持つ依存」を `AsyncExitStack` で内部ラップする。付けると CM オブジェクトそのものが注入され `AsyncSession` が取れない | **付ける** ── FastAPI のラップが無いので自前で context manager 化 |
| エンジン | モジュール共有シングルトン(`engine`)。アプリ寿命いっぱい | その場で `create_async_engine` → `finally` で `dispose()`(スクリプト実行専用の使い捨て) |
| セッションの後始末 | `async with AsyncSessionLocal() as session:` が抜けるとき `session.close()`(未コミット rollback + 接続をプールへ返却)。**手動 `close()` は書かない** | 同上(`async with factory() as session:`) |

- **セッションは「使うたびに作って `async with` で閉じる」**。閉じる = 物理切断ではなく**接続をプールへ返す**。
- **`engine.dispose()` は使い捨てエンジンでだけ**。app の共有 `engine` をリクエストごとに dispose しては
  いけない(プール全体を毎回捨てることになる)。共有 `engine` は `app/main.py` の `lifespan` が
  アプリ終了時に 1 回だけ dispose する。`dispose()` の要否は「`@asynccontextmanager` かどうか」でなく
  「**エンジンを自分で `create_async_engine` したか / 共有を借りただけか**」で決まる。

**`async_sessionmaker` の引数(2 ファイルの差)**:

| | 意味 |
| --- | --- |
| `async_sessionmaker(engine)` と `async_sessionmaker(bind=engine)` | **同じ**。第 1 位置引数が `bind` |
| `class_=AsyncSession` | `async_sessionmaker` の**デフォルトが `AsyncSession`** なので明示は冗長(害なし)。`analysis/db.py` は省略。sync の `sessionmaker` はデフォルト `Session` なので、そちらでは意味がある |
| `autoflush=False`(app のみ) | クエリ発行前の自動 flush を止める。repo が `session.flush()` を明示で呼ぶスタイルに合わせる。`analysis/db.py` は読み取り専用なので指定しない(デフォルト `True` のまま) |
| `expire_on_commit=False`(両方) | commit 後も ORM 属性を使える(async の commit 後遅延ロードは `MissingGreenlet` になりやすい) |

**寿命の 3 層**: ① `engine`(プール) / `AsyncSessionLocal`(ファクトリ) = **アプリ寿命**(module singleton)
② プール内の物理コネクション = プールが再利用管理(session を跨ぐ) ③ `session` = **1 リクエスト**
(`get_db` の `async with` が作って閉じる)。「アプリが立ち上がっている限り session が持続」ではなく、
**session はリクエストごとに作り直され、接続だけが再利用される**。(相談ログ Q26)

```python
# analysis/export.py(要点。全文は samples)
async def dump_rows(session, table, out_path, *, user_id=None) -> int:
    """渡された session から table の行を取り、1 行 1 JSON(JSONL)で書く。純粋部分。"""

async def export_table(table, out_path, *, user_id=None) -> int:
    """session_scope() で実 DB を開く CLI ラッパ。python -m analysis.export ... で使う。"""
```

- **`dump_rows`(session を受ける純粋部分)と `export_table`(`session_scope` で実 DB を開く
  ラッパ)を分ける** ── テストは `dump_rows(db_session, ...)` を SQLite で叩けて、実 DB を
  必要としない。
- uuid / datetime は `json.dumps(..., default=str)` で文字列化。
- decitima-ui の `src/db/`(「`db:export-json` で JSON へ書き出す一方向のみ」)と同じ発想:
  notebook / テスト / CI は**エクスポート済みファイル**を読む(ライブ DB 不要・再現可能)。

---

## 3. loaders ── JSONL → DataFrame

```python
# analysis/loaders.py(要点。全文は samples)
def load_benchmark_runs(path) -> pd.DataFrame:
    """benchmark_runs の JSONL を「(run, algorithm) 1 行」の flat DataFrame に。
    payload.entries を pd.json_normalize で平し、run のメタ(id / created_at / runs)を各行へ。"""

def load_solutions(path) -> pd.DataFrame:
    """solutions の JSONL を DataFrame に(Phase 14 の布石。metrics を metric_<key> 列に展開)。"""
```

- `load_solutions` は Phase 3 では使わないが、Phase 14(LLM vs Algorithm)が `solutions` を
  読むので**この単位で入れておく**(器を拡張前提で作る)。
- payload は JSONB なので通常 dict だが、方言によっては str のことがある → `_payload()` で吸収。

---

## 4. benchmark_report ── DataFrame → DataFrame

```python
# analysis/benchmark_report.py(要点。全文は samples)
def by_algorithm(df, *, stat="median") -> pd.DataFrame:
    """アルゴリズム別に time/ops/memory/quality を集約(1 アルゴリズム 1 行 + n_entries)。"""

def input_size_curve(df, *, size_col="size", value="operation_count") -> pd.DataFrame:
    """size × algorithm の value ピボット。df は size_col 列を含む必要がある
    (benchmark を複数サイズで回して concat し、各行に問題サイズを付けたもの)。"""

def regression(baseline, current, *, metric="elapsed_ms_median") -> pd.DataFrame:
    """同一アルゴリズムの baseline → current の変化率(ratio / pct_change)。Phase 15 の CI 回帰検知用。"""
```

- **benchmark 専用モジュール**。後続 Phase は横に `analysis/shift_analysis.py`(Phase 6)、
  `analysis/experiment.py`(Phase 14)を並べる。
- `operation_count` はアルゴリズム定義の単位(3-1 / 3-2)。`by_algorithm` は並べるだけで、
  **アルゴリズム間で `_ops` を割り算する集計はしない**。

---

## 5. plots ── matplotlib

```python
# analysis/plots.py(要点。全文は samples)
def plot_comparison(report_df, *, metric="elapsed_ms_median") -> Figure: ...
def plot_input_size_curve(curve_df, *, size_col="size", log=True) -> Figure: ...
```

- **`savefig` はしない** ── ファイルに落とすか notebook に inline 表示するかは呼び出し側。
- 入力サイズ曲線は既定で対数 y 軸(全探索の指数的な伸びを 1 枚で見せる)。
- ヘッドレス(CI / `nbconvert`)は `MPLBACKEND=Agg`、テストは `matplotlib.use("Agg")` を先に。

---

## 6. sample データと notebook

- `analysis/data/sample_benchmark_runs.jsonl` ── 実際に `BenchmarkService` を回して
  `dump_rows` した 3 run 分(例題 route + `build_scaled_route_problem(6)` / `(10)`)。
  `analysis/data/.gitignore` は生成物を無視しつつこのサンプルだけ追跡する。
- `analysis/notebooks/benchmark_explore.ipynb` ── `load_benchmark_runs` → `by_algorithm` →
  `plot_*` のデモ。**サンプルデータで完結**(DB 不要)。`jupyter nbconvert --execute` で通ることを
  確認済み。

---

## 7. 既存ファイルへの変更(差分)

```toml
# pyproject.toml
[dependency-groups]
analysis = [          # ← 追加
    "pandas>=2.2",
    "matplotlib>=3.9",
]
dev = [ ... ]

[tool.ruff]
src = ["app", "tests", "analysis"]        # ← analysis を追加(first-party 解決)

[tool.ruff.lint.isort]
known-first-party = ["app", "analysis"]   # ← analysis を追加
```

`jupyter` は**ロックしない**(重い)── `uv run --with jupyter jupyter lab`。

```gitignore
# .gitignore(backend か root)
analysis/data/*
!analysis/data/.gitignore
!analysis/data/sample_benchmark_runs.jsonl
```

pyright は `include = ["app", "tests"]` のまま ── **`analysis/` は ruff のみ**
(pandas の型は pyright standard で騒がしく、`app/ai` と同じ割り切り)。`tests/analysis/` は
`tests/` 配下なので pyright 対象(0 errors を確認済み)。

---

## 8. まとめ

- pandas は**分析トラック `analysis/`**(dev グループ)に置く。コア層・リクエスト経路には入れない。
- DB との結合は「エクスポート(async)→ ファイル読み(純粋)」の一方向。
- `loaders` / `benchmark_report` は純粋関数でユニットテスト。`plots` はスモーク。notebook は
  サンプルデータで完結し `nbconvert --execute` で回る。
- `analysis/` は Phase 4/6/10/12/14/15 が育てる器。3-8 はその土台と benchmark 分析を置く。

## テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - `test_loaders.py`: **対象** = `load_benchmark_runs` / `load_solutions`。**ドライバ** =
>   テスト関数(tmp_path に JSONL を書く / 固定サンプルを読む)。**スタブ不要** ──
>   file → DataFrame の純粋関数。
> - `test_benchmark_report.py`: **対象** = `by_algorithm` / `input_size_curve` / `regression`。
>   **ドライバ** = 手組み DataFrame。**スタブ不要**。
> - `test_plots.py`: **対象** = `plot_*`。「`Figure` を返す」だけ確認(Agg バックエンド)。
>   **スタブ不要**。
> - `test_export.py`: **対象** = `dump_rows`(`export_table` ではない ── 実 DB を開かない)。
>   **ドライバ** = `db_session`(インメモリ SQLite)+ `BenchmarkRun` を数行。**スタブ不要** ──
>   SQLite が実 DB の代役。

| ファイル | ケース | 期待 |
| --- | --- | --- |
| loaders | 2 run(2 + 1 entry)| DataFrame 3 行 / `algorithm` 列 / `created_at` が datetime |
| loaders | entries 空の run | 落とす(空 DataFrame になりうる) |
| loaders | payload が str | パースして読める |
| loaders | `load_solutions` | `metric_total_weight` 列に展開 |
| loaders | 固定サンプル | 壊れていない(`dijkstra` / `brute_force` を含む) |
| report | `by_algorithm` | 中央値 + `n_entries` / `stat="max"` で最大 |
| report | `input_size_curve` | size × algorithm ピボット / `size` 列なしで `KeyError` |
| report | `regression` | `ratio == 1.2` / `pct_change == 20.0` |
| plots | `plot_*` | `matplotlib.figure.Figure` / 対数軸 |
| export | `dump_rows` を 3 行 | JSONL 3 行 / `id` は str / `payload` は dict |
| export | `user_id` フィルタ | 該当ユーザーの行だけ |

`uv run pytest tests/analysis` / `uv run ruff check analysis tests/analysis` /
`uv run --with jupyter jupyter nbconvert --execute --to notebook analysis/notebooks/benchmark_explore.ipynb`。

---

## 9. Phase 3 の完了

これで Phase 3 は完了(3-1〜3-8 の 8 章)。`Phase-3-introduction.md` の「次のフェーズ」を確認し、
「Phase 4 を開始する」で Route Planner / Network Designer の教材を生成する。Phase 4 の
Route Benchmark は `analysis/` に `route_bench.py` 相当を足す形で拡張される。
