
import plotly.graph_objects as go
from datetime import datetime, timezone
import pandas as pd
import os
from research import performance as pf

from core.engine import run_backtest
from strategies import BuyAndHoldStrategy, MomentumStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers


def compare_to_benchmark():
    start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents'

    valid_tickers = []
    tickers = get_snp500_tickers()
    valid_tickers = get_valid_tickers(tickers, csv_dir ,start_date, end_date)
    valid_tickers.append("SPY")

    for file in os.listdir(csv_dir):
        df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=['Date'])

    bnh_port = run_backtest(
        BuyAndHoldStrategy,
        ['SPY'],
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        lookback=None,
        use_shorts=False
        )

    strategy_port = run_backtest(
        MomentumStrategy,
        valid_tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        lookback=252,
        use_shorts=True
        )
    
    # INITIAL TEST DATES:
    # start_date=datetime(2020, 1, 2, tzinfo=timezone.utc),
    # end_date=datetime(2023, 12, 29, tzinfo=timezone.utc)
    
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

# ======= PLOT PRICE CHART ========

    #all_bars = strategy_port.bars.get_all_bars(asset)
    #dates = all_bars.index.values
    #prices = all_bars['close'].values

    trades, wins, losses, breakeven = strategy_port.get_trade_points()
    
    df = pd.DataFrame(trades)
    print(f"\n\n========= ALL TRADES =========")
    print(df.to_string())
    print(f"Trade count: {len(trades)}")
    
    pf.display_win_ratio(wins, losses)
    pf.display_payoff_ratio(trades)
    #pf.create_price_chart(asset, dates, prices, trades) 

    print(f"TOTAL COMMISSION PAYED ON STRATEGY: {strategy_port.current_holdings['commission']}")


