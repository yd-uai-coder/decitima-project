# Phase 8-6: registry + select + cpm_nx オラクル + end-to-end(作業単位 8-6)

## この章のゴール

4 つ目の strategy `cpm_nx`(networkx の別実装オラクル)を作り、`registry["project_scheduling"]` に4 strategy をまとめて有効化、`select_strategy` に project 分岐を足す。ここで初めて**validate → select → solve → verify のフルパイプラインが緑**になる(進行のルール #15 ──
registry のキーは 8-6 でまとめて埋める。8-4 / 8-5 の strategy テストは `Strategy().solve()` を直接呼んでいた)。

**この章で作成 / 更新するファイル**:
`app/algorithms/scheduling/networkx_project.py`(新規)、`tests/unit/test_project_strategies.py`(新規)。
**既存への変更**(現行版は samples): `app/algorithms/registry.py`、`app/services/algorithm_selection.py`、
`tests/unit/test_algorithm_selection.py`(project 2 ケース追加。既存 assertion は不変)。

対応サンプル: `textbook/samples/app/algorithms/scheduling/networkx_project.py`、`textbook/samples/tests/unit/test_project_strategies.py`。設計は `Phase-4-6.md` / `Phase-5-4.md`(registry・select)。

---

## 1. `cpm_nx` ── networkx の DAG ユーティリティで CPM を別実装

```python
# app/algorithms/scheduling/networkx_project.py(要点。全文は samples)
import networkx as nx

class NetworkxCpmStrategy:
    meta = AlgorithmMeta(name="cpm_nx", family="scheduling", implementation="library:networkx", ...)

    def solve(self, problem):
        data = parse_project_problem(problem); dur = build_durations(data)
        graph = nx.DiGraph()
        graph.add_nodes_from(dur)
        graph.add_edges_from((d.predecessor, d.successor) for d in data.dependencies)
        if not nx.is_directed_acyclic_graph(graph):
            return infeasible_project_solution(self.meta)

        order = list(nx.topological_sort(graph))     # ← networkx の貢献(Kahn ベース)
        es = dict.fromkeys(order, 0)                  # 前進パス(手実装 cpm と同じ算術)
        for t in order:
            for s in graph.successors(t):
                es[s] = max(es[s], es[t] + dur[t])
        ...                                          # 後退パス → slack → critical_chain(8-2 を再利用)
        return project_solution(data, dict(es), result, self.meta, ops=None)
```

- **networkx の貢献は `nx.topological_sort` / `nx.is_directed_acyclic_graph` だけ**。CPM の前進 /
  後退パスの算術は手実装と同じ ── だから「トポロジカルソートの別実装(DFS vs Kahn)」と
  「CPM 算術の写経ミス」の両方を独立に検算できる。`critical_chain`(8-2 の公開関数)は presentation
  なので再利用する(route strategy が `reconstruct_path` を共有するのと同じ)。
- 資源は無視する(cpm と同じ「下界」)── networkx に RCPSP の仕組みは無い。資源つきの最適は `cp_sat`。
- `_ops` なし(ライブラリトラック)。

---

## 2. registry と select

```python
# app/algorithms/registry.py  # (Phase 8-6)
"project_scheduling": [
    CpmScheduleStrategy(),               # 手実装先頭 ── ?algorithm=cpm は手実装が当たる
    PriorityListScheduleStrategy(),
    OrToolsCpSatProjectStrategy(),
    NetworkxCpmStrategy(),
],

# app/services/algorithm_selection.py  # (Phase 8-6)
    if isinstance(data, ProjectData):
        # 資源制約あり → priority_list(資源 feasible な貪欲)。厳密は ?algorithm=cp_sat
        # 資源制約なし → cpm(純粋なクリティカルパス。O(V+E))
        return "priority_list" if data.resource_capacity is not None else "cpm"
```

- **手実装 4 strategy のうち先頭 = `cpm`**(進行のルール #15 の作法 ── `?algorithm=cpm` は
  `library:networkx` でなく手実装に当たる。ここは `cpm` と `cpm_nx` で `meta.name` が違うので
  Dijkstra / kruskal のような同名衝突は無いが、慣習に合わせる)。
- **`_preferred_name` の分岐**: 資源制約があれば `cpm` は必ず invalid になるので、既定を
  `priority_list`(常に feasible)にする。純粋 CPM でよければ `cpm`。厳密最適が要るときだけ
  `?algorithm=cp_sat` を明示 request(Phase 6 の shift → `?algorithm=cp_sat` と同じ運用)。

---

## 3. end-to-end と 4 者比較

```python
# tests/unit/test_project_strategies.py(要点。全文は samples)
def test_cpm_and_cpm_nx_agree_on_makespan_and_critical_tasks():
    for seed in range(6):
        problem = build_scaled_project_problem(n_tasks=10, seed=seed)
        hand, nx_sol = _plan(_CPM.solve(problem)), _plan(_NX.solve(problem))
        assert hand.makespan == nx_sol.makespan
        # 「どのタスクが余裕ゼロか」は両実装で一致(複数クリティカルパスは chain で 1 本に絞るので集合で)
        assert {s.task_id for s in hand.schedule if s.slack == 0} == \
               {s.task_id for s in nx_sol.schedule if s.slack == 0}
        assert hand.critical_path == nx_sol.critical_path   # tie-break も一致

def test_three_way_cpm_infeasible_priority_list_feasible_cpsat_optimal():
    problem = build_project_problem(resource_capacity=3)
    cpm_v   = verify(problem, select_strategy(problem, "cpm").solve(problem))
    pl_v    = verify(problem, select_strategy(problem, "priority_list").solve(problem))
    cpsat_v = verify(problem, select_strategy(problem, "cp_sat").solve(problem))
    assert cpm_v.status == "invalid"          # 資源超過
    assert pl_v.status == "valid" and cpsat_v.status == "valid"
    assert _plan(cpsat_v).makespan <= _plan(pl_v).makespan
```

- **`cpm_nx` が非制約 CPM のオラクル** ── 手実装 `cpm` と makespan / クリティカルタスク集合 /
  クリティカルパス(tie-break 込み)が完全一致。ランダム DAG 6 seed で回す。
- **3 者比較**が Phase 8 の教材の核の締め: `cpm`(資源無視 → invalid)/ `priority_list`(feasible)/
  `cp_sat`(最適 ≤ priority_list)。
- `numeric_bound` on `makespan`: `test_end_to_end_invalid_when_makespan_bound_violated` ──
  `makespan <= 5` を課すと Verification が invalid(既存の汎用チェッカーが `metrics["makespan"]` を
  読む。新チェッカー不要)。

---

## 4. まとめ

- `cpm_nx` = `nx.topological_sort` + 手実装と同じ CPM 算術。トポロジカルソートの別実装検算 +
  非制約 CPM のオラクル。`_ops` なし。
- `registry["project_scheduling"]` に 4 strategy をまとめて。手実装先頭。
- `select_strategy`: 資源制約あり → `priority_list` / なし → `cpm`。厳密は `?algorithm=cp_sat`。
- ここで初めて e2e パイプラインが緑。8-3 の `test_project_scheduling.py` は e2e を含まない。

## テスト観点(`textbook/samples/tests/unit/{test_project_strategies,test_algorithm_selection}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `REGISTRY["project_scheduling"]`、`select_strategy` の project 分岐、
>   `NetworkxCpmStrategy`、validate→select→solve→verify のパイプライン
> - **ドライバ**: このテスト関数 / fixture。各段を直接呼ぶ(`test_mst_strategies.py` と同型)
> - **スタブ**: **不要** ── strategy / validation / verification はすべて純粋(Redis は
>   `SolveService` の関心事で、ここでは各段を直接呼ぶ)。`test_algorithm_selection.py` は
>   実 REGISTRY を使い、既存の route / network / shift の assertion は不変(#16)

| ケース                                  | 期待                                                                        |
| ------------------------------------ | ------------------------------------------------------------------------- |
| `REGISTRY["project_scheduling"]` の名前 | `["cpm", "priority_list", "cp_sat", "cpm_nx"]` / 先頭 handwritten           |
| `select_strategy`(資源制約あり / なし)       | `"priority_list"` / `"cpm"`                                               |
| `select_strategy(_, "cp_sat")`       | `cp_sat` / `library:ortools`                                              |
| cpm ⟷ cpm_nx(ランダム DAG 6 seed)        | makespan / クリティカルタスク集合 / critical_path 一致                                 |
| `cpm_nx` の metrics                   | `"_ops"` を含まない                                                            |
| e2e パイプライン(資源制約なし)                   | `status == "valid"` / `produced_by.name == "cpm"`                         |
| 3 者比較(資源 capacity 3)                 | cpm = invalid / priority_list = valid / cp_sat = valid かつ ≤ priority_list |
| `makespan <= 5` を課す                  | `status == "invalid"`(汎用 numeric_bound チェッカー)                             |

`uv run pytest tests/unit/test_project_strategies.py tests/unit/test_algorithm_selection.py` /
`uvx pyright app`。

---

次章([Phase-8-7](./Phase-8-7.md))では、作業単位 8-7 ── Project Manager ページ(decitima-ui)。
`project-planner` フィーチャースライス(Phase 4-8 / 7-7 と同型)と、新規 `GanttCanvas`
(ドメイン非依存のタイムラインバー ── `GraphCanvas` と並ぶチャート)。依存 DAG は `GraphCanvas`
再利用、スケジュールは `GanttCanvas`、クリティカルパスは赤、資源超過は赤メッセージ。
