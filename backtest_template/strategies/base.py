"""Strategy contract. Implementations return Signals consumed by backtest.simulate_trades."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Signals:
    """Per-entry inputs the simulator needs.

    All arrays have the same length N (one per entry candidate).
    `entry_idx` indexes into the execution-tf DataFrame passed to the simulator.
    """
    entry_idx: np.ndarray         # int positions in df_exec
    side: np.ndarray              # +1 long, -1 short
    stop_price: np.ndarray        # initial stop price
    atr_at_entry: np.ndarray      # ATR (price units) at entry — used for SL buffer
    target_price: np.ndarray      # planned TP price; NaN -> simulator uses RR fallback


class Strategy(ABC):
    """Subclass + implement build_signals."""
    name: str = "strategy"

    @abstractmethod
    def build_signals(self, df_exec: pd.DataFrame, df_regime: pd.DataFrame) -> Signals:
        ...
