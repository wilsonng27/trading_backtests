"""Data loading + resampling. Handles Databento 1m CSV / CSV.zst, parquet caching, front-month roll."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import zstandard as zstd

from .config import CACHE_DIR


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def dataset_slug(path: Path) -> str:
    """Stable cache key derived from the source filename — strips .csv / .csv.zst."""
    name = path.name
    for suffix in (".csv.zst", ".csv"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


_DATABENTO_DTYPES = {
    "open": "float32", "high": "float32", "low": "float32",
    "close": "float32", "volume": "int64", "symbol": "category",
}
_DATABENTO_COLS = ["ts_event", "open", "high", "low", "close", "volume", "symbol"]


def _read_databento(src) -> pd.DataFrame:
    return pd.read_csv(
        src,
        usecols=_DATABENTO_COLS,
        dtype=_DATABENTO_DTYPES,
        parse_dates=["ts_event"],
    )


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def load_minute_csv(path: Path) -> pd.DataFrame:
    """Parse Databento 1m OHLCV (.csv or .csv.zst), cache to per-dataset parquet."""
    cache_dir = CACHE_DIR / dataset_slug(path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "raw_1m.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    print(f"[load] reading {path.name}")
    if path.name.endswith(".csv.zst"):
        with open(path, "rb") as fh:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                text = io.TextIOWrapper(reader, encoding="utf-8")
                df = _read_databento(text)
    else:
        df = _read_databento(path)
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df.to_parquet(cache, compression="zstd")
    return df


# Backwards-compat alias — older callers may still import the old name.
load_minute_csv_zst = load_minute_csv


def load_parquet(path: Path) -> pd.DataFrame:
    """Already-prepared OHLCV parquet (ts_event index or column)."""
    df = pd.read_parquet(path)
    if "ts_event" in df.columns:
        df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
        df = df.set_index("ts_event")
    return df.sort_index()


# --------------------------------------------------------------------------- #
# Front-month continuous series
# --------------------------------------------------------------------------- #
def build_front_month(df_1m: pd.DataFrame, cache_key: str = "default") -> pd.DataFrame:
    """Pick most-active contract per UTC date (max daily volume). Mark roll boundaries."""
    cache_dir = CACHE_DIR / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "front_1m.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    print("[front-month] selecting per-day active contract")
    df = df_1m.copy()
    df["date"] = df["ts_event"].dt.tz_convert("America/New_York").dt.date

    daily_vol = (
        df.groupby(["date", "symbol"], observed=True)["volume"]
          .sum()
          .reset_index()
    )
    active = (
        daily_vol.sort_values("volume", ascending=False)
                 .drop_duplicates("date")
                 .set_index("date")["symbol"]
    )
    df["active_sym"] = df["date"].map(active).astype("category")
    front = df[df["symbol"] == df["active_sym"]].copy()
    front = front[["ts_event", "open", "high", "low", "close", "volume", "symbol"]]
    front = front.sort_values("ts_event").set_index("ts_event")

    front["roll"] = front["symbol"].ne(front["symbol"].shift()).astype("int8")
    front.to_parquet(cache, compression="zstd")
    return front


# --------------------------------------------------------------------------- #
# Resampling
# --------------------------------------------------------------------------- #
def resample_ohlcv(df_1m: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = (
        df_1m[["open", "high", "low", "close", "volume"]]
        .resample(rule, label="left", closed="left")
        .agg(agg)
    )
    return out.dropna(subset=["open", "high", "low", "close"])


def attach_roll_flag(df_exec: pd.DataFrame, df_1m: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Mark execution bars that contain a contract roll."""
    if "roll" not in df_1m.columns:
        df_exec["roll_any"] = False
        return df_exec
    roll_per = (
        df_1m["roll"]
        .resample(rule, label="left", closed="left")
        .max()
        .reindex(df_exec.index)
        .fillna(0)
        .astype(bool)
    )
    df_exec["roll_any"] = roll_per
    return df_exec
