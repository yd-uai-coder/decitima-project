"""Route Planner の問題固有データ(葉モジュール)。

このファイルは兄弟モジュール(shift_scheduler.py / network_design.py)を import しない。
ユニオンの合成は problem.py(アグリゲータ)が行う。設計は Phase-0-2.md §5.1 / §2.5。

Phase 4 での変更(Phase 1 で凍結していたモデルの改訂):
  - `RouteEdge.weight` の `Field(ge=0)` を撤廃(負辺を Bellman-Ford で扱うため)
  - `RouteData.allow_negative` を追加 ── False(既定)なら負辺を model_validator が弾く
    ので、従来の「負の重みは Pydantic が弾く」挙動はデフォルトのまま保たれる
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator


class RouteNode(BaseModel):
    """経路問題のノード1つ。座標 x / y は A*(Phase 4)のヒューリスティック用で任意。"""

    id: str
    label: str | None = None
    x: float | None = None
    y: float | None = None


class RouteEdge(BaseModel):
    """経路問題のエッジ1本。weight は距離または所要時間。

    Phase 1 は weight=Field(ge=0) で負を Pydantic が弾いていた。Phase 4 で負辺を
    許容できるようにし(Bellman-Ford 用)、ガードは RouteData 側の model_validator に移した。
    """

    id: str
    source: str  # 端点ノードの id
    target: str  # 端点ノードの id
    weight: float
    directed: bool = False  # False なら source <-> target の双方向


class RouteData(BaseModel):
    """Route Planner の問題固有データ。グラフ(ノード・エッジ)と始点・終点。"""

    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str  # 出発ノードの id
    goal: str  # 目標ノードの id
    # True のときだけ負辺を許可する。負辺は Dijkstra/A* が扱えないので Bellman-Ford 前提。
    allow_negative: bool = False

    @model_validator(mode="after")
    def _guard_negative_weights(self) -> RouteData:
        """allow_negative=False で負辺があれば Input Validation で弾く(従来の ge=0 相当)。"""
        if not self.allow_negative:
            bad = [e.id for e in self.edges if e.weight < 0]
            if bad:
                raise ValueError(
                    f"negative weight on edge(s) {bad}; set allow_negative=True to use Bellman-Ford"
                )
        return self
