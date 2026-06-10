from core.engine import run_backtest
from strategies import MomentumStrategy, BuyAndHoldStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers
from performance import *
import pandas as pd
from datetime import datetime, timezone
import itertools

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

def concat_trades_dicts(trade_list):
    comb_trade_df = pd.concat(trade_list, ignore_index=False)
    comb_trade_df.index.name = "trade_id"
    return comb_trade_df
    




def get_ticker_list(csv_dir, start_date, end_date):
    tickers = get_snp500_tickers()
    valid_tickers = get_valid_tickers(tickers, csv_dir, start_date, end_date)
    return valid_tickers


def evaluate_params(strategy, tickers, start_date, end_date, initial_capital, param_grid, track_dates):
    best_sharpe = None
    best_params = None

    keys = list(param_grid.keys())
    combinations = list(itertools.product(*param_grid.values()))
    
    for c in combinations:
        params = dict(zip(keys, c))

        train_port, regime_detector = run_backtest(
                            strategy,
                            tickers,
                            start_date,
                            end_date,
                            initial_capital,
                            lookback=params.get('lookback', 252),
                            rebalance=params.get('rebalance', 21),
                            top_n=params.get('top_n', 10),
                            track_dates=track_dates
                            )
    
        
        sharpe = float(round(train_port.output_summary_stats()['sharpe'], 2))
        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params
        
    #print(f'Best Sharpe: {best_sharpe} | Params: {best_params}')
    
    return best_sharpe, best_params, regime_detector


def test_params(strategy, tickers, start_date, end_date, initial_capital, test_params, track_dates, regime_detector):
    test_port, regime_detector = run_backtest(
        strategy,
        tickers,
        start_date,
        end_date,
        initial_capital,
        lookback=test_params.get('lookback', 252),
        rebalance=test_params.get('rebalance', 21),
        top_n=test_params.get('top_n', 10),
        track_dates=track_dates,
        regime_detector=regime_detector
    )

    sharpe = float(round(test_port.output_summary_stats()['sharpe'], 2))
    if strategy == BuyAndHoldStrategy:
        print(f"BuyAndHold Sharpe: {sharpe}")
    else:
        print(f"Test Sharpe: {sharpe}")
    test_port.create_equity_curve_dataframe()
    #trade_list.append(test_port.trades)

    return sharpe, test_port.equity_curve['equity_curve'], test_port


def get_combined_eq_curve(eq_curves, initial_capital):
    adj_curves = []
    multiplier = float(0)
    for i in range(len(eq_curves)):
        if i == 0:
            eq_curves[i] = eq_curves[i] * initial_capital
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
    test_eq_curves, bnh_eq_curves = [], []
    trade_list = []

    results = {
        "A": None,
        "B": 0,
        "C": 0,
        "D": 0,
        "E": 0,
        "F": 0
    }

    bnh_results = {
        "A": None,
        "B": 0,
        "C": 0,
        "D": 0,
        "E": 0,
        "F": 0
    }

    a_start, a_end = datetime(2006, 1, 1, tzinfo=timezone.utc), datetime(2008, 12, 31, tzinfo=timezone.utc)
    b_start, b_end = datetime(2009, 1, 1, tzinfo=timezone.utc), datetime(2011, 12, 31, tzinfo=timezone.utc)
    c_start, c_end = datetime(2012, 1, 1, tzinfo=timezone.utc), datetime(2014, 12, 31, tzinfo=timezone.utc)
    d_start, d_end = datetime(2015, 1, 1, tzinfo=timezone.utc), datetime(2017, 12, 31, tzinfo=timezone.utc)
    e_start, e_end = datetime(2018, 1, 1, tzinfo=timezone.utc), datetime(2020, 12, 31, tzinfo=timezone.utc)
    f_start, f_end = datetime(2021, 1, 1, tzinfo=timezone.utc), datetime(2023, 12, 31, tzinfo=timezone.utc)

    periods = [
        ('A', a_start, a_end),
        ('B', b_start, b_end),
        ('C', c_start, c_end),
        ('D', d_start, d_end),
        ('E', e_start, e_end),
        ('F', f_start, f_end)
    ]

    for i in range(len(periods) - 1):
        print(f"TRAINING ON PERIOD A to {periods[i][0]}")
        csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constituents'
        train_start_date = periods[0][1]
        train_end_date = periods[i][2]
        strategy = MomentumStrategy
        tickers = get_ticker_list(csv_dir, train_start_date, train_end_date)
        initial_capital = 100000

        param_grid = {
            'lookback': [128],
            'rebalance': [21],
            'top_n': [10]
        }

        best_sharpe, best_params, regime_detector = evaluate_params(
            strategy, 
            tickers, 
            train_start_date, 
            train_end_date,
            initial_capital, 
            param_grid, 
            track_dates=False)
        
        
        print(f"TESTING ON PERIOD {periods[i+1][0]}")

        test_start_date = periods[i+1][1]
        test_end_date = periods[i+1][2]
        strategy = MomentumStrategy
        tickers = get_ticker_list(csv_dir, test_start_date, test_end_date)
        test_sharpe, test_eq_curve, test_port = test_params(
            strategy,
            tickers,
            test_start_date,
            test_end_date,
            initial_capital,
            best_params,
            track_dates=True,
            regime_detector=regime_detector
        )

        strategy = BuyAndHoldStrategy
        bnh_sharpe, bnh_eq_curve, bnh_port = test_params(
            strategy,
            ['SPY', '^VIX'],
            test_start_date,
            test_end_date,
            initial_capital,
            best_params,
            track_dates=False,
            regime_detector=None
        )

        results[periods[i+1][0]] = test_sharpe
        bnh_results[periods[i+1][0]] = bnh_sharpe

        test_eq_curves.append(test_eq_curve)
        bnh_eq_curves.append(bnh_eq_curve)

        test_trades_df = pd.DataFrame.from_dict(test_port.trades, orient="index")
        test_trades_df.index.name = "trade_id"
        trade_list.append(test_trades_df)

        

    print(f'Strategy results: {results}')
    print(f'BNH results: {bnh_results}')
    comb_trades = concat_trades_dicts(trade_list)
    print(comb_trades)
    comb_eq = get_combined_eq_curve(test_eq_curves, initial_capital)
    bnh_comb_eq = get_combined_eq_curve(bnh_eq_curves, initial_capital)
    display_walkforward_curve(comb_eq, bnh_comb_eq)

