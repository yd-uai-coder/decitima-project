# Phase 2 — Validation / Constraint Engine(実装フェーズ)導入

作業章(`Phase-2-1.md` 以降)を始める前に、この 1 本で Phase 2 の全体像を掴む。
目的 / solve・verify のライフサイクル上の位置 / レイヤー / 進め方 / テスト / スコープ /
章一覧 / 実装前チェックリスト。

---

## 1. このフェーズの目的

Phase 1 は `POST /api/v1/solve` に **route 限定の Validation / Verification 骨格**(walking skeleton)を通した。Phase 2 はその骨格を **全 problem_type・全 kind へ一般化**する。
README §19 の依存連鎖では「Phase 1 の route 限定 V&V を全 kind・shift へ一般化する」がこのフェーズの定義そのもの。

Phase 1 が意図的にスタブにした 3 箇所を埋める:

| Phase 1 の状態                                                                                    | Phase 2 での姿                                                                               |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `validation.py` は `isinstance(problem.data, RouteData)` のハードコード分岐。shift は素通し                   | problem_type ごとの検査を `domain/problems/semantic.py` の `SEMANTIC_CHECKS` レジストリに集約。shift も検証  |
| `verification.py` の `_CHECKERS` は `forbidden` / `required_inclusion` の 2 つだけ。チェッカーは同ファイルにインライン | `domain/constraints/` に kind ごとのチェッカー + `CHECKERS` レジストリ。`numeric_bound` / `staffing` を追加 |
| shift 解を検証する術がない                                                                               | `domain/solutions/structure.py` の `verify_shift_structure`(可用性・労働時間・連続勤務・希望休・metrics)     |

さらに **`POST /api/v1/verify`**(解だけ持ち込んで検証)と、**Invalid Solution Handling**
(`status="invalid"` の解を「エラーでなく結果」として扱う導線)を仕上げる。

> **shift の V&V をなぜ Phase 2 で作るか**(Phase 1 の objectives 撤回とは扱いが違う)
> objectives(重み付き和の評価器)は「探索中に解を採点する機構」で、消費するアルゴリズムが無ければ意味がないため Phase 5 送りにした。Validation / Verification は **事前 / 事後の純粋なチェック**で、Phase 1 で凍結済みのデータモデル(`ShiftData` / `ShiftSolution` /`StaffingConstraint`)に対して働く。`POST /verify` は手組みの `ShiftSolution` を検証する実消費者になる。shift を解く strategy(Greedy / Backtracking)は Phase 5 のままだが、検証器はここで揃える ── Phase 5 は「アルゴリズムを書く」ことだけに集中できる。

---

## 2. solve と verify のライフサイクル

### `POST /api/v1/solve`(Phase 1 から。Phase 2 で (b)(e) の中身が厚くなる)

```text
① routes/solve.py       SolveRequest 受領、認証
        ▼
② SolveService.solve()   ← トランザクション境界。ここで commit
        ├ (a) RateLimiter(resource="solve").enforce(user_id)
        ├ (b) ProblemValidationService.validate(problem)      ★Phase 2: 全 problem_type
        │        route: 端点・エッジ端点(整合) + 到達可能性(BFS)
        │        shift: スロット参照・人数実行可能性・スキル・週上限
        │        整合 NG → ProblemValidationError(400) / 原理的に不能 → InfeasibleProblemError(400)
        ├ (c) select_strategy(problem, requested)
        ├ (d) strategy.solve(problem) → CandidateSolution     純粋・タイムアウト監視
        ├ (e) SolutionVerificationService.verify(problem, sol) ★Phase 2: 構造検証(route+shift)
        │        + metrics enrich + kind ディスパッチ(CHECKERS)
        │        hard 違反 → status="invalid" / soft 違反 → soft_penalty
        ├ (f) persist(invalid でも保存する)
        └ (g) commit
        ▼
③ routes/solve.py       SolveResponse(解 + id)。invalid でも 200
```

### `POST /api/v1/verify`(Phase 2 新規)

```text
① routes/verify.py       VerifyRequest(problem + solution)受領、認証
        ▼
② VerifyService.verify()  DB を触らない(永続化しない)
        ├ RateLimiter(resource="verify").enforce(user_id)
        └ SolutionVerificationService.verify(problem, solution)   ← solve と同じ検証器
        ▼
③ routes/verify.py       VerifyResponse(status / violations / metrics)。invalid でも 200
```

- **Validation は verify では走らせない** ── 「解けるか」ではなく「この解が条件を満たすか」を見るため(`Phase-0-7.md` §3.2)。
- **解の制約違反は例外ではない**。`status="invalid"` として 200 で返す(`Phase-0-6.md` §4。`VerificationFailedError` は作らない)。

---

## 3. レイヤーと責務(Phase 2 で増える部分)

```text
routes/{solve,verify}.py
        │
schemas/optimization.py           SolveRequest/Response, VerifyRequest/Response
        │
services/{solve, verify,          ユースケース・トランザクション境界
          validation, verification}
        │   validation.py / verification.py は Phase 2 で「純粋なオーケストレーション」に縮小
        │
        ├──▶ domain/problems/semantic.py      SEMANTIC_CHECKS レジストリ(純粋)
        ├──▶ domain/constraints/               CHECKERS レジストリ + kind ごとのチェッカー(純粋)
        ├──▶ domain/solutions/structure.py    verify_route_structure / verify_shift_structure(純粋)
        └──▶ algorithms/graph/dijkstra.py, algorithms/search/bfs.py   route 到達可能性のみ
```

- **`domain/` は `algorithms/` を import しない**。両方とも純粋だが、`algorithms → domain` の一方向を保つ(`Phase-0-3.md` §2.2)。そのため route の「到達可能性」検査(`build_adjacency`と BFS が要る)だけは `domain/problems/semantic.py` に置かず、`services/validation.py` に残す。**この 1 点が『どの層に何を置くか』を実際に決めた例** ── 各章のテスト観点で言語化する。
- **2 つのサービスがレジストリ上のオーケストレーションになる**:
  `validation.py` は `SEMANTIC_CHECKS` を回すだけ、`verification.py` は
  「構造検証 → metrics enrich → `CHECKERS` ディスパッチ → hard/soft 集計」だけ。
  検証ロジックの本体は全部 `domain/` にある。`algorithms/registry.py` と同じ発想。

---

## 4. 章一覧(章 = 作業単位)

`Phase-2-M.md` = 作業単位 2-M。旧 `Phase-1-7.md` §5 の 7 単位表から、`verifications` テーブル
(旧 2-7)を落として **6 章**にした(理由は §7)。依存の薄い 2-1 から着手できる。

| 章                           | トピック                                           | 依存       | 主な内容                                                                                                                                                 |
| --------------------------- | ---------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-2-1](./Phase-2-1.md) | Input Validation の拡充(Pydantic)                 | ―        | `ShiftSlot` に `end_hour > start_hour` の `model_validator` と `day` の ISO 日付 `field_validator`、`ShiftData` に id 重複を弾く `model_validator`。純粋な値オブジェクト、422 |
| [Phase-2-2](./Phase-2-2.md) | Semantic Validation の一般化                       | 2-1      | `domain/problems/semantic.py`(`SemanticIssue` / route・shift の検査関数 / `SEMANTIC_CHECKS`)、`services/validation.py` をレジストリ駆動に改訂、到達可能性は services に残す理由    |
| [Phase-2-3](./Phase-2-3.md) | Constraint Checker 全実装 + `domain/constraints/` | 2-2      | kind ごとのチェッカー 4 ファイル + `CHECKERS` レジストリ、`domain/solutions/structure.py`(構造検証を services から移設)、`services/verification.py` をオーケストレーションに縮小               |
| [Phase-2-4](./Phase-2-4.md) | Verification(shift)                            | 2-3      | `verify_shift_structure` ── 人数・可用性・スキル・週勤務時間・連続勤務日数(hard)、希望休(soft)、`labor_cost` / `day_off_satisfaction`(metrics)。手組み `ShiftSolution` fixture でテスト  |
| [Phase-2-5](./Phase-2-5.md) | `POST /api/v1/verify`                          | 2-3      | `VerifyRequest` / `VerifyResponse`、`VerifyService`、`routes/verify.py`、`verify_router` の集約、`resource="verify"` のレート制限                                 |
| [Phase-2-6](./Phase-2-6.md) | Invalid Solution Handling                      | 2-3, 2-5 | `status="invalid"` の解が solve / verify を 200 で通る導線、`Solution.status` カラムへの保存(スキーマ変更なし)、`GET /solutions/{id}` での読み出し                                   |

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1 と同じ)

1. 章(`Phase-2-*.md`)は **要点の抜粋** だけ。動くコードは `samples/`(実 `app/` ツリー鏡写し +絶対 import)。
2. `samples/` から `decitima-api/backend/` へ **ファイル単位で写経・改変**。
3. `samples/` には **Phase 2 で新規に作るファイルだけ**。既存ファイルへの追記
   (`app/core/config.py` / `app/api/routes/__init__.py`)と、Phase 1 のファイルを Phase 2 が書き換えるもの(`app/services/{validation,verification}.py` /
   `app/domain/problems/shift_scheduler.py` / `tests/fixtures/optimization.py` /
   `tests/unit/test_{validation,verification}_service.py`)は、**現行版を `samples/` に置き**、Phase 1 側の該当ファイルには `# [Phase 2 改訂]` マーカーを付けて現行版へ誘導する
   (進行のルール #12)。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる。

```text
textbook/Phase-2/
├── Phase-2-introduction.md   この導入
├── Phase-2-1.md 〜 2-6.md     各作業単位の解説
└── samples/
    ├── README.md             写経の対応表・overlay 検証手順
    ├── app/**                → decitima-api/backend/app/**
    └── tests/**              → decitima-api/backend/tests/**
```

**着手前に §10 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層(`Phase-0-9.md` §1 の再確認)

| レベル         | 使うもの                              | Phase 2 で書くもの                                                                |
| ----------- | --------------------------------- | ---------------------------------------------------------------------------- |
| domain(主戦場) | 素の pytest。DB 不要                   | `semantic.py` の検査関数 / `constraints/` のチェッカー / `structure.py` の構造検証           |
| サービス層       | `db_session`(SQLite)+ `FakeRedis` | `ProblemValidationService` / `SolutionVerificationService` / `VerifyService` |
| API         | `httpx.AsyncClient` + 依存差し替え      | `POST /verify` の契約、`POST /solve` が invalid 解を返す契約                            |

Phase 2 の domain は **すべて純粋関数**。スタブが 1 つも要らない ── これが「純粋レイヤー」設計
(`Phase-0-3.md`)の帰結で、各章のテスト観点で毎回確認する。

```bash
uv run pytest      # unit + service + api(overlay end 状態で 121 passed, 3 deselected)
```

---

## 7. Phase 2 のスコープと非スコープ

| Phase 2 でやる                                                                                    | 送る先                                                 |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 全 problem_type の Semantic Validation                                                           | ―                                                   |
| kind ごとの Constraint Checker(`forbidden` / `required_inclusion` / `numeric_bound` / `staffing`) | `network_design` の制約(Phase 4)、目的別の重み付き評価(Phase 5)   |
| shift 解の構造検証と metrics(`labor_cost` / `day_off_satisfaction`)                                   | shift を解く strategy = Greedy / Backtracking(Phase 5) |
| `POST /api/v1/verify`                                                                          | `POST /benchmark`(Phase 3)                          |
| Invalid Solution Handling(API 表現・保存)                                                           | invalid 解の UI 表示(UI 実装フェーズ)                         |
| ―                                                                                              | **`verifications` テーブル** ── 作らない(下記)                |

**`verifications` テーブルを作らない理由**: 検証結果(`status` / `violations` / `soft_penalty`
/ metrics)は Phase 1 の `Solution.status`(カラム)+ `Solution.payload`(JSONB)に既に入る。
MVP(Phase 0〜5)に「hard 違反した解だけ集計」のような payload 内クエリ需要は無く、取得はすべて id / 実カラム経由(`Phase-0-8.md` §4、Notes Q12)。README §19 の Phase 2 にもこのテーブルは無い。`benchmark_runs`(Phase 3)を作るとき、または実際にそのクエリ需要が出たときに消費者と一緒に切り出す。ORM / マイグレーション / リポジトリは Phase 2 では **一切触らない**。

---

## 8. サンプルコード(`samples/`)

| 場所                                                                                         | 内容                                                                            |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `app/domain/problems/semantic.py`                                                          | Semantic Validation(新規)                                                       |
| `app/domain/problems/shift_scheduler.py`                                                   | ShiftSlot / ShiftData の validator(Phase 1 のファイルを Phase 2 が改訂した現行版)            |
| `app/domain/constraints/{__init__,forbidden,required_inclusion,numeric_bound,staffing}.py` | kind ごとのチェッカー + `CHECKERS`(新規。`__init__.py` は Phase 0 の stub を置き換え)           |
| `app/domain/solutions/structure.py`                                                        | `verify_route_structure` / `verify_shift_structure` / `structural_verify`(新規) |
| `app/services/{validation,verification}.py`                                                | オーケストレーションに縮小した現行版                                                            |
| `app/services/verify.py` / `app/api/routes/verify.py`                                      | verify ユースケースとルート(新規)                                                         |
| `app/schemas/optimization.py`                                                              | Phase 1 の内容 + `VerifyRequest` / `VerifyResponse`                              |
| `tests/**`                                                                                 | domain / service / api の各テスト                                                  |

既存ファイルへの追記(samples に含めない、各章に差分):
`app/core/config.py`(`VERIFY_RATE_LIMIT_PER_HOUR`)、`app/api/routes/__init__.py`(`verify_router`)。

検証: `decitima-api/backend` に Phase 1 end 状態を作り、Phase 2 samples を overlay して
`uv run pytest`(121 passed, 3 deselected)/ `ruff check` / `ruff format --check`(clean)/
`uvx pyright`(0 errors)を確認済み(手順は `samples/README.md`)。

---

## 9. Phase 2 の成果物

- **textbook**: この `Phase-2/` 一式(導入 + `Phase-2-1`〜`2-6` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/domain/problems/semantic.py` /
  `app/domain/constraints/**` / `app/domain/solutions/structure.py` /
  `app/services/{validation,verification,verify}.py` の改訂・新規 / `app/api/routes/verify.py` /
  `app/schemas/optimization.py`・`app/core/config.py`・`app/api/routes/__init__.py` への追記 /
  `app/domain/problems/shift_scheduler.py` の validator / `tests/**`
- **Phase 1 / Phase 0 教材への `[Phase 2 改訂]` マーカー**
- **ルート CLAUDE.md の Notes**: Phase 2 の設計決定 + 質問ログ Q14

---

## 10. Phase 2 実装前チェックリスト

進行のルール #11。教材生成後・実装着手前に、ここで疑問を出し切る。行 `2-M` ↔ 章 `Phase-2-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                       | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                                                                   | テスト観点                                                                                                                                                                                                                                 |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2-1 | `app/domain/problems/shift_scheduler.py`(改訂)                                                                                                                                       | `ShiftSlot._end_after_start`(model_validator)/ `ShiftSlot._day_is_iso_date`(field_validator)/ `ShiftData._unique_ids`(model_validator。slot / staff の id 重複を弾く)                                                                                                                                                                                                     | 正常構築 / `end_hour <= start_hour` で `ValidationError` / 非 ISO 日付で `ValidationError` / 単項値域は `Field` が担う / id 重複で `ValidationError`                                                                                                      |
| 2-2 | `app/domain/problems/semantic.py`(新規)、`app/services/validation.py`(全面改訂)                                                                                                           | `SemanticIssue`(message, infeasible)/ route: `check_route_endpoints` / `check_route_edge_endpoints` / shift: `check_shift_slot_refs` / `check_shift_staffing_feasible` / `check_shift_skill_coverage` / `check_shift_weekly_hours_cover` / `SEMANTIC_CHECKS` レジストリ / `ProblemValidationService.validate`(レジストリを回す + route 到達可能性のみ services に残す)                    | route: 未知 start で `ProblemValidationError` / 到達不能で `InfeasibleProblemError` / shift: 未知スロット参照で `ProblemValidationError` / 適格スタッフ不足で `InfeasibleProblemError` / 正常な route・shift は通過                                                    |
| 2-3 | `app/domain/constraints/{__init__,forbidden,required_inclusion,numeric_bound,staffing}.py`(新規)、`app/domain/solutions/structure.py`(新規)、`app/services/verification.py`(全面改訂)        | `check_forbidden` / `check_required_inclusion`(services から移設、非 route 解は素通し)/ `check_numeric_bound`(`metrics[field]` を `operator value` と比較)/ `check_staffing`(スロット人数 = required_headcount)/ `CHECKERS` レジストリ / `verify_route_structure` / `structural_verify`(解の型でディスパッチ)/ `SolutionVerificationService.verify`(構造検証 → metrics enrich → `CHECKERS` → hard/soft 集計) | `CHECKERS` に 4 kind / `numeric_bound` 充足で None・違反で `ConstraintViolation`・metrics 欠落で素通し / `forbidden` は非 route 解で None / route の禁止エッジ・必須ノード欠落で `invalid` / `numeric_bound(total_weight)` で `invalid` / 元の解を書き換えない / `infeasible` は素通し |
| 2-4 | `app/domain/solutions/structure.py` の `verify_shift_structure`、`tests/fixtures/optimization.py`(`build_shift_solution` / `build_infeasible_shift_problem`)                         | `verify_shift_structure`(割当実在 id / 可用性 / 必要スキル / 週勤務時間 ≤ `max_weekly_hours` / 連続勤務日数 ≤ `max_consecutive_days` は素の日次スキャン=hard、希望休=soft、`labor_cost` / `day_off_satisfaction`=metrics)                                                                                                                                                                               | 有効な shift 解は `valid` で metrics 計算 / 人数不足で `invalid`(staffing) / 非 available スロット割当で `invalid` / 週上限超過で `invalid` / 連続勤務超過で `invalid` / 希望休は soft で penalty 加算・`day_off_satisfaction` 反映                                               |
| 2-5 | `app/schemas/optimization.py`(追記)、`app/services/verify.py`(新規)、`app/api/routes/verify.py`(新規)、`app/core/config.py`(追記)、`app/api/routes/__init__.py`(追記 ── `verify_router` の集約。#15) | `VerifyRequest`(problem + solution)/ `VerifyResponse`(status / violations / metrics)/ `VerifyService.verify`(レート制限 → 検証。DB なし)/ 薄いルート                                                                                                                                                                                                                              | route 有効解で 200・`status="valid"` / 禁止エッジ使用解で 200・`status="invalid"` / shift 有効解で 200・`labor_cost` metrics / shift 人数不足で 200・`status="invalid"` / 認証なしで 401                                                                             |
| 2-6 | `tests/api/test_solve_invalid.py`(新規)。プロダクションコードの新規追加なし                                                                                                                            | solve は hard 違反解を 200 + `status="invalid"` で返す(例外にしない)。invalid でも `Solution.status` カラムに保存され `GET /solutions/{id}` で読める                                                                                                                                                                                                                                            | `numeric_bound(total_weight <= 8)` の route 問題を solve → 200・`status="invalid"`・`violations` に `numeric_bound`・`problem_id`/`solution_id` あり / `GET /solutions/{id}` の `status` が `"invalid"`                                           |

各単位ごとに `uv run ruff check .` と `uv run pytest` を通してからコミット。

---

## 11. 次のフェーズ

Phase 2 完了後、「Phase 3 を開始する」で **Benchmark**(`POST /benchmark`、複数アルゴリズムの
実測比較、`benchmark_runs` テーブル、`numpy` 導入)の教材を生成する。Phase 2 で「同一
インターフェース・同一スキーマの下で解の品質(status / violations / metrics)を測る」土台が
揃うので、Phase 3 はそれを複数アルゴリズムに並べるだけになる。
