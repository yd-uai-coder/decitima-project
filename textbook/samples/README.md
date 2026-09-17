# textbook/samples ── 実装の初期状態（単一の真実源・全 Phase 共有）

`decitima-api/backend/` と `decitima-ui/` に重ねる前提の実装スケッチ。進行のルール #3 のとおり、
教材本文（`textbook/Phase-<N>/Phase-<N>-<M>.md`）は要点の抜粋だけ、動くコードはここ。

**このフォルダは 1 つ・全 Phase で共有する**（旧方式: Phase 毎に `Phase-<N>/samples/` を全文生成していた）。各ファイルは
**最新 Phase の end 状態**（現在 = Phase 9 end）。ファイル冒頭のコメントに Phase の系譜を書く:

```
# DeciTima samples │ Phase 4              ← Phase 4 でのみ作成・変更
# DeciTima samples │ 初出 Phase 1 │ 改訂 Phase 4,6   ← Phase 1 で作成、4 と 6 で変更
# DeciTima samples │ Phase 7(7-2: knapsack_2d / 7-4: KnapsackDpTravelStrategy)  ← 1 Phase 内で章をまたぐ
```
単一章で完結する新規ファイルはモジュール docstring 1 行目に `作業単位 <N>-<M>`(テストと同じ)。

## 写経モデル ── end 状態のみ + 章が delta を語る

- サンプルは常に完成形。「Phase 3 の時点のスナップショット」は無い。
- 各 `Phase-<N>-introduction.md` の実装前チェックリストと各章冒頭の「この章で作成 / 更新するファイル」が
  「この Phase で何を写経するか」を案内し、章本文が「この Phase の変更行」を説明する。
- 章単位の孤立テスト実行はしない（検証は end 状態でまとめて回す）。
- 章 N が作る / 触るどのファイルも、import 先（モジュール **と** そのシンボル）がその章までに
  存在すること。新規ファイル・既存追記の別なく。end 状態では常に解決するので、写経を章順に進める
  利用者だけが前方 import を踏む（`from x import foo` で `x` はあるが `foo` が後の章、も前方 import。
  後の章で生まれるものへの import を含むファイル / 関数 / クラスは最初の消費者の章へ寄せる ── #15）。
- **Phase 7 以降の更新**は「旧コードをコメントアウト + 新コードを `# (Phase N-M)` タグ付きで追記」
  （進行のルール #12。`#` の後にスペース 1 個 ── `ruff format` が正規化する）。
  新規ファイルは冒頭コメントに生成 Phase。

```python
def score(...):
    # (Phase 6-3)
    # return weighted_sum(objectives, metrics)
    # (Phase 9-2) 正規化を挟む
    return weighted_sum(objectives, normalize(metrics, ranges))
```

## ディレクトリ対応

| samples 内 | 写経先 |
| --- | --- |
| `app/**` | `decitima-api/backend/app/**` |
| `alembic/**` | `decitima-api/backend/alembic/**` |
| `analysis/**` | `decitima-api/backend/analysis/**` |
| `scripts/**` | `decitima-api/backend/scripts/**` |
| `tests/**` | `decitima-api/backend/tests/**` |
| `pyproject.toml` | `decitima-api/backend/pyproject.toml`（DeciTima が足した依存・ruff 設定のみ差分で写す） |
| `ui/src/**` | `decitima-ui/src/**` |

Phase 0 の設計スケッチ（`textbook/Phase-0/samples/` の 4 ファイル ── `problem_schema.py` 等の
フラットなスケッチ）は実装前の設計フェーズの成果物で、この共有フォルダとは別。整理の正はここ。

## 検証（overlay ── 1 回）

> **生成中は章ごとの部分実行**（`uv run pytest tests/unit/test_<当該章>.py`）で回し、下記の
> full overlay（343 テスト）は **Phase 完了時の 1〜2 回だけ**。`ruff` の scope は必ず
> `app tests analysis`（`textbook/samples/` 全体は `alembic/versions/*.py` を巻き込む）。
> 理由は `cl-development-retrospective.md` §2.5。

### backend

```bash
# clean base（decitima-api/backend HEAD）
git -C decitima-api archive HEAD backend | tar -x -C <work>
ln -s "$(pwd)/decitima-api/backend/.venv" <work>/.venv

# 共有 samples を 1 回重ねる（--delete は付けない ── テンプレート由来ファイルを消さない）
rsync -a textbook/samples/{app,tests,analysis,alembic,scripts}/ <work>/…/
cp textbook/samples/pyproject.toml <work>/pyproject.toml

# Phase 11 のみ: Web検索QA機能の廃止に伴い削除するファイル(rsync は既存ファイルを消さない
# ため、overlay では手動で rm する。実リポジトリでも同じ3ファイルを削除する ── Phase-11-7.md)
rm -f <work>/app/ai/tools/tavily.py <work>/app/services/chat.py <work>/app/api/routes/chat.py
uv pip install --python <work>/.venv/bin/python 'pandas>=2.2' 'matplotlib>=3.9'   # analysis 用
uv pip install --python <work>/.venv/bin/python 'pulp>=2.9' 'arq>=0.26'   # Phase 9（MILP / ジョブキュー）

cd <work>
uv run pytest                                              # 481 passed / 5 deselected
uv run ruff check  --config <backend>/pyproject.toml app tests analysis   # samples は clean
uv run ruff format --check --config <backend>/pyproject.toml app tests analysis
uvx pyright app tests                                      # 0 errors
DATABASE_URL=sqlite+aiosqlite:///./_ov.db REDIS_URL=redis://x JWT_SECRET_KEY=x \
  uv run alembic upgrade head                              # 2b97… → c65b… → d4f1…（jobs テーブルは
  # 新規 migration をユーザー側で `alembic revision --autogenerate` して足す。Phase 9-8 参照）
PYTHONPATH=$PWD uv run --with jupyter --with nbconvert --with ipykernel \
  jupyter nbconvert --to notebook --execute analysis/notebooks/*.ipynb   # 4 本完走
```

### ui

```bash
git -C decitima-ui archive HEAD | tar -x -C <work-ui>
ln -s "$(pwd)/decitima-ui/node_modules" <work-ui>/node_modules
rsync -a textbook/samples/ui/src/ <work-ui>/src/

cd <work-ui>
npx tsc --noEmit                                           # clean
npx vitest run src/features/optimization src/features/structuring src/components/auth \
  src/components/ui/charts                                 # 64 passed(Phase 11。features/structuring 新設)
npx eslint src/features/optimization src/features/structuring src/components/auth \
  src/components/ui/charts \
  'src/app/(pages)/optimization' 'src/app/(pages)/login' src/lib/api/types.ts src/lib/menu-tree.ts   # clean
```

（`alembic/versions/*.py` は backend の ruff `extend-exclude` 対象なので lint しない。
`decitima-api/backend` HEAD 自体の pre-existing lint 債務 ── `app/services/errors.py` 等 ──
は samples の対象外。`src/components/layout/Menu.test.tsx` の既存失敗も Phase 3 以前からのテンプレート rot。
`useJobPolling`（Phase 9-9）のテストはフェイクタイマー環境で `waitFor` がデッドロックするため
`vi.advanceTimersByTimeAsync` を `act()` で包む ── `Phase-9-9.md` §テスト観点参照。）

最終検証: 2026-09-17（Phase 13 ── Result Explanation）: README §13「Result Explanation」を
実装 ── 永続化済みの `Solution` を id 指定し、`produced_by`/`metrics`/`violations` を LLM に
narrate させる新エンドポイント `POST /api/v1/solutions/{solution_id}/explain`(既存
`routes/solutions.py` に追記、`OptimizationReadService.get_solution`/`get_problem` を
第三の消費者として無変更で再利用)。**「他候補との違い」は他アルゴリズムを再 solve しない**
── Phase 12 の `_ALGORITHM_DESCRIPTIONS` を `problem_type` でフィルタするだけで比較材料を
揃える。この帰結として同定数(Phase 12 では非公開)が2人目の消費者を得たため
`app/domain/problems/algorithm_catalog.py` へ抽出し `ALGORITHM_DESCRIPTIONS`/
`describe_algorithm`(公開)に改名(進行のルール #17、Phase 12 側は import に置き換えるだけ
── 既存 `test_algorithm_recommendation_service.py` は無改造のまま緑)。**LangGraph は使わない**
(DB読み取り1回+LLM呼び出し高々1回の単純な流れ、Phase 12 と同じ判断)。LLM 呼び出し失敗は
Phase 12(ルールのみで返す)と異なり、`metrics`/`violations` を直接文字列化した機械的な要約に
フォールバックする(Result Explanation は narrate すること自体が価値のため。`logger.warning`
は必ず残す)。永続化しない(新テーブル無し、ステートレス)。UI は各 Planner Panel の既存
「解く」が `persist: false` のため explain がそのまま呼べない ── `ExplanationCard` 専用の
永続化つき `persistSolve`(`features/optimization/api/solve.ts`、新規・別ファイル)を用意し、
押下時に solve(persist: true)→ explain の2段階を store 内部で完結させ、既存「解く」ボタンの
挙動には一切触れずに解決した。
backend **602 passed**(新規 unit 10(catalog 3 + schema 2 + service 5)+ api 3)、`ruff check` /
`ruff format --check` / `uvx pyright`(`.venv` を指す)0 件(`app/services/errors.py` の
pre-existing 債務は対象外)。ui vitest **77 passed**、既存回帰なし(`Menu.test.tsx` の
1件失敗は Phase 12 以前からの既存事象)。`npx tsc --noEmit` / `npx eslint` clean。
alembic は既存 no-op のまま(新テーブル無し)。

前回(2026-09-14、Phase 11 ── LLM Problem Structuring)。README「LLM に最適解を計算させない」
を実装 ── 自然言語 → LLM(Gemini、既存 `app/ai/` 資産を全面作り替え)→ Structured Problem
(`OptimizationProblem`)→ Validation。**グラフ構造ドメイン(route/network/project/logistics)の
非対称性への対処**: LLM が埋めてよいのは objectives/constraints/data のトップレベル・スカラー
までとし、ノード/エッジ/タスクのカタログは `app/domain/problems/base_problems.py`(6ドメイン分の
ベース問題、新規)から常に引き継ぐ。機構は Phase 10 `apply_overrides` を**第二の消費者**として
再利用(`base_problem + LLM抽出パッチ → apply_overrides → Validation`)。**グラウンディング検査
を新設**(`ground_references`)── 既存 `ProblemValidationService` は id 参照の実在性を検査しない
ため、LLM のハルシネーション(存在しない id の参照)を弾く最後の砦として追加(新しい例外
クラスは増やさず既存 `ProblemValidationError` を再利用)。LangGraph ワークフローは
`classify_problem_type → load_base_problem → extract_objectives_constraints →
extract_domain_data(EXTRACTORS レジストリでドメイン別ディスパッチ。network_design は
LLM を呼ばない)→ assemble_problem → validate_problem` の一直線パイプライン。
**既存の Web検索QAチャットワークフロー(Tavily)は全面廃止**(`app/ai/tools/tavily.py`・
`app/services/chat.py`・`app/api/routes/chat.py`・`app/schemas/generation.py` を削除。
`Conversation`/`Message` モデル・`ConversationRepository` は無改造のまま Phase 11 で初めて
実消費者を得る)。既知の型債務(`app/ai/**`・関連テストの pyright ignore)を解消(`pyproject.toml`
の ignore リストから削除)。`POST /api/v1/structure` を新設、返る `problem` はそのまま
`POST /api/v1/solve` に渡せる。UI は README §11 の Human-in-the-loop を実演 ── 新規
`features/structuring/`(自然言語入力 → 確認カード → 確定)+ 共有
`features/optimization/stores/pending-problem-store.ts`/`hooks/usePendingProblemHydration.ts`
で既存6ドメインページへ1行ずつ配線(新しい solve ビューアは作らず既存資産を再利用)。
**overlay の特記事項**: rsync は既存ファイルを消さないため、Web検索QA機能の廃止で削除される
3ファイル(`app/ai/tools/tavily.py`・`app/services/chat.py`・`app/api/routes/chat.py`)は
overlay 手順に `rm` を追加した(実リポジトリでも同じ3ファイルを削除する。他 Phase には無い
初めてのケース)。
backend **576 passed / 6 deselected**、`ruff` / `uvx pyright app tests`(0 errors、ignore
リストから `app/ai` と `test_ai_graph_nodes.py` を削除)clean。ui **64 passed**(スコープ:
`src/features/optimization` + 新設 `src/features/structuring`)、`npx tsc --noEmit` /
`npx eslint` clean。alembic は既存 no-op のまま(新テーブル無し、`Conversation`/`Message`
は既存テーブルを再利用)。

前回（2026-09-13、Phase 10 ── What-if Simulation）: 新しい problem_type やドメイン
アルゴリズムは追加せず、Phase 4〜9 の6ドメインを横断する意思決定支援層として実装。
`apply_overrides`(RFC 7386 JSON Merge Patch 相当 + Pydantic 再検証。ドメイン別コード無し)/
`SimulationService.run_simulation`(Phase 3 `BenchmarkService` と対称。永続化を持たない
素の async 関数)/ `find_threshold`(二分探索の応用、「答えを二分探索する」)。**新テーブルは
作らず Phase 9-8 の `jobs` テーブル・ジョブキューを再利用**(`POST /api/v1/simulate` を新設、
結果のポーリングは既存 `GET /api/v1/jobs/{id}` をそのまま再利用)。**Phase 9 への改訂 1 件**:
`JobStatusResponse.result` を `CandidateSolution | SimulationResult | None` に広げた(両型の
必須フィールドが重ならないため discriminator タグ不要、`solve_job` の実装・既存 e2e テストは
無改造)。分析トラック `simulation_analysis.py` + UI `simulation` スライス(シナリオ JSON
エディタ + 比較表、`useJobPolling` を無変更で再利用)。
backend **508 passed / 6 deselected**（overlay は `git archive` でクリーンな一時ディレクトリを
作って実施。`ruff` / `uvx pyright app tests`(0 errors)clean。integration 1 件追加(`simulate_job`
の e2e、`-m integration` は環境上未実行 ── 既存 `solve_job` の e2e も同条件で未実行、退行では
ない)/ ui **51 passed**（スコープ: `src/features/optimization` 配下 + `simulation` の新規追加分。
`npx tsc --noEmit` / `npx eslint` clean）/ alembic は既存 no-op のまま(新テーブル無し)。

前回（2026-09-11、Phase 9 ── Logistics Optimizer）: `logistics_planning` を 6 つ目の
problem_type に配線(CVRP。複数車両・容量制約)。手実装 4 strategy(knapsack_dp / greedy /
branch_and_bound / brute_force)+ 産業ソルバー `pulp_milp`(PuLP、使用台数最小化のビンパッキング
MILP)。**ジョブキュー基盤(`arq`)を新規導入**(problem_type 非依存の横断インフラ、
`POST /api/v1/jobs` が既存の同期 `POST /solve` と併存。`jobs` テーブルが初めて alembic に
実テーブルを増やす)。UI に `logistics-planner` スライス。
backend 481 passed / 5 deselected / ui 142 passed(pre-existing の `Menu.test.tsx` 1 件除く)。

さらに前回（2026-09-10、Phase 8 ── Project Manager）: `project_scheduling` を 5 つ目の problem_type
として配線。Topological Sort（DFS）/ Critical Path Method / RCPSP（priority_list + OR-Tools
CP-SAT）/ networkx オラクルを追加。backend 405 passed / ui 35 passed / alembic no-op。

さらにその前（2026-09-10、Phase 7 ── Travel Planner）: `travel_planning` を 4 つ目の problem_type
として配線、Floyd-Warshall / Knapsack DP / Greedy / BruteForce。backend 343 passed / ui 31 passed。
