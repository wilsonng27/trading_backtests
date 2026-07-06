"""IID bootstrap CIs on the trade-level R distribution."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import StatsConfig


def bootstrap_ci(trades: pd.DataFrame, stats: StatsConfig) -> dict:
    rs = trades["r"].to_numpy()
    if len(rs) < 5:
        return {}
    rng = np.random.default_rng(stats.rng_seed)
    idx = rng.integers(0, len(rs), size=(stats.n_bootstrap, len(rs)))
    samples = rs[idx]
    means = samples.mean(axis=1)
    stds = samples.std(axis=1, ddof=1)
    sharpes = np.where(stds > 0, means / stds * np.sqrt(len(rs)), np.nan)
    return {
        "mean_pt":   means.mean(),
        "mean_lo":   np.nanpercentile(means, 2.5),
        "mean_hi":   np.nanpercentile(means, 97.5),
        "sharpe_pt": np.nanmean(sharpes),
        "sharpe_lo": np.nanpercentile(sharpes, 2.5),
        "sharpe_hi": np.nanpercentile(sharpes, 97.5),
        "p_pos":     (means > 0).mean(),
    }


def print_bootstrap(b: dict, n_iter: int) -> None:
    if not b:
        return
    print(f"\n=== Bootstrap (n={n_iter:,}, 95% CI) ===")
    print(f"  Mean R-Multiple   : {b['mean_pt']:.3f}  CI [{b['mean_lo']:.3f}, {b['mean_hi']:.3f}]")
    print(f"  Sharpe (per-trade): {b['sharpe_pt']:.3f}  CI [{b['sharpe_lo']:.3f}, {b['sharpe_hi']:.3f}]")
    print(f"  P(mean R > 0)     : {b['p_pos']:.2%}")
