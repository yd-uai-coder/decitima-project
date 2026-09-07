"""benchmark レポートの図(matplotlib)。

`savefig` はしない ── ファイルに落とすか notebook にinline表示するかは呼び出し側の責務。
ヘッドレス環境(CI / `jupyter nbconvert`)では `MPLBACKEND=Agg` か、テスト側で
`matplotlib.use("Agg")` を先に呼ぶ。

Phase 4 で `plot_handwritten_vs_library`(route benchmark 用)を追加。
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def plot_comparison(report_df: pd.DataFrame, *, metric: str = "elapsed_ms_median") -> Figure:
    """`by_algorithm()` の出力を棒グラフに(アルゴリズム × 指標)。"""
    fig, ax = plt.subplots()
    ax.bar(report_df["algorithm"], report_df[metric])
    ax.set_ylabel(metric)
    ax.set_title(f"algorithm comparison — {metric}")
    fig.tight_layout()
    return fig


def plot_input_size_curve(
    curve_df: pd.DataFrame, *, size_col: str = "size", log: bool = True
) -> Figure:
    """`input_size_curve()` の出力を折れ線に。全探索の指数的な伸びを見るため既定は対数 y 軸。"""
    fig, ax = plt.subplots()
    for col in curve_df.columns:
        if col == size_col:
            continue
        ax.plot(curve_df[size_col], curve_df[col], marker="o", label=col)
    if log:
        ax.set_yscale("log")
    ax.set_xlabel(size_col)
    ax.set_ylabel("operation count")
    ax.set_title("input size vs operation count")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_handwritten_vs_library(pivot_df: pd.DataFrame, *, algorithm: str = "dijkstra") -> Figure:
    """`route_benchmark.handwritten_vs_library()` の出力を size × 実装の折れ線に。"""
    rows = pivot_df[pivot_df["algorithm"] == algorithm].sort_values("size")
    fig, ax = plt.subplots()
    for col in ("handwritten",) + tuple(
        c for c in pivot_df.columns if isinstance(c, str) and c.startswith("library")
    ):
        if col in rows.columns:
            ax.plot(rows["size"], rows[col], marker="o", label=col)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("size (nodes)")
    ax.set_ylabel("elapsed_ms_median")
    ax.set_title(f"{algorithm}: handwritten vs library")
    ax.legend()
    fig.tight_layout()
    return fig
