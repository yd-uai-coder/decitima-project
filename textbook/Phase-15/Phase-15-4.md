# Phase 15-4: DBクエリ最適化監査(作業単位 15-4)

## この章のゴール

`OptimizationReadService`(Phase 1)の主要クエリを、実運用より大きな合成データに対して`EXPLAIN ANALYZE` で実測監査する。README §15「DB Query Optimization」。
**結論: 追加のインデックスは不要**(既存の設計で十分)── コード変更のない監査のみの章。

**この章で作成 / 更新するファイル**: なし(監査結果は本章と `CLAUDE.md` Notes に記録)。

---

## 1. 対象クエリ ── 所有者スコープ付き読み取り2本

`app/services/optimization_read.py::OptimizationReadService` の2つの読み取りメソッドを対象にする(頻度が高く、かつ JOIN やソートを含むため):

```python
# app/services/optimization_read.py(既存、抜粋)
async def get_solution(self, solution_id: uuid.UUID, *, user_id: uuid.UUID) -> Solution:
    stmt = (
        select(Solution)
        .join(Problem, Solution.problem_id == Problem.id)
        .where(Solution.id == solution_id, Problem.user_id == user_id)
    )
    ...

async def list_solutions_for_problem(
    self, problem_id: uuid.UUID, *, user_id: uuid.UUID
) -> list[Solution]:
    await self.get_problem(problem_id, user_id=user_id)
    stmt = (
        select(Solution).where(Solution.problem_id == problem_id).order_by(Solution.created_at)
    )
    ...
```

既存インデックス(`app/models/optimization.py`):`problems.user_id`・`problems.problem_type`・
`solutions.problem_id`・`solutions.algorithm_name` に `index=True`(いずれも Phase 1)。

## 2. 実測 ── 実運用よりかなり大きい合成データで `EXPLAIN ANALYZE`

開発環境の実データは数件しかなく、PostgreSQL のプランナは小さいテーブルでは常に
Seq Scan を選ぶため意味のある計測にならない。**トランザクション内で合成データを投入し、計測後に `ROLLBACK` して実データには一切影響を与えない**方法で実測した:

- problems: 20,000件(様々な user_id・problem_type に散らす想定)
- solutions: 1問題あたり1件を20,000件 + 「1問題に5,000件」という極端な worst case を1件

```sql
-- BEGIN; ... ROLLBACK; で囲み、実データには残らない
EXPLAIN ANALYZE
SELECT solutions.* FROM solutions
JOIN problems ON solutions.problem_id = problems.id
WHERE solutions.id = :id AND problems.user_id = :user_id;
-- => Nested Loop, Index Scan using solutions_pkey + problems_pkey, Execution Time: 1.98ms

EXPLAIN ANALYZE
SELECT * FROM solutions WHERE problem_id = :problem_id ORDER BY created_at;
-- (1問題に5,000件という worst case)
-- => Bitmap Index Scan using ix_solutions_problem_id, Sort(quicksort), Execution Time: 4.80ms
```

両クエリとも既存インデックスを正しく使い(`Index Scan`/`Bitmap Index Scan`、`Seq Scan`は出ない)、実運用よりかなり大きい規模(20,000問題、1問題に5,000解という非現実的なworst case)でも実行時間は数ミリ秒に収まった。

## 3. 結論 ── 追加インデックスは不要

`list_solutions_for_problem` の `ORDER BY created_at` に複合インデックス
(`problem_id, created_at`)を追加する案も検討したが、実測(5,000件でも4.8ms、クイックソートがメモリ内で完結)から見送り。実運用では1問題あたりのソリューション数は登録済みアルゴリズムの数(多くても十数件)にしかならないため、このワークロードでは既存の単一列インデックス + 実行時ソートで十分。README §15設計のポイント「テンプレートが既に足場を提供しており作り直さず再利用する」は、Phase 1 が最初から用意した
インデックス設計にもそのまま当てはまる ── 新規に追加するものは無い。

> **投機的な最適化をしない**: 複合インデックスの追加はデータ量に依存する判断であり、「将来大量のソリューションが1問題に紐づくようになったら」という仮定に基づく先回りの最適化は進行のルール #17 の「実在の消費者」テストに落ちる。実測で示された現在のワークロードには不要と判断し、見送る。

---

## まとめ

- `get_solution`(JOIN + id検索)/ `list_solutions_for_problem`(problem_id検索 + ソート)を実運用よりかなり大きい合成データ(20,000問題、1問題に5,000解の worst case)で実測した。
- 両クエリとも既存インデックスを正しく使い、数ミリ秒で完了する。
- 追加のインデックスは不要と判断した(コード変更なし)。

## テスト観点

本章はコード変更を伴わない監査のため専用テストは追加しない。監査に使った合成データは本番/開発データベースに残さないよう `BEGIN`/`ROLLBACK` で囲んで実行した(手順は本章§2)。

```bash
# 実測の再現(docker compose の postgres コンテナに対して。ROLLBACK するので安全)
docker compose exec postgres psql -U <user> -d <db> < <本章§2のSQL、BEGIN...ROLLBACKで囲む>
```

---

次章([Phase-15-5](./Phase-15-5.md))では非同期ワーカー(arq)の並行数をチューニングする。
