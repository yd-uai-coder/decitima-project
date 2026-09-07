# Phase 2-2: Semantic Validation の一般化(作業単位 2-2)

## この章のゴール

Phase 1 の `ProblemValidationService` は `isinstance(problem.data, RouteData)` のハードコード
分岐で、route の検査だけをインラインで持っていた。shift は素通し。これを:

- problem_type ごとの **検査関数** を `app/domain/problems/semantic.py` に集約
- `SEMANTIC_CHECKS: dict[str, list[検査関数]]` レジストリ(`algorithms/registry.py` と同じ発想)
- `ProblemValidationService.validate` は **レジストリを回すだけ**

に作り替え、**shift の Semantic Validation** を足す。

**この章で新規作成するファイル**: `app/domain/problems/semantic.py`、
`app/algorithms/graph/reachability.py`(§3)。
**既存ファイルへの変更**: `app/services/validation.py`(Phase 1 の実装を全面改訂。現行版は
`samples/app/services/validation.py`。Phase 1 側に「以降 Phase で修正予定」マーカー)。

対応サンプル: `samples/app/domain/problems/semantic.py`,
`samples/app/algorithms/graph/reachability.py`, `samples/app/services/validation.py`。
テストは `samples/tests/unit/test_validation_service.py`(Phase 1 版を改訂 ──
`test_shift_problem_passes_through_for_now` は失効)、`samples/tests/unit/test_reachability.py`(新規)。
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

| 関数                           | 見るもの                                    | infeasible? |
| ---------------------------- | --------------------------------------- | ----------- |
| `check_route_endpoints`      | `start` / `goal` が `nodes` に実在          | No(整合性)     |
| `check_route_edge_endpoints` | 各エッジの `source` / `target` が `nodes` に実在 | No(整合性)     |

到達可能性は **ここに無い**(§3)。

### shift の検査

| 関数                               | 見るもの                                                             | infeasible? |
| -------------------------------- | ---------------------------------------------------------------- | ----------- |
| `check_shift_slot_refs`          | スタッフの `available_slot_ids` が実在スロットを指す                            | No(整合性)     |
| `check_shift_staffing_feasible`  | 各スロットに「入れる」(available かつ必要スキル保持)スタッフが `required_headcount` 人以上いる | **Yes**     |
| `check_shift_skill_coverage`     | 各 `required_skills` を持ち、かつそのスロットに入れるスタッフが存在                      | **Yes**     |
| `check_shift_weekly_hours_cover` | `max_weekly_hours` が最長スロット 1 本分以上                                | **Yes**     |

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
        # SEMANTIC_CHECKSからproblem_typeをキーにcheckに関数を格納するループ
        # -> checkという変数に関数が入っているため引数(problem)で関数が実行される
        # -> 結果をissues配列に格納する。
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
        if isinstance(problem.data, RouteData):        # 到達可能性は「計算」── 詳細は §3
            forbidden = {禁止エッジ id}
            if not route_reachable(problem.data, forbidden):
                infeasible.append("goal ... is unreachable ...")
        if infeasible:
            raise InfeasibleProblemError("; ".join(infeasible))
```

**優先順位**: 整合性 NG があれば `ProblemValidationError` を投げて終わり。無ければ
infeasible をまとめて `InfeasibleProblemError`。Phase 1 の「整合性チェック → 早期 return →到達可能性」と同じ順序を、収集してから判定する形にしただけ。

---

## 3. 到達可能性 ── 計算は `algorithms/`、判定は `services/`

`SEMANTIC_CHECKS` に入れた検査(`check_route_endpoints` 等)は、どれも問題フィールドに対する
**純粋な述語**だ ──「`start` は `nodes` にあるか?」を `in` で見るだけ。だから `domain/` に
置ける。

ところが「禁止エッジを除いても `start`→`goal` に行けるか」は述語ではない。**隣接リストを組んで
BFS を走らせる = グラフ計算**。種類が違う。

### 責務を層で切る

| やること                                                       | どの層か          | 実体                                                                                    |
| ---------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- |
| 到達可能性を**計算する**                                             | `algorithms/` | `route_reachable(data, forbidden) -> bool`(新規 `app/algorithms/graph/reachability.py`) |
| 計算結果を**hard ゲートとして判定する**(NG → `InfeasibleProblemError`)    | `services/`   | `ProblemValidationService.validate` の中                                                |
| (この検査に `domain/` の出番は**無い**。純粋述語だけが domain。計算は algorithms) | ―             | ―                                                                                     |

```python
# app/algorithms/graph/reachability.py(全文は samples。build_adjacency + BFS の薄い合成)
def route_reachable(data: RouteData, forbidden_edge_ids: set[str]) -> bool:
    adjacency = build_adjacency(data, forbidden_edge_ids)   # ← dijkstra.py の関数を再利用
    plain = {n: [nxt for nxt, _e, _w in es] for n, es in adjacency.items()}
    return data.goal in reachable_nodes(plain, data.start)  # ← search/bfs.py の BFS
```

```python
# app/services/validation.py(要点)── サービスは「呼んで判定」だけ
if isinstance(problem.data, RouteData):
    forbidden = {item for c in problem.constraints
                 if isinstance(c, ForbiddenConstraint) for item in c.items}
    if not route_reachable(problem.data, forbidden):
        infeasible.append(f"goal ... is unreachable ...")
```

`validate` は「純粋述語のレジストリ(`SEMANTIC_CHECKS`)を回す」+「計算プリミティブ
(`route_reachable`)を呼んで判定する」の合成 ── これが services 層の仕事。

### なぜ `dijkstra.py` と同じ `graph/` にいて統合しないのか

| | `dijkstra.py` | `reachability.py` |
| --- | --- | --- |
| 正体 | **`AlgorithmStrategy`**(問題まるごとを解く) | **アルゴリズム・プリミティブ**(`Phase-1-3.md` §1 / `Phase-0-4.md` §2.4 の 2 層の下側) |
| `registry` / `AlgorithmMeta` | 載る / 持つ | 載らない / 不要(素の関数) |
| 返す | `CandidateSolution` | `bool` |
| 消費者 | `SolveService` | `ProblemValidationService` |
| 変わる理由 | タイブレーク / 区間分割 / ベンチ計測… | 有向辺の扱い / 到達集合 vs 経路の有無… |

`search/` に `bfs.py` `dfs.py` `binary_search.py` が別ファイルで並ぶのと同じ ── **1 ファイル
1 関心事**。変更理由も消費者も別なので統合しない(`Phase-0-2.md` §2.5「一緒に変わるものを
同じファイルに」)。共有する `build_adjacency` は第 3 の関心事で、今は `dijkstra.py` に同居
(Phase 1 の割り切り)、Phase 4 でグラフプリミティブを整理するとき独立させる。

> **[Phase 4 で確定 ── adjacency.py に抽出]** Phase 4-1 で `build_adjacency` /
> `plain_adjacency` / `has_negative_weight` を `graph/adjacency.py` に、route 3 strategy の
> 共通足回り(`Segment` / `collect_route_constraints` / `plan_route` / `route_solution` ── 旧
> `dijkstra.py::solve` のインライン処理)を `graph/segments.py` に切り出した。消費者の直し方は不揃い ──
> `brute_force.py` は import 行 1 つ、`reachability.py` は import + インライン内包表記を
> `plain_adjacency()` 化、`dijkstra.py` は `build_adjacency` / `_Segment` / `_waypoints` が外へ出て
> `solve` が `plan_route` / `route_solution` への委譲に痩せる(いずれも挙動不変)。
> CSR 行列ビルダーは scipy を足す Phase まで遅延。詳細 `Phase-4-1.md` §3。

> `route_reachable` を `domain/problems/semantic.py` に置くと **`domain/` が `algorithms/` をimport する**ことになり、`Phase-0-3.md` §2.2 の依存方向(`algorithms → domain` 片方向)を破る。
> pyright / import 解決がその瞬間に気づかせてくれる ── が、これは **guardrail** であって、判断の理由ではない。理由は「これは計算か? 述語か?」。guardrail が無くても、そう問えば`route_reachable` は `algorithms/` だと分かる。

> **CL 開発の狙い**: アーキテクチャ判断は「ルールに従えば OK」ではなく「各層が何のためにあるか」で下す。図で「domain は純粋、依存は内向き」と読んでも、どこにエッジがあるかは体感できない。
> ここでは `import` 制約という guardrail が写経中に手を止めさせ、「これは計算か? 述語か?この責務はどの層のものか?」と問い直す機会を作る。その問いが `route_reachable` を`algorithms/`、判定を `services/` に分ける判断を生んだ。写経して `validation.py` を見ると、`SEMANTIC_CHECKS` のループと `route_reachable` の呼び出しが**並んで**いて、「なぜ前者はレジストリ経由で後者は直呼びなのか」が引っかかる ── その摩擦が、層の意味を指先で理解する
> 場所。

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
2. `samples/app/algorithms/graph/reachability.py` を新規写経(§3)。
3. `samples/app/services/validation.py` で既存の `validation.py` を上書き
   (`build_adjacency` / `reachable_nodes` の直接 import が消え、`route_reachable` 越しになる)。
4. `samples/tests/unit/test_validation_service.py` で既存のテストを上書き、
   `samples/tests/unit/test_reachability.py` を新規写経。
5. `uv run pytest tests/unit/test_validation_service.py tests/unit/test_reachability.py` → 緑。
   `Phase-1-6` の `test_solve_*` も緑のまま(route の挙動は不変)。

---

## 6. テスト観点(`test_validation_service.py` / `test_reachability.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `ProblemValidationService.validate` と `SEMANTIC_CHECKS` の各検査関数、
>   `route_reachable`(単体でも直接テストする)
> - **ドライバ**: テスト関数 + `build_route_problem()` / `build_shift_problem()` /
>   `build_infeasible_shift_problem()`(fixture ビルダー)。`route_reachable` は `RouteData` を
>   手組み
> - **スタブ**: **不要** ── 検査関数も `route_reachable` も純粋。`route_reachable` は
>   `build_adjacency` / BFS を呼ぶが副作用が無いので本物(スタブにする理由がない)。
>   「`domain/` にスタブが要るなら純粋レイヤー設計が崩れている」を毎章確認する。

`test_reachability.py`: 禁止なしで到達可 / goal への辺を全禁止で到達不可 / 2 経路の片方だけ
禁止なら到達可 / start が孤立で到達不可 / 一方向辺が逆向きで到達不可。

| ケース                                 | 期待                       |
| ----------------------------------- | ------------------------ |
| route: 妥当な問題(forbidden + required)  | 通過                       |
| route: 未知の start ノード                | `ProblemValidationError` |
| route: エッジが未知ノードを参照                 | `ProblemValidationError` |
| route: 禁止エッジ除去後に到達不能                | `InfeasibleProblemError` |
| shift: 妥当な問題                        | 通過                       |
| shift: スタッフが未知スロットを参照               | `ProblemValidationError` |
| shift: 適格スタッフ数 < required_headcount | `InfeasibleProblemError` |
| shift: 必要スキル保持者が居ない                 | `InfeasibleProblemError` |

`uv run pytest tests/unit/test_validation_service.py tests/unit/test_reachability.py` と
`uvx pyright app/domain/problems app/algorithms/graph/reachability.py app/services/validation.py`。

---

## 7. まとめ

- Semantic Validation の**純粋述語**は problem_type ごとの検査関数 + `SEMANTIC_CHECKS`
  レジストリ(domain)。`validation.py` はそれを回すだけ。
- `SemanticIssue.infeasible` で `ProblemValidationError`(整合性)と `InfeasibleProblemError`
  (原理的に不能)を分ける。整合性 NG を優先。
- 到達可能性は述語でなく**計算**。`route_reachable`(計算)は `algorithms/graph/reachability.py`、
  それを hard ゲートとして**判定**するのは services。domain は不関与。
- `domain → algorithms` の import 禁止は誤りを写経中に顕在化させる **guardrail**。
  判断の理由は「これは計算か? 述語か? この責務はどの層のものか?」。

次章([Phase-2-3](./Phase-2-3.md))では、作業単位 2-3 ── 解の検証側。`domain/constraints/` に
kind ごとのチェッカーを揃え、`services/verification.py` をオーケストレーションに縮小する。
