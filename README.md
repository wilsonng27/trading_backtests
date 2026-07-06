# trading_backtests

Public subset of a larger local backtesting workspace.

This repo intentionally exposes only:

- `backtest_template/`: the reusable engine
- `strategy_template_long_only_orb/`: a template strategy folder built on top of that engine

Everything else in the local `trading_backtests/` workspace stays private and should not be pushed.

## Included Folders

### `backtest_template/`

Shared backtest engine:

- data loading for Databento-style 1-minute OHLCV CSV / CSV.zst
- front-month continuous contract construction
- resampling into execution and regime timeframes
- signal contract via `Signals`
- trade simulation with slippage, fees, cooldown, and time stop
- analytics, bootstrap stats, Monte Carlo analysis, and plots

### `strategy_template_long_only_orb/`

Example/template strategy package that imports `backtest_template` and shows how to:

- create a strategy folder outside the engine
- implement `build_signals(df_exec, df_regime)`
- configure a runnable `run.py`

## Local Layout

```text
trading_backtests/
├── backtest_template/
└── strategy_template_long_only_orb/
```

## Install

Python 3.12+ recommended.

```bash
pip install -r requirements.txt
```

## Run

From the repo root:

```bash
python -m strategy_template_long_only_orb.run
```

Or run the engine smoke test:

```bash
python -m backtest_template.main
```

## Input Data

The loader expects Databento-style 1-minute OHLCV data with:

- `ts_event`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `symbol`

## Notes Before Publishing

- This repo should be initialized at the parent `trading_backtests/` level only if you want both folders in one repo.
- The `.gitignore` is set up to ignore all other sibling strategy folders and local artifacts.
- Review hardcoded local paths in runnable files before pushing if you want a cleaner public repo.

