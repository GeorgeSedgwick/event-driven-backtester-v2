
import plotly.graph_objects as go
from datetime import datetime, timezone
import pandas as pd
import os
from performance import *

from core.engine import run_backtest
from strategies import BuyAndHoldStrategy, MomentumStrategy, MeanReversionStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

def compare_to_benchmark():
    start_date = datetime(2018, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constituents'

    valid_tickers = []
    tickers = get_snp500_tickers()
    valid_tickers = get_valid_tickers(tickers, csv_dir, start_date, end_date)

    valid_tickers = [x for x in valid_tickers if x != "SPY" and x != "^VIX"]
    valid_tickers = ["SPY"] + valid_tickers + ["^VIX"]


    bnh_port, _ = run_backtest(
        BuyAndHoldStrategy,
        ['SPY', '^VIX'],
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        track_dates=False
        )

    """strategy_port = run_backtest(
        MeanReversionStrategy,
        valid_tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        lookback=30,
        short_period=21,
        long_period=63,
        z_condition=2.0,
        z_exit_threshold=0.5,
        use_shorts=False,
        track_dates=False
        )"""
    
    strategy_port, regime_detector = run_backtest(
        MomentumStrategy,
        valid_tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        lookback=252,
        rebalance=42,
        top_n=5,
        use_shorts=False,
        track_dates=True
        )
    





    display_benchmark_results(bnh_port, strategy_port)
    display_win_loss(strategy_port)
    display_payoff_ratio(strategy_port)

    trades = get_trade_df(strategy_port)


    print(f"PnL Sum by Regime:\n{trades.groupby('regime')['pnl'].sum()}")
    print(f"\nMean PnL by Regime:\n{trades.groupby('regime')['pnl'].mean()}")





