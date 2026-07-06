"""Backtest entrypoint for this strategy folder.

Run from trading_backtests/:
    python -m strategy_template_long_only_orb.run
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from backtest_template.config import EngineConfig, RiskConfig, StatsConfig
from backtest_template.main import load_from_databento_csv, run

from .strategy import MyStrategy, Params


DATA_PATH = Path("/Users/chunwaing/Data/nq_ohlcv.csv")
HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Edit these — everything else is engine-managed
# --------------------------------------------------------------------------- #


def main(
    slippage_ticks: float = 1,
    transaction_fee: float = 2.5,
    start_date: str = "2020-01-01",
    end_date: str = "2026-06-17",
    risk_per_trade: float = 0.01,
    tick_size: float = 0.25,
) -> None:
    """Run backtest with customizable parameters."""
    cfg = EngineConfig(
        exec_tf="5min",
        regime_tf="1d",
        risk=RiskConfig(
            risk_per_trade=risk_per_trade,
            slippage_ticks=slippage_ticks,
            transaction_fee=transaction_fee,
        ),
        stats=StatsConfig(),
        start=pd.Timestamp(start_date, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC"),
        tick_size=tick_size,
    )

    df_exec, df_regime = load_from_databento_csv(DATA_PATH, cfg)
    run(df_exec, df_regime, MyStrategy(Params()), cfg, out_dir=HERE)


if __name__ == "__main__":
    main()
