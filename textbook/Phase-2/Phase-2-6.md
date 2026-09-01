# Phase 2-6: Invalid Solution Handling(作業単位 2-6)

## この章のゴール

`README.md` §6 / §10 / §22 の「検証に失敗した解は **INVALID SOLUTION** として結果を採用しない」
を、DeciTima の API 契約として仕上げる。ここまでの章で仕組みはすべて揃っているので、この章は
**新しいプロダクションコードを書かない** ── 既存の導線が「invalid 解 = エラーではなく結果」に
なっていることを、テストで固定する。

Phase 0-6 §4 の設計判断(再掲):

> `VerificationFailedError` は**作らない**。解が制約を破っていても、それはエラーではなく
> `CandidateSolution.status="invalid"` として正常にレスポンスへ載せる(「アルゴリズムが失敗した」
> ではなく「この解は使えないと分かった」)。

**この章で新規作成するファイル**: なし(プロダクションコード)。
**テスト**: `samples/tests/api/test_solve_invalid.py`(新規)。
設計は `Phase-0-6.md` §4、`Phase-0-2.md` §6(`status` の 3 値)。

---

## 1. `status` の 3 値と、それぞれの扱い

| `status` | 意味 | HTTP | 保存 | violations |
| --- | --- | --- | --- | --- |
| `valid` | hard 制約をすべて満たす | 200 | する | soft のみ or 空 |
| `invalid` | hard 制約に違反(近似アルゴリズムの限界 / 制約をアルゴリズムが扱わない) | **200** | **する** | hard を含む |
| `infeasible` | 条件を満たす解が原理的に存在しない | 200(solve)/ 400(Validation が先に捕まえた場合) | する | ― |

**invalid でも保存する**理由(`Phase-0-8.md` §1): 再現性の証跡(NFR-1)、監査(NFR-4)、
Phase 3 で「このアルゴリズムは N% の確率で hard 制約を破る」を測るため。`Solution.status`
カラム(Phase 1 で用意済み)にそのまま入る ── **スキーマ変更なし**。

---

## 2. どうやって solve から invalid 解が出るか

Dijkstra は `forbidden` / `required_inclusion` を **自分で回避** して経路を作るので、route の
構造制約では invalid にならない。invalid 解が出るのは **アルゴリズムが扱わない制約** が
付いているとき:

```python
build_route_problem(forbidden=["e_bd"], max_total_weight=8)
# forbidden=e_bd → Dijkstra は A→B→C→E(w9)を出す
# NumericBoundConstraint(total_weight <= 8) → Dijkstra は無視 → Verification が invalid にする
```

パイプライン:
1. Validation: 端点 OK、到達可能(E は A から到達可能)→ 通過
2. `select_strategy` → dijkstra
3. `dijkstra.solve` → `RouteSolution`(w9)、`metrics={"total_weight": 9.0}`
4. `verify`: 構造検証 OK → `CHECKERS["numeric_bound"]`: `9.0 <= 8` が偽 → hard 違反 →
   `status="invalid"`
5. persist(`Solution.status = "invalid"`)、commit
6. `SolveResponse`(200)

これは `Phase-2-3` の `numeric_bound` チェッカーが `solve` 経由で end-to-end に効く最初の例
でもある。

---

## 3. UI への伝え方(方針のみ ── 実装は UI フェーズ)

`decitima-ui` に DeciTima 固有の画面はまだ無い。invalid 解の表示は将来の UI フェーズだが、
**API 契約として何を渡すか** は Phase 2 で決まる:

- `SolveResponse.solution.status` / `VerifyResponse.status` を見て `"invalid"` なら
  「この解は条件を満たしません」バナー
- `solution.violations[]` の `constraint_kind` / `message` / `detail` を違反リストとして表示
- `solution.metrics["soft_penalty"]` が > 0 なら「希望は一部満たせていません」

`decitima-ui/src/lib/api/` の `apiFetch` は 200 をそのまま返すので、invalid 解は
`try/catch` ではなく **通常のレスポンス** としてハンドリングする ── これが「エラーにしない」
設計の UI 側の帰結。

---

## 4. テスト観点(`samples/tests/api/test_solve_invalid.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `POST /solve` → `GET /solutions/{id}` の、invalid 解に対する契約
> - **ドライバ**: `httpx.AsyncClient`(`api` フィクスチャ)
> - **スタブ**: FastAPI 依存差し替え(`get_db` → SQLite、`get_redis` → `FakeRedis`)。
>   `DijkstraStrategy` と `SolutionVerificationService` は本物。

| ケース | 期待 |
| --- | --- |
| `numeric_bound(total_weight<=8)` の route 問題を solve | **200** / `solution.status == "invalid"` / `violations` に `numeric_bound` / `problem_id` と `solution_id` が返る(invalid でも永続化) |
| その `solution_id` で `GET /solutions/{id}` | 200 / `status == "invalid"`(カラムに保存されている) |

`uv run pytest tests/api/test_solve_invalid.py`。

---

## 5. まとめ

- `status="invalid"` は「エラー」ではなく「結果」。solve / verify とも 200 で返し、永続化する。
  `VerificationFailedError` は存在しない。
- invalid 解は `Solution.status` カラムに入る ── スキーマ変更なし、`GET /solutions/{id}` で
  読める。
- Dijkstra が扱わない制約(`numeric_bound` 等)が付いたとき、Verification が invalid にする ──
  「solve は検証しない / Verification が別」の設計がここで効く。
- UI 側は 200 レスポンスとして invalid をハンドリングする(実装は UI フェーズ)。

これで Phase 2 は完了。`Phase-2-introduction.md` の「次のフェーズ」を確認し、「Phase 3 を
開始する」で Benchmark(複数アルゴリズムの実測比較)の教材を生成する。
