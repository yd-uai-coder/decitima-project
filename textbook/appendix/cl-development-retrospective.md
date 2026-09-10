# 付録: CL(Curriculum Loop)開発 振り返り(Phase 0〜6 / MVP)

> **Phase 6(MVP)完了時点の棚卸し。** CL 開発の進行で発生した課題と対応を一覧化し、MVP 後も
> 残る継続課題を整理する。**現行 Phase の教材・samples・コードは変更しない。**
>
> この一覧の多く(進行のルール #12〜#17、投機実装の撤回、設計判断の問い直し)は、ユーザーが
> 手を動かして当たった摩擦が質問・相談を経て教材へ還流した結果 ── 双方向還流ループそのものの
> 記録でもある。

関連(重複させず参照する):

- `textbook/q_a.md` ── 質問・相談ログ Q1〜（保存用アーカイブ・非参照）。「いつ・何を・なぜ相談し、どう決めたか」の一次記録。
- `CLAUDE.md`「### 設計判断・検証知見」── そこから「後の Phase に効く決定・知見」を圧縮した参照用ダイジェスト。
  **本書はこれらの要約 + Q 番号ポインタに徹し、詳細は重複させない**
- `README.md` §19「CL(Curriculum Loop)開発」── 手法の自己定義・メリット・既知の弱点(進行スピード非保証)
- 各 `textbook/Phase-<N>/Phase-<N>-introduction.md` の「後続 Phase での改訂」/「Phase N の成果物」節
  ── 還流ループが実際に書き換えた箇所の一次記録
- 進行のルール #1〜#17(`CLAUDE.md`「### 進行のルール」)
- `textbook/appendix/library-fork-impact.md` ── アーキテクチャの seam 評価(完成後フォークの影響調査)

---

## 1. 課題と対応の一覧(解決済み)

テーマ別 6 グループ(A〜F)。各グループ内は Phase 順。`状態` の語:
`ルール化(#N)` / `是正済み` / `確定` / `撤回` / `YAGNI 確定`。

### A. 教材構成・進行ルール ── 摩擦がルールを生んだ経緯

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| A1 | 共通スキーマをファイル分割したいが、サブパッケージに `__init__.py` は要るか / 置き場は | 0 | 必要(一貫性・ツール予測性・re-export の窓口)。置き場は `schemas/` でなく `domain/`。各コードブロック先頭に配置先パスをコメント明記するルールを新設(Q1) | ルール化(#7) |
| A2 | 教材の章立ての粒度・`samples/` を実 `app/` ツリーの鏡写しにするか | 1 | 作業単位に沿った章立て + 実ツリー鏡写しの samples(絶対 import、overlay で検証)(Q3) | 是正済み |
| A3 | 章番号(`Phase-1-1`…)と作業単位番号(1-1…)が 1 ズレて混乱。概観章と index が重複 | 1 | 章番号 = 作業単位番号に整列。別建て概観章 `Phase-<N>-0` と index を廃し `Phase-<N>-introduction.md` 1 本に統合(Q6 / Q7) | ルール化(#2 / #6) |
| A4 | ある章が、その章で作る全ファイルを解説していない(`solutions/*.py` に触れず) | 1 | 各章冒頭に「この章で新規作成するファイル」を明記し、全ファイルを責務 + 要点で解説。生成後に突き合わせ(Q6) | ルール化(#13) |
| A5 | `samples/` に既存 `decitima-api` ファイルの全文コピーが混在。意図せぬ差分(全角括弧等)を持ち込む | 1 | samples は「その Phase の新規ファイルのみ」。既存への追記は各章の差分として提示。overlay 時に追記を適用(Q4) | 是正済み |
| A6 | 後続 Phase での設計変更が、変更元の以前の Phase 教材に反映されず、読み手が古い記述に従ってしまう | 1 | 変更元に定型マーカーを付す 3 種(A: 後続で設計が変わる / B: サンプルの後追い同期 / C: 旧計画の撤回)。本文・コードは残し差分を注記。全マーカーの一覧は `CLAUDE.md` #12 の grep コマンド(Q5 / Q6) | ルール化(#12) |
| A7 | テストのスタブ・ドライバの関係が写経者に見えず、設計理解に結びつかない | 1 | 各章 `## テスト観点` に SUT / ドライバ / スタブ(テストダブル)を明記。スタブ不要なら理由込みで(Q8) | ルール化(#14) |
| A8 | `registry.py` が後の章で作る `dijkstra.py` を import し、章を写経した時点でテストが赤 | 1 | 前方参照は import ごとコメントアウト + マーカー、参照先を作る章がコメント解除 + 配線テスト。機構テストはフェイクで(Q9)。**Step 2 で機構(コメントアウト + マーカー)は退役、規範(前方 import の禁止)は #15 条項として存続。再発 Phase 7-1(Q41)/ 7-2〜7-4 4 件(Q42)。検出はタグ grep でなく実 import 監査(モジュール + シンボルの誕生章)。見直しは §2.6** | ルール化(#15)/ §2.6 で機構→規範 + 実 import 監査に |
| A9 | 章が作る 3 ファイルのうち 1 つしかその章のテストが import せず、写経漏れを素通し。以前の Phase のテストがリファクタで壊れる | 4 | 「章が新規作成する全ファイルを、その章のテストが少なくとも 1 度は import する」を #15 に追加。以前の Phase のテストの追従(現行版 + 統合スモーク)を #16 に新設(Q30) | ルール化(#15 追加 / #16) |
| A10 | 以前の Phase のコードを共通化のために触ってよいか、明文の基準が無く過剰な自己制約 | 6 | 「後続 Phase の実在の消費者が駆動する共通化は、以前の Phase を触ってでも重複を残さない」。判定は「駆動する消費者は何か」の一問。禁止は本文の全面リライトと動機なき遡及監査のみ(Q38) | ルール化(#17) |
| A11 | 進行ルール #1〜#17 と Notes が肥大化(CLAUDE.md 144K 字、88% が履歴ナラティブ)し、規範がノイズに埋もれて後半ほど解釈ズレが増えた。サンプルも Phase 毎に全文生成で重複 + さかのぼり参照コストが大きい | 横断(MVP 完了時) | **Step 1**: 質問・相談ログを `textbook/q_a.md`(保存用・非参照)へ、Phase 別主要決定 + 検証事象を「### 設計判断・検証知見」1 節へ集約、所感を本ファイルへポインタ化、ルール #1〜#17 を 6 カテゴリに再配置 + 重複短縮 + グレー 4 点の明確化(番号は参照保持のため固定)。**Step 2**: サンプル 7 フォルダ → `textbook/samples/` 1 共有フォルダ(Phase 6 end 状態、冒頭コメントに Phase 系譜)、写経モデルは「end 状態のみ + 章が delta を語る」、ルール #12/#15/#16 を #12 に統合(更新は旧コードのコメントアウト + `# (Phase N-M)` タグ)、検証は共有フォルダの 1 回 overlay(pytest 292 / pyright 0 / tsc・vitest 27・eslint clean)。CLAUDE.md 144K → ~36K(Q39) | Step 1・2 とも完了 |

### B. 三重管理・同期ズレ

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| B1 | 同じ定義が「教材 Markdown / samples / 実コード」の 3 箇所に存在し、変更時に同期ズレ(`probrem.py` の綴り、`AnyConstraint` 未定義、`Field` の import 元ミスが実コード側だけで発生) | 0 | 教材 Markdown は長いコードブロックを持たず「要点抜粋 + `samples/` 参照」。samples を「実装の初期状態 = 単一の真実源」に(#3) | ルール化(#3) |
| B2 | `NumericBoundConstraint` のフィールドが samples(`op`)と実 backend(`operator`)でズレ | 1→2 | 初の実消費者 `check_numeric_bound`(Phase 2)を作るとき samples を `operator` に同期。設計変更でなく後追い同期なので #12 B 種のマーカー(#9) | 是正済み |
| B3 | Phase 5 samples の `test_graph_primitives.py` が Phase 4-1 版を丸ごと置換し、route プリミティブのテスト 11 本(Q30 の dijkstra リファクタ番人を含む)が静かに消失。overlay のフル検証は「件数が減っても緑は緑」で気づけない | 5 | Phase 5 版 = Phase 4-1 の全内容 + network 4 本の現行版に是正。「現行版」ラベルのテストは `diff <過去 Phase 版> <現 Phase 版>` で assertion 削除の有無を必ず見る(Q35 ③)。**Step 2 で共有 1 フォルダになり「現行版で置換」の構図自体が消えた**(1 ファイルに `# (Phase N-M)` タグで追記) | 是正済み / Step 2 で構造的に解消 |
| B4 | metric 式の集約を宣言しつつ、型エイリアス `type Assignment` も巻き込んで移動 → 写経で循環 import(`domain → algorithms` 禁止に抵触) | 6 | 共有型は「両レイヤーが循環なしで import できる最下層」(`domain/solutions/shift_scheduler.py`)に置く。共有シンボルは常に定義元から import(再エクスポート経由は `ruff --fix` で静かに壊れる)。リファクタで「まとめる対象」を宣言したら範囲を厳密に守る(Q38 フォローアップ 2) | 是正済み |

### C. 検証環境

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| C1 | Pylance の `ProblemData` 型式エラー(`app` パッケージを解決できない) | 0 | `decitima-api/backend/pyproject.toml` の `[tool.pyright]` + ルート `.vscode/settings.json` の `extraPaths`。開発環境必須の tooling 設定として明示管理(テンプレート還元候補) | 是正済み |
| C2 | `typeCheckingMode = "standard"` でテンプレート由来コード(`app/ai/**` 等)に既知の型エラー | 0 | 新規コードは standard で厳格、テンプレート債務は `[tool.pyright]` の `ignore` で当面抑制。Phase 11 で解消しテンプレートへ還元 | 継続(Phase 11) |
| C3 | samples が実 `app/` ツリーの鏡写しで単体では import 解決せず、pytest / pyright を回せない。かつ Phase 毎フォルダを N 層スタックして「Phase N end 状態」を再構築する必要があった | 1〜6 | `decitima-api/backend` を複製 + シンボリックリンク `.venv` + samples を overlay してから検証。**Step 2 で共有 1 フォルダ・end 状態になり、スタック再構築は不要 ── 1 回の overlay に**(`textbook/samples/README.md`) | Step 2 で軽減(単体実行は §2.3 で継続検討) |
| C4 | `ruff format` をリポジトリルートから実行すると backend の line-length 100 を拾わず 88 で全面再フォーマット | 4 | 検証コマンドは `--config <backend>/pyproject.toml` を明示。overlay は「ファイルを別の場所に置く」ので config 探索が本来の場所を見失う | 是正済み |
| C5 | 写経先 `test_brute_force_strategy.py` に `test_deterministic_same_input_same_output` が 2 回定義(pyright `reportRedeclaration`) | 4 | pre-existing(Phase 3 写経時の混入)。samples 側は 1 回のみ。写経先の当該関数を消せば解消 | 是正済み(写経先) |
| C6 | `nx.Graph` は平行エッジを持てないが `RouteData` は同ノード対に複数エッジを持てる → seed 依存でテストが落ちる | 4 | `_add_min_edge`(既存があれば軽い方を残す)。最短経路・MST では重い平行辺を使わないので手実装と等価 | 是正済み |

### D. スコープ判断 ── 投機実装の撤回 / Phase 送り / YAGNI

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| D1 | objectives(多目的の重み付き和の評価器)を Phase 1 に投機実装したが、消費者(単一目的の Dijkstra)がおらずテストも無い | 1 | 撤回して Phase 6 送り。初の多目的ストラテジー(Greedy / Backtracking / B&B)が実消費者になったとき `weighted_sum` を実装。「消費者ドリブンで判断する」原則の起点(Q4 / Q14 / Phase 6-1) | 撤回 → Phase 6 で実装 |
| D2 | `network_design` を Phase 1 のユニオンに含めるか | 1 | Phase 1 のユニオンから外す(route / shift の 2 メンバー)。当初 Phase 4 → Q29 で Phase 5 に単独フェーズ化。「新 problem_type を端から端まで足す」の実演教材に(Q29 / Phase 5-3) | 確定(Phase 5) |
| D3 | `verifications` テーブル(検証結果を `Solution.payload` から別テーブルへ切り出す)を作るか | 1〜3 | 作らない。`Solution.status`(カラム)+ `payload`(JSONB)で足り、MVP に payload 内クエリ需要ゼロ。`benchmark_runs` 作成時(Phase 3)に再検討 → 引き続き作らないで確定(Q12 / Q14) | YAGNI 確定 |
| D4 | オラクルのプロパティテストに `hypothesis` を導入するか | 3 | 見送り。手書きジェネレータ + for ループ(seed を振る)で足りた(`Phase-0-9.md` にマーカー。Phase 3-2) | YAGNI 確定 |
| D5 | `bfs_shortest_path` を「全最短経路を返す」形に拡張するか | 1 | 拡張しない。本質は組合せ爆発リスク、かつ DeciTima に全最短経路を要る消費者が無い。決定的タイブレークは安価な代替として記録のみ(Q10) | YAGNI 確定 |
| D6 | Phase 4 が 11 章・ファイル数過多で、他フェーズの倍近い | 4 | Route Planner(8 章)/ Network Designer(5 章)に分割し現 Phase 5〜14 を +1。MVP を Phase 0〜6 に。実装の順序は不変。11 章 Phase は【重点課題】(§2.1)が指すものそのもの(Q29) | 是正済み |

### E. 設計判断の訓練 ──「各層が何のためにあるか」で下す

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| E1 | 問題タイプを `route_planner.py` / `shift_scheduler.py` に分割したが、ユニオンを組むのに相互 import が要る → 統合すべきか | 0 | 分割のまま。`problem.py` が両者を束ねるのは「アグリゲータの役割」で悪い密結合ではない(同型が routes 集約 / `alembic/env.py` / `registry.py`)。基準は「一緒に変わるものを同じファイルに」(Q2) | 確定 |
| E2 | route の到達可能性チェックの置き場所。当初 `validation.py` の private メソッドにインライン | 2 | 「これは計算か? 述語か?」── 到達可能性は BFS を走らせる**計算**なので `route_reachable` を `algorithms/graph/reachability.py` に抽出、hard ゲート**判定**は `services/`、`domain` は不関与。`domain → algorithms` の import 禁止は誤りを写経中に顕在化させる **guardrail** であって理由ではない(Q15 / Phase 2-2 §3) | 是正済み |
| E3 | `BenchmarkRunRepository` を `repositories/benchmark.py` に単独ファイル化。model / schema は `optimization.py` に同居 → 層の対応が不整合 | 3 | 単独ファイル化は「そのファイルを触ると samples の現行版再出荷 + マーカーが要る」という **samples 運用の都合が設計判断に化けた**もの。廃止して `repositories/optimization.py` に同居。data 層(model / schema / repository)= 「永続化の関心事」で 1 ファイル、route / service = 「操作」で割る(Q21 / Phase 3-3 §2.3) | 是正済み |
| E4 | 先頭 `_` 付きの関数・変数は何の慣習か / DTO 型と store の置き場の差は何か | 3 | `_` = PEP 8 の「非公開」+ プロジェクト独自の `metrics["_ops"]`(診断指標の印)。型・スキーマ(契約の語彙)は共有層、振る舞い・状態は feature / 操作で分割(backend と frontend で同じ原則)(Q22 / Q23) | 記録済み(規約に追記) |
| E5 | 経路復元(7 行)が Dijkstra では `_reconstruct` に分離、Bellman-Ford / A* ではインライン複製。`_` 付きで他モジュールから import できず | 4 | ジェネリックと分かっている処理は **1 本目の時点で**公開の共通モジュールへ ── `reconstruct_path` を `segments.py` の公開関数に。**ヘルパの置き場は「2 本目の消費者」で決まる**(Q31) | 是正済み |
| E6 | `solve` 内の `plan_route(...)` 呼び出しが 3 strategy 共通。ラッパーで括るべきか | 4 | 括らない。純粋なパススルーは「名前を変えた `plan_route`」。共通化するのは**機構**(`plan_route` / `reconstruct_path` / `route_solution`)であって**オーケストレーション**(`solve` 本体)ではない。`solve` は「この strategy のレシピ」として直線的に読めるのが目的(Q32) | 確定 |
| E7 | `_negative_cycle_violation` が Bellman-Ford と networkx strategy に同一定義で重複 | 4 | E5 と同型。`negative_cycle_violation` を `segments.py` の公開関数に 1 本化。既に兄弟の `negative_weight_violation` が同じ場所にあった(Q33) | 是正済み |
| E8 | shift の metrics 計算ヘルパ 6 本が `domain/solutions/structure.py` と `algorithms/scheduling/common.py` にほぼ同一で重複。生成時に「Phase 2 と同じ式」と注記までしていた | 6 | 式は domain の事実で、消費者が 2 系統(検証器 + shift strategy 4 本)と生成時点で判明していた。公開 leaf `domain/solutions/shift_metrics.py` に集約し双方が import。「同じ式」と注記した瞬間に「1 箇所に置けないか。駆動する消費者は誰か」を自問する(Q38 / #17) | 是正済み |

### F. 写経の詰まり ── 教材が変更差分を見せていない

| # | 課題 | 発生 Phase | 対応 | 状態 |
| --- | --- | --- | --- | --- |
| F1 | `test_deterministic_same_input_same_output` の `f(x) == f(x)` は自明では? | 1 | テストの意図(`solve` の純粋性 = NFR-1 再現性の機械的な番人。状態蓄積・入力破壊・時刻/乱数で赤になる)が写経者に伝わっていなかった → 教材で言語化(Q11) | 記録済み |
| F2 | `test_solve_api.py` が全滅(`fixture 'api' not found` / 404) | 1 | ① `tests/api/conftest.py` が章の新規ファイルに未列挙 ② `solve_router` の集約が後の章送り(章またぎ前方依存)。→ `solve_router` 集約をその章に移し、テスト用フィクスチャを samples README の作業単位表に列挙(Q13 / #15 のフィクスチャ条項) | 是正済み |
| F3 | `_dijkstra_segment` の写経バグ(末尾の `return ..., pops` を欠いて写す)で `TypeError`。原因の特定に手間取る | 4 | §3.3 が `solve` の before/after しか見せず、実際に変わった `_dijkstra_segment` / `_reconstruct` を見せていなかった。→ 変わった関数本体の before/after を教材に載せる + 章の第一テストに `DijkstraStrategy().solve()` の統合スモーク + docstring に「この失敗 → この行を見る」(Q30 / #16) | 是正済み |
| F4 | `hours_by_staff(data, sol)` と機械的に写して `AttributeError`(シグネチャが `sol` → `assignments: dict` に変わっていた) | 6 | `Phase-6-1.md` §2 が末尾 1 行しか見せず call site の引数変更を隠していた。→ 「変わった行の before → after 表」+「写経の罠」blockquote(この `AttributeError` → `sol` を渡している)+ テスト観点に「6-1 の `test_verification_service.py` が第一の番人」(Q38 フォローアップ 1) | 是正済み |

---

## 2. 継続課題(MVP 後も残る)

### 2.1 進行スピードが担保できない(【重点課題】)

CL 開発は「教材 → 実装 → 摩擦 → 教材改訂」の還流ループを**品質優先**で回す設計で、**時間の次元が
手法に組み込まれていない**。納期の定まった実務プロジェクトには、そのままでは不向き。個人学習でも
所要期間の見積りが立ちにくい。律速と変動要因(`CLAUDE.md` の同名節に詳細):

| # | 原因要素 | 対の提案(すべて未採用・ユーザー判断) |
| --- | --- | --- |
| 1 | 時間の設計が手法に無い(Phase / 作業単位に目安工数・タイムボックスが無い) | **A**: チェックリスト各行に「目安: 写経 N 分 + 理解 M 分」、超過時は深掘りを隔離してまず通す |
| 2 | 二重の学習曲線(ドメイン + 実装スタック)が同時進行。スタック側の摩擦は事前に読めない | **B**: 各章頭に「新しく使う言語 / ライブラリ機能」3 点 + 既知のつまずき FAQ |
| 3 | 還流ループに反復上限が無い(「疑問を出し切ってから実装」は終了条件が開放的) | **C**: WIP 制限 + 前進優先。事前質問は設計判断のみに限定、実装詳細は着手後に即質問 |
| 4 | 写経が律速だが学習価値が不均一(コアと定型を区別せず全部手打ち) | **D**: samples 各ファイルに `写経レベル: コア / 定型` マーカー。納期モードは定型コピー |
| 5 | 生成と実装が直列で待ちが出る。難所は生成して初めて判明(Phase 6 の OR-Tools 追加) | **E**: 生成の先行(別セッションで次 Phase のドラフト)。「今すぐ着手可(依存なし)」を強調 |
| 6 | 完了判定・到達度の基準が無い | **F**: 各 introduction に「Phase 完了チェック」3〜5 問の概念質問(実装前チェックリストと対) |
| 7 | 状態(Notes / ルール)の肥大化でセッション立ち上げが重い | **G**: → §2.2 |
| 8 | 検証環境に一手多い(overlay) | **H**: → §2.3 |

**横断提案 ── 2 モードの明示**: 学習モード(現行。全写経 + テスト値改変 + 事前質問を厚く。速度非保証)
/ 納期モード(速習パス + 定型コピー + テストは実行のみ + 学習は事後レビューで回収。学習効果は落ちる)。
提案 A・D・F があれば同じ教材のまま切り替えられる。

**Claude の推奨(未採用・記録のみ)**: まず A(タイムボックス + 目安工数)/ D(写経レベル)/
C(事前質問を設計判断に限定)。この 3 つで「見積れる・律速を削る・ループを閉じる」が揃う。

### 2.2 `CLAUDE.md` / サンプルの肥大化 ── Step 1・2 で対処済み(Q39)

Notes(質問ログ Q1〜Q38 + Phase 別主要決定 + 検証事象 + 所感)が 144K 字・全体の 88% まで肥大化し、
規範がノイズに埋もれた。サンプルも Phase 毎に全文生成で重複 + さかのぼり参照コストが大きかった。

- **Step 1(提案 G の変形)**: 質問・相談ログは `textbook/q_a.md`(保存用・非参照)へ逐語移設。
  Phase 別主要決定 + 検証事象は `CLAUDE.md`「### 設計判断・検証知見」1 節へ集約(後の Phase に効く分だけ圧縮)。
  所感・重点課題は本ファイルへポインタ化。進行ルールは 6 カテゴリに再配置。
- **Step 2**: サンプル 7 フォルダ → `textbook/samples/` 1 共有フォルダ(Phase 6 end 状態)。写経モデルは
  「end 状態のみ + 章が delta を語る」。ルール #12/#15/#16 を #12 に統合(更新は旧コードのコメントアウト +
  `# (Phase N-M)` タグ)。検証事象から Phase 毎 overlay の記述を削除。
- **CLAUDE.md 144K → ~36K**。overlay は共有フォルダを 1 回重ねて `uv run pytest`(292)/ pyright(0)/
  `npx tsc`・`vitest`(27)・`eslint` clean。

### 2.3 抜粋の追従 / overlay 検証の一手

- 教材の「要点抜粋」は samples の手切り出しで、samples を直したら抜粋も直す必要がある。
  提案(未採用): 抜粋は「シグネチャ + 1〜2 行の核心」に絞る(おおむね実施済み)、さらに
  `samples/<path>:<lineno>` 参照を付けてズレに気づけるようにする。
- samples が実 `app/` ツリーの鏡写しで単体で動かず、overlay 検証(複製 + シンボリックリンク
  `.venv` + rsync)が各サイクルに乗る。**Step 2 で N 層スタックは 1 回の overlay に減った**が、overlay 自体は残る。
  提案 H(未採用): `textbook/samples/` に `conftest.py` + `pyrightconfig.json` を置き overlay 不要にする。

### 2.4 やり直しリスクは 0 にできない / 事前理解のハードル

コーディング着手前にユーザーが設計を理解し疑問を解消しておく必要があるが、学習を兼ねるため
ハードルが高い。実装前チェックリスト(#11)で緩和したが、構造的には残る。

### 2.5 Phase 7 の実測 ── ルール整理(Step 1/2)は生成量を増やしていない

「Step 1/2 の直後に Phase 7 の生成が遅くなった(体感 40 分 → 70 分)」を、セッション記録
(`~/.claude/projects/.../*.jsonl` の `usage` トークン)で検証した。

**結論: ルール整理は生成量を減らしている。遅延の主因は別。**

| 指標 | Phase 6 生成 | Phase 7 生成 |
| --- | --- | --- |
| アクティブなモデル時間 | ~72 分 | ~68 分(≒同じ。体感差はコンパクション中断) |
| 出力トークン / thinking | 422k / 133k | **378k / 107k(−10% / −20%)** |
| 毎ターンの CLAUDE.md | 240K字(~80k tok) | 63K字(~21k tok。**−59k/ターン**) |
| Bash 呼び出し | 80 | **143(+79%)** |
| Phase 着手時の文脈サイズ | ~504k | **~750k** |
| コンパクション | 1 | **強制 1(セッション計 3)** |

**遅延の原因(寄与度順)**:

1. **セッションのスタッキング(最大)** ── 振り返り → ルール分析 → Step 1 → Step 2 → Phase 7 を
   1 セッションで連続実行。Phase 7 着手時点で文脈 750k(75%)、24 分で天井 → 強制コンパクション。
   ルール整理前から同型(Phase 4 セッションもコンパクション 2 回)。
2. **Phase 種別** ── 新 problem_type Phase(3/5/7/9)は ~20 ファイルを端から端で触る。
   アルゴリズム追加 Phase(4/6/8)はスキーマ凍結済みで軽い。Phase 6 は「アルゴリズムを書くだけ」。
3. **検証ループ** ── Step 2 の「end 状態を 1 回でまとめて検証」モデルで、生成中も full overlay
   (338 テスト)を 8〜10 回再実行。部分検証に戻すべき(下記)。
4. **サンプルモデルのコスト移動** ── 旧「新規フォルダを全文生成(出力のみ)」→ 新「蓄積 end 状態を
   Read → マーカー付き Edit」。出力は減るが読みが増える(新 problem_type Phase で顕著)。

**Phase 8 以降の運用調整**:

- **A. 1 Phase = 1 セッション**。着手前に `/clear`。振り返り・ルール整理・大規模リファクタは別セッション。
- **B. 「検証で発覚した事象」は 1 エントリ 3 行以内**(`CLAUDE.md` の同節に明文化済み)。長文は `q_a.md`。
- **C. 新 problem_type Phase は着手時に「触る ~20 ファイル」を実装前チェックリストから確定し一括 Read**。
- **D. 生成中は章ごとの部分 pytest(`pytest tests/unit/test_<章>.py`)、full overlay は Phase 完了時の
  1〜2 回**。`ruff` の scope は `app tests analysis`(`textbook/samples/` 全体は alembic を巻き込む)。
- **E. Step 1/2 は撤回しない** ── 固定オーバーヘッド −59k/ターン・出力 −10% は実測で確認済み。

効果測定: Phase 8 生成後に同じ集計を回し、「開始時文脈 < 150k / コンパクション 0 回 / Bash < 100 回 /
CLAUDE.md < 50K字」を確認する。

### 2.6 写経経路の検証 ── end 状態 overlay は章順の写経を保証しない(Q41 / Q42)

**現象**: Step 2(§1-A A11)で per-Phase folder の「章までのファイルで import 解決・テスト緑」
保証(旧 #15、由来は A8 / `q_a.md` Q9)が退役し、検証は共有 `textbook/samples/` の
**end 状態 overlay 1 回**に集約された。end 状態は常に import 解決するので、章 N を章順に
単体写経したときだけ壊れるケース ──
① 既存共有ファイルへの前方 import(章 N が後続章 M のモジュールを import)、
② その章の新規ファイルの写経漏れ、③ リファクタの写経ミス ──
のうち overlay が捕まえるのは「end 状態でも壊れるもの」だけ。①②③ は end 状態では消えるため、
**実際に章順で回さない限り検出されない**。A8「ルール化(#15)」の解決は A11 Step 2 で
**機構だけ**部分撤回されており、retrospective 内で未整理だった(本節で明示)。

**Phase 7-1 の実例**: `Phase-7-1.md` §2 が `adjacency.py` の module top に 7-3 の葉
`travel_planner.TravelData` の import を足していた。overlay は 338 passed のまま緑、
章順写経だと 7-1 完了時に `adjacency.py` を import する route/network のテスト collection が
全赤。是正 = `build_leg_adjacency`(+ import + テスト 2 本)を最初の消費者の章 7-4 へ移動
(Q41。samples はタグ是正 + テスト移動のみ、`adjacency.py` の end 状態は不変)。

**Q41 が 4 件取りこぼした(Q42)**: Q41 の Phase 7 監査は **`# (Phase 7-N)` タグの grep ベース**
だったため、① 新規ファイルの前方 import(`travel_common.py` / `knapsack.py` / `test_knapsack.py`
── 新規ファイルはヘッダ以外に行タグを持たない)と ②「モジュールはあるが名前が無い」
(`verification.py` の `from …travel_common import all_pairs, tour_cost` ── モジュールは 7-2、
名前は 7-4)を見落とした。とくに `verification.py`(7-3 で編集)は **import-time `ImportError`** で
`solve.py` / `benchmark.py` / 約 8 テストの collection を 7-3 完了時に全崩れさせる。Q42 で
タグ grep を**実 import 監査**(各 `.py` の全 `from app.` 行 × import 先のモジュール **と
シンボル** の誕生章)に置換し、Phase 7-2〜7-5 を全面是正(7-2 = 純粋 `knapsack_2d` のみ、
`travel_common` 全体 + `KnapsackDpTravelStrategy` + `_verify_travel_plan` を 7-4、
`test_travel_common.py` 新設)。章ごとの overlay シミュレーションで 7-1〜7-5 各段の collection
green を確認(7-3: 262 passed、以前は全崩れ)。

**対の提案**(#10。採否はユーザー判断):

| # | 提案 | コスト | 状態 |
| --- | --- | --- | --- |
| 1 | **#15 に前方 import 条項 + 生成後の実 import 監査** ── 「章 N が作る / 触るどのファイルも import 先(モジュール **と** シンボル)がその章までに存在」。生成後に各 `.py` の全 `from app.` を列挙し誕生章と突き合わせる。タグ grep は補助 | 極小(Claude の突き合わせ 1 項目) | **採用済み** ── 初版(Q41)はタグ grep 依存で新規ファイル / シンボル欠落が盲点。Q42 で実 import 監査に強化 |
| 2 | **各 `Phase-<N>-introduction.md` に「写経順序」(依存トポロジカル順)を明記**。章番号順 ≠ 依存順のとき各章冒頭に「写経前提: 章 X, Y を先に」。`Phase-7-3.md` が持つ章内の写経順序リストの Phase 全体版。②(写経漏れ)で「どの章から写経すべきか」を利用者が誤らないようにする | 低(introduction に 1 表) | 採用推奨・未着手 ── Q42 の 5 件で必要性が裏付けられた |
| 3 | **章単位の部分 overlay 再構築**(章 N までのファイルだけを clean tree に重ね `pytest tests/unit/test_<N>.py`)。①②③ を実行時に確実に捕まえる | 高 ── Step 2 が潰した「N 層スタック再構築」が復活(§2.3 / §2.5 item 3、§1-C C3) | **見送り推奨**。#15 現行 +提案 1 + 提案 2 で ①②③ の大半は生成時に捕まえられ、残りは end 状態 overlay 1 回でカバーできるため割に合わない |
| 4 | **Phase 1〜6 の各章に提案 1 の静的チェックを 1 回だけ通す**(Step 2 のフラット化で前方 import が紛れ込んでいないか)。#17(b)「動機なき遡及監査の禁止」との線引き ── 今回は「この再検討」が駆動する実在の消費者なので (b) には当たらない。修正が出ても章 attribution のみ、`samples/` の内容は不変 | 低(静的 grep 1 回) | 任意・未着手。Phase 1〜6 は旧 #15 で緑 by construction だったので、フラット化が前方 import を作らない限り出ないはず ── 確認的作業 |

**A8 のステータス更新**(§1-A の表): 「Step 2 で前方参照の**機構**(コメントアウト + マーカー)は
退役、**規範**(前方 import の禁止 = 章 attribution で守る)は #15 条項として存続。検出は
タグ grep でなく実 import 監査(モジュール + シンボルの誕生章)── Q41 / Q42」。

**#12.2 の拡張(Q42)**: 「1 ファイルを同一 Phase の複数の章で完成させる場合、各章の担当分に
`# (Phase N-M)` タグ + 冒頭コメントに担当章。単一章ファイルは docstring 1 行目に `作業単位 N-M`」。
`# (Phase N-M)` は Phase またぎだけでなく Phase 内の章またぎ著述にも使う(`travel_common.py` に
章 attribution が無かったのが発端)。

---

## 3. 次の判断ポイント(Phase 8 着手前)

- **§2.5 の運用調整 A〜D を Phase 8 で試す** ── 特に A(1 Phase = 1 セッション、`/clear`)。
  Phase 8 は Project Manager(Critical Path / Topological Sort)= アルゴリズム追加型で、
  スキーマ配線が薄いので B/C/D の効果が測りやすい。
- Phase 7 以降を「学習モード」で続けるか「納期モード」を試すか(§2.1)。提案 A(目安工数)/
  C(事前質問を設計判断に限定)/ D(写経レベル)を Phase 8 教材から試験導入するか。
- `library-fork-impact.md` §5 との突き合わせ ── Phase 7 の Floyd-Warshall は **確認済み ──
  手実装の三重ループ(`list`/`dict`)で §8 の前提と整合(Q40)**。numpy 版はフォーク向けメモに留める。

---

## 4. まとめ 1 枚

| 問い | 答え | 参照 |
| --- | --- | --- |
| CL 開発の還流ループは実際に機能したか | した。この一覧の §1-A / §1-E / §1-F はすべて「写経者の摩擦 → 質問 → 教材・ルール改訂」の記録 | §1 |
| 一番効いたルールは | #12(改訂マーカー)と #15 / #16(章の自己完結とテストの追従)。「その Phase の時点では samples のまま実装してよい」と写経者が判断でき、詰まりを教材へ還流する経路が言語化された | A6 / A8 / A9 |
| MVP で撤回した投機実装は | objectives 評価器(Phase 1 → 6)。「駆動する実在の消費者は何か」で判断する原則(#17)の起点 | D1 / E8 |
| 繰り返し現れた設計の問いは | 「これは計算か? 述語か?」「ヘルパの置き場は 2 本目の消費者」「機構 vs オーケストレーション」「samples 運用の都合が設計判断に化けていないか」── 一度言語化すると次の Phase で「型」として使い回せる | E2 / E3 / E5 / E6 |
| MVP 後の最優先課題は | 進行スピード ── 手法に時間の次元が無い。提案 A / C / D、および Notes 分割(G) | §2.1 / §2.2 |
| ルール整理(Step 1/2)は生成を重くしたか | **していない**。実測で出力 −10% / thinking −20% / CLAUDE.md −59k tok/ターン。Phase 7 の遅延はセッションのスタッキング(着手時文脈 750k)と検証ループ激増が主因 | §2.5 |
| 現行の教材・コードに手を入れる必要は | 無い。本書は棚卸しであって改訂ではない(#12 の対象外)。§2.5 は追加の実測分析 | 冒頭 blockquote |
