# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発ポリシー

この開発・学習手法を **CL(Curriculum Loop)開発** と呼ぶ(定義は Notes の「この開発・学習手法の呼称」)。

README.md の内容に沿って、Claude が設計・各開発ステップの詳細・コードを提案し学習教材として提供する。
ユーザーは Claude と共に開発することで、設計から開発・デプロイまでのプロセスを学習しながら
アプリケーション全体をつかむ。Claude はコードをただ生成するのではなく、設計意図・問題分解・
アルゴリズム・トレードオフを説明する。ユーザーが理解できるよう必要に応じて実装理由を説明する。
既存コードを変更する場合は変更前に影響範囲を調査する。大きな変更を一度に実装せず、検証可能な
単位に分割する。

**設計討議のアジェンダ**(Phase 開始時に Claude が押さえる 7 点。#11 の「実装前チェックリスト」=
`Phase-<N>-introduction.md` に置く表 とは別物):
1. Requirements / 2. Domain Model / 3. Architecture / 4. Algorithm / 5. Complexity /
6. Implementation Plan / 7. Test Strategy

### 進行のルール

番号(#1〜#17)は新設順に固定 ── `textbook/q_a.md` / Notes / textbook 約 30 ファイルからの
`#N` 参照を保つため。以下はカテゴリ別に並べ替えてある。新しいルールは該当カテゴリ末尾に次番号で追加する。

#### A. 教材の生成 ── いつ・何を

**#1.** 学習教材を Phase 毎に `textbook/` フォルダに `.md` 形式で作成する。

**#5.** ユーザーの「Phase#を開始する」というプロンプトで、その Phase の教材・サンプルを生成する。

#### B. Phase 教材の構成 ── ファイルと章立て

**#2.** 学習教材は各 Phase の中で章立てする。**構成は `Phase-<N>-introduction.md`(導入)+ `Phase-<N>-1.md` 以降(作業単位ごと。章番号 = 作業単位番号)**。別建ての概観章やインデックスは作らず、導入ファイル 1 本に集約する(内容は #6、実装前チェックリストは #11)。設計フェーズ(Phase 0)は作業単位を持たないので `Phase-0-introduction.md` + `Phase-0-1.md` 以降(設計トピックの逐次解説)。

**#6.** Phase 毎に**導入ファイル `Phase-<N>-introduction.md`** を各 Phase フォルダ直下に作成する。内容: フェーズの目的 / パイプライン上の位置づけ・作業章を始める前に理解すべき前提(概観)/ 章一覧(各章のトピック・依存関係・リンク)/ サンプルコード一覧 / 実装前チェックリスト(#11)/ 次のフェーズ。`Phase-<N>-1.md` 以降を読み始める前に、この 1 本で前提を説明しきる。章を追加・変更したらここも更新する。

**#11.** 各 `Phase-<N>-introduction.md` に「実装前チェックリスト」を置く。内容: その Phase で作成するファイル一覧 / 各クラス・関数の責務 1 行 / テスト観点。Phase 教材の生成後・実装着手前に、ユーザーがこれで疑問を出し切ってから実装に入る。行キーは作業単位番号(章番号と一致)。設計フェーズ(Phase 0)は実装が無いため省略可。

#### C. 教材内のコード提示 ── 抜粋 / samples / パッケージ

**#3.** 教材で提示するコードは、長いコードブロックを Markdown に直書きせず「要点の抜粋 + 共有 `textbook/samples/` のファイル参照」とする。samples は **1 フォルダを全 Phase で共有**し(Phase 6 end 状態。詳細 `textbook/samples/README.md`)、ユーザーが `decitima-api/app/`(または `decitima-ui/src/`)へ写経・改変して実装する。これで「教材 Markdown / samples / 実コード」の三重管理を避ける。**反映の順序は「相談で決定 → samples に反映(#9)→ 教材の抜粋が追従」**── samples が基準、教材 Markdown はその抜粋。以前の Phase 教材で後続 Phase により内容が変わる箇所の扱いは #12(提示コード・設計)/ #16(テスト)/ #17(共通化の可否)。教材の**構成・体裁・番号**の変更(章のリネーム、節の再編等)はマーカーを付けず内容で上書きする。

**#7.** 教材でコードを提案するときは、配置先のファイルパスを各コードブロックの先頭にコメントで明記する(例: `# app/domain/problems/route_planner.py`)。分割するモジュールはパッケージ(`__init__.py` 付き)として示し、`__init__.py` の re-export 形とファイル間の依存方向も示す。既存教材の修正時・以降の Phase でも同様。

**#9.** 検討・相談の中で提示するコード(クラス名・シグネチャ・型など)に変更が生じたら、対応する `textbook/Phase-<N>/samples/` のサンプルコードにも同じ変更を反映する。反映後は `uv run python`(decitima-api の環境)で実行確認し、可能なら型チェック(pyright standard)も通す。

#### D. 章ごとの解説とテスト設計

> **実装ファイルを作らない章**(Phase 0 の各章、Phase 5-2 / 6-6 のような理論章)は #13 の全ファイル解説・#15 の全ファイル import・#12.4 のリファクタ追従の対象外。introduction の章一覧でその旨を明記する。

**#13.** 各章は、その章で**作成 / 更新する全ファイル**を「責務 1 行 + 中身の要点(型・シグネチャ・非自明な判断。パッケージは #7 のとおり `__init__` の re-export 形も)」で解説する。ファイル構成ツリーに列挙するだけで解説を省略しない。各章の冒頭に「この章で作成 / 更新するファイル」を明記する。教材生成後、章の解説とサンプル / 実装前チェックリストのファイル一覧を突き合わせ、漏れが無いか確認する(#15 の「全ファイルをテストが import」と同一機会に)。

**#14.** 各章の `## テスト観点` 節では、テスト(またはテスト群)ごとに **テスト対象(SUT)/ ドライバ / スタブ(テストダブル)** の関係を明記する。スタブが不要な場合は「スタブ不要 ── 対象が純粋(副作用なし)で外部依存を呼ばないため」のように**理由込みで**書く。狙いは CL 開発の趣旨「テストを通じた設計理解の重要視」── テストダブルの要否がレイヤー設計(純粋 / 副作用)の鏡であることを各章で言語化すること。用語(SUT / ドライバ / スタブ)は初出の章で 1 行定義し、以降の章は関係の明記のみでよい。`Phase-<N>-introduction.md` の実装前チェックリストの「テスト観点」列は対象外(簡潔さを優先)。

**#15.** **章が作成 / 更新する全ファイルを、その章のテストが少なくとも 1 度は import する**こと(教材生成後・#13 の突き合わせと同時に確認)。3 ファイル触って 1 ファイルしかテストが import していない、のような穴を作らない ── 写経漏れ・写経ミスを検知できるようにするため。集約の**機構**のテスト(`get_strategies` / `find_strategy` 等)は具体的な後発実装でなく**フェイク**(fixture で登録)で行う。テスト用フィクスチャ(`tests/fixtures/*.py`)も初出章の作成物として実装前チェックリストに含める。純粋関数は素で、外部依存を注入できる設計(`segment_fn` 等)はフェイクで(#14)。samples のフル検証は共有 `textbook/samples/` を 1 回 overlay して回す(#3 / `textbook/samples/README.md`)。
    - **前方 import の禁止 ── 章 N が作成 / 編集するどのファイルも、その import 先(モジュール **と** モジュール内のシンボル)が {以前の Phase} ∪ {この Phase の章 N まで} で存在しなければならない**。新規ファイルも既存ファイルへの追記も同じ扱い。後の章 M(> N)で生まれるモジュール・シンボルへの import を含むファイル(またはその関数・クラス)は、最初の消費者の章(≥ M)で書く。samples は end 状態で常に解決済みのため overlay では顕在化せず、章順に写経する利用者だけが `ModuleNotFoundError` / `ImportError` で collection を落とす ── **章 attribution の誤り**として扱い、素の前方参照 + 注記での出荷は認めない(前例: `textbook/q_a.md` Q34 Phase 5-2→5-3、Q41 `adjacency.py` 7-1→7-4、Q42 `travel_common` ほか 7-2→7-4 / `verification.py` 7-3→7-4)。**2 つの罠**:(a) **新規ファイルはヘッダ以外に Phase タグを持たない** ── `grep "# (Phase N-"` では出ない。ファイルの**全 `from app.` 行**を読む。(b) **「モジュールはあるが名前が無い」** ── `from x import foo` で `x` は章 N にあるが `foo` が章 M 追加なら前方 import(`verification.py` の `from …travel_common import all_pairs`(7-4)を 7-3 で書いた例)。集約キー + その実装 import + 配線テストを**同じ章**で足すのは前方参照ではない(`registry["travel_planning"]` を 7-5 でまとめるのが正)。**生成後の突き合わせ = 実 import 監査**(#13 と同一機会):samples の各 `.py`(ヘッダに当該 Phase を含むもの)について ① 作成 / 初出章を実装前チェックリスト + 章本文から確定、② 全 `from app.` / `import app.` を列挙、③ 各 import 先の**モジュールとシンボル**の誕生章を確定(モジュールの header 系譜 + そのシンボルを追加した章)、④ ③ > ① を全て潰す。タグ grep は補助。
    - **旧**(Step 2 以前 ── Phase 毎に samples フォルダがあった時代): 各章の samples を「その章までのファイルだけで import 解決・テスト緑」に設計し、集約モジュール(`registry.py` 等)の前方参照はコメントアウト + マーカーで出荷していた。共有 1 フォルダ・end 状態になり、この前方緑の**保証機構**(コメントアウト + マーカー)は退役 ── ただし**規範**(前方 import の禁止)は上のとおり存続し、「編集を消費者の章へ寄せる」で守る(検証は end 状態でまとめて)。

#### E. 後続 Phase での改訂 ── 以前の Phase への遡及

**#12.** 後続 Phase で、以前の Phase の**提示コード・設計・決定事項**に変更が生じたら(共通化のために触ってよいかの判断は #17):
    1. 変更後の内容は当該後続 Phase の教材に書く(要点の抜粋。動くコードは共有 `textbook/samples/`)。
    2. **共有サンプルの当該ファイルに変更を記録する**:
       - **更新**: 旧コードをコメントアウトし、新コードに `# (Phase <N>-<M>)` タグ(理由を一言)。ファイル冒頭コメントの系譜に `改訂 Phase <N>` を足す。**`#` の後にスペース 1 個**(`ruff format` が正規化するため。Python 以外も揃える)。「Phase」と番号の間もスペース(`(Phase 7-3)`。`(Phase7-3)` にしない)。
         ```
         def score(...):
             # (Phase 6-3)
             # return weighted_sum(objectives, metrics)
             # (Phase 9-2) 正規化を挟む
             return weighted_sum(objectives, normalize(metrics, ranges))
         ```
       - **新規**: ファイル冒頭コメントに `# DeciTima samples │ Phase <N>`(または `初出 Phase <N>`)。**1 つのファイルを同一 Phase の複数の章で完成させる場合は、各章の担当分に `# (Phase <N>-<M>)` タグを付け、冒頭コメントに担当章を書く**(例: `# DeciTima samples │ Phase 7(7-2: knapsack_2d / 7-4: KnapsackDpTravelStrategy)`)。単一章で完結する新規ファイルはモジュール docstring 1 行目に `作業単位 <N>-<M>` を書く(テストの docstring と同じ ── どの章の成果物か写経者が即分かる)。`# (Phase N-M)` タグは Phase またぎの改訂だけでなく **Phase 内の章またぎの著述** にも使う。
       - **やらないことに確定**(旧計画の撤回): 教材の当該箇所に blockquote
         `> **[Phase <N> で確定 ── 〈…しない〉]** 当初〈…する予定〉→ 撤回。理由〈…〉。`
       - grep 用合言葉: 更新 = `# (Phase` / 撤回 = `で確定 ──`。
    3. 変更元 Phase の `Phase-<M>-introduction.md` に「後続 Phase での改訂」節を設けて 1 行、`CLAUDE.md`「### 設計判断・検証知見」にも要点を残す。
    4. **リファクタ(公開挙動を変えない整理 ── 関数の抽出・移動・シグネチャ変更)の写経ミスの番人 = 当該章の第一テストの統合スモーク**(リファクタ対象の公開 API を素で 1 回呼ぶ)。docstring に「よくある失敗モード → どの行を見るか」(間接的なエラーほど有効)。以前の Phase の該当テスト(`test_xxx.py`)は共有サンプルにあり写経後に再実行する ── 公開挙動が不変ならアサーションはそのまま、変わるなら変更前後をコメントで対比する。
    - **教材の構成・体裁・番号の変更**(章のリネーム、節の再編、TOC 更新、参照リンクの張り替え等)は #12 の対象外。マーカーを付けず内容で上書きし、決定の記録は Notes / 質問ログ(#4 / #8)に残す。
    - **旧**(Step 2 以前): Phase 毎に samples フォルダがあり、A(以降 Phase で修正予定)/ B(サンプル修正)/ C(で確定)の 3 マーカーで「旧 samples に付す」「現行版を新 samples に置く」を分けていた(`textbook/q_a.md` Q5 / Q6 / Q30 / Q38)。共有 1 フォルダになり `# (Phase N-M)` タグ + 冒頭系譜に一本化。既存の教材本文に残る旧マーカー記述は Step 2 以前の運用の記録(遡及リライトはしない)。

**#16.** → #12.4 に統合。リファクタ追従は「当該章の第一テストの統合スモーク + 以前の Phase の該当テストの写経後 再実行」。#12 が**コードの遡及記録**、#14 が**テスト設計**、#12.4 が**リファクタの写経ミス検知**を扱う。

**#17.** **以前の Phase のコードを共通化のために触ってよいかの判断基準**。後続 Phase が以前の Phase のコードと同じ**ドメインの事実**(式・不変条件・データ構造)を必要とするとき、「コピーして各 Phase に重複させる」か「以前の Phase のコードを抽出・共通化して両者で共有する」かの分岐では **常に共有を選ぶ**。#12 の `# (Phase N-M)` 記録 + #12.4 のスモークのコスト(Claude のタスク量が増える)を払ってでも重複を残さない。**触らないもの**: (a) 教材本文の遡及的**全面**リライト(差分はマーカーで示す ── #12。本文・コードは残す) (b) **駆動する新しい消費者がいない**遡及クリーンアップ / 監査(「どこかに重複はないか」と以前の Phase を巡回すること) (c) レイヤー境界が要求する分割(`domain → algorithms` の import 禁止による `structure._longest_consecutive_run` vs `patterns/sliding_window` など ── これは重複でなく必然)。**判定の一問**: 「この共通化を今 駆動している、この Phase の実在の消費者は何か」に具体名で答えられれば実施、「将来たぶん」「一般に良い設計だから」なら見送る。#12(遡及記録)/ #12.4(リファクタ追従)と対で、#17 は**以前の章のコードそのものを共有化のために変更してよい条件**を定める。「以前の Phase を過剰に触らない」という明文ルールは無い ── 開発ポリシー前文「既存コードは変更前に影響範囲を調査」は #12 記録 + #12.4 スモークのコスト評価を指すのであって「触るな」の意味ではない。

#### F. 記録

**#4.** 実装段階での検討事項・検証段階で発覚した事象は `CLAUDE.md` の Notes に記録する。#4 は包括方針で、具体的な振り分けは ── 質問・相談ログ → #8(`textbook/q_a.md`)/ 進行方法の所感 → #10(retrospective)/ 後の Phase に前向きに効く決定・知見 → Notes「### 設計判断・検証知見」。

**#8.** ユーザーが Claude に行った質問・相談とその回答を `textbook/q_a.md` に**追記**する(保存専用・作業中は参照しない)。各エントリは次の形式:
   1. 疑問が生じた Phase
   2. 質問・相談内容
   3. 回答と対応方針

   進行方針にかかわる決定・設計判断は Notes「### 設計判断・検証知見」にも要約を残す(こちらが参照用)。

**#10.** 本プロジェクトの進行方法について気づいた点(特徴・メリット / 課題 / 課題解決への提案)を `textbook/appendix/cl-development-retrospective.md` に追記する。課題には可能な限り「提案」を対で書く。提案をプロジェクトに組み込むかはユーザーが個別に判断する(Claude は勝手に適用しない)。


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

### 設計判断・検証知見（参照する）

進行の一次記録は `textbook/q_a.md`（保存用・作業中は参照しない）。本節はそこから
「後の Phase の判断に効く決定・知見」を圧縮したもの。詳細は各
`textbook/Phase-<N>/Phase-<N>-introduction.md` と `textbook/appendix/`。

> **本節の 1 エントリは 3 行以内**（現象 / 原因 1 行 / 対策 1 行）。この節は毎ターン文脈に載る。
> 経緯・再現手順・overlay の件数推移などの長文は `q_a.md` に書き、ここは「次の Phase で何を
> 気をつけるか」の 1〜3 行に絞る。CL 開発の進行スピード分析は `cl-development-retrospective.md` §2.5。

#### 基盤の決定（全 Phase 共通）

- **既存 LLM チャット機能は Phase 11 まで route 無効化（コードは保持）** ── `/chat` を router 集約から外す。`app/ai/`・関連モデル・マイグレーションは Phase 11 の土台として残す。
- **アルゴリズムは 2 トラック（手実装 + 産業ソルバー）を同一 `AlgorithmStrategy` 契約で並存** ── `meta.implementation` で区別。Phase 3 ベンチ・Phase 14 比較がそのまま「手実装 vs ソルバー」比較になる。詳細は「設計上の決定事項」節。
- **ワークスペースルート = `decitima-project`（教材のみ）、ui/api は `.gitignore` 除外** ── submodule は使わない。
- **Phase 0 設計**（詳細 `Phase-0-introduction.md`）: ハイブリッドスキーマ（`objectives`/`constraints` は共通の型付き語彙、`data`/`assignments` は `problem_type` を判別子にした Pydantic 判別可能ユニオン）/ `domain/`・`algorithms/` は純粋レイヤー（副作用なし、乱数は seed を入力に）/ `AlgorithmStrategy` は Protocol・`solve` は検証しない（制約判定は Verification）/ Validation（問題の妥当性）と Verification（解の制約充足）を分離 ── hard 違反 → `status=invalid`、soft → `soft_penalty`、違反は例外にしない / DB は JSONB `payload` + 検索キー（`problem_type`/`status`/`algorithm_name`）のみカラム化・JSON カラムは毎回まるごと代入 / MVP は同期実行 + タイムアウト（ジョブキューなし・YAGNI）・solve 結果は永続化 / 専用エンドポイントを作らず `POST /api/v1/solve` に `problem_type` 付き `OptimizationProblem` / 制約は `ConstraintBase` + サブタイプ + `GenericConstraint`（pyright `reportIncompatibleVariableOverride` 回避）/ アルゴリズムは 2 層 ── 問題まるごとは `AlgorithmStrategy`（registry に載る）、部品・技法はプリミティブ（素の純粋関数、registry 非搭載）。

#### 設計判断の型（新しい Phase の判断に流用する）

経緯は `textbook/appendix/cl-development-retrospective.md` §1-E。

- **分割 vs 統合**: 「一緒に変わるものを同じファイルに」。ピアが互いを import しなければ、アグリゲータ（`problem.py` が `RouteData`/`ShiftData` を束ねる、`registry.py`、`routes/__init__.py`）は悪い密結合ではない。
- **「これは計算か? 述語か?」**: 問題フィールドの純粋述語 → `domain`。BFS 等を走らせる計算 → `algorithms`。hard ゲート判定 → `services`。`domain → algorithms` の import 禁止は誤りを写経中に顕在化させる **guardrail** であって判断の理由ではない。
- **data 層の粒度**: model / schema / repository は「永続化の関心事」で 1 ファイル（`optimization.py` = Problem / Solution / BenchmarkRun）。`routes` / `services` は「操作」で割る。「短いから別ファイル」はしない。1:1:1:1 には収束しない。
- **ヘルパの置き場は「2 本目の消費者」で決まる**: ジェネリックと分かっている処理は 1 本目の時点で公開の共通モジュールへ（`segments.py` の `reconstruct_path` / `negative_*_violation`、`shift_metrics.py`）。
- **共通化するのは機構であってオーケストレーションではない**: `plan_route` / `reconstruct_path` / `route_solution` は共通化、`solve` 本体は strategy ごとに直線的なレシピとして見せる。
- **以前の Phase のコードを共通化のために触ってよいか** = 進行のルール #17。「この共通化を今 駆動している、この Phase の実在の消費者は何か」に具体名で答えられれば実施、「将来たぶん」「一般に良い設計だから」は見送る。
- **samples 運用の都合が設計判断に化けていないか**: 「このファイルを分けた理由は設計か、samples の書きやすさか」を教材生成時に自問する（`repositories/benchmark.py` の単独化は前者に見せた後者だった）。
- **YAGNI で見送ったもの**: ジョブキュー（MVP は同期で十分）/ `bfs_shortest_path` の全最短経路化（消費者なし）/ `verifications` テーブル（`Solution.status` + `payload` で足りる）/ hypothesis（手書きジェネレータ + for ループで足りた）。

#### 未ルール化の確定事項

- `bfs_shortest_path` は単一経路のまま（全最短経路を要る消費者が無い）。タイブレークが要るなら近傍を `sorted(...)`。
- MVP は `payload` 内クエリをしない。取得はすべて id / 実カラム（`problem_type` / `status` / `algorithm_name` / `user_id` / `created_at`）経由。
- decitima-ui の feature slice（`route-planner` / `network-designer` / `shift-scheduler`）は **generic 化しない** ── `problem_type` / 解の型 / 可視化が違う。共有は `lib/api/` の型と `apiFetch` だけ。
- `weighted_sum` の各 metric を [0,1] に正規化してから重み付き和を取る改善は **Phase 9 / 10 / 14** で実データのレンジを見てから（生の `Σ wᵢ·fᵢ` は `labor_cost` のようなスケールの大きい目的に支配される）。
- NumPy / SciPy / pandas は「設計上の決定事項」のラベル付き境界の裏だけ。フォーク（数値ライブラリ全面版）の影響調査は `textbook/appendix/library-fork-impact.md`。

#### Phase 別の要点（詳細は各 `Phase-<N>-introduction.md`）

- **Phase 1**: `select_strategy` は `services/algorithm_selection.py`（`registry.find_strategy` は純粋で該当なし → `None`、services が `NoAlgorithmError`）/ 型エイリアスは PEP 695 `type` 文 / solve のタイムアウト = `asyncio.wait_for(asyncio.to_thread(strategy.solve, ...))` → `SolveTimeoutError`（504）、超過してもスレッドは止まらない / `OptimizationProblem` に `problem_type == data.problem_type` の `model_validator` / objectives 評価器は Phase 1 で投機実装 → 消費者なしで撤回 → Phase 6。
- **Phase 2**: `SEMANTIC_CHECKS` = `domain/problems/semantic.py`、`CHECKERS` = `domain/constraints/__init__.py`、2 サービスは「レジストリを回すオーケストレーション」/ `route_reachable` を `algorithms/graph/reachability.py` に（計算）、判定は `services` / 構造検証は `domain/solutions/structure.py`（合成モジュール ── `ConstraintViolation` の循環回避）/ `StaffingConstraint` は opt-in の `check_staffing` / 連続勤務日数の Verification は完成割当の 1 回スキャン（`itertools.pairwise` + `date` 差分。Sliding Window に前方依存しない）/ `POST /verify` は DB を触らず Semantic Validation も走らせない、invalid 解も 200。
- **Phase 3**: `services/measurement.py::measure_call`（時間 = `perf_counter` の中央値 + 四分位、メモリ = `tracemalloc` ピーク）/ `_ops` は各 strategy が `solve()` 内で積む ── **アルゴリズム定義の単位なので time/memory のように直接比較しない** / `BruteForceRouteStrategy` = registry 2 本目・Phase 3 の正解オラクル / `BenchmarkService` は Validation を通す、Verification は計測の外、`resource="benchmark"` の専用レート制限 / `benchmark_runs` テーブル（`id` / `user_id` / `problem_type` / `created_at` + `payload` JSONB）、`Problem` への FK なし / `quality_ratio` は「run 中の最良値」基準 / numpy は `measurement.py` の集計だけ / pandas は分析トラック `analysis/`（dev 依存、`app` から切り離し、`export → JSONL → DataFrame` の一方向）── コア層と solve/verify/benchmark 経路には入れない / 最小ログイン UI を 3-5 に、`refreshTokens()` を `AccessToken` 契約に修正。
- **Phase 4（Route Planner）**: グラフプリミティブを `graph/{adjacency,segments,waypoints}.py` に整理（`build_adjacency` を `adjacency.py` へ、`reconstruct_path` / `negative_weight_violation` / `negative_cycle_violation` は `segments.py` の公開関数）/ 負辺 = `RouteEdge.weight` の `ge=0` 撤廃 + `RouteData.allow_negative` + `model_validator` ── Bellman-Ford が負閉路検出、Dijkstra / A* は負辺で `infeasible` / A* の h(n) = `RouteNode` 座標のユークリッド距離、座標なしは 0（→ Dijkstra に縮退）/ 複数経由地 = `optimize_waypoint_order`（m ≤ 8 は全順列、それ以上は与えられた順。近似は Phase 7）/ networkx を **runtime 依存**（`library:*` は solve/benchmark 経路で動く）、library トラックは `_ops` を出さない / rule-based `select_strategy`（負辺 → `bellman_ford` / 全座標 → `a_star` / 既定 → `dijkstra`）/ **実測: MVP 規模では手実装 Dijkstra が networkx より速い**（`crossover_size` = `None`）/ 経路図は手描き SVG `GraphCanvas`。
- **Phase 5（Network Designer）**: Union-Find（経路圧縮 + ランク合併、`union` が bool を返す ── Kruskal が閉路判定に使う）/ 5-2 は MST 理論章（実装ファイルなし）/ `network_design` 配線: `NetworkDesignData` / `NetworkDesignSolution` をユニオンに、`NetworkLink.endpoints` は**常に無向**、連結性の計算は `algorithms/graph/connectivity.py`（BFS ベース）・判定は `services` / MST = Kruskal（`UnionFind`）/ Prim（`heapq`）/ `NetworkxMST`、`registry` に `"network_design"` キー新設 / ページは Route Planner と同型、generic 化しない。
- **Phase 6（Shift Scheduler ── MVP 完成）**: `weighted_sum(objectives, metrics) -> float`（minimize 向きスカラー。minimize → `+w·f`、maximize → `−w·f`）── **スケール差の落とし穴**（`labor_cost` が支配、`weight` が意図を表さなくなる）/ shift の metrics 計算は `domain/solutions/shift_metrics.py` に集約（検証器 + 4 strategy が共有 ── drift 防止）、`type Assignment` は `domain/solutions/shift_scheduler.py`（両レイヤーが循環なしで届く葉）・**共有シンボルは定義元から import**（再エクスポート経由は `ruff --fix` で静かに壊れる）/ プリミティブ = `patterns/sliding_window.py`（逐次の連続日数判定）/ `patterns/difference_array.py`（imos 法）── Phase 2 の `_longest_consecutive_run` は書き換えない / 手実装 3 strategy（Greedy / Backtracking / Branch and Bound）+ `scheduling/common.py` の共通足回り / B&B の anytime は**決定論的なノード予算**（`_MAX_NODES = 200_000` + `metrics["_truncated"]`）── `solve` は純粋なので壁時計を見ない / 6-6 は全列挙オラクル章（実装ファイルなし）/ OR-Tools CP-SAT = `OrToolsCpSatShiftStrategy`、`ortools` を `[project].dependencies` に、`hour_variance` は CP-SAT では spread（max−min）で代理、決定論は `num_search_workers=1` + `random_seed` 固定。
- **Phase 7（Travel Planner）**: `travel_planning` を 4 つ目の problem_type に配線（Phase 5-3 と同型 ── 葉 2 本 + ユニオン 1 メンバー + `semantic` 3 チェック + `structure` 1 arm + チェッカー 2 arm は **7-3**、`verification._verify_travel_plan` は **7-4**（`travel_common.tour_cost` 依存 ── Q42）。route/network/shift 無変更、`alembic` no-op）/ **travel には Validation の計算ゲートが無い** ──「回れるか」は solve の責務（`services/validation.py` に travel 分岐を足さない。`Phase-2-2.md` §3 の「計算か述語か」の 3 例目）/ `graph/floyd_warshall.py` = **手実装の三重ループ**（numpy なし。全点対最短、`math.inf` 初期化、平行辺は軽い方、O(V³)）── registry 非搭載のプリミティブ / `knapsack_2d`（2 次元 0/1 ナップサック、容量は**降順**、`take[][][]` で復元、擬多項式 O(n·A·B)、float cost は消費 `ceil` / 容量 `floor` で整数グリッド化）/ **教材の核 ── DP は place cost/duration だけで詰める =「移動費用を無視した上界」**。`order_and_cost`（Floyd-Warshall + `optimize_waypoint_order` の anchor 閉路）が足す移動分で予算超過 → Verification が `invalid`。Greedy は 1 手ごとに実際の巡回コストで判定 → 必ず valid。BruteForce（部分集合の全列挙、移動込みで真の最適）が正解オラクル / **章の帰属（Q41 / Q42）── 7-1: `floyd_warshall`（純粋）/ 7-2: `knapsack_2d`（純粋、既存ファイル変更なし）/ 7-3: ドメイン配線（葉・ユニオン・semantic・structure・constraints ── `elements.py` 共通化含む Q43・fixture）/ 7-4: `travel_common` 全体 + `build_leg_adjacency` + `KnapsackDpTravelStrategy` + `_verify_travel_plan` + m>8 近似 / 7-5: Greedy・BruteForce・registry・select・e2e**。`travel_common` は `TravelData`（7-3）を要るので全関数 7-4 / `optimize_waypoint_order` の m > 8 を「与えられた順」→ 最近傍法 + 2-opt に（Phase 4-1 の宿題 Q27。シグネチャ不変なので route 3 strategy は無変更で恩恵）/ `family="optimization"` 再利用 / `analysis/travel_analysis.py`（`dp_vs_greedy` の gap / `invalid_rate_by_size`）/ UI は Route Planner と同型の 4 スライス目、`TravelPlanCanvas` は `GraphCanvas` 再利用。

#### 検証で発覚した事象（再発防止）

> **overlay 検証は共有 `textbook/samples/` を clean な `decitima-api/backend` + `decitima-ui` に 1 回重ねて回す**(手順・期待値は `textbook/samples/README.md`)。

- **Pylance の `ProblemData` 型式エラー(型式では変数を使用できません / reportInvalidTypeForm)** — 原因は `ProblemData` 自体ではなく、`RouteData` / `ShiftData` の import が Pylance で未解決なこと。ワークスペースを `decitima/`(プロジェクトルート)で開くと `app` パッケージ(`decitima-api/backend/app`、3 階層下)を Pylance が見つけられない。対応: `decitima-api/backend/pyproject.toml` に `[tool.pyright]`(`include = ["app", "tests"]` / `venvPath = "."` / `venv = ".venv"` / `typeCheckingMode = "standard"`)を追加、加えて `decitima/.vscode/settings.json` に `python.analysis.extraPaths: ["decitima-api/backend"]`。適用後「Developer: Reload Window」。この設定で再発しない。bare import(`from route_planner import ...`)は実行時 `ModuleNotFoundError` にもなるので絶対 import 必須。この `[tool.pyright]` と `.vscode/settings.json` は「開発環境に必須の tooling 設定」であり、`fastapi-langchain-template` への還元候補。
- **テンプレート由来の型債務** — `typeCheckingMode = "standard"` を入れたところ、テンプレート由来のコード(`app/ai/**` の `GraphState` 部分構築、`tests/unit/test_ai_graph_nodes.py` / `test_auth_service.py` のテストフェイク、`app/repositories/conversation.py` の `get_by_id` override)に既知の型エラーが出た。DeciTima の新規コードは standard で厳格に保ちつつ、これらは `[tool.pyright]` の `ignore` で当面抑制。Phase 11(`app/ai` 作り替え)とテスト基盤整備で解消し、`fastapi-langchain-template` へ還元する。
- **Phase 1 の軽微な pyright / 実装上の対応** — (1) `binary_search` の `_Comparable` プロトコルは `__lt__(self, other: Any)` にする(`object` だと組み込み比較型が満たせず standard で警告)。(2) テストで `FakeRedis` を `SolveService` に渡す箇所は `cast(Redis, FakeRedis())`(既存 `test_auth_service.py` は pyright ignore で処理していたが、Phase 1 は cast で明示)。(3) 判別可能ユニオンの消費側テストは `assert isinstance(sol.assignments, RouteSolution)` で絞り込む(サンプルの `_route(sol)` ヘルパ)。
- **`NumericBoundConstraint` のフィールドが Phase 1 samples(`op`)と実 backend(`operator`)でズレていた** — Phase 1 写経時にユーザーが `op` → `operator` にリネーム(実 backend は自己整合、fixture も更新済み)、samples 側は `op` のまま残っていた。stdlib の `operator` モジュールと同名だが、モデルの属性名なので衝突せず、チェッカー側も `from operator import le, ...` の名前 import なら `import operator` しないので安全。Phase 2 の `check_numeric_bound` が初の実消費者なので、Phase 2 生成時に **samples を `operator` に同期**(`textbook/Phase-1/samples/app/domain/problems/problem.py` と `tests/fixtures/optimization.py`、`Phase-0-2.md` §4.2 と `Phase-1-1.md` §2 に「サンプル修正」マーカー)。rule #9 のサンプル同期であって設計変更ではない。
- **numpy / pandas / matplotlib を実 `.venv` に導入した** — Phase 3 samples 検証時、共有 `.venv`(overlay がシンボリックリンク)に `uv pip install 'numpy>=2.0' 'pandas>=2.2' 'matplotlib>=3.9'` を実行済み。numpy は runtime 依存(`[project].dependencies`)、pandas / matplotlib は 3-7 の分析トラック用(`[dependency-groups].analysis`)として `pyproject.toml` に追加予定。ユーザーが `uv sync` するまで `pyproject.toml` / `uv.lock` は未更新。notebook 実行の検証には `uv run --with jupyter --with nbconvert --with ipykernel jupyter nbconvert --execute` を使用(jupyter はロックしない方針)。

- **既知の pre-existing 事象(Phase 4 とは無関係)** — 写経先の `decitima-api/backend/tests/unit/test_brute_force_strategy.py` に `test_deterministic_same_input_same_output` が **2 回定義**されており(L58 と L73)、pyright が `reportRedeclaration` を 1 件出す。Phase 3 samples 側は 1 回のみ ── Phase 3 の写経時に混入した重複。写経先の当該 1 関数を消せば解消(Phase 4 の変更対象外)。
- **`nx.Graph` は平行エッジを持てない** — `RouteData` は同じノード対に複数 `RouteEdge` を持てる(`build_scaled_route_problem` は `rng.sample` で偶発的に作る)。`NetworkxShortestPath._to_graph` / `NetworkxMST` は `_add_min_edge`(既存があれば軽い方を残す)で対応。最短経路・MST では重い平行辺は絶対に使わないので手実装と等価。これを入れないと `test_networkx_matches_handwritten_dijkstra_property` が seed 依存で落ちる(発覚 → 修正済み)。
- **Phase 4-1 のテスト観点の穴 + `_dijkstra_segment` の写経バグ(ユーザー写経で発覚。相談ログ Q30)** — 4-1 は `adjacency.py` / `segments.py` / `waypoints.py` の 3 ファイルを新規作成し `dijkstra.py` を大改修するが、章が指定するテスト `test_graph_primitives.py` は **`adjacency.py` しか import しない**。`waypoints.py` の写経漏れ(`ModuleNotFoundError`)は Phase 1 の `test_dijkstra_strategy.py` を回して初めて発覚した。対応: (1) `test_graph_primitives.py` を拡張し `segments`(`plan_route` にフェイク区間を注入)/ `waypoints`(`optimize_waypoint_order` にフェイク cost)/ `collect_route_constraints` / `route_solution` をカバー(import が `segments → waypoints` を辿るので 3 ファイルのどれかの写経漏れで collection が赤に)。(2) Phase 1 の `test_dijkstra_strategy.py` を **Phase 4 samples の現行版**として置き(docstring に「4-1 で内部が segments 経由に。公開挙動は不変。赤なら refactor の写経ミス」を追記、アサーション不変)、Phase 1 samples にマーカー。(3) 進行のルール **#16 を新設**(以前の Phase のテストのリファクタ追従)+ **#15 に「章が作る全ファイルをその章のテストが 1 度は import する」条項**。ユーザーの写経バグ自体は `_dijkstra_segment` の末尾を `return _reconstruct(prev, start, goal, dist[goal]), pops` でなく `_reconstruct(prev, start, goal, weight)`(`return` 無し・`weight` 未定義・`, pops` 無し)と写していたこと ── §3.3 が `solve` の before/after しか見せず `_dijkstra_segment` / `_reconstruct` の変化を見せていなかったのが遠因。§3.3 に `_dijkstra_segment` 末尾 + `_reconstruct` の before/after を追加。overlay `ov4`: `test_graph_primitives.py`(+6)+ `test_dijkstra_strategy.py` 現行版で route-end **182 passed / 2 deselected**、ruff / pyright clean。写経先(`decitima-api/backend`)の `dijkstra.py` バグはユーザーが修正(2026-09-03)。
  - **フォローアップ**: 上記反映後もユーザーが `test_dijkstra_strategy.py` で `TypeError: cannot unpack non-iterable NoneType`(出所 `segments.py`)に当たり、`_dijkstra_segment` の末尾の写経ミスと結びつけるのに手間取った。**#16 の「以前の Phase の別ファイルのテストを再実行」だけでは、間接的なエラーのとき詰まりが解けない**。→ (a) `test_graph_primitives.py`(章の第一テスト)に `DijkstraStrategy().solve()` の**統合スモーク**を 1 本追加 ── 写経ミスをその章のテストでその場で赤にする。docstring に失敗モード(この `TypeError` → `_dijkstra_segment` の末尾を見る)を明記。(b) samples `dijkstra.py` の `_dijkstra_segment` 直前に「写経の罠」コメント。(c) `Phase-4-1.md` §3.3 に「写経ミスの見分け方」blockquote、§テスト観点を「第一テスト = graph_primitives(統合スモーク込み)/ 補助 = Phase 1 の再実行」に整理。(d) #16 に「第一の番人は当該章の第一テストに統合スモーク」の一文。overlay `ov4` route-end **183 passed / 2 deselected**、`_dijkstra_segment` の `return` を消すとスモークが `TypeError` で赤(4-test 版は素通り)。ユーザーは L61 を自力修正済み(写経先 `pytest tests/unit/test_{dijkstra_strategy,graph_primitives}.py` → 10 passed)。写経先は触らない(2026-09-03)。
- **`Phase-4-4.md` の `waypoints.py` 作成 Phase 誤記** — L9/L14 が「4-2 で作った `waypoints.py` を本実装に差し替える」としていたが、`segments.py` が `waypoints` を import し `dijkstra.py`(4-1 でリファクタ)が `segments` を import する以上、3 ファイルとも **4-1 で作られる**。samples は end 状態(全順列版)なので 4-4 で写経するファイルは無い ── 4-4 は「全順列で最適順を選ぶ」挙動の深掘りとテスト(`test_route_strategies.py` の経由順セクション)に主眼を移す。`Phase-4-1.md` / `Phase-4-4.md` の「4-1 は素朴版」表現も「骨格を 4-1、深掘りは 4-4」に統一(Q30 で修正)。

- **`test_mst_properties.py` / network fixture の作成 Phase 誤記 ── 5-2 → 5-3(相談ログ Q34)** — 教材は `test_mst_properties.py` と `tests/fixtures/optimization.py` の network 部分を作業単位 5-2 の成果物としていたが、両方とも 5-3 で生まれる `app.domain.problems.network_design`(`NetworkDesignData` / `NetworkLink`)を import し、テストはさらに 5-3 の `app.algorithms.graph.connectivity`(`forms_spanning_tree`)にも依存する ── 5-2 まで写経した状態では collection 段階で `ModuleNotFoundError`(進行のルール #15 違反。`Phase-5-2.md` §5 は素の前方参照を注記だけで許容していた)。5-3 の `test_network_design.py` も既に `build_network_problem` に依存しており、fixture は元々 5-2 の clean な成果物になり得なかった。対応: 実測テストと network fixture を **5-3 の成果物**に移し、5-2 は理論章(実装ファイルなし)にした ── **教材 Markdown の章-attribution 変更のみ**。`samples/` のファイル内容・配置は不変(`test_mst_properties.py` docstring 冒頭の「作業単位 N」表記だけ是正)。overlay は Phase 5 network-end **206 passed / 2 deselected**(この時点。直後の Q35 で `test_graph_primitives.py` 是正により **217** に)(2026-09-07)。

- **`test_network_design.py::test_network_design_end_to_end_pipeline` が `registry["network_design"]`(5-4)に前方依存(相談ログ Q35 ②)** — validate→select→solve→verify を通すこのテストは 5-3 の `test_network_design.py`(5-3 の成果物)に入っていたが、`registry["network_design"]` は 5-4 で埋まるため 5-3 状態では `select_strategy` が `NoAlgorithmError`(実測: 5-3 状態で 1 failed / 12 passed)。#15 違反。→ `test_mst_strategies.py`(5-4)へ移設。5-4 には strategy の solve テスト / select→kruskal テストはあったがフルパイプラインの統合テストが無かったので、移設先として過不足ない。`test_network_design.py` は 9 本に。

- **Phase 5 samples の `test_graph_primitives.py` が Phase 4-1 版を丸ごと置換していた(相談ログ Q35 ③)** — Phase 5 の版は `build_link_adjacency` / `connectivity` の network 4 テストだけを持ち、Phase 4-1 の route プリミティブテスト 11 本(`build_adjacency` / `plain_adjacency` / `plan_route` の連結 / `collect_route_constraints` / `route_solution` / `optimize_waypoint_order` / `has_negative_weight` / **Q30 で足した dijkstra リファクタの統合スモーク `test_dijkstra_solve_still_works_after_segments_refactor`**)を落としていた。overlay で Phase 4 版を上書きするため **Phase 5 end 状態でこれらが消失**(実測: 従来 200 passed excl analysis)。→ Phase 5 版 = **Phase 4-1 の全内容 + network 4 本の「現行版」**に是正(route 分の assertion は 4-1 のまま = #16 の番人を維持)。是正後 **211 passed(excl analysis)**。Phase 5 の件数「206」→ analysis 6 本込みで **217** に更新(introduction §6 / 本 Notes の Q29・Q34 の「206」記述)。

- **`shift_metrics.py` 抽出で `verify_shift_structure` の call site 引数が `sol` → `sol.assignments` に変わる写経ミス(Q38 のフォローアップ。ユーザー写経で発覚)** — Phase 6-1 で metrics ヘルパを `structure.py` から `domain/solutions/shift_metrics.py` に抽出したとき、ヘルパのシグネチャが `_hours_by_staff(data, sol: ShiftSolution)` → `hours_by_staff(data, assignments: dict)` に変わった。ユーザーが `hours_by_staff(data, sol)` と機械的に写し、`test_greedy_shift.py`(6-3、`SolutionVerificationService().verify` 経由)で `AttributeError: 'ShiftSolution' object has no attribute 'items'`。**遠因**: `Phase-6-1.md` §2 が末尾 1 行(`return out, assignment_metrics(...)`)しか見せず、関数本文の 2 つの call site(`hours_by_staff` / `working_days_by_staff`)の引数変更を見せていなかった(Q30 の `_dijkstra_segment` と同型)。対応: (1) samples `verify_shift_structure` の先頭で `assignments = sol.assignments` を **1 度だけ**束ね、全 call site を `f(data, assignments)` に統一(`.assignments` の反復 4→1、`sol.assignments` は plain dict 属性なので振る舞い不変)。(2) §2 を「変わった行の before → after 表 + 写経の罠 blockquote(この `AttributeError` → `sol` を渡している / `uvx pyright` なら `reportArgumentType`)」に差し替え。(3) §テスト観点に「6-1 の `test_verification_service.py` が第一の番人 ── その場で `AttributeError` で赤。6-3 まで持ち越さない」。overlay `ov6f2` 再検証: 修正 `structure.py` で `uv run pytest` **271 passed / 2 deselected**、ruff / pyright clean。`assignments` 束ねを消して `hours_by_staff(data, sol)` に戻すと `test_verification_service.py` が `AttributeError` で赤(第一の番人が効く)。写経先(`decitima-api/backend`)はユーザーが 3 箇所を `sol` → `sol.assignments` に修正(Claude は触らない)。

- **リファクタで `type Assignment` を `shift_metrics.py` に巻き込んでいた → 置き場は `shift_scheduler.py`(Q38 のフォローアップ 2。ユーザーの import 経路監査 → 写経で循環 import 発覚)** — metric **式**の集約が目的だったのに、`common.py` の `type Assignment = dict[str, list[str]]` も一緒に `shift_metrics.py` へ移していた。4 strategy の `from ...common import Assignment` は暗黙 re-export で動く(271 passed)が定義まで 2 hop。**当初 `common.py` に戻したが誤り** ── `shift_metrics.py`(`app/domain/solutions/`)は `Assignment` を要るのに `domain → algorithms` 禁止で `common`(`app/algorithms/scheduling/`)から import できず、ユーザーが写経で `ImportError: cannot import name 'Assignment' ... (circular import)`。**共有型の置き場は「両レイヤーが循環なしで import できる最下層」で決まる** ── `Assignment` は `domain/solutions/shift_scheduler.py`(`ShiftSolution.assignments` の型そのもの。app を何も import しない葉)に定義。`shift_metrics`(domain 兄弟)/ `scheduling/common`(algorithms→domain。既に `ShiftSolution` を同ファイルから import 済み)の双方が届く。route の `Segment`↔`segments.py` 類推は「`Segment` を要る domain ファイルが無い」前提でのみ成立 ── shift には無い前提。**当初は `common` が再エクスポートし strategy の import 行を据え置いたが、ユーザーが「間接 import では?」と指摘 → 4 strategy も `from app.domain.solutions.shift_scheduler import Assignment` の定義元 import に修正**(関数だけ `common` から。route strategy が `Segment` を `segments.py` から取るのと揃えた)。再エクスポート経由の import は動くが、元モジュールが内部使用をやめると `ruff --fix` が F401 で削除して静かに壊れる。Phase 1 samples の `shift_scheduler.py` に #12 マーカー(#17 ── 凍結ファイルを触ってでも重複排除の実例)。教訓 ── **リファクタで「まとめる対象」を宣言したら範囲を厳密に守る**(式の重複排除 ≠ 型エイリアスの移動)。#13 の突き合わせに「移動したシンボルは宣言した対象だけか」+「共有型は両レイヤーが循環なしで届く最下層に置いたか」+「各 import はその名前の**定義元**を指しているか(再エクスポート経由でないか)」を足す。

- **Phase 7 ── インラインタグは `# (Phase N-M)`(`#` の後にスペース必須)** — `ruff format` が `#comment` → `# comment` に正規化する。#12 / `samples/README.md` の例と grep 合言葉を `# (Phase` に是正済み(既存 27 タグも全てスペースあり)。
- **Phase 7 ── `ruff` は scope を `app tests analysis` に限定** — `textbook/samples/` 全体にかけると `alembic/versions/*.py`(ruff `extend-exclude` 対象)を巻き込む。誤爆したら `git checkout textbook/samples/alembic/`。
- **Phase 7 ── `sample_travel_runs.jsonl` の作り方** — 実 `BenchmarkService` を SQLite で `build_scaled_travel_problem(5,6,7,9,12)` × 予算ゆるめ/きつめで回し `dump_rows` した 5 run(DP invalid/valid 両方を含む)。`analysis/*.py` 本体は pyright include 外、`tests/analysis/` は対象。
- **Phase 7 ── 章順写経で collection が崩れる前方 import が 5 件(Q41 で 1 件、Q42 で残り 4 件是正)** — `adjacency.py`(7-1→7-4)/ `travel_common.py` + `knapsack.py` + `test_knapsack.py`(7-2 の新規ファイルが 7-3/7-4 依存)/ `verification.py` の `from …travel_common import all_pairs, tour_cost`(モジュールは 7-2、名前は 7-4 ── import-time `ImportError` で 7-3 完了時に全テスト崩壊)/ `test_travel_strategies.py`(7-4 初出、7-5 モジュール import)。原因: Q41 の監査がタグ grep 依存(新規ファイルは不可視)+「モジュールはあるが名前が無い」を見ず。対策: 7-2 を純粋 `knapsack_2d` に、`travel_common` 全体 + `KnapsackDpTravelStrategy` + `_verify_travel_plan` を 7-4、`test_travel_common.py` 新設。#15 を実 import 監査(モジュール + シンボルの誕生章)に、#12.2 に「Phase 内の章またぎ著述も `# (Phase N-M)`」。詳細 §2.6 / Q42。
- **Phase 7-3 ── `constraints/{forbidden,required_inclusion}.py` の私設ヘルパ重複を `constraints/elements.py::solution_element_ids` に一本化(Q43)** — 差は route の nodes/edges 1 行だけ、network/travel arm は同一で Phase 5-3 / 7-3 が両コピーに並行追加していた(#17 ── Q38 `shift_metrics` と同型)。`aspect` 引数で route だけ分岐。`check_*` の public 挙動・テスト不変。overlay 341 passed(既存 338 は Q41/Q42 の更新漏れ、実測 340 + 新ヘルパテスト 1)。
- **isinstance ディスパッチ arm の番人テストは「arm 未接続で赤」でなければ #15 の穴(Q44)** — ユーザーの `structural_verify` 写経が network(5-3)/ travel(7-3)の 2 arm を欠き、`verify_*_structure` が dead code 化 → travel の予算超過 hard チェックが走らず `test_dp_can_overrun`(7-5)で初めて FAIL。原因: `test_structural_verify_dispatches_{network,travel}` が `assert isinstance(violations, list)` / `assert violations == []`(良い解)しか見ておらず、ルーティングが切れても緑。対策: 両テストを「ルーティング先の violation をアサート」に強化(arm を外すとその章のテストが即赤)。教訓 = 章の配線を章のテストがその場で突く(Q30 / Q38 と同型)。

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

- 手順は「### 進行のルール」#1〜#17(A 生成 / B 構成 / C コード提示 / D 章とテスト / E 改訂 / F 記録)。
- 決定・知見の記録: 一次記録は `textbook/q_a.md`(保存用)、参照用ダイジェストは本 Notes
  「### 設計判断・検証知見」、振り返りは `textbook/appendix/cl-development-retrospective.md`。

### 進行方法の所感・課題

CL 開発の振り返り（特徴とメリット / 課題と提案 / 【重点課題】進行スピードが担保できない /
進行ルール #1〜#17 の重複・グレーの整理）は
`textbook/appendix/cl-development-retrospective.md` に集約。以降の気づき（進行のルール #10）も
そちらに追記する。MVP（Phase 0〜6）時点の課題と対応の一覧は同ファイル §1。
