"""Backtest engine + risk config. Strategy-specific knobs live in each strategy module."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# --------------------------------------------------------------------------- #
# Paths / window
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent
# Shared cache for slow data prep (raw_1m.parquet, front_1m.parquet) — strategy-agnostic.
CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)

START = pd.Timestamp("2019-01-01", tz="UTC")
END = pd.Timestamp("2026-01-01", tz="UTC")


# --------------------------------------------------------------------------- #
# Tick sizes for different futures contracts
# --------------------------------------------------------------------------- #
TICK_SIZES = {
    "ES": 0.25,      # E-mini S&P 500
    "MES": 0.25,     # Micro E-mini S&P 500
    "NQ": 0.25,      # E-mini Nasdaq-100
    "MNQ": 0.25,     # Micro E-mini Nasdaq-100
    "YM": 1.0,       # E-mini Dow ($5 Jones)
    "MYM": 1.0,      # Micro E-mini Dow
    "RTY": 0.10,     # E-mini Russell 2000
    "M2K": 0.10,     # Micro E-mini Russell 2000
    "CL": 0.01,      # Crude Oil
    "MCL": 0.01,     # Micro Crude Oil
    "GC": 0.10,      # Gold
    "MGC": 0.10,     # Micro Gold
    "SI": 0.005,     # Silver
    "SIL": 0.005,    # Micro Silver
    "ZN": 0.015625,  # 10-Year T-Note (1/64)
    "ZB": 0.03125,   # 30-Year T-Bond (1/32)
}


def get_tick_size(symbol: str) -> float:
    """Extract tick size from symbol. Handles root symbols like 'ESH4' -> 'ES'."""
    for root in TICK_SIZES:
        if symbol.startswith(root):
            return TICK_SIZES[root]
    return 0.01  # default fallback


# --------------------------------------------------------------------------- #
# Engine config (shared across strategies)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RiskConfig:
    init_equity: float = 100_000.0
    risk_per_trade: float = 0.01      # fraction of equity risked per 1R
    sl_buf_atr: float = 0.20
    tp_fallback_r: float = 2.0
    time_stop_bars: int = 48
    cooldown_hours: int = 24
    slippage_ticks: float = 1.0       # slippage in ticks per side
    transaction_fee: float = 2.50     # cost per round-turn trade (both entry + exit)


@dataclass(frozen=True)
class StatsConfig:
    n_bootstrap: int = 10_000
    n_monte_carlo: int = 1_000
    rng_seed: int = 7
    ruin_dd: float = -0.50            # P(MaxDD <= ruin_dd) in MC


@dataclass(frozen=True)
class EngineConfig:
    exec_tf: str = "1h"               # execution timeframe
    regime_tf: str = "4h"              # higher-tf context
    risk: RiskConfig = field(default_factory=RiskConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)
    start: pd.Timestamp = START
    end: pd.Timestamp = END
    tick_size: float = 0.25           # tick size for the instrument (auto-detected if symbol available)
