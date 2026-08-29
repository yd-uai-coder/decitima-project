# Phase 0-0: 概観 ── Phase 0 は「設計フェーズ」

## この章のゴール

Phase 0 の 9 章を読む前の見取り図。**Phase 0 は実コードをほとんど書かない設計フェーズ**で、
成果物は「共通スキーマ・レイヤー構成・検証の分け方・API/DB の形」を決めた設計文書
(この `Phase-0/` 一式)と、`decitima-api` への低リスクな骨組みだけ。実装は Phase 1 から。

---

## 1. DeciTima の核 ── 責務分離

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

## 2. 設計を検証する 2 題材

抽象論で終わらせず、Phase 0 の設計はすべてこの 2 つで「本当に表現できるか」を確認する。

| | Route Planner(Phase 4) | Shift Scheduler(Phase 5) |
| --- | --- | --- |
| 問題の型 | グラフ探索 | 組合せ最適化(割当) |
| 目的 | 単一(距離最小化) | 多目的(人件費最小 + 希望休最大) |
| 制約 | ほぼ hard のみ | hard と soft の混在 |
| 解の形 | ノードの列(経路) | 二次元の割当表 |

性質が対照的なので、両方を 1 スキーマ・1 エンジンインターフェースで扱えれば汎用性は十分。

---

## 3. MVP スコープ

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

## 4. 9 章の地図 ── 「7 項目チェックリスト」との対応

実装前に確認する 7 項目(開発ポリシー)に、各章が対応する。

| 章 | 7 項目 | 決めること |
| --- | --- | --- |
| [Phase-0-1](./Phase-0-1.md) 要件定義とスコープ | 1. Requirements | 問題クラス、非ゴール、MVP、FR / NFR |
| [Phase-0-2](./Phase-0-2.md) ドメインモデル | 2. Domain Model | 共通スキーマ(ハイブリッド型)。`OptimizationProblem` / `Constraint` / `Objective` / `CandidateSolution` |
| [Phase-0-3](./Phase-0-3.md) アーキテクチャ設計 | 3. Architecture | `domain/` `algorithms/` の純粋レイヤー、solve のライフサイクル |
| [Phase-0-4](./Phase-0-4.md) Algorithm Engine 設計 | 4. Algorithm | `AlgorithmStrategy` Protocol、`registry`、Strategy とプリミティブの 2 層 |
| [Phase-0-5](./Phase-0-5.md) 計算量とパフォーマンス | 5. Complexity | 時間/空間計算量、手実装の破綻点、Phase 3 の測定項目、同期 + タイムアウト |
| [Phase-0-6](./Phase-0-6.md) Validation と Verification | 6. Implementation Plan | 2 つの検証の分離、hard→invalid / soft→penalty、`AppError` 派生 |
| [Phase-0-7](./Phase-0-7.md) API 設計 | 6. Implementation Plan | `POST /solve` を軸に MVP エンドポイントを絞る |
| [Phase-0-8](./Phase-0-8.md) DB 設計 | 6. Implementation Plan | JSONB 中心 + 検索キーのみカラム化 |
| [Phase-0-9](./Phase-0-9.md) テスト戦略・引き継ぎ | 7. Test Strategy | テストの階層、Docker、Phase 1 の作業分割 |

主要な設計決定の一覧と、後続 Phase での変更点(`[Phase N 改訂]` マーカー)は
[`phase-0-index.md`](./phase-0-index.md) を参照。

---

## 5. Phase 0 の成果物

- **textbook**: この `Phase-0/` 一式(概観 + 設計 9 章 + `samples/`)
- **decitima-api の低リスク整備**: chat ルート無効化 / `domain/`・`algorithms/` の空骨子 /
  `PROJECT_NAME` リブランド / `decitima-api/CLAUDE.md` 更新
- **ルート CLAUDE.md の Notes**: Phase 0 の主要な設計決定

次は [Phase-0-1](./Phase-0-1.md)(要件定義とスコープ)から。「Phase 1 を開始する」で実装フェーズへ。
