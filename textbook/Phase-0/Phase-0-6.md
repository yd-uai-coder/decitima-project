# Phase 0-6: Validation と Verification 設計

## この章のゴール

DeciTima の設計で最も混同されやすい 2 つの検証を、はっきり分けて設計する。

- **Validation** ── 「問題定義として妥当か?」(Algorithm Engine に渡す**前**)
- **Verification** ── 「出てきた解が制約を満たすか?」(候補解が出た**後**)

> | 用語               | 意味    | 確認すること                     |
> | ---------------- | ----- | -------------------------- |
> | **Validation**   | 妥当性確認 | 「入力・データ・結果が**目的に対して適切か**？」 |
> | **Verification** | 検証    | 「仕様・設計どおりに**正しく作られているか**？」 |

加えて、失敗時のエラー設計(`AppError` 階層への追加)を決める。

---

## 1. なぜ 2 つに分けるのか

パイプライン(Phase 0-1)の 4 番と 6 番。

```
3. Structured Problem
     ▼
4. Validation      ← 「この問題、そもそも解く意味ある?」
     ▼
5. Algorithm Engine
     ▼
6. Verification    ← 「出てきたこの解、条件守ってる?」
     ▼
7. Simulation
```

混ぜると切り分けられない問い(Phase 0-1 再掲):

- 解が変 → アルゴリズムのバグ? 問題定義が壊れていた?
- 制約違反 → アルゴリズムが破った? 実行不可能な問題だった?

**Validation は「入力の健全性」、Verification は「出力の正当性」。**
役割・実行タイミング・失敗の意味・対応する HTTP ステータスがすべて違う。

|       | Validation                   | Verification                   |
| ----- | ---------------------------- | ------------------------------ |
| 対象    | `OptimizationProblem`        | `CandidateSolution`            |
| いつ    | Algorithm Engine の前          | Algorithm Engine の後            |
| 失敗の意味 | 問題定義が間違っている / 実行不可能          | 解が制約を破っている(アルゴリズムの問題)          |
| 失敗時   | 計算せず 400 / 422 を返す           | 解を返すが `status="invalid"` にする   |
| 実装    | `app/services/validation.py` | `app/services/verification.py` |

---

## 2. Validation ── 問題定義の妥当性

### 2.1 2 段階

README 6 節のとおり。

```
① Input Validation（構文・型・単項の値域）
     budget >= 0 / duration > 0 / required_headcount > 0
     → Pydantic の Field 制約と field_validator で大半をカバー

② Semantic Validation（フィールド間の整合・実行可能性の下限）
     required_staff <= available_staff
     max_hours >= min_hours
     start と goal が nodes に存在する
     → Pydantic の model_validator、または domain のセマンティック検査関数
```

### 2.2 Input Validation は Pydantic に寄せる

```python
# app/domain/problems/shift_scheduler.py（Phase 0-2 の ShiftSlot に検証を足す）
class ShiftSlot(BaseModel):
    required_headcount: int = Field(ge=1)     # 1 以上
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)

    @model_validator(mode="after")
    def _end_after_start(self):
        if self.end_hour <= self.start_hour:   # 終業は始業より後
            raise ValueError("end_hour must be greater than start_hour")
        return self
```

`OptimizationProblem` を受け取った時点で Pydantic が走るので、Input Validation の
多くは「スキーマを定義した時点で完了」する。

### 2.3 Semantic Validation は専用サービス

Pydantic だけでは表現しにくい「問題全体を見ないと分からない」検査。

```python
# app/services/validation.py
class ProblemValidationService:
    """OptimizationProblem がアルゴリズムに渡せる状態か、問題全体を見て検査する。"""

    def validate(self, problem: OptimizationProblem) -> None:
        checks = _SEMANTIC_CHECKS.get(problem.problem_type, [])
        errors: list[str] = []
        # 各セマンティックチェックを順に適用し、違反を集める
        for check in checks:
            msg = check(problem)
            if msg is not None:
                errors.append(msg)
        if errors:
            raise ProblemValidationError("; ".join(errors))
```

problem_type ごとのチェック関数(`domain/problems/` に置く):

| problem_type     | セマンティックチェック例                                                                                             |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| route_planning   | `start` / `goal` が `nodes` に存在 / エッジの端点が `nodes` に存在 / `ForbiddenConstraint` を除いても start→goal が到達可能(連結性) |
| shift_scheduling | 各スロットで「そのスロットに入れるスタッフ数 ≥ `required_headcount`」/ 必要スキルを持つスタッフが存在 / `max_weekly_hours` が最低 1 スロット分以上       |

### 2.4 「実行不可能」をどう扱うか

Semantic Validation で「どう頑張っても解けない」と分かる場合がある。
たとえば「必要人数 3 だが勤務可能なスタッフが 2 人しかいない」。

- これは `InfeasibleProblemError`(`ProblemValidationError` の一種、あるいは並び)。
- **アルゴリズムを走らせない**。走らせても `infeasible` が返るだけで、時間の無駄。
- ただし「連結性はあるが遠回りが必要」のような「解けるが最適でないかも」は
  Validation では弾かない。それは Algorithm と Verification の仕事。

境界の原則: **Validation は「明らかに無理」だけを弾く。グレーゾーンは通す。**

---

## 3. Verification ── 解の制約充足

### 3.1 Constraint Checker

各制約の `kind`(`AnyConstraint` の各サブタイプ)に対応するチェッカー関数が
`app/domain/constraints/` にある。

```python
# app/domain/constraints/numeric_bound.py
def check_numeric_bound(
    constraint: NumericBoundConstraint,
    problem: OptimizationProblem,
    solution: CandidateSolution,
) -> ConstraintViolation | None:
    """解の該当メトリクスが constraint の境界を満たすか判定する。"""
    actual = _extract_field(constraint.field, problem, solution)
    ok = _compare(actual, constraint.op, constraint.value)   # 例: actual <= value
    if ok:
        return None
    return ConstraintViolation(
        constraint_kind=constraint.kind,
        severity=constraint.severity,
        message=f"{constraint.field}={actual} violates {constraint.op} {constraint.value}",
        detail={"actual": actual, "expected": constraint.value},
    )
```

### 3.2 Verification サービス

```python
# app/services/verification.py
class SolutionVerificationService:
    """候補解が problem のすべての制約を満たすか検証し、status と violations を確定する。"""

    def verify(
        self, problem: OptimizationProblem, solution: CandidateSolution
    ) -> CandidateSolution:
        violations: list[ConstraintViolation] = []
        # 全制約を対応チェッカーにディスパッチして違反を集める
        for c in problem.constraints:
            checker = _CHECKERS.get(c.kind)
            if checker is None:
                continue   # 未対応 kind は素通し（設計漏れは別途検知）
            v = checker(c, problem, solution)
            if v is not None:
                violations.append(v)

        has_hard = any(v.severity == "hard" for v in violations)
        soft_penalty = sum(
            (p.penalty or 0.0)
            for p, v in _pair_penalties(problem.constraints, violations)
        )

        # hard 違反が1つでもあれば解は invalid
        return solution.model_copy(update={
            "status": "invalid" if has_hard else solution.status,
            "violations": violations,
            "metrics": {**solution.metrics, "soft_penalty": soft_penalty},
        })
```

### 3.3 hard と soft の扱い

|          | hard                         | soft                                      |
| -------- | ---------------------------- | ----------------------------------------- |
| 1 件違反したら | `status = "invalid"`。解は採用しない | 解は valid のまま。`soft_penalty` を metrics に加算 |
| 例(Shift) | 必要人数不足、勤務時間超過                | 希望休が守られなかった                               |
| 例(Route) | 禁止エッジを使った、必須ノード未経由           | (MVP の Route は soft 制約なし)                 |

**設計判断**: Verification は解を書き換えない ── `model_copy(update=...)` で
新しい `CandidateSolution` を返す。元の「アルゴリズムが出した生の解」も残せる
(監査・デバッグ用)。

### 3.4 なぜアルゴリズムに検証させないのか(再掲)

Phase 0-4 で述べたとおり。<u>`solve` は解を作るだけ。</u>検証を別にすることで:

- 近似アルゴリズム(貪欲法)が hard 制約を破っても「バグ」ではなく
  「`invalid` な候補」として扱え、Phase 3 で「貪欲法は N% の確率で制約違反」を測れる。
- チェッカーのバグとアルゴリズムのバグを切り分けられる。
- 新しい制約種類を足すとき、全アルゴリズムを触らずチェッカーを 1 つ足すだけで済む。

---

## 4. エラー設計 ── `AppError` 階層への追加

`app/services/errors.py`(循環 import を避ける末端モジュール)に追加する。

```python
from app.core.errors import BadRequestError, UnprocessableEntityError  # 後者は無ければ追加

class ProblemValidationError(BadRequestError):
    """OptimizationProblem がセマンティック検査に通らなかった場合に送出する。"""

class InfeasibleProblemError(BadRequestError):
    """条件を満たす解が原理的に存在しないと Validation 段階で判明した場合に送出する。"""

class NoAlgorithmError(BadRequestError):
    """problem_type に対応するアルゴリズムが registry に無い場合に送出する。"""

class SolveTimeoutError(AppError):
    """アルゴリズムの実行が規定時間を超えた場合に送出する（HTTP 504 相当）。"""
    status_code = 504
```

- ルートは **これらを try/except しない**。既存の `register_error_handlers` が
  `AppError` → JSON に一括変換する。
- `VerificationFailedError` は**作らない**。解が制約を破っていても、それはエラーではなく
  `CandidateSolution.status="invalid"` として正常にレスポンスへ載せる
  (「アルゴリズムが失敗した」ではなく「この解は使えないと分かった」)。
- 例外: `app/api/deps.py` の認証境界だけは生の `HTTPException`(既存の設計方針、統一漏れではない)。

### HTTP ステータスの割り当て

| 事象               | 例外                           | ステータス                    |
| ---------------- | ---------------------------- | ------------------------ |
| Pydantic の型・値域違反 | (FastAPI が自動)                | 422                      |
| セマンティック検査 NG     | `ProblemValidationError`     | 400                      |
| 実行不可能な問題         | `InfeasibleProblemError`     | 400                      |
| 対応アルゴリズムなし       | `NoAlgorithmError`           | 400                      |
| 計算タイムアウト         | `SolveTimeoutError`          | 504                      |
| レート制限超過          | `RateLimitExceededError`(既存) | 429                      |
| 解が制約違反           | (例外にしない)                     | 200 + `status="invalid"` |

---

## 5. 検証 ── 2 題材の検証項目一覧

### 5.1 Route Planner

| フェーズ                  | 項目                                                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Validation(Input)     | 各エッジ weight ≥ 0 / headcount 等の数値域                                                                                                     |
| Validation(Semantic)  | start・goal が nodes に存在 / エッジ端点が nodes に存在 / 禁止エッジ除去後も start→goal が到達可能                                                                |
| Verification(hard)    | path が連結(隣接ノードがエッジで結ばれている)/ path が start で始まり goal で終わる / 禁止エッジ(`ForbiddenConstraint`)を含まない / 必須ノード(`RequiredInclusionConstraint`)を通る |
| Verification(metrics) | `total_weight` が path 上のエッジ weight の合計と一致                                                                                             |

### 5.2 Shift Scheduler

| フェーズ                  | 項目                                                                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Validation(Input)     | hourly_wage ≥ 0 / required_headcount ≥ 1 / start_hour < end_hour                                                                  |
| Validation(Semantic)  | 各スロットに入れるスタッフ数 ≥ required_headcount / 必要スキル保持者が存在                                                                                 |
| Verification(hard)    | 全スロットで割当人数 = required_headcount / 各スタッフの週合計勤務時間 ≤ max_weekly_hours / 連続勤務日数 ≤ max_consecutive_days / 割当スタッフがそのスロットを available に持つ |
| Verification(soft)    | 希望休(`requested_days_off`)にあたるスロットに割り当てられた件数 → `soft_penalty`                                                                      |
| Verification(metrics) | `labor_cost` = Σ(割当スタッフの時給 × スロット時間)/ `day_off_satisfaction` = 守れた希望休 ÷ 希望休総数                                                     |

**確認**: すべての検証項目が「問題全体を見る Validation」か「解を照合する Verification」の
どちらかに素直に分類できた。設計の分割は妥当。

---

## 6. まとめ

- **Validation**(問題定義の妥当性)と **Verification**(解の制約充足)は別物。
  対象・タイミング・失敗の意味・HTTP ステータスがすべて違う。
- Input Validation は Pydantic に寄せる。Semantic Validation は problem_type ごとの
  チェック関数(`domain/problems/`)。「明らかに無理」だけ弾き、グレーは通す。
- Verification は制約の `kind` ごとのチェッカー(`domain/constraints/`)に
  ディスパッチ。hard 違反 → `status="invalid"`、soft 違反 → `soft_penalty`。
  解は書き換えず新インスタンスを返す。
- エラーは `app/services/errors.py` に `AppError` 派生を追加。
  ルートで try/except せず、既存ハンドラに任せる。解の制約違反は例外にしない。

次章(Phase 0-7)では、これらを公開する **API** を設計する。

---

## 後続 Phase での改訂

- **[Phase 1]** route 限定の最小 V&V を先に `SolveService` に配線(walking skeleton)。
  `Phase-1-6.md`。
- **[Phase 2]** この章のスケッチを実装。実装上の判断:
  - Semantic Validation の `_SEMANTIC_CHECKS` は `app/domain/problems/semantic.py`、
    Constraint Checker の `_CHECKERS`(→ `CHECKERS`)は `app/domain/constraints/__init__.py`
    に置く。`validation.py` / `verification.py` はレジストリを回すオーケストレーションに縮小。
  - route の「到達可能性」検査は `domain/` でなく `services/validation.py` に置く
    (`domain → algorithms` の逆流を作らない)。`Phase-2-2.md` §3。
  - `_verify_route_structure`(§5.1)/ 新 `verify_shift_structure`(§5.2)は leaf でも
    aggregator でもない `app/domain/solutions/structure.py` に置く(`ConstraintViolation`
    を返すため leaf に置くと循環)。`Phase-2-3.md` §2。
  - §5.2 の「割当人数 = required_headcount」は **`StaffingConstraint` を宣言した問題だけ**が
    受ける opt-in の検査(`check_staffing`)。可用性・労働時間・スキルは常時オンの構造検証。
    `Phase-2-3.md` §1 / `Phase-2-4.md`。
  - §5.2 の連続勤務日数は完成割当の 1 回スキャンで判定(Sliding Window プリミティブ =
    Phase 6 のソルバー用 ── に依存しない)。`Phase-2-4.md` §3。
