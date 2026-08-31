"""registry ── problem_type からアルゴリズム候補を引く仕組み。

設計は Phase-0-4.md §4。このファイルは **純粋**(app.domain と標準ライブラリしか import しない)。

Phase-0-4.md の設計スケッチでは select_strategy をここに置き NoAlgorithmError を送出して
いたが、NoAlgorithmError は HTTP ステータスに対応する AppError 派生(app/services/errors.py)
であり、それを algorithms 層が import すると「algorithms → services」の逆流になる
(Phase-0-3.md §2.2 の依存方向)。そこで Phase 1 では:
  - registry.py(純粋): REGISTRY / get_strategies / all_strategies /
    find_strategy(見つからなければ None を返す)
  - app/services/algorithm_selection.py: select_strategy(None のとき NoAlgorithmError を送出)
に分ける。判断の記録はルート CLAUDE.md の Notes。

各 strategy は「それを作成した章」でコメントを外して有効化する(進行ルール #15)。
registry は集約モジュールなので作成順の都合で未作成の strategy を前方参照しがち ──
コメントアウト + マーカーで「その章まで写経すればテストが緑」を保つ。
"""

from __future__ import annotations

from app.algorithms.base import AlgorithmStrategy

# 作業単位 1-4 で次行のコメントを外す(進行ルール #15)
# from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.domain.problems.problem import OptimizationProblem

# problem_type -> 候補アルゴリズム。エントリはモジュールロード時に1回だけ生成する
# (solve が純粋 = インスタンス状態を持たないので安全。Phase-0-4.md §4.2)。
# 新しいアルゴリズムの追加は 1 行足すだけ(オープン・クローズドの原則)。
REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [
        # DijkstraStrategy(),     ← 作業単位 1-4 で有効化
        # AStarStrategy(),        ← Phase 4
        # NetworkxShortestPath(), ← Phase 4(networkx 導入時)
    ],
    "shift_scheduling": [
        # GreedyShiftStrategy(), BacktrackingShiftStrategy() ← Phase 5
    ],
}


def get_strategies(problem_type: str) -> list[AlgorithmStrategy]:
    """problem_type に対応するアルゴリズム候補を返す。未登録なら空リスト。"""
    return REGISTRY.get(problem_type, [])


def all_strategies() -> list[tuple[str, AlgorithmStrategy]]:
    """(problem_type, strategy) の全ペア。GET /api/v1/algorithms が使う。"""
    return [(pt, s) for pt, strategies in REGISTRY.items() for s in strategies]


def find_strategy(
    problem: OptimizationProblem, requested: str | None = None
) -> AlgorithmStrategy | None:
    """rule-based のアルゴリズム選択(純粋版)。該当が無ければ None を返す(送出はしない)。

    - requested 指定があれば meta.name 一致を最優先
    - MVP の rule は素朴に「候補の先頭」(Phase-0-4.md §6。問題特性による分岐は Phase 4/5)
    """
    candidates = get_strategies(problem.problem_type)
    if not candidates:
        return None
    if requested is not None:
        return next((s for s in candidates if s.meta.name == requested), None)
    return candidates[0]
