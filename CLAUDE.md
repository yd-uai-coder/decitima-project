# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発ポリシー

この開発・学習手法を **CL(Curriculum Loop)開発** と呼ぶ(定義は Notes の「この開発・学習手法の呼称」)。

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
2. 学習教材は各Phaseの中で章立てする。**構成は `phase-<N>-index.md`(インデックス)+ `Phase-<N>-0.md`(概観)+ `Phase-<N>-1.md` 以降(作業単位ごと)。章番号は作業単位番号に一致させる**(概観 = 0、作業単位 M = 章 M)。設計フェーズ(Phase 0)は作業単位を持たないので `Phase-0-0.md`(概観)+ `Phase-0-1.md` 以降(設計トピックの逐次解説)。
3. 教材で提示するコードは、長いコードブロックを Markdown に直書きせず「要点の抜粋 + `textbook/Phase-<N>/samples/` のファイル参照」とする。samples を「実装の初期状態(単一の真実源)」と位置づけ、ユーザーが `decitima-api/app/`(または `decitima-ui/src/`)へ写経・改変して実装する。これで「教材 Markdown / samples / 実コード」の三重管理を避ける。以前の Phase の既存教材は設計フェーズのスケッチとして残すが、後続 Phase で**提示コード・設計・決定事項**に変更が生じた箇所には `[Phase <N> 改訂]` マーカーを付す(ルール #12)。教材の**構成・体裁・番号**の変更(章のリネーム、節の再編等)はマーカーを付けず内容で上書きする。
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
11. 各 `phase-<N>-index.md` に「実装前チェックリスト」を置く。内容: その Phase で作成するファイル一覧 / 各クラス・関数の責務 1 行 / テスト観点。Phase 教材の生成後・実装着手前に、ユーザーがこれで疑問を出し切ってから実装に入る。行キーは作業単位番号(章番号と一致)。
12. 後続 Phase で、以前の Phase の**提示コード・設計・決定事項**に変更が生じたら:
    1. 変更後の内容は当該後続 Phase の教材に通常どおり書く。
    2. **変更元(以前の Phase の該当箇所)に定型の改訂マーカーを付す**。目的は「変更前後でどんな問題が解決されるか」を記録に残すこと。以前の本文・コードは残し、マーカーで差分を示す(遡及的な全面書き換えはしない)。
       - `.md`: 該当箇所の直後に blockquote `> **[Phase <N> 改訂]** 当初〈X〉→ 現在〈Y〉。理由(解決される問題)〈…〉。詳細 `Phase-<N>-*.md` §〈…〉。`
       - `.py`(samples): 冒頭 docstring の直後にコメントブロック `# [Phase <N> 改訂] …`。コードはそのまま残す。
    3. 変更元 Phase の `phase-<M>-index.md` に「後続 Phase での改訂」節を設けて 1 行追記し、`CLAUDE.md` の Notes にも要点を残す。
    - **教材の構成・体裁・番号の変更**(章のリネーム、節の再編、TOC 更新、参照リンクの張り替え等)は改訂マーカーの対象外。マーカーを付けず内容で上書きし、決定の記録は Notes / 質問ログ(#4 / #8)に残す。
13. 各章は、その章で**新規作成する全ファイル**を「責務 1 行 + 中身の要点(型・シグネチャ・非自明な判断)」で解説する。ファイル構成ツリーに列挙するだけで解説を省略しない。各章の冒頭に「この章で新規作成するファイル」を明記する。教材生成後、章の解説とサンプル/実装前チェックリストのファイル一覧を突き合わせ、漏れが無いか確認する。



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
- **制約は `ConstraintBase` + サブタイプ + `GenericConstraint` に分割** — 「基底で `kind: str`、サブクラスで `kind: Literal[...]`」は pyright / Pylance の standard モードで `reportIncompatibleVariableOverride` 警告が出る(実行時は問題なし)。基底 `ConstraintBase` は共通フィールド(severity / penalty / description)だけ持ち、判別子 `kind` は各サブタイプが宣言。ad-hoc な `kind` 用に `GenericConstraint(kind: str)`。`constraints` の要素型は `AnyConstraint`(サブタイプ + `GenericConstraint` の `union_mode="left_to_right"` ユニオン、`: TypeAlias` 明示)。(`Phase-0-2.md` §4 / §4.4)【Phase 1 で `: TypeAlias` → PEP 695 `type` 文に変更。`Phase-0-2.md` に改訂マーカー付与(ルール #12)】
- **アルゴリズムスコープを確定 + `AlgorithmStrategy` とプリミティブの 2 層** — 25 項目の網羅性確認から、① 有効性・代替可能性 ② 全体設計への影響 で採否を判断。追加: 差分法(imos 法、プリミティブ)/ Bellman-Ford(`route_planning` の Strategy)/ Floyd-Warshall(全点対距離、プリミティブ、Travel Planner が内部利用)/ 全探索・ビット全探索(明記)。**2 層**: 問題まるごとを解くものは `AlgorithmStrategy`(registry に載る)、部品・技法(二分探索・ツーポインタ・累積和・差分法・Union-Find・Floyd-Warshall・再帰・分割統治 等)は**アルゴリズム・プリミティブ**として素の純粋関数で実装しストラテジーの内部で使う(registry に載らない)。MST は新 `problem_type` `network_design` として追加(Phase 4、Kruskal / Prim / Union-Find)。README §8 を英名（和名）+ 担当 Phase で改訂、§12.6 Network Designer を追加。(`Phase-0-4.md` §2.4 / `Phase-0-2.md` §8.1 / README §8・§12・§19)

#### Phase 1(実装フェーズ)の主要決定 — 詳細は `textbook/Phase-1/`

- **Phase 1 教材は作業単位 1-1〜1-7 に沿った 7 章 + samples ツリー** — samples は実 `decitima-api/backend/` に重ねる前提の `app/...` レイアウト(絶対 import)。ユーザーがファイル単位で写経する。検証は decitima-api の venv を使ったオーバーレイで `uv run pytest`(89 passed / 3 integration deselected)・`ruff check`(clean)・`uvx pyright`(0 errors)。(`phase-1-index.md`, `samples/README.md`)
- **型エイリアスは `: TypeAlias` から PEP 695 の `type` 文へ変更** — Phase 0-2 §4.4 は `AnyConstraint: TypeAlias = Annotated[...]` としていたが、ruff `UP040` が非推奨。`type X = Annotated[..., Field(discriminator=...)]` は Pydantic 2.13 で判別可能ユニオン・`union_mode` を正しく解決し、pyright も型として扱う(`: TypeAlias` が必要だった理由が消える)。`decitima-api` の PEP 695 ジェネリクス採用と一貫。Phase 0 の samples はスケッチとして遡及しない。(`Phase-1-1.md` §2.1)
- **`select_strategy` は registry(純粋)ではなく `app/services/algorithm_selection.py` に置く** — Phase-0-4 §6 スケッチは `registry.py` に置き `NoAlgorithmError` を送出していたが、それは `AppError` 派生(`app/services/errors.py`)であり、`app/algorithms/` が import すると「algorithms → services」の逆流(Phase-0-3 §2.2)。registry.py は純粋のまま `find_strategy`(該当なし → `None`)を持ち、services 層の `select_strategy` が `None` のとき `NoAlgorithmError` を送出する。(`Phase-1-2.md` §3)
- **Phase 1 の Validation / Verification は route_planning 限定の最小実装を solve に配線** — README では Validation/Verification は Phase 2 だが、`SolveService` のライフサイクル(Phase-0-3 §3)にステージとして組み込まれている。Phase 1 は枠(`_CHECKERS` ディスパッチ、`_SEMANTIC_CHECKS` 相当)を通し、中身は route のみ(Validation: 存在・端点・BFS 到達可能性 / Verification: 経路構造 + `forbidden`・`required_inclusion` チェッカー)。shift・全 kind・`POST /verify`・invalid 解ハンドリング・`verifications` テーブルは Phase 2 の 7 単位に分割(`Phase-1-7.md` §5)。(`Phase-1-0.md` §6 / `Phase-1-6.md`〜`Phase-1-7.md`)
- **`network_design` は Phase 1 samples から外し Phase 4 に送る** — Phase 0 の `problem_schema.py` は 3 メンバーユニオンだったが、`phase-0-index.md` の 1-1 は「MVP は route / shift の 2 つ」。Phase 1 の `OptimizationProblem.problem_type` / `ProblemData` / `SolutionData` は 2 メンバー。追加手順は `Phase-1-1.md` §5。(`Phase-1-1.md` §2.2)
- **`OptimizationProblem` に `problem_type == data.problem_type` の `model_validator` を追加** — Phase-0-2 §5.3 が「一致は model_validator でチェック(Phase 0-6)」としていたものを Phase 1 で実装(Input Validation として Pydantic に寄せる)。(`Phase-1-1.md` §2)
- **objectives(多目的の重み付き和の評価器)は Phase 1 では作らない → Phase 5 送り** — 当初 `domain/objectives/weighted_sum.py` を Phase 1 に入れたが、(a) `phase-0-index.md` の実装前チェックリスト 1-1〜1-7 に objectives が含まれない、(b) Phase 1 で registry に載る唯一の strategy(Dijkstra)は単一目的で消費者もテストも無い、ため投機実装として撤回。初の多目的ストラテジー(Phase 5 の Shift Scheduler = Greedy / Backtracking)を実装するときに追加する。`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の「Phase 1」表記には `[Phase 1 改訂]` マーカーを付与(ルール #12)。(`Phase-1-1.md` §1 の注記 / `Phase-1-7.md` §5)
- **solve のタイムアウトは `asyncio.wait_for(asyncio.to_thread(strategy.solve, ...))`** — 同期・純粋な `solve` をスレッドに逃がして監視。超過で `SolveTimeoutError`(504)。タイムアウトしてもスレッド自体は止められない(MVP の割り切り。Phase-0-5 §5)。(`Phase-1-6.md` §4)

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

**Q3.（Phase 1 開始時の確認)教材の章立ての粒度 / samples の置き方**

1. **Phase**: Phase 1(教材生成の開始時)
2. **質問**: (a) Phase 1 教材の章立てをどの粒度にするか(7 章 / 5 章 / 9 章)。(b) Phase 1 の `samples/` を実 `app/` ツリーの鏡写しにするか、Phase 0 と同じフラット構成にするか。
3. **回答と対応方針**:
   - (a) **作業単位に沿った約 7 章**(`phase-0-index.md` の実装前チェックリスト 1-1〜1-7 と 1:1)。1-2 と 1-3 の相当が Protocol/registry と探索プリミティブで分かれ、1-6/1-7 を 1 章に束ねた計 7 章 + 概観(→ Q6 で章番号を作業単位に整列し、概観 `Phase-1-0` + `Phase-1-1`〜`1-7` の 8 章に再構成)。
   - (b) **実 `app/` ツリーを鏡写し**(`textbook/Phase-1/samples/app/domain/problems/problem.py` のように、本番と同じ相対パス・絶対 import `from app...`)。decitima-api の venv でそのまま `uv run pytest` / `uvx pyright` が通り、ユーザーはファイル単位でコピーするだけ。進行のルール #9 の検証手順に一致。検証は decitima-api/backend の複製に overlay して実施。
   - 反映: `Phase-1-0.md`〜`Phase-1-7.md` + `phase-1-index.md` + `samples/`(README 付き)を生成。

**Q4.（Phase 1 生成後の指示)samples を新規ファイルのみに絞る / 章は取り扱うファイルのみ提示**

1. **Phase**: Phase 1(教材生成の直後)
2. **指示**: (a) 各章では、その章が取り扱うサンプルファイルだけを提示する。(b) `textbook/Phase-1/samples/` から Phase 1 に関係ないファイルを削除する。
3. **回答と対応方針**:
   - samples から既存 `decitima-api` ファイルの全文コピー 5 つ(`app/core/config.py` / `app/services/errors.py` / `app/models/__init__.py` / `app/api/routes/__init__.py` / `app/domain/objectives/__init__.py`)と、投機実装だった `app/domain/objectives/weighted_sum.py` を削除。samples = **Phase 1 の新規ファイルのみ**。
   - 既存ファイルへの追記は各章に差分として明示(章は元々ほぼその形。`Phase-1-2` §4 / `Phase-1-5` §3 / `Phase-1-6` §1 / `Phase-1-7` §3)。各章の「対応サンプル」行も新規作成ファイルだけを列挙。
   - objectives 評価器は Phase 5 送り(上の「主要決定」項)。
   - overlay 検証時は config / errors / models/__init__ / api/routes/__init__ の 4 点の追記を複製側へ適用してから pytest/ruff/pyright を回す(89 passed / 3 deselected、clean、0 errors を再確認)。
   - 反映: `Phase-1-1` `Phase-1-2` `Phase-1-5` `Phase-1-6` `phase-1-index` `samples/README.md` `CLAUDE.md` を更新、commit `93c3302` を amend。

**Q5.（Phase 1 生成後の指示)以前の Phase への変更は「改訂マーカー」で以前の Phase にも反映する**

1. **Phase**: Phase 1(教材生成の直後)
2. **指示**: `Phase-1-1.md` §2.1(`: TypeAlias` → `type` 文)/ §2.2(network_design は Phase 4)の変更を Phase 0 にも反映する。その際「当初より変更があったことがわかるように」記載する。以降、以前の Phase の内容から変更が生じた場合も同様の扱いとする。
3. **回答と対応方針**:
   - 進行のルールに **#12** を新設(後続 Phase での変更は変更元 Phase の該当箇所に定型マーカー `[Phase <N> 改訂]` を付す。本文・コードは残し差分を注記。index に「後続 Phase での改訂」節、Notes にも記録)。ルール #3 の「遡及リライトせず」を #12 に合わせて修正。
   - Phase 0 に反映: `Phase-0-2.md` §4.4・§5.3・§6・§8.1・§2.5、`Phase-0-3.md` §2.3、`textbook/Phase-0/samples/problem_schema.py`(冒頭コメント)、`phase-0-index.md`(「後続 Phase での改訂」節)。
   - 反映した改訂: ① `: TypeAlias` → PEP 695 `type` 文、② network_design を Phase 1 のユニオンから外し Phase 4 へ、③(同カテゴリの未処理分)objectives 評価器を Phase 1 → Phase 5。
   - マーカー形式は `[Phase <N> 改訂]`(greppable、絵文字なし)。

**Q6.(Phase 1 生成後の指示)章内で作成する全ファイルの網羅的解説 / 章番号を作業単位に整列**

1. **Phase**: Phase 1(教材生成後)
2. **指示**: (a) `Phase-1-2.md`(作業単位 1-1)が `solutions/route_planner.py`・`shift_scheduler.py` に触れていない。各章はその章で作成する全ファイルを網羅的に解説する(設計理解の補完)。生成時にこれを確認する。(b) 章番号(`Phase-1-1`…)と作業単位(`1-1`…)が 1 ズレていて混乱する。概観章を `Phase-1-0` にし、章番号 = 作業単位番号にそろえる。新構成は他の Phase にも適用。(c) 改訂マーカー(ルール #12)は「提示コードの変更で解決される問題を記録する」趣旨。構成変更は上書きでよい。
3. **回答と対応方針**:
   - ルール #13 を新設(各章は新規作成ファイルを網羅的に解説。冒頭に「この章で新規作成するファイル」)。ルール #2 を「概観 = `Phase-N-0`、章番号 = 作業単位番号」に、#12 に「構成・体裁・番号の変更はマーカー対象外・上書き」を明記。
   - 案1(番号を整列、作業単位概念は残す)を採用。案2(作業単位廃止)は Phase-0-9 §7 等への波及が大きく見送り。
   - Phase 1: `Phase-1-1`→`Phase-1-0`、`1-2`→`1-1`…`1-6`→`1-5` にリネーム(git mv)。旧 `Phase-1-7`(作業単位 1-6+1-7)を新 `Phase-1-6`(1-6)/ 新 `Phase-1-7`(1-7 + Phase 2 引き継ぎ)に分割。参照(章リンク・§)を一括で上書き更新(マーカーは付けない)。`Phase-1-1` に「解の葉モジュール」節と問題葉のフル解説を追加。
   - Phase 0: 章番号は変えず `Phase-0-0.md`(概観)を新設。`Phase-0-*` の `[Phase 1 改訂]` マーカーは本文を残し章参照のみ新番号に。
   - 反映: Phase-1 全 8 章 + `phase-1-index.md` + `samples/README.md` + `CLAUDE.md`(ルール #2/#3/#11/#12/#13)+ `Phase-0-0.md` 新設 + `Phase-0-2/0-3/phase-0-index/problem_schema.py` の参照更新。

### 検証で発覚した事象の原因と解決

- **Pylance の `ProblemData` 型式エラー(型式では変数を使用できません / reportInvalidTypeForm)** — 原因は `ProblemData` 自体ではなく、`RouteData` / `ShiftData` の import が Pylance で未解決なこと。ワークスペースを `decitima/`(プロジェクトルート)で開くと `app` パッケージ(`decitima-api/backend/app`、3 階層下)を Pylance が見つけられない。対応: `decitima-api/backend/pyproject.toml` に `[tool.pyright]`(`include = ["app", "tests"]` / `venvPath = "."` / `venv = ".venv"` / `typeCheckingMode = "standard"`)を追加、加えて `decitima/.vscode/settings.json` に `python.analysis.extraPaths: ["decitima-api/backend"]`。適用後「Developer: Reload Window」。この設定で再発しない。bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` にもなるので絶対 import 必須。この `[tool.pyright]` と `.vscode/settings.json` は「開発環境に必須の tooling 設定」であり、`fastapi-langchain-template` への還元候補。
- **テンプレート由来の型債務** — `typeCheckingMode = "standard"` を入れたところ、テンプレート由来のコード(`app/ai/**` の `GraphState` 部分構築、`tests/unit/test_ai_graph_nodes.py` / `test_auth_service.py` のテストフェイク、`app/repositories/conversation.py` の `get_by_id` override)に既知の型エラーが出た。DeciTima の新規コードは standard で厳格に保ちつつ、これらは `[tool.pyright]` の `ignore` で当面抑制。Phase 10(`app/ai` 作り替え)とテスト基盤整備で解消し、`fastapi-langchain-template` へ還元する。
- **Phase 1 samples の検証は decitima-api への overlay で行う(Claude 側の作業)** — `textbook/Phase-1/samples/` は実 `app/` ツリーの鏡写しで、`from app...` / `from tests...` の絶対 import を使う。単体では import が解決しないため、`decitima-api/backend` を `.venv` 除外で複製し `.venv` をシンボリックリンク、`samples/{app,tests,alembic/versions}` を overlay してから `./.venv/bin/python -m pytest` / `./.venv/bin/ruff check` / `ruff format --check` / `uvx pyright` を実行する。**samples には Phase 1 の新規ファイルだけを置く**方針なので(下項)、既存ファイルへの 4 点の追記(`app/core/config.py` の `SOLVE_RATE_LIMIT_*`・`SOLVE_TIMEOUT_SECONDS` / `app/services/errors.py` の import と 4 クラス / `app/models/__init__.py` の `Problem`・`Solution` / `app/api/routes/__init__.py` の 3 ルーター)を overlay 側に適用してから実行する。Phase 1 では pytest 89 passed(3 integration deselected)/ ruff・format clean / pyright 0 errors を確認。
- **`textbook/Phase-1/samples/` は Phase 1 で新規作成するファイルのみ** — 既存 `decitima-api` ファイルへの追記(`app/core/config.py` / `app/services/errors.py` / `app/models/__init__.py` / `app/api/routes/__init__.py` / `alembic/env.py`)は samples に全文コピーを置かず、各章に差分として示す。当初計画どおり(生成時に全文コピーで逸脱していたのを訂正)。samples の全文コピーは意図せぬ差分(全角括弧の書き換え等)も持ち込むため。各章の「対応サンプル」行も、その章で新規作成するファイルだけを列挙する。
- **Phase 1 の軽微な pyright / 実装上の対応** — (1) `binary_search` の `_Comparable` プロトコルは `__lt__(self, other: Any)` にする(`object` だと組み込み比較型が満たせず standard で警告)。(2) テストで `FakeRedis` を `SolveService` に渡す箇所は `cast(Redis, FakeRedis())`(既存 `test_auth_service.py` は pyright ignore で処理していたが、Phase 1 は cast で明示)。(3) 判別可能ユニオンの消費側テストは `assert isinstance(sol.assignments, RouteSolution)` で絞り込む(サンプルの `_route(sol)` ヘルパ)。

### この開発・学習手法の呼称 ── CL(Curriculum Loop)開発

本プロジェクトの進行方法を **CL(Curriculum Loop)開発** と呼ぶ(略称 CL、正式名 Curriculum Loop 開発)。

> AI が Phase 単位で学習教材とサンプルコードを著述し、人間が手でコードを書く。実装で当たった
> 疑問・改善点が質問・相談を通じて教材とサンプルに還流し、教材とプロジェクトが一つのループの
> 中で共に洗練されていく開発・学習手法。

**2 本柱**

1. **双方向の還流ループ**: 「教材 → 実装」の一方向でなく「実装で当たった摩擦 → 教材・サンプルの改訂」。
   次の Phase はより洗練された状態で始まり、大きなやり直しのリスクを抑える。
2. **役割分担**: AI = 設計・教材・サンプル・トレードオフの説明 / 人間 = 実装のタイピング。
   AI がコードを書く `vibe coding` の対極。

**既存概念との関係**

- Codecademy の「Vibe Learning」(2025)に隣接するが、あちらは AI 生成コードを人間が理解する構図。
  CL 開発は人間が実装を書く点で逆。
- 下敷き: cognitive apprenticeship(専門家がモデルを示し学習者が実践)、worked examples 効果、
  spec-driven development、project-based learning。この組み合わせを 1 手法として束ねた前例は
  調べた範囲で見当たらなかったため命名した。

**実践**

- 手順は「進行のルール」#1〜#11(Phase 教材・サンプルの生成、コード配置パスの明記、
  質問・相談ログ、サンプルへの変更反映、実装前チェックリスト等)。
- 決定・知見の記録は本 Notes の各節(実装段階の検討事項 / 質問・相談ログ / 検証で発覚した事象 /
  進行方法の所感)。

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
- (Claude 観察 / ユーザー指示で制度化)後続 Phase での設計変更が、**変更元の以前の Phase にも
  `[Phase N 改訂]` マーカーで戻る**(進行のルール #12)。双方向還流ループの明文化。以前の Phase は
  設計スナップショットとして読めるまま、どこがどう変わったか(当初 → 現在 → 理由 → 参照先)を
  追える。`grep -rn "\[Phase .* 改訂\]" textbook/` で全変更点を一覧できる。

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
- **samples が「実 app/ ツリーの鏡写し」だと単体で動かせない**(Claude 記、Phase 1)。
  Phase 1 の samples は `from app...` 絶対 import を使うため、`textbook/Phase-1/samples/` 単体では
  import が解決せず、pytest / pyright を回すのに `decitima-api/backend` への overlay(複製 + シンボ
  リックリンクした `.venv` + `rsync`)が要る。手順が一手多い。
  - 提案(未採用・ユーザー判断): (a) `samples/` に `conftest.py` + `pyrightconfig.json` を置き、
    `samples/` をルートに単体で回せるようにする(overlay 不要だが samples 内に検証設定が増える)。
    (b) `decitima-api/backend` 側に `pytest` の追加 testpath を切り、samples を直接収集できるようにする。
    (c) 現状どおり Claude が overlay で検証し、手順は `samples/README.md` に明記(今回採用)。
  - 追記(ユーザー指示で対応済み): samples は **Phase 1 の新規ファイルのみ**にし、既存ファイルへの
    追記は全文コピーを置かず各章の差分に一本化した。overlay 検証時はその追記を複製側へ適用する。
    副次効果として「全文コピーが意図せぬ差分(全角括弧の書き換え等)を持ち込む」問題も解消。
- **教材内のコードと samples の同期は「教材=抜粋」でほぼ解消したが、抜粋の追従は残る**(Claude 記)。
  進行のルール #3 で実コードは samples に一本化できたが、章の Markdown に載せる「要点の抜粋」は
  依然 samples を手で切り出したもので、samples を直したら抜粋も直す必要がある。
  - 提案(未採用・ユーザー判断): 抜粋は「シグネチャ + 1〜2 行の核心」に絞り、完全な関数本体は
    載せない(すでにおおむね実施)。さらに減らすなら抜粋にも `samples/<path>:<lineno>` の参照を
    付け、ズレたときに気づけるようにする。