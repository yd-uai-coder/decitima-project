# Phase 9-7: registry + select + end-to-end + プロパティテスト(作業単位 9-7)

## この章のゴール

`registry.py` に 5 strategy を登録し、`select_strategy` に既定分岐を足して
validate→select→solve→verify の end-to-end パイプラインを通す。`build_scaled_logistics_problem`
(9-1)を使ったプロパティテストで、`brute_force` を正解オラクルに他 4 strategy の質を比較する
── これで **6 つ目の problem_type `logistics_planning` が端から端まで通る**。

**この章で作成 / 更新するファイル**: `tests/unit/test_logistics_strategies.py`(新規)。
**既存への変更**(現行版は samples): `app/algorithms/registry.py`、
`app/services/algorithm_selection.py`、`tests/unit/test_algorithm_selection.py`。

---

## 1. registry ── 手実装を先頭に

```python
# app/algorithms/registry.py(追加)
"logistics_planning": [  # (Phase 9-7)
    KnapsackDpLogisticsStrategy(),
    GreedyLogisticsStrategy(),
    BranchAndBoundLogisticsStrategy(),
    BruteForceLogisticsStrategy(),
    PulpMilpLogisticsStrategy(),
],
```

他 problem_type と同じ並び順の作法 ── **手実装を先頭に**。`find_strategy` の `requested`未指定時は先頭(`knapsack_dp`)にフォールバックする。

---

## 2. select_strategy ── 既定は knapsack_dp

```python
# app/services/algorithm_selection.py(追加)
if problem.problem_type == "logistics_planning":  # (Phase 9-7)
    # 既定は Knapsack DP(高速)。厳密確認は ?algorithm=brute_force、
    # 台数最小化は ?algorithm=pulp_milp を明示 request
    return "knapsack_dp"
```

travel(既定 `knapsack_dp`)と同じ判断 ── 高速な近似を既定にし、厳密解や別目的関数の
ソルバーは明示的な `?algorithm=` request でのみ使う。project(資源制約の有無で分岐)やroute(負辺・座標の有無で分岐)のような**問題特性に基づく自動切り替えはしない** ──
logistics は「容量が厳しいから branch_and_bound」のような単純な閾値では判断しづらいため(進行のルール #17 の判定基準に照らし、いま自動切り替えを駆動する実在の要求は無い)。

---

## 3. プロパティテスト ── quality_ratio と教材の核の実演

```python
# tests/unit/test_logistics_strategies.py(要点。全文は samples)
def test_handwritten_strategies_never_beat_the_brute_force_oracle() -> None:
    """brute_force が真の最適。他の手実装3本がそれを下回ることはあり得ない。"""

def test_knapsack_dp_can_lose_to_greedy_on_travel_distance() -> None:
    """教材の核: knapsack_dp は容量だけを見て詰めるので、地理的に離れた組合せを選び、
    greedy より総距離で劣ることがある(容量違反にはならない)。"""

def test_pulp_milp_uses_no_more_vehicles_than_any_handwritten_strategy() -> None:
    """pulp_milp は使用台数を最小化するので、他の strategy が使う台数以下になるはず。"""
```

- `test_knapsack_dp_can_lose_to_greedy_on_travel_distance` は 20 seed の乱数生成で`knapsack_dp` が `greedy` に距離で劣る例が実際に発生することを確認する(検証時の実測では20 seed 中 10 seed で発生 ── 十分頑健で、たまたま揃わないような偶然の一致ではない)。
  Phase 7/8 のように 1 つの手計算 fixture で厳密な数値を示す代わりに、Phase 4 の
  `test_networkx_matches_handwritten_dijkstra_property` と同じ「乱数プロパティで実演する」
  方式を採る ── 割当の組合せが多く、手計算で「必ずこの差が出る」例を作るのが煩雑なため。
- `test_pulp_milp_uses_no_more_vehicles_than_any_handwritten_strategy` は fixture 規模(n=6)では手実装 4 本と pulp_milp が同じ使用台数(2 台)に一致する ── これは`test_pulp_logistics.py`(9-6)の「3 台目の余裕があっても 2 台に収める」検証と同じ性質の問題(容量的に最小台数が一意)。**手実装がより多くの台数を使ってしまう例は、より大きな規模(配送先 8〜10 件)で実在する**ことを教材著者側で確認済み(`knapsack_dp` / `greedy` が3 台使うところを `pulp_milp` が 2 台に収める)── ただし `BruteForceLogisticsStrategy` を含めた比較はその規模だと数秒かかるため、高速に回る fixture 規模のテストに留め、質的な優位性は本文で言及するに留める。

---

## 4. まとめ

- `logistics_planning` problem_type が **validate → select → solve → verify** の全経路を通った
  ── これで DeciTima は 6 つの実問題ドメインを持つ。
- 5 strategy(手実装 4 + 産業ソルバー 1)は Phase 4〜7 のプリミティブの組み合わせだけで
  実装され、Phase 9 で新規に追加したプリミティブは実質無い。
- `knapsack_dp`(容量だけの上界)と `pulp_milp`(台数最小化)は、それぞれ異なる軸で
  「見えていないもの」がある ── 前者は移動距離、後者は経路順序の最適性。この非対称性が
  README §8/§14 の「2 トラック比較」「LLM vs Algorithm 比較」の土台になる。

## テスト観点(`textbook/samples/tests/unit/test_logistics_strategies.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14)
> 
> - **対象**: `select_strategy`、`REGISTRY["logistics_planning"]`、
>   validate→select→solve→verify のパイプライン、5 strategy の比較
> - **ドライバ**: このテスト関数。`build_logistics_problem` / `build_scaled_logistics_problem`
>   (9-1)で入力生成
> - **スタブ**: **不要** ── strategy / validation / verification はすべて純粋
>   (`test_mst_strategies.py` / `test_travel_strategies.py` と同じ)

| ケース                                      | 期待                                                      |
| ---------------------------------------- | ------------------------------------------------------- |
| `REGISTRY["logistics_planning"]`         | 5 strategy が手実装優先の順で登録                                  |
| `find_strategy` の既定                      | `knapsack_dp`                                           |
| `select_strategy` の既定                    | `knapsack_dp`                                           |
| `select_strategy(requested="pulp_milp")` | `pulp_milp`                                             |
| end-to-end パイプライン                        | `status == "valid"`、`produced_by.name == "knapsack_dp"` |
| `total_distance` に厳しい上限                  | Verification が `invalid`                                |
| 4 手実装の決定論                                | 同じ入力 → 完全に同じ出力                                          |
| 手実装 3 本 vs `brute_force` オラクル(6 seed)    | オラクルを下回ることはない                                           |
| `knapsack_dp` vs `greedy`(20 seed)       | 少なくとも1 seed で `knapsack_dp` が劣る                         |
| `pulp_milp` の使用台数                        | 他 4 strategy 以下(fixture 規模では同数)                         |

`uv run pytest tests/unit/test_logistics_strategies.py tests/unit/test_algorithm_selection.py` /
`uvx pyright app/algorithms app/services`。

---

次章([Phase-9-8](./Phase-9-8.md))では、作業単位 9-8 ── ジョブキュー基盤(`arq` + Redis)。
problem_type に依存しない横断インフラとして `POST /api/v1/jobs` / `GET /api/v1/jobs/{id}` を
新設し、既存の同期 `POST /api/v1/solve` と併存させる。
