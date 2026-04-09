import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import sqlite3

def create_sharpe_ratio(returns, periods=252):
    """
    Create a sharpe ratio for the given number of periods 
    As the backtester is currently using daily data, this is set to 252
    (the number of trading days in US)
    
    """
    returns = np.array(returns)
    std = np.std(returns)
    mean = np.mean(returns)

    if std == 0 or pd.isna(std):
        return 0.0
    return np.sqrt(periods) * mean / std


def create_drawdowns(equity_curve):
    equity_curve = equity_curve.dropna()
    
    hwm = [equity_curve.iloc[0]]
    eq_idx = equity_curve.index
    drawdown = pd.Series(index = eq_idx, dtype=float)
    duration = pd.Series(index = eq_idx, dtype=float)

    drawdown.iloc[0] = 0.0
    duration.iloc[0] = 0.0

    for t in range(1, len(eq_idx)):
        cur_hwm = max(hwm[t-1], equity_curve.iloc[t])
        hwm.append(cur_hwm)
        drawdown.iloc[t] = (cur_hwm - equity_curve.iloc[t]) / cur_hwm * 100
        duration.iloc[t] = 0 if drawdown.iloc[t] == 0 else duration.iloc[t-1] + 1
    return drawdown.max(), duration.max()


def create_price_chart(asset, dates, prices, trades):
    long_entry_dates, long_exit_dates = [], []
    short_entry_dates, short_exit_dates = [], []
    long_entry_prices, long_exit_prices = [], []
    short_entry_prices, short_exit_prices = [], []

    for i in range(len(trades)):
        if trades[i]['direction'] == 'long':
            long_entry_dates.append(trades[i]['entry_datetime'])
            long_exit_dates.append(trades[i]['exit_datetime'])
            long_entry_prices.append(trades[i]['entry_price'])
            long_exit_prices.append(trades[i]['exit_price'])
        
        elif trades[i]['direction'] == 'short':
            short_entry_dates.append(trades[i]['entry_datetime'])
            short_exit_dates.append(trades[i]['exit_datetime'])
            short_entry_prices.append(trades[i]['entry_price'])
            short_exit_prices.append(trades[i]['exit_price'])

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=asset
    ))

    fig2.add_trace(go.Scatter(
        x=long_entry_dates,
        y=long_entry_prices,
        mode='markers',
        name='Long Buy',
        marker=dict(color='green', size=10, symbol='triangle-up')
    ))

    fig2.add_trace(go.Scatter(
        x=long_exit_dates,
        y=long_exit_prices,
        mode='markers',
        name='Long Exit',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ))

    fig2.add_trace(go.Scatter(
        x=short_entry_dates,
        y=short_entry_prices,
        mode='markers',
        name='Short Sell',
        marker=dict(color='red', size=10, symbol='triangle-down')
    
    ))

    fig2.add_trace(go.Scatter(
        x=short_exit_dates,
        y=short_exit_prices,
        mode='markers',
        name='Short Cover',
        marker=dict(color='green', size=10, symbol='triangle-up')
    ))

    fig2.show()
    

def display_win_ratio(wins, losses):
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Ratio: {wins / (wins + losses) if (wins + losses) > 0 else 0:.2f}")
    #print(f"Win/Loss Ratio: {(wins / losses) if losses > 0 else wins}")


def display_payoff_ratio(trades):
    trade_pnl_wins = []
    trade_pnl_losses = []

    for trade in trades:
        pnl = trade.get('pnl')
        if pnl is None:
            continue
        if pnl > 0:
            trade_pnl_wins.append(pnl)
        elif pnl < 0:
            trade_pnl_losses.append(pnl)
        else:
            continue

    if len(trade_pnl_losses) > 0:
        payoff_ratio = np.mean(trade_pnl_wins) / abs(np.mean(trade_pnl_losses))
    else:
        payoff_ratio = float('inf')
    
    print(f"Avg Win / Avg Loss: {payoff_ratio:.2f}")


def display_walkforward_curve(combined_equity_curve):
    """
    Reveives a combined equity curve (Pandas Series) and creates a graph.
    """
    fig = go.Figure()
    fig = fig.add_trace(go.Scatter(x=combined_equity_curve.index,
                                    y=combined_equity_curve,
                                    name=f""))
    
    fig.update_layout(title_text=f"S&P 500 Universe 2018 - 2026 | Combined equity curve")
    fig.update_layout(legend_title="Strategy")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Portfolio Value")

    fig.show()



def create_sql_database():
    con = sqlite3.connect("tutorial.db")

    pass