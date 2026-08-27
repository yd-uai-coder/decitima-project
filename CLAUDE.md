# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発ポリシー
このプロジェクトの開発にあたり、README.mdの内容に沿って
claude codeで設計や各開発ステップの詳細やコードを提案し、学習教材としてユーザーに提供する。
それによりユーザーはclaude codeと共に開発をすることで設計から開発、デプロイまでのプロセスを学習しながらアプリケーションの全体をつかむ事ができる。

Claudeはコードをただ生成するのではなく、
設計意図・問題分解・アルゴリズム・トレードオフを説明する。

実装前に以下を確認する。

1. Requirements
2. Domain Model
3. Architecture
4. Algorithm
5. Complexity
6. Implementation Plan
7. Test Strategy

ユーザーが理解できるよう、
必要に応じて実装理由を説明する。

既存コードを変更する場合は、
変更前に影響範囲を調査する。

大きな変更を一度に実装せず、
検証可能な単位に分割する。

### 進行のルール
1. 学習教材をPhase毎にtextbookフォルダに.md形式で作成する
2. 学習教材は各Phaseの中で章立てする。例）Phase-0-1.md, phase-0-2.md ...
3. 教材で提示するコードは、長いコードブロックを Markdown に直書きせず「要点の抜粋 + `textbook/Phase-<N>/samples/` のファイル参照」とする。samples を「実装の初期状態(単一の真実源)」と位置づけ、ユーザーが `decitima-api/app/`(または `decitima-ui/src/`)へ写経・改変して実装する。これで「教材 Markdown / samples / 実コード」の三重管理を避ける。Phase 0 の既存教材は遡及リライトせず設計フェーズのスケッチとして残す(Phase 1 から適用)。
4. 実装段階での検討事項や、検証段階で発覚した事象はCLAUDE.mdのNotes欄に記録していく
5. ユーザーの「Phase#を開始する」というプロンプトでそのPhaseのtextbookを生成する。
6. Phase毎にインデックス用ファイル `phase-<N>-index.md` を各Phaseフォルダ直下に作成する。フェーズの目的、各章のトピックと説明、各ファイル(章・サンプルコード)へのリンクを記載する。章を追加・変更したらインデックスも更新する。
7. 教材でコードを提案するときは、配置先のファイルパスを各コードブロックの先頭にコメントで明記する(例: `# app/domain/problems/route_planner.py`)。分割するモジュールはパッケージ(`__init__.py` 付き)として示し、`__init__.py` の re-export 形とファイル間の依存方向も示す。既存教材の修正時・以降の Phase でも同様。
8. ユーザーが Claude に行った質問・相談とその回答を、`## Notes` の `### 実装段階での検討事項と採用した方針、採用理由` 内の `#### 質問・相談ログ` に追記する。各エントリは次の形式:
   1. 疑問が生じた Phase
   2. 質問・相談内容
   3. 回答と対応方針
9. 検討・相談の中で提示するコード(クラス名・シグネチャ・型など)に変更が生じたら、対応する `textbook/Phase-<N>/samples/` のサンプルコードにも同じ変更を反映する。反映後は `uv run python`(decitima-api の環境)で実行確認し、可能なら型チェック(pyright standard)も通す。
10. 本プロジェクトの進行方法について気づいた点(特徴・メリット / 課題 / 課題解決への提案)を `## Notes` の `### 本プロジェクトの進行方法についての所感` に追記する。課題には可能な限り「提案」を対で書く。提案をプロジェクトに組み込むかはユーザーが個別に判断する(Claude は勝手に適用しない)。
11. 各 `phase-<N>-index.md` に「実装前チェックリスト」を置く。内容: その Phase で作成するファイル一覧 / 各クラス・関数の責務 1 行 / テスト観点。Phase 教材の生成後・実装着手前に、ユーザーがこれで疑問を出し切ってから実装に入る。



## プラグインの利用ルール
以下のルールに従ってプラグインを使用する。
### 常時利用
- superpowers(スキル呼び出しで作動。作業開始時に `using-superpowers` を参照)
- explanatory-output-style(`/output-style explanatory` で明示適用が必要。自動では有効化されない)
- security-guidance
- context7

### 機能開発
Use feature-dev when implementing a significant feature.

### フロントエンド開発
Use frontend-design when designing or substantially modifying UI.

### E2E テスト
Use playwright when implementing or debugging browser-based E2E tests.

### コードレビュー
Use code-review before completing a significant feature or pull request.


## このディレクトリの位置づけ

`decitima/` は **DeciTima プロジェクトのワークスペース** であり、GitHub では `decitima-project` という独立リポジトリになる。アプリのコードは配下に置かず、プロジェクト全体の説明・学習教材・進行ルールだけを持ち、`decitima-ui` / `decitima-api` へ誘導する役割。

| パス | 内容 | git |
| --- | --- | --- |
| `README.md` | DeciTima の製品ビジョン / 仕様書(日本語・約1500行)。「AI-assisted Decision Optimization Platform」の全体設計、Phase 0〜14 の開発計画、MVP 範囲(Phase 0〜5) | `decitima-project` が追跡 |
| `CLAUDE.md` | 本ファイル。開発ポリシー・進行ルール・決定事項・Notes | `decitima-project` が追跡 |
| `textbook/` | Phase 毎の学習教材(`.md`)とサンプルコード。詳細は「進行のルール」 | `decitima-project` が追跡 |
| `decitima-ui/` | フロントエンド。`github.com/yd-uai-coder/decitima-ui` | **独立リポジトリ**(ルートの `.gitignore` で除外) |
| `decitima-api/` | バックエンド。`github.com/yd-uai-coder/decitima-api` | **独立リポジトリ**(ルートの `.gitignore` で除外) |

**git 構成**: GitHub 上に `decitima-project` / `decitima-ui` / `decitima-api` の 3 並列リポジトリ。ルートの git は `decitima-ui/` `decitima-api/` を `.gitignore` で完全に無視する(submodule / gitlink は使わない — サブリポジトリのコミットはルートに連動しない)。ui / api 内では従来どおり独立して `git` を操作する。

**コミット / プッシュの分担**: 3 リポジトリいずれも、Claude は**コミットまで**を行う。`git push` はユーザーが手動で行う(Claude は push しない)。

コード・コメント・コミットメッセージ・ドキュメントは基本的に **日本語**。

## ビジョンと現状のギャップ(最重要)

`README.md` が描く DeciTima は次のパイプラインを核とする:

```
自然言語の要求 → LLM が構造化 → Validation → Algorithm/Optimization Engine
→ 候補解 → Constraint Verification → Simulation/比較 → LLM による説明 → 意思決定
```

**設計思想: LLM に最適解を計算させない。** LLM は「曖昧な要求の理解・構造化・説明」だけを担当し、経路探索・DP・スケジューリング・制約判定・数値最適化・ベンチマークはすべて決定論的な Algorithm Engine が担当する。この責務分離が再現性・制約遵守・検証可能性・アルゴリズム比較を可能にする。

一方で `decitima-api` / `decitima-ui` は **どちらもまだ汎用テンプレート段階**(各リポジトリとも初回コミットのみ):

- `decitima-api` は「FastAPI + LangChain + LangGraph の AI チャットバックエンド」テンプレート。`algorithms/` `domain/`(problems/constraints/objectives/solutions)`validation_service` `verification_service` など README が要求する最適化レイヤーはまだ存在しない。現状あるのは JWT 認証・会話 CRUD・LangGraph チャットワークフロー・レート制限。
- `decitima-ui` は「Next.js(App Router)+ Tamagui」の UI サンプル/デモ集(`next-tamagui-templates`)。DeciTima 固有の画面(問題定義確認 UI、経路可視化、ガントチャート等)はまだ無い。

DeciTima 機能を実装するタスクでは、README の Phase 定義・Problem/Constraint/Objective/Solution スキーマ・`README.md` 16〜19 節の目標ディレクトリ構造を設計の出発点にする。

## 設計上の決定事項

### アルゴリズム実装方針 — 2 トラック

同一の `Algorithm`(strategy)インターフェースと同一の Problem / Solution スキーマの下に、2 つの実装を並存させる:

1. **手実装トラック(主軸)** — BFS / DFS / Binary Search / Dijkstra / A* / Knapsack / Backtracking / Branch and Bound 等を自前で実装する。学習教材の中心であり、再現性・計算量・設計判断を説明できることを最優先する。ポートフォリオとしての「アルゴリズムを実装できる」証明もここが担う。
2. **産業ソルバートラック(実務)** — 実規模でスケールしない問題(Phase 5 Shift Scheduler、Phase 8 Logistics 等)向けに、同じインターフェースの裏で OR-Tools CP-SAT / scipy / networkx を使う実装も用意する。

各 strategy はメタデータに `implementation`(`"handwritten"` / `"library:ortools"` 等)を持つ。両トラックが同一インターフェース・同一スキーマなので、**Phase 3 のベンチマークと Phase 13 の「LLM vs Algorithm」比較がそのまま「手実装 vs 産業ソルバー」比較に拡張できる**(スケール限界・解の品質差・いつソルバーに切り替えるべきかを実測で示す)。

ライブラリ依存は必要になった Phase まで追加を遅延する: `networkx`(Phase 4、手実装グラフアルゴリズムの検証オラクル兼)、`ortools`(Phase 5、Phase 7/8 で再利用)、`numpy`(Phase 3 ベンチマーク集計)、`pulp` / `scipy`(Phase 8 で MILP 化する場合)。

### 既存 LLM チャット機能の扱い

`decitima-api` のテンプレートには LLM チャット機能(`app/ai/` の LangGraph ワークフロー、`POST /chat`、`conversation` / `message` モデル)が含まれるが、README では LLM は **Phase 10〜13**。それまでの Phase 0〜9 では:

- `app/api/routes/__init__.py` の集約から `chat` ルーターを外し、**エンドポイントを無効化**する。
- `app/ai/`・`schemas/chat.py`・`schemas/generation.py`・`conversation` / `message` モデル・既存マイグレーションは **削除せず保持**する(Phase 10 で DeciTima 用ワークフローに作り替える土台)。

## コード提示・コメント規約

### 再利用性とテンプレートへの還元

`decitima-ui` / `decitima-api` は次の**元テンプレートリポジトリ**から作られている。DeciTima 開発中に得られた汎用的な改善は、こちらへ戻すことを前提に進める。

| 対象 | ローカル | GitHub |
| --- | --- | --- |
| UI | `~/my-apps/project-templates/next-tamagui-templates` | `yd-uai-coder/next-tamagui-templates` |
| API | `~/my-apps/project-templates/fastapi-langchain-tamplate`(ローカルの綴りは "tamplate") | `yd-uai-coder/fastapi-langchain-template` |

- DeciTima 開発中に**ドメイン非依存の汎用部品・ユーティリティ・パターン**(特定の問題ドメインに依存しないもの)を作った場合、そのテンプレートリポジトリへの変更・追加を**都度提案する**。実際に反映する作業のタイミングはユーザーが別途指示する。
- **ネーミングも還元を見越す**。関数名・ファイル名・ディレクトリ名は、テンプレートへ戻せるようドメイン非依存の名前を優先し、DeciTima 固有の語(shift, route, travel など)を汎用部品名に埋め込まない。ドメイン固有のものは `decitima-ui` の `src/features/<name>/`、`decitima-api` の `app/domain/` 側に置き、汎用層とはっきり分ける。
- 還元はテンプレート側の既存規約に沿わせる — `next-tamagui-templates`: `src/components/` は機能非依存のデザインシステム層、ドメインは `src/features/<name>/{components,hooks,api,stores}` へ分割。`fastapi-langchain-template`: `routes → services → repositories → models` のレイヤー境界、`commit()` はサービス層のみ、ドメイン例外は `services/errors.py` に集約。

### コメント

リポジトリ本体・`textbook/` のサンプルコード双方に、日本語で以下のコメントを付ける。**文字数は目安**。既存コードの「なぜ / ハマりどころ」中心の記述はそのまま活かし、本規約はその**最低ライン**とする。型と命名で自明な引数・変数はコメントを省略してよい。

| 対象 | 内容 | 目安 |
| --- | --- | --- |
| 関数の説明 | 何をする関数か(必要なら「なぜ」も) | 60〜100 文字程度 |
| 関数の引数・戻り値 | 各引数の意味と戻り値 | 簡潔に |
| 関数内の条件分岐・繰り返し | その分岐 / ループが何を判定・処理するか | 40 文字程度 |
| 関数内の変数 | その変数が保持する値 | 簡潔に |

言語ごとの書き方は既存スタイルに合わせる:

- **Python(`decitima-api`)** — 関数 / クラス直下に `"""..."""` docstring。引数・変数はシグネチャ直後や該当行の直前に `# 名前: 説明` のインラインコメント。条件分岐・ループは直前に `#` コメント。参考: `backend/app/repositories/base.py`, `backend/app/services/rate_limit.py`。
- **TypeScript(`decitima-ui`)** — 関数 / フック直上に JSDoc `/** ... */`(`@param` / `@returns` タグは型があるので必須ではない。文章で説明する)。非自明な引数・戻り値は JSDoc 本文か直前の `//` で補う。条件分岐・非自明なロジックは直前に `//` コメント。参考: `src/hooks/useFilterSortPagination.ts`, `src/lib/api/client.ts`。

## サブリポジトリでの作業

各リポジトリに専用の `CLAUDE.md` と `README.md` がある。**そのリポジトリで作業するときは必ずそちらを読む**(コマンド・アーキテクチャ・ハマりどころが詳細に書かれている。ここでは繰り返さない)。

- `decitima-api/CLAUDE.md` — レイヤー構成(routes → services → repositories → models、+ ai)、`AppError` 集約エラーハンドリング、リポジトリ層は `flush` のみ、テスト分離など
- `decitima-ui/CLAUDE.md` — 全ページ SSG、`src/lib/api/` の FastAPI 連携層、Tamagui テーマ設定、Vitest など。加えて `decitima-ui/AGENTS.md`: この Next.js はメジャーアップデートで破壊的変更があるため、コード記述前に `node_modules/next/dist/docs/` の該当ガイドを読むこと

### よく使うコマンド(詳細は各 CLAUDE.md)

```bash
# decitima-ui/ で
npm run dev          # http://localhost:3000
npm run lint
npm run test                                  # Vitest 一度だけ
npx vitest run path/to/File.test.tsx          # 単一ファイル
npx vitest run -t "テスト名の一部"

# decitima-api/backend/ で
uv sync
uv run uvicorn app.main:app --reload          # http://localhost:8000
uv run ruff check .
uv run pytest                                  # 統合テストは除外される(-m 'not integration')
uv run pytest -m integration                   # 要 docker compose up postgres redis
uv run pytest tests/unit/test_x.py::test_name  # 単一テスト
uv run alembic upgrade head

# decitima-api/ で(Docker 開発環境一式)
docker compose up --build
```

## リポジトリをまたぐ連携

- UI → API は `decitima-ui/src/lib/api/client.ts` の `apiFetch<T>()` 経由。接続先は `NEXT_PUBLIC_API_URL`(未設定時 `http://localhost:8000`)。
- API はデフォルトで `:8000` を公開。UI をローカル起動して API と繋ぐ場合、API 側(または docker compose)を先に立ち上げる。
- 認証は JWT(access + refresh)。API 側の契約は `decitima-api` の `app/api/routes/auth.py` と `app/schemas/auth.py`、UI 側のトークン保持は `decitima-ui/src/components/auth/auth-store.ts`。


## Notes

### 実装段階での検討事項と採用した方針、採用理由

- **既存 LLM チャット機能を Phase 10 まで route 無効化(コードは保持)** — README で LLM は Phase 10 開始。テンプレート由来の `/chat` を router 集約から外し、`app/ai/` と関連モデル/マイグレーションは Phase 10 の土台として残す。今削除して作り直すより、既存の LangGraph 構成・構造化出力パターンを流用できる方が学習・実装コストが低い。
- **アルゴリズムは 2 トラック(手実装 + 産業ソルバー)を同一インターフェースで並存** — 学習/ポートフォリオ価値(手実装)と実務での実規模対応(OR-Tools 等)を両立させるため。単一インターフェースにすることで Phase 3 ベンチ・Phase 13 比較の基盤がそのまま「手実装 vs ソルバー」比較に使える。詳細は「設計上の決定事項」節。
- **ワークスペースルートを `decitima-project` として git 化、ui/api は `.gitignore` 除外** — `decitima-project` は全体説明と教材のみを持ちアプリコードを置かない方針のため、submodule での版固定は不要。ネストした git のコミット連動は起きない(gitlink は使わない)。

#### Phase 0(設計フェーズ)の主要決定 — 詳細は `textbook/Phase-0/`

- **共通スキーマはハイブリッド型** — `objectives` / `constraints` は全 problem_type 共通の型付き語彙、`data` / `assignments` は `problem_type` を判別子にした Pydantic 判別可能ユニオン。ジェネリック(`dict`/`Any`)だと型の恩恵ゼロ、problem_type ごと別モデルだと「共通スキーマ」が崩れる。中間を取り、共通骨格は閉じ問題固有部分は開く。(`Phase-0-2.md`)
- **`domain/` と `algorithms/` を「純粋レイヤー」として新設** — 副作用(I/O・DB・時刻・乱数)を持たない。これが再現性(NFR-1)とテスタビリティ(DB 不要の高速な純粋関数テスト)を生む。乱数使用時は seed を入力に含める。(`Phase-0-3.md`, `Phase-0-9.md`)
- **`AlgorithmStrategy` は Protocol、`solve` は検証しない** — 継承を強制しないので手実装/ライブラリラッパー/テストフェイクが同じ契約に乗る。`solve` は解の生成だけ担当し、制約充足の判定は Verification が別途行う。これで近似アルゴリズムの制約違反を「バグ」でなく「`status=invalid` な候補」として測れる。(`Phase-0-4.md`, `Phase-0-6.md`)
- **Validation(問題定義の妥当性)と Verification(解の制約充足)を別サービスに分離** — 対象・タイミング・失敗の意味・HTTP ステータスがすべて違う。Validation は「明らかに無理」だけ弾きグレーは通す。hard 違反→`status=invalid`、soft 違反→`soft_penalty`。解の制約違反は例外にしない。(`Phase-0-6.md`)
- **Shift Scheduler は中規模で手実装が破綻 → Phase 5 で OR-Tools CP-SAT トラックを計画に織り込む** — バックトラッキングは最悪指数時間。スタッフ 20 × 7 日規模で現実的に終わらない。手実装は「小規模で最適解を出し原理を学ぶ」用途に位置づける。(`Phase-0-5.md`)
- **DB は JSONB 中心 + 検索キーのみカラム化** — ハイブリッドスキーマを完全正規化すると problem_type ごとにテーブルが増殖しマイグレーションが要る。`OptimizationProblem` / `CandidateSolution` 全体を JSONB(`payload`)に、`problem_type` / `status` / `algorithm_name` だけカラムに。テスト SQLite 向けに `JSON().with_variant(JSONB(), "postgresql")`。JSON カラムは書き換えず毎回まるごと代入(ミューテーション追跡の落とし穴回避)。(`Phase-0-8.md`)
- **MVP は同期実行 + タイムアウト、ジョブキューは導入しない(YAGNI)** — Celery/arq はインフラを増やす。MVP の題材は同期で十分。ただし solve 結果は必ず永続化し `solution_id` で引ける設計にして、将来の非同期化に備える。(`Phase-0-5.md`, `Phase-0-7.md`)
- **Route/Shift の専用エンドポイントを作らない** — `POST /api/v1/solve` に `problem_type` 付きの `OptimizationProblem` を渡すだけ。共通スキーマ設計の狙いどおりの姿。(`Phase-0-7.md`)
- **Phase 0 で decitima-api に低リスク整備のみ適用** — chat ルート無効化(コード保持)/ `app/domain/`・`app/algorithms/` の空パッケージ骨子(docstring のみ)/ `PROJECT_NAME` を "DeciTima API" に / `decitima-api/CLAUDE.md` に固有レイヤー節。スキーマ・インターフェースの実装は Phase 1。ruff・pytest(26 passed)グリーンを確認済み。
- **制約は `ConstraintBase` + サブタイプ + `GenericConstraint` に分割** — 「基底で `kind: str`、サブクラスで `kind: Literal[...]`」は pyright / Pylance の standard モードで `reportIncompatibleVariableOverride` 警告が出る(実行時は問題なし)。基底 `ConstraintBase` は共通フィールド(severity / penalty / description)だけ持ち、判別子 `kind` は各サブタイプが宣言。ad-hoc な `kind` 用に `GenericConstraint(kind: str)`。`constraints` の要素型は `AnyConstraint`(サブタイプ + `GenericConstraint` の `union_mode="left_to_right"` ユニオン、`: TypeAlias` 明示)。(`Phase-0-2.md` §4 / §4.4)

#### 質問・相談ログ

進行のルール #8 に従い、ユーザーからの質問・相談と回答を記録する。

**Q1. サブパッケージに `__init__.py` は必要か / 共通スキーマのファイル分割**

1. **Phase**: Phase 0(Phase 0-2 の実装中)
2. **質問**: `samples/problem_schema.py` の共通スキーマを「共通 / Route Planner / Shift Scheduler」でファイル分割し、`schemas/problems` フォルダで管理したい。この場合サブフォルダに `__init__.py` は必要か。フォルダ名も提案してほしい。
3. **回答と対応方針**:
   - `__init__.py` は**必要**。理由: (a) `decitima-api` の全パッケージが持ち一貫する、(b) pytest / ruff / mypy / Alembic autogenerate が明示的な regular package で予測どおり動く(暗黙の namespace package は "duplicate module" 等の原因)、(c) 分割ファイルの re-export(公開窓口)の置き場所になる。
   - 配置先は `app/schemas/` ではなく **`app/domain/`**(Phase 0-3 §2.4: `schemas/` は HTTP 境界専用)。フォルダ名は **`problems`**(複数形、README §17 と整合)。
   - 分割: `problem.py`(Objective / Constraint / OptimizationProblem / ProblemData)/ `route_planner.py` / `shift_scheduler.py` / `__init__.py`。`__init__.py` は明示 import + `__all__`(ruff F401 対策、既存 `app/models/__init__.py` と同じ)。
   - 反映: 進行のルール #7 を追加、`Phase-0-2.md` に §2.5「ファイル構成」を新設、各コードブロックに配置先パスのコメントを追加。

**Q2.（相談)問題タイプを分割したが、ユニオンを組むのに import が必要 ── 統合すべきか**

1. **Phase**: Phase 0(Phase 0-2 の実装中)
2. **相談**: Route Planner と Shift Scheduler を別問題と捉えて `route_planner.py` / `shift_scheduler.py` に分割したが、`problem.py` で `ProblemData = Annotated[RouteData | ShiftData, Field(discriminator="problem_type")]` を組むために分割ファイルを import する必要が生じた。1 ファイルに統合すべきか、分割 + import か。
3. **回答と対応方針**:
   - **分割のまま、`problem.py` が両ファイルを import するのが正しい。統合しない。**
   - `RouteData` と `ShiftData` が互いを import しない(ピアの独立)ことが守れていれば、`problem.py` が両者を束ねるのは**アグリゲータの役割**であり悪い密結合ではない。同型が `app/api/routes/__init__.py`(全ルーター集約)・`alembic/env.py`(全モデル import)・`registry.py`(全 strategy import)にある。
   - 判断基準:「一緒に変わるものを同じファイルに」。`RouteData` / `ShiftData` は別の理由で変わるので分割、`ProblemData` / `OptimizationProblem` は「対応する問題タイプの集合」が変わったとき変わるので `problem.py` に置く。
   - ユニオンを `__init__.py` に置くと `problem.py ↔ __init__.py` が循環するので避ける。
   - あわせて指摘したバグ: `shift_scheduler.py` の `from typing import Literal, Field`(`Field` は pydantic)/ `probrem.py` → `problem.py` リネーム未実施 / `AnyConstraint` 未定義。
   - 反映: `Phase-0-2.md` §2.5 に「分割 vs 統合の判断」を追記。

### 検証で発覚した事象の原因と解決

- **Pylance の `ProblemData` 型式エラー(型式では変数を使用できません / reportInvalidTypeForm)** — 原因は `ProblemData` 自体ではなく、`RouteData` / `ShiftData` の import が Pylance で未解決なこと。ワークスペースを `decitima/`(プロジェクトルート)で開くと `app` パッケージ(`decitima-api/backend/app`、3 階層下)を Pylance が見つけられない。対応: `decitima-api/backend/pyproject.toml` に `[tool.pyright]`(`include = ["app", "tests"]` / `venvPath = "."` / `venv = ".venv"` / `typeCheckingMode = "standard"`)を追加、加えて `decitima/.vscode/settings.json` に `python.analysis.extraPaths: ["decitima-api/backend"]`。適用後「Developer: Reload Window」。この設定で再発しない。bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` にもなるので絶対 import 必須。この `[tool.pyright]` と `.vscode/settings.json` は「開発環境に必須の tooling 設定」であり、`fastapi-langchain-template` への還元候補。
- **テンプレート由来の型債務** — `typeCheckingMode = "standard"` を入れたところ、テンプレート由来のコード(`app/ai/**` の `GraphState` 部分構築、`tests/unit/test_ai_graph_nodes.py` / `test_auth_service.py` のテストフェイク、`app/repositories/conversation.py` の `get_by_id` override)に既知の型エラーが出た。DeciTima の新規コードは standard で厳格に保ちつつ、これらは `[tool.pyright]` の `ignore` で当面抑制。Phase 10(`app/ai` 作り替え)とテスト基盤整備で解消し、`fastapi-langchain-template` へ還元する。

### 本プロジェクトの進行方法についての所感

進行のルール #10 に従い、気づいた点を随時追記する(課題には提案を対で書く)。

**特徴とメリット**

- AIに全てのコーディングを任せるのではなく、コーディング作業はユーザーの手で行う。
  作業の中でユーザーの疑問や改善点はclaudeに質問・相談することで教材やコードに反映されるため、
  進行の過程で教材を含むプロジェクトが洗練されていく。
- Phase毎に教材とサンプルコードを生成するため、実装途中で発生した変更は後のPhaseにも反映される。
  そのため、大きなやり直し作業が発生するリスクを抑えられる。
- (Claude 観察)「教材 → 実装」の一方向でなく、**ユーザーが手を動かして当たった問題**(型チェッカー
  の警告、import の落とし穴など)が質問・相談を経て教材へ還流する双方向フィードバックループが
  機能している。例: `AnyConstraint` / `ConstraintBase` の設計改善は、実装時に pyright の
  `reportIncompatibleVariableOverride` 警告に当たったことが起点。
- (Claude 観察)教材の設計判断が `textbook/Phase-N/samples/*.py` で `uv run python` / pyright に
  よって実検証されるため、「机上の空論」で終わりにくい。

**課題と提案**

- **やり直しリスクは 0 にできない / 事前理解のハードル**(ユーザー記)。
  コーディング着手前にユーザーが設計を理解し疑問・改善点を事前に解消しておく必要があるが、
  学習を兼ねた進行のためハードルが高い。
  - 提案(採用): 各 Phase の教材生成後・実装着手前に「実装前チェックリスト」
    (作るファイル / 各クラス・関数の責務 / テスト観点)を `phase-<N>-index.md` に置き、
    そこで疑問を出し切ってから実装に入る(進行のルール #11)。
- **教材 Markdown・samples・実コードの三重管理**(Claude 記)。
  同じ定義が 3 箇所に存在し、変更時に同期ズレが起きやすい(今セッションで `probrem.py` の綴り、
  `AnyConstraint` 未定義、`Field` の import 元ミス等が実コード側だけで発生した)。
  - 提案(採用): 教材 Markdown は長いコードブロックを持たず「要点抜粋 + samples 参照」に寄せ、
    samples を実装の初期状態=単一の真実源とする(進行のルール #3、Phase 1 から)。
- **tooling / 環境設定の知見がコードに現れず埋もれる**(Claude 記)。
  Pylance の解析ルート問題のような知見はコードに残らず、環境が変わると再発する。
  - 提案(採用): `[tool.pyright]`(`decitima-api/backend/pyproject.toml`)+ ルート
    `.vscode/settings.json` を明示管理し、開発環境セットアップ手順を `decitima-api` の
    README / CLAUDE.md に記載。テンプレートへの還元候補として扱う。