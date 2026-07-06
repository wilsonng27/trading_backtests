"""Equity curve, R-distribution, MC histogram plots."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import RiskConfig


def plot_equity(eq: pd.DataFrame, title: str, out_dir: Path) -> None:
    if eq.empty:
        return
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(eq.index, eq["equity"], lw=1.4, color="#1f77b4")
    ax.set_title(title)
    ax.set_ylabel("Equity ($)")
    ax.set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(out_dir / "equity_curve.png", dpi=130)
    plt.close(fig)


def plot_r_distribution(trades: pd.DataFrame, out_dir: Path) -> None:
    if trades.empty:
        return
    rs = trades["r"].to_numpy(dtype=np.float64)
    rs = rs[np.isfinite(rs)]
    if rs.size == 0:
        return
    bins = 1 if rs.min() == rs.max() else 40
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(rs, bins=bins, color="#9467bd", alpha=0.85)
    ax.axvline(0, color="black", lw=1)
    ax.set_title("R-Multiple Distribution")
    ax.set_xlabel("R")
    fig.tight_layout()
    fig.savefig(out_dir / "r_distribution.png", dpi=130)
    plt.close(fig)


def plot_monte_carlo(mc: dict, risk: RiskConfig, out_dir: Path) -> None:
    if not mc:
        return

    dds = np.asarray(mc["max_dds"], dtype=np.float64)
    dds = dds[np.isfinite(dds)]
    paths = np.asarray(mc.get("paths", np.empty((0, 0))), dtype=np.float64)

    if dds.size == 0 and paths.size == 0:
        return

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    # Left: Max DD distribution
    if dds.size > 0:
        rng = dds.max() - dds.min()
        scale = max(abs(dds.max()), abs(dds.min()), 1.0)
        bins = 1 if rng <= scale * 1e-9 else 60
        axes[0].hist(dds, bins=bins, color="#d62728", alpha=0.85)
        axes[0].axvline(np.median(dds), color="black", lw=1, ls="--", label="median")
    axes[0].set_title("MC Max Drawdowns")
    axes[0].set_xlabel("Max DD")
    axes[0].legend()

    # Right: Equity-curve fan chart over shuffled sequences
    if paths.size > 0:
        n_iter, n_trades = paths.shape
        x = np.arange(1, n_trades + 1)
        # subsample raw paths so the plot stays light
        sample = paths[: min(200, n_iter)]
        for p in sample:
            axes[1].plot(x, p, color="#2ca02c", lw=0.4, alpha=0.08)
        median = np.median(paths, axis=0)
        p5 = np.percentile(paths, 5, axis=0)
        p95 = np.percentile(paths, 95, axis=0)
        axes[1].fill_between(x, p5, p95, color="#2ca02c", alpha=0.20, label="P5–P95")
        axes[1].plot(x, median, color="#0a5d2a", lw=1.6, label="median")
        axes[1].axhline(risk.init_equity, color="black", lw=0.8, ls="--", label="start")
    axes[1].set_title("MC Equity Paths (shuffled order)")
    axes[1].set_xlabel("Trade #")
    axes[1].set_ylabel("Equity ($)")
    axes[1].legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(out_dir / "monte_carlo.png", dpi=130)
    plt.close(fig)


def plot_all(eq: pd.DataFrame, trades: pd.DataFrame, mc: dict,
             risk: RiskConfig, title: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_equity(eq, title, out_dir)
    plot_r_distribution(trades, out_dir)
    plot_monte_carlo(mc, risk, out_dir)
    print(f"[plots] saved to {out_dir}")
