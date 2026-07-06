# Trading Backtests

  This repository contains a reusable Python backtesting engine plus a public
  example strategy template.

  It is set up so the engine can be shared publicly while private strategy ideas
  stay outside the repo.

  ## Included

  - `backtest_template/`
    Shared engine for loading data, generating signals, simulating trades, and
    producing analytics.

  - `strategy_template_long_only_orb/`
    Example strategy folder showing how to build a strategy outside the engine
    package.

  ## Features

  - Databento-style 1-minute OHLCV CSV / CSV.zst support
  - Front-month continuous futures construction
  - Multi-timeframe backtesting workflow
  - Strategy interface built around `Signals`
  - Slippage, fees, cooldown, and time-stop handling
  - Equity curve, Monte Carlo, and R-distribution outputs

  ## Install

  ```bash
  pip install -r requirements.txt

  ## Run

  From the repo root:

  python -m strategy_template_long_only_orb.run

  You can also run the engine example directly:

  python -m backtest_template.main

  ## Expected Data Format

  Input data should contain:

  - ts_event
  - open
  - high
  - low
  - close
  - volume
  - symbol

  ## Example Results

  ### Equity Curve

  Equity Curve

  ### Monte Carlo

  Monte Carlo

  ### R Distribution

  R Distribution

  ## Repository Layout

  trading_backtests/
  ├── backtest_template/
  └── strategy_template_long_only_orb/

  ## Notes

  - This repo is the public subset of a larger private research workspace.
  - The engine is reusable across multiple strategy folders.
  - The included strategy folder is meant as a template, not a claim of
    production readiness.
