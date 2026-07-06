"""Sequence-shuffle Monte Carlo on the realized R series."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RiskConfig, StatsConfig


def monte_carlo_sequence(
    trades: pd.DataFrame,
    risk: RiskConfig,
    stats: StatsConfig,
) -> dict:
    rs = trades["r"].to_numpy()
    if len(rs) < 5:
        return {}
    rng = np.random.default_rng(stats.rng_seed + 1)
    n = len(rs)
    n_iter = stats.n_monte_carlo

    paths = np.empty((n_iter, n), dtype=np.float64)
    final_eq = np.empty(n_iter)
    max_dds = np.empty(n_iter)

    for i in range(n_iter):
        order = rng.permutation(n)
        eq = risk.init_equity * np.cumprod(1.0 + risk.risk_per_trade * rs[order])
        paths[i] = eq
        final_eq[i] = eq[-1]
        peak = np.maximum.accumulate(eq)
        max_dds[i] = (eq / peak - 1.0).min()

    return {
        "paths":     paths,
        "final_eq":  final_eq,
        "max_dds":   max_dds,
        "median_eq": np.median(final_eq),
        "p5_eq":     np.percentile(final_eq, 5),
        "p95_eq":    np.percentile(final_eq, 95),
        "median_dd": np.median(max_dds),
        "p5_dd":     np.percentile(max_dds, 5),
        "p95_dd":    np.percentile(max_dds, 95),
        "p_ruin":    (max_dds <= stats.ruin_dd).mean(),
    }


def print_monte_carlo(m: dict, n_iter: int, ruin_dd: float) -> None:
    if not m:
        return
    print(f"\n=== Monte Carlo Sequence Shuffle (n={n_iter:,}) ===")
    print(f"  Final Equity      : median ${m['median_eq']:,.0f}  "
          f"P5 ${m['p5_eq']:,.0f}  P95 ${m['p95_eq']:,.0f}")
    print(f"  Max Drawdown      : median {m['median_dd']:.2%}  "
          f"P5 {m['p5_dd']:.2%}  P95 {m['p95_dd']:.2%}")
    print(f"  P(DD <= {ruin_dd:.0%})    : {m['p_ruin']:.2%}")
