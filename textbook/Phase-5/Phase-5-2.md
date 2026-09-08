# Phase 5-2: MST 理論 ── なぜ貪欲で最適になるか(作業単位 5-2)

## この章のゴール

Kruskal も Prim も **貪欲法** ── 「一番軽い辺から」採る。貪欲は多くの問題で最適解を外すのに、なぜ MST では最適になるのか。その根拠が **cut property(切除性)** と **交換論法**。

> その時点で「一番良さそうな選択」を繰り返して、最終的な答えを求めるアルゴリズム。「将来どうなるか」をすべて考えるのではなく、**今この瞬間の最善手を選ぶ**のが特徴です。

この章は**コードを書かない理論章**。cut property / cycle property / 交換論法を押さえ、5-3 以降の配線・実装を「なぜこれで正しいのか分かった状態」で始めるためにある。

**この章で作成 / 更新するファイル**: なし(理論章)。cut / cycle property を小グラフの**全域木の全列挙**で実測するテスト(`test_mst_properties.py`)と、その入力になる network fixture は **5-3 の成果物**にした ── 列挙オラクルが `NetworkDesignData`(schema)と `forms_spanning_tree`(述語)を使い、どちらも 5-3 で生まれるため(進行のルール #15)。実測は [Phase-5-3](./Phase-5-3.md) §7。

設計は README §12.6、CLRS 23 章(MST の一般アルゴリズムと安全な辺)。

---

## 1. 用語

- **全域木(spanning tree)**: グラフの全頂点を含み、辺数 V-1、<u>閉路なし</u>の部分グラフ。連結グラフには必ず存在する。
- **最小全域木(MST)**: 全域木のうち辺の重み和が最小のもの。複数ありうる(重みに同点があるとき)。
  
  > グラフが
  > - **頂点（ノード）**を複数持つ
  > - **辺（エッジ）**にコスト・距離・重みがある
  > - **無向グラフ**
  > - すべての頂点がつながっている
  > 
  > という条件のとき、
  > 
  > **すべての頂点をつなぎながら、辺の重みの合計を最小にする木**
  > 
  > が **MST（Minimum Spanning Tree）**
- **カット(cut)**: 頂点集合を空でない 2 つ (S, V∖S) に分割すること。
- **カットを跨ぐ辺(crossing edge)**: 片方の端点が S、もう片方が V∖S にある辺。

---

## 2. cut property(切除性)── 安全な辺の見つけ方

> **任意のカット (S, V∖S) について、そのカットを跨ぐ辺のうち最小重みのものは、
> いずれかの MST に含まれる。**

直感: S と V∖S を繋ぐには跨ぐ辺が最低 1 本要る。一番安いやつを選んでおけば損しない。

**Kruskal / Prim はどちらもこの property を回しているだけ**:

|             | どんなカットを見ているか                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Prim**    | S = 「今の木に入っている頂点」。木から出る最小の辺 = そのカットの最小 crossing edge                                                                                        |
| **Kruskal** | weight 昇順に辺 e=(u,v) を見た瞬間、S = 「u を含む今の連結成分」。e が閉路を作らない(u と v が別成分)なら、e はそのカットの最小 crossing edge(それより軽い crossing edge があれば先に処理され両成分は既に繋がっている) |

`test_cut_property_min_crossing_edge_is_in_some_mst`(5-3 の samples)がこれを実測する ── fixture のグラフでカット `{A}` を取り、跨ぐ辺 `L_ab(1)` / `L_ac(5)` / `L_ae(7)` の最小 `L_ab` が、全列挙した MST のいずれかに入っていることを確認。

---

## 3. cycle property ── 捨ててよい辺

> **任意の閉路について、その閉路の最大重みの辺は、どの MST にも含まれない。**
> (厳密には「その辺より軽い辺だけで両端点が繋がる」なら不要。重みが全て異なれば「最大辺は不要」)

直感: 閉路の最重量辺を MST が使っていたら、それを外して閉路の別の(より軽い)辺に**交換**すれば連結性を保ったまま総重量が下がる ── 元が MST だった仮定に矛盾。これが**交換論法**。

`test_cycle_property_heaviest_cycle_edge_is_in_no_mst`(5-3 の samples)── 閉路 A–B–C–A
(`L_ab`=1 / `L_bc`=2 / `L_ac`=5)の最重量辺 `L_ac` が、全列挙したどの MST にも入っていないことを確認。

---

## 4. 交換論法 ── cut property の証明スケッチ

跨ぐ最小辺を e、それを含まないある MST を T とする。T に e を足すと閉路ができる(T は全域木)。
その閉路には e 以外に「カットを跨ぐ辺」e' が必ず 1 本以上ある。`weight(e) ≤ weight(e')`(e は最小 crossing edge)。T から e' を除いて e を足した T' も全域木で、`weight(T') ≤ weight(T)`。
T が MST なら T' も MST で、T' は e を含む。

**この「1 本だけ入れ替えても壊れない・悪くならない」構造**が、貪欲を正当化する。動的計画法や分枝限定が要らない ── 局所的に最善の辺が大域的にも安全だから。

---

## 5. 全域木の全列挙 ── 正解オラクル(実測は 5-3)

cut / cycle property は「実測」できる ── 小グラフなら**全域木を全部列挙**して、性質が本当に
成り立つか数え上げで確かめられる:

```python
# 要点(実装とテストは 5-3 の samples: tests/unit/test_mst_properties.py)
def _all_spanning_trees(node_ids, links):
    """リンク候補から (V-1) 本を選ぶ組み合わせのうち、全域木になるものを全列挙(小グラフ専用)。"""
    need = max(len(node_ids) - 1, 0)
    return [combo for combo in combinations(links, need)
            if forms_spanning_tree(node_ids, [link.endpoints for link in combo])]
```

- **`itertools.combinations` で総当たり** ── fixture は 5 頂点 7 リンクなので C(7,4)=35 通り。
  そのうち全域木は数本。この中で最小のものが「真の MST」。
- Phase 3 の `BruteForceRouteStrategy` と同じ発想 ── **小規模で厳密解を出し、貪欲アルゴリズムの
  裏取りに使う**(5-4 の `test_mst_strategies.py` が「Kruskal の総コスト == 既知の最小」を確認)。
- **この列挙オラクルと `test_mst_properties.py` は 5-3 に置く** ── `forms_spanning_tree`
  (`connectivity.py`)と `NetworkLink` / `NetworkDesignData`(`network_design.py`)に依存し、
  どちらも 5-3 で生まれるため(進行のルール #15。テストは自章までのファイルだけで import 解決させる)。
  5-2 で理論を押さえ、schema が揃う 5-3 で実測する、という順序。

---

## 6. まとめ

- cut property: 任意のカットの最小 crossing edge はいずれかの MST に入る ── Kruskal も Prim もこれを回しているだけ。
- cycle property + 交換論法: 閉路の最重量辺はどの MST にも入らない ── 「1 本入れ替えても悪くならない」構造が貪欲を正当化する。
- これらは小グラフの**全域木の全列挙**を正解オラクルにして実測できる ── その実装は 5-3(schema と `forms_spanning_tree` が揃う章)。

## この章のテスト観点

**この章は実装を持たない**(理論章)。cut / cycle property・既知 MST の実測は
[Phase-5-3](./Phase-5-3.md) §7 の `test_mst_properties.py`(全域木の全列挙オラクル)が担う。

理解できたかの確認(実装前チェック):

- 任意のカットで「最小 crossing edge が MST に入る」と言えるのはなぜか(交換論法で説明できるか)。
- 閉路の最重量辺が「どの MST にも入らない」のはなぜか。
- Kruskal / Prim がそれぞれ「どんなカット」を見ているか(§2 の表)。

---

次章([Phase-5-3](./Phase-5-3.md))では、作業単位 5-3 ── `network_design` を判別可能ユニオンに
配線する。`NetworkDesignData` / `NetworkDesignSolution` を 1 メンバーずつ足し、`connectivity.py` と
`build_link_adjacency` を作り、`semantic` / `structure` / `validation` / `verification` /
`select_strategy` に network の分岐を入れる。route / shift には一切触れない。schema が揃うので、
この章の cut / cycle property を全域木の全列挙で**実測する** `test_mst_properties.py` もここで書く。
