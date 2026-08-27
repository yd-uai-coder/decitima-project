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
3. 提示するサンプルコードはtextbookフォルダの各Phaseフォルダ内に保存する。
4. 実装段階での検討事項や、検証段階で発覚した事象はCLAUDE.mdのNotes欄に記録していく
5. ユーザーの「Phase#を開始する」というプロンプトでそのPhaseのtextbookを生成する。

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

### 検証で発覚した事象の原因と解決