# Phase 8-2: Critical Path Method(CPM)プリミティブ(作業単位 8-2)

## この章のゴール

各タスクの所要時間と依存 DAG (Directed Acyclic Graph：有向非巡回グラフ) から、**プロジェクト全体が最短で何日で終わるか(makespan)**、**どのタスクが律速か(クリティカルパス)**、**各タスクをどれだけ遅らせても全体に響かないか(slack)**を求める。これが **Critical Path Method(CPM)** ── トポロジカル順の 1 往復で全部出る。

> **ES / EF(最早開始 / 最早終了)** ── 先行タスクが全部終わったら即開始した場合の時刻。
> **LS / LF(最遅開始 / 最遅終了)** ── makespan を伸ばさずに済む、いちばん遅い開始 / 終了。
> **slack(余裕 / フロート)** ── `LS − ES`(= `LF − EF`)。0 なら「1 日遅れると全体が 1 日遅れる」= クリティカル。

**この章で作成 / 更新するファイル**:
`app/algorithms/scheduling/critical_path.py`(新規)、`tests/unit/test_critical_path.py`(新規)。
既存ファイルへの変更は無い ── 自己完結する。`cpm` は **`topological_sort`(8-1)にだけ依存**し、所要時間と後続を**生の dict** で受け取る(`ProjectData` は 8-3 の葉なので触らない ── `floyd_warshall`が `Adjacency` 型だけを使うのと同じ設計。進行のルール #15)。

対応サンプル: `textbook/samples/app/algorithms/scheduling/critical_path.py`、
`textbook/samples/tests/unit/test_critical_path.py`。設計は README §12.4 / §19 Phase 8。

---

## 1. 前進パス ── 最早開始 / 最早終了(トポロジカル順)

```python
# app/algorithms/scheduling/critical_path.py(要点。全文は samples)
@dataclass(frozen=True)
class CpmResult:
    order: list[str]
    predecessors: dict[str, list[str]]   # priority_list(8-4)が使う
    earliest_start: dict[str, int]
    earliest_finish: dict[str, int]
    latest_start: dict[str, int]
    latest_finish: dict[str, int]
    slack: dict[str, int]
    critical_path: list[str]
    makespan: int
    relaxations: int                     # strategy が _ops に使う

def cpm(durations, successors) -> CpmResult:
    order = topological_sort(successors)          # ← 8-1
    predecessors = {t: [] for t in order}
    for t in order:
        for nxt in successors.get(t, []):
            predecessors[nxt].append(t)

    es, ef = {}, {}
    for t in order:                               # トポロジカル順 = 先行が必ず先に確定済み
        start = max((ef[p] for p in predecessors[t]), default=0)
        es[t], ef[t] = start, start + durations.get(t, 0)
    makespan = max(ef.values(), default=0)
    ...
```

**`CpmResult` の各メンバ**(fixture 例: A=3, B=2, C=4, D=2, E=1 / 依存 A→C, B→D, C→E, D→E):

| メンバ                   | 意味                                                                   | fixture の値                        | 下流の消費者                                                                 |
| --------------------- | -------------------------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------- |
| `order`               | トポロジカルソートの結果。全辺 u→v で u が v より前。前進パスはこの順、後退パスは逆順                     | `["B","D","A","C","E"]`           | `ProjectSolution.task_order`                                           |
| `predecessors`        | 各タスク → 直前の先行タスク群。前進パス `ES[t]=max(EF[p])` に使う。`CpmResult` に載せて再計算させない | `{A:[],B:[],C:[A],D:[B],E:[C,D]}` | `priority_list`(先行完了 = ready time)                                     |
| `earliest_start`(ES)  | 最早開始。「全先行が終わったら即開始」した時刻                                              | `{A:0,B:0,C:3,D:2,E:7}`           | `cpm` / `cpm_nx` の実開始時刻                                                |
| `earliest_finish`(EF) | 最早終了 = `ES + duration`                                               | `{A:3,B:2,C:7,D:4,E:8}`           | `critical_chain`(律速辺 `EF[p]==ES[s]` の判定)                               |
| `latest_start`(LS)    | 最遅開始。makespan を伸ばさずに済むいちばん遅い開始                                       | `{A:0,B:3,C:3,D:5,E:7}`           | `priority_list` の優先順位(LS 昇順 = 余裕の少ない順)                                 |
| `latest_finish`(LF)   | 最遅終了 = `LS + duration` = `min(LS[s] for s in succ)`(後続なしは makespan)  | `{A:3,B:5,C:7,D:7,E:8}`           | slack の別式 `LF−EF` の裏取り(直接の消費者はテスト)                                     |
| `slack`               | 余裕(トータルフロート)= `LS − ES`(= `LF − EF`)。0 = クリティカル                      | `{A:0,B:3,C:0,D:3,E:0}`           | `ScheduledTask.slack`(4 strategy 全部)/ critical 集合                      |
| `critical_path`       | slack 0 を起点 → 終点へ律速辺で 1 本に(複数あれば後続 id 昇順で単一。§3)                      | `["A","C","E"]`                   | `ProjectSolution.critical_path`                                        |
| `makespan`            | 全体所要 = `max(EF)`。「資源が無限なら何日で終わるか」の下界(§4)                             | `8`                               | `cpm` / `cpm_nx` の暫定 makespan(最終値は `project_solution` が実 finish から再計算) |
| `relaxations`         | 前進 + 後退パスで辺を触って ES/LF を更新した回数。4 辺 × 2 パス = 8                         | `8`                               | `cpm` strategy の `metrics["_ops"]`(仕事量の目安。time/memory とは比較しない)         |

いずれも `int`(`duration: int` に限定したため。8-3)。`ScheduledTask` 側の `start` / `finish` /
`slack` は `float`(`metrics` 辞書 / `weighted_sum` に合わせる)。`CpmResult` は `frozen=True` ──
strategy に渡した後は不変で、4 つの strategy が「開始時刻の決め方」だけを差し替えて共有する。

- **なぜトポロジカル順で回せるか**: `ES[t]` は全先行の `EF` の最大値。トポロジカル順なら `t` を処理する時点で先行はすべて処理済み ── DP の「小さい部分問題から」と同じ(Phase 7 の DP 語彙)。
- 先行が無いタスクは `ES = 0`。makespan = 全 `EF` の最大値。

---

## 2. 後退パス ── 最遅開始 / 最遅終了(逆トポロジカル順)

```python
    lf, ls = {}, {}
    for t in reversed(order):                     # 逆順 = 後続が必ず先に確定済み
        finish = min((ls[s] for s in successors.get(t, [])), default=makespan)
        lf[t], ls[t] = finish, finish - durations.get(t, 0)
    slack = {t: ls[t] - es[t] for t in order}
```

- `LF[t]` = 全後続の `LS` の最小値(後続を遅らせずに済む、いちばん遅い終了)。後続が無ければ
  `LF = makespan`。逆トポロジカル順なので後続は処理済み。
- `slack[t] = LS[t] − ES[t]`。前進 + 後退で辺を触った回数を `relaxations` に積む(strategy の `_ops`)。

---

## 3. クリティカルパスの復元 ── slack 0 を「律速している辺」で繋ぐ

```python
def critical_chain(order, successors, earliest_finish, earliest_start, critical) -> list[str]:
    # 起点 = クリティカルかつ ES 0(先行クリティカルが無い head)。id 昇順で 1 つ
    head = min((t for t in order if t in critical and earliest_start[t] == 0), default=None)
    ...
    while True:
        nxts = sorted(s for s in successors.get(cur, [])
                      if s in critical and earliest_finish[cur] == earliest_start[s])
        if not nxts: break
        cur = nxts[0]; path.append(cur)
```

- `slack == 0` のタスクは**すべて**「あるクリティカルパス上」にある。そのうち 1 本を、`EF[p] == ES[s]`(p の終了が s の開始を実際に律速している)辺だけ辿って繋ぐ。
  
  > slack == 0 ->「遅れてもよい余裕時間がない」-> 待ち時間なし -> 最短ルート
- **複数のクリティカルパスがあるとき単一を返す**(タイブレーク = 後続 id 昇順)── `bfs_shortest_path`が単一経路を返す方針と同じ(`CLAUDE.md`「未ルール化の確定事項」)。テストは「どのタスクがslack 0 か」の**集合**で別実装(8-6 の networkx)と突き合わせ、chain は完全一致も確認する。

---

## 4. 教材の核 ── CPM の makespan は「資源無視の下界」

CPM は**依存関係だけ**を見て、資源(人・機材)は一切見ない。だから CPM の makespan は
「**資源が無限にあれば** 何日で終わるか」= 実現可能な最短の**下界**。

現実には「A と B は両方リソース 2 を使うが、同時に使えるリソースは 3 まで」のような資源上限がある(RCPSP)。そのとき CPM のスケジュール(全タスクを ES に置く)は資源を超過する ──`cpm` strategy(8-4)はそれをそのまま返し、**Verification が資源超過 hard 違反で `invalid`** にする。
資源を守った実行可能なスケジュールは `priority_list`(8-4)/ `cp_sat`(8-5)。

Phase 7 の対比: 「Knapsack DP は place cost だけで詰める =『移動費用を無視した上界』」↔ 「CPM は依存だけを見る =『資源を無視した下界』」。
**上界も下界も、無視した要素を足すと実行不能になる**。
この構図が Phase 8 の教材の背骨。

---

## 5. まとめ

- CPM = トポロジカル順で前進パス(ES/EF)→ makespan → 逆順で後退パス(LS/LF)→ slack。O(V + E)。
- クリティカルパス = slack 0 を律速辺で 1 本に。複数あれば id 昇順で単一。
- `cpm` は `topological_sort`(8-1)にだけ依存し、生の dict を取る ── `ProjectData`(8-3)に前方依存しない。
- makespan は「資源無視の下界」── 資源上限を足すと `cpm` の解は超過し得る(8-4 の教材の核)。

## テスト観点(`textbook/samples/tests/unit/test_critical_path.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `cpm`(純粋関数。内部で `topological_sort` を呼ぶ)、`critical_chain`
> - **ドライバ**: このテスト関数。所要時間 dict と後続 dict を直接渡す(`ProjectData` は 8-3)
> - **スタブ**: **不要** ── 純粋で外部依存を呼ばない
> - **第一テスト = 統合スモーク**(`test_smoke_known_project_makespan_and_critical_path`)──
>   既知の 5 タスク DAG(fixture と同じ)で `cpm` を 1 回呼び、`makespan == 8` /
>   `critical_path == ["A", "C", "E"]` / `earliest_start` をアサート。前進パスの末尾を消す・
>   後退パスの初期値を 0 にする等の写経ミスは、ここで `makespan` / `critical_path` が狂って
>   即赤になる(Q30 の `_dijkstra_segment` / Q38 の `shift_metrics` と同型の番人)

| ケース                          | 期待                                                      |
| ---------------------------- | ------------------------------------------------------- |
| 既知 DAG(A3→C4→E1、B2→D2→E)     | `makespan == 8` / `critical_path == ["A","C","E"]`      |
| slack                        | 中央のクリティカル(A/C/E)= 0 / B・D = 3                           |
| 最遅開始 / 最遅終了                  | `latest_start["B"] == 3` / `latest_finish["A"] == 3`    |
| 依存なしの並行タスク(A3 / B5 / C2)     | `makespan == 5` / クリティカル = {B}                          |
| 単一タスク / 空プロジェクト              | `makespan == 4` / `makespan == 0`・`critical_path == []` |
| `relaxations`(4 辺 × 前進 + 後退) | `== 8`                                                  |
| `predecessors["E"]`          | `["C", "D"]`(priority_list が使う)                         |

`uv run pytest tests/unit/test_critical_path.py` / `uvx pyright app/algorithms/scheduling`。

---

次章([Phase-8-3](./Phase-8-3.md))では、作業単位 8-3 ── `project_scheduling` problem_type の配線。
`ProjectData` / `ProjectSolution` をユニオンに 1 メンバーずつ足し、semantic 2 チェック、structure
1 arm、`validation.py` に閉路ゲート(`has_cycle`)を追加する。Phase 5-3 / 7-3 と同型で、
新しい DB テーブルは作らない。
