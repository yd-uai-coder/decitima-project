"""スケジューリング。シフト割当ソルバー。

手実装トラック(`Phase-0-4.md` §5.3):
- `GreedyShiftStrategy`      … 速いが hard 制約を破ることがある(status="invalid" candidate)
- `BacktrackingShiftStrategy`… 小規模なら最適。規模が増えると指数的に遅くなる
- `BranchAndBoundShiftStrategy` … Backtracking + 下界で枝刈り + 決定論的 anytime

産業ソルバートラック:
- `OrToolsCpSatShiftStrategy` … 実規模でも現実的な時間(implementation="library:ortools")

共通の足回りは `common.py`。設計は `Phase-0-4.md` / `Phase-0-5.md` / README §12.2。
"""
