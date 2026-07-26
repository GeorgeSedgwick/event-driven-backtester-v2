from core.engine import run_backtest
from strategies import MomentumStrategy, BuyAndHoldStrategy, StatArbStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers, get_nq100_tickers
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
    tickers = get_nq100_tickers()
    valid_tickers = get_valid_tickers(tickers, csv_dir, start_date, end_date)
    if "^VXN" not in valid_tickers:
        valid_tickers.append("^VXN")
    if "QQQ" not in valid_tickers:
        valid_tickers.insert(0, "QQQ")
    return valid_tickers


def evaluate_params(strategy, tickers, start_date, end_date, initial_capital, param_grid, use_stops, use_shorts, track_dates):
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
                            #n_pairs=params.get('n_pairs'),
                            top_n=params.get('top_n', 5),
                            use_stops=use_stops,
                            use_shorts=use_shorts,
                            track_dates=track_dates
                            )
    
        
        sharpe = float(round(train_port.output_summary_stats()['sharpe'], 2))
        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params
        
    #print(f'Best Sharpe: {best_sharpe} | Params: {best_params}')
    
    return best_sharpe, best_params, regime_detector


def test_params(strategy, tickers, start_date, end_date, initial_capital, test_params, use_stops, use_shorts, track_dates, regime_detector):
    test_port, regime_detector = run_backtest(
        strategy,
        tickers,
        start_date,
        end_date,
        initial_capital,
        lookback=test_params.get('lookback',126),
        rebalance=test_params.get('rebalance', 8),
        top_n=test_params.get('top_n', 5),
        #n_pairs=test_params.get('n_pairs', 5),
        use_stops=use_stops,
        use_shorts=use_shorts,
        track_dates=track_dates,
        regime_detector=regime_detector
    )

    sharpe = float(round(test_port.output_summary_stats()['sharpe'], 2))
    if strategy == BuyAndHoldStrategy:
        #print(f"BnH Sharpe: {sharpe}")
        #print(f"BnH Drawdown: {round(test_port.output_summary_stats()['max_drawdown'], 2)}%")
        max_dd = round(test_port.output_summary_stats()['max_drawdown'], 2)
    else:
        #print(f"Strategy Sharpe: {sharpe}")
        #print(f"Strategy Drawdown: {round(test_port.output_summary_stats()['max_drawdown'], 2)}%")
        max_dd = round(test_port.output_summary_stats()['max_drawdown'], 2)
    test_port.create_equity_curve_dataframe()
    #trade_list.append(test_port.trades)

    return sharpe, max_dd, test_port.equity_curve['equity_curve'], test_port


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
        "A": {'Sharpe': None, 'Max_DD': None, 'Total_Rtn': None},
        "B": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "C": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "D": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "E": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "F": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "G": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0}
    }

    bnh_results = {
        "A": {'Sharpe': None, 'Max_DD': None, 'Total_Rtn': None},
        "B": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "C": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "D": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "E": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "F": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0},
        "G": {'Sharpe': 0, 'Max_DD': 0, 'Total_Rtn': 0}
    }

    a_start, a_end = datetime(2005, 1, 1, tzinfo=timezone.utc), datetime(2007, 12, 31, tzinfo=timezone.utc)
    b_start, b_end = datetime(2008, 1, 1, tzinfo=timezone.utc), datetime(2010, 12, 31, tzinfo=timezone.utc)
    c_start, c_end = datetime(2011, 1, 1, tzinfo=timezone.utc), datetime(2013, 12, 31, tzinfo=timezone.utc)
    d_start, d_end = datetime(2014, 1, 1, tzinfo=timezone.utc), datetime(2016, 12, 31, tzinfo=timezone.utc)
    e_start, e_end = datetime(2017, 1, 1, tzinfo=timezone.utc), datetime(2019, 12, 31, tzinfo=timezone.utc)
    f_start, f_end = datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2022, 12, 31, tzinfo=timezone.utc)
    g_start, g_end = datetime(2023, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)


    periods = [
        ('A', a_start, a_end),
        ('B', b_start, b_end),
        ('C', c_start, c_end),
        ('D', d_start, d_end),
        ('E', e_start, e_end),
        ('F', f_start, f_end),
        ('G', g_start, g_end)
    ]

    for i in range(len(periods) - 1):
        print(f"TRAINING ON PERIOD A to {periods[i][0]}")
        csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/nasdaq_constituents'
        train_start_date = periods[0][1]
        train_end_date = periods[i][2]
        strategy = MomentumStrategy
        tickers = get_ticker_list(csv_dir, train_start_date, train_end_date)
        initial_capital = 100000

        param_grid = {
            'lookback': [126],
            'rebalance': [8],
            'top_n': [5]
           # 'n_pairs': [5]
        }

        best_sharpe, best_params, regime_detector = evaluate_params(
            strategy, 
            tickers, 
            train_start_date, 
            train_end_date,
            initial_capital, 
            param_grid,
            use_stops=True,
            use_shorts=False,
            track_dates=False)
        
        if best_params != None:
            print(best_params)
        
        print(f"TESTING ON PERIOD {periods[i+1][0]}")

        test_start_date = periods[i+1][1]
        test_end_date = periods[i+1][2]

        strategy = MomentumStrategy
        tickers = get_ticker_list(csv_dir, test_start_date, test_end_date)

        test_sharpe, test_dd, test_eq_curve, test_port = test_params(
        strategy,
        tickers,
        test_start_date,
        test_end_date,
        initial_capital,
        test_params=best_params,
        use_stops=True,
        use_shorts=False,
        track_dates=False,
        regime_detector=regime_detector)



        """            strategy,
            tickers,
            test_start_date,
            test_end_date,
            initial_capital,
            best_params,
            use_stops=True,
            use_shorts=False,
            track_dates=False,
            regime_detector=regime_detector)"""
        

        strategy = BuyAndHoldStrategy
        bnh_sharpe, bnh_dd, bnh_eq_curve, bnh_port = test_params(
            strategy,
            ['QQQ', '^VXN'],
            test_start_date,
            test_end_date,
            initial_capital,
            best_params,
            use_stops=False,
            use_shorts=False,
            track_dates=False,
            regime_detector=None
        )

        


        results[periods[i+1][0]]['Sharpe'] = test_sharpe
        results[periods[i+1][0]]['Max_DD'] = test_dd
        results[periods[i+1][0]]['Total_Rtn'] = test_port.output_summary_stats()['total_return']
        bnh_results[periods[i+1][0]]['Sharpe'] = bnh_sharpe
        bnh_results[periods[i+1][0]]['Max_DD'] = bnh_dd
        bnh_results[periods[i+1][0]]['Total_Rtn'] = bnh_port.output_summary_stats()['total_return']

        test_eq_curves.append(test_eq_curve)
        bnh_eq_curves.append(bnh_eq_curve)

        test_trades_df = pd.DataFrame.from_dict(test_port.trades, orient="index")
        test_trades_df.index.name = "trade_id"
        trade_list.append(test_trades_df)

        



    comb_trades = concat_trades_dicts(trade_list)
    comb_eq = get_combined_eq_curve(test_eq_curves, initial_capital)
    bnh_comb_eq = get_combined_eq_curve(bnh_eq_curves, initial_capital)
    display_walkforward_curve(comb_eq, bnh_comb_eq, display_curve=True)
    #print(comb_trades)
    #regime_df = get_regime_stats(comb_trades)
    #print(regime_df)


    for i in range(min(len(results), len(bnh_results)) - 1):
        print(f"\n===== TEST PERIOD: {periods[i+1][0]} ====")
        print(f"Strategy | Sharpe: {results[periods[i+1][0]]['Sharpe']} | Max DD: {results[periods[i+1][0]]['Max_DD']} | Total Return: {results[periods[i+1][0]]['Total_Rtn']}")
        print(f"BnH      | Sharpe: {bnh_results[periods[i+1][0]]['Sharpe']} | Max DD: {bnh_results[periods[i+1][0]]['Max_DD']} | Total Return: {bnh_results[periods[i+1][0]]['Total_Rtn']}\n")

    

    regime_df = get_regime_stats(comb_trades)
    print(regime_df)
