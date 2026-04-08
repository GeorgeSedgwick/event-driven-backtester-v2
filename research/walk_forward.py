import pandas as pd
from datetime import datetime, timezone
from core.engine import run_backtest
from strategies import MomentumStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers
import plotly.graph_objects as go
from research import performance as pf
pd.options.display.max_rows
import itertools


"""

    A -> Train
    B -> Test
    A+B -> Train
    C -> Test
    A+B+C -> Train
    D -> Test

"""

def evaluate_parameters(strategy, tickers, start, end, param_grid, initial_capital):

    best_sharpe = None
    best_params = None

    keys = list(param_grid.keys())
    combinations = list(itertools.product(*param_grid.values()))

    for comb in combinations:
        params = dict(zip(keys, comb))

        port = run_backtest(
            strategy,
            tickers,
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
            lookback=params.get('rebalance', 252),
            rebalance=params.get('rebalance', 21),
            use_shorts=False,
            track_dates=False
        )

        stats = port.output_summary_stats()
        sharpe = stats['sharpe']
        print(f"Params {params} | Sharpe: {sharpe:.2f}")

        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params

    return best_params, best_sharpe


period_A_start, period_A_end = datetime(2018, 1, 1, tzinfo=timezone.utc), datetime(2020, 1, 1, tzinfo=timezone.utc)
period_B_start, period_B_end = datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2022, 1, 1, tzinfo=timezone.utc)
period_C_start, period_C_end = datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 1, tzinfo=timezone.utc)
period_D_start, period_D_end = datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 1, tzinfo=timezone.utc)

periods = [
    ("A", period_A_start, period_A_end),
    ("B", period_B_start, period_B_end),
    ("C", period_C_start, period_C_end),
    ("D", period_D_start, period_D_end),
]

def run_walk_forward():
    base_curves = []

    param_grid = {
        'lookback': [252],
        'rebalance': [5, 21, 36, 48]
    }

    initial_capital = 100000
    strategy = MomentumStrategy
    tickers = get_snp500_tickers()
    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents'
    train_name = "TRAIN A"

    print("\n===== START WALK FORWARD =====")
    for i in range(1, len(periods)):
        train_start = periods[i-1][1]
        train_end = periods[i - 1][2]

        test_name = periods[i][0]
        test_start = periods[i][1]
        test_end = periods[i][2]

        print(f"\n======= {train_name} ========")
        print(f"Train start: {train_start} | Train end: {train_end}")

        # Begin training, get valid tickers for train period
        train_tickers = get_valid_tickers(
            tickers,
            csv_dir,
            start_date=train_start,
            end_date=train_end
        )

        best_params, best_sharpe= evaluate_parameters(
            strategy,
            train_tickers,
            train_start,
            train_end,
            param_grid,
            initial_capital
        )


        train_name = " + ".join([train_name, str(periods[i][0])])


        print(f"Best Params: {best_params} | Train Sharpe: {best_sharpe:.2f}")




        print(f"\n====== TEST {test_name} ======")
        print(f"Test start: {test_start} | Test end: {test_end}")
        # Begin testing, get valid tickers for test period
        test_tickers = get_valid_tickers(
            tickers,
            csv_dir,
            start_date=test_start,
            end_date=test_end
        )

        test_port = run_backtest(
            strategy,
            test_tickers,
            start_date=test_start,
            end_date=test_end,
            initial_capital=initial_capital,
            lookback=best_params['lookback'],
            rebalance=best_params['rebalance'],
            use_shorts=False,
            track_dates=False
        )

        test_stats = test_port.output_summary_stats()
        test_sharpe = test_stats['sharpe']
        print(f"Test Sharpe: {test_sharpe:.2f}")

        test_port.create_equity_curve_dataframe()

    
        base_curves.append(test_port.equity_curve["equity_curve"])

    adj_curves = []
    multiplier = float(0)
    for i in range(len(base_curves)):

        if i == 0:
            adj_curves.append(base_curves[i])
            multiplier = base_curves[i].iloc[-1]
            continue
        else:
            temp = base_curves[i] * multiplier
            adj_curves.append(temp)
            multiplier = temp.iloc[-1]



    comb_eq = pd.concat(adj_curves).sort_index()

    pf.display_walkforward_curve(comb_eq)

    
