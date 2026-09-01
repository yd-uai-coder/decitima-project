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
- NumPy（ベンチマーク集計。Phase 3〜）
- pandas / matplotlib（分析トラック `analysis/`。dev 依存、`app` からは切り離し。Phase 3〜)

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
- **設計判断は「ルールに従えば OK」でなく「各層が何のためにあるか」で下す**。
  「domain は純粋、依存は内向き」と図で読んでも、どこにエッジがあるかは体感できない。
  CL 開発では `import` 制約のような guardrail が誤りを写経中に顕在化させ、
  「これは計算か? 述語か?」「この責務はどの層のものか?」と問い直す機会になる ──
  図で素通りしがちなアーキテクチャ判断を、手を動かして体得する
  (例: Phase 2-2 で route の到達可能性を「計算 = `algorithms`、判定 = `services`」に分けた。
  `textbook/Phase-2/Phase-2-2.md` §3)。

### 適さないケース / 制約

- **進行スピードは非保証**。開発と学習を兼ね、還流ループを品質優先で回すため。
  **納期の定まった実務プロジェクトには、そのままでは不向き**。
- 個人学習でも所要期間の見積りが立ちにくい(現状、Phase に目安工数・タイムボックスが無い)。
- 想定は「学習モード」(全写経 + テスト値改変 + 事前質問を厚く)。速度が要るときは
  「納期モード」(速習パス + 定型コードはコピー + テストは実行のみ + 学習は事後レビューで回収)
  に切り替える ── ただし学習効果は落ちる。
- 原因の分解と改善提案(タイムボックス / 写経レベル / 到達度チェック等)は
  `CLAUDE.md` の所感「【重点課題】進行スピードが担保できない」を参照。



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

## Phase の順序 ── 設計思想

Phase は「作れるものから作る」順ではなく、次の 3 原則で並べている。

### 原則 1 — ケイパビリティ層を先に、ドメイン適用を後に

```text
Phase 1  計算する          ┐
Phase 2  検証する          ├─ ドメイン非依存の「エンジンと周辺機構」(横断)
Phase 3  測る・比べる      ┘
        ───────────────────────────────────────────────
Phase 4〜8   実問題ドメイン(グラフ → 制約最適化 → DP → スケジューリング → 複合)
Phase 9      What-if シミュレーション(意思決定支援層)
Phase 10〜13  LLM 層(構造化・推薦・説明・比較)
Phase 14     本番化
```

プラットフォーム(エンジン)を先に固め、その上に問題ドメインを差し込む。
**LLM は最後**(Phase 10〜)── 決定論的なエンジンが信頼できる状態になって初めて、
その前段に LLM を置く。この責務分離が DeciTima の核(§2)。

### 原則 2 — 各 Phase の成果物が次の Phase の前提(依存の連鎖)

| Phase | 足すもの | なぜこの位置か |
| --- | --- | --- |
| **1** 計算基盤 | `AlgorithmStrategy` / Dijkstra / 探索プリミティブ / `POST /solve` | 純粋層なので単体で作れて速くテストできる。下流はすべて「解を生成するもの」を呼ぶ。route 限定の最小 Validation / Verification も配線し、パイプラインの骨格を 1 本通す(walking skeleton) |
| **2** 検証 | 全 kind の Constraint Checker / Solution Verification | **検証には検証対象(候補解)が要る** → Phase 1 が先。Phase 1 の route 限定 V&V を全 kind・shift へ一般化する |
| **3** ベンチマーク | 実行時間・操作回数・メモリ計測 / 比較 UI / 全探索オラクル | 「計算できる + 検証できる」があって初めて「測って比べる」ができる。Phase 4/5 が同一問題に複数アルゴリズムを足す前に、比較基盤を用意しておく |
| **4** Route Planner | Graph Model / Bellman-Ford / A* / MST / 経路可視化 | **最初の実ドメイン**。Phase 1 のグラフ資産を最大限再利用 ── 新パラダイムでなく「グラフの深掘り」。制約はほぼ hard のみ、解は経路(列)で可視化・検証も素直 |
| **5** Shift Scheduler | Staff/Shift モデル / Greedy / Backtracking / Branch and Bound / 多目的評価 | **最難関を最後に**。組合せ探索(新パラダイム)+ 多目的 + hard/soft 混在、そして**手実装が実規模で破綻**(Phase 5)→ OR-Tools CP-SAT トラックを導入。Strategy 契約・ベンチ・Verification が揃ってから第 2 トラックを吸収する |

### 原則 3 — アルゴリズムの難易度を単調増加に(学習カリキュラム)

CL 開発は学習を兼ねるため、教科書の章が進むように難しくする:
線形/二分探索・BFS/DFS・Dijkstra(Phase 1)→ Bellman-Ford・A*・MST(Phase 4)→
Backtracking・Branch and Bound(Phase 5)→ Knapsack DP・Floyd-Warshall(Phase 6)→
Topological Sort・Critical Path(Phase 7)。

### Route を Shift より先にする理由

「再利用が最大 / 新概念が最小」の回を先に、「新概念が最大 / 設計の最難関の主張
(多目的・hard/soft・手実装 vs 産業ソルバー比較)をまとめて実証する」回を後に。

### 補足 — リスクは Phase 0 で前倒し済み

定石は「最も不確実なものを最初に」。MVP 最大のリスク(Phase 5 の手実装破綻 → CP-SAT が必要)は
最後に置くが、破綻点も OR-Tools トラックの計画も Phase 0(`textbook/Phase-0/Phase-0-5.md`)で
分析済み。Phase 5 は「既知の計画を実行する」段階。

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

### 設計のポイント

- **「LLM に最適解を計算させない」を全体の前提に置く。** LLM は曖昧な要求の理解・構造化・説明のみ、探索 / DP / スケジューリング / 制約判定 / 数値最適化はすべて決定論的な Algorithm Engine が担う。この責務分離が再現性・制約遵守・検証可能性・アルゴリズム比較(NFR-1〜5)を生む。
- **共通スキーマはハイブリッド型。** `objectives` / `constraints` は全 problem_type 共通の型付き語彙、`data` / `assignments` は `problem_type` を判別子にした判別可能ユニオン。ジェネリックな dict(型の恩恵ゼロ)と problem_type ごとの別モデル(共通エンジンを持てない)の中間を取る。
- **`domain/` と `algorithms/` を純粋レイヤーとして新設**(I/O・DB・時刻・乱数を持たない)。DB 不要の高速な純粋関数テストと再現性の源泉。
- **Validation(問題定義の妥当性)と Verification(解の制約充足)を別サービスに分ける。** 対象・タイミング・失敗の HTTP ステータスが違う。制約違反の解は例外にせず `status="invalid"` な候補として返す。

詳細: `textbook/Phase-0/Phase-0-introduction.md`

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

### 設計のポイント

- **`AlgorithmStrategy` は `typing.Protocol`**(継承を強制しない)。手実装・ライブラリラッパー・テストフェイクが同じ契約に乗る。`registry` が `problem_type` → 候補アルゴリズムを引き、アルゴリズム追加は 1 行(開放閉鎖)。
- **`solve` は解の生成だけを担い、制約充足を判定しない。** 近似アルゴリズムの制約違反を「バグ」でなく `status=invalid` な候補として測れる(Phase 3 比較の土台)。
- **2 層に分ける。** 問題まるごとを解く `AlgorithmStrategy`(registry 搭載)と、部品・技法(二分探索・BFS / DFS・Union-Find・Floyd-Warshall 等)の**アルゴリズム・プリミティブ**(素の純粋関数、registry 非搭載)。
- **`select_strategy` は純粋な `registry` でなく services 層に置く。** `NoAlgorithmError`(`AppError` 派生)を送出するため。`algorithms → services` の逆流を防ぐガードレール。

詳細: `textbook/Phase-1/Phase-1-introduction.md`

---

## Phase 2 — Validation / Constraint Engine

**目的：入力と制約を検証する**

- Pydantic Validation
- Constraint Validation
- Constraint Checker
- Solution Verification
- Invalid Solution Handling

### 設計のポイント

- **Phase 1 の route 限定 V&V 骨格を全 problem_type・全 constraint kind へ一般化する。** problem_type ごとの `SEMANTIC_CHECKS`、kind ごとの `CHECKERS` をレジストリ化し、2 サービスは「レジストリを回すオーケストレーション」に縮小。
- **到達可能性は「計算」なので `algorithms/` に置く**(`route_reachable` = 隣接リスト構築 + BFS)。判定は services、純粋述語(端点チェック等)は `domain/problems/semantic.py`。`domain → algorithms` の import 禁止が「これは計算か述語か」を写経中に問い直させる。
- **shift の V&V は Phase 2 で作る**(shift strategy 本体は Phase 5)。`POST /verify` が手組み shift 解の実消費者になり、検証器を先に凍結すれば Phase 5 はアルゴリズムに専念できる。
- **`status="invalid"` はエラーでなく結果。** `solve` / `verify` とも 200 を返し、invalid 解も永続化する(監査証跡 / Phase 3 の「この近似は N% 制約を破る」測定)。

詳細: `textbook/Phase-2/Phase-2-introduction.md`

---

## Phase 3 — Benchmark

**目的：アルゴリズムを定量評価できる基盤を作る**

- 実行時間計測
- 操作回数
- メモリ使用量
- 入力サイズ別比較
- アルゴリズム比較UI
- 可視化

### 設計のポイント

- **「計算できる + 検証できる」が揃って初めて「測って比較できる」**(Phase 順序の原則 2)。かつ Phase 4 / 5 が 1 問題に複数アルゴリズムを載せる前に、比較の基準を用意しておく必要がある。
- **Phase 0 で確定した 6 指標**(実行時間 / 操作回数 / メモリ / 入力サイズ別カーブ / 解の品質 / 制約違反数)を測る。操作回数は `solve()` 内で数えて `metrics["_ops"]` に返し(Phase 1 Dijkstra が種まき済み)、時間・メモリは外側の `measure_call`(`services/measurement.py`)が測る。`_ops` はアルゴリズム定義の単位なので直接比較はしない。
- **`BruteForceRouteStrategy`(全単純パス列挙)を registry の 2 本目**として登録。Dijkstra の最適性を小規模グラフで裏取りする正解オラクル兼、ベンチの比較相手になる。`benchmark_runs` テーブル(JSONB payload 中心、`Problem` への FK なし)と `numpy`(中央値・分位数の集計のみ)を追加。
- **`POST /api/v1/benchmark`** は Validation を通す(verify との違い ── 実際に解くため)。invalid 解も 200。
- 可視化は既存の手描き SVG を軸・凡例・対数軸に拡張し、初の `src/features/optimization/`(比較テーブル + グループ棒 + 入力サイズ曲線)を立ち上げる。本格的な図ライブラリの選定は Phase 4(経路 / ネットワーク図)へ。
- **分析トラック `decitima-api/analysis/` を新設**(pandas / matplotlib、dev 依存、`app` から切り離し)。`benchmark_runs` を「エクスポート → DataFrame」で集計・可視化する。コア層(`domain` / `algorithms` / solve 経路)には pandas を入れない。この `analysis/` は Phase 4/5/9/11/13(LLM vs Algorithm)/14 が育てる分析の背骨になる。

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

### 設計のポイント

- **最初の実ドメイン。Shift より先**にするのは、Phase 1 のグラフ資産を最大再利用でき新パラダイムを持ち込まないため(「グラフの深掘り」)。
- Bellman-Ford(負辺・負閉路検出)、A*(可容な heuristic が要る。`RouteNode` に座標 `x/y` を optional で持たせてあるのはこのため)を追加。
- **MST は新 `problem_type` `network_design` として追加**(Kruskal / Prim / Union-Find)。判別可能ユニオンにメンバーを足すだけで既存コードに一切触れない ── ハイブリッドスキーマ設計の狙いどおりの姿。
- 複数必須経由地(2 点以上 = 順列・小 TSP)を Phase 1 から先送りしてここで扱う。`networkx` を産業ソルバートラック兼**手実装 Dijkstra の検証オラクル**として導入。

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

### 設計のポイント

- **意図的に MVP の最後に置く。** 組合せ探索という新パラダイム + 多目的 + hard / soft 混在を一度に導入するため。
- **中心的課題 ── 手実装の破綻 → OR-Tools。** バックトラッキング / Branch and Bound は最悪指数時間で、中規模(スタッフ 20 × 7 日 × 3 スロット)で終わらない。同じ `AlgorithmStrategy` 契約の裏に **OR-Tools CP-SAT トラック**を用意する。この破綻点と CP-SAT 計画は Phase 0 で前倒し分析済みなので、Phase 5 は「既知の計画の実行」。
- Greedy(高速だが hard 違反 → `invalid` 候補)/ Backtracking(小規模で最適・大規模で指数)/ Branch and Bound を手実装トラックとして揃える。
- **`app/domain/objectives/`(重み付き和の評価器)を初実装**(消費者がいなかったので Phase 1 から先送り)。Sliding Window プリミティブもここで実装。検証器は Phase 2 で完成済みなので「アルゴリズムを書くだけ」。

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

### 設計のポイント

- **DP を実問題へ適用する。** Knapsack DP、Floyd-Warshall(訪問地間の全点対距離を**前処理**として計算する距離行列プリミティブ。Strategy ではない)、Greedy。
- `TravelData` / `TravelSolution` を判別可能ユニオンに追加。難易度単調増加のカリキュラム(Backtracking / B&B の次に Knapsack-DP / Floyd-Warshall)を継続する。

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

### 設計のポイント

- **グラフ / スケジューリングを工程管理へ適用する。** Task / Dependency / DAG モデル、Topological Sort、Critical Path、スケジュール生成、ガントチャート。
- 資源平準化に Difference Array(imos 法)プリミティブ。Phase 1 の DFS が Topological Sort の土台になる。

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

### 設計のポイント

- **1 問題で複数アルゴリズムを組み合わせる総合最適化。** Dijkstra / A*(経路)+ DP(積載)+ Greedy / TSP(配送順)+ Backtracking(制約)+ 複合的な制約検証。
- **ジョブキューを導入するとしたらここ**(それまでは YAGNI で同期実行 + タイムアウト)。MILP 化する場合は `pulp` / `scipy` を追加。

---

## Phase 9 — What-if Simulation

**目的：意思決定支援へ拡張する**

- 条件変更
- 複数シナリオ生成
- 結果比較
- Cost / Time / Quality比較
- Sensitivity Analysis

### 設計のポイント

- **意思決定支援レイヤーへ拡張する。** 条件変更 / 複数シナリオ生成 / Cost・Time・Quality 比較 / Sensitivity Analysis。`POST /simulate`。
- シナリオ = 一部の値を変えて複製した `OptimizationProblem`。**スキーマ自体は不変**のまま扱う。全ドメインが出そろった後に置く(シミュレーションする対象があるように)。

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

### 設計のポイント

- **LLM はここで初めて登場する。** 決定論的エンジンが信頼できるようになって初めて前段に置く(Phase 順序の原則 1。これが DeciTima の核心テーゼ)。
- **LLM 出力は常に信頼しない** ── 必ず Validation Layer を通す。LLM Service は本流の外に置き、スキーマ経由でのみ接続し、Algorithm Engine と直結させない。既存の LangGraph 構造化出力パターンを流用する。

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

### 設計のポイント

- **問題特性 → アルゴリズム候補の推薦は Rule Engine + LLM の併用**(LLM 単独ではない)。
- Phase 0 で設計した 3 段階セレクション(ルールベース → LLM 推薦 → ベンチマークベース)の「第 2 段」にあたる。

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

### 設計のポイント

- **LLM がアルゴリズムの結果を人間に説明する**(なぜこの解か / どの制約が効いたか / どのアルゴリズムか / 他候補との違い / 改善余地)。
- すべての `CandidateSolution` が必ず持つ `produced_by` + `metrics` + `violations` を消費する ── Phase 0 で敷いた説明可能性(NFR-4)の土台がここで回収される。

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

### 設計のポイント

- **プロジェクトの核心的な検証テーマ。** 同一データで「LLM Only」と「LLM → Validation → Algorithm → Verification」パイプラインを比較する。
- 制約遵守率 / 最適性 / 再現性 / 実行時間 / エラー率 / 検証可能性を実測。示したいのは「AI を使う」ではなく**「AI と決定論的アルゴリズムをどう組み合わせるか」**。

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

### 設計のポイント

- **Testing / Performance / Security / Deployment を実サービス品質へ仕上げる。**
- セキュリティ・インフラの多く(認証・レート制限・CORS・Docker・CI)は**テンプレートが既に足場を提供**しており、作り直さず再利用する。E2E は Playwright、API は GitHub Actions → Docker → VPS、UI は Vercel。

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
