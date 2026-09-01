# Phase 3 — Benchmark(実装フェーズ)導入

作業章(`Phase-3-1.md` 以降)を始める前に、この 1 本で Phase 3 の全体像を掴む。
目的 / パイプライン上の位置 / 測る 6 指標 / レイヤー / 進め方 / テスト / スコープ /
章一覧 / 実装前チェックリスト。

---

## 1. このフェーズの目的

Phase 1 で「決定論的に**計算できる**」、Phase 2 で「解が制約を満たすか**検証できる**」土台が
揃った。Phase 3 はその上に「複数のアルゴリズムを同じ問題にかけて**測って比較できる**」基盤を
作る。README §19 の Phase 順序・原則 2 がこのフェーズの定義そのもの:

> 「計算できる + 検証できる」があって初めて「測って比べる」ができる。
> **Phase 4/5 が同一問題に複数アルゴリズムを足す前に、比較基盤を用意しておく。**

Phase 3 で新しく入るもの:

| 新規 | 中身 |
| --- | --- |
| **測定コア** `services/measurement.py` | `solve()` の**外**で実行時間(中央値)とメモリ(ピーク)を測る `measure_call`。集計に numpy |
| **正解オラクル** `algorithms/optimization/brute_force.py` | 全単純パス列挙の厳密解。Dijkstra の解が最適かを裏取りし、ベンチの 2 本目の対象にもなる |
| **`BenchmarkService`** + `POST /api/v1/benchmark` | 1 問題を registry の全アルゴリズムで解いて実測を横並びにする |
| **`benchmark_runs` テーブル** + `GET /api/v1/benchmarks/{id}` | ベンチマーク 1 回分を JSONB payload で永続化(Phase 1 以来の初 ORM 作業) |
| **比較 UI**(decitima-ui) | 初の `src/features/optimization/`。比較テーブル + グループ棒 + 入力サイズ曲線。可視化は既存の手描き SVG を軸・凡例・対数軸に拡張 |

> **なぜ Brute Force を「registry に載せる Strategy」にするか**
> Phase 3 時点で route_planning に登録済みなのは Dijkstra 1 本だけで、「複数アルゴリズムの
> 比較」の相手がいない。全探索は (1) Dijkstra の最適性を小規模グラフで裏取りする**正解
> オラクル**、(2) 「賢いアルゴリズムがどれだけ効くか」を数字で見せる**2 本目のベンチ対象**、
> の 2 役を兼ねる。README §8 も「Brute Force ── Phase 3(ベンチマークの正解オラクル)、
> 以降 各問題で随時」と定義。同じ `AlgorithmStrategy` 契約なので registry に 1 行足すだけ。

---

## 2. benchmark のライフサイクル

### `POST /api/v1/benchmark`(Phase 3 新規)

```text
① routes/benchmark.py    BenchmarkRequest(problem + algorithms? + runs) 受領、認証
        ▼
② BenchmarkService.run()  ← トランザクション境界。persist なら commit
        ├ (a) RateLimiter(resource="benchmark").enforce(user_id)
        ├ (b) ProblemValidationService.validate(problem)   ★ 実際に解くので Validation を通す
        │        NG → ProblemValidationError(400) / InfeasibleProblemError(400)
        ├ (c) strategy 解決: request.algorithms でフィルタ or 全候補。空 → NoAlgorithmError
        ├ (d) 各 strategy:
        │        measure_call(strategy.solve, runs) を to_thread + wait_for で監視
        │        → (solution, Measurement{elapsed_ms_median, peak_memory_kb})
        ├ (e) SolutionVerificationService.verify(problem, solution)  ★ 計測対象外
        │        → hard / soft 違反の件数
        ├ (f) quality_ratio: 目的関数値 / この run 中の最良値
        └ (g) persist=True なら benchmark_runs に 1 行、commit
        ▼
③ routes/benchmark.py    BenchmarkResponse(entries + benchmark_id)。invalid 解も 200
```

- **Validation を走らせる** ── verify との違い。benchmark は実際に solve するので、
  「明らかに解けない問題」を測っても意味がない(`Phase-0-6.md` §2)。
- **Verification は計測の外**でかける ── 検証にかかる時間はアルゴリズムの性能ではない。
  結果の hard / soft 違反数を `BenchmarkEntry` に載せる(6 指標の「制約違反数」)。
- **invalid 解も 200** ── 「Greedy は N% の確率で hard 制約を破る」を測るのがベンチの狙い
  (`Phase-0-6.md` §4)。

### `GET /api/v1/benchmarks/{id}`

保存済みの 1 回分を所有者スコープで返すだけ(`solve` → `solutions` と同じ形)。

---

## 3. 測る 6 指標(`Phase-0-5.md` §4 で確定)と測り方

| # | 指標 | 測り方 | どこで |
| --- | --- | --- | --- |
| 1 | 実行時間 | `time.perf_counter` で 1 run ずつ、`runs` 回の**中央値**(+ 四分位) | `solve()` の外(`measure_call`) |
| 2 | 操作回数 | アルゴリズムが内部でカウンタを回し `metrics["_ops"]` に積む | `solve()` の**中**(Phase 1 の Dijkstra が種まき済み) |
| 3 | メモリ使用量 | `tracemalloc` のピーク(runs 回の最大) | `solve()` の外(`measure_call`) |
| 4 | 入力サイズ別 | サイズ n を振って 1〜3 を再測定し曲線を描く | ドライバ(テスト / UI)が n を振る |
| 5 | 解の品質 | 目的関数値。オラクル(全探索)の最良値との比 = `quality_ratio` | `BenchmarkService`(f) |
| 6 | 制約違反数 | `SolutionVerificationService` を通した `violations` の hard / soft 件数 | `BenchmarkService`(e) |

> **`_ops` はアルゴリズム定義の単位**。Dijkstra は heap pop 数、BruteForce は展開した部分パス
> 数を数える。**時間・メモリは直接比較できるが、`_ops` は「そのアルゴリズムの内部仕事量」
> としてのみ読む**(2 つのアルゴリズムの `_ops` を割り算しても意味は薄い)。誠実なベンチマーク
> 設計の要点として教材で明示する。

---

## 4. 章一覧(章 = 作業単位)

`Phase-3-M.md` = 作業単位 3-M。依存の薄い 3-1 から着手できる。

| 章 | トピック | 依存 | 主な内容 |
| --- | --- | --- | --- |
| [Phase-3-1](./Phase-3-1.md) | 測定コア + Benchmark スキーマ + numpy | ― | `services/measurement.py`(`Measurement` / `measure_call`)。`schemas/optimization.py` に `Benchmark{Request,Entry,Response,RunRead}`。`pyproject.toml` に numpy |
| [Phase-3-2](./Phase-3-2.md) | 正解オラクル = BruteForce strategy | 3-1 | `algorithms/optimization/brute_force.py`(`BruteForceRouteStrategy`)。`registry.py` に 2 本目登録。`tests/fixtures` に `build_scaled_route_problem`。「Dijkstra == BruteForce」プロパティテスト |
| [Phase-3-3](./Phase-3-3.md) | `BenchmarkService` + `POST /benchmark` + `benchmark_runs` 永続化 | 3-1, 3-2 | `services/benchmark.py`、`api/routes/benchmark.py`(POST)。`models` に `BenchmarkRun` + Alembic マイグレーション + `repositories/benchmark.py`。`config` / `routes/__init__` / `models/__init__` / `alembic/env.py` 追記 |
| [Phase-3-4](./Phase-3-4.md) | 入力サイズ別カーブ + 解の品質 + `GET /benchmarks/{id}` | 3-3 | `BenchmarkEntry.quality_ratio` の解説。入力サイズ曲線テスト。`api/routes/benchmark.py` に GET 追加、`optimization_read.py` に `get_benchmark_run` |
| [Phase-3-5](./Phase-3-5.md) | 可視化基盤の選定 + `src/features/optimization/` 骨格 + api 層の型付け | 3-3 | decitima-ui: `src/lib/api/types.ts` に手書き DTO、`src/features/optimization/{api,stores,hooks}`、Zustand + TTL キャッシュ |
| [Phase-3-6](./Phase-3-6.md) | 比較テーブル + 入力サイズ曲線チャート + ページ | 3-5 | decitima-ui: `src/components/ui/charts/` に汎用の軸付きチャート、`src/features/optimization/components/`、`src/app/(pages)/optimization/benchmark/page.tsx`、`MENU_TREE` 追記 |
| [Phase-3-7](./Phase-3-7.md) | 分析トラック `analysis/`(pandas 導入) | 3-3 | decitima-api: `analysis/{db,export,loaders,benchmark_report,plots}.py` + sample データ + notebook。`benchmark_runs` を pandas で集計・可視化。`[dependency-groups].analysis`。`app/` から切り離し。Phase 4/5/9/11/13/14 が育てる器 |

3-1〜3-4 と 3-7 が decitima-api、3-5〜3-6 が decitima-ui。3-7 は 3-3(`benchmark_runs`)にだけ
依存し、UI(3-5/3-6)とは独立。

3-3 で `benchmark.py` / model / migration / repo は最終形になる。3-4 は route に GET ハンドラを
1 本足すだけの軽い改訂(Phase 2 が Phase 1 のファイルを改訂したのと同じ「現行版を samples に」
方式。#15 のコメントアウト機構は使わない)。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1 / 2 と同じ)

1. 章(`Phase-3-*.md`)は **要点の抜粋** だけ。動くコードは `samples/`(実 `app/` `src/` ツリー
   鏡写し + 絶対 import)。
2. `samples/app/**` → `decitima-api/backend/app/**`、`samples/ui/src/**` → `decitima-ui/src/**` へ
   **ファイル単位で写経・改変**。
3. `samples/` には **Phase 3 で新規に作るファイル**と、**Phase 1 / 2 のファイルを Phase 3 が
   書き換えるもの**(現行版)。既存テンプレートファイルへの追記
   (`config.py` / `api/routes/__init__.py` / `models/__init__.py` / `alembic/env.py` /
   `registry.py` / `pyproject.toml` / `menu-tree.ts` / `lib/api/types.ts`)は各章に差分で示す。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる。

```text
textbook/Phase-3/
├── Phase-3-introduction.md   この導入
├── Phase-3-1.md 〜 3-6.md     各作業単位の解説
└── samples/
    ├── README.md             写経の対応表・overlay 検証手順(backend + ui)
    ├── app/**                → decitima-api/backend/app/**
    ├── tests/**              → decitima-api/backend/tests/**
    ├── alembic/versions/*.py → decitima-api/backend/alembic/versions/
    ├── analysis/**           → decitima-api/backend/analysis/**(3-7)
    └── ui/src/**             → decitima-ui/src/**
```

**着手前に §10 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル | 使うもの | Phase 3 で書くもの |
| --- | --- | --- |
| algorithms / measure(純粋・主戦場) | 素の pytest。DB 不要 | `measure_call`(フェイク callable)/ `BruteForceRouteStrategy`(fixture グラフ + seed プロパティ)/ 入力サイズカーブ |
| サービス層 | `db_session`(SQLite)+ `FakeRedis` | `BenchmarkService` / `BenchmarkRunRepository` |
| API | `httpx.AsyncClient` + 依存差し替え | `POST /benchmark` / `GET /benchmarks/{id}` の契約 |
| 統合 | 実 PostgreSQL(`-m integration`) | `benchmark_runs` の JSONB ラウンドトリップ |
| 分析(3-7) | 素の pytest。`db_session`(export のみ) | `loaders` / `benchmark_report`(純粋)/ `plots`(スモーク)/ `dump_rows` |
| UI | Vitest + jsdom / node env | `benchmark-store` / `api/benchmark` / `GroupedBarChart` |

`measure_call` と各 strategy、`analysis/` の `loaders` / `benchmark_report` は**純粋**なので
スタブ不要 ── これが「純粋レイヤー」設計(`Phase-0-3.md`)の帰結で、各章のテスト観点で毎回確認する。

```bash
# decitima-api/backend で
uv run pytest      # overlay end 状態で 165 passed, 3 deselected(3-7 の analysis 14 件を含む)
# decitima-ui で
npm run test       # Phase 3 の追加分は全緑
```

---

## 7. Phase 3 のスコープと非スコープ

| Phase 3 でやる | 送る先 |
| --- | --- |
| 6 指標の測定 + `POST /benchmark` + `benchmark_runs` 永続化 | ― |
| Brute Force を route_planning に登録(正解オラクル兼ベンチ対象) | shift / network_design への全探索オラクル(Phase 4 / 5、README §8「随時」) |
| 入力サイズ別カーブ(テスト + UI での掃引) | ― |
| 初の `src/features/optimization/` + 比較テーブル + グループ棒 + 入力サイズ曲線 | 問題定義入力 UI / 経路可視化(Phase 4) |
| 可視化は既存の手描き SVG を軸・凡例・対数軸に拡張 | 本格的な図ライブラリの選定(グラフ / 経路描画が要る Phase 4) |
| numpy(集計) | networkx(Phase 4)/ ortools(Phase 5) |
| ― | **`verifications` テーブル ── やはり作らない**(下記) |
| ― | **`hypothesis` ── 見送り**(手書きジェネレータで足りる) |
| ― | Benchmark-based のアルゴリズム自動選択(Phase 11。Phase 3 はデータを貯めるだけ) |
| 分析トラック `analysis/` の器 + benchmark 分析(pandas)| Phase 5/9/13 の分析モジュール、Phase 4 の Route Benchmark 拡張 |
| ― | **入力アダプタ(CSV/Excel → `OptimizationProblem`)── 別レイヤー**。runtime 依存になるので `app/adapters/`、Phase 5/7/8 で必要になったら |

**`verifications` テーブルを作らない**(`Phase-0-8.md` §4 は「`benchmark_runs` を作るとき再検討」
としていた): 検証結果は Phase 1 の `Solution.status` + `Solution.payload` に既に入り、MVP に
payload 内クエリ需要が無い(Q12)。benchmark_runs も同じく JSONB payload 中心で済む。→ 確定。

**`hypothesis` を見送る**(`Phase-0-9.md` §2 は「Phase 3 で検討」): オラクルのプロパティテストは
`_random_route_problem` 相当の seed 付き手書きジェネレータ + for ループで十分(MVP 方針)。
`hypothesis` の依存追加は、入力生成が本当に複雑になった Phase まで遅延。

---

## 8. サンプルコード(`samples/`)

| 場所 | 内容 |
| --- | --- |
| `app/services/measurement.py` | `Measurement` / `measure_call`(新規。ドメイン非依存) |
| `app/algorithms/optimization/brute_force.py` | `BruteForceRouteStrategy`(新規) |
| `app/algorithms/optimization/__init__.py` | docstring 更新(brute_force の追記) |
| `app/services/benchmark.py` | `BenchmarkService` / `BenchmarkOutcome`(新規) |
| `app/repositories/benchmark.py` | `BenchmarkRunRepository`(新規) |
| `app/api/routes/benchmark.py` | `POST /benchmark` / `GET /benchmarks/{id}`(新規) |
| `app/models/optimization.py` | `BenchmarkRun` を追加した現行版 |
| `app/services/optimization_read.py` | `get_benchmark_run` を追加した現行版 |
| `app/schemas/optimization.py` | Phase 2 の内容 + `Benchmark{Request,Entry,Response,RunRead}` |
| `alembic/versions/d4f1a9c2b8e7_add_benchmark_runs_table.py` | `benchmark_runs` のマイグレーション(新規) |
| `tests/fixtures/optimization.py` | `build_scaled_route_problem` を追加した現行版 |
| `tests/**` | measure / strategy / service / repo / api / 統合 / UI の各テスト |
| `ui/src/lib/api/types.ts` | `AsyncStatus` + benchmark DTO(現行版) |
| `ui/src/features/optimization/**` | api / stores / hooks / components / sample-problems(新規) |
| `ui/src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx` | 軸・凡例つき汎用チャート(新規) |
| `ui/src/app/(pages)/optimization/benchmark/page.tsx` | ベンチマークページ(新規) |
| `ui/src/lib/menu-tree.ts` | `Optimization` グループを追加した現行版 |
| `analysis/{__init__,db,export,loaders,benchmark_report,plots}.py` | 分析トラック(新規。3-7) |
| `analysis/{README.md,data/.gitignore,data/sample_benchmark_runs.jsonl,notebooks/benchmark_explore.ipynb}` | 使い方 / 固定サンプル / notebook(新規。3-7) |

既存ファイルへの追記(samples に含めない、各章に差分):
`app/core/config.py`(`BENCHMARK_RATE_LIMIT_*`)、`app/api/routes/__init__.py`(`benchmark_router`)、
`app/models/__init__.py`(`BenchmarkRun`)、`alembic/env.py`(`BenchmarkRun` の import)、
`app/algorithms/registry.py`(`BruteForceRouteStrategy` の import + 1 行)、
`pyproject.toml`(`numpy>=2.0` / `[dependency-groups].analysis` / ruff の `src`・`known-first-party` に `analysis`)、
`.gitignore`(`analysis/data/` の生成物)。

検証: `decitima-api/backend`(Phase 2 end 状態)に Phase 3 samples を overlay し `uv sync` →
`uv run pytest`(**165 passed, 3 deselected** ── 3-7 の analysis 14 件を含む)/
`ruff check`(analysis 含む)/ `ruff format --check` / `uvx pyright`(0 errors。`analysis/` は
ruff のみで pyright include 外)/ `alembic upgrade head` /
`jupyter nbconvert --execute analysis/notebooks/benchmark_explore.ipynb`。
decitima-ui に overlay し `npx tsc --noEmit` / `npm run test`(Phase 3 追加分 8 件 緑)/ `npm run lint`。
手順は `samples/README.md`。

---

## 9. Phase 3 の成果物

- **textbook**: この `Phase-3/` 一式(導入 + `Phase-3-1`〜`3-7` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/services/{measurement,benchmark}.py` /
  `app/algorithms/optimization/brute_force.py` / `app/repositories/benchmark.py` /
  `app/api/routes/benchmark.py` / `app/models/optimization.py`・`app/services/optimization_read.py`・
  `app/schemas/optimization.py` の現行版 / `alembic/versions/*_add_benchmark_runs_table.py` /
  `tests/**` / `config.py`・`api/routes/__init__.py`・`models/__init__.py`・`alembic/env.py`・
  `registry.py`・`pyproject.toml` への追記
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/**` /
  `src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx` /
  `src/app/(pages)/optimization/benchmark/page.tsx` / `src/lib/api/types.ts`・`src/lib/menu-tree.ts`
- **decitima-api の分析トラック**(3-7): `analysis/**` / `pyproject.toml` の `[dependency-groups].analysis`
- **Phase 0 / Phase 1 / Phase 2 教材への「以降 Phase で修正予定」/「サンプル修正」/「で確定」マーカー**
- **ルート CLAUDE.md の Notes**: Phase 3 の設計決定 + 質問ログ Q17 / Q18(pandas 相談)。
  `decitima-api/CLAUDE.md` / `decitima-ui/CLAUDE.md` にも節を追加

---

## 10. Phase 3 実装前チェックリスト

進行のルール #11。教材生成後・実装着手前に、ここで疑問を出し切る。行 `3-M` ↔ 章 `Phase-3-M`。

| # | 作る / 変えるファイル | 主なクラス・関数の責務(1 行) | テスト観点 |
| --- | --- | --- | --- |
| 3-1 | `app/services/measurement.py`(新規)、`app/schemas/optimization.py`(追記)、`pyproject.toml`(追記) | `Measurement`(集計 dataclass)/ `measure_call[T](fn, runs) -> (T, Measurement)`(fn を runs 回、perf_counter + tracemalloc、numpy で中央値・四分位)/ `BenchmarkRequest`(problem + algorithms? + runs + persist)/ `BenchmarkEntry`(algorithm + 実測 + violations + quality_ratio)/ `BenchmarkResponse` / `BenchmarkRunRead` | `measure_call` が runs 回 fn を呼ぶ / 集計形状 / sleep が中央値に出る / runs=0 で `ValueError` / runs=1 で四分位 == 中央値 |
| 3-2 | `app/algorithms/optimization/brute_force.py`(新規)、`app/algorithms/optimization/__init__.py`(改訂)、`app/algorithms/registry.py`(追記)、`tests/fixtures/optimization.py`(追記) | `BruteForceRouteStrategy.solve`(全単純パスを DFS 列挙 → 最小重み。forbidden / required 尊重。`metrics["_ops"]` = 展開した部分パス数。非連結 → `infeasible`)/ `registry` の route_planning に 2 本目 / `build_scaled_route_problem(n, seed)`(連鎖 + ランダム横エッジの連結グラフ) | fixture で Dijkstra と同じ `total_weight` / forbidden・required 尊重 / `_ops` > 0 / 非連結で `infeasible` / 再現性 / route_planning に登録 / seed 0〜49 で `dijkstra.total_weight == brute_force.total_weight` |
| 3-3 | `app/services/benchmark.py`(新規)、`app/api/routes/benchmark.py`(新規)、`app/repositories/benchmark.py`(新規)、`app/models/optimization.py`(改訂)、`app/models/__init__.py`・`alembic/env.py`・`app/core/config.py`・`app/api/routes/__init__.py`(追記)、`alembic/versions/*_add_benchmark_runs_table.py`(新規) | `BenchmarkService.run`(レート制限 → Validation → strategy 解決 → 各 strategy を measure_call → Verification で違反数 → quality_ratio → persist)/ `BenchmarkOutcome`(entries + benchmark_id)/ `BenchmarkRun`(ORM。user_id / problem_type / payload JSONB)/ `BenchmarkRunRepository.create` / `POST /benchmark`(薄いルート) | route で dijkstra + brute_force の 2 entry(実測 + 違反数 0)/ `algorithms` フィルタ / 未知アルゴリズムで `NoAlgorithmError` / 不正・不能問題で `ProblemValidationError` / `InfeasibleProblemError` / persist=True で行作成・False で id なし / repo ラウンドトリップ / POST 200・401・400 / 統合: JSONB ラウンドトリップ |
| 3-4 | `app/services/benchmark.py`(`_annotate_quality_ratio` の解説)、`app/api/routes/benchmark.py`(GET 追加)、`app/services/optimization_read.py`(改訂) | `_annotate_quality_ratio`(目的値 / run 中最良値。minimize は最小基準、maximize は最大基準。目的が metrics に無ければ None)/ `get_benchmark_run`(所有者スコープ、他人 → `NotFoundError`)/ `GET /benchmarks/{id}` | n を振ると brute_force の `_ops` が dijkstra より急伸 / 全サイズで両者の最適値一致 → `quality_ratio == 1.0` / `GET /benchmarks/{id}` ラウンドトリップ / 他人の → 404 / 無い → 404 |
| 3-5 | `src/lib/api/types.ts`(追記)、`src/features/optimization/{api/benchmark.ts,stores/benchmark-store.ts,hooks/useBenchmark.ts,sample-problems.ts}`(新規) | `runBenchmark` / `getBenchmarkRun`(`apiFetch` 経由)/ `useBenchmarkStore`(result / status / error / fetchedAt / run(TTL キャッシュ)/ reset)/ `useBenchmark`(薄いフック)/ `SAMPLE_ROUTE_PROBLEM` | store: 成功で result 保持 / 失敗で error / TTL 内は再実行しない(force で無視)/ reset で初期化 / api: POST body に runs / GET パス |
| 3-6 | `src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx`(新規)、`src/features/optimization/components/{BenchmarkTable,BenchmarkComparisonChart,InputSizeCurveChart,BenchmarkPanel}.tsx`(新規)、`src/app/(pages)/optimization/benchmark/page.tsx`(新規)、`src/lib/menu-tree.ts`(追記) | `GroupedBarChart`(軸 + 凡例 + グループ内複数棒)/ `MultiLineChart`(軸 + 凡例 + 対数軸オプション)/ `BenchmarkTable`(Algorithm × 6 指標)/ `BenchmarkPanel`(フォーム + 表 + チャート、`"use client"`)/ ページは SSG | `GroupedBarChart` が (group × series) 本の `<rect>` と系列ぶんの凡例を描く / x 軸ラベル / `@tamagui/next-theme` はモック |
| 3-7 | `analysis/{__init__,db,export,loaders,benchmark_report,plots}.py`(新規)、`analysis/{README.md,data/.gitignore,data/sample_benchmark_runs.jsonl,notebooks/benchmark_explore.ipynb}`(新規)、`pyproject.toml`(`[dependency-groups].analysis` + ruff `src`/`known-first-party`)、`.gitignore`(追記) | `session_scope`(分析専用の独立 async エンジン)/ `dump_rows`(session→JSONL の純粋部分)+ `export_table`(CLI ラッパ)/ `load_benchmark_runs` / `load_solutions`(JSONL→DataFrame)/ `by_algorithm` / `input_size_curve` / `regression`(DataFrame→DataFrame の純粋関数)/ `plot_comparison` / `plot_input_size_curve`(→ Figure) | loaders: 2 run が 3 行に平される / 空 entries は落とす / 固定サンプルが壊れていない / report: 中央値 + `n_entries` / `input_size_curve` は size 列なしで `KeyError` / `regression` の ratio・pct / plots: `Figure` を返す / `dump_rows` が JSONL を書き user_id で絞る |

各単位ごとに `uv run ruff check .`(backend)/ `npm run lint`(ui)と各テストを通してからコミット。

---

## 11. 次のフェーズ

Phase 3 完了後、「Phase 4 を開始する」で **Route Planner / Network Designer**(Bellman-Ford /
A* / 最小全域木 = `network_design` problem_type、経路可視化、`networkx` 導入)の教材を生成する。
Phase 3 で「同一問題に複数アルゴリズムをかけて実測を並べる」土台が揃うので、Phase 4 で
アルゴリズムが増えるたびに registry に足すだけでベンチに乗り、3-7 の `analysis/` に
Route Benchmark 用のモジュールを足す形で分析が拡張される(本格的な図ライブラリの選定も Phase 4)。
