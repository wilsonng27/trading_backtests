"""Template strategy seeded with a 15-minute ORB long-only example.

Use this file as your starting point:
  - rename ``MyStrategy`` and ``Params`` if you want a clearer strategy identity
  - edit ``build_signals()`` to define your own entry, stop, and target rules
  - keep the returned ``Signals`` arrays aligned and the same length

YOUR RESPONSIBILITY:
  - Code all entry/exit logic, including any risk-to-reward filtering
  - Calculate stop_price and target_price based on your strategy rules
  - Handle all risk management logic (position sizing logic is handled by the engine)
  - The engine will apply slippage and transaction fees automatically

This example implements:
  - 15-minute opening range from 09:30 to 09:45 New York time
  - first close above ORB high triggers a long entry
  - stop at ORB low
  - target at 2R
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backtest_template.strategies.base import Signals, Strategy


@dataclass(frozen=True)
class Params:
    # Add tunable parameters here as your strategy evolves.
    pass


class MyStrategy(Strategy):
    name = "15m_orb_long_only"

    def __init__(self, params: Params | None = None) -> None:
        self.p = params or Params()

    def build_signals(self, df_exec: pd.DataFrame, df_regime: pd.DataFrame) -> Signals:
        # Replace this implementation with your own rules if you are adapting the template.
        # Align timestamps to New York session time for ORB window logic.
        try:
            ny_time = df_exec.index.tz_convert("America/New_York")
        except TypeError:
            ny_time = df_exec.index.tz_localize("UTC").tz_convert("America/New_York")

        df = pd.DataFrame(
            {
                "high": df_exec["high"].to_numpy(np.float64),
                "low": df_exec["low"].to_numpy(np.float64),
                "close": df_exec["close"].to_numpy(np.float64),
                "time_str": ny_time.strftime("%H:%M"),
            },
            index=df_exec.index,
        )

        df["is_orb_window"] = (df["time_str"] >= "09:30") & (df["time_str"] < "09:45")
        df["session_id"] = (df["time_str"] == "09:30").cumsum()

        orb_highs = df[df["is_orb_window"]].groupby("session_id")["high"].max()
        orb_lows = df[df["is_orb_window"]].groupby("session_id")["low"].min()

        df["orb_high"] = df["session_id"].map(orb_highs)
        df["orb_low"] = df["session_id"].map(orb_lows)

        after_orb = df["time_str"] >= "09:45"
        long_cond = after_orb & (df["close"] > df["orb_high"])
        df["long_trigger"] = long_cond & (long_cond.groupby(df["session_id"]).cumsum() == 1)

        raw_idx = np.where(df["long_trigger"])[0]
        entry = df["close"].to_numpy(np.float64)[raw_idx]
        stop = df["orb_low"].to_numpy(np.float64)[raw_idx]
        risk = entry - stop
        target = entry + 2.0 * risk

        return Signals(
            entry_idx=raw_idx.astype(np.int64),
            side=np.ones(raw_idx.size, dtype=np.int8),
            stop_price=stop,
            atr_at_entry=np.ones(raw_idx.size),
            target_price=target,
        )
