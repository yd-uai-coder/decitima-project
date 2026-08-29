# Phase 1 — Algorithm Engine(実装フェーズ)

## このフェーズの目的

Phase 0 で確立した設計 ── 共通スキーマ `OptimizationProblem`、純粋な `domain/` と
`algorithms/`、Validation / Verification の分離、`POST /solve` ── を **決定論的な計算基盤**として実コードにする。README §19 Phase 1 の deliverable は「Binary Search / BFS / DFS /Dijkstra / 基本的な Algorithm Interface / Algorithm 実行 API / Unit Test」。

CL(Curriculum Loop)開発では **AI はコードを書かず、ユーザーが手で実装する**。この Phase の章は要点の抜粋のみで、動くコードは `samples/`(実 `app/` ツリーの鏡写し)にある。ユーザーはsamples を `decitima-api/backend/` へ写経し、作業単位ごとに `uv run ruff check .` /`uv run pytest` を通してコミットする(進行のルール #3)。

Validation / Verification は Phase 1 では **route_planning 限定の最小実装**を solve に配線し、全 kind・shift への拡張は Phase 2 に送る(理由は `Phase-1-0.md` §6)。

## 章一覧

概観章は `Phase-1-0`、以降 `Phase-1-M` = 作業単位 1-M(進行のルール #2)。

| 章                           | トピック                                  | 説明                                                                                                                                                                                                                         |
| --------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-1-0](./Phase-1-0.md) | 概観と solve ライフサイクル                     | 7 作業単位の地図と依存、`POST /solve` のライフサイクル(レート制限 → Validation → strategy 選択 → 計算 → Verification → 永続化 → commit)、実装 = 写経の進め方、テストの階層、Phase 1 のスコープと Phase 2 送り                                                                      |
| [Phase-1-1](./Phase-1-1.md) | 共通スキーマの実装(1-1)                        | `app/domain/problems` `solutions` へのファイル分割、葉 → アグリゲータ → `__init__` の一方向依存、Phase 0 スケッチからの変更(`: TypeAlias` → `type` 文 / `network_design` は Phase 4)、`Field` 制約と `model_validator`、書きかけコードとの差分                  |
| [Phase-1-2](./Phase-1-2.md) | AlgorithmStrategy と registry(1-2)     | `AlgorithmStrategy` Protocol(`@runtime_checkable`、純粋・非検証の `solve`)、`REGISTRY` / `get_strategies` / `find_strategy`(純粋)、`select_strategy` を services 層に置く理由(依存方向)、`app/services/errors.py` に 4 つの `AppError` 派生             |
| [Phase-1-3](./Phase-1-3.md) | 探索プリミティブ(1-3)                         | `linear_search` / `binary_search`(PEP 695 ジェネリクス、`_Comparable`)/ `bfs`(距離・到達可能性・最短経路)/ `dfs`(訪問順・経路の有無、再帰)。registry に載せない素の純粋関数。BFS は route Validation で再利用                                                                |
| [Phase-1-4](./Phase-1-4.md) | DijkstraStrategy(1-4)                 | `build_adjacency`(forbidden エッジ除外)、`_waypoints`(必須経由 0〜1 の区間分割)、`heapq` ダイクストラ、非連結で `status="infeasible"`、`metrics["_ops"]` の規約、`route_planner_example` の期待解(A→B→C→E, weight 9)                                            |
| [Phase-1-5](./Phase-1-5.md) | 永続化(1-5)                              | `Problem` / `Solution` ORM(JSONB `payload` + 検索キーのみカラム、`JSON().with_variant(JSONB())`)、JSON はまるごと代入、`CRUDRepository` 継承のリポジトリ(`flush` のみ)、`app/models/__init__.py` と `alembic/env.py` の両登録、autogenerate と目視確認              |
| [Phase-1-6](./Phase-1-6.md) | solve API ── Validation・Verification・SolveService(1-6) | route 限定の最小 `ProblemValidationService` / `SolutionVerificationService`、`SolveService` ライフサイクルとタイムアウト、`SolveRequest`/`SolveResponse`、`app/api/routes/solve.py`、`settings` 3 行の追記 |
| [Phase-1-7](./Phase-1-7.md) | 取得系と Phase 2 への引き継ぎ(1-7) | `OptimizationReadService`(所有者スコープ)、`GET /algorithms` / `GET /solutions/{id}` / `GET /problems/{id}(/solutions)`、ルーター集約(`routes/__init__.py` 追記)、Phase 2 の 7 単位分割表 |

## サンプルコード(`samples/`)

`samples/` には **Phase 1 で新規に作るファイルだけ**を置く。既存 `decitima-api` ファイルへの
追記(`app/core/config.py` / `app/services/errors.py` / `app/models/__init__.py` /
`app/api/routes/__init__.py` / `alembic/env.py`)は samples に入れず、各章に差分として示す
(`samples/README.md` に対応表)。

| 場所 | 内容 |
| --- | --- |
| [samples/app/domain/](./samples/app/domain/) | 共通スキーマの実装(`problems/` `solutions/`) |
| [samples/app/algorithms/](./samples/app/algorithms/) | `base.py`(Protocol)/ `registry.py` / `search/`(4 プリミティブ)/ `graph/dijkstra.py` |
| [samples/app/services/](./samples/app/services/) | `algorithm_selection` / `validation` / `verification` / `solve` / `optimization_read` |
| [samples/app/models/optimization.py](./samples/app/models/optimization.py) [samples/app/repositories/optimization.py](./samples/app/repositories/optimization.py) | `Problem` / `Solution` の ORM とリポジトリ |
| [samples/app/schemas/optimization.py](./samples/app/schemas/optimization.py) [samples/app/api/routes/](./samples/app/api/routes/) | API のスキーマとルート(`solve` / `algorithms` / `solutions`) |
| [samples/alembic/versions/](./samples/alembic/versions/) | `problems` / `solutions` テーブルのマイグレーション(autogenerate 目視確認用) |
| [samples/tests/](./samples/tests/) | unit(スキーマ / registry / 探索 / Dijkstra / V&V / SolveService / リポジトリ)、api、integration |

samples は `decitima-api` の venv に重ねて(既存ファイルへの 4 点の追記を適用したうえで)
`uv run pytest`(89 passed, 3 deselected)/ `uv run ruff check` / `ruff format --check`(clean)/
`uvx pyright`(0 errors)を確認済み。

## Phase 1 の成果物

- **textbook**: この `Phase-1/` 一式(概観 `Phase-1-0` + 解説 `Phase-1-1`〜`1-7` + samples + index)
- **decitima-api の実装**(ユーザーが写経): `app/domain/{problems,solutions}/**` / `app/algorithms/**` /
  `app/services/{solve,validation,verification,algorithm_selection,optimization_read}.py` /
  `app/models/optimization.py` / `app/repositories/optimization.py` /
  `app/schemas/optimization.py` / `app/api/routes/{solve,algorithms,solutions}.py` /
  `app/models/__init__.py`・`app/services/errors.py`・`app/core/config.py`・
  `app/api/routes/__init__.py`・`alembic/env.py` への追記 / 新マイグレーション / `tests/**`
- **ルート CLAUDE.md の Notes**: Phase 1 の設計決定(`select_strategy` の層、`type` 文への変更、
  V&V 最小実装の線引き、`network_design` の Phase 4 送り、objectives 評価器は Phase 5 送り)

## Phase 1 実装前チェックリスト

進行のルール #11。教材生成後・実装着手前に、ここで疑問を出し切る。
行 `1-M` ↔ 章 `Phase-1-M`(概観は `Phase-1-0`)。

| #   | 作るファイル                                                                                                                                                                                        | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                                                                                                        | テスト観点                                                                                                                                                                             |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1-1 | `app/domain/problems/{problem,route_planner,shift_scheduler,__init__}.py`、`app/domain/solutions/{solution,route_planner,shift_scheduler,__init__}.py` | `Objective` / `ConstraintBase`(+ 判別子付きサブタイプ)/ `GenericConstraint` / `AnyConstraint`(left_to_right)/ `ProblemData`・`SolutionData`(discriminator)/ `OptimizationProblem`(`problem_type == data.problem_type` の `model_validator`)/ `CandidateSolution`。route / shift の 2 problem_type(network_design は Phase 4、objectives 評価器は Phase 5)                                                                          | dict → 各サブタイプ構築 / discriminator 不一致で `ValidationError` / 未知 kind → `GenericConstraint` / 負 weight 拒否 / `model_dump`↔`model_validate` 往復 / pyright standard 0 errors               |
| 1-2 | `app/algorithms/base.py`、`app/algorithms/registry.py`、`app/services/algorithm_selection.py`、`app/services/errors.py`(追記)                                                                      | `AlgorithmStrategy` Protocol(`meta` + 純粋・非検証の `solve`)/ `REGISTRY`・`get_strategies`・`all_strategies`・`find_strategy`(None 返し)/ `select_strategy`(None → `NoAlgorithmError`)/ 4 つの `AppError` 派生                                                                                                                                                                                                         | フェイクが `isinstance` を通る / `dijkstra` が route に登録 / 既定で先頭候補 / `requested` 最優先 / 未登録で `NoAlgorithmError`                                                                             |
| 1-3 | `app/algorithms/search/{linear_search,binary_search,bfs,dfs}.py`                                                                                                                              | 決定論的な手実装。入力は素のデータ構造(ソート済み列・隣接リスト)。registry に載せない。`bfs.reachable_nodes` は 1-6 の Validation が再利用                                                                                                                                                                                                                                                                                                          | 正常系 / 空 / 単一要素 / 到達不能 / 既知の最短距離と一致 / binary と linear の結果一致。DB 不要                                                                                                                  |
| 1-4 | `app/algorithms/graph/dijkstra.py`                                                                                                                                                            | `DijkstraStrategy`: `build_adjacency`(forbidden 除外)→ `_waypoints`(必須 0〜1 の区間分割)→ `heapq` → `RouteSolution`。非連結で `infeasible`。`build_adjacency` は module 関数として export                                                                                                                                                                                                                                    | 制約なしで A→B→D→E(w5)/ `forbidden`+`required` で A→B→C→E(w9)/ 禁止エッジ不使用 / 必須ノード経由 / 非連結で `infeasible` / 同入力→同出力                                                                         |
| 1-5 | `app/models/optimization.py`、`app/repositories/optimization.py`、`alembic/versions/xxxx_*.py`、`app/models/__init__.py`(追記)、`alembic/env.py`(追記)                                                | `Problem` / `Solution` ORM(JSONB `payload` + 検索キーのみカラム)/ `ProblemRepository`・`SolutionRepository`(`CRUDRepository` 継承、`create` / `list_for_problem`、`flush` のみ)/ 両所への登録                                                                                                                                                                                                                                 | `alembic upgrade head` が通る / SQLite で CRUD 往復 / JSON まるごと代入で更新 / `list_for_problem` が `created_at` 順 / 実 PG で JSONB(integration)                                                  |
| 1-6 | `app/services/{validation,verification,solve}.py`、`app/schemas/optimization.py`、`app/api/routes/solve.py`、`app/core/config.py`(追記)                                                            | `ProblemValidationService.validate`(route: 存在・端点・到達可能性 BFS。NG は `ProblemValidationError` / `InfeasibleProblemError`)/ `SolutionVerificationService.verify`(route 構造 + `_CHECKERS` の forbidden・required_inclusion。hard→`invalid`、`model_copy` で新インスタンス)/ `SolveService.solve`(レート制限 → Validation → `select_strategy` → 計算+timeout → Verification → 永続化 → commit)/ `SolveRequest`・`SolveResponse` / 薄いルート | Route 問題で `status="valid"` の検証済み解 / `persist=false` で id は None / 未対応 problem_type で 400 / 到達不能で 400 / 認証なしで 401 / `timeout_seconds` 極小で `SolveTimeoutError` / verify が元の解を書き換えない |
| 1-7 | `app/services/optimization_read.py`、`app/api/routes/{algorithms,solutions}.py`、`app/api/routes/__init__.py`(追記)                                                                               | `OptimizationReadService`(所有者スコープの `get_problem` / `get_solution` / `list_solutions_for_problem`)/ `GET /algorithms`(registry 集約)/ `GET /solutions/{id}` / `GET /problems/{id}` / `GET /problems/{id}/solutions` / ルーター 3 本を集約に追加                                                                                                                                                                       | `GET /algorithms` が `dijkstra` の name/family/implementation/problem_types を返す / solve → `GET /solutions/{id}` / 他ユーザーの解は 404                                                      |

各単位ごとに `uv run ruff check .` と `uv run pytest` を通してからコミット。

## 次のフェーズ

Phase 1 完了後、「Phase 2 を開始する」で Validation / Constraint Engine の教材を生成する。
Phase 1 で通した V&V の「枠」を埋める 7 単位(Pydantic Validation 拡充 / shift の Semantic Validation / kind ごとの Checker 全実装 / shift の Verification / `POST /verify` / Invalid Solution Handling / `verifications` テーブル)。詳細は [Phase-1-7](./Phase-1-7.md) §5。
