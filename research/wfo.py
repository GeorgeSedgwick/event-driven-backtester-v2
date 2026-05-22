from core.engine import run_backtest
from strategies import MomentumStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers
from research import performance as pf
import pandas as pd
from datetime import datetime, timezone
import itertools




def get_ticker_list(start_date, end_date):
    tickers = get_snp500_tickers()
    valid_tickers = get_valid_tickers(tickers, "~/python-projects/ed-backtest/backtester/data/sp_constituents", start_date, end_date)
    return valid_tickers


def evaluate_params(strategy, tickers, start_date, end_date, param_grid, track_dates):
    best_sharpe = None
    best_params = None

    keys = list(param_grid.keys())
    combinations = list(itertools.product(*param_grid.values()))

    for c in combinations:
        params = dict(zip(keys, c))

        train_port = run_backtest(
                            strategy,
                            tickers,
                            start_date,
                            end_date,
                            100000,
                            lookback=params.get('lookback', 252),
                            rebalance=params.get('rebalance', 21),
                            top_n=params.get('top_n', 10),
                            track_dates=track_dates
                            )
        
        sharpe = float(round(train_port.output_summary_stats()['sharpe'], 2))
        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params
        
    print(f'Best Sharpe: {best_sharpe} | Params: {best_params}')
    
    return best_sharpe, best_params


def test_params(strategy, tickers, start_date, end_date, test_params, track_dates):
    
    test_port = run_backtest(
        strategy,
        tickers,
        start_date,
        end_date,
        100000,
        lookback=test_params.get('lookback', 252),
        rebalance=test_params.get('rebalance', 21),
        top_n=test_params.get('top_n', 10),
        track_dates=track_dates
    )

    sharpe = float(round(test_port.output_summary_stats()['sharpe'], 2))
    print(f"Test Sharpe: {sharpe}")
    test_port.create_equity_curve_dataframe()

    return sharpe, test_port.equity_curve['equity_curve']


def get_combined_eq_curve(eq_curves):
    adj_curves = []
    multiplier = float(0)
    for i in range(len(eq_curves)):
        if i == 0:
            adj_curves.append(eq_curves[i])
            multiplier = eq_curves[i].iloc[-1]
        else:
            temp = eq_curves[i] * multiplier
            adj_curves.append(temp)
            multiplier = temp.iloc[-1]
    
    return pd.concat(adj_curves)








def display_wfo_ui():
    print("======= WFO =======")


def run_wfo():
    display_wfo_ui()
    test_eq_curves = []

    results = {
        "A": None,
        "B": 0,
        "C": 0,
        "D": 0
    }

    a_start, a_end = datetime(2006, 1, 1, tzinfo=timezone.utc), datetime(2008, 12, 31, tzinfo=timezone.utc)
    b_start, b_end = datetime(2009, 1, 1, tzinfo=timezone.utc), datetime(2011, 12, 31, tzinfo=timezone.utc)
    c_start, c_end = datetime(2012, 1, 1, tzinfo=timezone.utc), datetime(2014, 12, 31, tzinfo=timezone.utc)
    d_start, d_end = datetime(2015, 1, 1, tzinfo=timezone.utc), datetime(2017, 12, 31, tzinfo=timezone.utc)

    periods = [
        ('A', a_start, a_end),
        ('B', b_start, b_end),
        ('C', c_start, c_end),
        ('D', d_start, d_end)
    ]

    for i in range(len(periods) - 1):
        print(f"TRAINING ON PERIOD A to {periods[i][0]}")

        train_start_date = periods[0][1]
        train_end_date = periods[i][2]
        strategy = MomentumStrategy
        tickers = get_ticker_list(train_start_date, train_end_date)

        param_grid = {
            'lookback': [252],
            'rebalance': [21],
            'top_n': [10]
        }

        best_sharpe, best_params = evaluate_params(
            strategy, 
            tickers, 
            train_start_date, 
            train_end_date, 
            param_grid, 
            track_dates=False)
        
        print(f"TESTING ON PERIOD {periods[i+1][0]}")

        test_start_date = periods[i+1][1]
        test_end_date = periods[i+1][2]
        strategy = MomentumStrategy
        tickers = get_ticker_list(test_start_date, test_end_date)

        test_sharpe, test_eq_curve = test_params(
            strategy,
            tickers,
            test_start_date,
            test_end_date,
            best_params,
            track_dates=False
        )

        results[periods[i+1][0]] = test_sharpe
        test_eq_curves.append(test_eq_curve)

        

    print(results)
    comb_eq = get_combined_eq_curve(test_eq_curves)
    pf.display_walkforward_curve(comb_eq)
    
