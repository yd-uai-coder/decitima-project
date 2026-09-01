# Phase 0-3: アーキテクチャ設計

## この章のゴール

Phase 0-2 で作った共通スキーマを中心に据えて、`decitima-api` のレイヤー構成と
データフローを設計する。

- システム全体の構成(UI / API / LLM Service / DB)
- `decitima-api` に増やす新レイヤー ── `domain/` と `algorithms/`
- solve リクエストが通る道筋(ライフサイクル)
- 2 トラック(手実装 / 産業ソルバー)をアーキテクチャ上どこで吸収するか
- 既存テンプレート資産の再利用方針
- `decitima-ui` 側の将来構成の概観

---

## 1. システム全体の構成

README 16 節の構成をベースにする。

```
┌───────────────────────────────────────────────┐
│              decitima-ui (Next.js)             │
│  Dashboard / Problem Input / AI Interpretation │
│  Visualization / Simulation / Benchmark        │
└───────────────────────┬───────────────────────┘
                        │ REST API (JSON)
                        ▼
┌───────────────────────────────────────────────┐
│              decitima-api (FastAPI)            │
│                                               │
│  api/routes  ──▶  services  ──┬──▶ domain     │
│                               ├──▶ algorithms │
│                               └──▶ repositories ──▶ models
└───────────────────────┬───────────────────────┘
                        ▼
                ┌───────────────┐   ┌───────────┐
                │  PostgreSQL   │   │   Redis   │
                └───────────────┘   └───────────┘

  ┌─────────────────────────────────┐
  │  LLM Service (app/ai/)           │  ← Phase 10〜。solve の本流には入らない
  │  意図抽出 / 制約抽出 / 説明生成   │     出力は OptimizationProblem
  └─────────────────────────────────┘
```

ポイント:

- **UI は API としか話さない**。DB にも LLM にも直接触れない。
- **LLM Service は本流の外**。Phase 0〜9 では休眠。Phase 10 で「自然言語 →
  `OptimizationProblem`」を担うが、それでも Algorithm Engine とは直接つながらず、
  スキーマを介する(Phase 0-2 の疎結合方針)。

---

## 2. `decitima-api` のレイヤー構成

### 2.1 既存テンプレートのレイヤー

`decitima-api/CLAUDE.md` に記載のとおり、テンプレートは次の 4 層。

```
routes  →  services  →  repositories  →  models
                ↓
              ai/  (LangGraph)
```

- **routes**: リクエスト/レスポンスの変換のみ。ビジネスロジックを持たない。
- **services**: ユースケース単位のロジック。トランザクション境界。`commit()` はここだけ。
- **repositories**: 永続化のみ。`flush()` はするが `commit()` はしない。
- **models**: SQLAlchemy ORM 定義のみ。

### 2.2 DeciTima が足す 2 層

```
routes  →  services  ──┬──▶  domain/       ← 純粋。問題・制約・目的・解の「型と意味」
                       ├──▶  algorithms/   ← 純粋関数。決定論的な計算
                       └──▶  repositories  →  models
```

| 新レイヤー | 責務 | 依存してよいもの | 依存してはいけないもの |
| --- | --- | --- | --- |
| `app/domain/` | `OptimizationProblem` 等のスキーマ、制約チェッカー、目的関数の評価、解の表現 | 標準ライブラリ、Pydantic | services / repositories / DB / HTTP / Redis / ai |
| `app/algorithms/` | 決定論的な計算。**問題まるごとを解くストラテジー**(`OptimizationProblem` → `CandidateSolution`)と、**部品となるプリミティブ**(素の純粋関数。二分探索・Union-Find 等)の 2 層(Phase 0-4 §2.4) | `app/domain/`、標準ライブラリ、(2 トラックの実務側は)networkx / ortools 等 | services / repositories / DB / HTTP / Redis / ai |

**この 2 層は「純粋」**── 副作用(I/O、DB、時刻、乱数)を持たない。これが
再現性(NFR-1)とテスタビリティを生む。乱数が必要なアルゴリズムは seed を
引数で受け取る。

### 2.3 ディレクトリ構成(README 17 節に沿う)

**Pydantic モデル(型)は `problems/` と `solutions/` に置く。** `constraints/` と
`objectives/` は `Constraint.kind` / `Objective` で横断的にディスパッチする**ロジック**
(チェッカー関数・重み付き和の評価器、Phase 2〜5)の置き場。問題タイプ固有の
セマンティック検査は `problems/` 側に同居してよい。ファイル単位の分割は Phase 0-2 §2.5。

> **[以降 Phase で修正予定 ── Phase 2-3 / Phase 5]** 当初この置き場のロジックは「Phase 1〜2」
> としていた。実際は `constraints/` のチェッカーは **Phase 2-3 で実装済み**、`objectives/` の
> 重み付き和の評価器は **Phase 5**(初の多目的ストラテジー実装時)。Phase 1 の Validation /
> Verification は route 限定の最小実装のみ。詳細は `Phase-1-introduction.md` §7 /
> `Phase-1-7.md` §5 / `Phase-2-3.md`、`Phase-0-2.md` §2.5 の同マーカー。

```
app/
├── domain/
│   ├── problems/       型: Objective / ConstraintBase(+サブタイプ) / GenericConstraint /
│   │                       AnyConstraint / OptimizationProblem / ProblemData ユニオン /
│   │                       RouteData / ShiftData
│   │                   （problem.py + route_planner.py + shift_scheduler.py + __init__.py）
│   │                   + problem_type ごとのセマンティック検査関数（Phase 2）
│   ├── solutions/      型: CandidateSolution / SolutionData ユニオン / AlgorithmMeta /
│   │                       ConstraintViolation / RouteSolution / ShiftSolution
│   ├── constraints/    kind ごとのチェッカー関数（Phase 2）。型は problems/ 側
│   └── objectives/     重み付き和の評価（Phase 5。当初 Phase 1 ── 上のマーカー）。型は problems/ 側
│
├── algorithms/
│   ├── base.py         AlgorithmStrategy プロトコル
│   ├── search/         binary_search(プリミティブ) / bfs / dfs
│   ├── graph/          dijkstra / bellman_ford / a_star(Strategy)、
│   │                   floyd_warshall / union_find(プリミティブ)、kruskal / prim(Strategy, MST)、
│   │                   （実務: networkx アダプタ）
│   ├── optimization/   greedy / dynamic_programming / backtracking / branch_and_bound / brute_force
│   ├── scheduling/     シフト割当ソルバー（実務: ortools CP-SAT アダプタ）
│   ├── patterns/       two_pointers / sliding_window / prefix_sum / difference_array /
│   │                   hash_search / recursion 等のプリミティブ
│   └── registry.py     problem_type → 候補 AlgorithmStrategy のマップ
│
├── services/
│   ├── solve.py            SolveService（本流のユースケース）
│   ├── validation.py       ProblemValidationService（問題定義の妥当性）
│   ├── verification.py     SolutionVerificationService（解の制約充足）
│   └── benchmark.py        （Phase 3）
│
├── schemas/            API のリクエスト/レスポンス（domain とは別。API 契約）
├── models/             ORM（problems / solutions / verifications / benchmark_runs）
├── repositories/       上記モデルの CRUD
└── ...（既存: core / api / infrastructure / ai）
```

### 2.4 `domain/` と `schemas/` を分ける理由

一見どちらも Pydantic モデルで重複しそうに見えるが、役割が違う。

| | `app/domain/` | `app/schemas/` |
| --- | --- | --- |
| 何のためか | システム内部の共通言語。計算・検証で使う | HTTP の境界。API のリクエスト/レスポンス契約 |
| 変わる理由 | ドメインの理解が深まったとき | API のバージョニング、クライアントの都合 |
| 例 | `OptimizationProblem`, `Constraint` | `SolveRequest`, `SolveResponse`, `SolutionRead` |

MVP では両者がほぼ一致するかもしれない。それでも層を分けておくと、
将来 API の後方互換を保ちながらドメインモデルを進化させられる。
`schemas/` が `domain/` を import して薄くラップする形が基本。

---

## 3. solve リクエストのライフサイクル

`POST /api/v1/solve` が来てからレスポンスを返すまで。

```
① routes/solve.py
   SolveRequest（JSON）を受け取る。認証済みユーザーを取得（既存 CurrentUserDep）
        │
        ▼
② SolveService.solve()  ← トランザクション境界。ここで commit
        │
        ├─ (a) RateLimiter(resource="solve").enforce(user_id)   ← 既存 RateLimiter 再利用
        │
        ├─ (b) domain: SolveRequest → OptimizationProblem に変換
        │
        ├─ (c) ProblemValidationService.validate(problem)
        │        NG なら ProblemValidationError（→ 400）でここで終了
        │
        ├─ (d) registry から problem.problem_type に対応する AlgorithmStrategy を選ぶ
        │        （指定があればそれ、なければ既定の 1 つ。複数指定は Phase 3）
        │
        ├─ (e) strategy.solve(problem) → CandidateSolution   ← 純粋な計算。副作用なし
        │        タイムアウトはここで監視（Phase 0-5）
        │
        ├─ (f) SolutionVerificationService.verify(problem, solution)
        │        hard 違反があれば solution.status = "invalid"
        │        solution.violations を埋める
        │
        ├─ (g) repositories: problem と solution と verification を永続化
        │
        └─ (h) commit
        │
        ▼
③ routes/solve.py
   CandidateSolution → SolveResponse（schema）に詰めて返す
```

- **例外はルートで捕まえない**。`ProblemValidationError`（`BadRequestError` 派生）や
  `InfeasibleProblemError` はそのまま伝播し、既存の `register_error_handlers` が
  JSON に変換する(Phase 0-6)。
- **(e) の計算は純粋**。DB もネットワークも触らない。だからこそ同じ入力で同じ結果になり、
  ユニットテストが速い。

---

## 4. 2 トラックをアーキテクチャ上どこで吸収するか

「手実装トラック」と「産業ソルバートラック」は、`app/algorithms/` の中で
**同じ `AlgorithmStrategy` インターフェースを実装する別クラス**として並ぶ。

```
app/algorithms/graph/
├── dijkstra.py           class DijkstraStrategy       implementation="handwritten"
├── a_star.py             class AStarStrategy          implementation="handwritten"
└── networkx_shortest.py  class NetworkxShortestPath   implementation="library:networkx"

registry.py:
REGISTRY["route_planning"] = [DijkstraStrategy(), AStarStrategy(), NetworkxShortestPath()]
```

- 呼び出し側(`SolveService`)は `AlgorithmStrategy` としてしか見ない。
  手実装かライブラリかを気にしない。
- `AlgorithmMeta.implementation` にどちらかが記録される。
- Phase 3 のベンチマークは「同じ problem を REGISTRY の全 strategy で解いて metrics を比較」
  するだけ。手実装 vs ライブラリの比較が自動的に成立する。
- **依存の遅延**: `networkx` / `ortools` は必要な Phase まで `pyproject.toml` に足さない。
  Phase 0 時点では `app/algorithms/` に手実装トラックの置き場所(空パッケージ)だけ用意する。

---

## 5. 既存テンプレート資産の再利用

`decitima-api` はテンプレート由来の資産を持っている。DeciTima 用に作り直さず活かす。

| 資産 | 場所 | DeciTima での使い方 |
| --- | --- | --- |
| `AppError` 階層 | `app/core/errors.py` | `ProblemValidationError(BadRequestError)` 等を派生。エラー処理のボイラープレート不要 |
| `register_error_handlers` | `app/api/error_handlers.py` | `AppError` → JSON 変換を一括。ルートに try/except を書かない |
| `CRUDRepository[ModelType]` | `app/repositories/base.py` | `problems` / `solutions` テーブルのリポジトリはこれを継承 |
| `RateLimiter` | `app/services/rate_limit.py` | `resource="solve"` で solve 実行にレート制限。ウィンドウ設定だけ渡す |
| `CurrentUserDep` / `SessionDep` | `app/api/deps.py` | solve ルートの認証と DB セッション注入 |
| conftest の `db_session` | `tests/conftest.py` | サービス層テストのインメモリ SQLite セッション |
| 3 段 Dockerfile / docker-compose | `decitima-api/` | 変更不要。そのまま使う |
| LangGraph の構造化出力パターン | `app/ai/graph/nodes.py` | Phase 10 で「自然言語 → OptimizationProblem」に流用 |

**テンプレートへの還元(ルート CLAUDE.md「コード提示・コメント規約」)**:
`RateLimiter` の `resource` 汎用化など、DeciTima 非依存の改善が出たら
`fastapi-langchain-template` への反映を都度提案する。`domain/` `algorithms/` は
DeciTima 固有なので還元対象外。

---

## 6. `decitima-ui` の将来構成(概観)

Phase 0 では UI のコードは書かない。方針だけ確認する。

### 6.1 feature 分割の起点

`decitima-ui/CLAUDE.md` の指針:

> アプリ固有のドメインロジックが増えたら `src/components/` に足し続けず、
> `src/features/<name>/{components,hooks,api,stores}` に分割する。

DeciTima の最初の feature は Phase 3(ベンチマーク UI)か Phase 4(Route Planner)で生まれる。
そのとき次を作る。

```
src/features/optimization/
├── api/          apiFetch を使った solve / problems / solutions の呼び出し
├── stores/       Zustand: { data, status, error, fetchedAt } + TTL キャッシュ
├── hooks/        useSolve, useProblem など
└── components/   問題定義フォーム、結果表示、比較テーブル
```

`src/components/` は引き続き機能非依存のデザインシステム層。DeciTima 固有の語を
持ち込まない(ルート CLAUDE.md のネーミング方針)。

> **[Phase 3 で確定 ── UI feature + 分析トラックの 2 つが立ち上がる]** Phase 3-5/3-6 で
> `decitima-ui` の初の `src/features/optimization/`(benchmark 比較 UI)が生まれる。あわせて
> **`decitima-api` に `analysis/` を新設**(Phase 3-7)── `benchmark_runs` を pandas で集計・
> 可視化するオフラインの分析トラック。`app/` から import されず、依存は `[dependency-groups].analysis`
> (runtime に入れない)。UI(結果を見せる)と分析(結果を掘る)で置き場が分かれる。
> `analysis/` は Phase 4/5/9/11/13/14 が育てる器。詳細 `Phase-3-7.md`。

### 6.2 API との型の一致

`decitima-api` の `schemas/` が返す JSON と `decitima-ui` の型を手で合わせる。
MVP では OpenAPI からの自動生成は導入せず、`src/lib/api/types.ts` に手書きで
`OptimizationProblem` / `CandidateSolution` の TS 型を置く(Phase 0-7 で API を確定させてから)。

### 6.3 可視化ライブラリ

現状 UI には簡易チャート 3 種しかない。経路図・ガントチャート・ネットワーク図には
新しい依存が要る。**選定は Phase 3 / Phase 4 で行う**。Phase 0 では
「MVP で必要なのは経路の可視化(Phase 4)とシフト表(Phase 5)。両方とも
まずは SVG 手描き or 軽量ライブラリで足りるか検討する」とだけ記録しておく。

> **[Phase 3 で確定 ── 一部 Phase 4 送り]** Phase 3 のベンチマーク比較チャート(グループ棒 /
> 多系列ライン / 対数軸)は既存の手描き SVG(`BarChart` / `LineChart` のパターン + 
> `theme-gradients.ts` + `useHasMounted`)を `src/components/ui/charts/` に
> `GroupedBarChart` / `MultiLineChart` として拡張して対応。**新しい依存は足さない**。
> 本格的な図ライブラリ(recharts 等)の選定は、ノード / エッジ描画が要る経路図・ネットワーク図の
> Phase 4 で行う。詳細 `Phase-3-5.md` §1。

---

## 7. まとめ

- 全体は UI ─(REST)─ API ─ DB。LLM Service は本流の外(Phase 10〜)。
- `decitima-api` に `domain/`(スキーマと制約チェッカー)と `algorithms/`(計算)を足す。
  この 2 層は**純粋**(副作用なし)で、再現性とテスタビリティを担保する。
- solve のライフサイクルは 「変換 → Validation → strategy 選択 → 計算 → Verification →
  永続化 → commit」。計算部分だけが純粋、その外側が I/O。
- 2 トラックは `algorithms/` 内で同一インターフェースの別クラスとして並ぶ。
  registry が problem_type ごとに候補をまとめる。
- 既存テンプレート資産(`AppError` / `CRUDRepository` / `RateLimiter` / 認証 / Docker)は
  作り直さず再利用する。
- UI は Phase 3〜 で `src/features/optimization/` として立ち上げる。

次章(Phase 0-4)では `algorithms/` の心臓部 ── `AlgorithmStrategy` インターフェースと
registry ── を設計する。
