"""Trade simulation engine. Side-aware (long/short), SL/TP/time-stop/cooldown/roll exit."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RiskConfig
from .strategies.base import Signals

def simulate_trades(
    df_exec: pd.DataFrame,
    sig: Signals,
    risk: RiskConfig,
    tick_size: float = 0.25,
) -> pd.DataFrame:
    """Walk forward through signal entries, applying SL/TP/time/roll exits and cooldown.

    `df_exec` must have columns: open, high, low, close. Optional: roll_any (bool).
    Signals.side: +1 long, -1 short. Stops/targets are price levels in the side's direction.

    Applies slippage (in ticks) and transaction fees to all trades.
    """
    h = df_exec["high"].to_numpy(np.float64)
    l = df_exec["low"].to_numpy(np.float64)
    c = df_exec["close"].to_numpy(np.float64)
    ts = df_exec.index.tz_convert("UTC").tz_localize(None).values.astype("datetime64[ns]")
    roll = (
        df_exec["roll_any"].to_numpy(bool)
        if "roll_any" in df_exec.columns
        else np.zeros(len(df_exec), dtype=bool)
    )

    cooldown_ns = np.datetime64("1900-01-01", "ns")
    cooldown_delta = np.timedelta64(risk.cooldown_hours, "h").astype("timedelta64[ns]")
    n_bars = len(df_exec)
    trades = []

    # Calculate slippage in price units
    slippage_price = risk.slippage_ticks * tick_size

    for k, i in enumerate(sig.entry_idx):
        entry_ts = ts[i]
        if entry_ts < cooldown_ns:
            continue

        side = int(sig.side[k])
        entry_base = c[i]
        sl = float(sig.stop_price[k])
        tp = float(sig.target_price[k])
        a_e = float(sig.atr_at_entry[k])

        # Apply slippage to entry (worse fill)
        entry = entry_base + side * slippage_price

        risk_pts = (entry - sl) if side > 0 else (sl - entry)
        if risk_pts <= 0 or not np.isfinite(risk_pts):
            continue

        # TP fallback if NaN: N*R from entry in the trade's direction
        if not np.isfinite(tp):
            tp = entry + side * risk.tp_fallback_r * risk_pts

        max_j = min(i + risk.time_stop_bars, n_bars - 1)
        exit_idx, exit_price, reason = -1, np.nan, "open"

        for j in range(i + 1, max_j + 1):
            if roll[j]:
                exit_idx, exit_price, reason = j, c[j - 1], "roll"
                break

            if side > 0:
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp

            if hit_sl and hit_tp:
                exit_idx, exit_price, reason = j, sl, "sl"  # conservative
                break
            if hit_sl:
                exit_idx, exit_price, reason = j, sl, "sl"
                break
            if hit_tp:
                exit_idx, exit_price, reason = j, tp, "tp"
                break

        if exit_idx == -1:
            exit_idx = max_j
            exit_price = c[max_j]
            reason = "time"

        # Apply slippage to exit (worse fill)
        exit_price = exit_price - side * slippage_price

        pnl_pts = side * (exit_price - entry)

        # Subtract transaction fee from PnL
        pnl_pts_net = pnl_pts - (risk.transaction_fee / tick_size) * tick_size

        r = pnl_pts / risk_pts
        r_net = pnl_pts_net / risk_pts

        # Calculate planned RR for reporting
        rr_planned = (tp - entry_base) / risk_pts if side > 0 else (entry_base - tp) / risk_pts

        trades.append({
            "entry_ts":   pd.Timestamp(entry_ts, tz="UTC"),
            "exit_ts":    pd.Timestamp(ts[exit_idx], tz="UTC"),
            "side":       side,
            "entry":      entry,
            "exit":       exit_price,
            "sl":         sl,
            "tp":         tp,
            "atr":        a_e,
            "risk_pts":   risk_pts,
            "pnl_pts":    pnl_pts_net,  # net PnL after costs
            "pnl_gross":  pnl_pts,      # gross PnL before transaction fee
            "r":          r_net,         # net R multiple
            "r_gross":    r,            # gross R multiple before fee
            "bars":       exit_idx - i,
            "rr_planned": rr_planned,
            "reason":     reason,
            "slippage":   slippage_price * 2,  # round-turn slippage
            "fee":        risk.transaction_fee,
        })

        cooldown_ns = ts[exit_idx] + cooldown_delta

    return pd.DataFrame(trades)
