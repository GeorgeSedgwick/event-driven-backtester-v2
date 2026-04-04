# Event-Driven Backtester

A research-grade event-driven backtesting framework built from scratch in Python.

## Strategy
Best strategy tested is Momentum strategy across the S&P 500 universe using regime filtering (BULL/BEAR/FLAT) and monthly rebalancing.

## Momentum Results (2021-2026)
- Total Return: 465%
- Sharpe Ratio: 1.43
- Max Drawdown: 26%

## Architecture
- Market -> Signal -> Order -> Fill event pipeline
- T+1 FIFO execution to eliminate lookahead bias
- Custom OrderManagement class for capital reservation
- Walk-forward analysis for out-of-sample validation
