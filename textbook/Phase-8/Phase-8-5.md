# Phase 8-5: OR-Tools CP-SAT で RCPSP を厳密に解く(作業単位 8-5)

## この章のゴール

`priority_list`(8-4)の貪欲は資源制約を守るが、fixture では makespan 10 ── C を先に置いて D の置き場を塞ぐ「貪欲の近視眼」で最適(9)を外した。**厳密に最小の makespan** を求めるには、資源制約つきスケジューリング(RCPSP)を整数計画として解く ── **OR-Tools CP-SAT**。

> OR-ToolsはGoogle が提供している、**組合せ最適化問題を解くためのライブラリ**
> その中のCP-SAT は、**Constraint Programming（制約プログラミング） + SAT**を組み合わせた最適化ソルバー

手実装(cpm / priority_list)と**同じ `AlgorithmStrategy` 契約・同じ `ProjectSolution`**。
違うのは `implementation="library:ortools"` と、中身が CP-SAT の探索であること。
仕事がソルバーの中なので `_ops` は出さない ──「ライブラリトラックは操作回数を出せない」=2 トラック比較の観察点(Phase 6 CP-SAT / `Phase-0-4.md` / README §8)。

**`ortools` は Phase 6-7(Shift Scheduler)で `[project].dependencies` に追加済み** ──
pyproject の変更なし、`uv sync` 不要。

**この章で作成 / 更新するファイル**:
`app/algorithms/scheduling/ortools_project.py`(新規)、`tests/unit/test_cpsat_project.py`(新規)。
既存ファイルへの変更は無い。

対応サンプル: `textbook/samples/app/algorithms/scheduling/ortools_project.py`。
設計は README §8(2 トラック)、`Phase-6-7.md`(CP-SAT の骨)、OR-Tools CP-SAT の scheduling レシピ。

---

## 1. モデル ── interval var + cumulative

```python
# app/algorithms/scheduling/ortools_project.py(要点。全文は samples)
from ortools.sat.python import cp_model

class OrToolsCpSatProjectStrategy:
    meta = AlgorithmMeta(name="cp_sat", family="scheduling", implementation="library:ortools", ...)

    def solve(self, problem):
        data = parse_project_problem(problem)
        dur = build_durations(data)
        structure = cpm(dur, build_successors(data))    # slack / critical_path / order の供給元
        horizon = sum(dur.values())                     # 全タスク直列 = 開始時刻の上界

        model = cp_model.CpModel()
        starts = {t.id: model.new_int_var(0, horizon, f"s_{t.id}") for t in data.tasks}
        ends   = {t.id: model.new_int_var(0, horizon, f"e_{t.id}") for t in data.tasks}
        intervals = {t.id: model.new_interval_var(starts[t.id], dur[t.id], ends[t.id], f"iv_{t.id}")
                     for t in data.tasks}

        for d in data.dependencies:                     # 依存: 先行の end 以降に後続の start
            model.add(starts[d.successor] >= ends[d.predecessor])

        if data.resource_capacity is not None:          # 資源: 同時実行の需要合計 ≤ 容量
            demands = [t.resource for t in data.tasks]
            if any(demands):
                model.add_cumulative([intervals[t.id] for t in data.tasks],
                                     demands, data.resource_capacity)

        makespan = model.new_int_var(0, horizon, "makespan")
        model.add_max_equality(makespan, list(ends.values()))
        model.minimize(makespan)

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1        # ← 決定論
        solver.parameters.random_seed = 0
        status = solver.solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return infeasible_project_solution(self.meta)

        actual = {t.id: int(solver.value(starts[t.id])) for t in data.tasks}
        return project_solution(data, actual, structure, self.meta, ops=None)
```

- **`new_interval_var(start, size, end)`** ── CP-SAT の「区間変数」。`start + size == end` が自動で張られる。
  scheduling 問題の 1 級市民。
- **`add_cumulative(intervals, demands, capacity)`** ── 「任意の時刻で、そこにかかっている区間のdemand 合計が capacity 以下」。RCPSP の資源制約そのもの。`priority_list` の `while` ループをソルバーが一撃で扱う。
- **`minimize(max(end))`** ── `add_max_equality` で makespan 変数を作って最小化。
- **決定論**: `num_search_workers=1` + `random_seed=0`(Phase 6 の CP-SAT と同じ)。purity テスト(同入力 → 同出力)が緑になる。

---

## 2. slack / critical_path は手実装 `cpm` から供給する

CP-SAT が返すのは **実際の開始時刻だけ**。`ProjectSolution.slack` / `critical_path` / `task_order` は手実装 `cpm`(資源無視)の `CpmResult` から取る ── これらは「資源が無ければどこが律速か」の**構造的な情報**で、資源が押し出した実 makespan とは別物。

> **観察点**: CP-SAT の makespan(fixture では 9)は CPM の makespan(8)より大きいのに、`critical_path` は CPM のもの(A→C→E)。「クリティカルパスは資源フリーの律速。資源がそれをさらに 1 日押し出した」と読む。`verify_project_structure`(8-3)の「critical_path のタスクは
> slack 0」「makespan == max(finish)」は両方 CPM 由来 / 実スケジュール由来なので矛盾しない。

---

## 3. 3 者の関係(fixture、resource_capacity=3)

| strategy        | makespan | 資源 feasible | Verification |
| --------------- | -------- | ----------- | ------------ |
| `cpm`           | 8        | ✗(peak 4)   | **invalid**  |
| `priority_list` | 10       | ✓           | valid        |
| `cp_sat`        | **9**    | ✓           | valid        |

`cpm` の 8 は下界(資源無視)、`cp_sat` の 9 が資源制約下の真の最適、`priority_list` の 10 は貪欲が外した近似。**`cpm ≤ cp_sat ≤ priority_list`** が一般に成り立つ(下界 ≤ 最適 ≤ feasible な近似)──8-6 の `test_project_strategies.py` がプロパティとして確認する。

### なぜこの数字になるか ── 3 者の処理をトレースする

**`cpm`**: 前進パスは A=0,B=0,C=3(A の後),D=2(B の後),E=7(C=7 と D=4 の大きい方)。makespan=max(EF)=8。**資源チェックのロジックが無い**ので全タスクを ES にそのまま置く。資源プロファイルを積むと t3 で `C(3) + D(1) = 4 > 3`(C は t3-7、D は t2-4 で t3 が重なる)── cpm 自身はこれに気づかず `valid` を返し、**Verification が事後の検算で `invalid`** にする。

**`priority_list`**: 優先順位は資源無視の CPM で出した LS 昇順 `A(0) → B(3) → C(3、同点は id 順) → D(5) → E(7)`。**この順で 1 本ずつ確定し、後戻りしない**:

1. A: 0-3(資源 2)/ 2. B: 0-2(資源 1)
2. **C: 先行 A 完了(t3)以降の最早枠 → 3-7 に確定(資源 3、capacity を独占)**
3. D: 先行 B 完了(t2)以降が理想だが t3-6 は C が容量を使い切っていて入れない(3+1=4>3)。t7 まで待って **7-9**
4. E: 先行 C(7)と D(9)の両方待ち → **9-10**

makespan=10。**C を先に確定させたせいで、D が本来入れたはずの隙間(A と同時に走らせれば t2-4 で 2+1=3 に収まる)を失う**。貪欲は「今の視点で最良」の 1 手を選ぶだけで、後続タスクへの影響を評価しない。

**`cp_sat`**: 開始時刻を決定変数として依存・資源を制約に、makespan 最小化を**探索**で解く。優れた解の一つ ── A: 0-3(資源 2)、**D: 2-4(資源 1、A と同時に走らせる)** → t2-3 は 2+1=3 で収まる。C は D が空けた t4 以降 → 4-8(資源 3、独占)。E は C(8)/D(4)の両方待ち → 8-9。makespan=9。**priority_list が見つけられなかった「D を A の下に潜り込ませ、C の専有時間をなるべく早く空ける」配置**を、CP-SAT は全体探索で見つける。

|             | `cpm`                    | `priority_list`              | `cp_sat`                   |
| ----------- | ------------------------ | ---------------------------- | -------------------------- |
| 計算の型        | 決定論的な 2 パス計算(前進+後退)、探索なし | 1 パスの貪欲構成。逐次確定・後戻りなし         | 制約充足 + 最適化の探索(分枝限定 + 制約伝播) |
| 資源の扱い       | 見ない                      | 見る(置いた後は不変)                  | 見る(全タスクの配置を同時に最適化)         |
| 保証          | 「資源が無限ならこれより短くならない」下界    | 「資源は必ず守るが最適とは限らない」feasible 解 | 「この制約下でこれ以上短くできない」証明付き最適解  |
| 8→10→9 の差の源 | 資源制約そのものを無視              | 優先順位が固定・局所最適(C を先に確定した代償)    | 全体探索で C・D の資源競合を回避する配置を発見  |

---

## 4. まとめ

- CP-SAT モデル: interval var + `start[succ] >= end[pred]` + `add_cumulative` + `minimize(max(end))`。
- 決定論 = `num_search_workers=1` + `random_seed=0`。`_ops` なし(ライブラリトラック)。
- slack / critical_path / task_order は手実装 `cpm` から供給(資源フリーの構造情報)。
- `cpm ≤ cp_sat ≤ priority_list` ── 下界・最適・近似。「手実装ヒューリスティックが最適を外す →
  産業ソルバー」を工程管理で再演(Phase 6 と同じ骨)。

## テスト観点(`textbook/samples/tests/unit/test_cpsat_project.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `OrToolsCpSatProjectStrategy.solve`
> - **ドライバ**: このテスト関数 / `build_project_problem` fixture(8-3)
> - **スタブ**: **不要** ── `OptimizationProblem` → `CandidateSolution` の純粋関数
>   (CP-SAT は決定論設定。DB / ネットワークに触れない)

| ケース                             | 期待                                                                         |
| ------------------------------- | -------------------------------------------------------------------------- |
| `cp_sat.solve`(cap3)            | `status="valid"` / `implementation == "library:ortools"` / `makespan == 9` |
| cpm 下界 ≤ cp_sat ≤ priority_list | 不等式が成立                                                                     |
| cp_sat の解が資源 feasible           | `peak_resource ≤ 3` / `verify` が `valid`                                   |
| 依存を守る                           | `C.start >= A.finish` / `E.start >= C.finish`                              |
| 決定論(同入力)                        | `model_dump()` 一致                                                          |

`uv run pytest tests/unit/test_cpsat_project.py` / `uvx pyright app/algorithms/scheduling`。

---

次章([Phase-8-6](./Phase-8-6.md))では、作業単位 8-6 ── registry + select + `cpm_nx` オラクル +
end-to-end。`networkx_project.py`(`nx.topological_sort` で非制約 CPM を別実装検算)を作り、`registry["project_scheduling"]` に 4 strategy をまとめて有効化、`select_strategy` に project 分岐を足す。ここで初めてフルパイプラインが緑になる。
