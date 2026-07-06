"""Common indicators reused across strategies."""
from __future__ import annotations

import numpy as np
import pandas as pd


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift()
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def fractal_swing_highs(h: np.ndarray, k: int = 2) -> np.ndarray:
    n = len(h)
    out = np.zeros(n, dtype=bool)
    for i in range(k, n - k):
        seg = h[i - k:i + k + 1]
        if h[i] == seg.max() and (seg == h[i]).sum() == 1:
            out[i] = True
    return out


def fractal_swing_lows(l: np.ndarray, k: int = 2) -> np.ndarray:
    n = len(l)
    out = np.zeros(n, dtype=bool)
    for i in range(k, n - k):
        seg = l[i - k:i + k + 1]
        if l[i] == seg.min() and (seg == l[i]).sum() == 1:
            out[i] = True
    return out
