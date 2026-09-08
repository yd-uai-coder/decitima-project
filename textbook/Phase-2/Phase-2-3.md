# Phase 2-3: Constraint Checker 全実装 + `domain/constraints/`(作業単位 2-3)

## この章のゴール

Phase 1 の `verification.py` は、チェッカー関数(`_check_forbidden` /
`_check_required_inclusion`)と `_CHECKERS` dict をすべて **サービスファイルにインライン** で
持っていた。route 構造チェック(`_verify_route_structure`)も同様。Phase 2 で:

- kind ごとのチェッカーを `app/domain/constraints/` に **1 kind 1 ファイル** で切り出す
- `CHECKERS` レジストリを `app/domain/constraints/__init__.py` に置く
- 解の型ごとの「構造検証」を `app/domain/solutions/structure.py` に切り出す
- `services/verification.py` を **オーケストレーションだけ** に縮小する
- 新しいチェッカー `numeric_bound` / `staffing` を追加

**この章で作成 / 更新するファイル**:
`app/domain/constraints/{__init__,forbidden,required_inclusion,numeric_bound,staffing}.py`
(`__init__.py` は Phase 0 の docstring スタブを置き換え)、
`app/domain/solutions/structure.py`。
**既存ファイルへの変更**: `app/services/verification.py`(全面改訂。現行版は samples。Phase 1 側に
「以降 Phase で修正予定」マーカー)。

対応サンプル: `textbook/samples/app/domain/constraints/*.py`, `textbook/samples/app/domain/solutions/structure.py`,
`textbook/samples/app/services/verification.py`。
テストは `textbook/samples/tests/unit/test_constraint_checkers.py`,
`textbook/samples/tests/unit/test_verification_service.py`(route + `numeric_bound` 部分)。
設計は `Phase-0-6.md` §3 / §5、`Phase-0-2.md` §4.5。

---

## 1. `domain/constraints/` ── kind ごとのチェッカー

各ファイルは `check_<kind>(constraint, problem, solution) -> ConstraintViolation | None` を
1 つ export する純粋関数。

### `forbidden.py` / `required_inclusion.py`(Phase 1 から移設)

Phase 1 では `assert isinstance(solution.assignments, RouteSolution)` で「route 解以外が来たらクラッシュ」だった。移設にあたり **`return None`(素通し)** に変える ── `forbidden` 制約がたまたま shift 問題に付いていても落ちないように:

```python
# app/domain/constraints/forbidden.py(要点)
def check_forbidden(constraint, problem, solution) -> ConstraintViolation | None:
    if not isinstance(solution.assignments, RouteSolution):
        return None                          # ← Phase 1 の assert から変更
    hit = set(solution.assignments.path_edge_ids) & set(constraint.items)
    if not hit:
        return None
    return ConstraintViolation(constraint_kind=constraint.kind, severity=constraint.severity,
                               message=..., detail={"forbidden_hit": sorted(hit)})
```

### `numeric_bound.py`(新規)

`solution.metrics[field]` を `operator value` と比較する。**route の `total_weight` で今すぐ
効く**チェッカー ── `NumericBoundConstraint(field="total_weight", operator="<=", value=8)` を
route 問題に付ければ、`solve` 経由で end-to-end に動く(`Phase-2-6` の題材)。

```python
# app/domain/constraints/numeric_bound.py(要点)
from operator import eq, ge, gt, le, lt
_OPS = {"<=": le, ">=": ge, "==": eq, "<": lt, ">": gt}

def check_numeric_bound(constraint, problem, solution) -> ConstraintViolation | None:
    actual = solution.metrics.get(constraint.field)
    if actual is None:
        return None                          # そのメトリクスを誰も計算していない → 検証不能なので素通し
    if _OPS[constraint.operator](actual, constraint.value):
        return None
    return ConstraintViolation(...)
```

> `NumericBoundConstraint` のフィールド名は Phase 1 の `op` から **`operator`** に揃えた
> (実 backend に合わせた同期。`Phase-1-1.md` §2 / `Phase-0-2.md` §4.2 に注記)。
> stdlib の `operator` モジュールと名前が被るが、`from operator import le, ...` と関数を
> 名前で import すればモジュールを `import` しないので衝突しない。

### `staffing.py`(新規)

各スロットの割当人数が `required_headcount` **ちょうど** か。`StaffingConstraint` は
「スロットの必要人数を hard で守れ」という **宣言的フラグ**(数値自体は `ShiftData` 側。
`Phase-0-2.md` §4.2)。この制約を宣言した問題だけが人数検証される。

> **なぜ人数検証を `verify_shift_structure`(§2)に入れず、`staffing` チェッカーにするか**
> 可用性・労働時間・スキルは「物理的に / 法的に常に成り立つべき構造」= 構造検証。
> 「全スロットを過不足なく埋める」は **方針**(「入れられるだけ入れる」問題もありうる)。
> 方針は `problem.constraints` で宣言する ── 宣言したら hard で守られる、という opt-in。

### `__init__.py` ── `CHECKERS` レジストリ

```python
# app/domain/constraints/__init__.py(要点)
type ConstraintChecker = Callable[..., ConstraintViolation | None]

CHECKERS: dict[str, ConstraintChecker] = {
    "forbidden": check_forbidden,
    "required_inclusion": check_required_inclusion,
    "numeric_bound": check_numeric_bound,
    "staffing": check_staffing,
}
```

`Callable[..., ...]`(第 1 引数は `...`)は Phase 1 の `_Checker` と同じ割り切り ── kind ごとに
第 1 引数の具体型(`ForbiddenConstraint` 等)が違うので、レジストリ上では緩く受ける。
`algorithms/registry.py` の `REGISTRY` と同じ「機構のレジストリ」。新しい kind は
「サブタイプを `problem.py` に、チェッカーを 1 ファイル、`CHECKERS` に 1 行」。

---

## 2. `domain/solutions/structure.py` ── 構造検証

制約 `kind` に紐づかない、**解の型ごとに常に成り立つべき**検査。Phase 1 の
`_verify_route_structure` をここに移し(`verify_route_structure` に改名)、shift 用の
`verify_shift_structure`(中身は `Phase-2-4`)を足し、型でディスパッチする `structural_verify`
を置く。

```python
# app/domain/solutions/structure.py(要点。全文は samples)
def structural_verify(problem, solution) -> tuple[list[ConstraintViolation], dict[str, float]]:
    """解の型を見て構造検証にディスパッチ。(違反リスト, 追加メトリクス) を返す。"""
    a = solution.assignments
    if isinstance(a, RouteSolution) and isinstance(problem.data, RouteData):
        return verify_route_structure(problem.data, a), {}
    if isinstance(a, ShiftSolution) and isinstance(problem.data, ShiftData):
        return verify_shift_structure(problem.data, a)          # (違反, metrics)
    return [], {}
```

> **なぜ leaf(`route_planner.py` / `shift_scheduler.py`)でなく専用モジュールか**
> `verify_route_structure` は `ConstraintViolation`(`solution.py` にある)を返す。
> leaf が `solution.py` を import すると `solution.py → leaf → solution.py` の循環になる
> (`Phase-1-1.md` §4 の「leaf は aggregator を import しない」)。だから leaf でも
> aggregator でもない **合成モジュール** `structure.py` に置く。`structure.py` は leaf も
> `solution.py` も import してよい(逆向きは無い)。

`verify_route_structure` の中身は Phase 1 と同じ(始終点 / エッジ列長 / 各エッジが隣接ノード対を結ぶ / `total_weight` 整合、すべて hard)。

---

## 3. `services/verification.py` ── オーケストレーションだけ

```python
# app/services/verification.py(要点。全文は samples)
class SolutionVerificationService:
    def verify(self, problem, solution) -> CandidateSolution:
        if solution.status == "infeasible":
            return solution

        # 1. 構造検証 + 追加メトリクス(shift の labor_cost 等)
        structural, extra_metrics = structural_verify(problem, solution)
        enriched = solution.model_copy(update={"metrics": {**solution.metrics, **extra_metrics}})

        # 2. kind ごとのチェッカー(enriched の metrics を読む ── 順序が大事)
        kind_violations = []
        for c in problem.constraints:
            checker = CHECKERS.get(c.kind)
            if checker is None:
                continue
            v = checker(c, problem, enriched)
            if v is not None:
                kind_violations.append(v)

        violations = [*structural, *kind_violations]
        has_hard = any(v.severity == "hard" for v in violations)
        return enriched.model_copy(update={
            "status": "invalid" if has_hard else enriched.status,
            "violations": violations,
            "metrics": {**enriched.metrics, "soft_penalty": _soft_penalty(problem, violations)},
        })
```

**構造検証 → metrics enrich → kind ディスパッチ の順序が要点**: `check_numeric_bound` は
`solution.metrics["labor_cost"]` を読むことがあり、`labor_cost` は shift の構造検証が計算する。
だから構造検証を先に走らせ、その metrics を載せた `enriched` をチェッカーに渡す。

`_soft_penalty` は Phase 1 のまま(違反した soft 制約の `penalty` 合計)。

---

## 4. 既存への変更の当て方(写経手順)

1. `textbook/samples/app/domain/constraints/` の 5 ファイルを新規写経(`__init__.py` は Phase 0 の
   docstring スタブを上書き)。
2. `textbook/samples/app/domain/solutions/structure.py` を新規写経。
3. `textbook/samples/app/services/verification.py` で既存を上書き。
4. `textbook/samples/tests/unit/test_constraint_checkers.py` を新規、
   `textbook/samples/tests/unit/test_verification_service.py` で既存を上書き。
5. `uv run pytest tests/unit/test_constraint_checkers.py tests/unit/test_verification_service.py` → 緑。

`domain/constraints/__init__.py` は `Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 の
「以降 Phase で修正予定」マーカー(「constraints は Phase 2」)が指していた実装 ── ここで履行される。

---

## 5. テスト観点

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `check_*` チェッカー、`CHECKERS` レジストリ、`verify_route_structure`、
>   `SolutionVerificationService.verify`
> - **ドライバ**: テスト関数 + fixture ビルダー(`build_route_problem` / `build_shift_solution` /
>   `_route` ヘルパで解を手組み)
> - **スタブ**: **不要** ── チェッカーも構造検証もサービスも純粋。`verify` は `DijkstraStrategy`
>   の**本物**を使って解を作る(純粋なのでスタブにする意味がない)。`domain/` にスタブが
>   出てきたら純粋レイヤーが崩れているサイン。

`test_constraint_checkers.py`:

| ケース                                  | 期待                                                         |
| ------------------------------------ | ---------------------------------------------------------- |
| `CHECKERS` のキー集合                     | `{forbidden, required_inclusion, numeric_bound, staffing}` |
| `numeric_bound` 充足 / 違反 / metrics 欠落 | `None` / `ConstraintViolation` / `None`                    |
| `forbidden` を非 route 解に              | `None`(素通し)                                                |
| `required_inclusion` で必須ノード欠落        | `ConstraintViolation`(`detail["missing"]`)                 |
| `staffing` 過不足なし / 不足                | `None` / `ConstraintViolation`(`detail["slots"]`)          |

`test_verification_service.py`(route 部分):

| ケース                                        | 期待                                                 |
| ------------------------------------------ | -------------------------------------------------- |
| 制約充足の route 解                              | `valid` / `violations == []` / `soft_penalty == 0` |
| 禁止エッジ使用                                    | `invalid`(`forbidden`)                             |
| 必須ノード欠落                                    | `invalid`(`required_inclusion`)                    |
| `numeric_bound(total_weight <= 8)` を w9 解に | `invalid`(`numeric_bound`)                         |
| 元の解の `metrics` を書き換えない                     | `"soft_penalty" not in raw.metrics`                |
| `infeasible` の解                            | 素通し                                                |

`uv run pytest tests/unit/test_constraint_checkers.py tests/unit/test_verification_service.py` /
`uvx pyright app/domain app/services/verification.py`。

---

## 6. まとめ

- kind ごとのチェッカーは `domain/constraints/`(1 kind 1 ファイル)+ `CHECKERS` レジストリ。
  `numeric_bound`(route の `total_weight` で即効)/ `staffing`(宣言的フラグ)を追加。
- 構造検証は `domain/solutions/structure.py`(leaf でも aggregator でもない合成モジュール ──
  循環回避)。
- `verification.py` は「構造検証 → metrics enrich → `CHECKERS` ディスパッチ → hard/soft 集計」
  のオーケストレーションだけ。metrics を先に確定してからチェッカーに渡す順序が要点。

次章([Phase-2-4](./Phase-2-4.md))では、作業単位 2-4 ── `verify_shift_structure` の中身
(可用性・労働時間・連続勤務・希望休・metrics)を、手組み `ShiftSolution` fixture で検証する。
