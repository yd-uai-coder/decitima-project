"""Network Designer(最小全域木)の問題固有データ(葉モジュール)。

「すべての拠点を最小コストで接続するネットワークを設計する」(README §12.6)。
`route_planning` は start→goal の**単一経路**なので、リンク集合を返す MST は表現できない。
Phase 5-3 で新しい problem_type として追加(`Phase-0-2.md` §8.1)。

このファイルは兄弟(route_planner.py / shift_scheduler.py)を import しない。
ユニオンの合成は problem.py が行う。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class NetworkNode(BaseModel):
    """接続したい拠点1つ。"""

    id: str
    label: str | None = None


class NetworkLink(BaseModel):
    """敷設可能なリンク1本。**常に無向**(route の RouteEdge と違い directed は無い)。"""

    id: str
    endpoints: tuple[str, str]  # 接続する 2 拠点の id
    weight: float  # 敷設コスト / 距離


class NetworkDesignData(BaseModel):
    """Network Designer の問題固有データ。拠点と、敷設可能なリンクの候補。"""

    problem_type: Literal["network_design"] = "network_design"
    nodes: list[NetworkNode]
    links: list[NetworkLink]  # この中から最小コストで全拠点を繋ぐ部分集合を選ぶ
