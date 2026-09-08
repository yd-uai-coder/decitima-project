# Phase 5 — Network Designer(実装フェーズ)導入

作業章(`Phase-5-1.md` 以降)を始める前に、この 1 本で Phase 5 の全体像を掴む。
目的 / パイプライン上の位置(新 problem_type の足し方)/ グラフの 2 層 / 進め方 / テスト /
スコープ / 章一覧 / 実装前チェックリスト。

> **Phase 4 との関係**: 当初 Phase 4 は Route Planner と Network Designer を 1 フェーズで扱う予定だったが、README §12 が両者を同格の製品機能として並べていること・章数が多いことから
> **Phase 4 = Route Planner / Phase 5 = Network Designer** に分けた(`Phase-4-introduction.md`
> 冒頭の注記)。Phase 5 は Phase 4 の成果(`AlgorithmStrategy` / registry / `GraphCanvas` /
> `features/optimization/` / benchmark / analysis)を土台にする。

---

## 1. このフェーズの目的

README §12.6 Network Designer ──「すべての拠点を最小コストで接続する」は**最小全域木(MST)**。
`route_planning` は start→goal の単一経路なので、辺集合を返す MST は表現できない ──**新しい `problem_type` `network_design` が要る**。

これは **Phase 1 以来はじめての新 problem_type**。`Phase-0-2.md` §8.1 が設計済みで、
`Phase-1-1.md` §5 が「既存に触れず足せる」ことを予告していた。Phase 5 の教材上の価値はMST アルゴリズムそのものと同じくらい、**「共通スキーマ設計の下で新しい問題種別を端から端まで配線する手順」の実演**にある ── Phase 6(`TravelData`)以降の雛形になる。

Phase 5 で新しく入るもの:

| 新規                                                                             | 中身                                                                                                                                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Union-Find(素集合データ構造)** `graph/union_find.py`                                 | 経路圧縮 + ランク合併。ならし O(α(n))。`union` が bool を返す = Kruskal の閉路判定                                                                                            |
| **MST 理論**                                                                     | cut property(切除性)/ cycle property / 交換論法 ── なぜ「軽い辺から貪欲」で最適になるか。全域木の全列挙で実測確認                                                                            |
| **`network_design` problem_type**                                              | 判別ユニオンに `NetworkDesignData` / `NetworkDesignSolution` を 1 メンバー。`semantic` / `structure` / `connectivity` / `validation` / `verification` に network の分岐 |
| **Kruskal / Prim (+ networkx_mst)** `graph/{mst,kruskal,prim,networkx_mst}.py` | `registry["network_design"]` を新設。`select_strategy` に network の rule                                                                                    |
| **Network Designer ページ**(decitima-ui)                                          | `src/features/optimization/network-designer/`。`types.ts` / `menu-tree.ts` に network アーム。Phase 4-8 の Route Planner と同型                                  |

---

## 2. パイプライン上の位置 ── 「既存に触れず足す」

Phase 1 で決めたとおり(`Phase-0-7.md`)、network も **`POST /api/v1/solve` に `problem_type`
付きの `OptimizationProblem` を渡すだけ**。サービス層は「registry を回すオーケストレーション」なので、専用エンドポイントは作らない。

```text
POST /api/v1/solve   { problem_type: "network_design", data: { nodes, links }, ... }
      ▼
SolveService.solve()
      ├ (b) ProblemValidationService.validate   ← semantic.py に network_design の検査を追加
      │         + 「候補リンク全体で全拠点が連結か」を all_nodes_connected(algorithms)で判定
      ├ (c) select_strategy(problem)             ← rule-based: network_design → kruskal
      ├ (d) KruskalStrategy.solve                 ← 新 registry キー "network_design"
      ├ (e) SolutionVerificationService.verify   ← structure.py に verify_network_structure、
      │         「選んだリンクが本当に全域木か」は forms_spanning_tree(algorithms)で
      └ (f) 永続化 ── **新テーブルなし**(hybrid JSONB。Problem/Solution payload に入る)
```

`alembic upgrade head` は Phase 5 で **no-op**。これが `Phase-0-8.md` のハイブリッドスキーマ設計の狙いそのもの ── 「新しい problem_type でテーブルは増えない」。

**friction は最小**(すべて増分・衝突なし): 判別ユニオンの 4 ファイル編集
(`problem.py` / `solution.py` / `__init__.py` / `types.ts`)、`select_strategy` の 1 分岐、benchmark テストの entry 数 re-baseline。route / shift のロジックには一切触れない。

---

## 3. グラフの 2 層 ── Union-Find は「下の層」

|         | AlgorithmStrategy(registry に載る)                    | アルゴリズム・プリミティブ(載らない)                                                                  |
| ------- | -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Phase 5 | `KruskalStrategy` / `PrimStrategy` / `NetworkxMST` | `UnionFind` / `all_nodes_connected` / `forms_spanning_tree` / `build_link_adjacency` |
| 例       | `KruskalStrategy.solve()` が…                       | …`UnionFind`(プリミティブ)を内部で使う(`Phase-0-4.md` §2.4 の例そのもの)                               |

- **`union_find.py` は route では消費者がいない**(route は `search/bfs.py` + `reachability.py`)。
  Kruskal(5-4)が唯一の実消費者なので Phase 5 で導入する。
- **`connectivity.py` は `union_find` に依存しない** ── BFS ベース(`search/bfs.py::reachable_nodes`
  の薄い合成)。連結性は「隣接リストを組んで BFS」= 計算なので `domain` には置けない
  (`domain → algorithms` の逆流。`Phase-2-2.md` §3)。判定(hard ゲート)は `services/` が行う。

**`_ops` の扱い**: Kruskal = union 試行回数、Prim = heap pop 数。**単位が違うので割り算しない**。
`NetworkxMST` は仕事が C の中なので `_ops` を出さない(`operation_count` は `None`)。

---

## 4. 章一覧(章 = 作業単位)

`Phase-5-M.md` = 作業単位 5-M。

| 章                           | トピック                                      | 依存        | 主な内容                                                                                                                                          |
| --------------------------- | ----------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [Phase-5-1](./Phase-5-1.md) | Union-Find(素集合データ構造)の深掘り                  | Phase 4   | `graph/union_find.py`。経路圧縮 / ランク合併 / ならし計算量 / `union` の戻り値                                                                                    |
| [Phase-5-2](./Phase-5-2.md) | MST 理論 ── cut property・交換論法               | 5-1       | cut property / cycle property / 交換論法 ── なぜ「軽い辺から貪欲」で最適か(**理論章。実装なし**。実測は 5-3)                                                              |
| [Phase-5-3](./Phase-5-3.md) | `network_design` problem_type の配線         | 5-2       | `network_design.py`(problems / solutions)、グラフ・プリミティブ(`build_link_adjacency` / `connectivity.py`)、判別ユニオンのアーム、semantic / structure / validation / verification / `select_strategy` の network 分岐、network fixture + `test_{graph_primitives,network_design,mst_properties}.py` |
| [Phase-5-4](./Phase-5-4.md) | MST ストラテジー ── Kruskal / Prim (+ networkx) | 5-1, 5-3  | `graph/{mst,kruskal,prim,networkx_mst}.py`。`registry["network_design"]` 新設                                                                    |
| [Phase-5-5](./Phase-5-5.md) | Network Designer ページ(decitima-ui)         | Phase 4-8 | `network-designer/{api,stores,hooks,components}`、`types.ts` / `menu-tree.ts` に network アーム、`page.tsx`                                         |

5-1〜5-4 が decitima-api、5-5 が decitima-ui。順序の理由: **道具(Union-Find)→ なぜ動くか
(MST 理論)→ 配線(schema)→ 実装(Kruskal / Prim)→ UI**。理論を配線の前に置くことで
「MST とは何か・貪欲がなぜ最適か」を schema より先に理解させる。

registry の作法(進行のルール #15): 5-3 の時点では `kruskal` / `prim` はまだ無いので、
`registry.py` の `"network_design"` キー・import はコメントアウトのまま。5-4 でコメントを外し、
その章が「registry から引ける」テストを持つ。

---

## 5. この Phase の進め方 ── 実装 = 写経(Phase 1〜4 と同じ)

CL(Curriculum Loop)開発では **Claude はコードを書かず、人間が手で実装する**(進行のルール #3)。

1. 章(`Phase-5-*.md`)は **要点の抜粋** だけ。動くコードは全 Phase 共有の
   [`textbook/samples/`](../samples/)(Phase 6 end 状態、実 `app/` `src/` ツリー鏡写し + 絶対 import)。
2. `textbook/samples/{app,tests,analysis,alembic,scripts}/**` → `decitima-api/backend/…`、
   `textbook/samples/ui/src/**` → `decitima-ui/src/**` へ **ファイル単位で写経・改変**。
   この Phase の写経対象は §8 の一覧(冒頭系譜コメントに当該 Phase を含むファイル)。
3. **共有フォルダの各ファイルは完成形**。この Phase で更新されるファイルは変更行が
   `#(Phase 5-<M>)` タグ + 旧コードのコメントアウトで示される(進行のルール #12)。以前の章に残る
   「`registry.py` の該当行をコメントアウトして出荷 / 現行版を新 samples に置く」等の記述は、
   Phase 毎に samples フォルダがあった時代(Step 2 以前)の運用の記録。
4. 実装中の疑問は Claude に相談し、教材と samples に還流させる(進行のルール #8 / #9)。

**着手前に §10 の「実装前チェックリスト」で疑問を出し切る**(進行のルール #11)。

---

## 6. テストの階層

| レベル                  | 使うもの                              | Phase 5 で書くもの                                                                                                       |
| -------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| primitives(純粋・主戦場)   | 素の pytest。DB 不要                   | `UnionFind`(find 経路圧縮 / union 戻り値 / groups)/ `all_nodes_connected` / `forms_spanning_tree` / `build_link_adjacency` |
| 理論の実測                | 素の pytest + 全域木の全列挙               | `test_mst_properties.py`(cut property / cycle property / 既知 MST)── 章は 5-3(schema と `forms_spanning_tree` が要る) |
| domain(純粋)           | 素の pytest                         | `network_design` スキーマのラウンドトリップ / `semantic` チェック / `verify_network_structure`                                       |
| algorithms(strategy) | 素の pytest                         | `KruskalStrategy` / `PrimStrategy` / `NetworkxMST`(3 strategy で総コスト一致)                                              |
| サービス層                | `db_session`(SQLite)+ `FakeRedis` | `BenchmarkService`(network_design ケース)/ `select_strategy` の network 分岐                                              |
| API                  | `httpx.AsyncClient` + 依存差し替え      | `POST /benchmark` の network_design ケース                                                                              |
| UI                   | Vitest + jsdom / node env         | network-designer store                                                                                              |

すべて**純粋**なのでスタブ不要 ── `networkx` を使う strategy も決定論的。

```bash
# decitima-api/backend(overlay end 状態 = Phase 4 end + Phase 5 samples)で
uv run pytest      # 217 passed, 2 deselected  (analysis 6 本を含む。pandas 未導入なら 211)
# decitima-ui で
npx vitest run src/features/optimization   # 16 passed
```

---

## 7. Phase 5 のスコープと非スコープ

| Phase 5 でやる                                                  | 送る先                                                                                                    |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Union-Find / MST 理論 / Kruskal / Prim / networkx_mst          | ―                                                                                                      |
| `network_design` problem_type の端から端までの配線                     | ―                                                                                                      |
| Network Designer ページ(サンプル選択 + JSON エディタ + `GraphCanvas` 可視化) | リッチな作図エディタ ── 需要が出たら別 Phase                                                                            |
| `select_strategy` の `network_design → kruskal` 分岐            | 学習型のアルゴリズム選択(Phase 12)                                                                                 |
| ―                                                            | **Shift Scheduler**(Greedy / Backtracking / Branch and Bound、多目的評価器、OR-Tools)は Phase 6                 |
| ―                                                            | **Steiner 木 / 容量制約つきネットワーク設計**(README §12.6 の発展)── 需要が出たら別 Phase                                       |
| ―                                                            | **`analysis/network_benchmark.py`**(MST の size 別集計)── Phase 5 では作らない。Phase 6+ が `analysis/` を育てるとき合わせて |

---

## 8. サンプルコード ── 共有 `textbook/samples/`

動くコードは全 Phase 共有の [`textbook/samples/`](../samples/)（Phase 6 end 状態）。各ファイル冒頭の
`# DeciTima samples │ …` コメントが Phase の系譜を示す。以下は **この Phase が作成 / 更新するファイル**
（= この Phase での写経対象。冒頭系譜に当該 Phase を含むもの）。overlay 検証手順は
[`textbook/samples/README.md`](../samples/README.md)。

| 場所                                                                                                                                                                                                      | 内容                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `app/algorithms/graph/union_find.py`                                                                                                                                                                    | `UnionFind`(新規プリミティブ)                                                              |
| `app/algorithms/graph/connectivity.py`                                                                                                                                                                  | `all_nodes_connected` / `forms_spanning_tree`(新規プリミティブ。BFS ベース)                    |
| `app/algorithms/graph/adjacency.py`                                                                                                                                                                     | 現行版(`build_link_adjacency` 追加)                                                     |
| `app/algorithms/graph/{mst,kruskal,prim,networkx_mst}.py`                                                                                                                                               | MST 共通足回り + strategy(新規)                                                           |
| `app/domain/problems/network_design.py` / `app/domain/solutions/network_design.py`                                                                                                                      | `NetworkNode` / `NetworkLink` / `NetworkDesignData` / `NetworkDesignSolution`(新規葉) |
| `app/domain/problems/{problem,__init__,semantic}.py`                                                                                                                                                    | 現行版(ユニオンに `network_design` / semantic チェック)                                        |
| `app/domain/solutions/{solution,structure}.py`                                                                                                                                                          | 現行版(ユニオン + `verify_network_structure`)                                             |
| `app/domain/constraints/{forbidden,required_inclusion}.py`                                                                                                                                              | 現行版(network 解にも対応)                                                                 |
| `app/services/{validation,verification,algorithm_selection}.py`                                                                                                                                         | 現行版(network ゲート / 全域木チェック / kruskal rule)                                          |
| `tests/unit/{test_union_find,test_mst_properties,test_network_design,test_mst_strategies,test_graph_primitives,test_algorithm_selection,test_benchmark_service}.py` / `tests/api/test_benchmark_api.py` | 新規 + 現行版                                                                           |
| `tests/fixtures/optimization.py`                                                                                                                                                                        | 現行版(`build_network_problem` 系を追加)                                                  |
| `ui/src/lib/api/types.ts` / `ui/src/lib/menu-tree.ts`                                                                                                                                                   | 現行版(network アーム / network エントリ)                                                    |
| `ui/src/features/optimization/network-designer/**`                                                                                                                                                      | api / stores / hooks / components / sample-problems(新規)                            |
| `ui/src/app/(pages)/optimization/network-designer/page.tsx`                                                                                                                                             | ページ(`RequireAuth` で包む。新規)                                                          |

既存ファイルへの追記(samples に含めない、各章に差分):
`app/algorithms/registry.py`(`"network_design"` キー + 3 本)。

検証: Phase 4 end 状態に Phase 5 samples を overlay し `uv run pytest`(**217 passed, 2 deselected** ── analysis 6 本込み)/
`ruff` / `uvx pyright`(Phase 5 分 0 errors)/ `alembic upgrade head`(no-op)。
decitima-ui に overlay し `npx tsc --noEmit` / `npx vitest run`(**16 passed**)/ `npx eslint`。
手順は `textbook/samples/README.md`。

---

## 9. Phase 5 の成果物

- **textbook**: この `Phase-5/` 一式(導入 + `Phase-5-1`〜`5-5` + samples)
- **decitima-api の実装**(ユーザーが写経): `app/algorithms/graph/{union_find,connectivity,mst,kruskal,prim,networkx_mst}.py` /
  `app/domain/**` の network_design 配線 / `app/services/{validation,verification,algorithm_selection}.py` /
  `tests/**` / `registry.py` への追記
- **decitima-ui の実装**(ユーザーが写経): `src/features/optimization/network-designer/**` /
  `src/app/(pages)/optimization/network-designer/page.tsx` / `src/lib/api/types.ts`・`src/lib/menu-tree.ts`(現行版)
- **Phase 1 / 2 教材への「以降 Phase で修正予定 ── Phase 5-3」マーカー**(判別ユニオンの分割)
- **ルート `CLAUDE.md`「### 設計判断・検証知見」の Phase 5 要点**(経緯は `textbook/q_a.md` Q29)

---

## 10. Phase 5 実装前チェックリスト

進行のルール #11。行 `5-M` ↔ 章 `Phase-5-M`。

| #   | 作る / 変えるファイル                                                                                                                                                                                                                                                                              | 主なクラス・関数の責務(1 行)                                                                                                                                                                                                                                                                                                          |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5-1 | `graph/union_find.py`(新規)、`tests/unit/test_union_find.py`                                                                                                                                                                                                                                 | `UnionFind`(`find` = 根 + 経路圧縮 / `union` = 合併、同グループなら False / `connected` / `group_count` / `groups`)                                                                                                                                                                                                                      |
| 5-2 | ── (理論章。実装ファイルなし)                                                                                                                                                                                                                                                                          | cut property / cycle property / 交換論法 ── 「軽い辺から貪欲」がなぜ最適かを説明できる(実測は 5-3)                                                                                                                                                                                                                                                    |
| 5-3 | `domain/problems/network_design.py`、`domain/solutions/network_design.py`、`graph/connectivity.py`(新規)、`domain/{problems,solutions}` の現行版、`graph/adjacency.py`(`build_link_adjacency`)、`services/{validation,verification,algorithm_selection}.py`(現行版)、`tests/fixtures/optimization.py`(network fixture)、`tests/unit/{test_graph_primitives,test_network_design,test_mst_properties}.py`(現行版 + 新規) | `NetworkDesignData`(nodes / links、link は無向 `endpoints`)/ `NetworkDesignSolution`(selected_link_ids / total_weight)/ `build_link_adjacency`(無向リンク → 隣接。`adjacency.py`)/ `all_nodes_connected`・`forms_spanning_tree`(計算。`connectivity.py`、BFS ベース)/ `check_network_link_endpoints`・`check_network_has_links`(純粋述語)/ `verify_network_structure`(純粋述語)/ `_preferred_name` に network 分岐 / `build_network_problem`(5 拠点、既知 MST コスト 10)/ `_all_spanning_trees`(小グラフの全列挙オラクルで 5-2 の理論を実測)。写経順序 = 葉 → ユニオン → プリミティブ → domain 述語 → services → チェッカー → テスト |
| 5-4 | `graph/{mst,kruskal,prim,networkx_mst}.py`(新規)、`registry.py`、`tests/unit/{test_mst_strategies,test_algorithm_selection}.py`                                                                                                                                                               | `parse_network_problem` / `resolve_required`(必須リンク検証)/ `KruskalStrategy`(weight 昇順 + `UnionFind`)/ `PrimStrategy`(heapq)/ `NetworkxMST` / registry に `"network_design"` キー                                                                                                                                                |
| 5-5 | `ui: network-designer/{api,stores,hooks,components,sample-problems.ts}`(新規)、`app/(pages)/optimization/network-designer/page.tsx`、`lib/api/types.ts`・`lib/menu-tree.ts`(現行版)                                                                                                               | `solveNetwork` / `compareNetwork` / `useNetworkDesignerStore` / `NetworkDesignerPanel` / `MstResultCanvas`(選択リンク実線・候補破線)/ `types.ts` に network アーム / ページは SSG + `RequireAuth`                                                                                                                                             |

---

## 11. 次のフェーズ

Phase 5 完了で **MVP のアルゴリズム側は route_planning / network_design の 2 problem_type が
端から端まで通る**。次は「**Phase 6 を開始する**」で **Shift Scheduler**(Greedy / Backtracking /
Branch and Bound、多目的の重み付き評価器、そして**手実装の破綻 → OR-Tools CP-SAT トラック**)。
Phase 4 / 5 で「同じインターフェースの下に手実装と `library:*` を並べてベンチで比べる」枠組みが
実物で動いているので、Phase 6 の「いつソルバーに切り替えるべきか」を `analysis/shift_analysis.py`
の実測で示せる。MVP は Phase 0〜6。
