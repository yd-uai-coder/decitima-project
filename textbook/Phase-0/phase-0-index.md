# Phase 0 — Optimization Architecture(設計フェーズ)

## このフェーズの目的

責務分離と共通モデルを確立する。README §19 のとおり Phase 0 は**設計フェーズ**で、
実コードは Phase 1 から。DeciTima の核は「LLM は理解・構造化・説明のみ、
計算・検証・最適化は決定論的なアルゴリズム」で、両者の結合点が共通スキーマ
`OptimizationProblem`。

設計はすべて MVP の 2 題材 ── **Route Planner**(Phase 4)と
**Shift Scheduler**(Phase 5)── で通し検証している。

## 章一覧

| 章 | トピック | 説明 |
| --- | --- | --- |
| [Phase-0-1](./Phase-0-1.md) | 要件定義とスコープ | DeciTima が解く問題クラス、非ゴール(LLM に計算させない)、7 ステージの責務分離、MVP スコープ(Phase 0〜5)、検証題材 2 つの紹介と機能/非機能要件 |
| [Phase-0-2](./Phase-0-2.md) | ドメインモデル: 共通スキーマ | なぜ共通スキーマが要るか、ハイブリッド型の設計、`Objective` / `Constraint`(hard・soft)/ `OptimizationProblem` / `CandidateSolution`、Route と Shift を実際に書き下しての検証、拡張ポイント |
| [Phase-0-3](./Phase-0-3.md) | アーキテクチャ設計 | システム全体構成、`decitima-api` の新レイヤー `domain/` `algorithms/`(純粋・副作用なし)、solve リクエストのライフサイクル、2 トラックの吸収方法、既存テンプレート資産の再利用、`decitima-ui` の将来構成 |
| [Phase-0-4](./Phase-0-4.md) | Algorithm Engine 設計 | `AlgorithmStrategy` プロトコル(`solve` は純粋・検証しない)、`AlgorithmMeta`、`registry`(problem_type → 候補)、手実装/産業ソルバーの 2 トラックを同一契約に載せる方法、rule-based のアルゴリズム選択 |
| [Phase-0-5](./Phase-0-5.md) | 計算量とパフォーマンス設計 | MVP アルゴリズムの時間/空間計算量、想定入力サイズと手実装の破綻点(Shift は中規模で CP-SAT 必須)、Phase 3 で測る 6 指標、同期実行 + タイムアウトの方針(ジョブキューは YAGNI) |
| [Phase-0-6](./Phase-0-6.md) | Validation と Verification 設計 | 2 つの検証の分離(問題定義の妥当性 vs 解の制約充足)、Input/Semantic Validation、`Constraint.kind` ごとのチェッカー、hard→invalid / soft→penalty、`AppError` 派生の追加、2 題材の検証項目一覧 |
| [Phase-0-7](./Phase-0-7.md) | API 設計 | MVP エンドポイントの絞り込み(`POST /solve` が軸、Route/Shift 専用 API は作らない)、リクエスト/レスポンススキーマ、エラーレスポンス形式、既存 JWT 認証と `RateLimiter` の再利用、solve 結果は `solution_id` で引ける |
| [Phase-0-8](./Phase-0-8.md) | DB 設計 | 保存対象(`problems` / `solutions` ほか)、JSONB 中心 + 検索キーのみカラム化、ORM モデル案(既存 `conversation.py` パターン踏襲)、ミューテーション追跡の落とし穴回避、Alembic 運用(`__init__.py` と `env.py` の両方に登録) |
| [Phase-0-9](./Phase-0-9.md) | テスト戦略・Docker・Phase 1 への引き継ぎ | テストの階層(domain/algorithms の純粋関数テストが主戦場)、プロパティベーステスト候補、`conftest.py` の env 設定順序、Docker は変更不要、依存追加の Phase 別計画、Phase 0 で入れた低リスク整備、Phase 1 の作業分割(7 単位) |

## サンプルコード(`samples/`)

| ファイル | 内容 |
| --- | --- |
| [problem_schema.py](./samples/problem_schema.py) | 共通スキーマの Pydantic v2 スケッチ(`OptimizationProblem` / `Constraint` / `CandidateSolution` ほか) |
| [algorithm_strategy.py](./samples/algorithm_strategy.py) | `AlgorithmStrategy` Protocol + `registry` + `select_strategy` のスケッチ |
| [route_planner_example.py](./samples/route_planner_example.py) | Route Planner を共通スキーマで表現(禁止エッジ + 必須経由) |
| [shift_scheduler_example.py](./samples/shift_scheduler_example.py) | Shift Scheduler を共通スキーマで表現(多目的 + hard/soft 混在) |

いずれも `decitima-api/backend` の uv 環境で `uv run python <path>` して動作確認済み。
decitima-api には未配線の「設計の例示」で、Phase 1 で `app/domain/` へ整理する。

## Phase 0 の成果物

- **textbook**: この `Phase-0/` 一式(設計文書 + サンプル)
- **decitima-api の低リスク整備**: chat ルート無効化 / `domain/`・`algorithms/` の空骨子 /
  `PROJECT_NAME` リブランド / `decitima-api/CLAUDE.md` 更新
- **ルート CLAUDE.md の Notes**: Phase 0 の主要な設計決定を追記

## 次のフェーズ

「Phase 1 を開始する」で、この設計を決定論的な計算基盤として実装する
(スキーマ実装 / `AlgorithmStrategy` / Binary Search・BFS・DFS・Dijkstra の手実装 /
実行 API / Unit Test)。
