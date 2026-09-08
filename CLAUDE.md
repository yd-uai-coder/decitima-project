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
2. 学習教材は各Phaseの中で章立てする。**構成は `Phase-<N>-introduction.md`(導入)+ `Phase-<N>-1.md` 以降(作業単位ごと。章番号 = 作業単位番号)**。別建ての概観章(`Phase-<N>-0.md`)やインデックスは作らない ── 概観・目的・章一覧・実装前チェックリストはすべて `Phase-<N>-introduction.md` に集約する。設計フェーズ(Phase 0)は作業単位を持たないので `Phase-0-introduction.md` + `Phase-0-1.md` 以降(設計トピックの逐次解説)。
3. 教材で提示するコードは、長いコードブロックを Markdown に直書きせず「要点の抜粋 + `textbook/Phase-<N>/samples/` のファイル参照」とする。samples を「実装の初期状態(単一の真実源)」と位置づけ、ユーザーが `decitima-api/app/`(または `decitima-ui/src/`)へ写経・改変して実装する。これで「教材 Markdown / samples / 実コード」の三重管理を避ける。以前の Phase の既存教材は設計フェーズのスケッチとして残すが、後続 Phase で**提示コード・設計・決定事項**に変更が生じた箇所には「以降 Phase で修正予定」マーカーを付す(形式はルール #12。読み手は各 Phase の時点では samples のまま実装してよい)。教材の**構成・体裁・番号**の変更(章のリネーム、節の再編等)はマーカーを付けず内容で上書きする。
4. 実装段階での検討事項や、検証段階で発覚した事象はCLAUDE.mdのNotes欄に記録していく
5. ユーザーの「Phase#を開始する」というプロンプトでそのPhaseのtextbookを生成する。
6. Phase毎に**導入ファイル `Phase-<N>-introduction.md`** を各Phaseフォルダ直下に作成する(従来の `phase-<N>-index.md` および別建ての概観章に代わる。1 本に統合)。内容: フェーズの目的 / パイプライン上の位置づけ・作業章を始める前に理解すべき前提(概観)/ 章一覧(各章のトピック・依存関係・リンク)/ サンプルコード一覧 / 実装前チェックリスト(#11)/ 次のフェーズ。`Phase-<N>-1.md` 以降を読み始める前に、この 1 本で前提を説明しきる。章を追加・変更したらここも更新する。
7. 教材でコードを提案するときは、配置先のファイルパスを各コードブロックの先頭にコメントで明記する(例: `# app/domain/problems/route_planner.py`)。分割するモジュールはパッケージ(`__init__.py` 付き)として示し、`__init__.py` の re-export 形とファイル間の依存方向も示す。既存教材の修正時・以降の Phase でも同様。
8. ユーザーが Claude に行った質問・相談とその回答を、`## Notes` の `### 実装段階での検討事項と採用した方針、採用理由` 内の `#### 質問・相談ログ` に追記する。各エントリは次の形式:
   1. 疑問が生じた Phase
   2. 質問・相談内容
   3. 回答と対応方針
9. 検討・相談の中で提示するコード(クラス名・シグネチャ・型など)に変更が生じたら、対応する `textbook/Phase-<N>/samples/` のサンプルコードにも同じ変更を反映する。反映後は `uv run python`(decitima-api の環境)で実行確認し、可能なら型チェック(pyright standard)も通す。
10. 本プロジェクトの進行方法について気づいた点(特徴・メリット / 課題 / 課題解決への提案)を `## Notes` の `### 本プロジェクトの進行方法についての所感` に追記する。課題には可能な限り「提案」を対で書く。提案をプロジェクトに組み込むかはユーザーが個別に判断する(Claude は勝手に適用しない)。
11. 各 `Phase-<N>-introduction.md` に「実装前チェックリスト」を置く。内容: その Phase で作成するファイル一覧 / 各クラス・関数の責務 1 行 / テスト観点。Phase 教材の生成後・実装着手前に、ユーザーがこれで疑問を出し切ってから実装に入る。行キーは作業単位番号(章番号と一致)。設計フェーズ(Phase 0)は実装が無いため省略可。
12. 後続 Phase で、以前の Phase の**提示コード・設計・決定事項**に変更が生じたら(重複コードを共通化のために触ってよいかの判断は #17):
    1. 変更後の内容は当該後続 Phase の教材に通常どおり書く。
    2. **変更元(以前の Phase の該当箇所)に定型のマーカーを付す**。目的は 2 つ ── ①「変更前後でどんな問題が解決されるか」を記録に残す、②**カリキュラムを順に読む人が「この Phase の時点では samples のまま実装してよい」と分かる**ようにする。以前の本文・コードは残し、マーカーで差分を示す(遡及的な全面書き換えはしない)。マーカーは 3 種:
       - **A. 後続 Phase で設計が変わる**(samples 本体はその Phase 版のまま)。
         - `.md`: 該当箇所の直後に blockquote
           `> **[以降 Phase で修正予定 ── Phase <N>-<M>]** この節の実装は samples のとおりで進める。Phase <N>-<M> での変更: 当初〈X〉→ 現在〈Y〉。理由(解決される問題)〈…〉。詳細 `Phase-<N>-<M>.md`。`
         - `.py`(samples): 冒頭 docstring の直後にコメント。**コード本体はそのまま**。
           `# [以降 Phase で修正予定 ── Phase <N>-<M>] このファイルの現行版はこのまま(スナップショット)。Phase <N>-<M> で〈…〉。現行版 textbook/Phase-<N>/samples/<path>。`
       - **B. サンプルの後追い修正**(名前ズレの是正など、設計変更でないもの。samples 本体は**書き換え済み**)。「予定」表現は使わない。
         `> **[Phase <N> でサンプル修正 ── 実 backend に同期]** 〈X〉→〈Y〉(設計変更ではない)。以降 samples は〈Y〉。`
       - **C. 「やらないことに確定」**(旧計画を撤回)。
         `> **[Phase <N> で確定 ── 〈…しない〉]** 当初〈…する予定〉→ 撤回。理由〈…〉。`
       - grep 用合言葉: A=`修正予定` / B=`サンプル修正` / C=`で確定`。一覧は `grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/`。
    3. 変更元 Phase の `Phase-<M>-introduction.md` に「後続 Phase での改訂」節を設けて 1 行追記し、`CLAUDE.md` の Notes にも要点を残す(この節名は「完走後に読む差分ログ」の意味なので維持)。
    - **教材の構成・体裁・番号の変更**(章のリネーム、節の再編、TOC 更新、参照リンクの張り替え等)はマーカーの対象外。マーカーを付けず内容で上書きし、決定の記録は Notes / 質問ログ(#4 / #8)に残す。
13. 各章は、その章で**新規作成する全ファイル**を「責務 1 行 + 中身の要点(型・シグネチャ・非自明な判断)」で解説する。ファイル構成ツリーに列挙するだけで解説を省略しない。各章の冒頭に「この章で新規作成するファイル」を明記する。教材生成後、章の解説とサンプル/実装前チェックリストのファイル一覧を突き合わせ、漏れが無いか確認する。
14. 各章の `## テスト観点` 節では、テスト(またはテスト群)ごとに **テスト対象(SUT)/ ドライバ / スタブ(テストダブル)** の関係を明記する。スタブが不要な場合は「スタブ不要 ── 対象が純粋(副作用なし)で外部依存を呼ばないため」のように**理由込みで**書く。狙いは CL 開発の趣旨「テストを通じた設計理解の重要視」── テストダブルの要否がレイヤー設計(純粋 / 副作用)の鏡であることを各章で言語化すること。用語(SUT / ドライバ / スタブ)は初出の章で 1 行定義し、以降の章は関係の明記のみでよい。`Phase-<N>-introduction.md` の実装前チェックリストの「テスト観点」列は対象外(簡潔さを優先)。
15. 各章の samples(実装ファイル + テスト)は、**その章とそれ以前の章で作成したファイルだけで import が解決し、テストが緑になる**ように設計する。集約モジュール(`registry.py` 等、後の章で作るファイルを参照するもの)は、未作成分の import と登録エントリを**コメントアウト**して出荷し `# 作業単位 <N> で有効化` / `# Phase <N>` マーカーを付す。参照先を作る章が「コメントを外す手順」と「正しく配線された」ことのテストを持つ(その章の「この章で新規作成するファイル」に「既存への変更」として明記)。集約の**機構**のテスト(`get_strategies` / `find_strategy` 等)は具体的な後発実装でなく**フェイク**(fixture で登録)で行う。テスト用フィクスチャ(`tests/fixtures/*.py`)も初出の章の作成物として実装前チェックリストに含める。samples のフル検証は「Phase 末まで写経し終えた end 状態」(全マーカーのコメントを外した状態)で回す。
    - **章が新規作成する全ファイルを、その章のテストが少なくとも 1 度は import する**こと(教材生成後・#13 の突き合わせと同時に確認)。3 ファイル作って 1 ファイルしかテストが触っていない、のような穴を作らない ── 写経漏れ・写経ミスをその章のテストで検知できるようにするため。純粋関数は素で、外部依存を注入できる設計(`segment_fn` 等)はフェイクで(#14)。
16. 章が**以前の Phase でテスト済みのコードをリファクタ**(関数の抽出・移動・シグネチャ変更など、公開挙動を変えない整理を含む)する場合:
    - **第一の番人は当該章の第一テスト**。可能なら**統合スモークを 1 本**そこに置き(リファクタした対象の公開 API を素で 1 回呼ぶ)、写経ミスをその章内で赤にする。docstring に「よくある失敗モード → どの行を見るか」を書く(間接的なエラーメッセージほど有効)。
    - 加えて、その章の `## テスト観点` に「**以前の Phase の該当テスト(`test_xxx.py`)を写経後に再実行する**」を明記する ── 補助の番人。**公開挙動が不変**ならそのテストの現行版を当該章の samples に置き(docstring に「before → after の変更点」と「赤なら写経ミス(テストが番人)」を追記。**アサーションは変えない**)、旧 Phase samples の当該テストに #12.2 A/B のマーカー。**公開挙動が変わる**なら、変更前後をコメントで対比した更新版テストを当該章の samples に現行版として置き、旧 Phase samples にマーカー。
    狙いは #15 と対 ── #15 が「その章のファイルだけでテスト緑」を保証するのに対し、#16 は「以前の章のテストが後続章のリファクタで壊れていないか(壊れるなら追従する)」を保証する。#12 が**コード**の遡及マーカーを扱うのに対し、#16 は**テスト**の遡及を扱う。
17. **以前の Phase のコードを共通化のために触ってよいかの判断基準**。後続 Phase が以前の Phase のコードと同じ**ドメインの事実**(式・不変条件・データ構造)を必要とするとき、「コピーして各 Phase に重複させる」か「以前の Phase のコードを抽出・共通化して両者で共有する」かの分岐では **常に共有を選ぶ**。#12 マーカー + #16 現行版テストのコスト(Claude のタスク量が増える)を払ってでも重複を残さない。**触らないもの**: (a) 教材本文の遡及的**全面**リライト(差分はマーカーで示す ── #12。本文・コードは残す) (b) **駆動する新しい消費者がいない**遡及クリーンアップ / 監査(「どこかに重複はないか」と以前の Phase を巡回すること ── Q30 で確定した「遡及監査はしない」) (c) レイヤー境界が要求する分割(`domain → algorithms` の import 禁止による `structure._longest_consecutive_run` vs `patterns/sliding_window` など ── これは重複でなく必然)。**判定の一問**: 「この共通化を今 駆動している、この Phase の実在の消費者は何か」に具体名で答えられれば実施、「将来たぶん」「一般に良い設計だから」なら見送る。#15(前方 ── その章のファイルだけで緑)/ #16(後方 ── 以前の章のテストの追従)と対で、#17 は**以前の章のコードそのものを共有化のために変更してよい条件**を定める。「以前の Phase を過剰に触らない」という明文ルールは無い ── (a)(b) の混同で生まれた過剰な自己制約を防ぐ。



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
| `README.md` | DeciTima の製品ビジョン / 仕様書(日本語・約1500行)。「AI-assisted Decision Optimization Platform」の全体設計、Phase 0〜15 の開発計画、MVP 範囲(Phase 0〜6) | `decitima-project` が追跡 |
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
2. **産業ソルバートラック(実務)** — 実規模でスケールしない問題(Phase 6 Shift Scheduler、Phase 9 Logistics 等)向けに、同じインターフェースの裏で OR-Tools CP-SAT / scipy / networkx を使う実装も用意する。

各 strategy はメタデータに `implementation`(`"handwritten"` / `"library:ortools"` 等)を持つ。両トラックが同一インターフェース・同一スキーマなので、**Phase 3 のベンチマークと Phase 14 の「LLM vs Algorithm」比較がそのまま「手実装 vs 産業ソルバー」比較に拡張できる**(スケール限界・解の品質差・いつソルバーに切り替えるべきかを実測で示す)。

**NumPy / SciPy / pandas をコア層(`app/domain/` `app/algorithms/`)と solve / verify のリクエスト経路には入れない**(プロジェクトの前提。README §8「実装方針 ── 手実装を主軸に、数値ライブラリは境界の裏に」)。ベクトル化数値ライブラリを使うのは 3 つのラベル付き境界の裏だけ ── ① 産業ソルバートラック(networkx / OR-Tools / scipy。`meta.implementation` で区別)② 分析トラック `analysis/`(pandas / matplotlib。dev 依存)③ ベンチ集計(`services/measurement.py` の NumPy のみ)。理由: コア層で NumPy をフル活用すると (a) 手実装が「scipy を読める」証明に格落ち (b) `_ops` 計測が不能になり「手実装 vs 産業ソルバー」比較(Phase 3・14)が土俵を失う (c) Phase 6 の「破綻 → 切り替え」の教訓が消える。速度より 学習・再現性・検証可能性・比較可能性 を優先する整合的な選択。(相談ログ Q19)

ライブラリ依存は必要になった Phase まで追加を遅延する: `networkx`(Phase 4、追加済み)、**`ortools`(Phase 6-7 で `[project].dependencies` に追加済み。CP-SAT。Phase 8/9 で再利用)**、`numpy`(Phase 3 ベンチマーク集計、追加済み)、`pandas` / `matplotlib`(Phase 3、分析トラック `analysis/` の dev 依存、追加済み)、`pulp` / `scipy`(Phase 9 で MILP 化する場合)。

### 既存 LLM チャット機能の扱い

`decitima-api` のテンプレートには LLM チャット機能(`app/ai/` の LangGraph ワークフロー、`POST /chat`、`conversation` / `message` モデル)が含まれるが、README では LLM は **Phase 11〜14**。それまでの Phase 0〜10 では:

- `app/api/routes/__init__.py` の集約から `chat` ルーターを外し、**エンドポイントを無効化**する。
- `app/ai/`・`schemas/chat.py`・`schemas/generation.py`・`conversation` / `message` モデル・既存マイグレーションは **削除せず保持**する(Phase 11 で DeciTima 用ワークフローに作り替える土台)。

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

### 命名: 先頭 `_`(非公開の印)

PEP 8 の「先頭アンダースコア 1 個 = 非公開(internal)」に従う。lint では強制しない(ruff の `N`(pep8-naming)は未有効)── **読み手への約束**。言語が実際に効かせるのは ① `from m import *` が `_` 名を飛ばす ② クラス内 `__name`(2 個)の name-mangling(本プロジェクト未使用)の 2 点だけ。使い分け:

| 形 | 意味 |
| --- | --- |
| `self._attr` | インスタンス属性の非公開。クラスの公開面は公開メソッドだけ(`self._session` / `self._repo` 等)。呼び出し側は `Service(...).method(...)` を使い `._attr` に触らない |
| モジュールレベル `_func` / `_CONST` / `_TypeAlias` | そのモジュールの外から import させない内部部品。モジュールの公開 API = `_` なしの名前(+ `__all__`)(`_soft_penalty` / `_annotate_quality_ratio` / `_Adjacency` 等) |
| `for _ in ...` / `x, _ = pair` | 束縛するが使わない使い捨て変数 |
| `metrics["_ops"]` | **プロジェクト独自**。dict キーに `_` で「診断用の内部指標。目的値ではない・アルゴリズム間で time/memory のように比較しない」を表す |

`_` の有無は「この名前を外から使ってよいか」の設計判断そのもの(例: Phase 1 の `_CHECKERS`(モジュール内)→ Phase 2 の `CHECKERS`(domain の公開レジストリになったので `_` を外した))。末尾 `_`(`type_` 等)はキーワード/組込み衝突回避、`__dunder__` は言語予約で自作しない。(相談ログ Q22)

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

- **既存 LLM チャット機能を Phase 11 まで route 無効化(コードは保持)** — README で LLM は Phase 11 開始。テンプレート由来の `/chat` を router 集約から外し、`app/ai/` と関連モデル/マイグレーションは Phase 11 の土台として残す。今削除して作り直すより、既存の LangGraph 構成・構造化出力パターンを流用できる方が学習・実装コストが低い。
- **アルゴリズムは 2 トラック(手実装 + 産業ソルバー)を同一インターフェースで並存** — 学習/ポートフォリオ価値(手実装)と実務での実規模対応(OR-Tools 等)を両立させるため。単一インターフェースにすることで Phase 3 ベンチ・Phase 14 比較の基盤がそのまま「手実装 vs ソルバー」比較に使える。詳細は「設計上の決定事項」節。
- **ワークスペースルートを `decitima-project` として git 化、ui/api は `.gitignore` 除外** — `decitima-project` は全体説明と教材のみを持ちアプリコードを置かない方針のため、submodule での版固定は不要。ネストした git のコミット連動は起きない(gitlink は使わない)。

#### Phase 0(設計フェーズ)の主要決定 — 詳細は `textbook/Phase-0/`

- **共通スキーマはハイブリッド型** — `objectives` / `constraints` は全 problem_type 共通の型付き語彙、`data` / `assignments` は `problem_type` を判別子にした Pydantic 判別可能ユニオン。ジェネリック(`dict`/`Any`)だと型の恩恵ゼロ、problem_type ごと別モデルだと「共通スキーマ」が崩れる。中間を取り、共通骨格は閉じ問題固有部分は開く。(`Phase-0-2.md`)
- **`domain/` と `algorithms/` を「純粋レイヤー」として新設** — 副作用(I/O・DB・時刻・乱数)を持たない。これが再現性(NFR-1)とテスタビリティ(DB 不要の高速な純粋関数テスト)を生む。乱数使用時は seed を入力に含める。(`Phase-0-3.md`, `Phase-0-9.md`)
- **`AlgorithmStrategy` は Protocol、`solve` は検証しない** — 継承を強制しないので手実装/ライブラリラッパー/テストフェイクが同じ契約に乗る。`solve` は解の生成だけ担当し、制約充足の判定は Verification が別途行う。これで近似アルゴリズムの制約違反を「バグ」でなく「`status=invalid` な候補」として測れる。(`Phase-0-4.md`, `Phase-0-6.md`)
- **Validation(問題定義の妥当性)と Verification(解の制約充足)を別サービスに分離** — 対象・タイミング・失敗の意味・HTTP ステータスがすべて違う。Validation は「明らかに無理」だけ弾きグレーは通す。hard 違反→`status=invalid`、soft 違反→`soft_penalty`。解の制約違反は例外にしない。(`Phase-0-6.md`)
- **Shift Scheduler は中規模で手実装が破綻 → Phase 6 で OR-Tools CP-SAT トラックを計画に織り込む** — バックトラッキングは最悪指数時間。スタッフ 20 × 7 日規模で現実的に終わらない。手実装は「小規模で最適解を出し原理を学ぶ」用途に位置づける。(`Phase-0-5.md`)
- **DB は JSONB 中心 + 検索キーのみカラム化** — ハイブリッドスキーマを完全正規化すると problem_type ごとにテーブルが増殖しマイグレーションが要る。`OptimizationProblem` / `CandidateSolution` 全体を JSONB(`payload`)に、`problem_type` / `status` / `algorithm_name` だけカラムに。テスト SQLite 向けに `JSON().with_variant(JSONB(), "postgresql")`。JSON カラムは書き換えず毎回まるごと代入(ミューテーション追跡の落とし穴回避)。(`Phase-0-8.md`)
- **MVP は同期実行 + タイムアウト、ジョブキューは導入しない(YAGNI)** — Celery/arq はインフラを増やす。MVP の題材は同期で十分。ただし solve 結果は必ず永続化し `solution_id` で引ける設計にして、将来の非同期化に備える。(`Phase-0-5.md`, `Phase-0-7.md`)
- **Route/Shift の専用エンドポイントを作らない** — `POST /api/v1/solve` に `problem_type` 付きの `OptimizationProblem` を渡すだけ。共通スキーマ設計の狙いどおりの姿。(`Phase-0-7.md`)
- **Phase 0 で decitima-api に低リスク整備のみ適用** — chat ルート無効化(コード保持)/ `app/domain/`・`app/algorithms/` の空パッケージ骨子(docstring のみ)/ `PROJECT_NAME` を "DeciTima API" に / `decitima-api/CLAUDE.md` に固有レイヤー節。スキーマ・インターフェースの実装は Phase 1。ruff・pytest(26 passed)グリーンを確認済み。
- **制約は `ConstraintBase` + サブタイプ + `GenericConstraint` に分割** — 「基底で `kind: str`、サブクラスで `kind: Literal[...]`」は pyright / Pylance の standard モードで `reportIncompatibleVariableOverride` 警告が出る(実行時は問題なし)。基底 `ConstraintBase` は共通フィールド(severity / penalty / description)だけ持ち、判別子 `kind` は各サブタイプが宣言。ad-hoc な `kind` 用に `GenericConstraint(kind: str)`。`constraints` の要素型は `AnyConstraint`(サブタイプ + `GenericConstraint` の `union_mode="left_to_right"` ユニオン、`: TypeAlias` 明示)。(`Phase-0-2.md` §4 / §4.4)【Phase 1 で `: TypeAlias` → PEP 695 `type` 文に変更。`Phase-0-2.md` に改訂マーカー付与(ルール #12)】
- **アルゴリズムスコープを確定 + `AlgorithmStrategy` とプリミティブの 2 層** — 25 項目の網羅性確認から、① 有効性・代替可能性 ② 全体設計への影響 で採否を判断。追加: 差分法(imos 法、プリミティブ)/ Bellman-Ford(`route_planning` の Strategy)/ Floyd-Warshall(全点対距離、プリミティブ、Travel Planner が内部利用)/ 全探索・ビット全探索(明記)。**2 層**: 問題まるごとを解くものは `AlgorithmStrategy`(registry に載る)、部品・技法(二分探索・ツーポインタ・累積和・差分法・Union-Find・Floyd-Warshall・再帰・分割統治 等)は**アルゴリズム・プリミティブ**として素の純粋関数で実装しストラテジーの内部で使う(registry に載らない)。MST は新 `problem_type` `network_design` として追加(Phase 4、Kruskal / Prim / Union-Find)。README §8 を英名（和名）+ 担当 Phase で改訂、§12.6 Network Designer を追加。(`Phase-0-4.md` §2.4 / `Phase-0-2.md` §8.1 / README §8・§12・§19)

#### Phase 1(実装フェーズ)の主要決定 — 詳細は `textbook/Phase-1/`

- **Phase 1 教材は作業単位 1-1〜1-7 に沿った 7 章 + samples ツリー** — samples は実 `decitima-api/backend/` に重ねる前提の `app/...` レイアウト(絶対 import)。ユーザーがファイル単位で写経する。検証は decitima-api の venv を使ったオーバーレイで `uv run pytest`(89 passed / 3 integration deselected)・`ruff check`(clean)・`uvx pyright`(0 errors)。(`Phase-1-introduction.md`, `samples/README.md`)
- **型エイリアスは `: TypeAlias` から PEP 695 の `type` 文へ変更** — Phase 0-2 §4.4 は `AnyConstraint: TypeAlias = Annotated[...]` としていたが、ruff `UP040` が非推奨。`type X = Annotated[..., Field(discriminator=...)]` は Pydantic 2.13 で判別可能ユニオン・`union_mode` を正しく解決し、pyright も型として扱う(`: TypeAlias` が必要だった理由が消える)。`decitima-api` の PEP 695 ジェネリクス採用と一貫。Phase 0 の samples はスケッチとして遡及しない。(`Phase-1-1.md` §2.1)
- **`select_strategy` は registry(純粋)ではなく `app/services/algorithm_selection.py` に置く** — Phase-0-4 §6 スケッチは `registry.py` に置き `NoAlgorithmError` を送出していたが、それは `AppError` 派生(`app/services/errors.py`)であり、`app/algorithms/` が import すると「algorithms → services」の逆流(Phase-0-3 §2.2)。registry.py は純粋のまま `find_strategy`(該当なし → `None`)を持ち、services 層の `select_strategy` が `None` のとき `NoAlgorithmError` を送出する。(`Phase-1-2.md` §3)
- **Phase 1 の Validation / Verification は route_planning 限定の最小実装を solve に配線** — README では Validation/Verification は Phase 2 だが、`SolveService` のライフサイクル(Phase-0-3 §3)にステージとして組み込まれている。Phase 1 は枠(`_CHECKERS` ディスパッチ、`_SEMANTIC_CHECKS` 相当)を通し、中身は route のみ(Validation: 存在・端点・BFS 到達可能性 / Verification: 経路構造 + `forbidden`・`required_inclusion` チェッカー)。shift・全 kind・`POST /verify`・invalid 解ハンドリング・`verifications` テーブルは Phase 2 の 7 単位に分割(`Phase-1-7.md` §5)。(`Phase-1-introduction.md` §7 / `Phase-1-6.md`〜`Phase-1-7.md`)
- **`network_design` は Phase 1 samples から外し Phase 4 に送る** — Phase 0 の `problem_schema.py` は 3 メンバーユニオンだったが、`Phase-1-introduction.md` §10 の実装前チェックリスト 1-1 は「route / shift の 2 problem_type」。Phase 1 の `OptimizationProblem.problem_type` / `ProblemData` / `SolutionData` は 2 メンバー。追加手順は `Phase-1-1.md` §5。(`Phase-1-1.md` §2.2)
- **`OptimizationProblem` に `problem_type == data.problem_type` の `model_validator` を追加** — Phase-0-2 §5.3 が「一致は model_validator でチェック(Phase 0-6)」としていたものを Phase 1 で実装(Input Validation として Pydantic に寄せる)。(`Phase-1-1.md` §2)
- **objectives(多目的の重み付き和の評価器)は Phase 1 では作らない → Phase 6 送り** — 当初 `domain/objectives/weighted_sum.py` を Phase 1 に入れたが、(a) `Phase-1-introduction.md` §10 の実装前チェックリスト 1-1〜1-7 に objectives が含まれない、(b) Phase 1 で registry に載る唯一の strategy(Dijkstra)は単一目的で消費者もテストも無い、ため投機実装として撤回。初の多目的ストラテジー(Phase 6 の Shift Scheduler = Greedy / Backtracking)を実装するときに追加する。`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の「Phase 1」表記には「以降 Phase で修正予定」マーカーを付与(ルール #12)。(`Phase-1-1.md` §1 の注記 / `Phase-1-7.md` §5)
- **solve のタイムアウトは `asyncio.wait_for(asyncio.to_thread(strategy.solve, ...))`** — 同期・純粋な `solve` をスレッドに逃がして監視。超過で `SolveTimeoutError`(504)。タイムアウトしてもスレッド自体は止められない(MVP の割り切り。Phase-0-5 §5)。(`Phase-1-6.md` §4)

#### Phase 2(実装フェーズ)の主要決定 — 詳細は `textbook/Phase-2/`

- **Phase 2 教材は 6 章(2-1〜2-6)+ samples。旧 `Phase-1-7.md` §5 の 7 単位から `verifications` テーブル(旧 2-7)を削除** — 検証結果は Phase 1 の `Solution.status`(カラム)+ `Solution.payload`(JSONB)に既に入り、MVP に payload 内クエリ需要が無い(`Phase-0-8.md` §4 / Q12)。`benchmark_runs`(Phase 3)を作るとき、または実クエリ需要が出たときに切り出す。Phase 2 は ORM / マイグレーション / リポジトリに一切触れない。検証は overlay end 状態で `uv run pytest`(121 passed / 3 deselected)・`ruff`(clean)・`uvx pyright`(0 errors)。(`Phase-2-introduction.md`)
- **shift の Validation / Verification は Phase 2 で実装(Phase 1 の objectives 撤回の先例は転用しない)** — objectives は「探索中に解を採点する機構」で消費アルゴリズムが無ければ無意味だったため Phase 6 送り。V&V は事前 / 事後の純粋なチェックで、Phase 1 で凍結済みのデータモデル(`ShiftData` / `ShiftSolution` / `StaffingConstraint`)に対して働き、`POST /verify` が手組み shift 解の実消費者になる。README §19 も「route→全 kind へ一般化」と定義。shift strategy(Greedy / Backtracking)は Phase 6 のまま。(Q14)
- **`SEMANTIC_CHECKS` は `domain/problems/semantic.py`、`CHECKERS` は `domain/constraints/__init__.py` へ** — Phase 1 は `validation.py` / `verification.py` にインライン(route 限定)。Phase 2 で problem_type ごと / kind ごとのレジストリを domain に置き、2 サービスは「レジストリを回すオーケストレーション」に縮小(`algorithms/registry.py` と同じ発想)。(`Phase-2-2.md` / `Phase-2-3.md`)
- **route の到達可能性は「計算 = algorithms / 判定 = services」に分ける** — 他の Semantic 検査(`check_route_endpoints` 等)は問題フィールドの純粋述語なので `domain/problems/semantic.py`。到達可能性は BFS を走らせる**計算**なので、`route_reachable(data, forbidden) -> bool` を **新規 `app/algorithms/graph/reachability.py`**(`build_adjacency` + BFS の薄い合成)に起こす。`ProblemValidationService.validate` は「純粋述語のレジストリを回す + `route_reachable` を呼んで hard ゲート判定」のオーケストレーションに徹する。domain は不関与。`domain → algorithms` の import 禁止は「計算を domain に置く」誤りを写経中に顕在化させる **guardrail** であって判断の理由ではない ── 理由は「これは計算か? 述語か?」。当初は `_route_unreachable` を `validation.py` の private メソッドに `build_adjacency` 呼び出しごとインラインしていたが、ユーザー指摘(「現場レベルの設計なら service に置くべきものは、その形に起こすステップが要る」)で `route_reachable` に抽出。(`Phase-2-2.md` §3)
- **構造検証(`verify_route_structure` / `verify_shift_structure`)は `domain/solutions/structure.py`** — `ConstraintViolation`(`solution.py`)を返すため solution leaf に置くと `solution.py → leaf → solution.py` の循環。leaf でも aggregator でもない合成モジュールに置く。(`Phase-2-3.md` §2)
- **`StaffingConstraint`(人数=required_headcount)は opt-in の `check_staffing` チェッカー、`verify_shift_structure` には入れない** — 可用性・労働時間・スキルは「常に成り立つべき構造」(常時オン)、人数ちょうどは「方針」(宣言したら hard で守る)。`Phase-0-2.md` §4.2 の「フラグ的な意味づけ」に沿う。(`Phase-2-3.md` §1)
- **連続勤務日数の Verification は完成割当の 1 回スキャン(`itertools.pairwise` + `date` 差分)** — Sliding Window プリミティブ(README §8、Phase 6)は Backtracking ソルバーの逐次可否判定用。事後検証はそれに依存しない(Phase 6 への前方依存を作らない)。(`Phase-2-4.md` §3)
- **`numeric_bound` チェッカーは route の `metrics["total_weight"]` で即消費できる** — `solve` 経由で end-to-end に効く唯一の Phase 2 チェッカー。`NumericBoundConstraint(field="total_weight", operator="<=", value=8)` を w9 の route 問題に付けると Verification が `status="invalid"` にする ── `Phase-2-6` の Invalid Solution Handling の題材。(`Phase-2-3.md` / `Phase-2-6.md`)
- **`POST /api/v1/verify` は DB を触らず Semantic Validation も走らせない** — 「解けるか」でなく「この解が条件を満たすか」を見るため。`VerifyService` は `SolutionVerificationService` をレート制限(`resource="verify"`)で包むだけ。invalid 解も 200(`Phase-0-6.md` §4)。(`Phase-2-5.md`)

#### Phase 3(実装フェーズ)の主要決定 — 詳細は `textbook/Phase-3/`

- **Phase 3 教材は 6 章(3-1〜3-6)+ samples(backend + ui)。UI は完全な samples 作業単位(ユーザー選択)** — 3-1〜3-4 が decitima-api、3-5〜3-6 が decitima-ui。`samples/` に `app/**` と `ui/src/**` を両方置き、overlay 検証も 2 リポジトリ分。検証: backend overlay end 状態で `uv run pytest`(151 passed / 3 deselected)・`ruff`・`uvx pyright`(0 errors)・`alembic upgrade head`。ui overlay で `tsc --noEmit`・`vitest`(追加 8 件緑)・`eslint`。(`Phase-3-introduction.md`)
- **測定は「solve の外」に切り出す ── `services/measurement.py::measure_call`** — 実行時間(`perf_counter`、runs 回の中央値 + 四分位)とメモリ(`tracemalloc` ピーク)を測る汎用関数。ドメイン非依存(テンプレート還元候補)。操作回数は各 strategy が `solve()` 内で `metrics["_ops"]` に積む(Phase 1 Dijkstra が種まき済み)。**`_ops` はアルゴリズム定義の単位**(Dijkstra=heap pop 数、BruteForce=展開した部分パス数)なので時間・メモリのように直接比較しない ── 教材で明示。(`Phase-3-1.md` / `Phase-0-5.md` §4 にマーカー)
- **`BruteForceRouteStrategy`(全単純パス列挙)を registry の 2 本目に登録** — README §8「Brute Force = Phase 3 の正解オラクル」。役割 2 つ: ① Dijkstra の最適性を小規模グラフで裏取りする正解オラクル(`build_scaled_route_problem(n, seed)` の seed を for ループで振るプロパティテスト)② ベンチの 2 本目の対象。`find_strategy` は `candidates[0]` を返すので `solve` の既定は Dijkstra のまま。`family="optimization"`(技法で決める)、`build_adjacency` は `dijkstra.py` のものを再利用。(`Phase-3-2.md`)
- **`BenchmarkService` は Validation を通す(verify との違い)** — 実際に解くので「解けない問題」を弾く。Verification は**計測の外**でかけて hard/soft 違反数を entry に載せる(6 指標の「制約違反数」)。invalid 解も 200。per-run タイムアウトは `SOLVE_TIMEOUT_SECONDS` 再利用、`resource="benchmark"` の専用レート制限(solve より重いので厳しめ 10/h・50/日)。(`Phase-3-3.md`)
- **`benchmark_runs` テーブルを作る(ユーザー選択)+ `Problem` への FK は張らない** — Phase-0-8 §2 の計画どおり Phase 3-3 で追加。`id` / `user_id` / `problem_type` / `created_at` + `payload` JSONB(`{problem, entries, runs}`)。benchmark は「N 回の solve の永続化」でなく独立した測定記録なので自己完結。`Phase-0-8.md` §4 の「`verifications` を benchmark_runs 作成時に再検討」→ 再検討済み・引き続き作らないで確定。`GET /api/v1/benchmarks/{id}` は `get_problem` と同型の所有者スコープ。(`Phase-3-3.md` / `Phase-3-4.md`)
- **`quality_ratio` は「オラクルの値」でなく「run 中の最良値」を基準にする** — 全探索が entries にいれば実質オラクル比、いなくても「一番良かったやつとの比」として意味を持つ。minimize は最小、maximize は最大が基準。目的が metrics に無ければ None。(`Phase-3-4.md`)
- **numpy を追加(ユーザー選択、Phase-0-9 計画どおり)/ hypothesis は見送り** — numpy は `measure_call` の中央値・四分位集計だけに使う(アルゴリズムの計算には使わない)。hypothesis はオラクルのプロパティテストが手書きジェネレータ + for ループで足りたため見送り(`Phase-0-9.md` §2 / §5 にマーカー)。(`Phase-3-1.md` / `Phase-3-2.md`)
- **decitima-ui 初の `src/features/optimization/` + 可視化は手描き SVG 拡張** — これまで decitima-ui はテンプレートのデモページのみ。ベンチマークが最初の feature(`{api,stores,hooks,components}`)。可視化ライブラリは Phase 3 では**足さない** ── 既存の手描き SVG(`BarChart`/`LineChart` パターン)を `src/components/ui/charts/{GroupedBarChart,MultiLineChart}.tsx`(ドメイン非依存名、還元候補)に軸・凡例・対数軸・多系列で拡張。本格的な図ライブラリの選定はノード/エッジ描画が要る Phase 4 へ(`Phase-0-3.md` §6.3 にマーカー)。DTO 型は `src/lib/api/types.ts` に手書き(OpenAPI 生成しない)。ページは SSG のまま、取得はクライアント側 `apiFetch`。`@tamagui/next-theme` を使うチャートのテストは `vi.mock` で最小モック。(`Phase-3-6.md` / `Phase-3-7.md`)
- **pandas を「分析トラック」に導入(作業単位 3-8)── コア層には入れない** — ユーザー相談「pandas をどこに活用できるか」への回答。`app/domain` `app/algorithms` と solve/verify/benchmark のリクエスト経路には**入れない**(純粋レイヤーの契約 / 「手実装で示す」軸 / テスト速度と衝突。データも小さく numpy で足りる)。置き場は `decitima-api/backend/analysis/`(`app` から import されない。`tests/` と同じ「app の上」)、依存は `[dependency-groups].analysis`(`pandas` / `matplotlib`。runtime に入れない)。DB との結合は「エクスポート(async)→ JSONL → `pd.DataFrame`(純粋)」の一方向(decitima-ui の `src/db/` と同型)。`loaders` / `benchmark_report` は純粋関数でユニットテスト、`plots` はスモーク、notebook はサンプルデータで完結し `nbconvert --execute` で回す。`analysis/` は ruff のみ(pyright `include` 外)。**`analysis/` は Phase 4/6/10/12/14/15 が育てる多 Phase の背骨**(Phase 14 の「LLM vs Algorithm 実験フレームワーク」が中核)。入力アダプタ(CSV/Excel→Problem)は runtime 依存の別レイヤーで Phase 6/8/9 送り。overlay 検証: `uv run pytest` 165 passed(3-8 の analysis 14 件を含む)。(`Phase-3-8.md` / Notes Q18)【Q24 で章番号を 3-7 → 3-8 にリネーム(ログイン UI を 3-5 に挿入)。中身は不変】
- **レイヤーごとのファイル分割粒度を確定 ── data 層は「永続化の関心事」、route / service は「操作」** — `models` / `schemas` / `repositories` は `optimization.py` 1 本(`Problem` / `Solution` / `BenchmarkRun` は全部 JSONB payload の「最適化レコード」)、`api/routes` / `services` は操作単位で割る(`solve` / `verify` / `solutions` / `algorithms` / `benchmark`)。格納先はファイル名の層間対応でなく import で辿る(`models/__init__.py` が全 re-export)。当初 Phase 3 は `repositories/benchmark.py` を単独ファイルにしていたが、動機は samples 運用の都合(このファイルを触ると現行版再出荷 + マーカー)で設計判断でなかったため、`BenchmarkRunRepository` を `repositories/optimization.py` に同居させ `Phase-0-8.md` §5 の当初計画へ是正。`models/benchmark.py` / `schemas/benchmark.py` は作らない(18 行のモデル・8 行の repo で極小ファイルを量産しない。`Phase-0-2.md` §2.5「変更理由と消費者が別なら分割」で見ても `BenchmarkRun` は Problem / Solution と同じ永続化理由で変わり消費者も重なる)。Phase 4 以降 Web サービス性が強まっても、hybrid JSONB スキーマで data 層のテーブルは増えないため、このルールは 1:1:1:1 に収束せずそのまま効く(増えるのは操作 = route / service ファイルと、本物の新集約が出たときの 1 式)。(`Phase-3-3.md` §2.3 / 相談ログ Q21)
- **Phase 3 章を再構成 ── 3-5 に最小ログイン UI を挿入、以降を後ろへ、分析トラックを 3-8 に** — benchmark 画面が認証必須で「ブラウザ動作確認で 401 に当たる」ため。新章立て: 3-1〜3-4(backend)/ **3-5 = 最小ログイン UI**(`/login` + `LoginForm` + `RequireAuth` 配線)/ 3-6 = features/optimization 骨格 + api 層 / 3-7 = チャート + ページ / 3-8 = 分析トラック `analysis/`。ログインは feature の**下の層**(`src/components/auth/`)なので UI feature の前。分析トラックは Phase 4 に移さず 3-8 に据え置き(`git mv` のみ)── 執筆・検証済みの再配置を避け、`benchmark_runs` が生まれる Phase にアンカーを残す。Phase 4+ が既存 `analysis/` を「育てる」計画は不変。(相談ログ Q24 / `Phase-3-5.md`)
- **`refreshTokens()`(テンプレ由来)を DeciTima backend の `/auth/refresh` 契約に修正** — テンプレの `auth-store.ts::refreshTokens()` は `/auth/refresh` から `TokenPair`(access + refresh)を期待していたが、DeciTima backend は `AccessToken`(access のみ、ローテーション無し。`app/schemas/auth.py`)を返す。access token 期限切れ時に `refreshToken: undefined` を set して壊れる。修正: `apiFetch<AccessToken>` + `setState({ accessToken })` のみ(`refreshToken` 据え置き)。テンプレート還元候補(`next-tamagui-templates` ↔ `fastapi-langchain-template`)。(`Phase-3-5.md` §4 / 相談ログ Q24)

#### Phase 4(実装フェーズ)の主要決定 ── Route Planner。詳細は `textbook/Phase-4/`

> **Phase 4 / 5 の分割(相談ログ Q29)**: 当初 Phase 4 は Route Planner + Network Designer の 11 章構成だったが、README §12 が両者を同格の製品機能として並べていること・章数が他フェーズの倍近いこと・CL 開発の「小さく予測可能な単位」方針から **Phase 4 = Route Planner(8 章)/ Phase 5 = Network Designer(5 章)** に分割。現 Phase 5〜14 → 6〜15、MVP 範囲 Phase 0〜5 → 0〜6。実装の順序は不変。

- **Phase 4 教材は 8 章(4-1〜4-8)+ samples(backend + analysis + ui)** — 4-1〜4-6 が decitima-api、4-7〜4-8 が decitima-ui。overlay 検証: backend(Phase 3 end 状態 + Phase 4 samples + `networkx>=3.3`)で `uv run pytest` **176 passed / 2 deselected**・ruff clean・pyright(Phase 4 分 0 errors)・`alembic upgrade head` は **no-op**・notebook 実行。ui で `tsc --noEmit` clean・`vitest` **13 passed**・eslint clean。(`Phase-4-introduction.md`)
- **グラフプリミティブを整理 ── `graph/{adjacency,segments,waypoints}.py` を新設** — `build_adjacency` を `dijkstra.py` から `adjacency.py` へ移設(`Phase-2-2.md` §3 / `reachability.py` の予告どおり)。`reachability.py` / `brute_force.py` / `dijkstra.py` は import 元が変わるだけ(挙動不変、既存テスト緑)。route 3 strategy(Dijkstra / Bellman-Ford / A*)は「区間の最短経路の求め方」だけが違うので、共通足回り(`Segment` / `plan_route` / `route_solution` / `collect_route_constraints`)を `segments.py` に集約。CSR 行列ビルダー(`to_csr`)は scipy を足す Phase まで遅延(appendix フック①、`adjacency.py` に足すだけ)。`union_find.py` は Kruskal が唯一の実消費者なので Phase 5-1 へ。(`Phase-4-1.md`)
- **負辺 ── `RouteEdge.weight` の `Field(ge=0)` を撤廃、`RouteData.allow_negative` フラグ + `model_validator`** — ユーザー選択(スコープ相談 Q27)。`allow_negative=False`(既定)なら従来どおり Pydantic が負を弾く。ガードを `RouteEdge`(フィールド)から `RouteData`(親)の `model_validator` に移した ── `allow_negative` は親の方針。`BellmanFordStrategy` = V-1 回緩和 + もう 1 回で負閉路検出 → `infeasible` + `negative_cycle` violation。Dijkstra / A* は負辺グラフを渡されたら `infeasible`(壊れた解を返さない)。**負辺のデモは有向グラフで作る**(無向 + 負辺 = 即・負閉路)。(`Phase-4-2.md`)
- **A* ── `_ops`(heap pop 数)が Dijkstra と同じ数え方なので直接比較できる数少ない例** — h(n) はノード座標(`RouteNode.x/y`)のユークリッド距離、座標が無ければ 0(可容 → Dijkstra に縮退)。可容性を破ると(過大な h)非最適解になることをテストでわざと赤にして確認(#14 の趣旨)。(`Phase-4-3.md`)
- **複数必須経由地 = 小 TSP を Phase 4 で扱う** — ユーザー選択(Q27)。`graph/waypoints.py::optimize_waypoint_order` ── `m ≤ 8`(`_MAX_EXACT`)は訪問順の全順列、それ以上は「与えられた順」(近似は Phase 7 Travel Planner に送り前方依存を作らない)。区間の最短距離は呼び出し側 strategy が `cost` 関数で注入 ── `optimize_waypoint_order` はグラフを知らない純粋ロジック(フェイクの距離表でテストできる)。`_SegmentCache` が区間を 1 度だけ解いてメモ化(順序探索と連結で共有)。Dijkstra / Bellman-Ford / A* は `plan_route` 経由なので**無変更**で恩恵を受ける。(`Phase-4-4.md`)
- **networkx を runtime 依存に追加(`[project].dependencies` の `networkx>=3.3`)** — `library:*` トラックは `POST /solve` `/benchmark` のリクエスト経路で動くため(numpy / pandas の dev 依存とは違う)。`NetworkxShortestPath` は `meta.name="dijkstra"` / `implementation="library:networkx"` / `_ops` を積まない(仕事が C の中。「ライブラリトラックは操作回数を出せない」= 2 トラック比較の論点、Q19)。手実装 Dijkstra / Bellman-Ford の**別実装オラクル**(BruteForce は厳密最適、networkx は別実装照合 ── 役割が違う)。`_to_graph` は平行エッジを軽い方だけ残す(`nx.Graph` は 1 本しか持てない、最短経路では等価)。(`Phase-4-5.md`)
- **rule-based `select_strategy`(README §6 / `Phase-0-4.md` §6 の Step 1)** — `services/algorithm_selection.py`: 負辺 or `allow_negative` → `bellman_ford` / 全ノードに座標 → `a_star` / 既定 → `dijkstra`(手実装。`library:networkx` は明示 request 時のみ)。`registry.find_strategy` は純粋のまま「候補の先頭」、賢い選択は services 層(`Phase-1-2.md` §3 と同じ判断)。`network_design → kruskal` の分岐は Phase 5-3 で足す。学習型(Step 2/3)は Phase 12。(`Phase-4-5.md`)
- **`analysis/route_benchmark.py` を Phase 3-8 の `analysis/` に 1 本追加 ── 移設・作り直しなし** — `load_route_benchmark_runs`(size / density 列を足す)/ `by_size` / `handwritten_vs_library`(speedup)/ `crossover_size`。`build_scaled_route_problem` に `density`(既定 0.5 = Phase 3 と同挙動、RNG 呼び出し順も同じ)。**実測: MVP 規模(〜数百ノード)では手実装 Dijkstra が networkx より速い**(networkx のグラフ構築オーバーヘッド)── `crossover_size` はこの範囲で `None`。「手実装をやめてライブラリに切り替える点」を実測で示すという 2 トラック設計の目的(Q19)。ライブラリが効くのは OSM 規模(`Phase-0-5.md` §3.1)。(`Phase-4-6.md`)
- **経路図は手描き SVG(`GraphCanvas`)── 本格図ライブラリは入れない** — ユーザー選択(Q27)。Phase 3-6 §1 が Phase 4 に送っていた「選定」の結論。`src/components/ui/charts/GraphCanvas.tsx`(ドメイン非依存 = 還元候補、Phase 5 の Network Designer も使う): 座標 or 円環レイアウト / highlight(実線・強調)/ dashed(候補・破線)/ directed 矢印。Phase 4 のグラフはデモ規模(〜数十ノード)で手描きで十分軽く、「手実装を主軸に境界の裏だけライブラリ」の一貫性を保てるため。可視化には `POST /solve`(経路つき `CandidateSolution`)、比較表には `POST /benchmark`(`BenchmarkEntry` に `assignments` が無い)。(`Phase-4-7.md`)
- **decitima-ui 初の `src/features/optimization/route-planner/`** — benchmark(比較専用)に加えて 2 画面に(Phase 5 で network-designer を足して 3 画面)。route の slice は `{api, stores, hooks, components}`。共有は api 層の下 `apiFetch` と型 `lib/api/types.ts`(この時点では route のみのユニオン)だけ(Q23)。問題入力は**サンプル選択 + JSON テキストエリア**(`ProblemJsonEditor`)── リッチな作図エディタは作らない。ページは SSG + `RequireAuth`(Phase 3-5 の認証基盤の消費者)、`BenchmarkTable`(3-7)を再利用。(`Phase-4-8.md`)

#### Phase 5(実装フェーズ)の主要決定 ── Network Designer。詳細は `textbook/Phase-5/`

- **Phase 5 教材は 5 章(5-1 Union-Find / 5-2 MST 理論 / 5-3 network_design 配線 / 5-4 Kruskal・Prim・networkx_mst / 5-5 Network Designer ページ)+ samples** — overlay は Phase 4 end 状態の上に重ねる。backend `uv run pytest` **217 passed / 2 deselected**(Q35 是正後。analysis 6 本込み。pandas 未導入なら `--ignore=tests/analysis` で 211)・ruff/pyright clean・`alembic upgrade head` は **no-op**。ui `tsc` clean・`vitest` **16 passed**・eslint clean。順序の理由: 道具(Union-Find)→ なぜ動くか(MST 理論)→ 配線(schema)→ 実装 → UI。(`Phase-5-introduction.md`)
- **Union-Find(`graph/union_find.py`)を深掘り章として独立(相談ログ Q29 でユーザー確定)** — 経路圧縮 + ランク合併、ならし O(α(n))。**`union` が bool を返す**設計 ── 「すでに同じグループ = その辺は閉路」を Kruskal がそのまま使う。route は `search/bfs.py` + `reachability.py` で連結性を見るので Union-Find の消費者がいない(Phase 4 でなく Phase 5)。(`Phase-5-1.md`)
- **MST 理論を独立章に(相談ログ Q29)/ 実測テストと network fixture は 5-3 に置く(Q34)** — 5-2 は cut property(切除性)/ cycle property / 交換論法 ──「なぜ『軽い辺から貪欲』で最適になるか」を説明する**理論章(実装ファイルなし)**。小グラフの**全域木を全列挙**(`_all_spanning_trees`)して cut / cycle property と既知 MST を実測する `tests/unit/test_mst_properties.py` と、その入力の network fixture(`build_network_problem` 系、5 拠点・既知 MST コスト 10)は **5-3 の成果物**にした ── 列挙オラクルが `forms_spanning_tree`(`connectivity.py`)と `NetworkDesignData` / `NetworkLink`(`network_design.py`)を import し、どちらも 5-3 で生まれるため(進行のルール #15。当初 5-2 は素の前方参照を注記だけで許容していた)。5-3 の `test_network_design.py` も既に `build_network_problem` に依存しており、fixture は元々 5-2 の clean な成果物になり得なかった。Phase 3 の BruteForce オラクルと同じ発想。(`Phase-5-2.md` / `Phase-5-3.md` §7)
- **`network_design` problem_type を配線 ── 既存の route / shift に一切触れず、`alembic upgrade head` は no-op** — `NetworkDesignData`(`nodes` / `links`。`NetworkLink.endpoints: tuple[str,str]` は**常に無向** ── route の有向エッジと型で区別)/ `NetworkDesignSolution`(`selected_link_ids` / `total_weight`)をユニオンに 1 項目ずつ。semantic は「純粋述語」(`check_network_link_endpoints` / `check_network_has_links`)だけ `domain`、「連結性の計算」(`all_nodes_connected` / `forms_spanning_tree`)は `algorithms/graph/connectivity.py`(BFS ベース、`union_find` に依存しない)に置き `services`(validation / verification)が呼ぶ ── `Phase-2-2.md` §3 の「計算か? 述語か?」の切り分け。`build_link_adjacency` を `adjacency.py` に、`network_design → kruskal` を `select_strategy` に追加。既存の `forbidden` / `required_inclusion` / `numeric_bound` チェッカーが network 解にも効く(kind ベース、チェッカーに `selected_link_ids` 分岐を足すだけ)。`Phase-5-3.md` は §3「グラフ・プリミティブ」+ 写経順序リスト付き(Q35 ── `build_link_adjacency` / `connectivity.py` / `test_graph_primitives.py` の解説漏れを是正)。`test_graph_primitives.py` は 5-3 で network 4 テストを**追記**(Phase 4-1 の route 分は現行版として保持)。(`Phase-5-3.md`)
- **MST ── Kruskal(`UnionFind`)/ Prim(heapq)/ NetworkxMST。`registry` に `"network_design"` キーを新設** — Phase 1 以来はじめて registry に新 problem_type。`get_strategies` / `find_strategy` / `all_strategies` は無変更(`REGISTRY.get(pt, [])`)。`mst.py` に共通足回り(`parse_network_problem` / `resolve_required` ── 必須リンク検証 / `mst_solution`)。`NetworkxMST` は必須リンクを重みの下駄で強制(networkx に直接の仕組みが無い ── これも 2 トラック比較の観察点)。`_ops` の単位(Kruskal=union 試行、Prim=heap pop)はアルゴリズムごとに違う。(`Phase-5-4.md`)
- **Network Designer ページ ── Phase 4-8 の Route Planner と同型** — `src/features/optimization/network-designer/`。`types.ts` に `network_design` アーム、`menu-tree.ts` に network エントリ(backend のユニオン分割と 1:1)。`MstResultCanvas` は選んだリンクを実線・候補を破線で `GraphCanvas` に描く。generic 化しない(`problem_type` / 解の型 / 可視化が違う。Q23)。(`Phase-5-5.md`)

#### Phase 6(実装フェーズ)の主要決定 ── Shift Scheduler(MVP 完成)。詳細は `textbook/Phase-6/`

- **Phase 6 教材は 8 章(6-1〜6-8)+ samples(backend + analysis + ui)** — 6-1〜6-7 が decitima-api、6-8 が decitima-ui。overlay は **Phase 5 end 状態の上に重ねる**。backend `uv run pytest` **271 passed / 2 deselected**(Phase 5 の 217 + Phase 6 分)・ruff/format/pyright clean・`alembic upgrade head` は新テーブルなし・notebook 完走。ui `tsc` clean・`vitest` **17 passed**・eslint clean。`ortools` を共有 `.venv` に導入済み。順序の理由: 採点機構(objectives)→ 部品(primitives)→ 速い近似(Greedy)→ 厳密(Backtracking)→ 枝刈り(B&B)→ なぜ破綻するか → 産業ソルバー → UI。(`Phase-6-introduction.md`)
- **Phase 6 は「アルゴリズムを書くだけ」** — `ShiftData` / `ShiftSolution` は Phase 1 凍結 + 2-1 で model_validator、判別可能ユニオンに shift は既に 3 メンバーの 1 つ(配線ゼロ)、`SEMANTIC_CHECKS["shift_scheduling"]` 4 本と `verify_shift_structure` 5 チェック + `check_staffing` は Phase 2 完成、`POST /solve` `/verify` `/benchmark` は汎用ディスパッチ。Phase 6 の新規は `domain/objectives/` / `algorithms/patterns/{sliding_window,difference_array}` / `algorithms/scheduling/*` / `analysis/shift_analysis.py` / UI のみ。(`Phase-6-introduction.md` §1)
- **`domain/objectives/weighted_sum.py` を初実装(Phase 1 からの宿題)** — `weighted_sum(objectives, metrics) -> float` は多目的を **minimize 向きの 1 スカラー**に(minimize → `+w·f`、maximize → `−w·f`)。`Phase-0-2.md` §3 の約束「`Σ wᵢ·fᵢ` を最適化」の実装。Phase 1 で投機実装 → 消費者(Dijkstra は単一目的)がいなくて撤回 → Phase 6 の Shift Scheduler の Greedy / Backtracking / B&B が初の消費者。**スケール差の落とし穴**(`labor_cost`〜2万 vs `day_off_satisfaction` 0〜1 → 生の重み付き和は前者に支配。¥1 差(score 0.7)が `day_off_satisfaction` の全振れ幅(score 0.3)に勝つので `weight=0.3` は事実上無力)は教材で明示、**正規化([0,1] への min-max / 基準解比)は今後の改善検討事項として Q37 に記録**(入れる Phase は未定 ── 実データのレンジが見える Phase 9/10/14 あたり)。`hour_variance` の `weight=100` は問題サイズ依存の手調整値。`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 のマーカーを「Phase 6 で確定 ── 実装済み」に。(`Phase-6-1.md` / Q37)
- **shift の metrics 計算を `domain/solutions/shift_metrics.py`(新規・公開 leaf)に集約(現行版)** — `labor_cost` / `day_off_satisfaction` / `hour_variance`(第 3 目的「勤務時間均等化」= スタッフ週勤務時間の**母分散**。0 割当も母数に含める)の計算を 1 箇所に。**検証器(`verify_shift_structure`)と探索の 4 strategy(`common.score()` 経由)が同じコードを import** するので、検証で報告する値と探索が最適化する値が構造的に drift しない(Phase 2 は `verify_shift_structure` にインラインしていた ── 消費者が 2 系統になったので抽出。ルール #17 / Q38)。hard/soft の 5+1 チェックと `_longest_consecutive_run`(`domain → algorithms` 禁止でレイヤー上分ける)は不変 = 公開挙動不変(`test_verification_service.py` のアサーションそのまま。#16)。**集約対象は metric の式だけ** ── 型エイリアス `type Assignment` は `domain/solutions/shift_scheduler.py`(`ShiftSolution.assignments` の型。両レイヤーが循環なしで届く葉)に置き、`shift_metrics` も `scheduling/common` も **4 strategy も**、`Assignment` は `shift_scheduler` から**直接** import する(route が `Segment` を定義元 `segments.py` から取るのと同じ ── `common` 経由の間接 import は残さない。`common` は関数の窓口)。Q38 フォローアップ 2 ── 当初 `common.py` に置いて `domain → algorithms` 循環を踏んだ。Phase 1 samples の `shift_scheduler.py` / Phase 2・5 samples の `structure.py` に `[以降 Phase で修正予定 ── Phase 6-1]` マーカー。(`Phase-6-1.md` / Q38)
- **スケジューリング・プリミティブ ── `sliding_window.py` / `difference_array.py`** — `run_length_at(present_ordinals, point)` は Backtracking の「この 1 手で連続勤務日数が上限超過するか」を O(ラン長) で逐次判定。Phase 2 の `_longest_consecutive_run`(`itertools.pairwise` の事後 1 回スキャン)は**書き換えない** ── 用途が違う(`Phase-2-2.md` §3.3 の予告どおり)。`difference_array.range_add` は imos 法(区間の左端で +、右端で −、最後に累積和)で時間帯別の在籍人数を O(スロット数) に。累積和の対。(`Phase-6-2.md`)
- **手実装 3 ストラテジー ── Greedy / Backtracking / Branch and Bound(`family="scheduling"` / `implementation="handwritten"`)** — `scheduling/common.py` が 4 strategy 共通の足回り(`parse_shift_problem` / `eligible_staff` / `respects_hard` / `score`(`weighted_sum` × `shift_metrics.assignment_metrics`)/ `shift_solution`)── route の `segments.py` / network の `mst.py` と同型。metrics 式そのものは持たず `shift_metrics.py` を import(Q38)。Greedy = tightness 昇順に最安割当、hard 違反は例外でなく `invalid` 候補。Backtracking = スロット順の DFS(`combinations` で headcount 人の組)+ 週時間 / 連続日数で枝刈り + 葉で weighted_sum スコア。B&B = + admissible な下界(`labor_cost` の楽観推定 = suffix sum + maximize 目的の `−w`)。`_ops` の単位は strategy ごとに違う(割当試行 / 展開ノード / ノード + 下界計算)。(`Phase-6-3〜5.md`)
- **B&B の anytime は壁時計でなく決定論的なノード予算(`Phase-0-5.md` §5.1 の宿題の結論)** — `solve` は純粋関数の契約(時刻の読み取り = 副作用 → `test_deterministic_same_input_same_output` が赤)を守るため、`time.perf_counter()` を見ない。`_MAX_NODES = 200_000` を超えたら**その時点の最良解 + `metrics["_truncated"]=1.0`**(`_` 接頭辞 = 診断指標)を返す。壁時計 `SOLVE_TIMEOUT_SECONDS` は `SolveService` の既存の安全網のまま ── **`services/solve.py` は変更しない**(スレッドは止められない MVP の割り切り)。(`Phase-6-5.md`)
- **手実装の破綻を全列挙オラクルで実測(6-6 = Phase 5-2 と同型の理論章、実装ファイルなし)** — `_brute_force_optimal(problem)`(全割当を `itertools.product` で全列挙、`respects_hard` フィルタ、`score` 最小 ── 小規模専用のインラインヘルパ、registry 非搭載)を正解オラクルに、Backtracking / B&B が小規模で最適(== オラクル)、Greedy はオラクル以上(最適を外しうる)を確認。破綻シナリオ表(3×2×2 一瞬 / 8×7×3 秒〜十数秒 / 20×7×3 現実的に終わらない → CP-SAT 必須。`Phase-0-5.md` §3.2)。(`Phase-6-6.md`)
- **OR-Tools CP-SAT トラック ── フル実装(相談ログ Q36)** — `OrToolsCpSatShiftStrategy`(`implementation="library:ortools"`、`_ops` を出さない = `operation_count=None`)。`ortools` を `[project].dependencies` に追加(runtime。Phase 8/9 で再利用。README §18)。モデル: `x[s,t]` bool(eligible な組だけ)/ スロットごと `Σ == required_headcount` / per-staff `Σ x·hours ≤ max_weekly_hours` / `works_on_day` の連続 (max+1) 日窓 / 目的は weighted_sum を `_SCALE=1000` で整数線形式に。**`hour_variance` は CP-SAT が二乗を嫌うので spread(max−min)で代理** ── 手実装は本物の分散でスコアするので最適が完全一致しないことがある(教材の観察点 ── ライブラリはモデルの表現力に合わせて目的を近似する)。**決定論**: `num_search_workers=1` + `random_seed` 固定 → purity テスト緑。`registry` 最終形(4 strategy)。end-to-end パイプライン(validate→select→solve→verify)は registry が埋まる 6-7 で緑(Phase 5-3 → 5-4 の Q35 と同型)。(`Phase-6-7.md`)
- **「未登録 problem_type」テスト 3 本を現行版に(#16)** — Phase 5 まで `shift_scheduling` を「registry に何も無い problem_type」の例に使っていた(`test_registry` / `test_solve_service` / `test_solve_api`)。Phase 6 で全 problem_type に strategy が付いたので、`monkeypatch.setitem(REGISTRY, "shift_scheduling", [])` で「候補ゼロ → `NoAlgorithmError` / 400」に書き換え。Phase 1 samples 側にマーカー。(`Phase-6-7.md`)
- **`analysis/shift_analysis.py` を Phase 3-8 の `analysis/` に 1 本追加 ── 移設・作り直しなし** — `load_shift_benchmark_runs`(+ size 列 = スタッフ数 × スロット数)/ `by_size` / `handwritten_vs_cpsat`(**Greedy を除く** ── `_EXACT_HANDWRITTEN = ("backtracking", "branch_and_bound")`。Greedy は多項式時間だが最適でない)/ `crossover_size`(CP-SAT がはじめて手実装より速くなる size)/ `pareto_front`(labor_cost 小 × day_off_satisfaction 大の非支配)。`analysis/` は dev 依存(pandas / matplotlib)、`app` から切り離し。notebook `shift_explore.ipynb` はサンプルデータで完結。(`Phase-6-7.md`)
- **Shift Scheduler ページ ── Phase 4-8 / 5-5 と同型の 3 スライス目** — `src/features/optimization/shift-scheduler/{api,stores,hooks,components}`。`ShiftGrid` はスロット行 × 割当スタッフの**手描きテーブル**(図ライブラリなし)、人数不足のスロットは赤。`types.ts` に `ShiftData` / `ShiftSolution` / union / `CandidateSolution` アーム。**`CandidateSolution.assignments` に `ShiftSolution` を足すと、`.total_weight` を無条件アクセスしていた route / network の store テストが型エラー** → 現行版で `.assignments.total_weight` → `.metrics.total_weight`(どの解型にもある)に(#16)。generic 化しない(Q23)。(`Phase-6-8.md`)

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
   - objectives 評価器は Phase 6 送り(上の「主要決定」項)。
   - overlay 検証時は config / errors / models/__init__ / api/routes/__init__ の 4 点の追記を複製側へ適用してから pytest/ruff/pyright を回す(89 passed / 3 deselected、clean、0 errors を再確認)。
   - 反映: `Phase-1-1` `Phase-1-2` `Phase-1-5` `Phase-1-6` `phase-1-index` `samples/README.md` `CLAUDE.md` を更新、commit `93c3302` を amend。

**Q5.（Phase 1 生成後の指示)以前の Phase への変更は「改訂マーカー」で以前の Phase にも反映する**

1. **Phase**: Phase 1(教材生成の直後)
2. **指示**: `Phase-1-1.md` §2.1(`: TypeAlias` → `type` 文)/ §2.2(network_design は Phase 4)の変更を Phase 0 にも反映する。その際「当初より変更があったことがわかるように」記載する。以降、以前の Phase の内容から変更が生じた場合も同様の扱いとする。
3. **回答と対応方針**:
   - 進行のルールに **#12** を新設(後続 Phase での変更は変更元 Phase の該当箇所に定型マーカー `[Phase <N> 改訂]` を付す。本文・コードは残し差分を注記。index に「後続 Phase での改訂」節、Notes にも記録)。ルール #3 の「遡及リライトせず」を #12 に合わせて修正。
   - Phase 0 に反映: `Phase-0-2.md` §4.4・§5.3・§6・§8.1・§2.5、`Phase-0-3.md` §2.3、`textbook/Phase-0/samples/problem_schema.py`(冒頭コメント)、`phase-0-index.md`(「後続 Phase での改訂」節)。
   - 反映した改訂: ① `: TypeAlias` → PEP 695 `type` 文、② network_design を Phase 1 のユニオンから外し Phase 4 へ、③(同カテゴリの未処理分)objectives 評価器を Phase 1 → Phase 6。
   - マーカー形式は `[Phase <N> 改訂]`(greppable、絵文字なし)。【Phase 2 開始時に「以降 Phase で修正予定 ── Phase <N>-<M>」/「Phase <N> でサンプル修正」/「Phase <N> で確定」の 3 種に改称。読み手が「その Phase では samples のまま実装してよい」と分かるようにするため。ルール #12 の現行フォーマット参照】

**Q6.(Phase 1 生成後の指示)章内で作成する全ファイルの網羅的解説 / 章番号を作業単位に整列**

1. **Phase**: Phase 1(教材生成後)
2. **指示**: (a) `Phase-1-2.md`(作業単位 1-1)が `solutions/route_planner.py`・`shift_scheduler.py` に触れていない。各章はその章で作成する全ファイルを網羅的に解説する(設計理解の補完)。生成時にこれを確認する。(b) 章番号(`Phase-1-1`…)と作業単位(`1-1`…)が 1 ズレていて混乱する。概観章を `Phase-1-0` にし、章番号 = 作業単位番号にそろえる。新構成は他の Phase にも適用。(c) 改訂マーカー(ルール #12)は「提示コードの変更で解決される問題を記録する」趣旨。構成変更は上書きでよい。
3. **回答と対応方針**:
   - ルール #13 を新設(各章は新規作成ファイルを網羅的に解説。冒頭に「この章で新規作成するファイル」)。ルール #2 を「概観 = `Phase-N-0`、章番号 = 作業単位番号」に、#12 に「構成・体裁・番号の変更はマーカー対象外・上書き」を明記。
   - 案1(番号を整列、作業単位概念は残す)を採用。案2(作業単位廃止)は Phase-0-9 §7 等への波及が大きく見送り。
   - Phase 1: `Phase-1-1`→`Phase-1-0`、`1-2`→`1-1`…`1-6`→`1-5` にリネーム(git mv)。旧 `Phase-1-7`(作業単位 1-6+1-7)を新 `Phase-1-6`(1-6)/ 新 `Phase-1-7`(1-7 + Phase 2 引き継ぎ)に分割。参照(章リンク・§)を一括で上書き更新(マーカーは付けない)。`Phase-1-1` に「解の葉モジュール」節と問題葉のフル解説を追加。
   - Phase 0: 章番号は変えず `Phase-0-0.md`(概観)を新設。`Phase-0-*` の `[Phase 1 改訂]` マーカーは本文を残し章参照のみ新番号に。
   - 反映: Phase-1 全 8 章 + `phase-1-index.md` + `samples/README.md` + `CLAUDE.md`(ルール #2/#3/#11/#12/#13)+ `Phase-0-0.md` 新設 + `Phase-0-2/0-3/phase-0-index/problem_schema.py` の参照更新。

**Q7.(Phase 1 生成後の指示)概観章 `Phase-N-0` を index に統合し `Phase-N-introduction.md` に一本化**

1. **Phase**: Phase 1(教材生成後、Q6 の直後)
2. **指示**: `phase-1-index.md` と `Phase-1-0.md` は内容が重複している。`Phase-N-0` の内容を index に統合し、`Phase-N-1` 以降の作業章を始める前に理解しておくべき内容はこの 1 本で説明しきる構成にする。ファイル名は `Phase-N-introduction.md`。これはルールとして各 Phase の index 作成に代替する。
3. **回答と対応方針**:
   - ルール #2 / #6 / #11 / #12(3) を改訂。#6 =「Phase 毎に導入ファイル `Phase-<N>-introduction.md` を作成(従来の index + 概観章を 1 本に統合)」。別建ての `Phase-<N>-0.md` は作らない。
   - `git mv phase-1-index.md Phase-1-introduction.md` / `git mv phase-0-index.md Phase-0-introduction.md`。`Phase-1-0.md` を introduction に統合(11 節)→ `git rm`。`Phase-0-0.md` を統合(9 節)→ `git rm`。
   - 参照を一括更新(構成変更につき改訂マーカーは付けない・上書き)。`Phase-0-3.md` の `[Phase 1 改訂]` マーカー参照先は `Phase-1-introduction.md` §7 に張り替え(マーカー本文は据え置き)。
   - 反映: `Phase-1-introduction.md` / `Phase-0-introduction.md`(統合)、全 `Phase-1-*.md` の参照、`Phase-0-3.md`、`CLAUDE.md`(ルール #2/#6/#11/#12 + Notes 参照 + 本 Q7)。

**Q8.(Phase 1 実装中の質問 → ルール化)テスト観点に「テスト対象 / ドライバ / スタブ」を明記する**

1. **Phase**: Phase 1(作業単位 1-1 の写経中)
2. **質問・指示**: `test_route_problem_builds_and_narrows` に対してスタブ・ドライバの関係にあるのはどれか、という質問。回答を受けて「テスト観点の項目に『テスト対象 | ドライバ | スタブ』の関係を明記する」ルールを追加する指示。CL 開発の趣旨として「テストを通じた設計理解を重要視する」。README に「進行のポイント(メモ)」を追記済みで、この趣旨の補足も依頼。
3. **回答と対応方針**:
   - `test_route_problem_builds_and_narrows` の関係: **ドライバ** = テスト関数本体(+ pytest)。ビルダー fixture `build_route_problem` は入力生成なのでドライバ側。**スタブ** = 該当なし ── SUT(共通スキーマの判別ユニオン)が純粋な値オブジェクトで外部依存を呼ばない(Phase 0-3 の純粋レイヤー設計の帰結)。
   - ルール **#14** を新設(各章の `## テスト観点` 節で SUT / ドライバ / スタブの関係を明記。スタブ不要なら理由込みで。用語は初出章で 1 行定義)。
   - **ユーザー指示で範囲を限定**: `Phase-<N>-introduction.md` §10 実装前チェックリストの「テスト観点」列は追記不要(簡潔さ優先)。`Phase-0-9.md` §1 への用語アンカー追加も不要(用語は各章に簡潔に)。#11 / #13 は変更しない。
   - 反映: `CLAUDE.md`(#14 + 本 Q8 + 所感 1 行)、`textbook/Phase-1/Phase-1-1.md`〜`Phase-1-7.md` の `## テスト観点` 節(全 7 章)、`README.md`「進行のポイント(メモ)」に補足 5 点(SUT/ドライバ/スタブの言語化、スタブ要否は設計の鏡、わざと赤にして境界確認、`pytest -s` / `-rP` / `model_dump_json`)。

**Q9.(Phase 1 実装中の報告 → ルール化)章またぎの前方依存でテストが通らない(registry → dijkstra)**

1. **Phase**: Phase 1(作業単位 1-2 の写経中)
2. **報告・指示**: `Phase-1-2.md`(1-2)で作る `registry.py` が `from app.algorithms.graph.dijkstra import DijkstraStrategy` を持ち `REGISTRY` に登録しているが、`dijkstra.py` は 1-4 で作成予定。1-2 を写経した時点で `test_registry.py` が `ModuleNotFoundError`、かつ多くのテストが「dijkstra 登録済み」を前提にしていて緑にならない。各章のテストを「その章までに作ったファイルだけ」で完結させるか、後の章で作る分は暫定的にコメントアウトする構成にしてほしい(対策は Claude が提案)。
3. **回答と対応方針**:
   - 依存マップ調査 ── 前方依存は **registry.py → dijkstra.py の 1 箇所だけ**。他章は問題なし。
   - **ハイブリッド対策**: (a) `registry.py` は `DijkstraStrategy` を import ごとコメントアウトして出荷(既存の Phase 4/5 strategy と同じパターン)、(b) `test_registry.py` は `_FakeStrategy` を `monkeypatch.setitem(REGISTRY, ...)` で差し込んで registry の**機構**をテスト(具体アルゴリズムに依存しない)、(c) 1-4(`Phase-1-4.md` §7)で「コメントを外す手順」+「dijkstra が route_planning から引ける」テストを持つ。
   - ルール **#15** を新設(章の samples は「その章までのファイルだけ」で import 解決・緑。集約モジュールの前方参照はコメントアウト + マーカー、参照先を作る章がコメント解除 + 配線テスト。機構テストはフェイク。フル検証は end 状態で回す)。
   - #14 との整合: 1-2 の `test_registry.py` はスタブ相当(fixture で REGISTRY に差し込む `_FakeStrategy`)を持つことになり、その章の SUT/ドライバ/スタブ例がより正確になった。
   - 反映: `CLAUDE.md`(#15 + 本 Q9)、`samples/app/algorithms/registry.py`、`samples/tests/unit/test_registry.py`(再設計)、`samples/tests/unit/test_dijkstra_strategy.py`(登録テスト追加)、`Phase-1-2.md` §2/§5、`Phase-1-4.md`(§7 新設 + 章頭 + §8 テスト観点)、`samples/README.md`、`Phase-1-introduction.md` §10(1-2/1-4 行)。

**Q10.(Phase 1 実装中の質問)`bfs_shortest_path` を複数の最短経路に対応させるべきか**

1. **Phase**: Phase 1(作業単位 1-3 の探索プリミティブのテスト作成中)
2. **質問**: タイ(同じ長さの最短経路が複数)のあるグラフで、テストが特定の 1 本を `==` で assert すると BFS が返すもう片方では落ちる。`bfs_shortest_path` を「全最短経路を返す」形に拡張するのは複雑か。
3. **回答と対応方針**:
   - BFS 本体の変更は小さい。`parent: dict[str, str]` → `parents: dict[str, list[str]]`、訪問済みノードでも `elif dist[nxt] == dist[node] + 1:` で「別の最短予測子」を記録(再エンキューはしない)。復元が「親チェーン 1 本を辿る」→「再帰的に木を展開」に変わり、戻り値は `list[str]` → `list[list[str]]`。
   - **本質的な問題は組合せ爆発**。最短経路の本数はグラフサイズに対して指数的になりうる(n×n 格子の角から角で C(2n, n) 本)。全列挙 API はメモリを吹き飛ばすリスクがある。実務では最短経路 DAG(予測子構造)を圧縮表現として持ち、遅延展開 / 上限付き列挙にする。
   - **DeciTima に全最短経路を要る消費者は無い**(route Validation は到達可能性のみ、`DijkstraStrategy` は経路 1 本を提示、Phase 3 比較は別アルゴリズム同士)→ **YAGNI**。`bfs_shortest_path` は単一経路のまま。
   - タイの「どの 1 本か」を仕様化したいなら、近傍を `sorted(adjacency.get(node, ()))` で見る等の**決定的タイブレーク**が安価(実装ほぼ据え置き、テストで `==` を正当に書ける)。**提案(未採用・ユーザー判断)** ── 適用は別途指示。
   - テスト側の当座の対策: タイのあるグラフでは完全一致でなく「長さ + 端点 + 経路の妥当性(連続ペアが辺)」または「有効な最短経路の集合に含まれる」で検証する(サンプルの `test_bfs_shortest_path_len_matches_distance` がその形)。
   - 反映: 本 Q10 のみ。**コード・samples の変更なし**(提示コードに確定した変更が無いため進行のルール #9 は対象外)。

**Q11.(Phase 1 実装中の質問)`test_deterministic_same_input_same_output` は何を確認しているか(`f(x) == f(x)` は自明では?)**

1. **Phase**: Phase 1(作業単位 1-4、`test_dijkstra_strategy.py` を読んでいる最中)
2. **質問**: `assert _STRATEGY.solve(p).model_dump() == _STRATEGY.solve(p).model_dump()` は左辺と右辺が同じなので `==` は当たり前では?
3. **回答と対応方針**:
   - 左辺・右辺は同じ「値」だが同じ「オブジェクト」ではない ── `solve` を 2 回**別々に実行**し、ダイクストラを頭から 2 回まわして結果が完全一致するかを見る。
   - `f(x) == f(x)` は `f` が純粋関数なら自明だが、純粋でなければ成り立たない。このテストは `solve` の純粋性(NFR-1 再現性)を機械的に守る番人。赤になるケース: `self` に状態を溜める(`_STRATEGY` は registry と同じ 1 インスタンス共有)/ 入力 `p` の破壊的変更 / モジュールレベルのキャッシュ / 時刻・乱数・uuid / 浮動小数の累積順の非決定性。
   - `.model_dump()` は比較を明示的にし失敗時の diff を読みやすくするため(モデルの `==` でも動く)。
   - このテストが捕まえないもの: プロセス間で変わる `PYTHONHASHSEED`(両 `solve` は同一プロセス)。それは期待値ハードコードのテスト(`test_respects_forbidden_edge_and_required_node` の `== ["A","B","C","E"]`)が担当。「同じ入力→同じ出力」と「既知の正解と一致」の 2 種類で再現性をカバーする。
   - 反映: 本 Q11 のみ。コード・samples の変更なし。

**Q12.(Phase 1 実装中の相談)JSONB を使わない / 他 DB に切り替えても設計は成り立つか**

1. **Phase**: Phase 1(作業単位 1-5 の永続化を写経中)
2. **相談**: 現設計は JSONB 前提。JSONB を使わない、または他の DB に切り替えても正常に動くか(DB 移植性を考慮に入れたい)。
3. **回答と対応方針**:
   - **破綻しない**。JSONB は最適化であって構造的前提ではない。`JsonB = JSON().with_variant(JSONB(), "postgresql")` が既に移植性の縫い目 ── Postgres は JSONB、それ以外は汎用 JSON にフォールバック。Phase 1 のユニットテストがインメモリ SQLite で毎回走っている時点で「JSONB 無しでも動く」は常時検証済み。
   - JSONB が要るのは **payload の中身を DB レベルでクエリするとき**だけ(`metrics.total_weight > 100` の絞り込み、GIN 包含検索など)。MVP(Phase 0〜6)にその箇所は実質ゼロ ── すべて id か実カラム(`problem_type` / `status` / `algorithm_name` / `user_id` / `created_at`)経由。Phase 0-8 の「検索キーのみカラム化」方針そのもの。
   - 移植性の縫い目: ① リポジトリ層が永続化の唯一の接点(差し替えは `models/optimization.py` + `repositories/optimization.py` に閉じる)② `.with_variant()` 型 ③ ハイブリッド Pydantic スキーマは DB を知らない純 Python。
   - 他の SQL DB(MySQL / SQLite 本番)は現設計で可能。作業はマイグレーションの方言別再生成 / `DateTime(timezone=True)` の tz 挙動差 / payload 内インデックスは Postgres 限定なので諦めるか実カラム化。
   - ドキュメント DB(Mongo 等)は大きい ── `users ↔ problems ↔ solutions` の FK / 認証・conversation が SQL 前提 / SQLAlchemy ごと差し替え。ハイブリッド Pydantic スキーマは無傷。
   - **この設計の真の DB 依存は「JSONB」でなくリレーショナルな FK 関係**。JSONB を外すと「検索が Python 側 or 実カラム経由になる」だけ。
   - 対応: **この相談を記録するのみ**(ユーザー選択 ①)。「MVP は payload 内クエリ禁止・実カラムに昇格」の明文化や payload 往復テスト追加は今回見送り。必要になった Phase で再検討。

**Q13.(Phase 1 実装中の報告)`test_solve_api.py` が全部エラー/404 ── `tests/api/conftest.py` 未列挙 + `solve_router` 登録が 1-7 送り**

1. **Phase**: Phase 1(作業単位 1-6 の写経中)
2. **報告**: `test_solve_api.py` を走らせると 4 件 `fixture 'api' not found`、1 件 `assert 404 == 401`。
3. **回答と対応方針**:
   - 原因 2 つ。① `api` フィクスチャの定義元 `tests/api/conftest.py` が Phase-1-6 の「この章で新規作成するファイル」に無く、写経漏れになりやすい(進行ルール #15 のフィクスチャ条項に反する)。② `solve_router` の集約(`app/api/routes/__init__.py` 追記)が Phase-1-6 §5 で「1-7 §3」に送られていたが、`test_solve_api.py` は 1-6 のテストでルート登録に依存 → 未登録だと 404(Q9 と同じ章またぎ前方依存)。
   - 対応: `solve_router` の集約を **1-6 に移す**(`algorithms` / `solutions` は 1-7 のまま ── 各ルートはそれを作る章で集約に足す)。`tests/api/conftest.py` を Phase-1-6 の新規作成ファイルに明記。テスト用フィクスチャ(`tests/fixtures/optimization.py` は 1-1、`tests/fixtures/fake_redis.py` は 1-6)も samples README の作業単位表に列挙。
   - 反映: `Phase-1-6.md`(章頭 + §5 に `solve_router` 集約の手順 + §6 の conftest 注記)、`Phase-1-7.md`(章頭 + §3 を「2 本」に)、`samples/README.md`(既存追記表を solve=1-6 / algorithms・solutions=1-7 に分割、作業単位表にフィクスチャ追記、1-4 の registry コメント解除も追記)、`Phase-1-introduction.md` §10(1-6 / 1-7 行)。samples コードの変更は無し(`__init__.py` は元々 samples に入れない「既存への追記」)。
   - 検証: overlay end 状態で pytest 91 passed 維持。`solve_router` のみ登録した「1-6 状態」の部分 overlay で `test_solve_api.py` 5 passed。

**Q14.(Phase 2 開始時のスコープ確認)shift の V&V を Phase 2 で実装するか / `verifications` テーブルをどうするか**

1. **Phase**: Phase 2(教材生成の開始時)
2. **質問**: (a) Phase 1 は route 限定の V&V 骨格を通した。shift 側の Validation / Verification を Phase 2 で実装するか、Phase 6(shift strategy = Greedy / Backtracking)へ送るか。(b) 旧 7 単位の 2-7「`verifications` テーブル」(検証結果を `Solution.payload` から別テーブルへ切り出す)をどう扱うか。
3. **回答と対応方針**:
   - (a) **Phase 2 で実装する**(Phase 6 に送らない)。Phase 1 の objectives 撤回の先例は転用不可 ── objectives は「探索中に解を採点する機構」で消費アルゴリズムが無ければ無意味だが、V&V は事前 / 事後の純粋なチェックで、Phase 1 で凍結済みのデータモデル(`ShiftData` / `ShiftSolution` / `StaffingConstraint`)に対して働く。`POST /verify` が手組み shift 解の実消費者になる。README §19 も「Phase 1 の route 限定 V&V を全 kind・shift へ一般化する」と定義。deferする と Phase 2 が Phase 1 の骨格とほぼ重複する ~3 章に痩せる。shift strategy 本体は Phase 6 のまま。
   - (b) **`verifications` テーブルは作らない**。1 行の見送り注記のみ(`Phase-2-introduction.md` §7 非スコープ表 + 本 Notes、`Phase-0-8.md` §4 引用)。MVP に payload 内クエリ需要が無く、取得はすべて id / 実カラム経由(Q12)。「決定だけの章」も作らない ── ルール #3 の三重管理を生むため(`Phase-0-8.md` §4 が既にスケッチ)。→ Phase 2 は 6 章(2-1〜2-6)。
   - 反映: `textbook/Phase-2/` 一式(introduction + 2-1〜2-6 + samples)、Phase 1 / Phase 0 への「以降 Phase で修正予定」マーカー、本 Notes の「Phase 2 の主要決定」節。あわせてマーカー表記を統一(旧 `[Phase <N> 改訂]` → `[以降 Phase で修正予定 ── Phase <N>-<M>]` / サンプル修正 / で確定 の 3 種。ルール #12 を改訂)。

**Q15.(Phase 2-2 の教材レビュー中)到達可能性チェックの置き場所と、`dijkstra.py` / `reachability.py` を統合しない理由**

1. **Phase**: Phase 2(2-2 の教材レビュー中)
2. **質問・相談**:
   - (a) `Phase-2-2.md` §3 の「CL 開発の狙い」注記(「`import` 1 本が層の方向を破る制約が判断を作った」)をもっと詳しく解説してほしい。
   - (b) (a) を受けて ── 一般的な筋で考えて `_route_unreachable` が service に置くべきものなら、その「形に起こすステップ」が教材に要るのでは。現場レベルの設計を目指すのが前提。
   - (c) `dijkstra.py` と `reachability.py` が同階層(`app/algorithms/graph/`)にいながら統合されない理由。
3. **回答と対応方針**:
   - (b) 正しい指摘。到達可能性は他の Semantic 検査(`check_route_endpoints` 等 = 問題フィールドの純粋述語)と**種類が違う** ── 隣接リストを組んで BFS を走らせる「計算」。整理: 計算そのものは `route_reachable(data, forbidden) -> bool` を**新規 `app/algorithms/graph/reachability.py`**(`build_adjacency` + BFS の薄い合成)に起こす。それを hard ゲートとして**判定**するのが `ProblemValidationService.validate`(services)。domain は不関与。`domain → algorithms` の import 禁止は「計算を domain に置く」誤りを写経中に顕在化させる **guardrail** であって、判断の理由ではない ── 理由は「これは計算か? 述語か? この責務はどの層のものか?」。`134dc3b` でコード(`_route_unreachable` インライン → `route_reachable` 抽出)+ `Phase-2-2.md` §3 再構成 + `README.md` CL 開発「特徴とメリット」+ 本 Notes「Phase 2 の主要決定」+ 所感に反映。
   - (c) `dijkstra.py` = **`AlgorithmStrategy`**(`registry` に載る / `AlgorithmMeta` を持つ / `CandidateSolution` を返す / 消費者 `SolveService`)。`route_reachable` = **アルゴリズム・プリミティブ**(`Phase-0-4.md` §2.4 / `Phase-1-3.md` §1 の「2 層」の下側。registry 非搭載 / 素の関数 / 消費者 `validation.py`)。`search/` に `bfs.py` `dfs.py` `binary_search.py` が別ファイルで並ぶのと同じ「**1 ファイル 1 関心事**」。変更理由も消費者も別なので統合しない(`Phase-0-2.md` §2.5)。共有する `build_adjacency` は第 3 の関心事で、Phase 4 でグラフプリミティブを整理するとき独立させる。`Phase-2-2.md` §3 に比較表 + 3〜4 行で追記。
   - 併せて `Phase-2-2.md` §2 の `validate()` コード sketch が抽出前の `self._route_unreachable(...)` のまま残っていたのを修正(§3 だけ直して §2 を直し忘れていた)。

**Q16.(横断)README §19 の各 Phase に「設計のポイント」を明記する**

1. **Phase**: 横断(Phase 2 進行中)
2. **指示**: `README.md` の開発 Phase(§19、Phase 0〜15)の各エントリに設計のポイントを明記する。現状は `**目的：…**` + 成果物の箇条書きのみで「なぜその設計・順序か」が README 単体では追えない。
3. **回答と対応方針**:
   - 各 Phase エントリの箇条書きの後・`---` の直前に **`### 設計のポイント` 小節(H3)+ 2〜4 箇条書き**を挿入(全 15 Phase)。
   - 内容の軸は**理由・トレードオフ + 主要な成果物名**(`AlgorithmStrategy` / `route_reachable` / `network_design` 等は可、細かいシグネチャは不可)。textbook との三重管理を避けるため「なぜ」の高度に留める。
   - Phase 3〜15(textbook 未生成)も **Phase 0 設計スケッチ由来の確定的な筆致**で記述(ユーザー選択)。Phase 0 / 1 / 2 の末尾に `詳細: textbook/Phase-<N>/Phase-<N>-introduction.md` リンクを追加。
   - README 既存体裁を踏襲(GitHub admonition は未使用なので使わない)。変更は `README.md` のみ(+ 本 Notes)。

**Q17.(Phase 3 開始時のスコープ確認)UI の踏み込み / numpy / benchmark_runs**

1. **Phase**: Phase 3(教材生成の開始時)
2. **質問**: (a) 「アルゴリズム比較UI / 可視化」をどこまでやるか(decitima-ui はテンプレートのまま・chart ライブラリ無し・`src/features/` 未作成)。(b) 集計に numpy を入れるか(Phase-0-9 は計画済みだが `statistics` で足りる)。(c) `benchmark_runs` テーブルを Phase 3 で作るか(`verifications` を見送った前例あり)。
3. **回答と対応方針**:
   - (a) **UI も完全な samples 作業単位**(選択肢: backend 全部 + UI 設計章のみ / UI も完全 samples / backend のみ)。→ `textbook/Phase-3/samples/ui/src/**` を新設、overlay 検証も 2 リポジトリ分。3-5(feature 骨格)/ 3-6(チャート + ページ)。ただし**可視化ライブラリは足さず**手描き SVG を拡張(Phase 4 で本格選定)。
   - (b) **Phase 0 の計画どおり numpy を追加**(選択肢: `statistics` で保留 / numpy 追加)。`measure_call` の中央値・四分位集計だけに使う。`pyproject.toml` に `numpy>=2.0`。
   - (c) **`benchmark_runs` を作る**(選択肢: 作る + `GET /benchmarks/{id}` / インライン返却のみ)。Phase-0-8 §2 の計画どおり。`Problem` への FK は張らない。
   - 反映: `textbook/Phase-3/` 一式(introduction + 3-1〜3-6 + samples)、Phase 0 への「[Phase 3 で確定 / サンプル修正]」マーカー(`Phase-0-3.md` §6.3 / `Phase-0-5.md` §4 / `Phase-0-7.md` §3.4 / `Phase-0-8.md` §2 / `Phase-0-9.md` §2・§5)、Phase 1 / 2 samples の該当ファイルへの「以降 Phase で修正予定」マーカー、Phase 1 / 2 introduction の「後続 Phase での改訂」節、README §19 Phase 3 設計のポイントの追記、本 Notes の「Phase 3 の主要決定」節。

**Q18.(プロジェクト全体相談)pandas を導入するならどの機能にどう活用できるか**

1. **Phase**: Phase 3(教材生成の直後)
2. **相談**: このプロジェクトに pandas を導入するとしたら、どの機能にどのような形で活用可能か。Phase 3 以外(Phase 3 以前を含む)での活用可能性も知りたい。
3. **回答と対応方針**:
   - **活用は 3 レイヤー**: ① **分析トラック**(`decitima-api/backend/analysis/`、dev 依存、`app` から切り離し)── Phase 3(benchmark)→ 4(route bench)→ 5(手実装 vs OR-Tools の破綻境界・Pareto)→ 9(Sensitivity)→ 11(benchmark 由来の推薦決定表)→ 13(**LLM vs Algorithm の実験フレームワーク ── 中核成果**)→ 14(CI 性能回帰)を貫く背骨。② **入力アダプタ**(`app/adapters/`、runtime 依存だが `domain` 非依存の縁)── Phase 6(スタッフ名簿 Excel)/ 7(タスク一覧)/ 8(車両・配送)が本命。「スプレッドシートをアップロード」UX を作る Phase で追加。③ **テストオラクル**(`tests/`)── Phase 2 の shift 検証 / Phase 4 のグラフ統計で使いうるが限界的、遡及しない。
   - **入れない**: `app/domain` `app/algorithms`、solve/verify/benchmark のリクエスト経路、Phase 0〜1。**Phase 0〜2(実装済み)への遡及変更は不要**。
   - ユーザー選択で **① 分析トラックを作業単位 3-7 として Phase 3 に組み込む(フルセット)**。`analysis/{db,export,loaders,benchmark_report,plots}.py` + sample データ + notebook。上の「Phase 3 の主要決定」に詳細。
   - 反映: `textbook/Phase-3/Phase-3-7.md`(→ Q24 で `Phase-3-8.md` にリネーム)+ `samples/analysis/**` + `samples/tests/analysis/**`、`Phase-3-introduction.md`(§4/§7/§8/§10/§11)、`samples/README.md`、`Phase-0-3.md` §6.1・`Phase-0-9.md` §5 のマーカー、`decitima-api/CLAUDE.md` の「分析トラック」節、README §18・§19。

**Q19.(設計思想の相談)`Phase-3-1` §1.1「numpy はここだけ」の合理性 / numpy をフル活用しない理由**

1. **Phase**: Phase 3(教材生成の直後、Q18 の続き)
2. **相談**: (a) numpy を `measurement.py` だけに閉じることに、他で使わないメリットはあるか。(b) このアプリを numpy(scipy 含む)フル活用で仕上げた場合のメリット・デメリット、あえてそうしない理由。
3. **回答と対応方針**(ユーザー選択: 議論のみ・教材本体は現状維持。要約を Notes に記録):
   - **(a) メリットはあるが numpy 固有でなく「純粋レイヤー規約 + 依存の局所化」の一適用**。① `algorithms/` が numpy を使うと「アルゴリズムを理解」でなく「numpy/scipy を呼べる」証明に格落ち(§21・「手実装トラック(主軸)」)。② 局所化 = swap 可能・監査可能(`statistics` でも代替可)。③ `import numpy` 〜100ms は純粋関数テスト(<1ms × 数千件)と衝突。④ 唯一の使用箇所 + コメントが境界を対比で教える。正直な補足: `statistics.median` / `quantiles` でこの用途は足りる。numpy を入れるのは Phase-0-9 §5 の計画 + Phase 3-4 のカーブ / Phase 14 の回帰分析 + `analysis/` が pandas 経由で既に numpy を持つ、ため。制限のコストはほぼゼロ(`app/` で numpy が効くのに `algorithms/` でない場所が実質無い)。
   - **(b) numpy フル活用のデメリット(★★★ = プロジェクトの根幹を壊す)**:
     - ★★★ **ポートフォリオの核が崩れる** ── `scipy.sparse.csgraph.dijkstra(matrix)` は「scipy を読める」証明で、優先度キューの settle 不変条件・計算量の導出を示さない。採用側が「書ける候補」と「呼べる候補」を区別できない。
     - ★★★ **`_ops` 計測が不能に** ── Phase 3 ベンチは heap pop / 探索パス数を*自分のコードの中で*数える。numpy だと仕事が C の中。「手実装 vs 産業ソルバー」比較(明示目標)と Phase 14 の LLM vs Algorithm が同じ土俵を失う。
     - ★★★ **「いつライブラリに切り替えるか」の教訓が消える** ── 2 トラック設計は Phase 6(shift 手実装破綻 → OR-Tools)の切り替え点を実測で見せるため。最初から全部ライブラリなら発見すべき破綻点も教訓も無い。
     - ★★ 再現性の表面積(float64 累積順・BLAS・シード)/ 論理バグが形状・dtype バグに置換 / 疎グラフで密行列が O(V²) 無駄 / hot path の依存重量。
   - **numpy フル活用のメリット**: 実行速度 10〜100 倍(大規模)、コード量減、`scipy.sparse.csgraph` で実装工数減、実務リアリティ(numpy 流暢さ自体が市場価値)。
   - **あえてしない理由(核)**: DeciTima の価値提案は「実装でき・分析でき・推論でき、かつ手実装をやめて産業ソルバーに切り替える点を知っている」。それを担保するのが ① 説明できる手実装 ② 自分のコードを計測するベンチ ③ 切り替え点を見せる 2 トラック。numpy フル活用はこの 3 つを「scipy を呼べる」に置換する。速度より 学習 + ポートフォリオ + 検証可能性 を選んでいるので(README「再現性・制約遵守・検証可能性・アルゴリズム比較」)、numpy を絞るのは**制限でなく整合**。
   - **ニュアンス**: 「numpy 一切なし」ではなく「**ラベル付き境界の裏に置く**」── 手実装トラック = numpy なし、産業ソルバートラック(Phase 4 networkx / Phase 6 OR-Tools / Phase 9 scipy)= 中身は numpy/scipy、分析トラック = numpy/pandas。この分離があるから比較が意味を持つ。目標が「速い本番サービス」なら numpy フル活用が正解で手実装が無駄になる。
   - 反映: 本 Q19 のみ(教材・samples の変更なし)。

**Q20.(覚書)DeciTima ベースの「数値ライブラリ全面版」フォークへの置き換え影響調査**

1. **Phase**: Phase 3 完了後(Q19 の続き)
2. **相談**: DeciTima 完成後、これをベースに numpy / pandas 等フル活用版を別プロジェクトで作りたい。置き換えを前提とした設計にしておきたいので、予めライブラリ置き換えの影響調査だけしておきたい。スキーマ・コアの配列ネイティブ化まで想定。
3. **回答と対応方針**:
   - 影響調査ドキュメント `textbook/appendix/library-fork-impact.md`(新設 `textbook/appendix/`)を作成。8 節: ①目的・スコープ(2 トラック=並存 との違い / レベル A=strategy だけ・レベル B=スキーマまで)②置き換え表面カタログ(部品ごと 現行/置き換え先/seam/friction)③現行設計が既に置き換え可能な理由(Protocol / `meta.implementation` / 全境界 Pydantic / 独立 Verification / registry / analysis / 依存遅延)④レベル A の friction(id↔index アダプタ / `_ops` 計測不能 / 再現性テスト緩和 / 依存重量)⑤置き換えフック候補①〜⑤(今は入れない。Phase 4〜15 で任意)⑥レベル A の結論(約 8 割は契約で吸収)⑦レベル B(推奨: edges Pydantic/msgspec + 内部 `ProblemArrays` の hexagonal 化。レイヤー別インパクト表)⑧レベル B の結論(`domain/` の作り直しだが外部契約=REST JSON・DB JSONB・decitima-ui は同一に保てる「同じ外皮・別の中身」)。
   - **結論: 現行 DeciTima 側で今やるべきことは無い**。seam(`AlgorithmStrategy` Protocol / `schemas` ↔ `domain` 分離)が既に明確。フック⑤(schemas/domain 分離を Phase を追うごとに厳格に保つ)だけ意識。
   - **移植しない部品**: `brute_force.py`(厳密オラクル)/ Verification ロジック / `metrics["_ops"]` 計装 / 教材そのもの ── フォークでも自前で持つ。
   - 反映: `textbook/appendix/library-fork-impact.md`(新規)、`CLAUDE.md` 本 Q20、`README.md` §8「実装方針」末尾に 1 行ポインタ。現行 Phase 教材・samples・コードは不変。

**Q21.(設計相談)Phase 3 Benchmark のレイヤーごとのファイル分割粒度**

1. **Phase**: Phase 3(3-3 の教材レビュー中)
2. **相談(2 段階)**:
   - (a) Benchmark コードが `models/` `schemas/` では `optimization.py` に混在、`repositories/` `api/routes/` では `benchmark.py` に分離。合理的意図はあるか / 別ファイルに統一して models–repositories–schemas–routes の対応を見えるようにすべきでは。
   - (b) 調査結果を踏まえ再検討依頼:「1:1:1:1 はファイル構成のみでの判別性が高いと考えたが、短いコードのために別ファイルを作ると管理上の問題も生じる。import 文を見れば格納先は明白。最適な構成を提案してほしい。」
   - (c) 追加質問: Phase 3 までは計算基盤、Phase 4 以降は Web サービス性が強まる。その場合フォルダ分けルールは 1:1:1:1 に近づくと予想されるか。
3. **調査(Explore 2 本)で判明**:
   - **1:1:1:1 は既存コード・テンプレートに無い**。テンプレートは層ごとに軸が違う(models = 集約ルート、`conversation.py` に `Conversation`+`Message` / schemas = エンドポイント群 `chat.py` / repositories = DB アクセスのある集約だけ、`base.py` は対応なし / routes = URL プレフィックス、`auth.py` は model 無し / services = ユースケース)。
   - **routes / services を `benchmark.py` に分けたのは正しく既存 DeciTima と整合**(`solve` / `verify` / `solutions` / `algorithms` が既に操作単位。`Phase-0-3.md` §2.3 が `services/benchmark.py` を予告済み)。
   - **唯一の不整合は `repositories/benchmark.py` を別ファイルにしたこと**。`Phase-0-8.md` §5 は「全 repo を `repositories/optimization.py` に同居」と定めており理由の記載がない。動機はおそらく「そのファイルを触ると samples の現行版再出荷 + マーカーが要る」という **samples 運用の都合**が設計に漏れたもの。repo は model と 1:1 が期待される層なので「repo だけ別 / model は共有」が紛らわしさの正体。
4. **回答と対応方針(ユーザー確定)**:
   - **`repositories/benchmark.py` を廃止し `BenchmarkRunRepository` を `repositories/optimization.py` へ同居**(唯一の変更)。model / schema / read-service は共有のまま、route / service は `benchmark.py` のまま。
   - 確定ルール: **data 層(model / schema / repository)は「永続化の関心事」で 1 ファイル(`optimization.py` = Problem / Solution / BenchmarkRun。全部 JSONB payload の「最適化レコード」)。`api/routes` / `services` は「操作」で割る。格納先はファイル名の対応でなく import で辿る**(`models/__init__.py` が全 re-export)。「短いから別ファイル」はしない ── 分けるのは変更理由と消費者が別のとき(`Phase-0-2.md` §2.5)。`models/benchmark.py` / `schemas/benchmark.py` は作らない。
   - **(c) への回答: Phase 4 以降も 1:1:1:1 には近づかない**。理由 ── ① Web サービス化は route / service 層で起きる(既に操作単位なので機能追加 = ファイル追加で自然に伸びる。Phase 10 の `POST /simulate` は「スキーマ不変・新テーブルなし」と README 明記)② data 層は `Phase-0-8.md` のハイブリッド JSONB スキーマで意図的に狭い(problem_type ごとにテーブルは増えない。新タイプは `app/domain/` の判別ユニオンへ)③ 速く増える `app/domain/` `app/algorithms/` は既に「1 概念 1 ファイル」で最大限に割れ、models / repos と 1:1 でない ④ 1:1:1:1 は原理的に成立しない(`verify` は model / repo なし、`algorithms` は registry のみ)⑤ LLM(Phase 11–13)は 1:1:1:1 でなく別の境界づけられたコンテキスト(既存 `conversation` / `message` / `app/ai/` を再活性化、「本流の外・スキーマ経由でのみ接続」)。**変わるのは「集約の数」だけ** ── 本物の新集約(`Project` 等)が出たら既存ルールどおり model + repo + schema + route の一式を持つ(`user.py` / `conversation.py` と同型)。ルール自体は不変。
   - 反映: samples(`repositories/benchmark.py` 削除 → `repositories/optimization.py` 現行版に `BenchmarkRunRepository` 同居、`services/benchmark.py` + 2 テストの import 追従)、`Phase-3-3.md` §2.2/§2.3(「レイヤー分割の粒度」小節新設)、`Phase-3-introduction.md`、`textbook/Phase-3/samples/README.md`、`Phase-1/samples/app/repositories/optimization.py` のマーカー、`Phase-1-introduction.md` の改訂節、`Phase-0-8.md` §5 のマーカー + `Phase-0-introduction.md` §8 の表、`decitima-api/CLAUDE.md`、本 Notes(Q21 + Phase 3 主要決定 + 所感)。overlay 検証: **165 passed / 3 deselected**、ruff / pyright clean。

**Q22.(コード読解)service 等の先頭 `_` 付き関数・変数は何の慣習か**

1. **Phase**: Phase 3(3-3 の写経中)
2. **質問**: service 等で使われる `_` 始まりの関数・変数は、具体的にどのルール・慣習に基づくか。
3. **回答と対応方針**:
   - **根拠 = PEP 8 の「先頭アンダースコア 1 個 = 非公開(internal / "protected")」**。Python に `private` は無く、これが「公開しない」を表明する唯一の手段。本リポジトリは lint 強制なし(ruff `select` に `N`(pep8-naming)が無い)── 規律で守る「読み手への約束」。
   - **言語が実際に強制するのは 2 点だけ**: ① `from m import *` が `_` 名を読み込まない(`__all__` で上書き可)② クラス内の `__name`(2 個)は name-mangling で `_Class__name` に化ける(本コードベース未使用)。それ以外(`self._x` に外から触る等)は言語的に可能・破っても動く。
   - **このコードベースでの 4 つの現れ方**:
     - `self._attr` ── インスタンス属性の非公開。クラスの公開面は公開メソッドだけ(`self._session` / `self._repo` / `self._validation` / `self._rate_limiter` ── `services/solve.py` `services/benchmark.py` `repositories/base.py`)。route 層は `SolveService(session, redis).solve(...)` を呼ぶだけで `._session` に触らない ── `_` がその境界をコードで文書化。
     - モジュールレベル `_func` / `_CONST` / `_TypeAlias` ── モジュールの外から import させない内部部品。モジュールの公開 API = `_` なしの名前(+ `__all__`)(`_soft_penalty`=`verification.py` / `_annotate_quality_ratio`=`benchmark.py` / `_timed_call`=`measurement.py` / `_OPS`=`domain/constraints/numeric_bound.py` / `_Adjacency`=`dijkstra.py` の `type` 文 / `_STRATEGY`=テストモジュール)。
     - `for _ in range(...)` ── 束縛するが使わない使い捨て変数(`measurement.py`)。
     - `metrics["_ops"]` ── **プロジェクト独自**。dict の *キー* に `_` を付けて「診断用の内部指標。目的値ではない・time/memory のようにアルゴリズム間で比較しない」を表す(`dijkstra.py` / `brute_force.py` / `benchmark.py`、Phase 3 教材で明記)。
   - 補足: 末尾 `_`(`type_` 等)はキーワード/組込み衝突回避 ── 本プロジェクトは `NumericBoundConstraint.operator` フィールドで未使用(属性名なので stdlib `operator` と衝突しない、と Notes に既記)。`__dunder__` は言語予約で自作しない。
   - **`_` の有無は設計判断そのもの**: `_CHECKERS`(Phase 1、モジュール内ディスパッチ表)→ `CHECKERS`(Phase 2、domain のレジストリとして他モジュールから参照される公開物になったので `_` を外した)。
   - 反映: 本 Q22 + `## コード提示・コメント規約` に「命名: 先頭 `_`」の節を追加。教材本体・samples・コードは変更なし。

**Q23.(設計理解)decitima-ui で DTO 型は `src/lib/api/types.ts`、store / hooks は `src/features/` に置く差は何か**

1. **Phase**: Phase 3(3-5 の写経中)
2. **質問**: backend の type は既存テンプレの `@/lib/api/types` に書き、store / hooks は独立ファイルを `features/` 内に置いている。この差は何か。
3. **回答と対応方針**(Q21 のフロント版。コード変更なし):
   - **差 = 「外部システム(backend)との契約の記述」か「この feature 自身の振る舞い・状態」か**。`decitima-ui` は 3 段の層:
     - `src/lib/api/`(ドメイン非依存の共有プラミング)── backend と話す *機構* と *語彙*。`apiFetch`(認証ヘッダ / 401 サイレントリフレッシュ / エラーパース)/ `ApiError` / `cache.ts`(`isCacheFresh`)/ **`types.ts`**。変更理由 = backend の schema が変わったとき。
     - `src/features/optimization/api/`── この feature が叩く *具体的な呼び出し*(`runBenchmark` → `POST /api/v1/benchmark`)。「どの URL をどの形で叩くか」は feature 知識。
     - `src/features/optimization/{stores,hooks,components}/`── この feature の *状態・React バインディング・UI*(`useBenchmarkStore` の TTL キャッシュ / `useBenchmark` / パネル)。
   - **型が共有層に居る理由**: ① 型は純粋な記述(振る舞い・状態がない)= 共有しても結合ゼロ ② backend の契約は 1 つ。`OptimizationProblem` / `CandidateSolution` / `AlgorithmMeta` は将来の feature(経路可視化・ガント)も共通で使う ③ テンプレが `types.ts` を「backend schema の手書きミラー(OpenAPI 生成なし。`Phase-0-3.md` §6.2)」と定めており、「TS 型 ↔ `app/schemas/` がズレていないか」の突き合わせを 1 ファイルに閉じたい。
   - **store / hooks が feature ローカルな理由**: 状態を持つ / React に依存する / optimization の外で意味を持たない。テンプレの「store は使う場所に colocate、`src/lib/stores/` のような集約は作らない」慣習どおり(実例: `components/auth/auth-store.ts` / `components/ui/timer/timer-store.ts`)。`src/hooks/` は「何を処理するか」で命名した汎用フック置き場で、`useBenchmark` は benchmark 固有なので対象外。
   - **backend の Q21 とまったく同じ原則**: 型 / schema(= 契約の語彙)は共有・エリアでまとめる。振る舞いは使い方(feature / 操作)でまとめる。backend: `schemas/` 共有 + `services/`・`routes/` を操作で分割。frontend: `types.ts` 共有 + `stores/hooks/api` を feature で分割。
   - DTO が増えたら `types.ts` を `lib/api/types/optimization.ts` 等に割ることはあり得るが、それは共有層 `lib/api/` 内の再編であって `features/` への移動ではない。
   - 反映: 本 Q23 + `decitima-ui/CLAUDE.md` の「DeciTima 固有」節に 2〜3 行。教材本体・samples・コードは変更なし。

**Q24.(デバッグ + 章再構成)benchmark 画面が 401「Could not validate credentials」/ 最小ログイン UI をどこに入れるか**

1. **Phase**: Phase 3(3-6 相当の benchmark 画面をブラウザで試した時)
2. **質問**: デモ問題で「実行」押下 → 401。(1) 先に認証機能の実装が必要か (2) 認証はどのタイミングで呼ばれているか。
3. **原因**: 未ログイン → `apiFetch`(`src/lib/api/client.ts`)は `auth-store` の `accessToken` が `null` なので `Authorization` ヘッダを付けずに送信 → backend `POST /api/v1/benchmark` が `current_user: CurrentUserDep`(`app/api/deps.py::get_current_user`)を**ハンドラ本体より前に**解決 → Bearer 無しで `_credentials_exception`(401 "Could not validate credentials")。`apiFetch` の 401 分岐は `accessToken` が無いので silent-refresh をスキップし `ApiError` を throw → `benchmark-store` が `status:"error"` に。
4. **回答**:
   - **(Q1)** backend の JWT 認証(`/api/v1/auth/{register,login,refresh}`)と UI の認証ストア(`auth-store.ts` + `RequireAuth` / `LoginRequiredDialog`。`loginHref="/login"` 前提)は**テンプレートで実装済み**。不足は「実トークンを取得してストアに入れる導線 = ログインフォーム」だけ。benchmark/solve/verify は設計上認証必須(`Phase-0-7.md` §6.1。`benchmark_runs` の user_id スコープ)。→ **最小ログインフォームを作る**(認証を外すのは非推奨)。
   - **(Q2)** クライアント = `apiFetch`(全 API 呼び出しで `auth-store` の `accessToken` を読みヘッダ付与、無ければ付けない)。サーバー = FastAPI が `POST /benchmark` のハンドラ実行前に `CurrentUserDep` 依存を解決 → `get_current_user` が Bearer トークンを decode。無し/不正/期限切れ → 401。
   - **章再構成(ユーザー確定 = 案 F)**: ログインを **3-5** に挿入。旧 3-5(features 骨格)→ 3-6、旧 3-6(チャート + ページ)→ 3-7、旧 3-7(分析トラック)→ **3-8**(`git mv` のみ・中身不変)。
     - **なぜログインを 3-5(feature の前)か**: benchmark のページ章(3-7)はブラウザで実 backend に繋ぐ初の UI で前提が「ログイン済み」。api 層/stores/hooks(3-6)は mock で認証不要だがその先で必ず要る。`LoginForm` は `src/components/auth/`(app-shell 部品、`src/features/` より下の層)── 下の層から積む依存方向。
     - **なぜ分析を Phase 4 に移さず 3-8 に据え置きか(案 A でなく F)**: ① 旧 3-7 は執筆・コミット・overlay 検証済み ── 移設は検証済み教材の再配置になる(3-7→3-8 は純粋な `git mv`)② `analysis/` は「`benchmark_runs` を掘る章」なのでその表が生まれる Phase 3 に置くのが素直 ③ 「Phase 4 で豊富なデータ」の深掘りは案 F でも Phase 4 が既存 `analysis/` に report を足す形で行う(当初計画「育てる器」どおり)── 移すのは誕生 Phase の命名だけ ④ 横断ドキュメント(README §18/19、Q18、Notes)の書き換えコストは案 A のほうが大きい。
   - **実装(主に decitima-ui。backend は dev シードのみ追加)**: 新規 `src/components/auth/{auth-api.ts,LoginForm.tsx}` + `src/app/(pages)/login/page.tsx` + テスト 2 本。変更 `auth-store.ts`(`refreshTokens()` を `/auth/refresh` の `AccessToken` 契約に修正 ── 下記「検証で発覚」)、benchmark `page.tsx` を `RequireAuth` で包む(3-7 で新規作成時に)、`types.ts` に `TokenPair` / `AccessToken`。
   - **テストユーザーのシード(ユーザー指示で追加)**: `decitima-api/backend/scripts/{__init__,seed.py}` を新設(`analysis/` と同じ「`app/` の上」の dev スクリプト置き場。`uv run python -m scripts.seed`)。`UserService.create_user` で固定ユーザー `example-user@example.com` / `sample-user-0123`(`full_name="sample-user"`)を 1 人作る。`UserAlreadyExistsError` を握って冪等。dev 専用。テンプレート還元候補。overlay 検証: `alembic upgrade head` → `python -m scripts.seed` 2 回で「作成 → skip」、ruff / pyright 0 errors。反映: `Phase-3-5.md` §8、`samples/scripts/**`、`samples/README.md`、`Phase-3-introduction.md`、`decitima-api/README.md`「開発用シード」、`decitima-api/CLAUDE.md`「`scripts/`」節。
   - 反映: `Phase-3-5.md` 新設、`git mv` 3 本 + 全参照の番号更新(構成変更なのでマーカー無し・上書き。ルール #12)、`Phase-3-introduction.md` / `samples/README.md` / `README.md` §19 / `Phase-0-3.md` §6・`Phase-0-7.md` §6.1・`Phase-0-9.md` §5 / `textbook/appendix/library-fork-impact.md` / `decitima-ui/CLAUDE.md`、本 Q24 + 主要決定 + 検証事象。ui overlay 検証: `npx vitest run src/components/auth src/features/optimization` **11 passed**、`npx tsc --noEmit` clean、`npx eslint` clean(`Menu.test.tsx` の既存 1 失敗は無関係)。

**Q25.(コード読解)`app/core/database.py`(`Base` / `get_db`)と `analysis/db.py`(`session_scope`)の比較**

1. **Phase**: Phase 3(3-5 の scripts / 3-8 の analysis を読んでいる時)
2. **質問**: (a) `class Base(DeclarativeBase)` は何のため / どこで使う / なぜ本体にコードが無いか。
   (b) ① `get_db()` に `@asynccontextmanager` は不要か ② セッションは使用後に破棄が必要か / しない方がよいか。
3. **回答**(コード変更なし):
   - **(a) `Base`** = SQLAlchemy 2.0 の宣言的マッピング基底。全 ORM モデルが継承(`User` / `Problem` /
     `Solution` / `BenchmarkRun` / `Conversation` / `Message`)。提供するのは ① クラス ↔ テーブルの
     マッピング機構 ② **`Base.metadata`**(全 `Table` の集合)。使用箇所: `app/models/*.py`(継承)/
     `app/repositories/base.py`(`CRUDRepository[ModelType: Base]` の型境界)/ `alembic/env.py`
     (`target_metadata = Base.metadata` ── autogenerate の基準)/ `tests/*/conftest.py`
     (`Base.metadata.create_all`)。本体にコードが無いのは `DeclarativeBase` を継承するだけで機構が
     揃うから(docstring だけのクラス本体は valid)。共通カラム/mixin をここに書く選択肢はあるが本
     プロジェクトは各モデルで明示(`Phase-0-8.md` §4)。1.x の `declarative_base()` 関数が 2.0 で
     クラス継承に変わった。
   - **(b)① `@asynccontextmanager` は不要かつ付けてはいけない**。`get_db` は自分で呼ぶ CM ではなく
     **FastAPI の依存関数**(`SessionDep = Annotated[AsyncSession, Depends(get_db)]`)。FastAPI が
     「`yield` を持つ依存」を内部で `AsyncExitStack` にラップする(yield 前=setup / yield 値=注入値 /
     yield 後=後処理)。付けると `_AsyncGeneratorContextManager` オブジェクトが注入され `AsyncSession`
     が取れない。**対比**: `analysis/db.py::session_scope` は `analysis/export.py` が `async with` で
     **直接呼ぶ**ので `@asynccontextmanager` 必須。
   - **(b)② セッションは close される必要があり、`async with AsyncSessionLocal() as session:` が
     自動でやる**(手動 `close()` は書かない)。close = 未コミット rollback + ORM 切り離し +
     **接続をプールへ返却**(物理切断ではない)。**「破棄しない方がよい」のはエンジン/プール** ──
     `engine` はモジュールシングルトンでアプリ寿命いっぱい。リクエストごとの `engine.dispose()` は
     禁物。`engine.dispose()` はアプリ終了時 1 回(`app/main.py` の `lifespan`)。`analysis/db.py` が
     `finally` で `engine.dispose()` するのは、そこで作ったのがスクリプト実行専用の使い捨てエンジン
     だから。
   - 補足: `AsyncSessionLocal` の `expire_on_commit=False` は、サービス層が `commit()` した後に
     ルート層が ORM オブジェクトから Pydantic レスポンスを組む(async で `commit` 後の遅延ロードは
     `MissingGreenlet` になりやすい)ため。
   - 反映: 本 Q25 + `Phase-3-8.md` §2 に「`session_scope()` と `get_db()` の違い」対比表。コード変更なし。

**Q26.(コード読解・Q25 の続き)`async_sessionmaker` の引数比較 / `@asynccontextmanager` と `engine.dispose()` / `get_db` のセッション寿命**

1. **Phase**: Phase 3
2. **質問**: (1) `analysis/db.py` の `async_sessionmaker(engine, expire_on_commit=False)` と
   `app/core/database.py` の `async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)`
   ── ① `engine` と `bind=engine` の違い ② `class_=AsyncSession` が無いこと。
   (2) ① `@asynccontextmanager` を付けるとき `finally: await engine.dispose()` が推奨か
   ② `get_db()` はアプリが立ち上がっている限りセッションが持続するか。
3. **回答**(実シグネチャを `.venv` で確認。コード変更なし):
   - **(1)① `async_sessionmaker(engine)` == `async_sessionmaker(bind=engine)`**。第 1 位置引数が `bind`。
   - **(1)② `class_` は `async_sessionmaker` のデフォルトが `AsyncSession`** なので `analysis/db.py` の
     省略で同じ結果(`app/core/database.py` の明示は冗長・害なし)。sync の `sessionmaker` はデフォルト
     `Session` なので、そちらでは指定に意味がある。あわせて `autoflush` の差: `app` は `False` 明示
     (repo が `session.flush()` を明示で呼ぶスタイルに合わせる)、`analysis/db.py` は読み取り専用
     (export)なので指定せずデフォルト `True` のまま。`expire_on_commit=False` は両方明示。
   - **(2)① 「`@asynccontextmanager` だから dispose」ではない**。`dispose()` の要否は
     「**エンジンを自分で `create_async_engine` したか / 共有を借りただけか**」で決まる。
     `analysis/db.py` は CM の中で使い捨てエンジンを作るので `finally` で dispose するのが正しい。
     共有 `app.core.database.engine` を借りる CM を書くなら dispose してはいけない(共有プールを壊す)。
   - **(2)② No**。`get_db()` のセッションは **1 リクエストの寿命**。FastAPI がリクエストごとに `get_db`
     を呼び、`async with AsyncSessionLocal() as session:` に入り、レスポンス送信後に抜けて `close()`。
     次のリクエストは新しい session。**アプリ寿命いっぱい生きるのは `engine`(プール)と
     `AsyncSessionLocal`(ファクトリ)** であって個々の session ではない。プール内の物理コネクションは
     session を跨いで再利用される(「session が持続」でなく「接続が再利用される」)。寿命は 3 層:
     engine/factory = アプリ寿命 / 物理接続 = プールが再利用管理 / session = 1 リクエスト。
   - 反映: 本 Q26 + `Phase-3-8.md` §2 の対比表下に脚注(`async_sessionmaker` の引数差 + 寿命の 3 層 +
     dispose は自作エンジンのときだけ)。コード変更なし。

**Q27.(Phase 4 開始時のスコープ確認)UI の範囲 / 図ライブラリ / 負辺の扱い / 複数経由地**

1. **Phase**: Phase 4(教材生成の開始時)
2. **質問**: (a) Phase 4 の UI をどこまで samples 化するか(Phase 3 は完全な作業単位にした)。
   (b) 経路図・ネットワーク図の描画 ── 本格ライブラリ(React Flow 等)を選ぶか、手描き SVG を継続するか
   (Phase 3-6 §1 が「選定は Phase 4」と明記)。(c) Bellman-Ford の主題は負辺・負閉路。`RouteEdge.weight`
   は `Field(ge=0)`(Phase 1 で凍結)── どう扱うか。(d) 複数必須経由地(小 TSP)を Phase 4 で扱うか。
3. **回答と対応方針**(すべてユーザーが選択):
   - (a) **Route Planner / Network Designer 両方フル samples**(Phase 3 と同格。入力 UI + 可視化 +
     複数アルゴリズム比較)。→ `textbook/Phase-4/samples/ui/**` に 2 feature slice。
   - (b) **手描き SVG を継続拡張**。`src/components/ui/charts/GraphCanvas.tsx` を新設(ドメイン非依存 =
     還元候補)。**本格ライブラリ(recharts / React Flow 等)は入れない**。→ `Phase-0-3.md` §6.3 に
     「Phase 4 で確定 ── 入れない」マーカー。Phase 4 のグラフはデモ規模で手描きで十分軽く、
     「手実装を主軸に境界の裏だけライブラリ」の一貫性を保てる。
   - (c) **`RouteData.allow_negative: bool = False` フラグ + `RouteEdge.weight` の `Field(ge=0)` 撤廃 +
     `model_validator`**(親レベルのガードに移動)。既定は従来どおり負を弾く。→ Phase 1 の
     `route_planner.py` に「以降 Phase で修正予定 ── Phase 4-2」マーカー。
   - (d) **Phase 4 で扱う**。`m ≤ 8` は訪問順を順列全探索、各区間は Dijkstra/A*
     (`optimize_waypoint_order`)。→ `Phase-0-5.md` §5.3 / `Phase-1` の該当マーカーを「Phase 4 で確定」に。
     TSP の近似(m 大)は Phase 7 Travel Planner 送り。
   - 反映: `textbook/Phase-4/` 一式(introduction + 4-1〜4-11 + samples。**その後 Q29 で Phase 4(Route。4-1〜4-8)/ Phase 5(Network。5-1〜5-5)に分割**)、Phase 0 への「Phase 4 で確定」
     マーカー(`Phase-0-2.md` §8.1 / `Phase-0-3.md` §6.3 / `Phase-0-4.md` §4・§6 / `Phase-0-5.md` §5.3 /
     `Phase-0-9.md`)、Phase 1 / 2 / 3 samples の該当ファイルへの「以降 Phase で修正予定」マーカー、
     Phase 1 / 2 / 3 introduction の「後続 Phase での改訂」節、README §18・§19 Phase 4、本 Notes の
     「Phase 4 の主要決定」節。

**Q28.(Phase 4 完了後の相談)`analysis/` 以外に pandas を使える部分はあるか / フル活用版フォーク前の構成確認**

1. **Phase**: Phase 4 完了後(numpy・pandas フル活用版フォークにかかる前の事前確認)
2. **質問**: 現時点の機能想定で `analysis/` 以外に pandas を活用できる部分はどこか。フロント/バックの
   連携は JSON なのでフロント側で group-by / sort ができ pandas のメリットが薄いと分かった。一方、
   大規模データの加工・分析には pandas が有効。Phase 4 以降で作る Web アプリに pandas を組み込むなら
   どういう構成を想定しているか。フォーク作成前に確認しておきたい。
3. **回答と対応方針**(Q19 / Q20 と同じく議論のみ。教材/samples/コード 変更なし):
   - **(A) 現行設計ではリクエスト経路(`app/domain` / `app/algorithms` / solve・verify・benchmark)に
     pandas の居場所は実質ゼロ ── 意図的**。pandas が効くのは 3 条件が揃うとき ── ①列が異種混在
     ②多数行の group-by / join / pivot / 時系列リサンプリング ③I/O フォーマットの多様性。DeciTima の
     リクエスト経路は **1 問題ずつ・サイズ有界・構造化済み(Pydantic)** なので、どれも当てはまらない。
     README §8 の「コア層に numpy を入れると崩れる 3 つ」(説明できる手実装 / `_ops` の自己計測 /
     2 トラックの切り替え点教訓)+ 再現性の表面積 + テスト速度は pandas にもそのまま効く。
   - **(B) tabular に「見える」ロードマップ機能と、なぜ pandas でないか**:
     - Shift Scheduler(P6): staff × day × slot グリッド ── 小さい(20×7×3≈420)。計算は組合せ探索 /
       OR-Tools CP-SAT(aggregation でない)。時間帯集計は**手実装プリミティブ**(Prefix Sum /
       Difference Array = imos 法 ── カリキュラムの学習項目)。ソルバー化しても配列は OR-Tools の中
       (numpy がソルバー seam の裏)、pandas ではない。
     - Project Manager(P8): task は `list[Task]` Pydantic。ガントは Critical Path(グラフ)+
       Difference Array(資源平準化)で計算する timeline レイアウト。group-by / pivot が無い。
     - Logistics(P9): ロールアップ(総距離/コスト/稼働率/遅延リスク)は数本のルートの `sum()` / `max()`
       = 素の Python。距離行列は numpy/scipy がソルバー seam の裏。
     - What-if Simulation(P10): N シナリオ × M 指標 の行列 ── **最も pandas 的**だが N は小
       (README §13 の例は 3 行)M は固定。`list[dict]` → JSON で十分。掃引が大きくなる
       Sensitivity Analysis は**明示的に `analysis/` 送り**(P10 は `analysis/` を育てる Phase)。
     - Benchmark(P3+): numpy(`measurement.py`、中央値・四分位のみ)+ `analysis/`(pandas、
       オフライン)── 既に配置済み。
   - **(C) 唯一あり得るリクエスト経路の居場所 = `app/adapters/`(入力アダプタ)── 将来機能が要求したら**。
     README には無いが「スタッフ名簿の Excel をアップロード」等の UX を P6/P8/P9 で足すなら(Q18 の②):
     `app/adapters/` は `domain` / `algorithms` の**兄弟**(中に入れない)、**inbound 専用の縁**
     (`xlsx/csv bytes → 検証・整形 → OptimizationProblem`。一方向、戻り経路なし)。pandas はここなら可
     ── I/O 境界コード(DB 層と同じ位置づけ)、hot な solve 経路でない、Pydantic を吐いたら消える。
     `[project.optional-dependencies]` `ingest = ["pandas", "openpyxl"]` でゲートし、未インストールなら
     そのルートを mount しない(appendix フック③ と同じ)。adapter は schema 以外の
     `domain`/`algorithms` を import しない・逆も無い(hexagonal ports)。
   - **(D) フォークの本質 ── numpy と pandas は役割が違う**。「numpy・pandas フル活用版」は実質
     **numpy-in-core** プロジェクト(appendix の Level B: `ProblemArrays` @dataclass + ndarray、
     ベクトル化 DP / 距離行列 / bool 行列 Verification)。**pandas の footprint はフォークでもほぼ
     増えない** ── リクエスト経路は ndarray 形(数値計算)であって DataFrame 形(列指向分析)では
     ないため。pandas が居場所を得るのは `analysis/`(オフライン集計)と入力アダプタ(フォーマット
     解析)で、そこはフォークでも現行と同じ。フォークは `analysis/` を「主役」にするだけ
     (appendix §2)。「numpy/pandas フル活用」を 1 括りにするのが罠 ── 別のデータ形に対する別の
     ツール。**結論: Phase 4+ の Web アプリに「pandas を組み込む構成」は無く、フォークでも変わらない。
     現行 DeciTima 側で今やるべきことは無い**(appendix §8 の結論と同じ)。
   - 反映: 本 Q28 + `textbook/appendix/library-fork-impact.md` §9「pandas の位置づけ ── フォークでも
     edges のまま」。コード・samples 変更なし。

**Q29.(構成相談)Phase 4 を Phase 4 + Phase 5 に分割し、現 Phase 5 以降を +1 ずらすのは実装の流れとして不自然か**

1. **Phase**: Phase 4 の教材生成後(11 章 + samples が完成した状態)
2. **相談**: Phase 4 は他フェーズに比べ章数・ファイル数が多い。Phase 4 を **Phase 4(Route Planner)+ Phase 5(Network Designer)** に分け、現 Phase 5(Shift Scheduler)→ 6、以降を +1 ずらし、Phase 0〜6 を MVP とするのは実装の流れとして不自然か。
3. **回答と対応方針**:
   - **不自然ではない ── むしろ現行の束ね方が例外**。① README §12 は Route Planner(§12.1)と Network Designer(§12.6)を同格の製品機能として並べており、他の製品機能はすべて 1 機能 = 1 Phase。Phase 4 で 2 機能を束ねたのは「どちらもグラフ問題で Phase 1 資産を再利用」という理由だけの例外措置。② 実装の順序は 1 ミリも変わらない(primitives → Bellman-Ford → A* → waypoints → networkx →(Phase 5)network_design 配線 → MST → UI)。Phase 境界が中間に入るだけ = レビュー / コミット / 実装前チェックリストの単位が小さくなる。③ `network_design` はもともと「判別ユニオンに 1 メンバー + registry に 1 キー、既存に触れない」設計(`Phase-0-2.md` §8.1)── 分割で衝突するファイル書き換えはゼロ、増分編集のみ。④ **Network Designer 単独 Phase = 「新 problem_type を端から端まで足す」の実演教材**になる(Phase 1 以来初の新 problem_type、Phase 6 以降の雛形)。⑤ CL 開発の【重点課題】「進行スピードが担保できない」への直接の対策 ── 11 章 Phase がまさにその課題が指すもの。
   - **今やる理由**: 写経は未着手(`decitima-api/backend` は Phase 3 end 状態)。Phase 5〜14 の textbook はまだ存在しない ── 番号ずれのコストは「README + CLAUDE.md ×3 + Phase 0〜4 の前方参照 + samples コメント」だけで、ディレクトリ rename の連鎖は無い。後になるほど増える。
   - **ユーザー確定事項**: (1) Phase 5 = **5 章**(5-1 Union-Find / 5-2 MST 理論(独立章)/ 5-3 network_design 配線 / 5-4 Kruskal・Prim・networkx_mst / 5-5 Network Designer ページ)。(2) 番号ずれ(現 Phase 5〜14 → 6〜15)は教材分割と**同時に一括反映**、中途半端な状態を作らない。(3) README §20 MVP = **Phase 0〜6** で確定(成果物リスト不変 ── Route Planner / Network Designer / Shift Scheduler + 基盤)。
   - 反映: `textbook/Phase-4/` を Route 8 章に整理(旧 4-8/4-9/4-10 → 4-6/4-7/4-8、旧 4-1 から Union-Find 節を除去)、`textbook/Phase-5/` 新設(introduction + 5-1(新規)+ 5-2(新規)+ 旧 4-6/4-7/4-11 を移設 → 5-3/5-4/5-5)、samples を route / network に分割(共有ファイルは Phase 4 = route-only 版 / Phase 5 = full 版)、Phase 0〜3 samples のマーカーを route(`Phase 4-N`)/ network(`Phase 5-N`)に振り分け、番号ずれ ~262 行(README §8/§19/§20、CLAUDE.md ×3、Phase 0〜3 前方参照、appendix)、本 Q29 + 「Phase 4 の主要決定」節を Phase 4 / Phase 5 に分割 + README §19 に新 Phase 5 エントリ。overlay 検証: Phase 4 route-end `uv run pytest` **176 passed** / ui **13 passed**、Phase 5 network-end **206 passed** / ui **16 passed**(いずれも 2 deselected、ruff / pyright / tsc / eslint clean。既知の baseline 2 件は写経先の重複定義で Phase 4/5 と無関係)。

**Q30.(写経中のテスト報告)`test_graph_primitives.py` が写経漏れを検知できなかった / リファクタで壊れた過去 Phase のテストをどうするか**

1. **Phase**: Phase 4-1(§3 の書き直し後、ユーザーが 4-1 を写経した段階)
2. **報告**: ① `test_graph_primitives.py` は緑だったが、`waypoints.py` の写経漏れ(`ModuleNotFoundError`)は Phase 1 の `test_dijkstra_strategy.py` を回して初めて発覚した ── テスト項目が不十分では? ② 写経漏れ解消後、`test_dijkstra_strategy.py` が「変更前後の違い」で失敗した。要望: (②-1) `test_dijkstra_strategy.py` を記法変化に対応させ、コメントで変更前後が分かるように。(②-2) 過去 Phase で似たテストをした場合は再実行を促し、変更にかかるエラーが出るならテスト内容も対応させる ── ルール化。
3. **回答と対応方針**:
   - **① は正しい**。4-1 は 3 ファイル(`adjacency` / `segments` / `waypoints`)を新規作成し `dijkstra.py` を大改修するのに、章が指定するテストは `adjacency.py` しか import していなかった(進行のルール #15 の趣旨に反する ── その章のファイルだけで緑を保証するには、その章の全ファイルをテストが触っていなければならない)。→ `test_graph_primitives.py` を拡張(`plan_route` にフェイク区間を注入、`optimize_waypoint_order` にフェイク cost、`collect_route_constraints` / `route_solution`)。import が `segments → waypoints` を辿るので 3 ファイルのどれかの写経漏れで **collection が赤**になる。**#15 に「章が作る全ファイルをその章のテストが 1 度は import する」条項を追加**。
   - **② は写経バグ**(教材のせいでもある)。調査: `test_dijkstra_strategy.py` の 6 件は**正しい samples では全部緑**(公開挙動 `solve()` は不変)。ユーザーの `dijkstra.py` が `_dijkstra_segment` の末尾を `return _reconstruct(prev, start, goal, dist[goal]), pops` でなく `_reconstruct(prev, start, goal, weight)`(`return` 無し・`weight` 未定義・`, pops` 無し)と写していた → `_dijkstra_segment` が `None` を返し `plan_route` で `TypeError`。遠因は §3.3 の書き直しが `solve` の before/after しか見せず、**まさにユーザーが間違えた `_dijkstra_segment` / `_reconstruct` の変化を見せていなかった**こと。
   - 対応: (②-1)`test_dijkstra_strategy.py` は**アサーション不変**(挙動が変わっていないから)。docstring に「before → after の変更点」と「赤なら refactor の写経ミス(このテストが番人)」を追記し、**Phase 4 samples の現行版**として置く(Phase 1 samples にマーカー、#12.2 A/B)。§3.3 に `_dijkstra_segment` 末尾 + `_reconstruct` の before/after を追加。(②-2)**進行のルール #16 を新設** ── 章が以前の Phase のテスト済みコードをリファクタするとき、その章のテスト観点に「以前の Phase の該当テストを再実行する」を明記。公開挙動が不変なら現行版を samples に + docstring 注記、変わるなら更新版テスト。#15(前方)と対の後方参照ルール。
   - あわせて `Phase-4-4.md` の「4-2 で作った `waypoints.py`」誤記を「4-1 で作成済み」に是正(検証で発覚した事象欄)。
   - 反映(1 回目): `CLAUDE.md`(#15 追加条項 / #16 新設 / 本 Q30 / 検証で発覚した事象 / 所感)、`Phase-4-1.md`(§3.3 に `_dijkstra_segment`・`_reconstruct` の before/after、§テスト観点を書き直し、`waypoints` 素朴版表現の是正)、`Phase-4-4.md`(waypoints 作成 Phase の是正)、`Phase-4/samples/tests/unit/{test_graph_primitives.py 拡張, test_dijkstra_strategy.py 新規=現行版}`、`Phase-1/samples/tests/unit/test_dijkstra_strategy.py`(マーカー)、`Phase-4/samples/README.md` / `Phase-4-introduction.md`。
   - 反映(2 回目 ── フォローアップ): 上記でも詰まりが解けなかった(`TypeError` → `_dijkstra_segment` の結びつけに手間取る)ので、`test_graph_primitives.py` に `DijkstraStrategy().solve()` **統合スモーク**を追加(章の第一テストが写経ミスをその場で赤にする)、samples `dijkstra.py` に「写経の罠」コメント、§3.3 に「写経ミスの見分け方」、#16 に「第一の番人は当該章の第一テストに統合スモーク」の一文。overlay `ov4` route-end **183 passed / 2 deselected**。
   - 適用範囲は 4-1 の修正 + #16 新設のみ(Phase 2〜5 の遡及監査はしない ── ユーザー確定)。

**Q31.(教材レビュー)`bellman_ford.py` / `a_star.py` の経路復元がインラインで、`dijkstra.py` の `_reconstruct` と共通化されていないのはなぜ / 後で共通化する予定はあるか**

1. **Phase**: Phase 4-2(Bellman-Ford の samples を読んでいる最中)
2. **質問**: `_bellman_ford_segment` / `_astar_segment` の末尾の経路復元(`prev` を goal から辿って `Segment` を組む 7 行)は `dijkstra.py` では `_reconstruct` に分離されているのに Bellman-Ford / A* ではインライン。なぜ? 後の Phase で関数化・分離・Dijkstra との共通化を行う予定があるならその旨知りたい。
3. **回答と対応方針**:
   - **意図的な設計ではなく不整合**。経路復元(`prev: dict → node_ids/edge_ids → Segment`)は完全にジェネリックで Dijkstra 固有ロジックは 1 つも無い ── 3 strategy で 7 行が丸ごと重複していた。切り出さなかった遠因: `dijkstra._reconstruct` は `_` 始まり = モジュール非公開(規約)なので他モジュールから import できず、Bellman-Ford / A* はインラインで複製した。
   - **共通化の計画は教材に無かった**。しかも `Phase-4-1.md` §2 / `Phase-4-2.md` §2 は「strategy ファイルはアルゴリズムそのものに集中できる」と謳っており、現状(bellman_ford/a_star が復元をインラインで持つ)はその主張と食い違っていた。
   - **対応**: `_reconstruct` を `segments.py` の**公開関数** `reconstruct_path(prev, start, goal, weight) -> Segment` に昇格し、Dijkstra / Bellman-Ford / A* の 3 つが使う。ユーザー判断で **4-1 で最初から** segments.py に置く(Phase 4 開始時点で消費者が 3 つと設計上明白 ── 「知っている共通化は最初から共通の場所に」)。純粋なリファクタで挙動は不変。循環 import なし(`segments.py` は `Segment` を自前定義)。
   - 反映: samples(`segments.py` に `reconstruct_path` 追加、`dijkstra.py` の `_reconstruct` 削除 + import、`bellman_ford.py` / `a_star.py` のインライン 7 行を 1 行に、テスト docstring 2 本)、`Phase-4-1.md`(§ヘッダ / §2 / §3.3 移動表・before/after / §テスト観点 / §5 / §10 introduction 行)、`Phase-4-2.md` §2、`Phase-4-3.md` §1、`Phase-4-introduction.md`(§3 / §8 / §10)、`decitima-api/CLAUDE.md`、`appendix/library-fork-impact.md`。overlay `ov4` route-end **183 passed / 2 deselected**(件数不変)、ruff / format / pyright clean。`grep -c "node_ids = \[goal\]"` が 3 → 1。

**Q32.(教材レビュー ── Q31 の続き)`solve` 内の `plan_route(...)` 呼び出しは 3 strategy 共通だが、別関数でラップすべきか**

1. **Phase**: Phase 4(`dijkstra.py` / `bellman_ford.py` の `solve` を見比べている最中)
2. **質問**: `seg, ops = plan_route(data.start, data.goal, required, lambda a, b: _dijkstra_segment(adjacency, a, b))` という記述が `bellman_ford.py` にも同じ形である。共通だが処理は `plan_route` の呼び出しだけ。あえて別関数でラップしない判断は正しいか。それとも `関数名(start, goal, required, fn): return plan_route(start, goal, required, fn)` のようなラッパーを作るべきか。
3. **回答と対応方針**(コード変更なし・教材と Notes に記録のみ):
   - **ラップしないのが正しい**。提案のラッパーは純粋なパススルー = 「名前を変えた `plan_route`」で、呼び出し側は結局同じ 4 引数を組み立てる ── ロジックゼロの間接層が増えるだけ。直前の `reconstruct_path`(Q31)は 7 行の実ロジックが byte 一致・アルゴリズム非依存だったので抽出の基準を満たしたが、「既存関数を 1 回呼ぶだけ」は満たさない。
   - **`plan_route(...)` の行は seam(縫い目)として見えているべき** ── strategy が「自分の区間ソルバ(`_xxx_segment`)を共通足回りに手渡す」唯一の場所。`Phase-4-1.md` §2 の構図(strategy = アルゴリズムそのもの / `segments.py` = 共通足回り)で、`plan_route` はすでに抽出済みの機構。
   - **`solve` 本体のテンプレート化(`run_route_strategy(...)`)もしない**。本当に共通なのは `isinstance` ガード 2 行 + `return route_solution(...)` 1 行だけ。テンプレートにすると (a) Bellman-Ford の `try/except _NegativeCycle` が dijkstra/a_star の `if has_negative_weight` と形が違い「共通」の中に strategy 分岐が戻る (b) A* は `coords` を factory 経由で通す必要 (c) 読み手が `DijkstraStrategy.solve` を直線的なレシピとして追えなくなる。節約 ~3 行 vs 3 つの本物の strategy 差を隠す対価 ── 割に合わない。
   - **線引き**: 共通化するのは *機構*(`plan_route` / `reconstruct_path` / `route_solution` / `collect_route_constraints` / `build_adjacency`)であって *オーケストレーション*(`solve` 本体)ではない。
   - 反映: `Phase-4-1.md` §2 に bullet 1 つ(上記線引き)、本 Q32、所感 1 行。samples / 写経先は無変更。

**Q33.(教材レビュー)`NetworkxShortestPath` と `BellmanFordStrategy` に同じ `_negative_cycle_violation` が重複している ── 共通化すべきか**

1. **Phase**: Phase 4(4-2 / 4-5 の教材レビュー中)
2. **質問**: `bellman_ford.py` と `networkx_shortest.py` に同一の `_negative_cycle_violation() -> ConstraintViolation` が private 関数として重複定義されている。共通化して別ファイルに分離すべきではないか。
3. **回答と対応方針**:
   - **Q31(`reconstruct_path` の重複)と全く同型の見落とし**。しかも `segments.py` には既に同じ役割の兄弟関数 `negative_weight_violation(algorithm)`(Dijkstra / A* が消費)があり、「2 本の route strategy が消費する violation ビルダーは `segments.py` に公開関数として置く」という前例がその場に存在していたのに踏襲されなかった。
   - **対応**: `_negative_cycle_violation`(重複 2 本)を削除し、`segments.py` に公開関数 `negative_cycle_violation() -> ConstraintViolation`(引数無し ── メッセージがアルゴリズム名に依存しないため `negative_weight_violation` と違い引数を取らない)として 1 本化。1 本目の消費者である Bellman-Ford(4-2)の章で `segments.py` に追加し、2 本目の消費者 `NetworkxShortestPath`(4-5)はそれを import して再利用する形に揃えた ── Q31 の教訓「ヘルパの置き場は 2 本目の消費者で決まる、分かっているなら先回りする」をそのまま適用。
   - 両ファイルの `ConstraintViolation` import は(重複関数の削除で他に使用箇所が無くなったため)不要になり削除。テスト(`test_bellman_ford_detects_negative_cycle`)は `constraint_kind` の値だけを見ているため無変更で緑。
   - 反映: samples(`segments.py` に `negative_cycle_violation` 追加、`bellman_ford.py` / `networkx_shortest.py` の重複削除 + import 差し替え)、`Phase-4-2.md`(章頭の既存ファイル一覧・§2 のコード抜粋・共通足回り bullet)、`Phase-4-5.md`(§2 のコード抜粋コメント・bullet)、本 Q33。所感セクションへの追記は無し(Q31 が同種の教訓を既に言語化済みのため)。

**Q34.(教材レビュー ── ユーザーの写経前確認)`test_mst_properties.py` が 5-3 の `connectivity.py` / `network_design.py` に前方依存 ── 5-2 単独でテスト不能では**

1. **Phase**: Phase 5-2(`test_union_and_connected` の読解 → `test_mst_properties.py` の import 元の作成 Phase 確認)
2. **質問**: `test_mst_properties.py`(作業単位 5-2 の成果物)が `app.algorithms.graph.connectivity`(`forms_spanning_tree`)と `app.domain.problems.network_design`(`NetworkDesignData` / `NetworkLink`)を import しているが、どちらも 5-3 で作られる。5-2 まで写経した状態でこのテストは回るのか。#15(その章までのファイルだけで import 解決・テスト緑)に反していないか。
3. **回答と対応方針**(ユーザー選択: **テストと fixture を 5-3 へ移す**):
   - **反していた**。`test_mst_properties.py` と、5-2 で編集する `tests/fixtures/optimization.py` の network 部分(`build_network_problem` 系)の**両方**が 5-3 の `network_design.py` を import する。5-2 まで写経した状態で `pytest tests/unit/test_mst_properties.py` を回すと collection 段階で `ModuleNotFoundError`。`Phase-5-2.md` §5 に「章順の前方参照」と注記はあったが、#15 の処方(コメントアウト / フェイク / ローカルヘルパ → 後章で抽出)を取らず素の前方参照を許容していた ── Q9 / Q13 / Q30 で写経者が詰まった「章またぎ前方依存」と同じ構図。
   - **対応**: `test_mst_properties.py` と network fixture(`build_network_problem` / `build_network_solution` / `build_disconnected_network_problem` / `_NETWORK_LINKS`)を **5-3 の成果物**に移す。5-2 は cut / cycle property / 交換論法だけの**理論章(実装ファイルなし)**にする。列挙オラクルが必要とする schema(`NetworkDesignData`)と述語(`forms_spanning_tree`)が生まれる 5-3 に実測を置く ── Q31「ヘルパの置き場は消費側で決まる」と同型。さらに 5-3 の `test_network_design.py` も既に `build_network_problem` に依存しており、fixture は `network_design.py`(5-3 の葉)を import する以上そもそも 5-2 の clean な成果物になり得なかった。
   - **これは教材(Markdown)の章-attribution 変更のみ**。`samples/` のファイル内容・配置は変えない(samples = Phase 末 end 状態のフラット構成。`test_mst_properties.py` の docstring 冒頭「作業単位 N」表記だけ 5-2 → 5-3 に是正)。overlay 検証は **206 passed / 2 deselected** のまま。
   - 反映: `Phase-5-2.md`(§6 network fixture 削除、§5 は列挙オラクルを概念として残し前方参照の弁明を除去、テスト観点を「理論章 ── 実装なし」に)、`Phase-5-3.md`(章頭の新規/変更ファイルに追加、新 §7「network fixture と MST 理論の実測」、テスト観点に `test_mst_properties.py` の行、まとめを §8 に)、`Phase-5-introduction.md`(§4 章一覧 / §6 テスト階層 / §10 チェックリストの 5-2 ↔ 5-3)、`Phase-5/samples/README.md`(作業単位表、Phase 3 マーカーの `5-2` → `5-3`)、Phase 3 / 4 の network fixture マーカー(`Phase-3-introduction.md` / `Phase-4-6.md` / `Phase-4-introduction.md` / `Phase-4/samples/README.md` / `Phase-3/samples/tests/fixtures/optimization.py` の `.py` マーカー / `Phase-4/samples/tests/fixtures/optimization.py` の予告コメント ── いずれも `5-2` → `5-3`)、`CLAUDE.md`(Phase 5 主要決定 + 本 Q34 + 検証事象 + 所感)。

**Q35.(教材レビュー ── ユーザーの写経中の指摘)`Phase-5-3.md` の解説網羅性 ── `build_link_adjacency` を作る前に `validation.py` を編集させられた**

1. **Phase**: Phase 5-3(samples 写経中。`app/services/validation.py` の network 分岐を写す段で `build_link_adjacency` 未作成に気づいた)
2. **質問**: `Phase-5-3.md` は多数のファイル編集を案内するが、新規作成・編集されるファイル/関数の解説が網羅されていない(進行のルール #13)。
3. **回答と対応方針**(調査で 3 件判明。①はユーザー指摘、②③は関連して発見しユーザーが方針を選択):
   - **① 解説の欠落・順序の逆**:
     - `graph/connectivity.py`(**新規**、`all_nodes_connected` / `forms_spanning_tree`)── 章に名前が出るだけでコード・シグネチャ・責務が無かった。
     - `build_link_adjacency`(`adjacency.py` の**新規関数**)── 旧 §3 に 3 行の散文のみ、しかも**消費者 `validation.py` のスニペットの後**。`adjacency.py` が §1 の `network_design.py` を import する(= 葉を先に、写経ミスは route テストも巻き込む)ことも未記載。
     - `tests/unit/test_graph_primitives.py`(**5-3 で編集**、network プリミティブの 4 テスト)── **章に一切登場しない**(introduction §10 にも無い)。この 4 本が `build_link_adjacency` / `connectivity` 写経ミスの第一の番人。
     - `semantic.py` の 2 チェッカー / `test_network_design.py` ── シグネチャ / ファイル責務が薄い。
     - ~17 ファイルを触るのに**写経順序**が無い。
     - **対応**: `Phase-5-3.md` に新 §3「グラフ・プリミティブ ── `build_link_adjacency` / `connectivity.py`」を Semantic Validation の**前**に挿入(以降 §3→§4 … §8→§9 に繰り下げ)。`build_link_adjacency` / `connectivity` をシグネチャ + 中身 + 責務 + 依存(`adjacency.py` は `network_design.py` を、`connectivity.py` は既存 `bfs.reachable_nodes` を import)で解説。§3.3 で `test_graph_primitives.py` の 4 テストを組込み。§4 で semantic の 2 チェッカーをシグネチャ + 中身で提示。ヘッダ直後に**写経順序リスト**(葉 → ユニオン → プリミティブ → domain 述語 → services → チェッカー → fixture → テスト)。`connectivity.py` / `build_link_adjacency` のコードは変更しない(samples は正しい ── 足りなかったのは Phase-5-3.md の解説)。
   - **② `test_network_design.py::test_network_design_end_to_end_pipeline` が 5-4 への前方依存**(ユーザー選択: **5-4 へ移す**):validate→select→solve→verify を通すこのテストは `registry["network_design"]`(5-4 で登録)を要求し、5-3 状態は `NoAlgorithmError`(#15 違反。実測: 5-3 状態で 1 failed / 12 passed)。5-4 には strategy の solve テスト / select→kruskal テストはあるがフルパイプラインの統合テストが無かった。→ `test_mst_strategies.py`(5-4)へ移設。`test_network_design.py` は 9 本(スキーマ / semantic / 構造検証 / チェッカー)に。
   - **③ Phase 5 samples の `test_graph_primitives.py` が Phase 4 版を丸ごと置換**(ユーザー選択: **過去のテストを壊さない = Phase 4 版 + network 4 本の現行版に**):Phase 5 の版は network 4 テストだけを持ち、Phase 4-1 の route プリミティブテスト 11 本(`build_adjacency` / `plan_route` 連結 / `optimize_waypoint_order` / **Q30 で足した dijkstra リファクタの統合スモーク `test_dijkstra_solve_still_works_after_segments_refactor`**)を落としていた。overlay で上書きされるため Phase 5 end 状態でこれらが消失(実測確認済み)。→ Phase 5 版 = Phase 4-1 の全内容 + network 4 本の「現行版」に是正。
   - 反映: `Phase-5-3.md`(§3 新設 + 繰り下げ + ヘッダ写経順序 + semantic チェッカー展開 + テスト観点)、`Phase-5-4.md`(移設テストの受け入れ ── ヘッダ / §5 / テスト観点)、`Phase-5-introduction.md` §10、`Phase-5/samples/README.md`、samples 3 ファイル(`test_graph_primitives.py` = Phase 4 + network、`test_network_design.py` から end-to-end 削除、`test_mst_strategies.py` へ追加)、`CLAUDE.md`(本 Q35 + 主要決定 + 検証事象 + 所感)。overlay 検証: 5-3 部分 27 passed / Phase 5 end **211 passed(excl analysis。従来 200 から route プリミティブ 11 本が復活)** ── introduction / CLAUDE.md の Phase 5 件数「206」を更新。

**Q36.(Phase 6 開始時のスコープ確認)OR-Tools / 手実装の粒度 / 第 3 目的 / UI**

1. **Phase**: Phase 6(教材生成の開始時。ユーザー「Phase6を開始する」)
2. **質問**: (a) OR-Tools CP-SAT トラック(手実装の破綻 → 産業ソルバー)を Phase 6 でどこまでやるか。(b) 手実装ストラテジーの粒度(README §19 は Greedy / Backtracking / Branch and Bound の 3 つを列挙)。(c) 第 3 目的「勤務時間均等化」(hour_variance)と Difference Array プリミティブを MVP に入れるか。(d) decitima-ui の範囲。
3. **回答と対応方針**(すべてユーザーが選択):
   - (a) **フル実装**。`OrToolsCpSatShiftStrategy`(`implementation="library:ortools"`)、`ortools` を `[project].dependencies` に追加、CP-SAT モデリングの専用章(6-7)、`analysis/shift_analysis.py` で 20×7×3 規模の「手実装は終わらない / CP-SAT は数秒」を実測。README の「既知の計画の実行」通り。
   - (b) **3 ストラテジー・3 章**(Greedy=6-3 / Backtracking=6-4 / Branch and Bound=6-5 別々)。B&B は「Backtracking + 下界で枝刈り + 決定論的 anytime」として差分を学ぶ。
   - (c) **3 目的 + Sliding Window + Difference Array 全部**。`verify_shift_structure` に `hour_variance` metric を 1 本追加(現行版 + Phase 2/5 samples にマーカー)、`patterns/sliding_window.py`(Backtracking の連続勤務日数の逐次判定)+ `patterns/difference_array.py`(imos 法、時間帯別の在籍人数)。
   - (d) **フル samples 作業単位**(Phase 3/4/5 と同じ。6-8)。`shift-scheduler/{api,stores,hooks,components}` + ページ + シフト表可視化(`ShiftGrid`)。overlay 検証も ui 分。
   - 反映: `textbook/Phase-6/` 一式(introduction + 6-1〜6-8 + samples backend/analysis/ui)、`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の objectives マーカーを「Phase 6 で確定 ── 実装済み」に、Phase 2/4/5 samples の `structure.py` / `algorithm_selection.py` / `optimization.py` fixtures に「以降 Phase で修正予定 ── Phase 6-1 / 6-3」マーカー、README §18(OR-Tools)+ §19 Phase 6(詳細リンク)、本 Q36 + 「Phase 6 の主要決定」節。overlay 検証: Phase 5 end + Phase 6 samples + `ortools` で `uv run pytest` **271 passed / 2 deselected**、ruff / format / pyright clean、`alembic` 新テーブルなし、notebook 完走。ui **17 passed** / tsc / eslint clean。

**Q37.(Phase 6-1 の教材レビュー ── ユーザーが「スケール差」の限界を具体例で確認)`weighted_sum` の正規化を今後の改善検討事項として記録**

1. **Phase**: Phase 6-1(`Phase-6-1.md` §1「既知の限界 ── スケール差」を読んで)
2. **質問・指示**: 「素の重み付き和は `labor_cost` に支配される」を `build_shift_problem` の実数で具体的に説明してほしい。加えて、実務での直し方(正規化)を**今後の改善検討事項として CLAUDE.md に記録**してほしい。
3. **回答と対応方針**:
   - **具体例**(`build_shift_problem`: 4 スロット各 5h、tanaka ¥1200 / sato ¥1000 / ito ¥1100、tanaka は 09-02 希望休。`score = 0.7·labor_cost − 0.3·day_off_satisfaction`):
     - `day_off_satisfaction` を 0→1 まで完全改善しても score は `0.3 × 1.0 = 0.3` しか動かない。`labor_cost` は **¥1 差で score が 0.7 動く**。
     - **C**(希望休を守るが ¥1 高い: labor 20001 / dayoff 1.0)→ score `14000.4`。**D**(希望休を破るが ¥1 安い: labor 20000 / dayoff 0.0)→ score `14000.0`。**D < C なので 4 strategy 全員が「希望休を破る D」を選ぶ** ── `weight=0.3` を付けた `day_off_satisfaction` が labor の ¥1 差にすら負けて事実上無力。
     - 希望休違反 1 件を「実質 ¥5000 相当」にしたいなら必要な重みは `0.7 × 5000 ÷ 1 ≒ 3500`(≠ 0.3)。
     - `hour_variance` の `weight=100` も同じ ── この fixture で hour_variance は 0〜90 動くので、「自然な」weight 1 だと影響 `1 × 90 = 90`(labor の影響 1400 に対し誤差)。`100 × 90 = 9000` にして拮抗させた**問題サイズ依存の手調整値**(スタッフ数 / 時給が変われば付け直し)。
   - **本当の問題**: `score()`(`scheduling/common.py`)は 4 strategy 全員が探索中に「この割当は良いか」を判断するのに使う。そこが scale に支配されると **`Objective.weight` が「意図」を表さなくなる** ──「人件費 7 割・希望休 3 割で考えたい」と書いても実際は「人件費だけ」と変わらない。
   - **【今後の改善検討事項】各 metric を [0,1] に正規化してから重み付き和を取る**。案:
     - **min-max 正規化** ── その solve 内(または benchmark run 内)で見た最良 / 最悪で `(v − best) / (worst − best)`。全探索 / 貪欲で数解を先に出してレンジを掴む、または過去の `benchmark_runs` から典型値を取る。
     - **基準解比** ── 貪欲解などの baseline を 1.0 とし `v / baseline`。
     - 置き場: `domain/objectives/`(`weighted_sum` の隣に `normalize.py` など。純粋)。`Objective` に正規化のレンジ / 基準値を持たせるかは要検討(スキーマ変更 = 判別ユニオン非依存なので低コスト)。CP-SAT 側は整数線形の制約があるので正規化係数を整数スケールに載せ直す作業も要る。
     - **入れる Phase**: 未定。多目的が複数ドメインに広がる Phase 9(Logistics)や、`analysis/` で Pareto フロントを本格的に扱う Phase 10(Simulation)/ 14 のあたりで、実データのレンジを見てから入れるのが素直。Phase 6 は「素の `Σ wᵢ·fᵢ`(`Phase-0-2.md` §3 の約束)+ 落とし穴の明示」に留める(`Phase-6-introduction.md` §7 の非スコープ)。
   - 反映: 本 Q37 のみ。`Phase-6-1.md` §1 は既に「既知の限界」を書いているので追記不要。教材・samples・コードの変更なし。

**Q38.(教材レビュー ── ユーザーが `Phase-6-3.md` §1 の「metrics は Phase 2 の `verify_shift_structure` と同じ式」を問う)metrics 計算を別ファイルで重複させた理由の確認 → 一本化。あわせて「以前の Phase を触ってよいか」の判断基準を新設**

1. **Phase**: Phase 6-3(`common.py` の教材レビュー中)
2. **質問・指示**: (a)「同名の関数・同じ処理内容なら一本化できるのでは。あえて別ファイルで定義した理由があるか」。(b) 一本化できるなら、教材・サンプル生成時に「Phase 2 と同じ式」とまで判定しながら別ファイルで生成した判断理由は何か。加えて ExitPlanMode 却下時に「(c) その判断理由『以前の Phase を過剰に触らない』は CLAUDE.md の何行目か」「(d) 過去 Phase のファイルを触ってでもコード重複を回避する方針を、Phase 毎生成の都合と両立させる基準を提案してほしい」。
3. **回答と対応方針**:
   - **(a)(b) 一本化すべき。分割の理由は弱い**。`domain/solutions/structure.py` と `algorithms/scheduling/common.py` に、shift の metrics 計算ヘルパ(`_distinct` / `_hours_by_staff` / `_working_days` / `_labor_cost` / `_day_off_satisfaction` / `_hour_variance`)が ~50 行ほぼ同一で重複していた。生成時の判断理由は ① Phase 2 コードを最小限しか触りたくなかった(下記 (c) の混同)② 「`verification.py::verify` が `structural_verify` の `extra_metrics` で最終解の metrics を上書きするので数値は一致する」── どちらも弱い。式は **domain の事実**で、消費者が 2 系統(検証器 + shift strategy 4 本)と**生成時点で分かっていた**(Q31「消費者数が分かっているなら先回りする」)。→ 公開 leaf `app/domain/solutions/shift_metrics.py`(`distinct` / `hours_by_staff` / `working_days_by_staff` / `labor_cost` / `day_off_satisfaction` / `hour_variance` / `assignment_metrics`)に集約し、`structure.py` と `common.py` の双方が import。**唯一の正当な分割**は連続日数判定(`structure._longest_consecutive_run` vs `patterns/sliding_window`)── `domain → algorithms` の import 禁止によるレイヤー上の必然で `Phase-2-2.md` §3.3 で明文化済み。ここは触らない。
   - **(c)「以前の Phase を過剰に触らない」は CLAUDE.md に明文では無い**。実在するのは (a′) 教材本文の遡及的**全面**リライト禁止(#3 L38 / #12.2「遡及的な全面書き換えはしない」)、(b′) **動機なき遡及監査**の禁止(Q30「Phase 2〜5 の遡及監査はしない ── ユーザー確定」/ Q18「Phase 0〜2 への遡及変更は不要」)の 2 つだけ。狙い撃ちの差分変更は #12 マーカー / #16 現行版テストが用意する正規の仕組みで、禁止対象ではない。生成時に「触るな」と丸めていたのが過剰な自己制約だった。
   - **(d) 進行のルール #17 を新設**(→ ルール本文)。「後続 Phase の実在の消費者が駆動する共通化は、以前の Phase のコードを触ってでも重複を残さない。判定は『駆動する消費者は何か』の一問。禁止は (a′)(b′) と、レイヤー境界が要求する分割」。今回の `shift_metrics.py` は駆動する消費者(`common.score()` を通る Greedy / Backtracking / B&B / CP-SAT の 4 strategy)に具体名で答えられるので実施。
   - **位置づけ**: Q21「samples 運用の都合が設計判断に化ける」/ Q31「消費者数が分かっているなら先回り」の **4 例目**(Q2 = 分割 vs 統合、Q15 = 計算か述語か)。
   - 反映: `CLAUDE.md`(#17 新設 / #12 頭に参照句 / 本 Q38 / Phase 6 主要決定 / 所感 / 検証で発覚した事象)、`textbook/Phase-6/samples/app/domain/solutions/shift_metrics.py`(新規)、`structure.py` / `algorithms/scheduling/common.py`(現行版 ── 重複ヘルパ削除 + import)、`Phase-6-1.md` §2 / §まとめ / テスト観点、`Phase-6-3.md` §1、`Phase-6-introduction.md`(§1 表 / §6 / §9 / §10)、`samples/README.md`、`Phase-2` / `Phase-5` samples の `structure.py` マーカー本文。overlay 検証(ov6f2 上に 3 ファイル差し替え): `uv run pytest` **271 passed / 2 deselected**(件数不変 ── 挙動不変のリファクタ)、`ruff check` / `ruff format --check` clean、`uvx pyright` 0 errors。
   - **フォローアップ(ユーザー写経で発覚)**: `structure.py` を写経したユーザーが `test_greedy_shift.py` で `AttributeError: 'ShiftSolution' object has no attribute 'items'`(出所 `shift_metrics.hours_by_staff` の `assignments.items()`)。原因は写経ミス ── ヘルパのシグネチャが `_hours_by_staff(data, sol: ShiftSolution)` → `hours_by_staff(data, assignments: dict)` に**変わった**のに `hours_by_staff(data, sol)` と機械的に写した。遠因は `Phase-6-1.md` §2 が末尾 1 行(`return out, assignment_metrics(...)`)しか見せず、関数本文の 2 つの call site の `sol` → `sol.assignments` を見せていなかったこと(Q30 の `_dijkstra_segment` と同型)。対応: (1) samples `verify_shift_structure` の先頭で `assignments = sol.assignments` を 1 度だけ束ね、全 call site を `f(data, assignments)` に統一(`.assignments` の反復 4→1、振る舞い不変)。(2) §2 を「変わった行の before → after 表 + 写経の罠 blockquote(この `AttributeError` → `sol` を渡している / pyright なら `reportArgumentType`)」に差し替え。(3) テスト観点に「6-1 の `test_verification_service.py` が第一の番人 ── その場で赤」。overlay 再検証 **271 passed / 2 deselected**、`assignments` 束ねを消して `sol` に戻すと `test_verification_service.py` が `AttributeError` で赤。写経先は触らない(ユーザーが 3 箇所を `sol` → `sol.assignments` に修正)。
   - **フォローアップ 2(ユーザーの import 経路監査 → 写経で循環 import 発覚)**: 「重複を `shift_metrics.py` にまとめた変更が `backtracking.py` に反映されていないのでは」。リファクタで metric **式**を集約したとき `type Assignment = dict[str, list[str]]` も `common.py` から `shift_metrics.py` へ**巻き込んで**移してしまい、4 strategy は `from common import Assignment` を暗黙 re-export で解決していた(定義まで 2 hop)。**当初 `common.py`(algorithms)に戻したが誤り** ── `shift_metrics.py`(domain)は `Assignment` を要るのに `domain → algorithms` 禁止で `common` から import できず、ユーザーが写経で `ImportError: cannot import name 'Assignment' ... (circular import)` を踏んだ。route の `Segment`↔`segments.py` 類推が破れる理由もここ ── route には `Segment` を要る domain ファイルが無い(metrics は inline)。**共有エイリアスは domain に置くしかない**。**決着**: `type Assignment` を `domain/solutions/shift_scheduler.py`(`ShiftSolution.assignments` の型そのもの。pydantic/typing しか import しない葉)に定義 ── `shift_metrics`(domain 兄弟)も `scheduling/common`(algorithms→domain。既に同ファイルから `ShiftSolution` を import 済み)も循環なしで届く唯一の家。Phase 1 samples の `shift_scheduler.py` に `[以降 Phase で修正予定 ── Phase 6-1]` マーカー(#12・#17 ── 凍結ファイルを触ってでも重複を排除する実例)。**仕上げ**: ユーザーが「strategy → `common` → `shift_scheduler` は間接 import では?」と質問 ── その通り(`common` は `Assignment` を定義せず再エクスポートしているだけ。`common` が内部使用をやめると F401 で消えて壊れる)。4 strategy を `from app.domain.solutions.shift_scheduler import Assignment` の**定義元 import** に修正(関数は `common` のまま)。route strategy が `Segment` を定義元 `segments.py` から取るのと同じ。overlay `ov6f2` 再検証 **271 passed / 2 deselected**、ruff / format / pyright(Phase 6 分 0 errors)clean、`grep "import Assignment" app/` の全 6 行が `shift_scheduler` を指す(`common` 経由 0)、`python -c "import ...backtracking"` が循環なく通る。教訓 ── ①リファクタで「まとめる対象」を宣言したら範囲を厳密に守る(式の集約 ≠ 型エイリアスの移動) ②共有型の置き場は**両レイヤーが循環なしで import できる最下層**で決まる ③**共有シンボルは常に定義元から import する**(再エクスポート経由は動くが脆い)。

### 検証で発覚した事象の原因と解決

- **Pylance の `ProblemData` 型式エラー(型式では変数を使用できません / reportInvalidTypeForm)** — 原因は `ProblemData` 自体ではなく、`RouteData` / `ShiftData` の import が Pylance で未解決なこと。ワークスペースを `decitima/`(プロジェクトルート)で開くと `app` パッケージ(`decitima-api/backend/app`、3 階層下)を Pylance が見つけられない。対応: `decitima-api/backend/pyproject.toml` に `[tool.pyright]`(`include = ["app", "tests"]` / `venvPath = "."` / `venv = ".venv"` / `typeCheckingMode = "standard"`)を追加、加えて `decitima/.vscode/settings.json` に `python.analysis.extraPaths: ["decitima-api/backend"]`。適用後「Developer: Reload Window」。この設定で再発しない。bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` にもなるので絶対 import 必須。この `[tool.pyright]` と `.vscode/settings.json` は「開発環境に必須の tooling 設定」であり、`fastapi-langchain-template` への還元候補。
- **テンプレート由来の型債務** — `typeCheckingMode = "standard"` を入れたところ、テンプレート由来のコード(`app/ai/**` の `GraphState` 部分構築、`tests/unit/test_ai_graph_nodes.py` / `test_auth_service.py` のテストフェイク、`app/repositories/conversation.py` の `get_by_id` override)に既知の型エラーが出た。DeciTima の新規コードは standard で厳格に保ちつつ、これらは `[tool.pyright]` の `ignore` で当面抑制。Phase 11(`app/ai` 作り替え)とテスト基盤整備で解消し、`fastapi-langchain-template` へ還元する。
- **Phase 1 samples の検証は decitima-api への overlay で行う(Claude 側の作業)** — `textbook/Phase-1/samples/` は実 `app/` ツリーの鏡写しで、`from app...` / `from tests...` の絶対 import を使う。単体では import が解決しないため、`decitima-api/backend` を `.venv` 除外で複製し `.venv` をシンボリックリンク、`samples/{app,tests,alembic/versions}` を overlay してから `./.venv/bin/python -m pytest` / `./.venv/bin/ruff check` / `ruff format --check` / `uvx pyright` を実行する。**samples には Phase 1 の新規ファイルだけを置く**方針なので(下項)、既存ファイルへの追記を overlay 側に適用してから実行する ── `app/core/config.py` の `SOLVE_RATE_LIMIT_*`・`SOLVE_TIMEOUT_SECONDS` / `app/services/errors.py` の import と 4 クラス / `app/models/__init__.py` の `Problem`・`Solution` / `alembic/env.py` のモデル import / `app/api/routes/__init__.py` の 3 ルーター / **`app/algorithms/registry.py` の `DijkstraStrategy` 行 2 箇所のコメント解除(進行ルール #15。フル検証は end 状態で回す)**。クリーンな base は `git -C decitima-api archive HEAD backend | tar -x` で取る(backend の git ルートは `decitima-api/`)。end 状態で pytest 91 passed(3 integration deselected)/ ruff・format clean / pyright 0 errors を確認(2026-08-31 再確認)。1-2 のみを重ねた部分 overlay(dijkstra 無し)でも `test_registry.py` / `test_problem_schema.py` が緑。
- **`textbook/Phase-1/samples/` は Phase 1 で新規作成するファイルのみ** — 既存 `decitima-api` ファイルへの追記(`app/core/config.py` / `app/services/errors.py` / `app/models/__init__.py` / `app/api/routes/__init__.py` / `alembic/env.py`)は samples に全文コピーを置かず、各章に差分として示す。当初計画どおり(生成時に全文コピーで逸脱していたのを訂正)。samples の全文コピーは意図せぬ差分(全角括弧の書き換え等)も持ち込むため。各章の「対応サンプル」行も、その章で新規作成するファイルだけを列挙する。
- **Phase 1 の軽微な pyright / 実装上の対応** — (1) `binary_search` の `_Comparable` プロトコルは `__lt__(self, other: Any)` にする(`object` だと組み込み比較型が満たせず standard で警告)。(2) テストで `FakeRedis` を `SolveService` に渡す箇所は `cast(Redis, FakeRedis())`(既存 `test_auth_service.py` は pyright ignore で処理していたが、Phase 1 は cast で明示)。(3) 判別可能ユニオンの消費側テストは `assert isinstance(sol.assignments, RouteSolution)` で絞り込む(サンプルの `_route(sol)` ヘルパ)。
- **`NumericBoundConstraint` のフィールドが Phase 1 samples(`op`)と実 backend(`operator`)でズレていた** — Phase 1 写経時にユーザーが `op` → `operator` にリネーム(実 backend は自己整合、fixture も更新済み)、samples 側は `op` のまま残っていた。stdlib の `operator` モジュールと同名だが、モデルの属性名なので衝突せず、チェッカー側も `from operator import le, ...` の名前 import なら `import operator` しないので安全。Phase 2 の `check_numeric_bound` が初の実消費者なので、Phase 2 生成時に **samples を `operator` に同期**(`textbook/Phase-1/samples/app/domain/problems/problem.py` と `tests/fixtures/optimization.py`、`Phase-0-2.md` §4.2 と `Phase-1-1.md` §2 に「サンプル修正」マーカー)。rule #9 のサンプル同期であって設計変更ではない。
- **Phase 2 samples の検証も decitima-api への overlay(Phase 1 end 状態の上に重ねる)** — `git -C decitima-api archive HEAD backend` のクリーン base に Phase 1 samples + Phase 1 の既存追記 + registry のコメント解除で「Phase 1 end 状態」を作り、その上に Phase 2 samples + `config.py` の `VERIFY_RATE_LIMIT_PER_HOUR` + `api/routes/__init__.py` の `verify_router` を重ねる。end 状態で `pytest` 121 passed(3 deselected)/ `ruff check`・`ruff format --check` clean / `uvx pyright` 0 errors を確認(2026-09-01)。手順は `textbook/Phase-2/samples/README.md`。Phase 2 が Phase 1 のファイルを書き換えるもの(`services/{validation,verification}.py` / `domain/problems/shift_scheduler.py` / `tests/fixtures/optimization.py` / `tests/unit/test_{validation,verification}_service.py`)は現行版を Phase 2 samples に置き、Phase 1 samples 側は本体コードを残して「以降 Phase で修正予定」マーカーで誘導(rule #12.2 A)。

- **Phase 3 samples の検証は 2 リポジトリ overlay(backend + ui)** — backend: 現在の `decitima-api/backend` 作業ツリー(= Phase 2 end 状態、`varify.py`→`verify.py` 修正済み)を `.venv` 除外で複製 + `.venv` シンボリックリンク、`textbook/Phase-3/samples/{app,tests,alembic}` を重ね、既存への追記 6 点(`pyproject.toml` の numpy / `config.py` の `BENCHMARK_RATE_LIMIT_*` / `api/routes/__init__.py` の `benchmark_router` / `models/__init__.py` と `alembic/env.py` の `BenchmarkRun` / `registry.py` の `BruteForceRouteStrategy` import + list 1 行)を適用、`uv pip install --python .venv/bin/python 'numpy>=2.0'`。end 状態で `uv run pytest` **151 passed / 3 deselected**・`ruff check`(Phase 3 の新規/変更ファイルは clean。既存ツリーの Phase 2 lint 債務は別)・`ruff format --check` clean・`uvx pyright` 0 errors・`alembic upgrade head`(`c65b3aa7b03f → d4f1a9c2b8e7` で `benchmark_runs` 生成)を確認(2026-09-02)。ui: `decitima-ui` を `node_modules` 除外で複製 + シンボリックリンク、`textbook/Phase-3/samples/ui/src/` を重ね、`npx tsc --noEmit`(clean)・`npx vitest run src/components/auth src/features/optimization`(**11 passed** ── 3-5 の auth 5 件 + 3-6 の 6 件)・`npx eslint`(clean)。`src/components/layout/Menu.test.tsx` は Phase 3 以前から失敗しているテンプレートのテスト rot で、件数は増えない(2026-09-03 に Q24 の login UI を追加して再確認)。手順は `textbook/Phase-3/samples/README.md`。
- **numpy / pandas / matplotlib を実 `.venv` に導入した** — Phase 3 samples 検証時、共有 `.venv`(overlay がシンボリックリンク)に `uv pip install 'numpy>=2.0' 'pandas>=2.2' 'matplotlib>=3.9'` を実行済み。numpy は runtime 依存(`[project].dependencies`)、pandas / matplotlib は 3-7 の分析トラック用(`[dependency-groups].analysis`)として `pyproject.toml` に追加予定。ユーザーが `uv sync` するまで `pyproject.toml` / `uv.lock` は未更新。notebook 実行の検証には `uv run --with jupyter --with nbconvert --with ipykernel jupyter nbconvert --execute` を使用(jupyter はロックしない方針)。

- **Phase 4(Route)/ Phase 5(Network)samples の検証 ── 2 段階 overlay(相談ログ Q29 で 4/5 分割後)** — backend の base は現在の `decitima-api/backend` 作業ツリー(= Phase 3 end 状態)を `.venv` 除外で複製 + `.venv` シンボリックリンク。共有 `.venv` に `networkx==3.6.1` 導入済み。**`ruff format` は必ず `--config` で backend の pyproject を指すこと**(指定しないと line-length 88 で再フォーマット。backend は 100)。
  - **Phase 4 route-end**: `textbook/Phase-4/samples/{app,tests,analysis}` を重ね、`registry.py` に route 4 strategy(Dijkstra / BellmanFord / AStar / NetworkxShortestPath)+ BruteForce、`pyproject.toml` に `networkx>=3.3`。`uv run pytest` **176 passed / 2 deselected**、`ruff check` / `ruff format --check` clean、`uvx pyright` Phase 4 分 0 errors、`alembic upgrade head` no-op、notebook 完走。ui は `textbook/Phase-4/samples/ui/src/` を重ね `npx tsc` clean・`npx vitest run src/features/optimization src/components/ui/charts/GraphCanvas.test.tsx` **13 passed**(GraphCanvas 3 + route-planner store 4 + Phase 3 分)・`npx eslint` clean。
  - **Phase 5 network-end**: Phase 4 route-end の上に `textbook/Phase-5/samples/{app,tests}` を重ね、`registry.py` に `"network_design": [KruskalStrategy(), PrimStrategy(), NetworkxMST()]` を追加。`uv run pytest` **217 passed / 2 deselected**(analysis 6 本込み。pandas 未導入の環境では `--ignore=tests/analysis` で 211)、ruff / format / pyright clean、`alembic upgrade head` no-op。ui は `textbook/Phase-5/samples/ui/src/` を重ね `npx vitest run src/features/optimization` **16 passed**(+ network-designer store 3)。Q35 対応(`test_graph_primitives.py` を Phase 4 route + network の現行版に是正、end-to-end テストを 5-4 へ移設)後に再測(2026-09-07)。
  - 手順は `textbook/Phase-4/samples/README.md` / `textbook/Phase-5/samples/README.md`。再検証 2026-09-03(4/5 分割 + 番号ずれ反映後、コメントのみの sample 変更を含む)。
  - **Phase 6 shift-end(相談ログ Q36)**: Phase 5 network-end の上に `textbook/Phase-6/samples/{app,tests,analysis}` を重ね、`registry.py` に `"shift_scheduling": [Greedy, Backtracking, BranchAndBound, OrToolsCpSat]`、`pyproject.toml` に `ortools`。共有 `.venv` に `ortools` 導入済み。`uv run pytest` **271 passed / 2 deselected**、`ruff check` / `ruff format --check`(`--config` で backend pyproject)clean、`uvx pyright app tests` Phase 6 分 0 errors、`alembic upgrade head` 新テーブルなし、`jupyter nbconvert --to notebook --execute analysis/notebooks/shift_explore.ipynb` 完走。ui は Phase 5 UI end + `textbook/Phase-6/samples/ui/src/` を重ね `npx tsc --noEmit` clean・`npx vitest run src/features/optimization` **17 passed**(+ shift-scheduler store 4)・`npx eslint` clean。手順は `textbook/Phase-6/samples/README.md`(2026-09-07)。
  - **Phase 6 の既知事象**: (1) `CandidateSolution.assignments` に `ShiftSolution` を足すと、`.total_weight` を無条件アクセスしていた route / network の store テスト 2 本が tsc の型エラー → 現行版で `.metrics.total_weight` に(#16)。(2) CP-SAT の `hour_variance` は spread(max−min)で代理 ── 手実装(本物の分散)と最適が完全一致しないことがあるので、`test_shift_strategies.py` の「4 strategy 一致」は 2 目的の `build_shift_problem()` で `labor_cost` / `day_off_satisfaction` を照合し、3 目的版は「全 strategy が実行可能解を返す」だけを見る。
- **既知の pre-existing 事象(Phase 4 とは無関係)** — 写経先の `decitima-api/backend/tests/unit/test_brute_force_strategy.py` に `test_deterministic_same_input_same_output` が **2 回定義**されており(L58 と L73)、pyright が `reportRedeclaration` を 1 件出す。Phase 3 samples 側は 1 回のみ ── Phase 3 の写経時に混入した重複。写経先の当該 1 関数を消せば解消(Phase 4 の変更対象外)。
- **`nx.Graph` は平行エッジを持てない** — `RouteData` は同じノード対に複数 `RouteEdge` を持てる(`build_scaled_route_problem` は `rng.sample` で偶発的に作る)。`NetworkxShortestPath._to_graph` / `NetworkxMST` は `_add_min_edge`(既存があれば軽い方を残す)で対応。最短経路・MST では重い平行辺は絶対に使わないので手実装と等価。これを入れないと `test_networkx_matches_handwritten_dijkstra_property` が seed 依存で落ちる(発覚 → 修正済み)。
- **Phase 3-8(分析トラック。旧 3-7 ── Q24 でリネーム)の overlay 検証** — Phase 3 backend overlay(numpy 済み)に `textbook/Phase-3/samples/analysis/` と `tests/analysis/` を重ね、`pyproject.toml` に `[dependency-groups].analysis` + ruff の `src` / `known-first-party` に `analysis` を追加、pandas / matplotlib を install。`sample_benchmark_runs.jsonl` は実 `BenchmarkService` を SQLite で 3 回まわして `dump_rows` した生成物。`uv run pytest` **165 passed / 3 deselected**、`ruff check analysis tests/analysis` / `ruff format --check` clean、`uvx pyright tests/analysis` 0 errors(`analysis/` 自体は pyright include 外 ── `benchmark_report.py` / `export.py` に pandas 型と `type[Base]` narrowing の軽微な指摘が 2 件出るが ruff のみの割り切り)、`jupyter nbconvert --execute` 完走(2026-09-02)。

- **Phase 4-1 のテスト観点の穴 + `_dijkstra_segment` の写経バグ(ユーザー写経で発覚。相談ログ Q30)** — 4-1 は `adjacency.py` / `segments.py` / `waypoints.py` の 3 ファイルを新規作成し `dijkstra.py` を大改修するが、章が指定するテスト `test_graph_primitives.py` は **`adjacency.py` しか import しない**。`waypoints.py` の写経漏れ(`ModuleNotFoundError`)は Phase 1 の `test_dijkstra_strategy.py` を回して初めて発覚した。対応: (1) `test_graph_primitives.py` を拡張し `segments`(`plan_route` にフェイク区間を注入)/ `waypoints`(`optimize_waypoint_order` にフェイク cost)/ `collect_route_constraints` / `route_solution` をカバー(import が `segments → waypoints` を辿るので 3 ファイルのどれかの写経漏れで collection が赤に)。(2) Phase 1 の `test_dijkstra_strategy.py` を **Phase 4 samples の現行版**として置き(docstring に「4-1 で内部が segments 経由に。公開挙動は不変。赤なら refactor の写経ミス」を追記、アサーション不変)、Phase 1 samples にマーカー。(3) 進行のルール **#16 を新設**(以前の Phase のテストのリファクタ追従)+ **#15 に「章が作る全ファイルをその章のテストが 1 度は import する」条項**。ユーザーの写経バグ自体は `_dijkstra_segment` の末尾を `return _reconstruct(prev, start, goal, dist[goal]), pops` でなく `_reconstruct(prev, start, goal, weight)`(`return` 無し・`weight` 未定義・`, pops` 無し)と写していたこと ── §3.3 が `solve` の before/after しか見せず `_dijkstra_segment` / `_reconstruct` の変化を見せていなかったのが遠因。§3.3 に `_dijkstra_segment` 末尾 + `_reconstruct` の before/after を追加。overlay `ov4`: `test_graph_primitives.py`(+6)+ `test_dijkstra_strategy.py` 現行版で route-end **182 passed / 2 deselected**、ruff / pyright clean。写経先(`decitima-api/backend`)の `dijkstra.py` バグはユーザーが修正(2026-09-03)。
  - **フォローアップ**: 上記反映後もユーザーが `test_dijkstra_strategy.py` で `TypeError: cannot unpack non-iterable NoneType`(出所 `segments.py`)に当たり、`_dijkstra_segment` の末尾の写経ミスと結びつけるのに手間取った。**#16 の「以前の Phase の別ファイルのテストを再実行」だけでは、間接的なエラーのとき詰まりが解けない**。→ (a) `test_graph_primitives.py`(章の第一テスト)に `DijkstraStrategy().solve()` の**統合スモーク**を 1 本追加 ── 写経ミスをその章のテストでその場で赤にする。docstring に失敗モード(この `TypeError` → `_dijkstra_segment` の末尾を見る)を明記。(b) samples `dijkstra.py` の `_dijkstra_segment` 直前に「写経の罠」コメント。(c) `Phase-4-1.md` §3.3 に「写経ミスの見分け方」blockquote、§テスト観点を「第一テスト = graph_primitives(統合スモーク込み)/ 補助 = Phase 1 の再実行」に整理。(d) #16 に「第一の番人は当該章の第一テストに統合スモーク」の一文。overlay `ov4` route-end **183 passed / 2 deselected**、`_dijkstra_segment` の `return` を消すとスモークが `TypeError` で赤(4-test 版は素通り)。ユーザーは L61 を自力修正済み(写経先 `pytest tests/unit/test_{dijkstra_strategy,graph_primitives}.py` → 10 passed)。写経先は触らない(2026-09-03)。
- **`Phase-4-4.md` の `waypoints.py` 作成 Phase 誤記** — L9/L14 が「4-2 で作った `waypoints.py` を本実装に差し替える」としていたが、`segments.py` が `waypoints` を import し `dijkstra.py`(4-1 でリファクタ)が `segments` を import する以上、3 ファイルとも **4-1 で作られる**。samples は end 状態(全順列版)なので 4-4 で写経するファイルは無い ── 4-4 は「全順列で最適順を選ぶ」挙動の深掘りとテスト(`test_route_strategies.py` の経由順セクション)に主眼を移す。`Phase-4-1.md` / `Phase-4-4.md` の「4-1 は素朴版」表現も「骨格を 4-1、深掘りは 4-4」に統一(Q30 で修正)。

- **`test_mst_properties.py` / network fixture の作成 Phase 誤記 ── 5-2 → 5-3(相談ログ Q34)** — 教材は `test_mst_properties.py` と `tests/fixtures/optimization.py` の network 部分を作業単位 5-2 の成果物としていたが、両方とも 5-3 で生まれる `app.domain.problems.network_design`(`NetworkDesignData` / `NetworkLink`)を import し、テストはさらに 5-3 の `app.algorithms.graph.connectivity`(`forms_spanning_tree`)にも依存する ── 5-2 まで写経した状態では collection 段階で `ModuleNotFoundError`(進行のルール #15 違反。`Phase-5-2.md` §5 は素の前方参照を注記だけで許容していた)。5-3 の `test_network_design.py` も既に `build_network_problem` に依存しており、fixture は元々 5-2 の clean な成果物になり得なかった。対応: 実測テストと network fixture を **5-3 の成果物**に移し、5-2 は理論章(実装ファイルなし)にした ── **教材 Markdown の章-attribution 変更のみ**。`samples/` のファイル内容・配置は不変(`test_mst_properties.py` docstring 冒頭の「作業単位 N」表記だけ是正)。overlay は Phase 5 network-end **206 passed / 2 deselected**(この時点。直後の Q35 で `test_graph_primitives.py` 是正により **217** に)(2026-09-07)。

- **`test_network_design.py::test_network_design_end_to_end_pipeline` が `registry["network_design"]`(5-4)に前方依存(相談ログ Q35 ②)** — validate→select→solve→verify を通すこのテストは 5-3 の `test_network_design.py`(5-3 の成果物)に入っていたが、`registry["network_design"]` は 5-4 で埋まるため 5-3 状態では `select_strategy` が `NoAlgorithmError`(実測: 5-3 状態で 1 failed / 12 passed)。#15 違反。→ `test_mst_strategies.py`(5-4)へ移設。5-4 には strategy の solve テスト / select→kruskal テストはあったがフルパイプラインの統合テストが無かったので、移設先として過不足ない。`test_network_design.py` は 9 本に。

- **Phase 5 samples の `test_graph_primitives.py` が Phase 4-1 版を丸ごと置換していた(相談ログ Q35 ③)** — Phase 5 の版は `build_link_adjacency` / `connectivity` の network 4 テストだけを持ち、Phase 4-1 の route プリミティブテスト 11 本(`build_adjacency` / `plain_adjacency` / `plan_route` の連結 / `collect_route_constraints` / `route_solution` / `optimize_waypoint_order` / `has_negative_weight` / **Q30 で足した dijkstra リファクタの統合スモーク `test_dijkstra_solve_still_works_after_segments_refactor`**)を落としていた。overlay で Phase 4 版を上書きするため **Phase 5 end 状態でこれらが消失**(実測: 従来 200 passed excl analysis)。→ Phase 5 版 = **Phase 4-1 の全内容 + network 4 本の「現行版」**に是正(route 分の assertion は 4-1 のまま = #16 の番人を維持)。是正後 **211 passed(excl analysis)**。Phase 5 の件数「206」→ analysis 6 本込みで **217** に更新(introduction §6 / 本 Notes の Q29・Q34 の「206」記述)。

- **`shift_metrics.py` 抽出で `verify_shift_structure` の call site 引数が `sol` → `sol.assignments` に変わる写経ミス(Q38 のフォローアップ。ユーザー写経で発覚)** — Phase 6-1 で metrics ヘルパを `structure.py` から `domain/solutions/shift_metrics.py` に抽出したとき、ヘルパのシグネチャが `_hours_by_staff(data, sol: ShiftSolution)` → `hours_by_staff(data, assignments: dict)` に変わった。ユーザーが `hours_by_staff(data, sol)` と機械的に写し、`test_greedy_shift.py`(6-3、`SolutionVerificationService().verify` 経由)で `AttributeError: 'ShiftSolution' object has no attribute 'items'`。**遠因**: `Phase-6-1.md` §2 が末尾 1 行(`return out, assignment_metrics(...)`)しか見せず、関数本文の 2 つの call site(`hours_by_staff` / `working_days_by_staff`)の引数変更を見せていなかった(Q30 の `_dijkstra_segment` と同型)。対応: (1) samples `verify_shift_structure` の先頭で `assignments = sol.assignments` を **1 度だけ**束ね、全 call site を `f(data, assignments)` に統一(`.assignments` の反復 4→1、`sol.assignments` は plain dict 属性なので振る舞い不変)。(2) §2 を「変わった行の before → after 表 + 写経の罠 blockquote(この `AttributeError` → `sol` を渡している / `uvx pyright` なら `reportArgumentType`)」に差し替え。(3) §テスト観点に「6-1 の `test_verification_service.py` が第一の番人 ── その場で `AttributeError` で赤。6-3 まで持ち越さない」。overlay `ov6f2` 再検証: 修正 `structure.py` で `uv run pytest` **271 passed / 2 deselected**、ruff / pyright clean。`assignments` 束ねを消して `hours_by_staff(data, sol)` に戻すと `test_verification_service.py` が `AttributeError` で赤(第一の番人が効く)。写経先(`decitima-api/backend`)はユーザーが 3 箇所を `sol` → `sol.assignments` に修正(Claude は触らない)。

- **リファクタで `type Assignment` を `shift_metrics.py` に巻き込んでいた → 置き場は `shift_scheduler.py`(Q38 のフォローアップ 2。ユーザーの import 経路監査 → 写経で循環 import 発覚)** — metric **式**の集約が目的だったのに、`common.py` の `type Assignment = dict[str, list[str]]` も一緒に `shift_metrics.py` へ移していた。4 strategy の `from ...common import Assignment` は暗黙 re-export で動く(271 passed)が定義まで 2 hop。**当初 `common.py` に戻したが誤り** ── `shift_metrics.py`(`app/domain/solutions/`)は `Assignment` を要るのに `domain → algorithms` 禁止で `common`(`app/algorithms/scheduling/`)から import できず、ユーザーが写経で `ImportError: cannot import name 'Assignment' ... (circular import)`。**共有型の置き場は「両レイヤーが循環なしで import できる最下層」で決まる** ── `Assignment` は `domain/solutions/shift_scheduler.py`(`ShiftSolution.assignments` の型そのもの。app を何も import しない葉)に定義。`shift_metrics`(domain 兄弟)/ `scheduling/common`(algorithms→domain。既に `ShiftSolution` を同ファイルから import 済み)の双方が届く。route の `Segment`↔`segments.py` 類推は「`Segment` を要る domain ファイルが無い」前提でのみ成立 ── shift には無い前提。**当初は `common` が再エクスポートし strategy の import 行を据え置いたが、ユーザーが「間接 import では?」と指摘 → 4 strategy も `from app.domain.solutions.shift_scheduler import Assignment` の定義元 import に修正**(関数だけ `common` から。route strategy が `Segment` を `segments.py` から取るのと揃えた)。再エクスポート経由の import は動くが、元モジュールが内部使用をやめると `ruff --fix` が F401 で削除して静かに壊れる。Phase 1 samples の `shift_scheduler.py` に #12 マーカー(#17 ── 凍結ファイルを触ってでも重複排除の実例)。教訓 ── **リファクタで「まとめる対象」を宣言したら範囲を厳密に守る**(式の重複排除 ≠ 型エイリアスの移動)。#13 の突き合わせに「移動したシンボルは宣言した対象だけか」+「共有型は両レイヤーが循環なしで届く最下層に置いたか」+「各 import はその名前の**定義元**を指しているか(再エクスポート経由でないか)」を足す。

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
  「以降 Phase で修正予定」マーカーで戻る**(進行のルール #12)。双方向還流ループの明文化。
  以前の Phase は設計スナップショットとして「その時点では samples のまま実装してよい」まま読め、
  どこがどう変わるか(当初 → 現在 → 理由 → 参照先)を追える。
  `grep -rnE "修正予定|サンプル修正|で確定 ──" textbook/` で全変更点を一覧できる。
  マーカー見出しは当初 `[Phase <N> 改訂]` だったが「改訂済みに見えて紛らわしい」というユーザー
  指摘で「以降 Phase で修正予定 ── Phase <N>-<M>」に統一(読み手視点を優先)。
- (Claude 観察 / ユーザー指示で制度化)各章の `## テスト観点` に **テスト対象 / ドライバ / スタブ**
  を明記する運用(進行のルール #14)。テストダブルの要否がレイヤー設計(純粋 / 副作用)の鏡に
  なるため、写経しながら「この対象は何に依存しているか」を毎章で言語化する訓練が組み込まれた。
  起点は Phase 1-1 の写経中に出た「このテストのスタブ・ドライバはどれか」という質問(Q8)。
- (Claude 観察 / ユーザー指摘で深化)Phase 2 で「設計判断は『各層が何のためにあるか』で
  下す」ことが写経を通じて体得できると分かった。当初 Claude は「`import` 1 本が層の方向を破る
  という制約が判断を**強制した**」と書いたが、ユーザーが「一般的な筋で service に置くべきなら
  その形に**起こすステップ**が要る(現場レベルの設計が前提)」と指摘。整理: `import` 禁止は
  誤りを写経中に顕在化させる **guardrail** であって理由ではない。理由は「これは計算か? 述語
  か?」── 到達可能性は計算なので `route_reachable` を `algorithms/` に抽出し、判定を
  `services/` に置く(`domain/` は不関与)。構造検証を合成モジュール `structure.py` に置くのも
  同型(`ConstraintViolation` 経由の循環は guardrail、理由は「これは leaf の責務か合成の
  責務か」)。教材はこの「問い直し」を §3・テスト観点で言語化。(`Phase-2-2.md` §3 /
  `README.md` CL 開発「特徴とメリット」)
- (Claude 観察 / ユーザー指摘で顕在化)**samples 運用の都合が設計判断に化けることがある**。
  Phase 3 で `BenchmarkRunRepository` を `repositories/benchmark.py` に単独ファイル化したのは、
  「`repositories/optimization.py` を触ると現行版再出荷 + 改訂マーカーが要る」という samples の
  管理コストを避けた結果で、設計上の理由は無かった。ユーザーの「合理的意図はあるか / import で
  格納先は分かるのに短いコードのため別ファイルにするのは管理上の問題」という問い直しで発覚し、
  `Phase-0-8.md` §5 の当初計画(全 repo 同居)へ是正。教訓 ── 教材生成時に「このファイルを
  分けた理由は設計か、samples の書きやすさか」を自問する。二重ループ(実装で当たった摩擦 →
  教材改訂)が拾った 3 例目(Q2 の分割判断 / Q15 の到達可能性の層 / 本 Q21)。(相談ログ Q21 /
  `Phase-3-3.md` §2.3)
- (Claude 観察)**「新しい problem_type を足しても既存に触れない」がハイブリッドスキーマ設計の
  検証可能な成果**として Phase 4 で実物になった ── `network_design` を配線しても route / shift の
  コードは 1 行も変わらず、`alembic upgrade head` は no-op、`GET /algorithms` も `POST /benchmark` も
  自然に network を扱う。Phase 0-2 §8.1 / Phase 0-8 の「問題固有部分は開いておく」が、3 Phase
  越しに「実際に開いていた」ことで報われる形。CL 開発の「設計判断を後の Phase の samples で
  実証する」構造がここでも効いた。
- (Claude 観察)**`Phase-2-2.md` §3 の「計算か? 述語か?」の問いが Phase 4 で再利用できた** ──
  network の連結性(`all_nodes_connected` / `forms_spanning_tree`)を `domain` でなく
  `algorithms` + `services` に置く判断は、route の到達可能性(`route_reachable`)で一度言語化
  した問いをそのまま当てはめただけ。#14(SUT / ドライバ / スタブ)と同じで、一度言語化した
  設計の問いは以降の Phase で「型」として使い回せる。教材が積み上がるほど新しい Phase の
  判断コストが下がる。
- (Claude 観察 / 検証で発覚)**ツールの config スコープが overlay 検証の落とし穴**になった ──
  `ruff format` をリポジトリルートから実行すると backend の `pyproject.toml`(line-length 100)が
  拾われず、デフォルトの 88 で samples が全面再フォーマットされた。`--config <backend>/pyproject.toml`
  を明示して復旧。教訓 ── overlay は「ファイルを別の場所に置く」ので、ファイル発見型の設定
  (ruff / pyright / eslint の config 探索)が本来の場所を見失う。検証コマンドは config を明示する。
- (Claude 観察 / ユーザー写経で発覚 ── Q30)**「章が作る全ファイル」と「章のテストが触るファイル」の
  ズレが写経ミスを素通しさせる**。Phase 4-1 は 3 ファイル新規 + `dijkstra.py` 大改修なのに、指定
  テスト `test_graph_primitives.py` は `adjacency.py` しか import していなかった ── `waypoints.py` の
  写経漏れは Phase 1 の別テストを回して初めて出た。CL 開発は「samples = end 状態、フル検証は Phase 末」
  という設計上、**per-chapter 写経の途中状態を守るのは各章のテストの網羅性だけ**。にもかかわらず
  テスト観点(#14)は「SUT / ドライバ / スタブ」の関係は言語化させるが「章の全成果物をカバーしたか」は
  問うていなかった。→ #15 に条項追加(章の全ファイルをテストが 1 度は import)、#16 新設(以前の
  Phase のテストの再実行と追従)。**教材生成後の突き合わせ(#13)に「テストの import 集合 ⊇ 章の
  新規ファイル集合」チェックを足すべき**、という提案。overlay のフル検証(Phase 末)は緑でも、
  章単位で穴があると写経者がそこで詰まる ── 検証を「章ごとの部分 overlay」でも回すのが理想だが
  コスト高。最低限、教材のテスト観点レビューで機械的に集合比較する。
- (Claude 観察 / Q34 ── ユーザーの写経前確認で発覚)**Q30 の「テストの import 集合 ⊇ 章の新規
  ファイル集合」には逆向きの相棒が要る ── 「テストが import するファイル ⊆ その章までに作られる
  ファイル」**。Phase 5-2 の `test_mst_properties.py` は 5-3 で生まれる `network_design.py` /
  `connectivity.py` を import しており、5-2 単独では collection すら通らなかった(#15 違反)。
  #15 の前方参照の処方(コメントアウト / フェイク / ローカルヘルパ → 後章で抽出)を取らず素の
  前方参照を「注記」で許容していたのが穴。しかも「実測オラクルの置き場は、それが import する
  schema と述語が生まれる章」── これは Q31「ヘルパの置き場は 2 本目の消費者で決まる」と同じ形で、
  一度言語化した設計の問いが別 Phase で再利用できた例。#13 の教材生成後突き合わせに
  「各テストの import 文をその章までの成果物リストと照合」を機械的チェックとして足すべき。
- (Claude 観察 / Q35 ── ユーザーの写経中の指摘で発覚)**#13 の突き合わせは 3 方向要る**:
  (a) 章が触る全ファイル ⊆ 章本文で解説済み(Q35 ①: `connectivity.py` / `build_link_adjacency` /
  `test_graph_primitives.py` が Phase-5-3.md 本文から丸ごと抜けていた ── `test_graph_primitives.py`
  はヘッダのファイル一覧にすら無かった)。(b) 各テストの import ⊆ その章までの成果物(Q34。今回も
  `test_network_design.py` の end-to-end が 5-4 の registry に前方依存)。(c) **章が上書きする過去
  Phase のテストファイルが、過去の assertion を保持しているか(#16)**── Phase 5 の
  `test_graph_primitives.py` が Phase 4-1 版を丸ごと置換し、route プリミティブ 11 本(Q30 の
  dijkstra リファクタ番人を含む)を静かに落としていた。overlay のフル検証は「件数が減っても緑は緑」
  なので**件数の増減だけでは気づけない** ── 「現行版」ラベルのテストファイルは
  `diff <過去 Phase 版> <現 Phase 版>` で「assertion の削除が無いか」を必ず見る。
  さらに Phase-5-3.md は ~17 ファイルを触るのに写経順序が無く、`validation.py`(消費者)が
  `build_link_adjacency`(依存)より前に提示されていた ── **多ファイル章はヘッダに依存順の
  写経リストを置く**(今回 Phase-5-3.md に追加)。
- (Claude 観察 / Q30 フォローアップ)**リファクタの回帰は「以前の Phase の別ファイルのテストを
  再実行」より「その章の第一テストに統合スモークを 1 本」の方が確実**。#16 の初版は「Phase 1 の
  `test_dijkstra_strategy.py` を再実行」で回帰を拾う設計にしたが、ユーザーはそれを実行しても
  `TypeError: cannot unpack ... NoneType`(出所 `segments.py`)を `_dijkstra_segment` の末尾の
  写経ミスに結びつけられなかった。回帰テストが**別 Phase の別ファイル**にあり、エラーが**間接的**
  なほど「テストは正しく、自分の写経が悪い」と気づきにくい。対策として `test_graph_primitives.py`
  (章の第一テスト)に `DijkstraStrategy().solve()` を素で呼ぶスモークを足し、docstring に
  「この失敗 → この行を見る」を書いた。**テストの物理的な近さ(同じファイル・同じ章)+ docstring
  での失敗モードの明示**が、間接的なエラーの原因究明コストを下げる。#16 にこの一文を追加。
- (Claude 観察 / Q31 ── ユーザーの教材レビューで発覚)**ヘルパの置き場は「2 本目の消費者」で決まる**。
  Phase 4-1 で経路復元を `dijkstra.py` に `_reconstruct`(`_` 付き = 非公開)として切り出したが、
  2 本目(Bellman-Ford)/ 3 本目(A*)は規約上 import できず、同じ 7 行をインラインで複製した ──
  教材が「strategy はアルゴリズムそのものに集中」と謳うのと矛盾。**ジェネリックだと分かっている
  処理は 1 本目の時点で公開の共通モジュール(`segments.py`)へ**。「1 本目はローカル、2 本目で共通化」
  は摩擦が写経で顕在化してから直すことになる ── 消費者数が設計時点で分かっているなら先回りする。
  ユーザーが samples を読んで「なぜ Dijkstra だけ関数化?」と問うたのが起点(双方向還流ループの
  例。相談ログ Q31)。
- (Claude 観察 / Q31 → Q32 で言語化)**共通化するのは「機構」であって「オーケストレーション」
  ではない**。`plan_route` / `reconstruct_path` / `route_solution` のような再利用可能な機構は
  `segments.py` に抽出する一方、それらを並べる `solve` 本体は strategy ごとに見せる ── `solve` は
  「この strategy のレシピを DeciTima の語彙で書いたもの」として読めるのが目的で、1 つの
  `plan_route` 呼び出しをラップしてもオーケストレーションに層が増えるだけで思考は減らない。
  「どこまで DRY にするか」は判断が割れるが、CL 開発は各判断を Q ログに「型」として残せる
  (Q2 = 分割 vs 統合、Q15 = 計算か述語か、Q21 = data 層の分割粒度、Q31 = ヘルパの置き場、
  Q32 = 機構 vs オーケストレーション、Q38 = 以前の Phase を触ってでも共通化するかの基準)──
  教材が積み上がるほど新 Phase の判断コストが下がる。

- (Claude 観察 / Q38 ── ユーザーの教材レビューで発覚 → ルール #17 新設)**「以前の Phase を
  過剰に触らない」を明文ルールと思い込んで過剰な自己制約をかけていた**。実在するのは
  (a) 教材本文の遡及**全面**リライト禁止(#3 / #12)、(b) 動機なき遡及**監査**の禁止(Q30)の
  2 つだけで、どちらも「後続 Phase の実在の消費者が駆動する共通化」を禁じていない ── #12
  マーカー / #16 現行版テストがまさにそのための仕組み。Phase 6-1 で `hour_variance` を
  `verify_shift_structure` にインライン追加しつつ、同じ式の metrics ヘルパ 6 本を
  `common.py`(algorithms)に**重複**させたのがその表れ(生成時に「Phase 2 と同じ式」と注記まで
  していた)。教訓 ── **教材生成時に「同じ式 / 同じ処理」と注記した瞬間に「なら 1 箇所に
  置けないか。駆動する消費者は誰か」を #13 の突き合わせで自問する**。Q21(samples 運用の都合が
  設計判断に化ける)/ Q31(消費者数が分かっているなら先回り)と同じ二重ループが拾った 4 例目。

- **やり直しリスクは 0 にできない / 事前理解のハードル**(ユーザー記)。
  コーディング着手前にユーザーが設計を理解し疑問・改善点を事前に解消しておく必要があるが、
  学習を兼ねた進行のためハードルが高い。
  - 提案(採用): 各 Phase の教材生成後・実装着手前に「実装前チェックリスト」
    (作るファイル / 各クラス・関数の責務 / テスト観点)を `Phase-<N>-introduction.md` に置き、
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

#### 【重点課題】進行スピードが担保できない ── 原因要素と改善提案(ユーザー提起)

**課題**(ユーザー記): システム開発とユーザー学習を兼ねる関係上、進行スピードが担保できない。
現状の仕組みでは**納期の定まった実務プロジェクトに向かない**。個人学習でも「想定期間にはめる」
のはカリキュラムとして大事。この観点からの手法改善に大きな意義がある。

CL 開発は「教材 → 実装 → 摩擦 → 教材改訂」の還流ループを**品質優先**で回す設計で、
**時間の次元が手法に組み込まれていない**。律速と変動要因を 8 つに分解し、各々に提案を対で置く
(すべて未採用・ユーザー判断。ルール #10)。

1. **時間の設計が手法に無い** — Phase / 作業単位は成果物(README §19)で定義され、目安工数も
   タイムボックスも無い。実装前チェックリスト(#11)はファイルと責務を並べるが所要見積りが無い。
   → 見積れない = 納期にはめられない / 学習期間を切れない。
   - 提案 A: 実装前チェックリストの各行に「目安: 写経 N 分 + 理解 M 分」列を追加。introduction に
     Phase 合計の目安レンジ。各作業単位に「タイムボックス超過時の分岐 ── 深掘りは
     `## 深掘り(任意)` に隔離してまず通す」を明記。ルール #11 の改定候補。
2. **二重の学習曲線が同時進行** — ドメイン(探索・DP・計算量・最適化)と実装スタック
   (Pydantic v2 判別ユニオン、PEP 695、SQLAlchemy 2.0、pyright standard、pytest 構成)を同時に
   学ぶ。スタック側の摩擦は数も深さも事前に読めない(本セッションだけで `python` 直実行 vs
   `pytest` / `tests.fixtures` の写経漏れ / `operator` ↔ `op` 取り違え、と 3 件の寄り道)。
   - 提案 B: 各章頭に「この章で新しく使う言語 / ライブラリ機能」3 点 + 「既知のつまずき」FAQ
     (予約語 `operator`、`python` 直実行の `sys.path`、絶対 import と overlay 等)。
     `### 検証で発覚した事象` を事後 Notes でなく「章別つまずき集」として教材に前出しする。
3. **還流ループに反復上限が無い** — 「疑問を出し切ってから実装」(#11)は終了条件が開放的。
   1 つの質問が以前の Phase の複数章 + samples + Notes + ルールへの編集を誘発する(#8 / #9 / #12)。
   ループの強み(共進化)がそのまま時間の変動要因。
   - 提案 C: WIP 制限 +「前進優先」。事前質問は実装前チェックリストの責務行に対する**設計判断のみ**
     に限定し、実装詳細の疑問は着手後に即質問。1 質問で解けなければ Claude が代替案を出して前進、
     遡及マーカーの即時反映は必須にせず後続コミットにまとめる。ルール #11 の改定候補。
4. **写経が律速だが学習価値が均一でない** — コア(アルゴリズム本体・スキーマ設計・非自明な判断)
   と定型(`__init__.py` re-export、ORM カラム、薄いルート、fixture)を区別せず全部手打ちする。
   定型の写経は 1 打鍵あたりの学習価値が低く、かつ取り違えバグ(`operator` / `op`)の税を生む。
   - 提案 D: samples の各ファイル冒頭に `# 写経レベル: コア(必ず手写経)/ 定型(コピー可)`
     マーカー。章の「この章で新規作成するファイル」に併記。納期モードでは「定型はコピー、コアだけ
     写経」で律速を 3〜5 割圧縮。ルール #7 / #13 の改定候補。
5. **生成と実装が直列で待ちが出る** — 「Phase#を開始する」→ Claude が introduction + 全章 +
   samples + overlay 検証 を終えるまで着手できない。Phase の難所は生成して初めて判明する
   (Phase 6 手実装破綻 → OR-Tools トラック追加)ため生成時間自体もぶれる。依存の無い作業単位
   (1-1 / 1-3 / 1-5)は並行着手できるのに章の直列な読み順がそれを促さない。
   - 提案 E: 生成の先行(ユーザーが Phase N 実装中に Claude が Phase N+1 のドラフトを別セッションで
     生成)。introduction の章一覧に「今すぐ着手可(依存なし)」を強調表示。
6. **完了判定・到達度の基準が無い** — 「テストを通じた設計理解」(#14 / Q8)は良い方針だが到達度の
   ルーブリックが無い。ある概念に過剰投資しても素通りしても気づけない。章の区切りが曖昧。
   - 提案 F: 各 introduction に「Phase 完了チェック」── 3〜5 問の概念質問(答えは章 / Notes に
     ある。例:「なぜ solve は検証しないか」「スタブが要る / 要らないの判断基準」)。答えられれば
     次 Phase。実装前チェックリスト(事前)と対の「実装後チェック(到達度)」。
7. **状態(Notes / ルール)の肥大化でセッション立ち上げが重い** — `CLAUDE.md` Notes が肥大化し、
   セッションごとに読み直し・コンテキスト圧縮からの復帰・決定事項の再確認が要る。長期・
   ステートフルな分、固定コストが上がり続ける。
   - 提案 G: Phase 完了ごとに「確定した決定」を要約し、詳細な質問ログを
     `textbook/Phase-<N>/decisions.md` へ移設。`CLAUDE.md` Notes は現行 Phase + 横断ルールのみ保持。
     ルール #4 / #8 の改定候補。
8. **検証環境に一手多い(既出課題の格上げ)** — samples が実 app/ ツリーの鏡写しで単体で動かず
   overlay(複製 + シンボリックリンク `.venv` + rsync)が要る。各検証サイクルに手順が乗る。
   - 提案 H: `samples/` に `conftest.py` + `pyrightconfig.json` を置き overlay 不要にする
     (既存の未採用提案「samples 単体実行」(a) の格上げ)。

**横断提案 ── 2 モードの明示**:
- 学習モード(現行): 全写経 + テスト値改変 + 事前質問を厚く。学習効果最大、速度は非保証。
- 納期モード: 速習パス(章のコア設計判断のみ)+ 定型コピー + テストは実行のみ + 学習は
  「事後の解説つきレビュー」で回収。CL 開発の逆(vibe coding + 事後学習)を納期モードとして許容。
  学習効果は落ちると明記。
- 提案 A・D・F があれば、同じ教材のまま 2 モードを切り替えられる(工数見積り / 写経レベル /
  到達度チェックがスイッチになる)。

**Claude の推奨**: まず効くのは A(タイムボックス + 目安工数)/ D(写経レベル)/ C(事前質問を
設計判断に限定)。この 3 つで「見積れる・律速を削る・ループを閉じる」が揃い、納期モードの土台に
なる。F は個人学習の期間管理に直結。B / G / H は固定コスト削減で効いてくる。