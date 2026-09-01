# Phase 0 — Optimization Architecture(設計フェーズ)導入

Phase 0 の 9 章を読む前の見取り図。**Phase 0 は実コードをほとんど書かない設計フェーズ**で、
成果物は「共通スキーマ・レイヤー構成・検証の分け方・API/DB の形」を決めた設計文書
(この `Phase-0/` 一式)と、`decitima-api` への低リスクな骨組みだけ。実装は Phase 1 から。

---

## 1. このフェーズの目的

責務分離と共通モデルを確立する。DeciTima の核は「LLM は理解・構造化・説明のみ、
計算・検証・最適化は決定論的なアルゴリズム」で、両者の結合点が共通スキーマ
`OptimizationProblem`。設計はすべて MVP の 2 題材 ── **Route Planner**(Phase 4)と
**Shift Scheduler**(Phase 5)── で通し検証している。

---

## 2. DeciTima の核 ── 責務分離

README のパイプラインを 7 ステージに分ける。**LLM は計算しない**。

```text
1. User      自然言語(MVP では構造化 JSON を直接入力)
2. LLM       意図理解・条件抽出・問題構造化          ← Phase 10〜
3. Structured Problem   OptimizationProblem(共通スキーマ)= LLM と Algorithm の共通言語
4. Validation           「問題として妥当か?」        ← Phase 2
5. Algorithm Engine     決定論的な計算。候補解を生成   ← Phase 1〜
6. Verification         「解が制約を満たすか?」        ← Phase 2
7. Simulation / Comparison  条件を変えて比較           ← Phase 9
   → LLM が結果を説明                                ← Phase 12〜
```

**Validation(4)と Verification(6)を分ける**のが設計の肝。対象・タイミング・失敗の意味・
HTTP ステータスがすべて違う(`Phase-0-6.md`)。

---

## 3. 設計を検証する 2 題材

抽象論で終わらせず、Phase 0 の設計はすべてこの 2 つで「本当に表現できるか」を確認する。

| | Route Planner(Phase 4) | Shift Scheduler(Phase 5) |
| --- | --- | --- |
| 問題の型 | グラフ探索 | 組合せ最適化(割当) |
| 目的 | 単一(距離最小化) | 多目的(人件費最小 + 希望休最大) |
| 制約 | ほぼ hard のみ | hard と soft の混在 |
| 解の形 | ノードの列(経路) | 二次元の割当表 |

性質が対照的なので、両方を 1 スキーマ・1 エンジンインターフェースで扱えれば汎用性は十分。

---

## 4. MVP スコープ

MVP は **Phase 0〜5**。LLM は含まず、構造化 JSON を直接投入する。

| Phase | 目的 |
| --- | --- |
| 0 | 責務分離と共通モデルの確立(この設計フェーズ) |
| 1 | 決定論的な計算基盤(Binary Search / BFS / DFS / Dijkstra / `AlgorithmStrategy` / 実行 API / Unit Test) |
| 2 | 入力と制約の検証(Validation / Constraint Checker / Verification) |
| 3 | アルゴリズムの定量評価(ベンチマーク / 比較 UI) |
| 4 | Route Planner / Network Designer(グラフアルゴリズムの実問題適用) |
| 5 | Shift Scheduler(制約最適化) |

---

## 5. 章一覧 ── 9 章と「7 項目チェックリスト」の対応

実装前に確認する 7 項目(開発ポリシー)に、各章が対応する。

| 章 | 7 項目 | 説明 |
| --- | --- | --- |
| [Phase-0-1](./Phase-0-1.md) 要件定義とスコープ | 1. Requirements | 問題クラス、非ゴール(LLM に計算させない)、MVP、FR / NFR |
| [Phase-0-2](./Phase-0-2.md) ドメインモデル: 共通スキーマ | 2. Domain Model | なぜ共通スキーマが要るか、ハイブリッド型、ファイル構成(§2.5)、`Objective` / `Constraint`(hard・soft)/ `OptimizationProblem` / `CandidateSolution`、拡張ポイント(§8.1: `network_design`) |
| [Phase-0-3](./Phase-0-3.md) アーキテクチャ設計 | 3. Architecture | 全体構成、新レイヤー `domain/` `algorithms/`(純粋・副作用なし)、solve のライフサイクル、2 トラックの吸収、既存資産の再利用 |
| [Phase-0-4](./Phase-0-4.md) Algorithm Engine 設計 | 4. Algorithm | `AlgorithmStrategy` Protocol(`solve` は純粋・検証しない)、**Strategy とプリミティブの 2 層**(§2.4)、`AlgorithmMeta`、`registry`、手実装/産業ソルバーの 2 トラック、rule-based 選択 |
| [Phase-0-5](./Phase-0-5.md) 計算量とパフォーマンス設計 | 5. Complexity | 時間/空間計算量、想定入力サイズと手実装の破綻点(Shift は中規模で CP-SAT 必須)、Phase 3 で測る 6 指標、同期 + タイムアウト(ジョブキューは YAGNI) |
| [Phase-0-6](./Phase-0-6.md) Validation と Verification 設計 | 6. Implementation Plan | 2 つの検証の分離、Input/Semantic Validation、`kind` ごとのチェッカー、hard→invalid / soft→penalty、`AppError` 派生、2 題材の検証項目一覧 |
| [Phase-0-7](./Phase-0-7.md) API 設計 | 6. Implementation Plan | MVP エンドポイントの絞り込み(`POST /solve` が軸、専用 API は作らない)、リクエスト/レスポンス、エラー形式、既存 JWT / `RateLimiter` の再利用 |
| [Phase-0-8](./Phase-0-8.md) DB 設計 | 6. Implementation Plan | 保存対象、JSONB 中心 + 検索キーのみカラム化、ORM(既存 `conversation.py` 踏襲)、ミューテーション追跡の落とし穴、Alembic 運用 |
| [Phase-0-9](./Phase-0-9.md) テスト戦略・Docker・Phase 1 への引き継ぎ | 7. Test Strategy | テストの階層(domain/algorithms の純粋関数テストが主戦場)、プロパティベーステスト候補、`conftest.py` の env 順序、Docker は変更不要、依存追加の Phase 別計画、Phase 1 の作業分割 |

---

## 6. サンプルコード(`samples/`)

| ファイル | 内容 |
| --- | --- |
| [problem_schema.py](./samples/problem_schema.py) | 共通スキーマの Pydantic v2 スケッチ(`OptimizationProblem` / `Constraint` / `CandidateSolution` ほか) |
| [algorithm_strategy.py](./samples/algorithm_strategy.py) | `AlgorithmStrategy` Protocol + `registry` + `select_strategy` のスケッチ |
| [route_planner_example.py](./samples/route_planner_example.py) | Route Planner を共通スキーマで表現(禁止エッジ + 必須経由) |
| [shift_scheduler_example.py](./samples/shift_scheduler_example.py) | Shift Scheduler を共通スキーマで表現(多目的 + hard/soft 混在) |

いずれも動作確認済み。実行コマンド(ホストの uv / Docker 併記)は
[Phase-0-2 §7.3](./Phase-0-2.md#73-実行して確かめる)。
decitima-api には未配線の「設計の例示」で、Phase 1 で `app/domain/` へ整理する
(整理の正は `textbook/Phase-1/samples/`。§「後続 Phase での改訂」参照)。

---

## 7. Phase 0 の成果物

- **textbook**: この `Phase-0/` 一式(この導入 + 設計 9 章 + `samples/`)
- **decitima-api の低リスク整備**: chat ルート無効化 / `domain/`・`algorithms/` の空骨子 /
  `PROJECT_NAME` リブランド / `decitima-api/CLAUDE.md` 更新
- **ルート CLAUDE.md の Notes**: Phase 0 の主要な設計決定を追記

Phase 1 の実装前チェックリスト(作るファイル / 責務 / テスト観点)は
[`Phase-1-introduction.md`](../Phase-1/Phase-1-introduction.md) §10 が正。

---

## 8. 後続 Phase での改訂

進行のルール #12。Phase 0 の設計から後続 Phase で変わる点(該当箇所に「以降 Phase で修正予定」
マーカー ── その Phase を読む時点では samples のまま実装してよい):

| 変更元 | 当初 → 現在 | 詳細 |
| --- | --- | --- |
| `Phase-0-2.md` §4.4 / §5.3 / §6 / §8.1、`samples/problem_schema.py` | 型エイリアス `X: TypeAlias = Annotated[...]` → PEP 695 `type X = Annotated[...]` | `Phase-1-1.md` §2.1 |
| `Phase-0-2.md` §8.1、`samples/problem_schema.py` | `ProblemData` / `SolutionData` は 3 メンバー(network_design 含む)→ Phase 1 は route/shift の 2 メンバー。network_design は **Phase 4** | `Phase-1-1.md` §2.2 |
| `Phase-0-2.md` §2.5、`Phase-0-3.md` §2.3 | `objectives/`(重み付き和の評価器)は Phase 1 → **Phase 5**(初の多目的ストラテジー実装時) | `Phase-1-1.md` §1 / `Phase-1-7.md` §5 |
| `Phase-0-2.md` §4.2 | `NumericBoundConstraint` のフィールド `op` → `operator` | `Phase-2-1.md` / `Phase-2-3.md` §1 |
| `Phase-0-6.md` §2.3 / §3 / §5 | `_SEMANTIC_CHECKS` は `domain/problems/semantic.py`、`_CHECKERS` は `domain/constraints/`。到達可能性は services に残置。構造検証は `domain/solutions/structure.py`。`staffing` は opt-in。連続勤務は素の日次スキャン | `Phase-2-2.md` / `Phase-2-3.md` / `Phase-2-4.md` |
| `Phase-0-8.md` §2 / §4 | `verifications` テーブルは **作らない**(YAGNI 確定) | `Phase-2-introduction.md` §7 |

---

## 9. 次のフェーズ

「Phase 1 を開始する」で、この設計を決定論的な計算基盤として実装する
(スキーマ実装 / `AlgorithmStrategy` / Binary Search・BFS・DFS・Dijkstra の手実装 /
実行 API / Unit Test)。まず [`Phase-1-introduction.md`](../Phase-1/Phase-1-introduction.md) を読む。
