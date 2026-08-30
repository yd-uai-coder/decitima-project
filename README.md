# DeciTima

> **AI-powered Decision Optimization Platform**

## ## 概要

DeciTimaは、ユーザーの自然言語による要求をAIで構造化し、アルゴリズム・最適化手法によって複雑な制約条件を持つ問題を解決し、意思決定を支援するWebプラットフォームです。

単なるAIチャットアプリやアルゴリズム学習アプリではなく、

```text
ユーザーの要求
      ↓
LLMによる問題理解
      ↓
制約・目的の構造化
      ↓
Validation
      ↓
Algorithm / Optimization Engine
      ↓
候補解の生成
      ↓
Constraint Verification
      ↓
比較・シミュレーション
      ↓
意思決定
```

というパイプラインを基本とします。

---

## 1. プロジェクトの目的

本プロジェクトでは、

> **「人間が自然言語で表現した複雑な問題を構造化し、決定論的なアルゴリズムによって解決する」**

というAIとアルゴリズムの組み合わせを実現します。

特に重要なのは、**LLMに最適解そのものを計算させないこと**です。

LLMは曖昧な要求の理解・構造化・説明を担当し、実際の計算・制約判定・最適化はAlgorithm / Optimization Engineが担当します。

この責務分離によって、

- 再現性
- 制約遵守
- 計算結果の検証
- ベンチマーク
- アルゴリズム比較
- 結果の監査

を可能にします。

---

# 2. サービスコンセプト

## Decision Optimization Platform

サービスの中心概念を **Decision Optimization** とします。

ユーザーが、

```text
何をしたいか
どんな条件があるか
何を優先したいか
```

を入力すると、システムが問題を構造化し、適切なアルゴリズムを利用して解決します。

### 基本フロー

```text
┌──────────────────┐
│      User        │
│                  │
│ 自然言語で要求   │
└────────┬─────────┘
         ↓
┌──────────────────┐
│       LLM        │
│                  │
│ 意図理解         │
│ 条件抽出         │
│ 問題構造化       │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Structured       │
│ Problem          │
│                  │
│ Objective        │
│ Constraints      │
│ Variables        │
└────────┬─────────┘
         ↓
┌──────────────────┐
│    Validator     │
│                  │
│ 型・値・制約検証 │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Optimization     │
│ Engine           │
│                  │
│ DP               │
│ Graph            │
│ Greedy           │
│ Backtracking     │
│ Search           │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Candidate        │
│ Solutions        │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Verification     │
│                  │
│ Constraint Check │
│ Result Check     │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Simulation       │
│ / Comparison     │
└────────┬─────────┘
         ↓
      Decision
```

---

# 3. LLMの役割

LLMは本システムの**計算エンジンではありません**。

主な役割を以下の3つに限定します。

## 3.1 Natural Language → Structured Problem

ユーザーの自然言語を構造化します。

例えば、

> 5万円以内で東京を2日間旅行したい。食事を重視して、移動時間はできるだけ短くしたい。浅草には必ず行きたい。

という入力を、

```json
{
  "problem_type": "travel_optimization",
  "constraints": {
    "budget": 50000,
    "duration": 2,
    "required_places": ["浅草"]
  },
  "preferences": {
    "food": 1.0
  },
  "objectives": {
    "minimize": "travel_time"
  }
}
```

のような構造化データへ変換します。

ただし、**LLMの出力をそのまま信頼しません**。

必ずValidation Layerを通します。

---

## 3.2 Problem → Algorithm Recommendation

問題の性質を分析し、適切なアルゴリズム候補を提示します。

例えば、

```text
問題：
複数のスタッフを制約条件付きで
勤務時間に割り当てたい

Problem Type:
Constraint Optimization

Candidate Algorithms:
- Greedy
- Backtracking
- Branch and Bound

Recommended:
Backtracking
```

ただし、アルゴリズムの最終決定をLLMだけに依存しません。

**Rule Engine / Problem Characteristics / Input Size**などと組み合わせて決定します。

---

## 3.3 Result → Human-readable Explanation

Algorithm Engineが計算した結果を、人間が理解しやすい形に説明します。

例えば、

```text
最適化結果

人件費       ¥182,000
希望休達成率 96%
制約違反     0件
```

に対して、

> 人件費を優先しながら希望休を最大限反映した結果です。すべての必須制約を満たしています。

のような説明を生成します。

---

# 4. LLMに任せない処理

本プロジェクトでは、以下をLLMに直接任せません。

- 最適解の計算
- 経路探索
- Dynamic Programming
- Dijkstra
- スケジューリング
- 制約判定
- 数値計算
- ベンチマーク
- 結果の検証

これらは**Algorithm / Optimization Engine**が担当します。

### 理由

LLMは自然言語の理解には強い一方、

- 厳密な制約充足
- 数値最適化
- 再現性
- 最適性の保証

を決定論的に保証する計算エンジンではないためです。

したがって、

```text
LLM
 ↓
「こういう問題だと理解しました」
 ↓
Validation
 ↓
「実行可能な問題定義です」
 ↓
Algorithm Engine
 ↓
「この制約下での解です」
 ↓
Verification
 ↓
「すべての制約を満たしています」
```

という責務分離を基本設計とします。

---

# 5. Problem Schema

LLMとAlgorithm Engineの間には、共通の問題定義モデルを置きます。

概念的には、

```python
class OptimizationProblem:
    variables
    constraints
    objectives
    preferences
```

を基本とします。

例えば、

```json
{
  "variables": {
    "staff": 20,
    "days": 7
  },
  "constraints": [
    "minimum_staff_per_shift",
    "maximum_work_hours",
    "requested_holiday"
  ],
  "objectives": {
    "minimize": "labor_cost"
  }
}
```

のように表現します。

この**Problem Schemaをシステム内部の共通言語**とすることで、LLMと各アルゴリズムの結合を弱くします。

---

# 6. Validation Layer

LLMの出力は「提案」であり、システム上の事実ではありません。

そのため、LLMから受け取ったProblem Schemaを検証します。

### Input Validation

```text
budget >= 0
duration > 0
staff_count > 0
```

### Semantic Validation

```text
required_staff <= available_staff
maximum_hours >= minimum_hours
```

### Invalid Example

LLMが、

```json
{
  "budget": -50000
}
```

を返した場合、

```text
INVALID

budget must be >= 0
```

としてAlgorithm Engineへ渡しません。

---

# 7. Constraint Engine / Verification

Validationと、最適化結果の検証は分離します。

## Validation

「問題定義として正しいか？」

```text
budget >= 0
duration > 0
```

## Constraint Verification

「計算結果が条件を満たしているか？」

例えばシフト生成なら、

```text
staff_count >= required_staff
work_hours <= max_hours
requested_holiday == OFF
consecutive_days <= limit
```

を検証します。

1つでも必須制約に違反した場合、解を **INVALID** とします。

---

# 8. Algorithm / Optimization Engine

本プロジェクトの中心となる計算層です。各項目は「英名（和名）— 実装/使用する Phase」で示します
(プリミティブは主な使用 Phase または「随時」)。

## Search（探索）

- Linear Search（線形探索）— Phase 1
- Binary Search（二分探索）— Phase 1
- BFS（幅優先探索）— Phase 1
- DFS（深さ優先探索）— Phase 1

## Graph（グラフ）

- Dijkstra（ダイクストラ法）— Phase 1・4
- Bellman-Ford（ベルマン・フォード法）— Phase 4 ※負辺・負閉路検出
- A*（A スター探索）— Phase 4
- Floyd-Warshall（ワーシャル・フロイド法）— Phase 6 ※全点対最短。距離行列を返すプリミティブ
- Topological Sort（トポロジカルソート）— Phase 7
- Union-Find（素集合データ構造 / DSU）— Phase 4 ※プリミティブ
- Minimum Spanning Tree（最小全域木）: Kruskal（クラスカル法）/ Prim（プリム法）— Phase 4 ※`network_design` 問題

## Optimization（最適化）

- Brute Force（全探索）/ Bitmask Enumeration（ビット全探索）— Phase 3（ベンチマークの正解オラクル）、以降 各問題で小規模の厳密解として随時
- Greedy（貪欲法）— Phase 5・6
- Dynamic Programming（動的計画法。ボトムアップ / トップダウン = Memoization（メモ化））— Phase 6
- Knapsack（ナップサック問題）— Phase 6
- Backtracking（バックトラッキング）— Phase 5
- Branch and Bound（分枝限定法）— Phase 5

## Problem-solving Patterns（問題解決パターン）

これらはプリミティブ（§「Strategy とプリミティブの 2 層」）。特定 Phase に固定せず、使う
ストラテジーの実装時に必要に応じて実装する。下記は主な使用 Phase。

- Recursion（再帰）— 随時（DFS / Backtracking / 分割統治 / DP の実装手段。Phase 1〜）
- Divide and Conquer（分割統治法）— Phase 1（二分探索）、Phase 4（経路の区間分割）
- Two Pointers（ツーポインタ法）— 随時
- Sliding Window（スライディングウィンドウ）— Phase 5（連続勤務日数のチェック等）
- Prefix Sum（累積和）— Phase 4（累積距離）、Phase 5（時間帯別の集計）
- Difference Array（差分法 / imos 法）— Phase 5（連続時間帯の在籍人数）、Phase 7（リソース平準化）※累積和の対。区間加算の一括適用
- Hash-based Search（ハッシュを利用した探索）— Phase 1〜（id 引き・重複検出。全 Phase）

## Strategy とプリミティブの 2 層

アルゴリズムは単独で実装するのではなく、**実際の問題解決機能の内部で利用する**ことを基本とします。
これを 2 層に分けます。

- **AlgorithmStrategy（ストラテジー）**: 問題まるごとを解く。`OptimizationProblem` を受けて
  `CandidateSolution` を返す統一契約。Dijkstra / Bellman-Ford / Greedy / DP / Backtracking /
  Branch and Bound / Brute Force / Kruskal / Prim など。`registry` に載る。
- **アルゴリズム・プリミティブ**: 部品・技法。素の純粋関数として実装し、ストラテジーの内部や
  単体テストで使う。Binary Search / Two Pointers / Sliding Window / Prefix Sum /
  Difference Array / Hash-based Search / Union-Find / Floyd-Warshall（距離行列）/ 再帰 / 分割統治
  など。`registry` には載らない。

---

# 9. Algorithm Selection

アルゴリズム選択は、段階的に高度化します。

## Step 1 — Rule Based

まずは問題特性から決定します。

```text
if shortest_path:
    Dijkstra / A*

if subset_selection:
    Dynamic Programming

if scheduling_with_constraints:
    Backtracking

if local_optimum_is_valid:
    Greedy
```

## Step 2 — LLM Recommendation

LLMにもアルゴリズム候補を提示させます。

```text
Rule Engine
      +
LLM Recommendation
      ↓
Candidate Algorithms
      ↓
Algorithm Selection
```

## Step 3 — Benchmark-based Selection

将来的には、

- 入力サイズ
- 制約数
- グラフ密度
- 実行時間
- 解の品質

などの実測データを利用して、適切なアルゴリズムを選択する仕組みを検討します。

---

# 10. Candidate Solution → Verification

アルゴリズムは候補解を生成します。

```text
OptimizationProblem
        ↓
Algorithm
        ↓
CandidateSolution
        ↓
Constraint Checker
        ↓
       OK?
```

例えばシフト生成なら、

```text
Algorithm
 ↓
シフト生成
 ↓
Constraint Checker
 ├─ 人数 OK
 ├─ 勤務時間 OK
 ├─ 希望休 OK
 └─ 連続勤務 OK
```

となります。

検証に失敗した場合、

```text
INVALID SOLUTION
```

として結果を採用しません。

これにより、

> **「LLMがそう言ったから正しい」**
> 
> **「アルゴリズムが解を返したから正しい」**

という考え方を避け、**システム自身が解を検証する**設計にします。

---

# 11. Human-in-the-loop

AIが勝手に意思決定するのではなく、ユーザーが問題定義を確認できるUIを設けます。

```text
User
 ↓
LLM
 ↓
AIが理解した問題
 ↓
User Confirmation
 ↓
Optimization
 ↓
Result
```

例えば、

```text
AIが理解した条件
────────────────────────

予算：¥50,000
期間：2日
必須訪問先：浅草
優先事項：食事
最小化：移動時間

[この条件で最適化する]
[修正する]
```

とします。

これにより、**AIの解釈ミスを最適化処理の前段階で人間が修正できる**ようにします。

---

# 12. 実用ユースケース

## 12.1 Route Planner

経路を最適化します。

```text
Start
 ↓
Graph
 ↓
Dijkstra / A*
 ↓
最短経路
```

機能：

- Start / Goal設定
- 障害物設定
- 経路探索
- 複数アルゴリズム比較
- 経路可視化
- 距離・時間比較

---

## 12.2 Shift Scheduler

スタッフの勤務シフトを最適化します。

### 制約

- 勤務可能時間
- 希望休
- 最低勤務時間
- 最大勤務時間
- 最大連続勤務日数
- 必要人数
- 必要スキル

### 目的

- 人件費最小化
- 希望休最大化
- 勤務時間均等化

### 利用アルゴリズム

- Greedy
- Backtracking
- Branch and Bound

---

## 12.3 Travel Planner

予算・時間・訪問候補・ユーザーの好みから旅行プランを最適化します。

```text
予算
時間
訪問候補
好み
 ↓
LLM
 ↓
Structured Constraints
 ↓
DP / Graph / Greedy
 ↓
旅行プラン
```

### 利用アルゴリズム

- Dynamic Programming
- Knapsack
- Graph
- Greedy

---

## 12.4 Project Manager

タスクの依存関係から工程を最適化します。

```text
Task
 ↓
DAG
 ↓
Topological Sort
 ↓
Critical Path
 ↓
Project Schedule
```

### 機能

- タスク登録
- 依存関係設定
- ガントチャート
- Critical Path
- 完了予定日の計算

---

## 12.5 Logistics Optimizer

複数のアルゴリズムを組み合わせた総合最適化問題です。

```text
配送ルート
    ↓
Dijkstra / A*

積載
    ↓
Dynamic Programming

配送順序
    ↓
Greedy / TSP

制約
    ↓
Backtracking
```

評価項目：

- 総距離
- 総コスト
- 配送時間
- 車両稼働率
- 遅延リスク

---

## 12.6 Network Designer

すべての拠点を最小コストで接続するネットワーク(最小全域木)を設計します。
例：通信網・配電網・道路網・拠点間の専用線の敷設計画。

```text
拠点（ノード）と敷設可能なリンク（重み = コスト / 距離）
        ↓
Kruskal（Union-Find）/ Prim（優先度キュー）
        ↓
最小全域木（選択するリンクの集合）
```

### 制約

- 全拠点が連結していること（必須）
- 必ず使うリンク / 使えないリンク

### 目的

- 総敷設コストの最小化

### 利用アルゴリズム

- Kruskal（クラスカル法）
- Prim（プリム法）
- Union-Find（素集合データ構造）

---

# 13. What-if Simulation

最適解を1つ提示するだけではなく、

**条件を変えた場合に結果がどう変化するか**

を比較します。

例えば、

```text
車両数       配送時間       コスト
----------------------------------
5台           6.2h         ¥80,000
4台           7.8h         ¥72,000
3台          10.4h         ¥64,000
```

のように比較します。

目的は、

> 「最適解は何か？」

だけではなく、

> **「どの条件なら、どの選択をするべきか？」**

を支援することです。

---

# 14. Benchmark

アルゴリズムとLLMの性能・品質を定量的に評価します。

## Algorithm Benchmark

```text
Algorithm   Time    Operations   Result
----------------------------------------
BFS         12ms      8,421       521km
Dijkstra     8ms      4,213       521km
A*           4ms      1,872       521km
```

※数値は実装後に実測します。

評価項目：

- 実行時間
- 操作回数
- メモリ使用量
- 入力サイズ
- 解の品質
- 制約違反数

---

# 15. LLM vs Algorithm Pipeline

本プロジェクトの重要な検証テーマの一つです。

同一データセットに対して、

## A. LLM Only

```text
User
 ↓
LLM
 ↓
Answer
```

## B. LLM + Algorithm Pipeline

```text
User
 ↓
LLM
 ↓
Validation
 ↓
Algorithm
 ↓
Verification
 ↓
Answer
```

を比較します。

## 評価指標

| 指標    | LLM Only | Algorithm Pipeline |
| ----- | --------:| ------------------:|
| 制約遵守率 | 実測       | 実測                 |
| 最適性   | 実測       | 実測                 |
| 再現性   | 実測       | 実測                 |
| 実行時間  | 実測       | 実測                 |
| 検証可能性 | 実測       | 実測                 |
| エラー率  | 実測       | 実測                 |

**実際のベンチマーク結果を取得してから数値を記載することを原則とします。**

この検証によって、

> **「AIを使うこと」ではなく「AIと決定論的アルゴリズムをどのように組み合わせるべきか」**

を技術的に示します。

---

# 16. システムアーキテクチャ

```text
┌─────────────────────────────────────────┐
│            Next.js + Tamagui            │
│                                         │
│ Dashboard                               │
│ Problem Input                           │
│ AI Interpretation                       │
│ Visualization                           │
│ Simulation                              │
│ Benchmark                               │
└───────────────────┬─────────────────────┘
                    │
                    │ REST API
                    ▼
┌─────────────────────────────────────────┐
│                 FastAPI                 │
│                                         │
│ API Layer                               │
│        ↓                                │
│ Service Layer                           │
│        ↓                                │
│ Problem / Validation                    │
│        ↓                                │
│ Algorithm / Optimization Engine         │
│        ↓                                │
│ Verification                            │
│        ↓                                │
│ Repository Layer                        │
└───────────────┬─────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │  PostgreSQL   │
        └───────────────┘
```

LLMは独立したサービス層として扱います。

```text
┌──────────────────────────┐
│        LLM Service       │
│                          │
│ Intent Extraction        │
│ Constraint Extraction    │
│ Algorithm Recommendation │
│ Result Explanation       │
└────────────┬─────────────┘
             │
             ▼
       Structured Problem
```

LLM ServiceとAlgorithm Engineを直接結合させないことを基本とします。

---

# 17. Backend構成

```text
app/
├── main.py
│
├── api/
│   └── routes/
│       ├── algorithms.py
│       ├── optimization.py
│       ├── scheduling.py
│       ├── projects.py
│       ├── simulation.py
│       └── llm.py
│
├── services/
│   ├── algorithm_service.py
│   ├── optimization_service.py
│   ├── scheduling_service.py
│   ├── simulation_service.py
│   ├── validation_service.py
│   ├── verification_service.py
│   └── llm_service.py
│
├── algorithms/
│   ├── search/
│   ├── graph/
│   ├── optimization/
│   ├── scheduling/
│   └── patterns/
│
├── domain/
│   ├── problems/
│   ├── constraints/
│   ├── objectives/
│   └── solutions/
│
├── repositories/
│
├── schemas/
│
├── models/
│
└── core/
```

---

# 18. 技術スタック

## Frontend

- Next.js
- React
- TypeScript
- Tamagui

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

## Database

- PostgreSQL

## AI

- LLM API
- Structured Output
- Function Calling / Tool Calling
- LangChain / LangGraph（必要に応じて）

## Infrastructure

- Docker
- Docker Compose
- GitHub Actions
- Vercel
- VPS

---

# 19. 開発Phase

## CL(Curriculum Loop)開発

本プロジェクトの開発・学習手法を **CL(Curriculum Loop)開発** と名付ける。

> AIがPhase単位で学習教材とサンプルコードを著述し、人間が手でコードを書く。
> 実装で当たった疑問・改善点が質問・相談を通じて教材とサンプルに還流し、
> 教材とプロジェクトが一つのループの中で共に洗練されていく開発・学習手法。

### 特徴とメリット

- **人間が手で実装する**。AIはコードを書かず、設計・教材・サンプル・トレードオフの説明を担う
  (AIがコードを書く「vibe coding」の対極)。
- **Phase単位で教材とサンプルコードを生成する**。各Phaseは「学習教材 + サンプルコード +
  実装前チェックリスト」で構成し、`textbook/Phase-<N>/` に置く。
- **双方向の還流ループ**。「教材 → 実装」の一方向でなく、実装で生じた疑問・改善点が
  教材とサンプルに反映される。実装途中の変更は後のPhaseにも遡って反映されるため、
  教材とプロジェクトが共進化し、大きなやり直しのリスクを抑えられる。
- **設計判断がサンプルコードで実検証される**。教材で示す設計は
  `textbook/Phase-<N>/samples/` で実際に動作・型チェックされるため、机上の空論になりにくい。



### 進行

- ユーザーの「Phase#を開始する」で、そのPhaseの教材・サンプルを生成する。
- 実装着手前に「実装前チェックリスト」(作るファイル / 各クラス・関数の責務 / テスト観点)で
  疑問を出し切る。
- 設計判断・検討事項・質問と回答は `CLAUDE.md` のNotesに記録し、以降の進行に活かす。

### 進行のポイント(メモ)
- テストは必ずユーザー自身で実施する。
    - テスト値や結果を変えて実行してみる事。
  基本的にコードはコピペで問題なく動くが、テストはユーザーの設計理解を確認する上で重要な機会でもある。

#### テストを通じた設計理解(重要視する)

- 写経したテストごとに「**テスト対象は何か / それを呼ぶドライバは何か / 差し替えたスタブは何か**」を
  言えるようにする。テストダブル(スタブ)の要否は設計の鏡 ── 対象が純粋なら不要で、
  外部(DB・Redis・時刻・LLM)に依存するほど増える。
- スタブが要る = 対象がその依存に結合しているサイン。`app/domain` `app/algorithms` に
  スタブが出てきたら、純粋レイヤーの原則(Phase 0 アーキテクチャ設計)が崩れていないか疑う。
- ドライバはテスト関数自身。ビルダー fixture(`build_route_problem` 等)は入力生成なのでドライバ側。
  スタブ(対象が呼ぶ下位依存の代役)とは役割が別。
- 写経直後にテストが緑でも「コピペが効いただけ」かもしれない。期待値・制約・入力を変えて
  一度わざと赤にし、境界と不変条件(invariant)を体で確認する。
- 出力の確認は `pytest -s`(その場出力)/ `-rP`(成功テストの出力をまとめて表示)。
  オブジェクトの構造を見るなら `print(obj.model_dump_json(indent=2))`。
- 各 Phase 教材の `## テスト観点` に、この「対象 / ドライバ / スタブ」の関係を明記する
  (進行ルール #14)。

---

## Phase 0 — Optimization Architecture

**目的：責務分離と共通モデルを確立する**

- 要件定義
- アーキテクチャ設計
- Problem Schema
- Constraint Schema
- Objective Schema
- Solution Schema
- API設計
- DB設計
- Algorithm Engine設計
- Validation / Verification設計
- Docker環境

---

## Phase 1 — Algorithm Engine

**目的：決定論的な計算基盤を作る**

- Binary Search
- BFS
- DFS
- Dijkstra
- 基本的なAlgorithm Interface
- Algorithm実行API
- Unit Test

---

## Phase 2 — Validation / Constraint Engine

**目的：入力と制約を検証する**

- Pydantic Validation
- Constraint Validation
- Constraint Checker
- Solution Verification
- Invalid Solution Handling

---

## Phase 3 — Benchmark

**目的：アルゴリズムを定量評価できる基盤を作る**

- 実行時間計測
- 操作回数
- メモリ使用量
- 入力サイズ別比較
- アルゴリズム比較UI
- 可視化

---

## Phase 4 — Route Planner / Network Designer

**目的：Graph Algorithmを実問題へ適用する**

- Graph Model
- Dijkstra
- Bellman-Ford（負辺・負閉路検出）
- A*
- 経路可視化
- 複数アルゴリズム比較
- Route Benchmark
- Network Design（最小全域木）: `network_design` problem_type / Kruskal / Prim / Union-Find

---

## Phase 5 — Shift Scheduler

**目的：Constraint Optimizationを実装する**

- Staff Model
- Shift Model
- 制約定義
- Greedy
- Backtracking
- Branch and Bound
- Constraint Verification
- シフト可視化

---

## Phase 6 — Travel Planner

**目的：Dynamic Programmingを実問題へ適用する**

- Place Model
- Budget Constraint
- Time Constraint
- Preference Model
- Knapsack DP
- Graph
- Floyd-Warshall（訪問地間の全点対距離。訪問順最適化の前処理。内部利用）
- Greedy
- プラン比較

---

## Phase 7 — Project Manager

**目的：Graph / Scheduling Algorithmを工程管理へ適用する**

- Task Model
- Dependency
- DAG
- Topological Sort
- Critical Path
- Schedule Generation
- ガントチャート

---

## Phase 8 — Logistics Optimizer

**目的：複数アルゴリズムを組み合わせた総合最適化**

- Vehicle Model
- Delivery Model
- Capacity Constraint
- Route Optimization
- Packing Optimization
- Delivery Order Optimization
- 複合的なConstraint Verification

---

## Phase 9 — What-if Simulation

**目的：意思決定支援へ拡張する**

- 条件変更
- 複数シナリオ生成
- 結果比較
- Cost / Time / Quality比較
- Sensitivity Analysis

---

## Phase 10 — LLM Problem Structuring

**目的：自然言語を問題定義へ変換する**

```text
Natural Language
 ↓
LLM
 ↓
Structured Problem
 ↓
Validation
```

実装：

- LLM API
- Structured Output
- Intent Extraction
- Constraint Extraction
- Objective Extraction
- Problem Type Classification

---

## Phase 11 — Algorithm Recommendation

**目的：問題特性からアルゴリズム候補を提示する**

```text
Problem
 ↓
Rule Engine
 +
LLM
 ↓
Candidate Algorithms
 ↓
Algorithm Selection
```

---

## Phase 12 — Result Explanation

**目的：アルゴリズムの結果を人間に説明する**

```text
Algorithm Result
 ↓
LLM
 ↓
Explanation
```

説明対象：

- なぜこの解になったか
- どの制約が重要だったか
- どのアルゴリズムを使ったか
- 他の候補との違い
- 改善余地

---

## Phase 13 — LLM vs Algorithm Comparison

**目的：LLMと決定論的アルゴリズムの特性を実測する**

同一問題に対して、

```text
LLM Only
```

と、

```text
LLM
 ↓
Validation
 ↓
Algorithm
 ↓
Verification
```

を比較します。

評価：

- 制約遵守率
- 最適性
- 再現性
- 実行時間
- エラー率
- 検証可能性

---

## Phase 14 — Production

**目的：実サービスとして公開できる品質へ仕上げる**

### Testing

- Unit Test
- Integration Test
- API Test
- E2E Test
- Algorithm Test
- Constraint Test

### Performance

- Algorithm Benchmark
- DB Query Optimization
- 非同期処理
- Cache
- 大規模入力テスト

### Security

- Authentication
- Authorization
- Input Validation
- Rate Limit
- CORS
- Secret Management

### Deployment

```text
GitHub
   ↓
GitHub Actions
   ↓
Docker
   ↓
VPS

Next.js
   ↓
Vercel
```

---

# 20. MVP

最初からPhase 14まで完成させるのではなく、以下をMVPとします。

```text
Phase 0
   ↓
Phase 1
   ↓
Phase 2
   ↓
Phase 3
   ↓
Phase 4
   ↓
Phase 5
```

MVP完成時点で、

- Next.js
- Tamagui
- FastAPI
- PostgreSQL
- REST API
- Algorithm Engine
- Validation
- Verification
- BFS / Dijkstra / Bellman-Ford / Kruskal・Prim（Union-Find）等
- Benchmark
- 可視化
- Route Planner
- Network Designer（最小全域木）
- Shift Scheduler

を一通り経験できる構成とします。

その後、

```text
Travel Planner
      ↓
Project Manager
      ↓
Logistics
      ↓
Simulation
      ↓
LLM
      ↓
LLM vs Algorithm Benchmark
```

と段階的に拡張します。

---

# 21. ポートフォリオとして示す技術力

本プロジェクトでは、単にアルゴリズムを実装できることだけではなく、以下の能力を示すことを目的とします。

## Algorithm

- Search
- Graph
- Dynamic Programming
- Greedy
- Backtracking
- Branch and Bound
- Scheduling
- Optimization
- Problem-solving Patterns

## Backend

- FastAPI
- REST API
- Service / Repository Architecture
- Domain Modeling
- Validation
- Constraint Processing
- Result Verification
- Database設計

## Frontend

- Next.js
- React
- TypeScript
- Tamagui
- Dashboard
- Visualization
- Simulation UI

## AI

- LLM API
- Structured Output
- Function Calling / Tool Calling
- Natural Language Problem Structuring
- Algorithm Recommendation
- Result Explanation
- Human-in-the-loop
- AIと決定論的アルゴリズムの責務分離

## Engineering

- Docker
- CI/CD
- Testing
- Benchmark
- Performance Optimization
- Security
- Production Deployment

---

# 22. 最終的に実現するシステム

最終的には、以下のアーキテクチャを目標とします。

```text
                       User
                         │
                         ▼
              ┌──────────────────┐
              │   LLM Interface  │
              │                  │
              │ Understand       │
              │ Extract          │
              │ Explain          │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Problem Schema   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │    Validator     │
              │                  │
              │ Type Validation  │
              │ Constraint       │
              │ Validation       │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Algorithm        │
              │ Selector         │
              └────────┬─────────┘
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
            DP       Graph     Greedy
             │         │         │
             └─────────┼─────────┘
                       ▼
              ┌──────────────────┐
              │ Candidate        │
              │ Solution         │
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │ Verification     │
              │                  │
              │ Constraint Check │
              │ Result Check     │
              └────────┬─────────┘
                       │
                ┌──────┴──────┐
                │             │
              INVALID        VALID
                │             │
                │             ▼
                │      ┌──────────────┐
                │      │ Simulation   │
                │      │ Comparison   │
                │      └──────┬───────┘
                │             │
                └─────────────┤
                              ▼
                       ┌─────────────┐
                       │    LLM      │
                       │ Explanation │
                       └──────┬──────┘
                              ▼
                            User
```

---

# 23. プロジェクトの最終コンセプト

DeciTimaは、

> **AIを使って人間の曖昧な要求を構造化し、アルゴリズムによって厳密に問題を解決し、意思決定を支援するプラットフォーム**

を目指します。

AIにすべてを任せるのではなく、

```text
LLM
 ↓
理解・構造化
 ↓
Validation
 ↓
Algorithm
 ↓
Optimization
 ↓
Verification
 ↓
Simulation / Comparison
 ↓
LLM
 ↓
説明
```

という構造を採用します。

本プロジェクトの核心は、

> **「LLMでは保証できない厳密な制約・最適化を、決定論的なAlgorithm / Optimization Engineで担保する」**

ことです。

これにより、LLMの柔軟な自然言語理解と、アルゴリズムの再現性・検証可能性・計算上の厳密性を組み合わせます。

---

# 24. Project Goal

最終的なゴールは、単なる

> **AIアプリケーション**

でも、

> **アルゴリズム学習アプリケーション**

でもありません。

目指すのは、

> ### **AI-assisted Decision Optimization Platform**

です。

人間が問題を定義し、AIがその問題を構造化し、決定論的なアルゴリズムが解を計算・検証し、シミュレーションによって意思決定を支援する。

この一連のプロセスを、**再現可能・検証可能・比較可能なシステムとして実装すること**を本プロジェクトの最終目標とします。
