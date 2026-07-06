"""End-to-end runner.

Two ways to use this engine:

A) Run this file directly to backtest the example strategy on the default dataset:
       python -m backtest_template.main

B) Recommended for new strategies — create a sibling folder (e.g. ../my_strat/)
   with a `run.py` that imports from this package. See README pattern in answer.
   You then never edit anything inside backtest_template/ again.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .analytics import core_analytics, equity_curve, print_analytics
from .backtest import simulate_trades
from .bootstrap import bootstrap_ci, print_bootstrap
from .config import EngineConfig, get_tick_size
from .data import (
    attach_roll_flag,
    build_front_month,
    dataset_slug,
    load_minute_csv,
    load_parquet,
    resample_ohlcv,
)
from .monte_carlo import monte_carlo_sequence, print_monte_carlo
from .plots import plot_all
from .strategies.base import Strategy
from .strategies.example_breakout import DonchianBreakout


# --------------------------------------------------------------------------- #
# Data ingest — pick the path that matches your dataset
# --------------------------------------------------------------------------- #
def load_from_databento_csv(path: Path, cfg: EngineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Databento 1m multi-contract CSV / CSV.zst → front-month → resampled exec/regime frames."""
    raw = load_minute_csv(path)
    front = build_front_month(raw, cache_key=dataset_slug(path))
    front = front.loc[(front.index >= cfg.start) & (front.index < cfg.end)]

    # Auto-detect tick size from first symbol if not explicitly set
    if cfg.tick_size == 0.25 and "symbol" in front.columns and len(front) > 0:
        first_symbol = str(front["symbol"].iloc[0])
        detected_tick = get_tick_size(first_symbol)
        if detected_tick != 0.25:  # only print if different from default
            print(f"[config] Auto-detected tick size: {detected_tick} from symbol {first_symbol}")

    df_exec = resample_ohlcv(front, cfg.exec_tf)
    df_regime = resample_ohlcv(front, cfg.regime_tf)
    df_exec = attach_roll_flag(df_exec, front, cfg.exec_tf)
    return df_exec, df_regime


# Backwards-compat alias for older runners.
load_from_csv_zst = load_from_databento_csv


def load_from_parquet(path: Path, cfg: EngineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pre-built 1m parquet (single contract or already rolled)."""
    df_1m = load_parquet(path)
    df_1m = df_1m.loc[(df_1m.index >= cfg.start) & (df_1m.index < cfg.end)]
    df_exec = resample_ohlcv(df_1m, cfg.exec_tf)
    df_regime = resample_ohlcv(df_1m, cfg.regime_tf)
    if "roll" in df_1m.columns:
        df_exec = attach_roll_flag(df_exec, df_1m, cfg.exec_tf)
    return df_exec, df_regime


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def run(
    df_exec: pd.DataFrame,
    df_regime: pd.DataFrame,
    strategy: Strategy,
    cfg: EngineConfig,
    out_dir: Path,
) -> pd.DataFrame:
    """Full pipeline. Writes plots + trades.parquet + equity.parquet into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[data] exec ({cfg.exec_tf}): {len(df_exec):,}  regime ({cfg.regime_tf}): {len(df_regime):,}")

    sig = strategy.build_signals(df_exec, df_regime)
    trades = simulate_trades(df_exec, sig, cfg.risk, tick_size=cfg.tick_size)
    print(f"[sim] {len(trades)} trades after cooldown")
    if trades.empty:
        return trades

    eq = equity_curve(trades, cfg.risk)
    print_analytics(core_analytics(trades, eq, cfg.risk))
    print_bootstrap(bootstrap_ci(trades, cfg.stats), cfg.stats.n_bootstrap)
    mc = monte_carlo_sequence(trades, cfg.risk, cfg.stats)
    print_monte_carlo(mc, cfg.stats.n_monte_carlo, cfg.stats.ruin_dd)
    plot_all(eq, trades, mc, cfg.risk, title=f"Equity — {strategy.name}", out_dir=out_dir)

    trades.to_parquet(out_dir / "trades.parquet")
    eq.to_parquet(out_dir / "equity.parquet")
    print(f"\n[done] artifacts in {out_dir}")
    return trades


# --------------------------------------------------------------------------- #
# Default smoke run — NQ Databento CSV → front-month → DonchianBreakout
# --------------------------------------------------------------------------- #
DEFAULT_CSV = Path("/Users/chunwaing/Data/nq_ohlcv.csv")


def main() -> None:
    cfg = EngineConfig()
    df_exec, df_regime = load_from_databento_csv(DEFAULT_CSV, cfg)
    run(df_exec, df_regime, DonchianBreakout(), cfg, out_dir=Path(__file__).resolve().parent / "_demo_out")


if __name__ == "__main__":
    main()
