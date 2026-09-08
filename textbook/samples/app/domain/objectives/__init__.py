# DeciTima samples │ Phase 6
"""目的。多目的の重み付き和の評価をここに置く(型 `Objective` は problems/ 側)。

Phase 6 で初実装 ── 初の多目的ストラテジー(Shift Scheduler の Greedy / Backtracking / B&B)が
探索中に候補割当を採点するのに使う。当初 Phase 1 の予定だったが、Phase 1 で registry に載る
唯一の strategy(Dijkstra)は単一目的で消費者がいなかったため先送りしていた
(`Phase-0-2.md` §2.5 / `Phase-0-3.md` §2.3 のマーカー)。

設計は `Phase-0-2.md` §3。
"""

from app.domain.objectives.weighted_sum import weighted_sum

__all__ = ["weighted_sum"]
