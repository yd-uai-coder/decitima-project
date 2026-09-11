# 質問・相談ログ（保存用アーカイブ）

> **このファイルは記録・保存専用。教材・サンプル生成の作業中は参照しない。**
> 進行方針にかかわる決定・設計判断は `CLAUDE.md` の
> 「### 設計判断・検証知見」に要約されている（そちらが参照用）。
> ここは「いつ・何を・なぜ相談し、どう決めたか」の一次記録。
>
> 追記のみ。各エントリの形式（進行のルール #8）:
> 1. 疑問が生じた Phase / 2. 質問・相談内容 / 3. 回答と対応方針

---

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


**Q39.（振り返り ── MVP 完了後）進行ルールの競合・重複の整理 / CLAUDE.md スリム化の影響 / サンプル保存方針の変更**

1. **Phase**: 横断（Phase 6 = MVP 完了後）
2. **質問・指示**:
   - (a) 現時点の進行ルール #1〜#17 に競合・重複はあるか。
   - (b) CLAUDE.md を整理し「参照文字数」を減らすと今後の進行にどう影響するか（Phase 7 以降さらに参照が増えるため MVP 区切りで整理したい）。
   - (c) これを踏まえた具体方針: ① サンプルは `textbook/samples/` 1 フォルダを全 Phase 共有（部品ごと 1 ファイル・end 状態・更新は旧コードのコメントアウト + `#(Phase N-M)` 追記・新規は冒頭に生成 Phase）、テンプレート未変更ファイルはサンプル不要 ② 質問・相談ログは `q_a.md` に積み上げ（記録専用・参照しない）、進行方針にかかわる部分は従来どおり「検証で発覚した事象」に記録して後工程で参照、未ルール化部分は先に確定させる。
3. **回答と対応方針**:
   - (a) 明確な競合（矛盾）は無い。重複 7 系統（introduction 規定が #2/#6/#11、マーカー運用が #3/#12、全ファイル突き合わせが #13/#15、Notes 記録先が #4/#8/#10、パッケージ提示が #7/#13、「本文・コードは残す」が #3/#12/#17、CL 定義が 4 箇所）+ 解釈の割れ 4 点（「実装前チェックリスト」が前文 7 点と #11 の別物 2 つ / 実装ファイルを作らない章への #13/#15/#16 除外規定なし / 前文「影響範囲を調査」と #17 のトーン差 / 「samples = 単一の真実源」#3 と「samples にも反映」#9 のフレーミング不一致）。詳細は `textbook/appendix/cl-development-retrospective.md` §1-A A11。
   - (b) CLAUDE.md は毎セッション全文注入（144K 字、88% が履歴ナラティブ、規範は ~12%）。履歴を `textbook/` 側（オンデマンド）へ出せば ① 規範の可視性が上がる（「後半で解釈ズレが増えた」の主因）② 毎セッションのベースラインが軽くなる ③ Phase 15 に向けた線形増加が止まる（今が最も安い）。リスク ── Q ログに未ルール化の耐久的決定が埋まっている → ナラティブだけ外に出し、耐久的決定は「### 設計判断・検証知見」に蒸留して残す。「後の Phase ほど参照ファイル数が多い」は CL 開発の構造的性質でスリム化では解けない（サンプル 1 フォルダ共有が別途これを叩く）。
   - (c) **2 段階で実施**（`~/.claude/plans/` の承認済みプラン）。**Step 1（本エントリ時点で完了）**: Q ログを本ファイルへ逐語移設 / Phase 別主要決定 + 検証事象を「### 設計判断・検証知見」1 節へ集約 + 未ルール化決定のスイープ（`bfs_shortest_path` 単一経路 / MVP は payload 内クエリなし / UI feature を generic 化しない / `weighted_sum` 正規化は Phase 9/10/14）/ ルール #1〜#17 を 6 カテゴリに再配置（番号固定）+ 重複短縮 + グレー 4 点の明確化 / 所感・重点課題を retrospective へポインタ化。CLAUDE.md 144K → ~43K。**Step 2（未着手）**: `textbook/Phase-*/samples/` 7 フォルダ → `textbook/samples/` 1 共有フォルダ、`#(Phase N-M)` インライン履歴、写経モデルは「end 状態のみ + 章が delta を語る」、ルール #12/#15/#16 を 1 ルールに統合。


**Q40.(Phase 7 開始時のスコープ確認)問題モデルの範囲 / Floyd-Warshall の実装方針 / 手実装 strategy の数 / UI**

1. **Phase**: Phase 7(教材生成の開始時。ユーザー「Phase7を開始する」)
2. **質問**: (a) Travel Planner の問題モデルをどこまでやるか(訪問地の選択だけ / 選択 + 訪問順)。(b) Floyd-Warshall を手実装の三重ループにするか、numpy / scipy に寄せるか。(c) 手実装ストラテジーの数(Knapsack DP だけ / DP + Greedy / DP + Greedy + BruteForce オラクル)。(d) decitima-ui の範囲。
3. **回答と対応方針**(すべてユーザーが選択):
   - (a) **選択 + 訪問順(フル)**。Knapsack DP で place の部分集合を選び、Floyd-Warshall で前処理した全点対距離を使って `optimize_waypoint_order` で巡回順を決める。README §19 Phase 7 の「Floyd-Warshall は訪問順最適化の前処理」をそのまま実装。
   - (b) **手実装の三重ループ**(`list`/`dict` ベース、numpy なし)。README §8「コア層に数値ライブラリを入れない」を守る。訪問候補は数十のオーダーで密行列でも O(V³) は一瞬。appendix `library-fork-impact.md` の numpy メモはフォーク向け(retrospective §3 の突き合わせ結論)。`floyd_warshall` は `graph/` の**プリミティブ**(registry 非搭載)── Phase 5 の Union-Find / `connectivity.py` と同じ層。
   - (c) **DP + Greedy + BruteForce オラクル**。`KnapsackDpTravelStrategy`(2 次元 DP 予算×時間、選択のみ ── 移動は前処理後に計上)/ `GreedyTravelStrategy`(効用/追加資源比、1 手ごとに実際の巡回コストで判定)/ `BruteForceTravelStrategy`(部分集合の全列挙、移動込みで真の最適 ── Phase 3/6 と同じ正解オラクルの役割)。`family="optimization"` を再利用(network_design が `"graph"` を再利用したのと同じ。Literal 変更なし)。
   - (d) **フル samples 作業単位**(Phase 3/4/5/6 と同じ。7-7)。`travel-planner/{api,stores,hooks,components}` + ページ + プラン可視化(`TravelPlanCanvas` ── `GraphCanvas` を再利用)。overlay 検証も ui 分。
   - **教材の核**: Knapsack DP は place の cost/duration だけで詰める =「移動費用を無視した上界」。実際に巡回して起点に戻る移動分を足すと予算・時間を超えることがあり、Verification が hard 違反で `invalid` にする。Greedy は移動込みで逐次判定するので必ず valid。この差を 7-6 の `analysis/travel_analysis.py`(`dp_vs_greedy` / `invalid_rate_by_size`)で並べる。
   - **Phase 4 の宿題の回収**: `optimize_waypoint_order` の `_MAX_EXACT`(=8)超えを Phase 4-1 は「与えられた順」で通し明示的に Phase 7 送りにしていた(Q27)。7-4 で最近傍法 + 2-opt の近似に差し替える。シグネチャは不変なので route の 3 strategy は無変更で恩恵。
   - 反映: `textbook/Phase-7/` 一式(introduction + 7-1〜7-7 + samples backend/analysis/ui)、Phase 1-1 / Phase 4-4 / Phase 4-introduction の「後続 Phase での改訂」に travel_planning / 「Phase 7-4 で実装 ✅」の 1 行、`Phase-0-2.md` §8.1 の introduction 改訂節に 1 行、README §19 Phase 7 に詳細リンク、retrospective §3 の「Floyd-Warshall と §8 の整合確認」を「確認済み ── 手実装で整合(Q40)」に、本 Q40 + `CLAUDE.md`「### 設計判断・検証知見」の Phase 7 要点。overlay 検証: Phase 6 end + Phase 7 samples で `uv run pytest` **338 passed / 4 deselected**、ruff / format / pyright(Phase 7 分 0 errors)clean、`alembic` 新テーブルなし、notebook 4 本完走。ui **31 passed** / tsc / eslint clean。


**Q41.(Phase 7 写経中)`Phase-7-1.md` が `adjacency.py` に 7-3 の葉への前方 import を足している / 旧「章内完結」ルールの行方 / 設計手順・実装手順の再検討**

1. **Phase**: Phase 7(7-1 の写経中)
2. **質問・相談**:
   - Phase 7-1 で `adjacency.py` に足す `from app.domain.problems.travel_planner import TravelData` は、introduction によれば 7-3 で作成予定のファイルを指す。「各章のコードはその章とそれ以前の章で完結する」というルールがあったはずだが、ルール整理に巻き込まれて削除されたのか。
   - このような事象が再発しない様、設計手順・実装手順を再検討したい。
3. **回答と対応方針**:
   - **事実**: ユーザーの記憶は正しい。**旧 #15**(コミット `8abb11b` で新設、Q9「registry.py → dijkstra.py の章またぎ前方依存でテストが赤」が発端)に「各章の samples はその章とそれ以前の章で作成したファイルだけで import 解決・テスト緑。集約モジュールの前方参照はコメントアウト + マーカーで出荷し、参照先を作る章がコメント解除 + 配線テスト」があった。**ルール整理で事故的に消えたのではなく**、コミット `18aae96`「MVP完了後進行ルール整理」(2026-09-08、Step 2。Phase 毎 samples 7 フォルダ → 単一 `textbook/samples/` end 状態)に伴い、**この保証機構を意図的に「旧」注記へ格下げ**した(end 状態スナップショットが消え、検証を overlay 1 回に集約したため)。記録は #15/#12 の「旧」注記、`samples/README.md`、retrospective A11/B3/C3/§2.2。
   - **ただし退役に伴い、前方参照を写経者に強制可視化する仕組みが失われた**。現 #15 の「章が作る全ファイルをテストが import」は残るが、検証が end 状態 overlay だけなので**章順に写経する利用者が踏む collection 崩れを検出できない**(end 状態は常に import 解決する)。retrospective A8「ルール化(#15)」は「解決済み」のままだが、A11 Step 2 で機構だけ部分撤回されており未整理だった。
   - **Phase 7-1 の該当箇所**: `adjacency.py` に 7-3 の葉 `travel_planner.TravelData` の module-top import を足し、`test_floyd_warshall.py` も 7-3 の fixture を import。章順写経だと 7-1 完了時に `adjacency.py` を import する route(Dijkstra/BF/A*/BruteForce/reachability)+ network(build_link_adjacency)のテスト collection が全赤。前例 Q34(Phase 5-2 → 5-3)では「素の前方参照 + 注記」は #15 違反と判定され、成果物を依存元が生まれる章へ移すのが確定した対応。Phase 7 で章またぎ前方 import は `adjacency.py` の 1 件のみ(他は `# (Phase 7-3)` / `# (Phase 7-5)` で strategy と同じ章 ── 前方参照でない)。
   - **対応**(ユーザー選択):
     - (a) **`build_leg_adjacency`(+ `adjacency.py` への `TravelData` import + テスト 2 本)を 7-4 の成果物へ再配置**。最初の消費者 `travel_common.all_pairs` が 7-4。7-1 は `floyd_warshall.py` + DP 理論だけの自己完結章に戻る。samples: `test_floyd_warshall.py` を _adj ベース 4 ケースに縮小、`build_leg_adjacency` の 2 ケースを `test_travel_strategies.py`(7-4/7-5)へ移動、`adjacency.py` のインラインタグを `# (Phase 7-1)` → `# (Phase 7-4)` に是正(関数本体・end 状態は不変)。教材: `Phase-7-1.md`(§2 削除・章番号繰り上げ)、`Phase-7-4.md`(`build_leg_adjacency` 節を追加)、`Phase-7-3.md`(adjacency.py を「既存への変更」から削除)、`Phase-7-introduction.md`(章一覧・実装前チェックリスト行 7-1/7-4)。
     - (b) **#15 に前方 import 条項を追加**: 「章が既存の共有ファイルに足す import は {以前の Phase} ∪ {この Phase の章 N まで} で解決すること。後の章で生まれるモジュールへの import を伴う編集は最初の消費者の章へ移す。素の前方参照 + 注記での出荷は認めない」。生成後の突き合わせ(#13 と同一機会)に「新規 `.py` + 既存ファイルへの import 追加行」を列挙し前方 import が無いか確認、を追加。`samples/README.md` の写経モデル節にも 1 行。「旧」注記を「機構は退役、規範(前方 import 禁止)は存続」に整理。
     - (c) **写経経路の検証全体を retrospective §2.6 で見直し**。提案 1(#15 静的チェック ── 採用)/ 提案 2(introduction に「写経順序」トポロジカル順を明記 ── 採用推奨)/ 提案 3(章単位の部分 overlay 再構築 ── Step 2 のコスト復活で見送り推奨)/ 提案 4(Phase 1〜6 に静的チェックを 1 回 ── 任意)。A8 のステータスを「機構退役・規範存続」に更新。
   - **写経先(`decitima-api/backend`)は触らない**(CL 開発の役割分担。写経は本文の是正後にユーザーが実施)。overlay 再検証: `uv run pytest` 338 passed / 4 deselected を維持(テスト 2 関数がファイル間移動しただけ)、加えて「Phase 6 end + 7-1 成果物のみ」で `test_floyd_warshall.py` 4 passed + full collection 緑を確認。


**Q42.(Phase 7 写経中)Q41 の修正が `travel_common.py`(7-2)ほか同型ケースを取りこぼした / なぜか / 全面是正**

1. **疑問が生じた Phase**: Phase 7(7-2 の `travel_common.py::parse_travel_problem` を見て)
2. **質問・相談内容**:
   - `parse_travel_problem(problem) -> tuple[TravelData, ...]` の `TravelData` は 7-3 で作る内容なので、`travel_common.py` は 7-2 で着手すべきでない ── 先の `adjacency.py`(Q41)と同じ事象。Q41 でなぜ改善されなかったか検証する。
   - **追加**: 1 ファイルを複数章で完成させる場合、各章の担当分を `# (Phase N-M)` コメントで知らせるルールだったはず。`travel_common.py` にそれが無い。Phase 7 samples をこの観点でも精査。
3. **回答と対応方針**:
   - **検証結果 ── Phase 7 の前方参照は 5 件、Q41 で直したのは 1 件だけ**:
     ① `travel_common.py`(7-2 新規)の全公開関数が `TravelData`/`TravelSolution`(7-3)依存 + 名前 `all_pairs` 等が 7-4 / ② `knapsack.py`(7-2 新規)が `travel_common` 経由で 7-3 / ③ `test_knapsack.py`(7-2)が `build_travel_problem`(7-3)/ ④ `verification.py`(7-3 編集)の `from …travel_common import all_pairs, tour_cost` ── **モジュールは 7-2 にあるが名前が 7-4** ── これは import-time `ImportError` で `solve.py` / `benchmark.py` / 約 8 テストの collection を 7-3 完了時に全崩れさせる / ⑤ `test_travel_strategies.py`(7-4 初出)が `greedy_travel` / `brute_force_travel`(7-5)を module top で import。
   - **なぜ Q41 で取りこぼしたか(根本原因 3 つ)**: (1) Q41 の監査が `# (Phase 7-N)` タグの grep ベースだった ── 新規ファイルはヘッダ以外に行タグを持たず**構造的に不可視**。(2)「モジュールはあるが名前が存在しない」(④)を見ていなかった。(3) 書いた #15 条項が同じ盲点を継承(「既存共有ファイルへの**編集**」に限定、チェックも「後者の import 先」のみ)+ **条項を書いただけで Phase 7 に実行しなかった**。
   - **対応**(ユーザー選択: Q1 全面 / Q2 条項書き直し + 実 import 監査 / Q3 Phase 1〜6 走査は含めない):
     - (a) **7-1 テンプレを 7-2〜7-5 に全面適用**。7-2 = 純粋 `knapsack_2d` + DP 理論だけ(既存ファイル変更なし・自己完結)。`travel_common.py`(全関数)/ `KnapsackDpTravelStrategy`(`knapsack.py` に追記)/ `verification._verify_travel_plan`(7-3 §5 から移設)を **7-4** へ。`test_travel_common.py` を 7-4 に新設(`build_leg_adjacency` 2 + order/tour 3 + strategy 3 + `_verify_travel_plan` 2)。`test_travel_strategies.py` は素直な 7-5(greedy/brute/registry/select/e2e)。教材は Phase-7-2/3/4/5/introduction を再フレーミング。
     - (b) **#15 の前方 import 条項を書き直し** ── 「章 N が作る / 触るどのファイルも、import 先(**モジュールとシンボル**)がその章までに存在」。新規ファイル・既存追記の別なく。生成後の突き合わせを **実 import 監査**(各 `.py` の全 `from app.` 行 × モジュール + シンボルの誕生章)に置換。タグ grep は補助。`samples/README.md` も更新。
     - (c) **#12.2 を拡張** ── 「1 ファイルを同一 Phase の複数の章で完成させる場合、各章の担当分に `# (Phase N-M)` タグ + 冒頭コメントに担当章。単一章ファイルは docstring 1 行目に `作業単位 N-M`」。`# (Phase N-M)` は Phase またぎだけでなく Phase 内の章またぎ著述にも使う。Phase 7 samples を精査 ── `knapsack.py` に章タグ(`# (Phase 7-4)` on strategy)、`travel_common.py` / `floyd_warshall.py` / `travel_planner.py` ×2 / `greedy_travel.py` / `brute_force_travel.py` / `travel_analysis.py` の docstring に `作業単位 7-N`、`fixtures/optimization.py` の travel セクションに `# (Phase 7-3)`、`test_constraint_checkers.py` の travel テストに `# (Phase 7-3)`。
     - (d) **retrospective §2.6 更新** ── 「Q41 が 4 件取りこぼした」経緯 + 提案 1 のステータスを「実 import 監査に強化」、A8 の表も更新。
   - **写経先は触らない**。overlay 検証: clean overlay `uv run pytest` **340 passed / 4 deselected**(`test_travel_common.py` の `_verify_travel_plan` 2 本が純増、他はファイル間移動)、ruff / format / pyright は変更ファイルすべて clean(`errors.py` の既存債務は samples 対象外)。**章ごとの写経経路シミュレーション**: Phase 6 end に章成果物を順に重ね、7-1 / 7-2 / **7-3(262 passed ── #4 解消の肝)** / 7-4 / 7-5 の各段で full collection green。反証: 7-3 段で新 `verification.py`(travel_common なし)を混ぜると 10 collection errors。


**Q43.(Phase 7 写経中 ── コードレビュー)`constraints/forbidden.py` と `required_inclusion.py` の重複 ── ファイルを分けて重複コードを書くのは設計上合理的か**

1. **疑問が生じた Phase**: Phase 7(7-3 の `constraints/` サンプルを見て)
2. **質問・相談内容**: `app/domain/constraints/` の `forbidden.py` と `required_inclusion.py` はコードの重複箇所が多い。`RouteSolution` のときノードを扱うかエッジを扱うかの違いのみで他は共通している。この 1 箇所の違いのためにファイルを分けて重複コードを記述するのは合理的か。合理的でなければ修正するが、テキストは遡らず Phase 7-3 内で修正項を追加する。
3. **回答と対応方針**:
   - **調査結果 ── 重複は「私設ヘルパ」だけ、`check_*` 本体は重複でない**:
     - 私設ヘルパ `_used_element_ids`(forbidden)/ `_present_element_ids`(required_inclusion)は各 10 行、`isinstance` ディスパッチで**差は route 解の 1 行だけ**(forbidden → `path_edge_ids`、required → `path_node_ids`)。network arm(`selected_link_ids`)/ travel arm(`selected_place_ids`)は**完全に同一**。しかも **Phase 5-3 が network arm を、Phase 7-3 が travel arm を、どちらも両コピーに並行追加**していた(drift ハザードが実測 2 回)。
     - `check_forbidden` / `check_required_inclusion` 本体は「積集合が非空 → 違反 / detail key `forbidden_hit`」vs「差集合が非空 → 違反 / detail key `missing`」で**述語が逆・メッセージ・detail 形が別**。これは重複ではない。
   - **(a) ファイル分割は合理的**。`constraints/` は「1 kind 1 ファイル」(`numeric_bound.py` / `staffing.py` も単独)。2 本を 1 ファイルにマージすると規約に反し得るものが小さい。
   - **(b) 私設ヘルパの重複は合理的でない → 抽出(進行のルール #17)**。「駆動する実在の消費者は何か」= Phase 7-3 自身が両コピーに同一 arm を足している ── 具体名で答えられるので「実施」側。新規 `app/domain/constraints/elements.py` に `solution_element_ids(solution, *, aspect: Literal["nodes","edges"]) -> set[str] | None` を一本化(route の nodes/edges だけ `aspect` で分岐、network/travel は 1 種類なので無視)。`forbidden.py` は `aspect="edges"`、`required_inclusion.py` は `aspect="nodes"` で呼ぶだけに。`check_*` の公開シグネチャ・戻り値・既存テストの assertion は不変。Q38(`shift_metrics.py` 一本化)/ Q33(`negative_cycle_violation` 一本化)と同型。
   - **ユーザー確認**(AskUserQuestion): 解消方針 = 共有ヘルパ抽出 + 2 ファイル維持 / Phase 2 側 = #12.3 の定型ポインタのみ(Phase-2-3.md 本文・コードは触らない)。
   - **#15 / #13 の突き合わせ**: `test_constraint_checkers.py`(現行版)に `from app.domain.constraints.elements import solution_element_ids` を直接足し `test_solution_element_ids_route_aspect_splits_nodes_and_edges` を新設(route 解の nodes/edges 分岐 + shift 解 → `None`)。7-3 が触る 3 ファイル(`elements` / `forbidden` / `required_inclusion`)をこのテストがそれぞれ直接 import。`elements.py` の全 `from app.` 行は 7-3 までに解決(前方 import なし)。
   - **反映**: `textbook/samples/app/domain/constraints/elements.py`(新規)/ `forbidden.py` / `required_inclusion.py`(私設ヘルパ削除 + `elements` import に `# (Phase 7-3)`、docstring に一本化の 1 行)/ `tests/unit/test_constraint_checkers.py`(import + 新テスト 1 本 + docstring)、`Phase-7-3.md`(§5 を共有形に書き換え + #17 blockquote / 章頭ファイル一覧 / 写経順リスト / テスト観点 / ケース表 / §8 まとめ)、`Phase-7-introduction.md`(§2 friction / §4 章一覧 / §9 チェックリスト 7-3 行 / §6・§8 のテスト件数 338→341)、`Phase-7-7.md`・`textbook/samples/README.md`(件数 338→341 ── Q41/Q42 が textbook のみ修正で更新漏れ)、`Phase-2-introduction.md`「後続 Phase での改訂」に [Phase 7-3] 1 行、本 Q43、`CLAUDE.md`「### 設計判断・検証知見」の Phase 7 要点。
   - **overlay 検証**(ov7 ── Phase 6 end + Phase 7 samples): `uv run pytest` **341 passed / 4 deselected**(挙動不変、増分は新ヘルパテスト 1 本のみ)、`ruff check` / `ruff format --check`(`app tests analysis`)clean、`uvx pyright app/domain app/services` **0 errors**。**番人の逆確認**: `elements.py` の route 分岐で `aspect` を無視して `path_node_ids` 固定にすると `test_solution_element_ids_route_aspect_splits_nodes_and_edges` がその場で赤。`errors.py` の ruff format 差分は HEAD 由来の既存債務(samples 対象外)。


**Q44.(Phase 7 写経中 ── テスト失敗の相談)`test_dp_can_overrun_because_it_ignores_travel_cost` が `valid` になる / 原因は**

1. **疑問が生じた Phase**: Phase 7(7-5 の `test_travel_strategies.py` を docker で実行)
2. **質問・相談内容**: `assert dp_verified.status == "invalid"` が `valid` を得て失敗。原因は何か。
3. **回答と対応方針**:
   - **根本原因 ── 写経先の欠落**: `decitima-api/backend/app/domain/solutions/structure.py::structural_verify` が **Route / Shift の 2 arm しかディスパッチしていない**。Phase 5-3 の `NetworkDesignSolution` arm と Phase 7-3 の `TravelSolution` arm が両方欠落。`verify_travel_structure` / `verify_network_structure` 関数自体は写経済みだが**呼ばれない dead code**。→ travel 解は `structural_verify` から `([], {})` が返り、`verify_travel_structure` の `total_cost > data.budget` hard チェックが走らず、DP の「移動費用無視の上界」解が `valid` のまま。ユーザー環境で実測 `budget=5` → total_cost 6.0 / `budget=20` → 23.0 どちらも `verified=valid`(clean samples では両方 `invalid`)。overlay で samples から `TravelSolution` arm を外すと同じ失敗を再現。
   - **副次(原因ではない)**: ユーザーの当該テストは `build_travel_problem(budget=5, time_budget=5)` だが samples・docstring は `budget=20, time_budget=20`(写経タイポ)。samples コードなら `budget=5` でも invalid になるので単独では失敗しない。
   - **ユーザーの写経修正**(Claude は写経先を触らない): `structural_verify` に network / travel の 2 arm を戻す + テストの `budget=5,time_budget=5` → `budget=20,time_budget=20`。`tests/unit/test_network_design.py` も再実行推奨。
   - **samples / 教材の修正(#15 の番人が機能していなかった)**: `structural_verify` の isinstance ディスパッチ arm を**書く章**のテスト(`test_travel_planning.py::test_structural_verify_dispatches_travel`(7-3)/ `test_network_design.py::test_structural_verify_dispatches_network`(5-3))が、**arm が無くても緑**だった ── 前者は `assert isinstance(violations, list)`、後者は良い解を渡して `assert violations == []`。どちらも「戻り値の型・空判定」しか見ておらず、ルーティングが切れていても `([], {})` で通る。→ 両テストを「ルーティング先の violation をアサート」に強化(travel = `budget=3` + `total_cost=50` の手組み解を `structural_verify` 経由で → `any("budget" in v.message ...)`、network = `total_weight` をズラした解 → `any(v.constraint_kind == "network_structure" ...)`)。ユーザー確認(AskUserQuestion)= travel + network 両方強化。
   - **教訓**: **isinstance ディスパッチ arm の番人テストは、arm 未接続で赤になる形(ルーティング先の violation をアサート)でなければ #15 の穴**。`test_..._dispatches_...` という名前でも、戻り値の型・空リストしか見ないなら番人にならない。Q30(`test_graph_primitives` の写経漏れ検知不能)/ Q38(`shift_metrics` の引数変更が 6-3 まで持ち越し)と同型 ── 章の配線を章のテストがその場で突く。
   - **反映**: `textbook/samples/tests/unit/test_travel_planning.py` / `test_network_design.py`(各 1 テスト強化)、`textbook/q_a.md` 本 Q44、`CLAUDE.md`「### 設計判断・検証知見」の「#### 検証で発覚した事象」、`Phase-5-3.md` / `Phase-7-3.md` の §テスト観点に 1 行。overlay 検証(ov7): `uv run pytest` **343 passed / 4 deselected**(件数不変 ── アサート強化のみ)、ruff / format / pyright clean。**番人の逆確認**: `structural_verify` から travel arm を外すと `test_structural_verify_dispatches_travel` が赤、network arm を外すと `test_structural_verify_dispatches_network` が赤(いずれも従来は緑)。


**Q45.(Phase 8 開始時のスコープ確認)工程管理の資源の扱い / トポロジカルソートの実装 / UI・analysis の範囲**

1. **疑問が生じた Phase**: Phase 8 kickoff（「Phase8を開始する」）
2. **質問・相談内容**: README の Phase 8 節は他 Phase より簡素で、`problem_type` 文字列・スキーマ形・産業ソルバーの有無を明記していない。設計討議として (a) スコープ（CPM のみ / CPM + 資源平準化 / フル RCPSP + CP-SAT）(b) トポロジカルソートの実装（DFS ベース / Kahn 法 / 両方）(c) decitima-ui と analysis トラックの範囲。
3. **回答と対応方針**（ユーザーが AskUserQuestion で選択）:
   - **(a) フル RCPSP + CP-SAT**。`project_scheduling` を 5 つ目の problem_type に。手実装 `cpm`（資源無視 = makespan の下界）/ `priority_list`（余裕の少ない順の貪欲 SGS = 資源 feasible だが最適でないことがある）+ 産業ソルバー `cp_sat`（OR-Tools、`add_cumulative` で厳密 RCPSP）+ `cpm_nx`（networkx、非制約 CPM の別実装オラクル）。fixture では cpm=8（invalid）/ priority_list=10 / cp_sat=9。**Phase 6 の「手実装ヒューリスティックが破綻 → CP-SAT」を工程管理で再演**し、**Phase 7 の「Knapsack DP は移動費用を無視した上界」と対（cpm は資源を無視した下界）**になる教材構造。
   - **(b) DFS ベース**（README「Phase 1 の DFS が Topological Sort の土台」に忠実）。後行順の反転 + gray/black で back edge = 閉路検出。理論章（8-1 §2）で Kahn 法（入次数 BFS）を markdown で対比（サンプル関数は作らない）。出力は「辞書順」ではない点を明記。
   - **(c) UI スライスのみ**。`project-planner` フィーチャースライス（Phase 4-8 / 7-7 と同型）+ 新規 `GanttCanvas`（`components/ui/charts/` のドメイン非依存チャート。`GraphCanvas` と並ぶ）。依存 DAG は `GraphCanvas` 再利用。**analysis トラック（`project_analysis.py` + notebook）は後続 Phase 送り**（retrospective §3 の「Phase 8 で B/C/D の効果が測りやすい」に沿ってスコープを絞る）。
   - **確定した設計判断**（詳細は `Phase-8-introduction.md` §9）:
     - problem_type 名 = `project_scheduling`（route_planning / shift_scheduling / travel_planning と同じ noun+gerund）。
     - 依存はエッジリスト `TaskDependency(id, predecessor, successor)`（finish-to-start。RouteEdge / NetworkLink と同型で id 付き）。
     - 時間モデル = 整数時間単位（`duration: int > 0`、t=0 起点）。imos の資源グリッドが綺麗に回る。「完了予定日」は UI 側で `start_date + makespan`。domain / algorithms は日付を持たない。小数の所要時間は非スコープ。
     - **循環検出は「計算」**なので `algorithms/graph/topological.py`（`has_cycle` / `topological_sort` が raise）に置き、`services/validation.py` が呼ぶ（network の `all_nodes_connected` と同じ切り分け。`Phase-2-2.md` §3「計算か述語か」の **4 例目**）。閉路時は `InfeasibleProblemError`。`ProjectData.model_validator` は端点実在・id 一意・自己依存禁止のみ（走査しない）。
     - CPM プリミティブ（`scheduling/critical_path.py`）は generic dict（`durations` / `successors`）を取り、`ProjectData`（8-3）に依存しない ── 8-2 が 8-3 に前方依存しないため（`floyd_warshall` / `knapsack_2d` と同じ設計。進行のルール #15）。同様に `topological_sort`（8-1）も生の隣接だけ。
     - 資源制約 severity = **hard**（travel の予算超過と同じ）。cpm の出力が資源超過なら verification が `status=invalid`、priority_list / cp_sat は valid。
     - **Difference Array**（Phase 6 `patterns/difference_array.py::range_add`）を **無変更で再利用**（2 人目の消費者 ── `project_common.resource_profile`）。Phase 6 の `on_duty_by_hour` と全く同じ形。
     - forbidden / required_inclusion は **非該当**（project 解は全タスク実施）── `constraints/elements.py` は変更不要（未知の解型 → `None` → チェッカー素通し）。deadline は既存 `check_numeric_bound` が `metrics["makespan"]` を読んで動く（新チェッカー不要）。
     - objectives = `makespan`（minimize）/ `peak_resource`（minimize）。スケール差の注意は既存 Notes どおり、正規化は見送り。
     - `AlgorithmMeta.family` = `"scheduling"` を 4 strategy 全部で再利用（Literal 変更なし。travel が `"optimization"` を再利用したのと同じ）。
     - クリティカルパス復元は複数あるとき単一を返す（タイブレーク = 後続 id 昇順。`bfs_shortest_path` の単一経路方針と同じ）。networkx オラクルとは「slack 0 のタスク集合」で突き合わせ + chain も一致確認。
     - `GanttCanvas` は `src/components/ui/charts/`（ドメイン非依存。`{id, label, start, end, slack?, highlight?}[]` を取る）── テンプレート還元候補。
   - **章立て**（厳密な鎖 8-1→…→8-6、8-7 は Phase 4-8 依存）: 8-1 topological_sort（DFS）+ 理論 / 8-2 CPM プリミティブ / 8-3 problem_type 配線 + 閉路ゲート / 8-4 資源プロファイル（imos）+ cpm / priority_list / 8-5 CP-SAT RCPSP / 8-6 registry + select + cpm_nx + e2e / 8-7 Project Manager ページ + GanttCanvas。
   - **前方 import 監査**（進行のルール #15、Q41 / Q42 の再発防止）: 実 import ×（モジュール + シンボル）誕生章で確認。8-1 `topological.py` → `adjacency.Adjacency`（Phase 4）のみ / 8-2 `critical_path.py` → `topological_sort`（8-1）のみ、`ProjectData` を import しない / 8-3 の葉は純粋 Pydantic、`structure`/`semantic`/`validation` の arm は `ProjectData`（8-3 同一章）+ `has_cycle`（8-1）/ 8-4 `verification.py` の編集は `project_common`（8-4 同一章）→ 前方でない / 8-6 `registry.py` は cpm/priority_list（8-4）+ ortools_project（8-5）+ networkx_project（8-6 同一章）── 全て 8-6 時点で存在。**前方 import なし**。章順写経シミュレーション（8-3 / 8-4 / 8-5 各状態）で該当章のテストが green を確認。
   - **番人テスト**（Q44 の教訓）: 8-3 `test_structural_verify_dispatches_project`（`finish != start + duration` の解を `structural_verify` 経由 → `project_structure` violation をアサート。arm を外すと赤 ── overlay で逆確認済み）/ 8-4 `test_cpm_ignores_resources_and_verification_marks_it_invalid`（`_verify_project_resources` を連結から外すと赤）/ 8-2 第一テスト = 統合スモーク（`cpm` を既知 DAG で 1 回、makespan / critical_path をアサート）。
   - **反映**: `textbook/Phase-8/` 一式（introduction + `Phase-8-1`〜`8-7`）、`textbook/samples/` の Phase 8 分（backend 12 新規ファイル + 8 編集、ui 8 新規 + 2 編集）、`Phase-1-1.md` §5 / `Phase-0-2.md` §8 表 / `Phase-2-introduction.md`「後続 Phase での改訂」に [Phase 8-3] / `Phase-6-introduction.md` に「後続 Phase での改訂」節新設（[Phase 8-4/5/6]）、`textbook/samples/README.md` の最終検証スタンプ（343→405 / 31→35）、`CLAUDE.md`「### 設計判断・検証知見」の Phase 8 要点。
   - **overlay 検証**（ov8 ── Phase 7 end + Phase 8 samples）: `uv run pytest` **405 passed / 4 deselected**（+62 ── Phase 8 の primitives / domain / strategy / e2e）、`ruff check` / `ruff format --check`（`app tests analysis`）── Phase 8 分 clean（`errors.py` の既存債務は samples 対象外）、`uvx pyright`（Phase 8 の変更ファイル）**0 errors**、`alembic upgrade head` **no-op**（新テーブルなし）。decitima-ui: `npx tsc --noEmit` clean、`npx vitest run`（`features/optimization` + `components/{auth,ui/charts}`）**35 passed**（+4 ── project-planner store）、`npx eslint` clean。**番人の逆確認**: `structure.py` の project arm を外すと `test_structural_verify_dispatches_project` が赤 / `verification.py` の `_verify_project_resources` を外すと資源番人テストが赤。


**Q46.(Phase 8 生成後 ── 設計判断の確認)トポロジカルソートを DFS ベースにした理由 ── Kahn 法の方が工程管理の直感に近いのでは**

1. **疑問が生じた Phase**: Phase 8（`Phase-8-1.md` §2 の DFS vs Kahn 対比表を見て）
2. **質問・相談内容**: 8-1 §2 で Kahn 法（入次数ベース）を「『今すぐ着手できるタスクのキュー』── 工程管理の実務感覚に近い」と紹介しているのに、なぜ DFS ベースを推奨したのか。
3. **回答と対応方針**:
   - **「推奨」は技術的優位というより README 準拠 + 教材の連続性が主な理由**（正直グレー）:
     - README §19 が「**Phase 1 の DFS が Topological Sort の土台になる**」と名指し。CL 開発は README を設計の出発点にする（CLAUDE.md 前文）。
     - Phase 1 で `search/dfs.py`（`dfs_preorder` / `dfs_has_path`）を実装済み。DFS 版は「2 状態 `visited` → 3 色（白/灰/黒）に拡張し、帰りがけに積んで反転」という**既習アルゴリズムの発展**として提示できる。Kahn 法は「入次数」という新概念の導入になる。
     - 3 色による閉路検出（back edge = 灰へ戻る辺）は CLRS 22 章の中心的題材で教材価値がある。
     - AskUserQuestion（Q45）で「DFS ベース（推奨）」が選ばれた。
   - **Kahn 法の技術的な利点**（8-1 §2 で認めている）:
     - **CPM との相性** ── 「入次数 0 = 今すぐ着手可能」を剥がす順序は CPM の前進パス（ES/EF）がまさに必要とする順。前進パスと融合して書ける（DFS は全走査後にしか順が出ない）。
     - **再帰上限** ── 反復（キュー）なので依存が一直線に数百タスク続いても平気。DFS は再帰深さ = 最長パス長で、Python の既定再帰上限（1000）に当たり得る。
     - **閉路検出の説明** ── 「出力数 < V」は「一部のタスクが永遠に着手可能にならない」と直感的。
     - **出力順** ── ソート済みキューなら辞書順。DFS 版は「先に潜った枝が末尾」で辞書順にならず、テスト（`test_deterministic_neighbour_order` が `["A","C","B"]` をアサート）で説明が要る。
   - **総合**: 依存 DAG の規模が大きくなる工程管理では**技術的には Kahn 法（反復・CPM と融合可能・辞書順）の方が適する**。DFS を選んだのは教材上の判断で、そこはグレー。
   - **ユーザー方針**: **一旦は DFS 推奨どおり DFS ベースで進める**。プロジェクト（Phase 15）完成後に Kahn 法ベースへの置換を行うか検討する。**教材・サンプルは DFS 版のまま変更しない**。置換する場合の変更範囲 = `topological.py` + `test_topological_sort.py` + `Phase-8-1.md` §1/§2 の小変更（`has_cycle` / `successors_from_edges` の公開シグネチャは不変にできる）。
   - **反映**: 本 Q46、`CLAUDE.md`「### 設計判断・検証知見」の「#### 未ルール化の確定事項」に 1 行（Kahn 置換は完成後の検討課題）、`Phase-8-1.md` §2 末尾に課題ポインタ blockquote（教材本文の構成変更なので #12 マーカー不要）。コード変更なし・overlay 再検証なし。


**Q47.(Phase 8 生成後 ── コードレビュー)`priority_list.py::solve` の `build_durations` 二重呼び出し**

1. **疑問が生じた Phase**: Phase 8(`priority_list.py` を読んで)
2. **質問・相談内容**: `solve()` が `build_durations(data)` を try 内の inline 呼び出しと try 後の `dur = build_durations(data)` の 2 回呼んでいる。`ortools_project.py` は先に `dur` を束ねてから `cpm(dur, ...)` に渡す構成になっており、記述順がおかしいのでは。
3. **回答と対応方針**: 指摘のとおり。`dur = build_durations(data)` を try の**前**に移し、`cpm(dur, successors)` で束ねた `dur` を再利用するよう修正(`ortools_project.py` と同じ構成に統一)。`build_durations` は純粋なタスク→所要時間の辞書内包表記なので、呼び出し回数が変わっても挙動は不変(進行のルール #9 のとおり反映後に実行確認)。反映: `textbook/samples/app/algorithms/scheduling/priority_list.py`、`Phase-8-4.md` §3 のコード抜粋、本 Q47。overlay 検証: `uv run pytest tests/unit/{test_cpm_strategy,test_project_strategies,test_cpsat_project}.py` **23 passed**、`uvx pyright app/algorithms/scheduling/priority_list.py` **0 errors**、ruff check / format clean。
