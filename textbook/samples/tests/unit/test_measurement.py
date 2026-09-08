# DeciTima samples │ Phase 3
"""作業単位 3-1: measure_call。

測定コアの純粋テスト。対象は「callable を N 回まわして集計する」機構だけなので、
渡す fn は素のフェイク callable(スタブ不要 ── 外部依存を呼ばない)。
"""

import time

import pytest

from app.services.measurement import Measurement, measure_call


def test_calls_fn_exactly_runs_times() -> None:
    calls = 0

    def fn() -> int:
        nonlocal calls
        calls += 1
        return calls

    result, m = measure_call(fn, runs=5)
    assert calls == 5
    assert result == 5  # 「最後の戻り値」を代表値にする
    assert isinstance(m, Measurement)
    assert m.runs == 5


def test_aggregates_elapsed_and_memory_shape() -> None:
    result, m = measure_call(lambda: [0] * 1000, runs=3)
    assert result == [0] * 1000
    assert m.elapsed_ms_median >= 0.0
    assert m.elapsed_ms_p25 <= m.elapsed_ms_median <= m.elapsed_ms_p75
    assert m.peak_memory_kb > 0.0  # 1000 要素のリストを作っているので割当がある


def test_median_reflects_sleep() -> None:
    # 各 run で ~5ms スリープ → 中央値もおよそ 5ms 以上
    _, m = measure_call(lambda: time.sleep(0.005), runs=3)
    assert m.elapsed_ms_median >= 4.0


def test_runs_one_is_allowed() -> None:
    _, m = measure_call(lambda: 42, runs=1)
    assert m.runs == 1
    assert m.elapsed_ms_p25 == m.elapsed_ms_median == m.elapsed_ms_p75


def test_runs_zero_rejected() -> None:
    with pytest.raises(ValueError):
        measure_call(lambda: 42, runs=0)
