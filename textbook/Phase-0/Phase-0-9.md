# Phase 0-9: テスト戦略・Docker 環境・Phase 1 への引き継ぎ

## この章のゴール

7 項目チェックリストの「7. Test Strategy」にあたる。加えて Phase 0 の締めとして、
Docker 環境の確認と、Phase 1 で着手する作業単位を整理する。

- テストの階層(何を、どのレベルで、何を使ってテストするか)
- プロパティベーステストの候補
- 既存 `conftest.py` の注意点
- Docker 環境は変更不要であることの確認
- 依存ライブラリ追加の Phase 別計画
- Phase 0 で入れた低リスク整備の一覧
- Phase 1 の作業分割

---

## 1. テストの階層

DeciTima のレイヤー(Phase 0-3)ごとに、適切なテストレベルが違う。

```
┌─────────────────────────────────────────────────────────┐
│ E2E（Phase 14）           playwright / ブラウザ           │
├─────────────────────────────────────────────────────────┤
│ API テスト                httpx + FastAPI TestClient      │
│                           実 PG/Redis は不要（サービスをモック可）│
├─────────────────────────────────────────────────────────┤
│ サービス層テスト           db_session（インメモリ SQLite）  │
│  SolveService / Validation / Verification                 │
├─────────────────────────────────────────────────────────┤
│ domain / algorithms テスト  純粋関数。DB も I/O も不要      │
│  ← ここが最も厚くなる。速い。数千ケース回せる              │
├─────────────────────────────────────────────────────────┤
│ 統合テスト（@pytest.mark.integration）実 PostgreSQL + Redis │
│  docker compose up postgres redis が必要。既定では走らない  │
└─────────────────────────────────────────────────────────┘
```

### 1.1 domain / algorithms ── 純粋関数テスト(主戦場)

`app/domain/` と `app/algorithms/` は副作用がない(Phase 0-3)。だから:

- DB フィクスチャ不要。`pytest` の素の関数でよい。
- 1 テスト 1ms 未満。入力を変えて何千ケースも回せる。
- **再現性(NFR-1)のおかげでテストが安定する**。同じ入力 → 同じ出力なので
  フレーキーにならない。

例(Phase 1 で書く):

```python
def test_dijkstra_finds_shortest_path():
    problem = build_route_problem(...)          # samples の build_problem 相当
    solution = DijkstraStrategy().solve(problem)
    assert solution.assignments.path_node_ids == ["A", "B", "C", "E"]
    assert solution.metrics["total_weight"] == 9

def test_dijkstra_respects_forbidden_edges():
    problem = build_route_problem(forbidden=["e_bd"])
    solution = DijkstraStrategy().solve(problem)
    assert "e_bd" not in solution.assignments.path_edge_ids
```

### 1.2 サービス層 ── `db_session` フィクスチャ

`SolveService` / `ProblemValidationService` / `SolutionVerificationService` は
DB に触れる(永続化)。既存 `conftest.py` の `db_session`(インメモリ SQLite)を使う。

```python
async def test_solve_service_persists_problem_and_solution(db_session):
    service = SolveService(db_session, fake_redis)
    result = await service.solve(user_id=..., request=SolveRequest(problem=...))
    assert result.problem_id is not None
    assert result.solution.status == "valid"
```

- Redis はフェイク(`fakeredis` or 手製スタブ)。レート制限のロジックだけ検証。
- JSONB カラムは SQLite では `JSON` にフォールバック(Phase 0-8)。

### 1.3 API テスト ── httpx

`POST /solve` のリクエスト/レスポンス契約、認証、エラーレスポンス形式を検証。
`SolveService` はモックしてよい(ルートが薄いことの確認が目的)。

### 1.4 統合テスト ── 実 PG + Redis

`@pytest.mark.integration`。既定では `pyproject.toml` の
`addopts = "-m 'not integration'"` で除外される。実行するには
`docker compose up postgres redis` してから `uv run pytest -m integration`。

DeciTima で統合テストにするもの:

- Alembic マイグレーションが実際に適用できる(`alembic upgrade head`)。
- JSONB カラムへの読み書きと部分検索が Postgres 上で動く。

---

## 2. プロパティベーステスト(Verification と相性が良い)

「どんな入力でも成り立つべき性質」を検証する。

| 性質 | 対象 |
| --- | --- |
| **valid な解は必ず全 hard 制約を満たす** | `SolutionVerificationService` ── ランダムな問題と、その正しい解を生成して verify したら violations が空 |
| **アルゴリズムの解は必ずスキーマ的に整合** | `path_edge_ids` の端点が連続している / `assignments` のスタッフ ID が実在する |
| **Dijkstra の解の total_weight は BFS(無重み化)以上・全探索以下** | 複数アルゴリズムの結果の関係 |
| **同じ問題を 2 回解くと完全に同じ解** | 再現性(NFR-1)の機械的検証 |

MVP では `hypothesis` の導入は必須ではない。まず「小さな入力生成関数を手で書いて
for ループで回す」で十分。`hypothesis` は Phase 3(ベンチマークで多様な入力が要る)で検討。

> **[Phase 3 で確定 ── `hypothesis` 見送り]** オラクルのプロパティテスト
> (「Dijkstra の total_weight == BruteForce の total_weight」)は
> `tests/fixtures/optimization.py::build_scaled_route_problem(n, seed)` の `seed` を
> `for seed in range(50)` で振る手書きジェネレータで足りた(§2 の「まず手で書く」方針どおり)。
> `hypothesis` の依存追加は入力生成が本当に複雑化する Phase まで遅延。詳細 `Phase-3-2.md`。

---

## 3. 既存 `conftest.py` の注意点(再掲・重要)

```python
# tests/conftest.py の冒頭
os.environ.setdefault("DATABASE_URL", "...")   # ← app モジュールの import より前
```

Python の import は一度実行するとキャッシュされる。`app.core.database` などが
本物の設定で先に import されると、あとから環境変数を上書きしても手遅れ。
**DeciTima のテストでも、`app.*` を import する前に環境変数を設定する順序を守る。**
新しい conftest(`tests/unit/` など)を足すときも同じ。

---

## 4. Docker 環境

**変更不要。** 既存の構成をそのまま使う。

| ファイル | 役割 | DeciTima での変更 |
| --- | --- | --- |
| `backend/Dockerfile` | 3 段(base → builder → runtime) | なし |
| `docker-compose.yml` | postgres / redis / backend / nginx(開発) | なし |
| `docker-compose.prod.yml` | 本番 | なし |
| `nginx/nginx.conf` / `nginx.prod.conf` | 開発(平文)/ 本番(TLS) | なし |

- 依存ライブラリを足したとき(`networkx` 等)は `uv.lock` が更新され、
  Docker イメージの再ビルドが必要になる。これは Phase 4/5 の話。
- `ENVIRONMENT=production` で Swagger/ReDoc が自動的に無効になる(既存)。

---

## 5. 依存ライブラリ追加の Phase 別計画

| ライブラリ | 追加 Phase | 用途 |
| --- | --- | --- |
| (なし) | Phase 0-3 | 手実装のみ。標準ライブラリ + 既存の Pydantic / SQLAlchemy |
| `numpy` | Phase 3 | ベンチマークの集計(中央値・分位点) |
| `pandas` / `matplotlib` | Phase 3(**分析トラック**) | `analysis/` で `benchmark_runs` を集計・可視化。runtime でなく `[dependency-groups].analysis` |
| `networkx` | Phase 4 | Route Planner の産業ソルバートラック + 手実装 Dijkstra の検証オラクル |
| `ortools` | Phase 5 | Shift Scheduler の CP-SAT トラック(中規模以上) |
| `hypothesis` | ~~Phase 3(検討)~~ 見送り | プロパティベーステストの入力生成 ── 手書きジェネレータで足りた(§2 のマーカー) |
| `pulp` / `scipy` | Phase 8(必要なら) | Logistics を MILP として定式化する場合 |

**原則**: 必要になる Phase まで `pyproject.toml` に足さない。

> **[Phase 3 で確定]** `numpy` は計画どおり Phase 3-1 で追加(`measure_call` の中央値・四分位
> 集計だけに使う。アルゴリズムの計算には使わない)。`hypothesis` は見送り(上記)。
> **`pandas` / `matplotlib` を Phase 3-7 で追加** ── ただし runtime の `[project].dependencies`
> ではなく `[dependency-groups].analysis`(dev)。`app/domain` `app/algorithms` や solve 経路には
> 一切入れず、`decitima-api/backend/analysis/`(`app` から切り離した分析トラック)専用。
> `analysis/` は Phase 4/5/9/11/13/14 が育てる器。入力アダプタ(CSV→Problem)は別レイヤーで
> Phase 5/7/8 送り。詳細 `Phase-3-7.md` / Notes Q18。
Phase 0 では `app/algorithms/` に手実装トラックの空パッケージだけ置く。

---

## 6. Phase 0 で入れた低リスク整備(実施済み)

textbook 執筆と並行して、`decitima-api` に次の低リスクな整備を入れた。
詳細はルート `CLAUDE.md` の Notes を参照。

| 整備 | 内容 |
| --- | --- |
| chat ルート無効化 | `app/api/routes/__init__.py` の集約から `chat_router` を除去。`app/ai/` とモデルは Phase 10 の土台として保持 |
| 空パッケージ骨子 | `app/domain/{problems,constraints,objectives,solutions}/` と `app/algorithms/{search,graph,optimization,scheduling,patterns}/` の `__init__.py`(docstring のみ) |
| リブランド(最小) | `settings.PROJECT_NAME` の既定を `"DeciTima API"` に |
| `decitima-api/CLAUDE.md` 更新 | 「DeciTima 固有レイヤー」節を追加 |

**スキーマ・インターフェースの実装コードは入れていない。** それは Phase 1。

---

## 7. Phase 1 への引き継ぎ ── 作業分割

README の Phase 1 deliverable(Binary Search / BFS / DFS / Dijkstra / Algorithm
Interface / 実行 API / Unit Test)を、検証可能な単位に割る。

| # | 作業単位 | 完了の目安 |
| --- | --- | --- |
| 1-1 | `app/domain/` にスキーマ実装(`samples/problem_schema.py` を整理・分割) | Pydantic モデルが import でき、`samples/*_example.py` 相当の test が通る |
| 1-2 | `app/algorithms/` に `AlgorithmStrategy` Protocol + `registry` | `select_strategy` が動く。ダミー strategy で疎通 |
| 1-3 | 手実装 Binary Search / BFS / DFS + unit test | 各アルゴリズムの正常系・境界の test がグリーン |
| 1-4 | 手実装 Dijkstra(+ 必須経由・禁止エッジ対応)+ unit test | `route_planner_example` の期待解が出る |
| 1-5 | `app/models/optimization.py` + Alembic マイグレーション | `alembic upgrade head` が通る。統合テストで CRUD |
| 1-6 | `SolveService` + `POST /api/v1/solve` + API テスト | Route Planner の問題を投げて検証済みの解が返る |
| 1-7 | `GET /algorithms` / `GET /solutions/{id}` | registry の一覧と保存済み解の取得 |

各単位ごとに `uv run ruff check .` と `uv run pytest` を通してからコミット。

---

## 8. Phase 0 全体のまとめ

| 章 | 何を決めたか |
| --- | --- |
| 0-1 | DeciTima は最適化問題を共通の土台に。LLM は理解・構造化・説明のみ。MVP は Phase 0〜5。検証題材は Route Planner と Shift Scheduler |
| 0-2 | 共通スキーマはハイブリッド型。`objectives`/`constraints` は共通語彙、`data`/`assignments` は problem_type 判別子付きユニオン |
| 0-3 | `domain/`(純粋なスキーマと制約チェッカー)と `algorithms/`(純粋な計算)を新設。solve のライフサイクルを定義 |
| 0-4 | 全アルゴリズムが `AlgorithmStrategy` Protocol に従う。registry で problem_type → 候補。2 トラックは `implementation` で区別 |
| 0-5 | Dijkstra は多項式時間、Shift のバックトラッキングは中規模で破綻 → CP-SAT トラックを計画。Phase 3 の測定項目を確定 |
| 0-6 | Validation(問題の妥当性)と Verification(解の制約充足)を分離。hard→invalid / soft→penalty。`AppError` 派生を追加 |
| 0-7 | `POST /solve` を軸に MVP エンドポイントを絞る。Route/Shift の専用 API は作らない。既存の認証・レート制限を再利用 |
| 0-8 | JSONB 中心 + 検索キーのみカラム化。ORM は既存パターン踏襲。新モデルは `__init__.py` と `env.py` の両方に登録 |
| 0-9 | domain/algorithms の純粋関数テストが主戦場。Docker は変更不要。依存追加は Phase 単位で遅延。Phase 1 の作業を 7 単位に分割 |

Phase 0 の成果物は「設計」。次は「Phase 1 を開始する」で、この設計を
決定論的な計算基盤として実装していく。
