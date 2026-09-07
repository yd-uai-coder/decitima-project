# Phase 1 — Algorithm Engine(実装フェーズ)導入

作業章(`Phase-1-1.md` 以降)を始める前に、この 1 本で Phase 1 の全体像を掴む。
目的 / solve のライフサイクル / レイヤー / 進め方 / テスト / スコープ / 章一覧 / 実装前チェックリスト。

---

## 1. このフェーズの目的

Phase 0 で確立した設計 ── 共通スキーマ `OptimizationProblem`、純粋な `domain/` と `algorithms/`、
Validation / Verification の分離、`POST /solve` ── を **決定論的な計算基盤** として実コードにする。
README §19 Phase 1 の deliverable は「Binary Search / BFS / DFS / Dijkstra / 基本的な
Algorithm Interface / Algorithm 実行 API / Unit Test」。

Validation / Verification は Phase 1 では **route_planning 限定の最小実装** を solve に配線し、
全 kind・shift への拡張は Phase 2 に送る(理由は §7)。

---

## 2. solve のライフサイクル

`POST /api/v1/solve` が来てからレスポンスを返すまで(`Phase-0-3.md` §3 の実装形)。
部品がどうつながるかを先に頭に入れておく。

```text
① app/api/routes/solve.py         SolveRequest を受け取り、認証済みユーザーを取得
        │                          ルートは薄い ── サービスを呼んで詰めて返すだけ
        ▼
② app/services/solve.py  SolveService.solve()   ← トランザクション境界。ここで commit
        │
        ├ (a) RateLimiter(resource="solve").enforce(user_id)      既存 RateLimiter を再利用
        │
        ├ (b) ProblemValidationService.validate(problem)          NG は AppError で終了(計算しない)
        │        └ route: start/goal 存在・エッジ端点・到達可能性(BFS)
        │
        ├ (c) select_strategy(problem, requested)                 registry から候補を1つ選ぶ
        │        └ 該当なし → NoAlgorithmError(400)
        │
        ├ (d) strategy.solve(problem) → CandidateSolution         純粋な計算。副作用なし
        │        └ タイムアウトを監視(超過 → SolveTimeoutError, 504)
        │
        ├ (e) SolutionVerificationService.verify(problem, sol)    hard 違反 → status="invalid"
        │        └ 解は書き換えず新インスタンスを返す
        │
        ├ (f) persist=True なら Problem / Solution を保存(JSONB payload)
        │
        └ (g) await session.commit()
        │
        ▼
③ app/api/routes/solve.py         CandidateSolution → SolveResponse に詰めて返す
```

- **例外はルートで捕まえない**。`ProblemValidationError` / `NoAlgorithmError` / `SolveTimeoutError`
  はそのまま伝播し、既存の `register_error_handlers` が JSON 化する
  (`decitima-api/CLAUDE.md` のエラーハンドリング節)。
- **(d) の計算は純粋**。DB もネットワークも時刻も触らない。だから同じ入力で必ず同じ結果になり
  (NFR-1)、ユニットテストが DB なしで書ける。
- **解の制約違反は例外ではない**。`CandidateSolution.status="invalid"` として 200 で返す
  (`Phase-0-6.md` §4)。

---

## 3. レイヤーと責務(Phase 1 で増える部分)

```text
app/api/routes/{solve,algorithms,solutions}.py   HTTP 境界。薄い
        │
app/schemas/optimization.py                      リクエスト/レスポンスの型(domain を薄く包む)
        │
app/services/{solve,validation,verification,     ユースケース・トランザクション境界
              algorithm_selection,optimization_read}.py
        │
        ├──▶ app/domain/{problems,solutions,objectives}/   純粋。型と意味。副作用なし
        ├──▶ app/algorithms/{base,registry,search,graph}   純粋。決定論的な計算
        └──▶ app/repositories/optimization.py  ─▶  app/models/optimization.py
```

- `app/domain/` と `app/algorithms/` は **標準ライブラリ + Pydantic(+ 将来 networkx/ortools)
  しか import しない**。services / repositories / DB / HTTP / Redis / ai に依存しない
  (`Phase-0-3.md` §2.2)。この純粋性が再現性とテスタビリティを生む。
- `select_strategy` だけは registry(純粋)ではなく services 層に置く。理由は
  [Phase-1-2](./Phase-1-2.md) §3。

---

## 4. 章一覧(章 = 作業単位)

`Phase-1-M.md` = 作業単位 1-M
`Phase-0-9.md` §7 で 7 単位に割ってある。依存の無い 1-1 / 1-3 / 1-5 から着手できる。
**単位ごとに `uv run ruff check .` と `uv run pytest` を通してからコミット**。

| 章                           | トピック                                              | 依存            | 主な内容                                                                                                                                                                                                 |
| --------------------------- | ------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-1-1](./Phase-1-1.md) | 共通スキーマの実装                                         | ―             | `app/domain/problems` `solutions` へのファイル分割、葉 → アグリゲータ → `__init__` の一方向依存、Phase 0 からの変更(`: TypeAlias` → `type` 文 / `network_design` は Phase 4)、`Field` 制約と `model_validator`                         |
| [Phase-1-2](./Phase-1-2.md) | AlgorithmStrategy と registry                      | 1-1           | `AlgorithmStrategy` Protocol(`@runtime_checkable`、純粋・非検証の `solve`)、`REGISTRY` / `get_strategies` / `find_strategy`、`select_strategy` を services 層に置く理由、`app/services/errors.py` に 4 つの `AppError` 派生 |
| [Phase-1-3](./Phase-1-3.md) | 探索プリミティブ                                          | ―             | `linear_search` / `binary_search`(PEP 695 ジェネリクス)/ `bfs`(距離・到達可能性・最短経路)/ `dfs`(訪問順・経路の有無)。registry に載せない素の純粋関数。BFS は route Validation で再利用                                                           |
| [Phase-1-4](./Phase-1-4.md) | DijkstraStrategy                                  | 1-1, 1-2, 1-3 | `build_adjacency`(forbidden 除外)、`_waypoints`(必須経由 0〜1 の区間分割)、`heapq` ダイクストラ、非連結で `infeasible`、`metrics["_ops"]` の規約、期待解(A→B→C→E, weight 9)                                                           |
| [Phase-1-5](./Phase-1-5.md) | 永続化                                               | ―             | `Problem` / `Solution` ORM(JSONB `payload` + 検索キーのみカラム)、JSON はまるごと代入、`CRUDRepository` 継承のリポジトリ、`app/models/__init__.py` と `alembic/env.py` の両登録、autogenerate                                         |
| [Phase-1-6](./Phase-1-6.md) | solve API ── Validation・Verification・SolveService | 1-1〜1-5       | route 限定の最小 `ProblemValidationService` / `SolutionVerificationService`、`SolveService` ライフサイクルとタイムアウト、`SolveRequest`/`SolveResponse`、`app/api/routes/solve.py`、`settings` 3 行の追記                      |
| [Phase-1-7](./Phase-1-7.md) | 取得系と Phase 2 への引き継ぎ                               | 1-5, 1-6      | `OptimizationReadService`(所有者スコープ)、`GET /algorithms` / `GET /solutions/{id}` / `GET /problems/{id}(/solutions)`、ルーター集約(`routes/__init__.py` 追記)、Phase 2 の 7 単位分割表                                    |

---

## 5. この Phase の進め方 ── 実装 = 写経

CL(Curriculum Loop)開発では **AI はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-1-*.md`)は **要点の抜粋** だけを載せる。
2. 動くコードは `samples/` にある(実 `app/` ツリーを鏡写しにした構造 + 絶対 import)。
3. ユーザーは samples から `decitima-api/backend/` へ **ファイル単位で写経・改変** する。
4. 実装中の疑問・改善点は Claude に質問・相談し、教材と samples に還流させる(進行のルール #8 / #9)。

```text
textbook/Phase-1/
├── Phase-1-introduction.md   この導入(目的 / 概観 / 章一覧 / 実装前チェックリスト)
├── Phase-1-1.md 〜 1-7.md    各作業単位の解説
└── samples/
    ├── README.md             写経の対応表・検証手順・既存ファイルへの追記メモ
    ├── app/**                → decitima-api/backend/app/**
    ├── tests/**              → decitima-api/backend/tests/**
    └── alembic/versions/*.py → autogenerate の目視確認用
```

**着手前に §10 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層(`Phase-0-9.md` §1 の再確認)

| レベル                      | 使うもの                                       | Phase 1 で書くもの                                                 |
| ------------------------ | ------------------------------------------ | ------------------------------------------------------------- |
| domain / algorithms(主戦場) | 素の pytest。DB 不要                            | スキーマ / 探索プリミティブ / Dijkstra の純粋関数テスト                           |
| サービス層                    | `db_session`(インメモリ SQLite)+ `FakeRedis`    | `SolveService` / Validation / Verification                    |
| API                      | `httpx.AsyncClient` + 依存差し替え               | `POST /solve` / `GET /algorithms` / `GET /solutions/{id}` の契約 |
| 統合(既定で除外)                | 実 PostgreSQL(`docker compose up postgres`) | JSONB カラムの読み書き                                                |

`samples/tests/` にすべて用意してある。

```bash
uv run pytest                 # unit + service + api(89 passed, 3 deselected)
uv run pytest -m integration  # 要 docker compose up postgres
```

---

## 7. Phase 1 のスコープと非スコープ

| Phase 1 でやる                                             | Phase 2 以降に送る                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 共通スキーマの型(route / shift の 2 problem_type)                | `network_design` の型とアルゴリズム(Phase 4)                                          |
| `AlgorithmStrategy` + registry + rule-based 選択の骨組み      | LLM 推薦 / ベンチマークベース選択(Phase 12 / 3)                                           |
| Linear/Binary Search・BFS・DFS(プリミティブ)、Dijkstra(Strategy) | Bellman-Ford / A* / MST(Phase 4)、Greedy / Backtracking(Phase 6)              |
| **route 限定** の最小 Validation / Verification を solve に配線  | kind ごとの Checker 全実装 / shift の検証 / `POST /verify` / invalid 解ハンドリング(Phase 2) |
| `Problem` / `Solution` の永続化                             | `benchmark_runs`(Phase 3)。`verifications` テーブルは作らない(下記「後続 Phase での改訂」)  |
| 同期実行 + タイムアウト                                           | ジョブキュー(YAGNI。必要なら Phase 9)                                                   |
| objectives(多目的の重み付き和の評価器) ── **作らない**                   | Phase 6(初の多目的ストラテジー = Shift Scheduler)                                       |

Validation / Verification を Phase 1 で **最小だが配線する** 理由: README では Phase 2 だが、
`SolveService` のライフサイクル(`Phase-0-3.md` §3)にステージとして組み込まれており、
枠だけ先に通しておくと Phase 2 が「枠を埋める」作業になる。Phase 1 の実装は
route_planning に限定し、Phase 2 で shift と全 kind に広げる。

---

## 8. サンプルコード(`samples/`)

`samples/` には **Phase 1 で新規に作るファイルだけ** を置く。既存 `decitima-api` ファイルへの
追記(`app/core/config.py` / `app/services/errors.py` / `app/models/__init__.py` /
`app/api/routes/__init__.py` / `alembic/env.py`)は samples に入れず、各章に差分として示す
(`samples/README.md` に対応表)。

| 場所                                                                                                                                                                | 内容                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [samples/app/domain/](./samples/app/domain/)                                                                                                                      | 共通スキーマの実装(`problems/` `solutions/`)                                                   |
| [samples/app/algorithms/](./samples/app/algorithms/)                                                                                                              | `base.py`(Protocol)/ `registry.py` / `search/`(4 プリミティブ)/ `graph/dijkstra.py`         |
| [samples/app/services/](./samples/app/services/)                                                                                                                  | `algorithm_selection` / `validation` / `verification` / `solve` / `optimization_read` |
| [samples/app/models/optimization.py](./samples/app/models/optimization.py) [samples/app/repositories/optimization.py](./samples/app/repositories/optimization.py) | `Problem` / `Solution` の ORM とリポジトリ                                                   |
| [samples/app/schemas/optimization.py](./samples/app/schemas/optimization.py) [samples/app/api/routes/](./samples/app/api/routes/)                                 | API のスキーマとルート(`solve` / `algorithms` / `solutions`)                                   |
| [samples/alembic/versions/](./samples/alembic/versions/)                                                                                                          | `problems` / `solutions` テーブルのマイグレーション(autogenerate 目視確認用)                            |
| [samples/tests/](./samples/tests/)                                                                                                                                | unit(スキーマ / registry / 探索 / Dijkstra / V&V / SolveService / リポジトリ)、api、integration    |

samples は `decitima-api` の venv に重ねて(既存ファイルへの 4 点の追記を適用したうえで)
`uv run pytest`(89 passed, 3 deselected)/ `uv run ruff check` / `ruff format --check`(clean)/
`uvx pyright`(0 errors)を確認済み。

---

## 9. Phase 1 の成果物

- **textbook**: この `Phase-1/` 一式(この導入 + 解説 `Phase-1-1`〜`1-7` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/domain/{problems,solutions}/**` / `app/algorithms/**` /
  `app/services/{solve,validation,verification,algorithm_selection,optimization_read}.py` /
  `app/models/optimization.py` / `app/repositories/optimization.py` /
  `app/schemas/optimization.py` / `app/api/routes/{solve,algorithms,solutions}.py` /
  `app/models/__init__.py`・`app/services/errors.py`・`app/core/config.py`・
  `app/api/routes/__init__.py`・`alembic/env.py` への追記 / 新マイグレーション / `tests/**`
- **ルート CLAUDE.md の Notes**: Phase 1 の設計決定(`select_strategy` の層、`type` 文への変更、
  V&V 最小実装の線引き、`network_design` の Phase 5 送り、objectives 評価器は Phase 6 送り)

---

## 10. Phase 1 実装前チェックリスト

進行のルール #11。教材生成後・実装着手前に、ここで疑問を出し切る。行 `1-M` ↔ 章 `Phase-1-M`。
各章の冒頭にも「この章で新規作成するファイル」がある(進行のルール #13)。

| #   | 作るファイル                                                                                                                                                | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                                                                                                        | テスト観点                                                                                                                                                                             |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1-1 | `app/domain/problems/{problem,route_planner,shift_scheduler,__init__}.py`、`app/domain/solutions/{solution,route_planner,shift_scheduler,__init__}.py` | `Objective` / `ConstraintBase`(+ 判別子付きサブタイプ)/ `GenericConstraint` / `AnyConstraint`(left_to_right)/ `ProblemData`・`SolutionData`(discriminator)/ `OptimizationProblem`(`problem_type == data.problem_type` の `model_validator`)/ `CandidateSolution`。route / shift の 2 problem_type(network_design は Phase 5、objectives 評価器は Phase 6)                                                                   | dict → 各サブタイプ構築 / discriminator 不一致で `ValidationError` / 未知 kind → `GenericConstraint` / 負 weight 拒否 / `model_dump`↔`model_validate` 往復 / pyright standard 0 errors               |
| 1-2 | `app/algorithms/base.py`、`app/algorithms/registry.py`(strategy はコメントアウトして出荷。#15)、`app/services/algorithm_selection.py`、`app/services/errors.py`(追記) | `AlgorithmStrategy` Protocol(`meta` + 純粋・非検証の `solve`)/ `REGISTRY`・`get_strategies`・`all_strategies`・`find_strategy`(None 返し)/ `select_strategy`(None → `NoAlgorithmError`)/ 4 つの `AppError` 派生 | フェイクが `isinstance` を通る / フェイクを fixture で `REGISTRY` に登録し機構を検証(`get_strategies`・`all_strategies`・先頭候補・`requested` 一致・未登録で `NoAlgorithmError`・`find_strategy` は None 返し)。**dijkstra の登録確認は 1-4**(進行ルール #15) |
| 1-3 | `app/algorithms/search/{linear_search,binary_search,bfs,dfs}.py`                                                                                      | 決定論的な手実装。入力は素のデータ構造(ソート済み列・隣接リスト)。registry に載せない。`bfs.reachable_nodes` は 1-6 の Validation が再利用                                                                                                                                                                                                                                                                                                          | 正常系 / 空 / 単一要素 / 到達不能 / 既知の最短距離と一致 / binary と linear の結果一致。DB 不要                                                                                                                  |
| 1-4 | `app/algorithms/graph/dijkstra.py`。**既存への変更**: `app/algorithms/registry.py` の `DijkstraStrategy` 行 2 箇所のコメントを外す(#15) | `DijkstraStrategy`: `build_adjacency`(forbidden 除外)→ `_waypoints`(必須 0〜1 の区間分割)→ `heapq` → `RouteSolution`。非連結で `infeasible`。`build_adjacency` は module 関数として export | 制約なしで A→B→D→E(w5)/ `forbidden`+`required` で A→B→C→E(w9)/ 禁止エッジ不使用 / 必須ノード経由 / 非連結で `infeasible` / 同入力→同出力 / **registry から `dijkstra` が引ける** |
| 1-5 | `app/models/optimization.py`、`app/repositories/optimization.py`、`alembic/versions/xxxx_*.py`、`app/models/__init__.py`(追記)、`alembic/env.py`(追記)        | `Problem` / `Solution` ORM(JSONB `payload` + 検索キーのみカラム)/ `ProblemRepository`・`SolutionRepository`(`CRUDRepository` 継承、`create` / `list_for_problem`、`flush` のみ)/ 両所への登録                                                                                                                                                                                                                                 | `alembic upgrade head` が通る / SQLite で CRUD 往復 / JSON まるごと代入で更新 / `list_for_problem` が `created_at` 順 / 実 PG で JSONB(integration)                                                  |
| 1-6 | `app/services/{validation,verification,solve}.py`、`app/schemas/optimization.py`、`app/api/routes/solve.py`、`tests/api/conftest.py`(`api` フィクスチャ)、`app/core/config.py`(追記)、`app/api/routes/__init__.py`(追記 ── `solve_router` の集約。#15) | `ProblemValidationService.validate`(route: 存在・端点・到達可能性 BFS。NG は `ProblemValidationError` / `InfeasibleProblemError`)/ `SolutionVerificationService.verify`(route 構造 + `_CHECKERS` の forbidden・required_inclusion。hard→`invalid`、`model_copy` で新インスタンス)/ `SolveService.solve`(レート制限 → Validation → `select_strategy` → 計算+timeout → Verification → 永続化 → commit)/ `SolveRequest`・`SolveResponse` / 薄いルート | Route 問題で `status="valid"` の検証済み解 / `persist=false` で id は None / 未対応 problem_type で 400 / 到達不能で 400 / 認証なしで 401 / `timeout_seconds` 極小で `SolveTimeoutError` / verify が元の解を書き換えない |
| 1-7 | `app/services/optimization_read.py`、`app/api/routes/{algorithms,solutions}.py`、`app/api/routes/__init__.py`(追記 ── `algorithms` / `solutions` の 2 本。`solve` は 1-6) | `OptimizationReadService`(所有者スコープの `get_problem` / `get_solution` / `list_solutions_for_problem`)/ `GET /algorithms`(registry 集約)/ `GET /solutions/{id}` / `GET /problems/{id}` / `GET /problems/{id}/solutions` / `algorithms` / `solutions` ルーターを集約に追加                                                                                                                                                                       | `GET /algorithms` が `dijkstra` の name/family/implementation/problem_types を返す / solve → `GET /solutions/{id}` / 他ユーザーの解は 404                                                      |

各単位ごとに `uv run ruff check .` と `uv run pytest` を通してからコミット。

---

## 後続 Phase での改訂(進行のルール #12.3)

- **[Phase 2]** `services/validation.py` / `services/verification.py` は route 限定・インライン
  から、`domain/problems/semantic.py` の `SEMANTIC_CHECKS` と `domain/constraints/` の
  `CHECKERS` を回すオーケストレーションに縮小。shift の V&V を実装。詳細
  [Phase-2-2](../Phase-2/Phase-2-2.md) / [Phase-2-3](../Phase-2/Phase-2-3.md) /
  [Phase-2-4](../Phase-2/Phase-2-4.md)。該当は `Phase-1-6.md` §2 / §3。
- **[Phase 2]** `ShiftSlot` / `ShiftData` に Input Validation の validator を追加、
  `NumericBoundConstraint` のフィールドを `op` → `operator` に。`Phase-1-1.md` §2.3。
- **[Phase 2]** `verifications` テーブルは作らないことに確定(YAGNI。検証結果は
  `Solution.status` + `payload`。`Phase-0-8.md` §4)。旧 7 単位 → 6 単位。`Phase-1-7.md` §5。
- **[Phase 3]** `models/optimization.py` に `BenchmarkRun`(`benchmark_runs` テーブル)、
  `repositories/optimization.py` に `BenchmarkRunRepository` を同居、
  `services/optimization_read.py` に `get_benchmark_run` を追加。`Problem` への FK は張らない
  (独立した測定記録)。**レイヤー分割の粒度を確定**: data 層(model / schema / repository)は
  「永続化の関心事」で 1 ファイル、route / service は「操作」で割る(`Phase-3-3.md` §2.3)。
  詳細 [Phase-3-3](../Phase-3/Phase-3-3.md)。該当は `Phase-1-5.md` / `Phase-1-7.md`。
- **[Phase 4]** `domain/problems/route_planner.py` の `RouteEdge.weight` の `Field(ge=0)` を撤廃し
  `RouteData.allow_negative` + `model_validator` に(負辺を Bellman-Ford で扱う。`Phase-4-2.md`)。
  `ProblemData` / `SolutionData` を **3 メンバー**に(`network_design` 追加。`Phase-5-3.md`)。
  `graph/dijkstra.py` の `build_adjacency` を `graph/adjacency.py` へ移設、`_waypoints` を
  `optimize_waypoint_order` に(`Phase-4-1.md` / `Phase-4-4.md`)。`registry.py` に route 3 本
  + `network_design` キー、`services/algorithm_selection.py` を rule-based に(`Phase-4-5.md`)。
  該当は `Phase-1-1.md` §2.2 / §5、`Phase-1-2.md`、`Phase-1-4.md`、`Phase-1-5.md`。

## 11. 次のフェーズ

Phase 1 完了後、「Phase 2 を開始する」で Validation / Constraint Engine の教材を生成する。
Phase 1 で通した V&V の「枠」を埋める 6 単位(Input Validation 拡充 / Semantic Validation の
一般化 / kind ごとの Checker 全実装 / shift の Verification / `POST /verify` / Invalid Solution
Handling)。詳細は [Phase-1-7](./Phase-1-7.md) §5 と `Phase-2/Phase-2-introduction.md`。
