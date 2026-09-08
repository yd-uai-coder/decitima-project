# DeciTima samples │ Phase 1
"""線形探索(プリミティブ)。README §8 の Linear Search。

binary_search との対比用のウォームアップ。ソートを前提にしないぶん O(n) だが、
「前提条件が要らない」という利点がある。registry には載せない素の純粋関数。
"""

from __future__ import annotations

from collections.abc import Sequence


def linear_search[T](seq: Sequence[T], target: T) -> int:
    """seq を先頭から走査し、target と等しい最初の要素の添字を返す。無ければ -1。

    時間 O(n) / 空間 O(1)。seq はソートされていなくてよい。
    """
    for i, value in enumerate(seq):
        if value == target:
            return i
    return -1
