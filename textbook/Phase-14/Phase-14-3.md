# Phase 14-3: LLM Only 戦略(スケジューリング系)(作業単位 14-3)

## この章のゴール

`shift_scheduling` と `project_scheduling` の `LlmOnly*Strategy` を実装する。
`route_llm.py`/`network_llm.py`(14-2)と同じ形だが、2ドメインとも解のフィールド数が
多く、プロンプトに落とす情報量・検証される非自明な整合条件の種類が増える。

**この章で作成/更新するファイル**: `app/algorithms/llm/shift_llm.py`・`project_llm.py`(新規)、`tests/unit/test_llm_only_strategies.py`(shift/project 分を追記)。

---

## 1. `LlmOnlyShiftStrategy` ── 出力は `assignments: dict[str, list[str]]` だけ

```python
# app/algorithms/llm/shift_llm.py(新規、要点)
def _prompt(problem: OptimizationProblem, data: ShiftData) -> str:
    staff = "\n".join(
        f"- {s.id}: 時給{s.hourly_wage}、勤務可能スロット {s.available_slot_ids}、"
        f"スキル {s.skills}、希望休 {s.requested_days_off}"
        for s in data.staff
    )
    slots = "\n".join(
        f"- {sl.id}: {sl.day} {sl.start_hour}-{sl.end_hour}時、"
        f"必要人数 {sl.required_headcount}、必要スキル {sl.required_skills}"
        for sl in data.slots
    )
    return (
        "次のシフト割当問題を解いてください。各スロット id に、そのスロットで勤務可能かつ"
        "必要スキルを満たすスタッフ id を必要人数ぶん割り当ててください"
        "(assignments は {スロットid: [スタッフid, ...]} の形)。\n\n"
        f"スタッフ:\n{staff}\n\nスロット:\n{slots}\n\n"
        f"週労働時間の上限 {data.max_weekly_hours}h、"
        f"連続勤務日数の上限 {data.max_consecutive_days}日\n\n"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}"
    )


class LlmOnlyShiftStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(ShiftData, problem.data)
        # strip_problem_type: 判別子は LLM に見せない(Phase-14-2.md §4 の事象への対処)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(ShiftSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = ShiftSolution(
            problem_type="shift_scheduling", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

`ShiftSolution` は `assignments` 1フィールドしか持たない(Phase 1〜6)── 派生値の
自己申告(`total_weight` のような)が無いドメイン。その代わり検証条件が多い:
実在 id / 勤務可能スロット / 必要スキル / 週労働時間の上限 / 連続勤務日数の上限 / 希望休
(soft)── いずれも `structure.py::verify_shift_structure`(Phase 2、Phase 6 で
`shift_metrics.py` 呼び出しに整理済み)がそのまま判定する。プロンプトはこれらの制約を**LLM に説明はするが、判定は一切 LLM に委ねない** ── 判定は既存コードの仕事のまま。

`labor_cost`/`day_off_satisfaction`/`hour_variance` という目的の対象値は `ShiftSolution` のフィールドではなく、`verify_shift_structure` が `shift_metrics.assignment_metrics()` を呼んで `CandidateSolution.metrics` に積む(Phase 6-1)。**LLM Only 戦略はこれらの値を一切計算しない** ── 探索(algorithms/scheduling)と同じ計算コードを Verification 側が
呼ぶので、LLM が「良い割当」を選べば正しい `labor_cost` が自動的に付く(14-5 の
`_objective_metrics` がこの非対称を吸収する話は Phase-14-5.md で扱う)。

## 2. `LlmOnlyProjectStrategy` ── task_order / schedule / critical_path / makespan の4点セット

```python
# app/algorithms/llm/project_llm.py(新規、要点)
def _prompt(problem: OptimizationProblem, data: ProjectData) -> str:
    tasks = "\n".join(
        f"- {t.id}: {t.name or t.id}(所要時間 {t.duration}、資源 {t.resource})"
        for t in data.tasks
    )
    deps = "\n".join(f"- {d.id}: {d.predecessor} -> {d.successor}" for d in data.dependencies)
    capacity_line = (
        f"資源上限 {data.resource_capacity}\n\n" if data.resource_capacity is not None else ""
    )
    return (
        "次のプロジェクトスケジューリング問題を解いてください。依存関係(先行タスクが終わって"
        "から後続タスクを開始できる)を守り、全タスクの実行順(task_order)と各タスクの"
        "スケジュール(schedule: task_id / start / finish / slack)を決めてください。"
        "クリティカルパス(slack が 0 のタスクを起点から終点まで1本に繋いだ列)と、"
        "全体の所要時間(makespan)も答えてください。\n\n"
        f"タスク:\n{tasks}\n\n依存:\n{deps}\n\n{capacity_line}"
        f"目的:\n{render_objectives(problem)}\n\n制約:\n{render_constraints(problem)}\n\n"
        "finish は start + duration、makespan は全タスクの finish の最大値と矛盾しないよう"
        "正しく計算してください。"
    )


class LlmOnlyProjectStrategy:
    meta = LLM_ONLY_META

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        data = cast(ProjectData, problem.data)
        llm = get_gemini_llm(temperature=0).with_structured_output(
            strip_problem_type(ProjectSolution)
        )
        raw = cast(BaseModel, llm.invoke(_prompt(problem, data)))
        result = ProjectSolution(
            problem_type="project_scheduling", **raw.model_dump(exclude={"problem_type"})
        )
        return CandidateSolution(status="valid", assignments=result, produced_by=self.meta)
```

`ProjectSolution` は6ドメイン中もっとも構造検証(`verify_project_structure`、Phase 8-3)が細かい ── task_order が全タスクの順列か、`finish == start + duration`、依存のfinish-to-start、`critical_path` のタスクが本当に `slack == 0` か、`makespan` が`max(finish)` と一致するか。**この5条件をすべて「与えられた schedule から再計算して比較する」既存コードがそのまま LLM の出力に適用される** ── CPM のアルゴリズム(Phase 8-2)をLLM が正しく再現できているかどうかを、教材の中で最も条件の多い形で検証できる。

資源制約(`resource_capacity`)がある場合の容量超過検査(`_verify_project_resources`、Phase 8-4、imos 法で資源プロファイルを再計算)も無変更で適用される ── LLM が資源を無視したCPM的な詰め方をすれば、手実装の `CpmScheduleStrategy` と同じ理由で invalid になり得る(Phase 8 の「cpm は資源を無視した下界」という教材の核が、Phase 14 で「LLM も資源を無視しがち」という形で再登場する可能性がある ── 実測してみるまで分からない、というところに Phase 14 の実験的な価値がある)。

## 3. テストは resource_capacity=None(純粋 CPM)で単純化する

```python
# tests/unit/test_llm_only_strategies.py(要点)
def test_project_llm_only_solves_to_valid(monkeypatch):
    problem = build_project_problem(resource_capacity=None)  # 資源制約なしの純粋 CPM
    solution = ProjectSolution(
        task_order=["A", "B", "C", "D", "E"],
        schedule=[
            ScheduledTask(task_id="A", start=0, finish=3, slack=0),
            ScheduledTask(task_id="B", start=0, finish=2, slack=3),
            ScheduledTask(task_id="C", start=3, finish=7, slack=0),
            ScheduledTask(task_id="D", start=2, finish=4, slack=3),
            ScheduledTask(task_id="E", start=7, finish=8, slack=0),
        ],
        critical_path=["A", "C", "E"],
        makespan=8,
    )
    ...
```

`resource_capacity=None` を選ぶのは「テストで検証したい対象を絞る」ため(進行のルール #14の精神 ── 資源プロファイルの再計算は Phase 8-4 側で既にテスト済みの既存コード)。手計算したCPM の値(critical path = A → C → E、makespan = 8)は README の元ネタである`Phase-0-2.md` の例題(A=設計/B=調達/C=実装/D=検証/E=リリース)と同じタスク集合を使う ──
`tests/fixtures/optimization.py::build_project_problem` の既定値そのもの。

---

## まとめ

- `shift_llm.py`/`project_llm.py` も 14-2 と全く同じ形(`strip_problem_type()` +
  同期 `invoke` + 既存スキーマへの詰め替え)。差はプロンプトの情報量と、既存検証が確認する整合条件の数だけ。
- shift は目的値が `metrics`(検証側が計算)に、project は目的値が `assignments`
  (LLM が申告)にある ── この非対称が 14-5 の `_objective_metrics` を要求する。

## テスト観点(`tests/unit/test_llm_only_strategies.py`)

> **対象**: `LlmOnlyShiftStrategy.solve` / `LlmOnlyProjectStrategy.solve`
> **ドライバ**: このテスト関数
> **スタブ**: `FakeLLM`(`app.algorithms.llm.shift_llm`/`project_llm` の `get_gemini_llm` を
> それぞれ monkeypatch)。

| ケース                             | 期待                                     |
| ------------------------------- | -------------------------------------- |
| shift: 希望休(2026-09-02)を避けた正しい割当 | `status == "valid"`、`violations == []` |
| project: 資源制約なし、手計算した正しい CPM 解  | `status == "valid"`、`violations == []` |

> **写経の罠**: shift のテストで `tanaka`(希望休 `2026-09-02`)を s3/s4(その日のスロット)に割り当てると、`respect_days_off`(soft)違反が1件付き `verified.violations == []` のアサーションが赤くなる。「valid かどうか」と「violations が空かどうか」は別の話 ── soft違反があっても `status` は `"valid"` のままになり得る(Phase 2 の hard/soft 分離)。

```bash
uv run pytest tests/unit/test_llm_only_strategies.py -k "shift or project"
uvx pyright app/algorithms/llm/shift_llm.py app/algorithms/llm/project_llm.py
```

---

次章([Phase-14-4](./Phase-14-4.md))では、作業単位 14-4 ──
最適化系2ドメイン(travel_planning / logistics_planning)を実装する。
