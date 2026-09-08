# Phase 6-2: スケジューリング・プリミティブ ── Sliding Window / Difference Array(作業単位 6-2)

## この章のゴール

Backtracking / B&B / CP-SAT が内部で使う 2 つの技法を、registry に載らない**素の純粋関数**として作る
(`Phase-0-4.md` §2.4 の「2 層」の下側。README §8)。

- **Sliding Window** ── 連続勤務日数のチェック。事後検証(Phase 2 の
  `structure._longest_consecutive_run`)は `itertools.pairwise` の 1 回スキャンで済むが、探索は「候補を 1 手進めるたび」に判定するので、毎手 O(1)〜O(K) の**逐次判定**が要る。
- **Difference Array(差分法 / imos 法)** ── 時間帯別の在籍人数。各スロットが `[start, end)` をカバーするので、割り当てられたスロットぶんだけ区間加算し、時刻ごとの在籍人数配列を O(スロット数) で作る。

**この章で新規作成するファイル**: `app/algorithms/patterns/sliding_window.py`、
`app/algorithms/patterns/difference_array.py`、`tests/unit/test_scheduling_primitives.py`。
**既存ファイルへの変更**: `app/algorithms/patterns/__init__.py`(docstring を「Phase 6 で実装」に)。

対応サンプル: 上記すべて。

---

## 1. `sliding_window.py`

```python
# app/algorithms/patterns/sliding_window.py(要点。全文は samples)
def max_consecutive_days(days: Iterable[str | date]) -> int:
    """勤務日集合の最長連続日数。窓 = 途切れない暦日の並び。空なら 0。"""
    ords = _ordinals(days)                       # ISO 日付 → 日単位の序数
    if not ords:
        return 0
    longest = run = 1
    for prev, cur in zip(ords, ords[1:], strict=False):
        run = run + 1 if cur - prev == 1 else 1  # 途切れたら窓をリセット
        longest = max(longest, run)
    return longest

def run_length_at(present_ordinals: set[int], point: int) -> int:
    """present_ordinals に point が在るとして、point を含む連続ランの長さ(O(ラン長))。"""
    length = 1
    left = point - 1
    while left in present_ordinals:
        length += 1; left -= 1
    right = point + 1
    while right in present_ordinals:
        length += 1; right += 1
    return length
```

- `max_consecutive_days` ── 完成割当に対する事後スキャン。窓 = 「途切れない暦日の並び」で、gap が来たら窓の長さを 1 にリセットする degenerate な sliding window。
- `run_length_at` ── **逐次判定用**。Backtracking がスタッフに日 `d` を仮追加したとき、
  `run_length_at(ords | {d}, d) <= max_consecutive_days` で「この 1 手で上限超過するか」を判定する。
  窓を `d` から左右に広げるだけなので O(連続ラン長)。
- `to_ordinal(day)` ── ISO 日付 → 序数。`run_length_at` に渡す前の変換。
- **Phase 2 の `_longest_consecutive_run` は書き換えない**。事後検証はそのまま、探索の逐次判定はここ ── 用途が違う(`Phase-2-2.md` §3.3 の予告どおり)。

---

## 2. `difference_array.py`(imos 法)

```python
# app/algorithms/patterns/difference_array.py(要点)
def range_add(size: int, updates: Iterable[tuple[int, int, float]]) -> list[float]:
    """updates の各 (l, r, delta) を「[l, r) に +delta」として適用し、長さ size の配列を返す。"""
    diff = [0.0] * (size + 1)
    for left, right, delta in updates:
        left = max(left, 0); right = min(right, size)
        if left >= right:
            continue
        diff[left] += delta            # imos 法: 区間の左端で +、右端で −
        diff[right] -= delta
    out, running = [], 0.0
    for i in range(size):
        running += diff[i]             # 累積和で復元
        out.append(running)
    return out
```

- naive に「毎区間ループ」だと O(区間数 × 幅)。**imos 法は O(区間数 + サイズ)** ── 区間の左端で
  `+delta`、右端で `-delta` を記録し、最後に 1 回の累積和で全要素を確定する。**累積和(Prefix Sum)の対**。
- Shift での消費者(6-3): `scheduling/common.py::on_duty_by_hour` が、割り当てられた各スロットの
  `[start_hour, end_hour)` に `+headcount` を区間加算して、per-(day, hour) の在籍人数配列を作る。
  `min_hourly_coverage` の下地になる。

>  IMOS法とは「区間全体に値を加算する」という処理を、端点だけに記録して、最後に累積和で復元する方法。

>  例）range_add(5, [(1,3,2.0), (2,4,1.0)])

> 1. 差分を記録(各 update は O(1))
>    diff = [0, 0, 0, 0, 0, 0] # 長さ size+1 = 6
>    
>    (1, 3, 2.0): diff[1] += 2 # 「index 1 から +2 を始める」
>     diff[3] -= 2 # 「index 3 で +2 をやめる」
>     diff = [0, 2, 0, -2, 0, 0]
>    
>    (2, 4, 1.0): diff[2] += 1
>     diff[4] -= 1
>     diff = [0, 2, 1, -2, -1, 0]
>    
> 2. 累積和で復元(1 回のスキャン O(size))
>    
>    | i   | running += diff[i] | out[i] | 意味                     |
>    | --- | ------------------ | ------ | ---------------------- |
>    | 0   | 0 + 0 = 0          | 0      | 0 を含む区間なし              |
>    | 1   | 0 + 2 = 2          | 2      | [1,3) が始まった            |
>    | 2   | 2 + 1 = 3          | 3      | [1,3) と [2,4) が両方アクティブ |
>    | 3   | 3 + (−2) = 1       | 1      | [1,3) が終わり、[2,4) だけ残る  |
>    | 4   | 1 + (−1) = 0       | 0      | [2,4) も終わった            |
> 
> 

---

## 3. まとめ

- `sliding_window`: `max_consecutive_days`(事後)/ `run_length_at`(探索の逐次判定、O(ラン長))。
- `difference_array`: `range_add` の imos 法で区間加算を O(区間数 + サイズ) に。累積和の対。
- どちらも registry 非搭載の純粋関数。Phase 2 の事後検証コードには触れない。

## テスト観点(`samples/tests/unit/test_scheduling_primitives.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `max_consecutive_days` / `run_length_at` / `to_ordinal` / `range_add`(すべて純粋関数)
> - **ドライバ**: このテスト関数(生の値を直接渡す)
> - **スタブ**: **不要** ── 外部依存なし
> - この 4 本が `scheduling/common.py` と各 strategy の写経ミスの第一の番人(#15)

| ケース                                                       | 期待                       |
| --------------------------------------------------------- | ------------------------ |
| `max_consecutive_days(["09-01","09-02","09-03","09-05"])` | 3(01-02-03 が連続、05 で途切れる) |
| `max_consecutive_days([])`                                | 0                        |
| `run_length_at({10,11,12,14}, 11)`                        | 3                        |
| `range_add(5, [(1,3,2),(2,4,1)])`                         | `[0,2,3,1,0]`            |
| 範囲外の update                                               | クランプ(範囲内だけ加算)            |
| 空区間 `(2,2,5)`                                             | 無視                       |

`uv run pytest tests/unit/test_scheduling_primitives.py` / `uvx pyright app/algorithms/patterns`。

---

次章([Phase-6-3](./Phase-6-3.md))では、作業単位 6-3 ── `GreedyShiftStrategy` と共通足回り
`scheduling/common.py`。スロットを「厳しい順」に見て最安のスタッフを割り当てる速い近似。
`registry` に Greedy を配線し、`select_strategy` に shift 分岐を足す。
