
import plotly.graph_objects as go
from datetime import datetime, timezone
import pandas as pd
import os
from research import performance as pf

from core.engine import run_backtest
from strategies import BuyAndHoldStrategy, MomentumStrategy, MeanReversionStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

def compare_to_benchmark():
    start_date = datetime(2015, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents'

    valid_tickers = []
    tickers = get_snp500_tickers()
    valid_tickers = get_valid_tickers(tickers, csv_dir, start_date, end_date)
    if "SPY" in valid_tickers:
        valid_tickers.remove("SPY")
    valid_tickers.insert(0, "SPY")
    valid_tickers.append("^VIX")

    for file in os.listdir(csv_dir):
        df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=['Date'])

    bnh_port = run_backtest(
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
    
    strategy_port = run_backtest(
        MomentumStrategy,
        valid_tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        lookback=252,
        rebalance=42,
        top_n=5,
        use_shorts=False,
        track_dates=False
        )
    
    strategy_title = "Momentum" # FOR GRAPH (EDIT HERE)
    asset = 'S&P VS MOMENTUM (S&P UNIVERSE)' # USE TICKER TO PLOT PRICE (EDIT HERE)






    print(f"\n---- Buy And Hold Strategy Results ----\n")
    print(f"Total Portfolio Value: ${bnh_port.current_holdings['total']:.2f}")
    stats = bnh_port.output_summary_stats()
    print(f"Total return: {stats['total_return']:.2f}%")
    print(f"Sharpe: {stats['sharpe']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2f}%")
    print(f"Drawdown duration: {stats['drawdown_duration']:.2f}")
    print()
    print()
    print("---- Momentum Strategy Results ----\n")
    print(f"Total Portfolio Value: ${strategy_port.current_holdings['total']:.2f}")
    stats = strategy_port.output_summary_stats()
    print(f"Total return: {stats['total_return']:.2f}%")
    print(f"Sharpe: {stats['sharpe']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2f}%")
    print(f"Drawdown duration: {stats['drawdown_duration']:.2f}")

# ======= PLOT EQUITY CURVES =========
    strat_dfs = {"Buy and Hold": bnh_port.equity_curve, f"{strategy_title}": strategy_port.equity_curve}
    fig = go.Figure()
    for strategy in strat_dfs:
        fig = fig.add_trace(go.Scatter(x = strat_dfs[strategy].index,
                                       y = strat_dfs[strategy]["total"],
                                       name=strategy))
        
    fig.update_layout(title_text=asset)
    fig.update_layout(legend_title_text="Strategy")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Portfolio Value")

    fig.show()

    df_trades = pd.DataFrame.from_dict(strategy_port.trades, orient='index')
    df_trades.index.name = "trade_id"

    print(df_trades)
    print(f"Total Commission: ${strategy_port.current_holdings['commission']:.2f}")
    print(f"Total Slippage: ${strategy_port.current_holdings['slippage']:.2f}")



