# DeciTima samples │ Phase 10
"""作業単位 10-3: find_threshold(二分探索の応用 ──「答えを二分探索する」)。

テスト対象 / ドライバ / スタブ:
- 対象: `app.algorithms.optimization.threshold_search.find_threshold`
- ドライバ: このテスト関数
- スタブ: フェイクの `evaluate`(実運用では 1 回の solve に相当する重い呼び出しなので、
  ユニットテストでは単純な数式に差し替える ── 進行のルール #14「スタブの要否がレイヤー
  設計の鏡」。`evaluate` を注入可能にした設計そのものがこのテストを軽くしている)。
"""

from __future__ import annotations

import pytest

from app.algorithms.optimization.threshold_search import find_threshold


def test_find_threshold_at_most_finds_minimal_param_below_target() -> None:
    """evaluate が非増加(param が増えるほど値が下がる)。target 以下になる最小の param。"""
    values = {1: 10.0, 2: 8.0, 3: 6.0, 4: 4.0, 5: 2.0}
    calls: list[int] = []

    def evaluate(param: int) -> float:
        calls.append(param)
        return values[param]

    result = find_threshold(1, 5, evaluate, target=5.0, mode="at_most")

    assert result == 4  # values[4]=4.0 <= 5.0 が最小の param
    assert len(calls) < 5  # 全件スイープ(5 回)より少ない呼び出し数(教材の核)


def test_find_threshold_at_least_finds_minimal_param_reaching_target() -> None:
    """evaluate が非減少(param が増えるほど値が上がる)。target 以上になる最小の param。"""
    values = {1: 1.0, 2: 3.0, 3: 5.0, 4: 7.0, 5: 9.0}
    result = find_threshold(1, 5, lambda p: values[p], target=5.0, mode="at_least")
    assert result == 3


def test_find_threshold_returns_none_when_no_point_in_range_satisfies() -> None:
    """range の右端でも条件を満たさなければ、範囲内に答えは無い。"""
    values = {1: 10.0, 2: 9.0, 3: 8.0}
    result = find_threshold(1, 3, lambda p: values[p], target=0.0, mode="at_most")
    assert result is None


def test_find_threshold_single_point_range() -> None:
    result = find_threshold(3, 3, lambda _p: 1.0, target=1.0, mode="at_most")
    assert result == 3


def test_find_threshold_rejects_low_greater_than_high() -> None:
    with pytest.raises(ValueError, match="low"):
        find_threshold(5, 1, lambda _p: 0.0, target=0.0)


def test_find_threshold_can_be_misled_when_monotonicity_assumption_is_violated() -> None:
    """単調性が崩れた入力では、実際に条件を満たす最小の点とは異なる値を返しうる
    (前提が崩れたときの挙動を実演する ── 誤った答えを「決定論的に」返す点に注意)。

    values: 1→2.0(満たす), 2→9.0(満たさない), 3→1.0(満たす) は単調でない。
    """
    values = {1: 2.0, 2: 9.0, 3: 1.0}
    result = find_threshold(1, 3, lambda p: values[p], target=5.0, mode="at_most")

    # 単調性を仮定した二分探索は mid=2 で「満たさない」と判定し右半分を探索するため、
    # 本来最小の 1(values[1]=2.0<=5.0)を見落として 3 を返す
    assert result == 3
