"""Route Planner の問題固有データ(葉モジュール)。

このファイルは兄弟モジュール(shift_scheduler.py)を import しない。
ユニオンの合成は problem.py(アグリゲータ)が行う。設計は Phase-0-2.md §5.1 / §2.5。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RouteNode(BaseModel):
    """経路問題のノード1つ。座標 x / y は A*(Phase 4)のヒューリスティック用で任意。"""

    id: str
    label: str | None = None
    x: float | None = None
    y: float | None = None


class RouteEdge(BaseModel):
    """経路問題のエッジ1本。weight は距離または所要時間で、非負(Dijkstra の前提)。"""

    id: str
    source: str  # 端点ノードの id
    target: str  # 端点ノードの id
    # weight: Field(ge=0) で「負の重みは Pydantic が弾く」= Input Validation の一部
    weight: float = Field(ge=0)
    directed: bool = False  # False なら source <-> target の双方向


class RouteData(BaseModel):
    """Route Planner の問題固有データ。グラフ(ノード・エッジ)と始点・終点。"""

    problem_type: Literal["route_planning"] = "route_planning"
    nodes: list[RouteNode]
    edges: list[RouteEdge]
    start: str  # 出発ノードの id
    goal: str  # 目標ノードの id
