"""Example strategy: Donchian breakout, long-only, regime-filtered.

Replace with your own — just subclass Strategy and emit Signals.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import Signals, Strategy
from .indicators import atr, ema


@dataclass(frozen=True)
class BreakoutParams:
    atr_len: int = 14
    regime_ema_len: int = 50
    donchian_lookback: int = 20
    sl_atr_mult: float = 1.5
    tp_atr_mult: float = 3.0


class DonchianBreakout(Strategy):
    name = "donchian_breakout"

    def __init__(self, params: BreakoutParams | None = None) -> None:
        self.p = params or BreakoutParams()

    def build_signals(self, df_exec: pd.DataFrame, df_regime: pd.DataFrame) -> Signals:
        p = self.p
        h = df_exec["high"].to_numpy(np.float64)
        c = df_exec["close"].to_numpy(np.float64)
        a = atr(df_exec, p.atr_len).to_numpy(np.float64)

        # Donchian upper from prior N highs (exclude current bar)
        prior_hh = (
            df_exec["high"].shift(1).rolling(p.donchian_lookback).max().to_numpy(np.float64)
        )

        # Higher-tf regime: close > EMA
        regime = (df_regime["close"] > ema(df_regime["close"], p.regime_ema_len)).astype("int8")
        regime_exec = regime.reindex(df_exec.index, method="ffill").fillna(0).to_numpy(bool)

        breakout = c > prior_hh
        valid = breakout & regime_exec & ~np.isnan(a) & ~np.isnan(prior_hh)
        idx = np.where(valid)[0]

        side = np.ones(idx.size, dtype=np.int8)
        atr_e = a[idx]
        entry = c[idx]
        stop = entry - p.sl_atr_mult * atr_e
        target = entry + p.tp_atr_mult * atr_e

        print(f"[{self.name}] {idx.size} raw entry candidates")
        return Signals(
            entry_idx=idx,
            side=side,
            stop_price=stop,
            atr_at_entry=atr_e,
            target_price=target,
        )
