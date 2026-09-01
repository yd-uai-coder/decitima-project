# Phase 2-2: Semantic Validation の一般化(作業単位 2-2)

## この章のゴール

Phase 1 の `ProblemValidationService` は `isinstance(problem.data, RouteData)` のハードコード
分岐で、route の検査だけをインラインで持っていた。shift は素通し。これを:

- problem_type ごとの **検査関数** を `app/domain/problems/semantic.py` に集約
- `SEMANTIC_CHECKS: dict[str, list[検査関数]]` レジストリ(`algorithms/registry.py` と同じ発想)
- `ProblemValidationService.validate` は **レジストリを回すだけ**

に作り替え、**shift の Semantic Validation** を足す。

**この章で新規作成するファイル**: `app/domain/problems/semantic.py`。
**既存ファイルへの変更**: `app/services/validation.py`(Phase 1 の実装を全面改訂。現行版は
`samples/app/services/validation.py`。Phase 1 側に 「以降 Phase で修正予定」マーカー)。

対応サンプル: `samples/app/domain/problems/semantic.py`, `samples/app/services/validation.py`。
テストは `samples/tests/unit/test_validation_service.py`(Phase 1 版を改訂 ── `test_shift_problem_passes_through_for_now` は失効)。
設計は `Phase-0-6.md` §2.3 / §2.4。

---

## 1. `semantic.py` ── `SemanticIssue` と検査関数

各検査は **純粋関数 `(OptimizationProblem) -> list[SemanticIssue]`**。`SemanticIssue` は
「整合性の欠陥」か「原理的に解なし」かを 1 ビットで区別する:

```python
# app/domain/problems/semantic.py(要点。全文は samples)
@dataclass(frozen=True)
class SemanticIssue:
    message: str
    infeasible: bool = False   # False → ProblemValidationError / True → InfeasibleProblemError

type SemanticCheck = Callable[[OptimizationProblem], list[SemanticIssue]]
```

### route の検査

| 関数 | 見るもの | infeasible? |
| --- | --- | --- |
| `check_route_endpoints` | `start` / `goal` が `nodes` に実在 | No(整合性) |
| `check_route_edge_endpoints` | 各エッジの `source` / `target` が `nodes` に実在 | No(整合性) |

到達可能性は **ここに無い**(§3)。

### shift の検査

| 関数 | 見るもの | infeasible? |
| --- | --- | --- |
| `check_shift_slot_refs` | スタッフの `available_slot_ids` が実在スロットを指す | No(整合性) |
| `check_shift_staffing_feasible` | 各スロットに「入れる」(available かつ必要スキル保持)スタッフが `required_headcount` 人以上いる | **Yes** |
| `check_shift_skill_coverage` | 各 `required_skills` を持ち、かつそのスロットに入れるスタッフが存在 | **Yes** |
| `check_shift_weekly_hours_cover` | `max_weekly_hours` が最長スロット 1 本分以上 | **Yes** |

各検査は `if not isinstance(problem.data, ShiftData): return []` で自分の担当外を素通しする
(レジストリで problem_type を絞っているので普段は当たらないが、防御的に)。

### レジストリ

```python
SEMANTIC_CHECKS: dict[str, list[SemanticCheck]] = {
    "route_planning":   [check_route_endpoints, check_route_edge_endpoints],
    "shift_scheduling": [check_shift_slot_refs, check_shift_staffing_feasible,
                         check_shift_skill_coverage, check_shift_weekly_hours_cover],
}
```

新しい problem_type は「検査関数を書いて 1 エントリ足す」だけ。`validation.py` は触らない。

---

## 2. `validation.py` ── レジストリを回すだけ

```python
# app/services/validation.py(要点。全文は samples)
class ProblemValidationService:
    def validate(self, problem: OptimizationProblem) -> None:
        issues = [
            issue
            for check in SEMANTIC_CHECKS.get(problem.problem_type, [])
            for issue in check(problem)
        ]

        # 整合性の欠陥を優先 ── 端点が実在してこそ到達可能性の判定に意味がある
        integrity = [i.message for i in issues if not i.infeasible]
        if integrity:
            raise ProblemValidationError("; ".join(integrity))

        infeasible = [i.message for i in issues if i.infeasible]
        if isinstance(problem.data, RouteData):
            infeasible += self._route_unreachable(problem, problem.data)   # ← §3
        if infeasible:
            raise InfeasibleProblemError("; ".join(infeasible))
```

**優先順位**: 整合性 NG があれば `ProblemValidationError` を投げて終わり。無ければ
infeasible をまとめて `InfeasibleProblemError`。Phase 1 の「整合性チェック → 早期 return →
到達可能性」と同じ順序を、収集してから判定する形にしただけ。

---

## 3. 到達可能性だけ `services/` に残す ── 層の境界の実例

route の「禁止エッジを除いても start→goal に行けるか」は `build_adjacency`(`algorithms/graph`)
と BFS(`algorithms/search`)が要る。これを `domain/problems/semantic.py` に置くと
**`domain/` が `algorithms/` を import する**ことになる。

`Phase-0-3.md` §2.2 の依存方向は `algorithms → domain`(片方向)。逆流させると
`domain.problems.semantic → algorithms.graph.dijkstra → domain.problems.route_planner` と
`domain` を挟んで循環しかねない。両方とも「純粋」だが、**純粋どうしでも依存の向きは 1 つに
保つ**。

だから到達可能性は `ProblemValidationService._route_unreachable` として **services 層に残す**。
services は domain も algorithms も呼んでよい層。`SEMANTIC_CHECKS` は「domain だけで完結する
検査」、到達可能性は「アルゴリズムが要る検査」── サービスがこの 2 種類を合成する。

```python
def _route_unreachable(self, problem, data: RouteData) -> list[str]:
    forbidden = {item for c in problem.constraints
                 if isinstance(c, ForbiddenConstraint) for item in c.items}
    adjacency = build_adjacency(data, forbidden)          # ← Phase-1-4 の関数を再利用
    plain = {n: [nxt for nxt, _e, _w in es] for n, es in adjacency.items()}
    if data.goal in reachable_nodes(plain, data.start):   # ← Phase-1-3 の BFS
        return []
    return [f"goal {data.goal!r} is unreachable from {data.start!r} ..."]
```

> **CL 開発の狙い**: 「どの層に何を置くか」は抽象論では決まらない。`import` 1 本が層の
> 方向を破るという具体的な制約が、`_route_unreachable` を services に残す判断を作った。
> この手の判断を写経しながら味わうのが目的。

---

## 4. `test_shift_problem_passes_through_for_now` の失効

Phase 1 の `test_validation_service.py` には:

```python
def test_shift_problem_passes_through_for_now() -> None:
    # Phase 1 では shift の semantic validation は未実装 → 素通し
    _SERVICE.validate(build_shift_problem())
```

があった。Phase 2 で shift も検証するので、このテストの **意図**(素通しの確認)は失効する。
現行版(`samples/tests/unit/test_validation_service.py`)では `test_valid_shift_problem_passes`
(妥当な shift 問題が通ることの確認)に置き換わっている。「わざと赤にして境界を確認する」の
逆で、**仕様が変わったらテストの意図も変わる**という例。

---

## 5. 既存への変更の当て方(写経手順)

1. `samples/app/domain/problems/semantic.py` を新規写経。
2. `samples/app/services/validation.py` で既存の `validation.py` を上書き。
3. `samples/tests/unit/test_validation_service.py` で既存のテストを上書き。
4. `uv run pytest tests/unit/test_validation_service.py` → 緑。`Phase-1-6` の `test_solve_*`
   も緑のまま(route の挙動は不変、shift 問題は solve すると先に `select_strategy` で
   `NoAlgorithmError` になるのは Phase 1 と同じ ── shift の Semantic Validation は
   `build_shift_problem()` を通す)。

---

## 6. テスト観点(`samples/tests/unit/test_validation_service.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `ProblemValidationService.validate` と `SEMANTIC_CHECKS` の各検査関数
> - **ドライバ**: テスト関数 + `build_route_problem()` / `build_shift_problem()` /
>   `build_infeasible_shift_problem()`(fixture ビルダー)
> - **スタブ**: **不要** ── 検査関数は純粋。`_route_unreachable` は `algorithms/` の
>   純粋関数を呼ぶが、それらも副作用が無いので本物を使う(スタブにする理由がない)。
>   「`domain/` にスタブが要るなら純粋レイヤー設計が崩れている」を毎章確認する。

| ケース | 期待 |
| --- | --- |
| route: 妥当な問題(forbidden + required) | 通過 |
| route: 未知の start ノード | `ProblemValidationError` |
| route: エッジが未知ノードを参照 | `ProblemValidationError` |
| route: 禁止エッジ除去後に到達不能 | `InfeasibleProblemError` |
| shift: 妥当な問題 | 通過 |
| shift: スタッフが未知スロットを参照 | `ProblemValidationError` |
| shift: 適格スタッフ数 < required_headcount | `InfeasibleProblemError` |
| shift: 必要スキル保持者が居ない | `InfeasibleProblemError` |

`uv run pytest tests/unit/test_validation_service.py` と
`uvx pyright app/domain/problems app/services/validation.py`。

---

## 7. まとめ

- Semantic Validation は problem_type ごとの検査関数 + `SEMANTIC_CHECKS` レジストリ。
  `validation.py` はそれを回すだけ。
- `SemanticIssue.infeasible` で `ProblemValidationError`(整合性)と `InfeasibleProblemError`
  (原理的に不能)を分ける。整合性 NG を優先。
- 到達可能性だけは `algorithms/` が要るので services に残す ── `domain → algorithms` の
  逆流を作らないため。層の境界は `import` の制約で実際に決まる。

次章([Phase-2-3](./Phase-2-3.md))では、作業単位 2-3 ── 解の検証側。`domain/constraints/` に
kind ごとのチェッカーを揃え、`services/verification.py` をオーケストレーションに縮小する。
