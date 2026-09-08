"""問題解決パターン。two_pointers / sliding_window / prefix_sum / difference_array など、
他アルゴリズムの内部で使う補助的な手法。registry には載らない素の純粋関数。

Phase 6 で実装(Shift Scheduler が使う):
- `sliding_window` … 連続勤務日数のチェック(Backtracking の逐次可否判定)
- `difference_array`(imos 法)… 時間帯別の在籍人数を O(スロット数) で構築

設計は `Phase-0-4.md` §2.4、README §8。
"""
