# Phase 1-0: 概観 ── 決定論的な計算基盤と solve ライフサイクル

## この章のゴール

Phase 0 は設計フェーズだった。Phase 1 は **その設計を実コードにする最初の Phase**。
README §19 Phase 1 の deliverable は「Binary Search / BFS / DFS / Dijkstra /
基本的な Algorithm Interface / Algorithm 実行 API / Unit Test」。

- Phase 1 で作る 7 つの作業単位の地図
- `POST /solve` が通るライフサイクル(どのレイヤーが何をするか)
- この Phase の進め方 ── 「実装 = samples の写経」
- samples ツリーの構造と検証方法
- Phase 1 のスコープと、Phase 2 に送るもの

対応サンプル: `samples/` 一式(`samples/README.md` に写経の対応表)。

---

## 1. Phase 1 が作るもの

Phase 0-9 §7 / `phase-0-index.md` の「実装前チェックリスト」で 7 単位に割ってある。
**章番号 = 作業単位番号**(この概観が `Phase-1-0`、以降 `Phase-1-M` が作業単位 1-M。進行のルール #2)。

| 単位 | 内容 | 章 | 依存 |
| --- | --- | --- | --- |
| 1-1 | 共通スキーマの実装(`app/domain/`) | [Phase-1-1](./Phase-1-1.md) | ― |
| 1-2 | `AlgorithmStrategy` プロトコル + `registry` + `select_strategy` | [Phase-1-2](./Phase-1-2.md) | 1-1 |
| 1-3 | 探索プリミティブ(Linear / Binary Search・BFS・DFS) | [Phase-1-3](./Phase-1-3.md) | ― |
| 1-4 | `DijkstraStrategy`(禁止エッジ・必須経由対応) | [Phase-1-4](./Phase-1-4.md) | 1-1, 1-2, 1-3 |
| 1-5 | `Problem` / `Solution` の ORM とリポジトリ + マイグレーション | [Phase-1-5](./Phase-1-5.md) | ― |
| 1-6 | `SolveService` + `POST /api/v1/solve` + 最小 Validation/Verification | [Phase-1-6](./Phase-1-6.md) | 1-1〜1-5 |
| 1-7 | `GET /algorithms` / `GET /solutions/{id}` ほか取得系 | [Phase-1-7](./Phase-1-7.md) | 1-5, 1-6 |

依存の無い 1-1 / 1-3 / 1-5 から着手できる。**単位ごとに `uv run ruff check .` と
`uv run pytest` を通してからコミット**(進行のルール、`Phase-0-9.md` §7)。

---

## 2. solve のライフサイクル

`POST /api/v1/solve` が来てからレスポンスを返すまで(`Phase-0-3.md` §3 の実装形)。

```text
① app/api/routes/solve.py         SolveRequest を受け取り、認証済みユーザーを取得
        │                          ルートは薄い ── サービスを呼んで詰めて返すだけ
        ▼
② app/services/solve.py  SolveService.solve()   ← トランザクション境界。ここで commit
        │
        ├ (a) RateLimiter(resource="solve").enforce(user_id)      既存 RateLimiter を再利用
        │
        ├ (b) ProblemValidationService.validate(problem)          NG は AppError で終了(計算しない)
        │        └ route: start/goal 存在・エッジ端点・到達可能性(BFS)
        │
        ├ (c) select_strategy(problem, requested)                 registry から候補を1つ選ぶ
        │        └ 該当なし → NoAlgorithmError(400)
        │
        ├ (d) strategy.solve(problem) → CandidateSolution         純粋な計算。副作用なし
        │        └ タイムアウトを監視(超過 → SolveTimeoutError, 504)
        │
        ├ (e) SolutionVerificationService.verify(problem, sol)    hard 違反 → status="invalid"
        │        └ 解は書き換えず新インスタンスを返す
        │
        ├ (f) persist=True なら Problem / Solution を保存(JSONB payload)
        │
        └ (g) await session.commit()
        │
        ▼
③ app/api/routes/solve.py         CandidateSolution → SolveResponse に詰めて返す
```

ポイント:

- **例外はルートで捕まえない**。`ProblemValidationError` / `NoAlgorithmError` /
  `SolveTimeoutError` はそのまま伝播し、既存の `register_error_handlers` が JSON 化する
  (`decitima-api/CLAUDE.md` のエラーハンドリング節)。
- **(d) の計算は純粋**。DB もネットワークも時刻も触らない。だから同じ入力で必ず同じ結果になり
  (NFR-1)、ユニットテストが DB なしで書ける。
- **解の制約違反は例外ではない**。`CandidateSolution.status="invalid"` として 200 で返す
  (`Phase-0-6.md` §4)。

---

## 3. レイヤーと責務(Phase 1 で増える部分)

```text
app/api/routes/{solve,algorithms,solutions}.py   HTTP 境界。薄い
        │
app/schemas/optimization.py                      リクエスト/レスポンスの型(domain を薄く包む)
        │
app/services/{solve,validation,verification,     ユースケース・トランザクション境界
              algorithm_selection,optimization_read}.py
        │
        ├──▶ app/domain/{problems,solutions,objectives}/   純粋。型と意味。副作用なし
        ├──▶ app/algorithms/{base,registry,search,graph}   純粋。決定論的な計算
        └──▶ app/repositories/optimization.py  ─▶  app/models/optimization.py
```

- `app/domain/` と `app/algorithms/` は **標準ライブラリ + Pydantic(+ 将来 networkx/ortools)
  しか import しない**。services / repositories / DB / HTTP / Redis / ai に依存しない
  (`Phase-0-3.md` §2.2)。この純粋性が再現性とテスタビリティを生む。
- `select_strategy` だけは registry(純粋)ではなく services 層に置く。理由は
  [Phase-1-2](./Phase-1-2.md) §3。

---

## 4. この Phase の進め方 ── 実装 = 写経

CL(Curriculum Loop)開発では **AI はコードを書かず、人間が手で実装する**。Phase 1 からは
進行のルール #3 のとおり:

1. 章(`Phase-1-*.md`)は**要点の抜粋**だけを載せる。
2. 動くコードは `samples/` にある(実 `app/` ツリーを鏡写しにした構造 + 絶対 import)。
3. ユーザーは samples から `decitima-api/backend/` へ**ファイル単位で写経・改変**する。
4. 実装中の疑問・改善点は Claude に質問・相談し、教材と samples に還流させる
   (進行のルール #8 / #9)。

```text
textbook/Phase-1/
├── phase-1-index.md          目的 / 章一覧 / サンプル一覧 / 実装前チェックリスト
├── Phase-1-0.md              概観(この章)
├── Phase-1-1.md 〜 1-7.md    各作業単位の解説
└── samples/
    ├── README.md             写経の対応表・検証手順・既存ファイルへの追記メモ
    ├── app/**                → decitima-api/backend/app/**
    ├── tests/**              → decitima-api/backend/tests/**
    └── alembic/versions/*.py → autogenerate の目視確認用
```

**着手前に `phase-1-index.md` の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 5. テストの階層(`Phase-0-9.md` §1 の再確認)

| レベル | 使うもの | Phase 1 で書くもの |
| --- | --- | --- |
| domain / algorithms(主戦場) | 素の pytest。DB 不要 | スキーマ / 探索プリミティブ / Dijkstra の純粋関数テスト |
| サービス層 | `db_session`(インメモリ SQLite)+ `FakeRedis` | `SolveService` / Validation / Verification |
| API | `httpx.AsyncClient` + 依存差し替え | `POST /solve` / `GET /algorithms` / `GET /solutions/{id}` の契約 |
| 統合(既定で除外) | 実 PostgreSQL(`docker compose up postgres`) | JSONB カラムの読み書き |

`samples/tests/` にすべて用意してある。全体像:

```bash
uv run pytest                 # unit + service + api(89 passed, 3 deselected)
uv run pytest -m integration  # 要 docker compose up postgres
```

---

## 6. Phase 1 のスコープと非スコープ

| Phase 1 でやる | Phase 2 以降に送る |
| --- | --- |
| 共通スキーマの型(route / shift の 2 problem_type) | `network_design` の型とアルゴリズム(Phase 4) |
| `AlgorithmStrategy` + registry + rule-based 選択の骨組み | LLM 推薦 / ベンチマークベース選択(Phase 11 / 3) |
| Linear/Binary Search・BFS・DFS(プリミティブ)、Dijkstra(Strategy) | Bellman-Ford / A* / MST(Phase 4)、Greedy / Backtracking(Phase 5) |
| **route 限定**の最小 Validation / Verification を solve に配線 | kind ごとの Checker 全実装 / shift の検証 / `POST /verify` / invalid 解ハンドリング(Phase 2) |
| `Problem` / `Solution` の永続化 | `verifications` テーブル(Phase 2)、`benchmark_runs`(Phase 3) |
| 同期実行 + タイムアウト | ジョブキュー(YAGNI。必要なら Phase 8) |

Validation / Verification を Phase 1 で**最小だが配線する**理由: README では Phase 2 だが、
`SolveService` のライフサイクル(`Phase-0-3.md` §3)にステージとして組み込まれており、
枠だけ先に通しておくと Phase 2 が「枠を埋める」作業になる。Phase 1 の実装は
route_planning に限定し、Phase 2 で shift と全 kind に広げる。

---

## 7. まとめ

- Phase 1 は Phase 0 の設計を実コードにする。7 作業単位、単位ごとに ruff / pytest を通してコミット。
- solve のライフサイクルは「レート制限 → Validation → strategy 選択 → 計算 → Verification →
  永続化 → commit」。計算部分だけが純粋、その外側が I/O。
- `app/domain/` と `app/algorithms/` は純粋レイヤー。これが再現性(NFR-1)とテスタビリティの源。
- 実装は samples の写経。着手前に `phase-1-index.md` のチェックリストで疑問を出し切る。
- Validation / Verification は Phase 1 では route 限定の最小実装。全 kind・shift は Phase 2。

次章([Phase-1-1](./Phase-1-1.md))では、作業単位 1-1 ── 共通スキーマを `app/domain/` に
実装する。
