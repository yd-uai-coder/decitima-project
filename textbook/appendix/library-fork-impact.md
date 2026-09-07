# 付録: ライブラリ(NumPy / SciPy / networkx / pandas)フル活用版フォークの影響調査

> **これは覚書 + 影響調査であって、実装計画ではない。** DeciTima 完成後に、これをベースにした
> 「数値ライブラリ全面版」を**別プロジェクト**として作る想定で、置き換えの影響を先に洗い出す。
> **現行 Phase の設計・コードは一切変えない。** 今後の Phase で任意に入れられる「置き換えフック」
> 候補は §5 に列挙するに留める。

関連(重複させず参照する):

- `README.md` §8「実装方針 ── 手実装を主軸に、数値ライブラリは境界の裏に」── プロジェクトの前提
- `textbook/Phase-0/Phase-0-3.md` §4 / `Phase-0-4.md` §5.2 / `Phase-0-5.md` ── **2 トラック
  (手実装 / 産業ソルバー)**。同一 `AlgorithmStrategy` 契約の裏で networkx / OR-Tools を呼ぶ
  「並存」パターン
- `CLAUDE.md` Notes 相談ログ Q19(NumPy フル活用の pros/cons)/ Q20(この覚書)

---

## 1. 目的とスコープ

DeciTima を完成させた後、NumPy / SciPy / networkx / pandas を主軸にした派生版を作るときの
影響を、先に洗い出す。

### 「2 トラック(並存)」との違い

| | 2 トラック(既存の設計) | 本覚書(ライブラリ全面版フォーク) |
| --- | --- | --- |
| 何をする | 1 コードベースに手実装 strategy とライブラリ strategy を**共存**させ、`meta.implementation` で区別し、ベンチで比較する | DeciTima を**派生プロジェクトとして全面移植**し、計算をライブラリ主軸にする |
| ライブラリの位置 | スケールしない問題の実務側(Phase 6 CP-SAT、Phase 9）だけ | ほぼ全 strategy(+ 場合によっては `domain/` コアまで) |
| 目的 | 「手で書くと何倍遅いか / どこで逆転するか」を実測で示す(教材・ポートフォリオ) | 実規模を実用的な速度で解く production 寄りの派生 |

### 2 段構え

- **レベル A**: strategy レイヤーだけライブラリ化(スキーマ・API・DB・検証は現行のまま)── §2〜§6
- **レベル B**: スキーマ・コアも配列ネイティブ化(`domain/` の作り直しを伴う)── §7〜§8

---

## 2. 置き換え表面 ── 部品ごとのカタログ

各行: **現行(手実装)** / **置き換え先ライブラリ** / **固定される境界(seam)** / **影響(friction)**

| 部品 | 現行 | 置き換え先 | seam(変わらない契約) | friction(適応が要る点) |
| --- | --- | --- | --- | --- |
| `algorithms/graph/dijkstra.py` `DijkstraStrategy` | 隣接リスト(dict)+ `heapq` | `scipy.sparse.csgraph.dijkstra` / `networkx.shortest_path` | `AlgorithmStrategy.solve(OptimizationProblem) -> CandidateSolution`、`RouteSolution`(node/edge id 列)、`registry` 1 行 | `RouteData`(文字列 id)↔ CSR 行列(整数 index)の相互変換。`metrics["_ops"]` は計測不能(C の中)→ `operation_count = None`。タイブレークが手実装と異なりうる(再現性テスト) |
| `algorithms/graph/reachability.py` `route_reachable` | `build_adjacency` + BFS | `csgraph.connected_components` | `route_reachable(data, forbidden) -> bool`、消費者は `validation.py` のみ | index マップ変換のみ。影響は小 |
| `algorithms/search/{bfs,dfs}.py` | deque / 再帰、素の隣接リスト | `csgraph.breadth_first_order` / networkx | プリミティブ(registry 非搭載)。入力は素のデータ構造 | 入力型が `Mapping[str, Iterable[str]]` → (matrix, index) に変わる |
| `algorithms/search/binary_search.py` | 自前二分探索 | `bisect`(stdlib)/ `numpy.searchsorted` | プリミティブ | ほぼ無影響(そもそも stdlib で足りる) |
| `algorithms/optimization/brute_force.py` | 全単純パスの DFS 列挙 | **置き換え先なし**(これは厳密オラクル) | ─ | **移植しない**。フォークでも正解検証にそのまま使う(または networkx `all_simple_paths`) |
| Phase 4: Bellman-Ford / A* / MST(実装済み) | 自前(`graph/{bellman_ford,a_star,kruskal,prim}.py`)。共通足回りは `graph/{adjacency,segments,mst,union_find}.py`(`segments.reconstruct_path` = 3 strategy 共通の経路復元) | `csgraph.bellman_ford` / networkx `astar_path` / `csgraph.minimum_spanning_tree` | 同 `AlgorithmStrategy`、`network_design` の `NetworkDesignData`。seam は明確(Protocol + `segments.SegmentFn` の差し替えだけ) | 同上(index 変換 + `_ops` なし)。`NetworkxShortestPath` / `NetworkxMST` が既に `library:networkx` 側の実例 |
| Phase 6: Greedy / Backtracking / B&B | 自前 | **OR-Tools CP-SAT**(既に 2 トラックで計画済み) | 同 `AlgorithmStrategy`、`ShiftSolution`、`objectives` | 既に想定内。フォークでは CP-SAT が主 |
| Phase 7: Knapsack DP / Floyd-Warshall | 自前 DP / 三重ループ | NumPy ベクトル化 DP / `csgraph.floyd_warshall` | プリミティブ(距離行列)、`TravelSolution` | Floyd-Warshall は既に「距離行列を返すプリミティブ」= NumPy 配列がむしろ自然 |
| Phase 8: Topological Sort / Critical Path | 自前(DFS 土台) | networkx `topological_sort` / `dag_longest_path` | `AlgorithmStrategy`、ガントの DataFrame 化 | index 変換 + pandas を出力整形に使える |
| Phase 9: Logistics(複合) | 自前の組み合わせ | `scipy.optimize` / OR-Tools routing / `pulp` | `AlgorithmStrategy` | 最大の書き換え量。ただし境界は同じ |
| Verification(`domain/solutions/structure.py` + `domain/constraints/**`) | 完成割当の手スキャン | **原則置き換えない**(独立した検証は自前で) | `SolutionVerificationService.verify` は解の生成元を問わない | **ロジックは移植しない**。フォークでも検証は独立実装で持つ(pandas groupby でのオラクル併用は可)。詳細は §7 |
| スキーマ(`domain/problems/**` `domain/solutions/**`) | Pydantic 判別可能ユニオン | レベル A: そのまま / レベル B: ingress は Pydantic、内部を `ProblemArrays` に(§7) | API / DB(JSONB)/ Validation / Verification が全部これに依存 | レベル B は `domain/` の作り直し |
| `services/measurement.py` | NumPy(既に) | 変わらず | ─ | 影響なし |
| `analysis/**` | pandas(既に。Phase 3-8) | 拡張されるだけ | ─ | フォークでは分析が主役級になる |
| `services/{solve,verify,benchmark}.py` | オーケストレーション | 変わらず | strategy を呼ぶだけ。生成元非依存 | 影響なし(タイムアウトは SciPy が GIL を離すのでむしろ改善) |
| DB(`models/optimization.py` / Alembic) | JSONB payload | 変わらず | `payload` に何を入れるかだけ | レベル A: 影響なし。レベル B: §7 のエンコーダ |
| decitima-ui | 影響なし(TypeScript) | ─ | REST 契約 | 影響なし |

---

## 3. 現行設計が「既に置き換え可能」な理由 ── seam の棚卸し

1. **`AlgorithmStrategy` = `typing.Protocol`**(`app/algorithms/base.py`)── 継承不要。SciPy
   ラッパーは `meta` 属性と `solve` メソッドを持てばよい。**最大の enabler**。
2. **`AlgorithmMeta.implementation`** ── `"handwritten"` / `"library:scipy"` / `"library:networkx"`
   を最初から設計に持つ(`Phase-0-2.md` §6 / `Phase-0-4.md` §5.2)。
3. **`registry.py`** ── `REGISTRY["route_planning"].append(ScipyDijkstraStrategy())` の 1 行で
   追加できる(開放閉鎖)。
4. **Pydantic の Problem / Solution スキーマが全境界を占める** ── API・DB(JSONB)・Validation・
   Verification がすべてこれに依存し、strategy の中身を差し替えても外周は無変更。
5. **純粋な `domain/` の Verification** ── `SolutionVerificationService` は解の生成元を知らない。
   ライブラリ strategy が出した解も、手実装が出した解と同じく検証される。
6. **`benchmark_runs` + `analysis/`** ── 「手実装 vs ライブラリ」比較の受け皿(実測の永続化 +
   pandas 集計)が Phase 3 / 3-7 で既にある。
7. **依存の遅延追加の習慣**(`Phase-0-9.md` §5)── フォークは追加ライブラリを
   `[project.optional-dependencies]` に寄せやすい。

**見立て**: strategy レイヤーは「`solve` を実装 + `registry` に 1 行」で置き換え可能。
**約 8 割は契約で吸収される。**

---

## 4. フォークが必要とする変更(レベル A の friction)

| 論点 | 内容 | 対処 |
| --- | --- | --- |
| **グラフ表現のインピーダンス** | Pydantic `RouteData`(文字列 id)↔ SciPy CSR(整数 index)の往復 | 共有ヘルパ `algorithms/graph/adjacency.py` に `to_dict_adjacency` と `to_csr(data) -> (csr, id_to_idx, idx_to_id)` を置く。Phase 4 でどのみちグラフプリミティブを整理する(`Phase-2-2.md` §3 の注記)ので、そのとき CSR ビルダーも足せる → **置き換えフック①** |
| **`metrics["_ops"]` の欠落** | ライブラリ strategy は内部の操作回数を計測できない | `BenchmarkEntry.operation_count: int \| None` で既に対応済み(Phase 3-1)。「操作回数の比較は手実装トラック限定」と明記する。時間 / メモリ / 解の品質はクロストラックで比較できる |
| **再現性(NFR-1)** | `test_deterministic_same_input_same_output` は `model_dump()` の byte 一致を要求。SciPy / networkx は最短経路のタイブレークが手実装と違いうる | ライブラリ strategy 向けに「値一致 + 正規形(パスのタイブレークを sorted に固定)」へ緩める。または `_canonicalize_path` を strategy 側に持たせる → **置き換えフック②** |
| **実行時依存の重量** | SciPy + NumPy は Docker イメージが +100MB 級 | フォークでは solver 群を optional-extra(`pip install decitima[solvers]`)にし、`registry.py` は `try / except ImportError` で条件付き登録 → **置き換えフック③** |
| **移植しない部品** | `brute_force.py`(厳密オラクル)/ Verification ロジック / `_ops` 計装 / 教材そのもの | フォークでもオラクルと独立検証は「別実装」で持つ(実装言語や表現は変えてよいが、**ロジックは自前**で持つ ── 検証がライブラリと同じ実装だと「検証」にならない) |

---

## 5. 「置き換えを前提とした設計」── 今後の Phase で任意に入れられるフック(今は入れない)

現行 Phase の設計はいじらない。以下は Phase 4〜15 を進めるときに「ついでに入れておくと
フォークが楽になる」候補。やる / やらないはユーザーが各 Phase で判断する。**この覚書は
選択肢の提示のみ。**

- **フック①** `algorithms/graph/adjacency.py` に dict / CSR 両ビルダー ── **Phase 4-1 で
  `adjacency.py` は新設済み**(`build_adjacency` / `build_link_adjacency` / `plain_adjacency` /
  `has_negative_weight`)。CSR ビルダー(`to_csr(data) -> (csr, id_to_idx, idx_to_id)`)は
  scipy を足す Phase(または フォーク時)にこのファイルへ足すだけ ── 抽出は完了しているので
  「グラフプリミティブ整理」の再作業は不要になった。
- **フック②** 各 graph strategy が `RouteSolution` を返す前に通す `_canonicalize_path`
  (タイブレークを決定的に固定)── 手実装トラックでも「同じ入力 → 同じ出力」が強くなる副次利益
- **フック③** `registry.py` の optional-import 条件付き登録パターン
  (`try: from ... import X; REGISTRY[...].append(X()) except ImportError: pass`)
- **フック④** `AlgorithmMeta` に `backend: Literal["python", "c", "solver"] | None` を足す
  (比較レポートで「手実装 Python」「library C 実装」「ソルバー」を束ねやすい。任意)
- **フック⑤(レベル B 向け)** `schemas/`(HTTP 境界)と `domain/`(内部表現)の分離を Phase を
  追うごとに厳格に保つ ── `Phase-0-3.md` §2.4 で既に方針化されている。`schemas/` が `domain/` を
  薄く包むだけ、を守り続ければ、フォークは「`domain/` を `ProblemArrays` に差し替え + 変換層
  1 枚」で済む

---

## 6. レベル A の結論 ── strategy レイヤーだけライブラリ化する場合

現行 DeciTima は **`AlgorithmStrategy` Protocol + `AlgorithmMeta.implementation` + 全境界
Pydantic + 独立した純粋 Verification** により、**strategy レイヤーの全面ライブラリ化に対して
約 8 割準備済み**。

主な作業は次の 3 点で、いずれも境界(スキーマ / API / DB / 検証)には波及しない:

1. グラフの id ↔ index アダプタ(`to_csr` / `to_pydantic`)
2. 再現性テストをライブラリ strategy 向けに緩める(値一致 + 正規形)
3. solver 群の optional 依存化 + 条件付き登録

`brute_force`(厳密オラクル)と Verification と `_ops` 計装は**移植せず手実装で保持する**。

---

## 7. レベル B ── スキーマ・コアの配列ネイティブ化まで踏み込む場合

Problem / Solution を「Pydantic 判別可能ユニオン」から「ndarray / DataFrame ネイティブ」に
変えると、strategy だけでなく `domain/` 全体・Validation・Verification・DB 直列化が動く。

### 推奨アーキテクチャ(フォーク側)── edges に Pydantic、内部に `ProblemArrays`

```text
REST JSON ──(Pydantic で受けて検証)──▶ OptimizationProblem
                                           │  to_arrays(model)
                                           ▼
                                     ProblemArrays（@dataclass + ndarray）
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
  ベクトル化 Validation            AlgorithmStrategy.solve            ベクトル化 Verification
  （配列上の述語）                 （SciPy / OR-Tools）              （bool 行列演算）
                                           │
                                           ▼
                                     SolutionArrays
                                           │  to_pydantic(arrays)
                                           ▼
                                     CandidateSolution ──▶ model_dump(mode="json")
                                                            │
                                             ┌──────────────┴──────────────┐
                                             ▼                             ▼
                                    REST レスポンス                  DB payload（JSONB）
```

- **ingress(REST JSON)は Pydantic で受けてバリデート** → `to_arrays(model) -> ProblemArrays`
- 計算・ベクトル化 Validation / Verification は `ProblemArrays` / `SolutionArrays` の上で
- **egress は `to_pydantic(arrays) -> model` → `model_dump(mode="json")`**
- **外部契約(REST の JSON 形 / DB の JSONB 形)は現行と同一に保てる** ── 変わるのは内部表現だけ

### レイヤー別インパクト

| レイヤー | 現行 | 配列ネイティブ化 | 影響度 |
| --- | --- | --- | --- |
| `schemas/optimization.py` | `SolveRequest.problem: OptimizationProblem` | ingress は Pydantic 維持 + `to_arrays` 変換層を新設 | **中**(変換層の追加) |
| `domain/problems/**`(スキーマ) | leaf → aggregator → `__init__` の判別可能ユニオン | `ProblemArrays`(`@dataclass` + ndarray フィールド)+ `problem_type` → パーサ表。判別子の自動解決・型ナローイングは失う | **大** ── ハイブリッドスキーマの「共通骨格 + 問題固有部分」の利点が一部消える。problem_type 追加コストが上がる |
| Input Validation | Pydantic `Field` / `field_validator` / `model_validator` | ingress の Pydantic に残す(ここは Pydantic が最適)。または明示的検証関数に再実装 | **小〜中**(Pydantic を ingress に残せば小) |
| Semantic Validation(`semantic.py` `SEMANTIC_CHECKS`) | 純粋述語(問題フィールド上) | ベクトル化述語(配列上)。`start_idx in node_indices` 等。bulk ではむしろ簡潔 | **中**(書き換えるが「レジストリを回す」構造は保つ) |
| 到達可能性(`reachability.py`) | `build_adjacency` + BFS | `csgraph.connected_components` | **小** |
| Verification(`structure.py` / `constraints/**`) | 完成割当の手スキャン | bool 行列演算(shift の staff × slot、週勤務時間 = `assign @ durations`) | **中〜大** ── ロジックは移植可。`ConstraintViolation`(結果の型)は小さいので Pydantic / dataclass のまま維持推奨 |
| DB(`models/optimization.py` JSONB) | `model_dump(mode="json")` | 配列 → ネストリストのカスタムエンコーダ(`ndarray.tolist` / `DataFrame.to_dict`)。round-trip 可 | **小〜中** |
| services(`solve` / `verify` / `benchmark`) | strategy を呼ぶオーケストレーション | 変換層を挟む以外は無変更 | **小** |
| `AlgorithmMeta` / `ConstraintViolation` / `Objective` | Pydantic | **そのまま**(メタデータで bulk データでない) | **なし** |
| decitima-ui | ─ | REST / JSON 契約が同一なら**無影響** | **なし** |
| テスト | fixtures が Pydantic を生成 | 配列 fixtures か、テストヘルパに `to_arrays` を挟む | **中** |
| 教材価値 | 「型付き判別ユニオン」は Phase 0 の見どころ | フォークは教材でないので転写不要 | ─ |

### レベル B 固有の friction

- **id ↔ index 変換がグラフだけでなく全 problem_type に波及**(shift の staff / slot、travel の
  place)。一箇所でも取り違えると静かに壊れる → 変換層(`to_arrays` / `to_pydantic`)に
  往復テストを厚く。
- **Pydantic の「JSON を受けて検証」は非常に強い**。ingress では捨てないのが賢い(高速化したい
  なら `msgspec` でも可)。
- **problem_type ごとの追加コストが上がる**(現行: Pydantic モデル + ユニオン 1 行 / 配列版:
  struct + パーサ + Validation 関数群 + Verification 関数群 + 変換往復テスト)。ハイブリッド
  スキーマの狙い(`Phase-0-2.md` §2)が部分的に薄まる。

---

## 8. レベル B の結論

配列ネイティブ・コアは「派生」を超えて **`domain/` 層の作り直し**になる。ただし
**外部契約(REST の JSON 形・DB の JSONB 形・decitima-ui)は同一に保てる**ため、「別物」では
なく「**同じ外皮・別の中身**」に収められる。

移植戦略は **edges に Pydantic / `msgspec`、内部に `ProblemArrays`** の hexagonal 化。
`AlgorithmStrategy` 契約 / `registry` / services ライフサイクル / `benchmark_runs` / `analysis/`
はそのまま乗る。`brute_force`・独立 Verification ロジック・`_ops` 計装は(実装表現が変わっても)
フォークでも自前で保持する。

**現行 DeciTima 側で今やるべきことは無い。** 変換層を差し込む seam(`schemas/` ↔ `domain/` の
境界)は `Phase-0-3.md` §2.4 で既に明確なので、フォーク着手時に 1 レイヤー足すだけで済む。
§5 のフック⑤(schemas / domain 分離を厳格に保つ)だけ、今後の Phase で意識しておくとよい。

---

## 9. pandas の位置づけ ── フォークでも edges のまま(相談ログ Q28)

**「numpy・pandas フル活用版」は 1 括りにできない。フォークの本質は numpy-in-core であって、
pandas の footprint はほぼ増えない。**

§7 の hexagonal 図(`REST JSON → OptimizationProblem → ProblemArrays → …`)で数値計算を担うのは
**numpy**(ベクトル化 DP / 距離行列 / bool 行列 Verification)。pandas はこの経路に現れない ──
リクエスト経路は **ndarray 形(1 問題ずつ・サイズ有界の数値計算)** であって
**DataFrame 形(多数行の列指向分析・group-by / pivot / 時系列)** ではないため。

pandas が居場所を得るのは 2 箇所だけで、**そこはフォークでも現行と同じ**:

| pandas の居場所 | 現行 | フォーク |
| --- | --- | --- |
| **`analysis/`**(オフラインのベンチ / 実験集計。`benchmark_runs` / `solutions` を DB→JSONL→DataFrame) | dev 依存・`app/` から切り離し(§2 / `Phase-3-8.md`) | 変わらず。ただし比較すべきものが増えるので「主役」になる(§2 の "analysis becomes a lead role") |
| **`app/adapters/`**(入力ファイルアップロード UX を足す Phase = P5/P7/P8。README 未計画) | 未作成 | 作るなら `domain`/`algorithms` の**兄弟**・inbound 専用の縁(`xlsx/csv → 検証・整形 → Pydantic`。一方向)・`[project.optional-dependencies]` でゲート(フック③ と同型)。Pydantic を吐いたら pandas は消える |

ロードマップ機能の「tabular 感」── Shift の staff×day×slot グリッド(P5)、task 一覧 + ガント(P7)、
vehicle / delivery 一覧 + 多指標ロールアップ(P8)、シナリオ×指標 の比較行列(P9)── は、
**手実装プリミティブ(Prefix Sum / Difference Array / Sliding Window)+ Pydantic + JSONB +
`analysis/` 送り**で処理する。P5 の時間帯集計に imos 法を手実装するのはカリキュラムの学習項目
そのもの。P9 の Sensitivity 掃引が大きくなる分は明示的に `analysis/`。

→ **現行 DeciTima 側で今やるべきことは無い**(§8 の結論と同じ)。フォークで pandas を
「リクエスト経路に組み込む構成」は存在しない。

---

## まとめ 1 枚

| 問い | 答え |
| --- | --- |
| strategy をライブラリに置き換えられるか | **ほぼそのまま可**(`solve` 実装 + registry 1 行)。約 8 割は契約で吸収 |
| 何が要るか(レベル A) | id↔index アダプタ / 再現性テスト緩和 / optional 依存化 の 3 点 |
| スキーマ・コアも配列にできるか | できる。ただし `domain/` の作り直し。外部契約は同一に保てる(「同じ外皮・別の中身」) |
| 何が移植されないか | `brute_force`(オラクル)/ Verification ロジック / `_ops` 計装 / 教材 |
| 今の DeciTima で対応が要るか | **不要**。seam は既に明確。フック⑤(schemas/domain 分離の厳守)だけ意識 |
| pandas はフォークで増えるか | **ほぼ増えない**(§9)。`analysis/` + 入力アダプタのまま。フォークの数値ライブラリは numpy(コア計算)であって pandas ではない |
| いつやるか | DeciTima 完成後、別プロジェクトとして |
