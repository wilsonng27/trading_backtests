"""Equity curve + summary stats."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RiskConfig


def equity_curve(trades: pd.DataFrame, risk: RiskConfig) -> pd.DataFrame:
    """Compound equity: each trade risks `risk_per_trade` of current equity per 1R."""
    if trades.empty:
        return pd.DataFrame()
    eq = risk.init_equity
    rows = []
    for _, t in trades.iterrows():
        eq += eq * risk.risk_per_trade * t["r"]
        rows.append({"exit_ts": t["exit_ts"], "equity": eq, "r": t["r"]})
    return pd.DataFrame(rows).set_index("exit_ts")


def core_analytics(trades: pd.DataFrame, eq: pd.DataFrame, risk: RiskConfig) -> dict:
    if trades.empty or eq.empty:
        return {}
    rs = trades["r"].to_numpy()
    eq_s = eq["equity"]

    total_ret = eq_s.iloc[-1] / risk.init_equity - 1.0
    days = max((eq_s.index[-1] - eq_s.index[0]).days, 1)
    cagr = (eq_s.iloc[-1] / risk.init_equity) ** (365.25 / days) - 1.0

    peak = eq_s.cummax()
    max_dd = (eq_s / peak - 1.0).min()

    # per-trade returns -> annualized Sharpe/Sortino
    eq_arr = eq_s.to_numpy()
    prev = np.concatenate([[risk.init_equity], eq_arr[:-1]])
    rets = eq_arr / prev - 1.0
    yrs = max(days / 365.25, 1e-6)
    tpy = len(rets) / yrs
    mu, sd = rets.mean(), rets.std(ddof=1)
    sharpe = (mu / sd) * np.sqrt(tpy) if sd > 0 else np.nan
    downside = rets[rets < 0]
    sortino = (mu / downside.std(ddof=1)) * np.sqrt(tpy) if downside.size > 1 else np.nan

    wins = rs > 0
    losses = ~wins
    pf = (
        rs[wins].sum() / -rs[losses].sum()
        if losses.any() and rs[losses].sum() != 0
        else np.nan
    )

    return {
        "trades":        len(trades),
        "total_return":  total_ret,
        "cagr":          cagr,
        "max_dd":        max_dd,
        "sharpe":        sharpe,
        "sortino":       sortino,
        "win_rate":      wins.mean(),
        "profit_factor": pf,
        "avg_r":         rs.mean(),
        "avg_hold_bars": trades["bars"].mean(),
    }


def print_analytics(a: dict) -> None:
    if not a:
        print("No trades.")
        return
    print("\n=== Core Analytics ===")
    print(f"  Trades            : {a['trades']}")
    print(f"  Total Return      : {a['total_return']:.2%}")
    print(f"  CAGR              : {a['cagr']:.2%}")
    print(f"  Max Drawdown      : {a['max_dd']:.2%}")
    print(f"  Sharpe (ann.)     : {a['sharpe']:.2f}")
    print(f"  Sortino (ann.)    : {a['sortino']:.2f}")
    print(f"  Win Rate          : {a['win_rate']:.2%}")
    print(f"  Profit Factor     : {a['profit_factor']:.2f}")
    print(f"  Avg R-Multiple    : {a['avg_r']:.3f}")
    print(f"  Avg Hold (bars)   : {a['avg_hold_bars']:.1f}")
