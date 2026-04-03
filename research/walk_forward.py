import pandas as pd
from datetime import datetime, timezone
from core.engine import run_backtest
from strategies import MomentumStrategy
from utils.data_fetch import get_snp500_tickers, get_valid_tickers

"""

    A -> Train
    B -> Test
    A+B -> Train
    C -> Test
    A+B+C -> Train
    D -> Test

"""


def evaluate_lookbacks(strategy, tickers, start, end, lookback_values, initial_capital):
   
    results = {}

    best_sharpe = None
    best_lookback = None

    for lb in lookback_values:
        port = run_backtest(
            strategy,
            tickers,
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
            lookback=lb,
            use_shorts=False
        )

        stats = port.output_summary_stats()
        sharpe = stats['sharpe']

        results[lb] = port

        print(f"Lookback: {lb} | Sharpe: {sharpe:.2f}")

        if best_sharpe is None or sharpe > best_sharpe:
            best_sharpe = sharpe
            best_lookback = lb

    return best_lookback, best_sharpe, results


period_A_start, period_A_end = datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2021, 1, 1, tzinfo=timezone.utc)
period_B_start, period_B_end = datetime(2021, 1, 1, tzinfo=timezone.utc), datetime(2022, 1, 1, tzinfo=timezone.utc)
period_C_start, period_C_end = datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2023, 1, 1, tzinfo=timezone.utc)
period_D_start, period_D_end = datetime(2023, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 1, tzinfo=timezone.utc)

periods = [
    ("A", period_A_start, period_A_end),
    ("B", period_B_start, period_B_end),
    ("C", period_C_start, period_C_end),
    ("D", period_D_start, period_D_end),
]

def run_walk_forward():
    lookback_values = [20, 63, 126, 252, 378]
    initial_capital = 100000

    strategy = MomentumStrategy
    tickers = get_snp500_tickers()
    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents'

    print("\n===== START WALK FORWARD =====")

    for i in range(1, len(periods)):
        train_name = periods[i - 1][0]
        train_start = periods[0][1]
        train_end = periods[i - 1][2]

        test_name = periods[i][0]
        test_start = periods[i][1]
        test_end = periods[i][2]


        
        print(f"\n======= TRAIN A -> {train_name} ========")
        # Begin training, get valid tickers for train period
        train_tickers = get_valid_tickers(
            tickers,
            csv_dir,
            start_date=train_start,
            end_date=train_end
        )

        best_lookback, best_sharpe, _ = evaluate_lookbacks(
            strategy,
            train_tickers,
            train_start,
            train_end,
            lookback_values,
            initial_capital
        )

        print(f"Best lookback: {best_lookback} | Train Sharpe: {best_sharpe:.2f}")


        print(f"\n====== TEST {test_name} ======")
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
            lookback=best_lookback,
            use_shorts=False
        )

        test_stats = test_port.output_summary_stats()
        test_sharpe = test_stats['sharpe']
        print(f"Test Sharpe: {test_sharpe:.2f}")
