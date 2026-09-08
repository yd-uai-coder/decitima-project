# Phase 2-4: Verification(shift)(作業単位 2-4)

## この章のゴール

`Phase-2-3` で `domain/solutions/structure.py` の骨格(`structural_verify` のディスパッチと
`verify_route_structure`)を作った。ここで **`verify_shift_structure`** の中身を実装する。

`Phase-0-6.md` §5.2 のシフト検証項目一覧:

| 種別 | 項目 | 由来 |
| --- | --- | --- |
| hard | 割当が実在する slot / staff を指す | 構造 |
| hard | 割当スタッフがそのスロットを `available_slot_ids` に持つ | `Staff` |
| hard | 割当スタッフが `required_skills` を満たす | `ShiftSlot` |
| hard | 週合計勤務時間 ≤ `max_weekly_hours` | `ShiftData` |
| hard | 連続勤務日数 ≤ `max_consecutive_days` | `ShiftData` |
| soft | `requested_days_off` の日に割り当てられた | `Staff` → `soft_penalty` |
| metric | `labor_cost` = Σ(時給 × スロット時間) | ― |
| metric | `day_off_satisfaction` = 守れた希望休 ÷ 希望休総数 | ― |

**この章で作成 / 更新するファイル**: なし(`structure.py` は `Phase-2-3` で作成済み)。
**既存ファイルへの変更**: `app/domain/solutions/structure.py` に `verify_shift_structure` と
補助関数を追加、`tests/fixtures/optimization.py` に `build_shift_solution` /
`build_infeasible_shift_problem` を追加(Phase 1 のファイル。Phase 1 側に「以降 Phase で修正予定」マーカー)。

対応サンプル: `textbook/samples/app/domain/solutions/structure.py`(shift 部分)、
`textbook/samples/tests/fixtures/optimization.py`。
テストは `textbook/samples/tests/unit/test_verification_service.py`(shift 部分)。
設計は `Phase-0-6.md` §3.3 / §5.2。

---

## 1. shift 解を検証する消費者は誰か

**shift を解く strategy(Greedy / Backtracking)は Phase 6**。だから `verify_shift_structure`
の消費者は現時点で:

1. **`POST /verify`**(`Phase-2-5`)── クライアントが手組みの `ShiftSolution` を持ち込む
2. **ユニットテスト** ── `build_shift_solution({...})` で解を手組みする

`solve` 経由(strategy が `ShiftSolution` を生成 → verify)の経路は Phase 6 で開通する。
2-4 のテストはすべて **手組み fixture** で回す ── これは「消費者が居ないから作らない」
(Phase 1 の objectives)とは違い、`POST /verify` という実消費者があるうえで、検証器は
アルゴリズムより先に固めておくと Phase 6 が楽になる、という判断。

---

## 2. `verify_shift_structure` の構造

```python
# app/domain/solutions/structure.py(要点。全文は samples)
def verify_shift_structure(
    data: ShiftData, sol: ShiftSolution
) -> tuple[list[ConstraintViolation], dict[str, float]]:
    out: list[ConstraintViolation] = []
    slot_by_id = {s.id: s for s in data.slots}
    staff_by_id = {s.id: s for s in data.staff}

    # 1. 割当が実在 id を指すか
    # 2. 各スロットの割当スタッフ: available か + required_skills を満たすか
    # 3. 週合計勤務時間 ≤ max_weekly_hours
    # 4. 連続勤務日数 ≤ max_consecutive_days   ← §3
    # 5. soft: requested_days_off の日に入っていないか

    metrics = {"labor_cost": _labor_cost(data, sol),
               "day_off_satisfaction": _day_off_satisfaction(data, sol)}
    return out, metrics
```

補助関数(すべて純粋、`structure.py` 内):

| 関数 | 返すもの |
| --- | --- |
| `_distinct(staff_ids)` | 同一スロットの二重登録を 1 人に潰したリスト |
| `_slot_hours(data)` | `{slot_id: end_hour - start_hour}` |
| `_hours_by_staff(data, sol)` | `{staff_id: 週合計勤務時間}` |
| `_working_days_by_staff(data, sol)` | `{staff_id: {勤務日の集合}}` |
| `_longest_consecutive_run(days)` | 暦日として連続する最長勤務日数(§3) |
| `_labor_cost` / `_day_off_satisfaction` | metric 値 |

---

## 3. 連続勤務日数 ── 素の日次スキャン(Sliding Window は使わない)

```python
def _longest_consecutive_run(days: set[str]) -> int:
    if not days:
        return 0
    ordered = sorted(date.fromisoformat(d) for d in days)   # ← 2-1 の day validator が効く
    longest = run = 1
    for prev, cur in pairwise(ordered):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)
    return longest
```

`itertools.pairwise` + `datetime.date` の引き算だけ。README §8 の **Sliding Window
プリミティブは Phase 6**(Backtracking ソルバーが「候補を 1 手進めるたびに連続勤務日数が
超えていないか」を逐次判定するのに使う)。**事後の検証**は完成した割当を 1 回スキャンする
だけなので、そのプリミティブに依存しない ── Phase 6 への前方依存を作らない。

> `date.fromisoformat` が使えるのは `Phase-2-1` の `_day_is_iso_date` validator が入口で
> 保証しているから。検証器が入力の形を仮定できるのは Input Validation のおかげ、という
> 層の連携。

---

## 4. metrics ── `labor_cost` と `day_off_satisfaction`

```python
def _labor_cost(data, sol) -> float:
    hours = _slot_hours(data); wage = {s.id: s.hourly_wage for s in data.staff}
    return sum(wage.get(sid, 0.0) * hours.get(slot_id, 0.0)
               for slot_id, ids in sol.assignments.items() for sid in _distinct(ids))

def _day_off_satisfaction(data, sol) -> float:
    # 守れた希望休 ÷ 希望休総数。希望休が無ければ 1.0
```

この 2 つは `objectives`(`minimize labor_cost` / `maximize day_off_satisfaction`)が参照する
metric 名と一致している(`build_shift_problem` の `objectives` を参照)。Phase 6 の
多目的ストラテジーは、この metric を目的関数として最適化する ── 検証器が metric を確定して
おくと、Phase 6 は「どう最小化するか」だけ考えればよい。

---

## 5. 具体例(`build_shift_problem()`)

4 スロット(各 `required_headcount=1`)、スタッフ tanaka(¥1200)/ sato(¥1000)/ ito(¥1100)。
tanaka は `2026-09-02` が希望休。

有効解 `{s1:[tanaka], s2:[sato], s3:[ito], s4:[sato]}`:
- tanaka: s1(day1, 5h)。sato: s2(day1, 5h)+ s4(day2, 5h)= 10h。ito: s3(day2, 5h)。
- 可用性・スキル・週上限(20h)・連続勤務(sato の run=2 ≤ 5)すべて OK
- tanaka は day1 だけ → 希望休(day2)は守られている
- `labor_cost` = 5×1200 + 10×1000 + 5×1100 = **21500**
- `day_off_satisfaction` = 1/1 = **1.0**
- → `status="valid"`

希望休違反解 `{..., s4:[tanaka]}`(`with_days_off_penalty=True`):
- tanaka が day2 の s4 に入る → soft 違反 `respect_days_off`
- `_soft_penalty` = 5.0(問題に `GenericConstraint(kind="respect_days_off", penalty=5.0)` があるため)
- `day_off_satisfaction` = 0/1 = 0.0
- hard 違反は無いので → `status="valid"`(soft は status を変えない)

---

## 6. 既存への変更の当て方(写経手順)

1. `textbook/samples/app/domain/solutions/structure.py` の shift 部分(`verify_shift_structure` +
   補助関数 7 つ)を、`Phase-2-3` で写経した `structure.py` に追記(samples 全文で上書きが楽)。
2. `textbook/samples/tests/fixtures/optimization.py` で既存を上書き(`build_shift_solution` /
   `build_infeasible_shift_problem` 追加、`build_route_problem` に `max_total_weight` 追加、
   `op=` → `operator=`)。Phase 1 側に 「以降 Phase で修正予定」マーカー。
3. `uv run pytest tests/unit/test_verification_service.py` → 緑(shift ケースが増える)。

---

## 7. テスト観点(`textbook/samples/tests/unit/test_verification_service.py` の shift 部分)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `verify_shift_structure` と、それを通した `SolutionVerificationService.verify`
> - **ドライバ**: テスト関数 + `build_shift_problem()` / `build_shift_solution({...})`。
>   shift 解は**手組み**(strategy が無いため)── これはビルダー = ドライバ側
> - **スタブ**: **不要** ── 純粋関数。手組みの `ShiftSolution` は「入力データ」であって
>   テストダブルではない(SUT が呼ぶ下位依存の代役ではなく、SUT への引数そのもの)

| ケース | 期待 |
| --- | --- |
| 有効な shift 解 | `valid` / `metrics["labor_cost"] == 21500` / `day_off_satisfaction == 1.0` |
| スロット人数不足 | `invalid`(`staffing` ── `Phase-2-3` のチェッカー) |
| 非 available スロットに割当 | `invalid`(`"unavailable"` を含むメッセージ) |
| 週合計 > `max_weekly_hours` | `invalid`(`"max_weekly_hours"`) |
| 連続勤務 > `max_consecutive_days` | `invalid`(`"consecutive"`) |
| 希望休の日に割当(soft) | `valid` / `soft_penalty == 5.0` / `day_off_satisfaction == 0.0` |

`uv run pytest tests/unit/test_verification_service.py` /
`uvx pyright app/domain/solutions/structure.py`。

---

## 8. まとめ

- `verify_shift_structure`: 実在 id / 可用性 / スキル / 週勤務時間 / 連続勤務日数(hard)、
  希望休(soft)、`labor_cost` / `day_off_satisfaction`(metrics)。
- 連続勤務日数は完成した割当の 1 回スキャン ── Sliding Window プリミティブ(Phase 6 の
  ソルバー用)には依存しない。
- 消費者は `POST /verify`(`Phase-2-5`)と手組み fixture。shift strategy は Phase 6 だが
  検証器はここで完成させる。

次章([Phase-2-5](./Phase-2-5.md))では、作業単位 2-5 ── `POST /api/v1/verify` を生やす。
