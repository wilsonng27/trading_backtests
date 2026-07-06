  # trading_backtests

  A lightweight Python backtesting workspace with:

  - `backtest_template/`: reusable backtest engine
  - `strategy_template_long_only_orb/`: example strategy template built on top
  of the engine

  This repo is structured so the engine and one public example strategy can be
  shared, while private strategy folders stay out of the repository.

  ## Structure

  ```text
  trading_backtests/
  ├── backtest_template/
  └── strategy_template_long_only_orb/

  ## What’s Included

  ### backtest_template/

  Core engine components:

  - data loading for Databento-style 1-minute OHLCV CSV / CSV.zst
  - front-month continuous contract building
  - OHLCV resampling for execution and regime timeframes
  - strategy interface via Signals
  - trade simulation with slippage, fees, cooldown, and time stop
  - analytics, bootstrap stats, Monte Carlo analysis, and plots

  ### strategy_template_long_only_orb/

  A public example/template strategy that shows how to:

  - keep strategy logic outside the engine
  - implement build_signals(df_exec, df_regime)
  - configure a standalone run.py
  - generate output artifacts such as equity curve, Monte Carlo, and R-
    distribution charts

  ## Installation

  Python 3.12+ recommended.

  pip install -r requirements.txt

  ## Run

  From the repo root:

  python -m strategy_template_long_only_orb.run

  You can also run the engine smoke test:

  python -m backtest_template.main

  ## Input Data

  The loader expects Databento-style 1-minute OHLCV data with these columns:

  - ts_event
  - open
  - high
  - low
  - close
  - volume
  - symbol

  ## Example Result

  Below is an example result from the public template strategy.

  ### Equity Curve

  Equity Curve

  ### Monte Carlo

  Monte Carlo

  ### R Distribution

  R Distribution

  ## Notes

  - This public repo includes only backtest_template/ and
    strategy_template_long_only_orb/.

  - Private strategies, local datasets, caches, and most generated artifacts are
    intentionally excluded.

  - The example strategy is meant as a template for building new strategies on
    top of the shared engine.
