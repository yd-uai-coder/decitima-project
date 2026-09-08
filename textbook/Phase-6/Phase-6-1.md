# Phase 6-1: 重み付き和の評価器 ── `objectives/`(Phase 1 からの宿題)(作業単位 6-1)

## この章のゴール

多目的(人件費最小化 / 希望休最大化 / 勤務時間均等化)を **1 つのスカラー**にまとめる評価器を作る。
Greedy / Backtracking / B&B はこのスカラーを最小化することで「良い割当」を選ぶ。

`app/domain/objectives/` は **Phase 1 で一度作って撤回**した(当時 registry に載る唯一の strategy= Dijkstra は単一目的で消費者がいなかった。`Phase-0-2.md` §2.5 / `Phase-1-1.md` §1 のマーカー)。
Phase 6 で **初の多目的ストラテジー**という消費者を得て復活する。

**この章で作成 / 更新するファイル**: `app/domain/objectives/weighted_sum.py`、
`app/domain/objectives/__init__.py`、
`app/domain/solutions/shift_metrics.py`(shift の metrics 計算を集約した公開 leaf)、
`tests/unit/test_weighted_sum.py`。
**既存ファイルへの変更**(現行版は samples):
- `app/domain/solutions/shift_scheduler.py` ── `type Assignment = dict[str, list[str]]` を追加し
  `ShiftSolution.assignments: Assignment` に(共有語彙。挙動不変)。Phase 1 で凍結した葉を触るが、
  shift を解く `algorithms` と検証する `domain` の両方が循環なしで import できる唯一の家がここ(#17)。
- `app/domain/solutions/structure.py` ── `verify_shift_structure` は `shift_metrics.py` を呼ぶだけに。
  metrics ヘルパ 6 本を移設、`hour_variance` を追加。
- `tests/unit/test_verification_service.py` ── hour_variance のケース。

写経順序: `shift_scheduler.py`(現行版)→ `weighted_sum.py` → `__init__.py` → `shift_metrics.py`
→ `structure.py`(現行版)→ テスト 2 本。

対応サンプル: 上記すべて。設計は `Phase-0-2.md` §3、README §12.2。

---

## 1. `weighted_sum` ── minimize 向きのスカラー

```python
# app/domain/objectives/weighted_sum.py(要点。全文は samples)
def _orient(value: float, sense: str) -> float:
    return -value if sense == "maximize" else value

def weighted_sum(objectives: Iterable[Objective], metrics: dict[str, float]) -> float:
    total = 0.0
    for obj in objectives:
        value = metrics.get(obj.target, 0.0)          # 目的が metrics に無ければ寄与 0
        total += obj.weight * _orient(value, obj.sense)
    return total
```

- `Objective(sense, target, weight)` は `problem.py` の型(`Phase-0-2.md` §3)。`domain/objectives/` は**ロジックだけ、型は置かない**(`Phase-0-3.md` §2.3)。
- **「小さいほど良い」向きにそろえる**: minimize 目的はそのまま `+w·f`、maximize 目的は符号反転
  `−w·f`。こうすると探索アルゴリズムは常に「スカラーを最小化」すればよい。
- `Phase-0-2.md` §3 の約束「アルゴリズムは重み付き和 `Σ wᵢ·fᵢ` を最適化する」の実装。

### 既知の限界 ── スケール差

`labor_cost`(数千〜数万)と `day_off_satisfaction`(0〜1)はスケールが桁違い。**素の重み付き和は`labor_cost` に支配される**。実務では各 metric を基準解比 / min-max で `[0,1]` に正規化してから足す。
本実装は素の重み付き和に留め、`weight` でスケールを吸収する前提(fixture の `0.7` / `0.3`、`hour_variance` の `100` はそのつもりの手調整値)。正規化は将来の改善余地
(`Phase-6-introduction.md` §7 の非スコープ)。

- `domain` 層 = 純粋。`services` / `repositories` を import しない。registry には載らない。

---

## 2. shift の metrics 計算を `shift_metrics.py` に集約(現行版)

Phase 2-4 の教訓(§4):「**検証器が metric を先に確定しておくと、Phase 6 は『どう最小化するか』だけ考えればよい**」。Phase 2 は `labor_cost` / `day_off_satisfaction` を `verify_shift_structure` の中で計算していた。ここで 3 つ目の目的「勤務時間均等化」が参照する `hour_variance` を足すが、**同時に計算コード自体を 1 箇所に集約する**。

理由 ── この式(`labor_cost = Σ wage·hours` など)は **domain の事実**で、消費者が 2 系統ある:

1. **Verification**(`verify_shift_structure`)── 最終解の metrics を確定する
2. **探索**(`algorithms/scheduling` の 4 strategy)── 候補割当を `weighted_sum` で採点する(6-3〜6-7)

Phase 2 版は 1 だけの消費者を想定して `verify_shift_structure` にインラインしていた。Phase 6 で 2 が現れる。**同じ式を 2 箇所に書くと drift する**(検証で報告する値と探索が最適化する値がズレる)ので、新しい公開 leaf `app/domain/solutions/shift_metrics.py` に出し、双方が import する。

```python
# app/domain/solutions/shift_metrics.py(要点。全文は samples)
from app.domain.solutions.shift_scheduler import Assignment   # slot_id -> [staff_id, ...] の共有語彙
def distinct(ids: Iterable[str]) -> list[str]: ...                    # 二重登録を 1 人に
def hours_by_staff(data, assignments) -> dict[str, float]: ...        # 0 割当も 0.0 で埋める
def working_days_by_staff(data, assignments) -> dict[str, set[str]]: ...
def labor_cost(data, assignments) -> float: ...                      # README §12.2 第 1 目的
def day_off_satisfaction(data, assignments) -> float: ...            # 第 2 目的
def hour_variance(data, assignments) -> float: ...                   # 第 3 目的(母分散)
def assignment_metrics(data, assignments) -> dict[str, float]:       # 上の 3 つを 1 dict に
    return {"labor_cost": ..., "day_off_satisfaction": ..., "hour_variance": ...}
```

```python
# app/domain/solutions/structure.py(現行版)
from app.domain.solutions.shift_metrics import (
    assignment_metrics, distinct, hours_by_staff, working_days_by_staff,
)

def verify_shift_structure(data: ShiftData, sol: ShiftSolution) -> tuple[list[ConstraintViolation], dict[str, float]]:
    assignments = sol.assignments        # ← 生 dict を 1 度だけ取り出す。以降すべてこれを渡す
    ...
    for sid, hours in hours_by_staff(data, assignments).items(): ...          # 週勤務時間チェック
    working_days = working_days_by_staff(data, assignments)                   # 連続日数 + 希望休
    ...
    return out, assignment_metrics(data, assignments)                        # metrics は shift_metrics に丸投げ
```

**`verify_shift_structure` の変わった行**(Phase 5 版 → 現行版。**hard/soft チェックの本体は不変**):

| 箇所 | Phase 5 版(before) | 現行版(after) |
| --- | --- | --- |
| 関数先頭 | ─ | `assignments = sol.assignments`(1 度だけ) |
| 週勤務時間ループ | `_hours_by_staff(data, sol)` | `hours_by_staff(data, assignments)` |
| 連続日数 / 希望休 | `_working_days_by_staff(data, sol)` | `working_days_by_staff(data, assignments)` |
| 末尾の metrics | `metrics = {"labor_cost": _labor_cost(data, sol), ...}` / `return out, metrics` | `return out, assignment_metrics(data, assignments)` |
| 二重登録の除去 | `_distinct(...)` | `distinct(...)`(引数は不変) |

> **写経の罠 ── 引数が `sol` から `assignments` に変わっている**。`shift_metrics` の関数は
> **ShiftSolution でなく生の割当 dict**(`dict[str, list[str]]`)を取る ── strategy が探索中の
> dict をそのまま渡せるようにするため。ヘルパ名だけ機械的に写して `hours_by_staff(data, sol)` と
> すると `AttributeError: 'ShiftSolution' object has no attribute 'items'` が `shift_metrics.py` から
> 出る。`verify_shift_structure` は先頭で `assignments = sol.assignments` を 1 度取り出し、
> 以降は全部 `assignments` を渡す。`uvx pyright` なら `reportArgumentType` で気づける。

- **`shift_metrics` の関数は `assignments: Assignment`(= `dict[str, list[str]]`)を受ける**(生の割当)。
  `verify_shift_structure` は先頭で `sol.assignments` を取り出して渡し、strategy は探索中の割当を直接渡す。
- **`type Assignment` は `shift_scheduler.py` に置く** ── `ShiftSolution.assignments` の型そのもの。
  検証する `domain`(`shift_metrics`)も解く `algorithms`(`scheduling/common` と 4 strategy)も
  **この葉から直接 import する**(route が `Segment` を定義元 `segments.py` から import するのと同じ)。
  algorithms 側に置くと `domain → algorithms` 禁止で `shift_metrics` が import できず循環する(Q38)。
- **0 割当のスタッフも母数に含める**(`hours_by_staff`)── 一部のスタッフに偏らせる割当にペナルティ(= 均等化)。
- 既存の 5 つの hard / 1 soft チェックには**一切触らない**(振る舞い不変。`test_verification_service.py` のアサーションはそのまま)。移動したのは metrics 計算ヘルパだけ。
- **連続勤務日数の判定は移さない** ── `structure._longest_consecutive_run`(事後スキャン)は残す。`domain` は `patterns/sliding_window`(探索の逐次判定)を import できないためレイヤー上分ける(`Phase-2-2.md` §3.3)。これは重複でなく必然。
- 共有 `textbook/samples/` の `app/domain/solutions/structure.py` と `shift_scheduler.py` は
  冒頭コメントに `改訂 Phase 6` があり、この Phase での変更(`Assignment` 追加 / metrics 抽出)は
  §2 と `#(Phase 6-1)` タグで示される(#12・#17)。

---

## 3. まとめ

- `weighted_sum` は多目的を「小さいほど良い」1 スカラーに。minimize は `+w·f`、maximize は `−w·f`。
- スケール差の落とし穴は明示(正規化は将来)。
- `objectives/` は Phase 1 で撤回 → Phase 6 で消費者(shift strategy)を得て復活。
- shift の metrics 計算を `domain/solutions/shift_metrics.py`(公開 leaf)に集約。`verify_shift_structure`
  と探索の 4 strategy が**同じコード**を呼ぶので値が drift しない。`hour_variance` もそこに実装。
- 連続日数判定(`_longest_consecutive_run`)は移さない ── レイヤー境界(`domain → algorithms` 禁止)による必然。

## テスト観点(`textbook/samples/tests/unit/{test_weighted_sum,test_verification_service}.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> **`test_weighted_sum.py`**
> 
> - **対象**: `weighted_sum`(純粋関数)
> - **ドライバ**: このテスト関数(`Objective` と metrics dict を直接渡す)
> - **スタブ**: **不要** ── 外部依存なし
> 
> **`test_verification_service.py`**(hour_variance 分 ── #16 のリファクタ追従も兼ねる)
> 
> - **対象**: `verify_shift_structure` の metrics に `hour_variance` が入り、均等な割当ほど小さい。
>   加えて **metrics 計算を `shift_metrics.py` に移しても `labor_cost` / `day_off_satisfaction` の
>   数値が Phase 2 と一致する**(公開挙動不変 ── アサーションは変えない。赤なら写経ミス)
> - **ドライバ**: `build_shift_problem` + `build_shift_solution`(手組み)
> - **スタブ**: **不要** ── `SolutionVerificationService` は DB / Redis を触らない
> - `shift_metrics.py`(この章の新規ファイル)は `test_weighted_sum.py` では触れないが、
>   `test_verification_service.py` が `verify_shift_structure` 経由で必ず import する(#15)。
>   **第一の番人**: `structure.py` の写経で引数を `sol` のままにすると、この 6-1 のテストが
>   `AttributeError: 'ShiftSolution' object has no attribute 'items'` でその場で赤になる
>   (`hours_by_staff` の `assignments.items()`)── 6-3 以降の strategy テストまで持ち越さない。

| ケース                      | 期待                              |
| ------------------------ | ------------------------------- |
| minimize 目的              | `weighted_sum` の寄与は `+w·metric` |
| maximize 目的              | 符号反転 `−w·metric`                |
| 目的の target が metrics に無い | 寄与 0(その目的は無視)                   |
| 良い割当 vs 悪い割当             | `weighted_sum` が「良い < 悪い」       |
| valid な shift 解          | `metrics["hour_variance"] >= 0` |
| 均等な割当 vs 偏った割当           | `hour_variance` が「均等 < 偏り」      |

`uv run pytest tests/unit/test_weighted_sum.py tests/unit/test_verification_service.py` /
`uvx pyright app/domain`。

---

次章([Phase-6-2](./Phase-6-2.md))では、作業単位 6-2 ── スケジューリング・プリミティブ。
Backtracking が「連続勤務日数が上限を超えないか」を毎手 O(1) で判定する `sliding_window` と、
「時間帯別の在籍人数」を O(スロット数) で構築する `difference_array`(imos 法)を作る。
