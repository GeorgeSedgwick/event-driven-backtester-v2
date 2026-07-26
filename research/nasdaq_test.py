
import pandas as pd
from performance import *

from core.engine import run_backtest
from strategies import BuyAndHoldStrategy, MomentumStrategy, StatArbStrategy
from utils.data_fetch import get_nq100_tickers, get_valid_tickers
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def run_nq_test(config):
    csv_dir = '/Users/george/python-projects/ed-backtest/backtester/data/nasdaq_constituents'
    tickers = get_nq100_tickers()

    valid_tickers = get_valid_tickers(tickers, csv_dir, config.get('start'), config.get('end'))
    valid_tickers = ["QQQ"] + valid_tickers + ["^VXN"]
    
    if "Mom" in config.get('strategy') or "mom" in config.get('strategy'):
        bnh_port, _ = run_backtest(
            BuyAndHoldStrategy,
            ['QQQ', '^VXN'],
            start_date=config.get('start'),
            end_date=config.get('end'),
            initial_capital=config.get('capital'),
            use_stops=False,
            track_dates=False,
            market='QQQ',
            iv_idx='^VXN'
            )

        strategy_port, regime_detector = run_backtest(
                MomentumStrategy,
                valid_tickers,
                start_date=config.get('start'),
                end_date=config.get('end'),
                initial_capital=config.get('capital'),
                lookback=126,
                rebalance=10,
                top_n=5,
                use_shorts=False,
                use_stops=False,
                track_dates=False,
                market='QQQ',
                iv_idx='^VXN'
            )
        
        return bnh_port, strategy_port

    elif config.get('strategy') == 'StatArb':

        bnh_port, _ = run_backtest(
            BuyAndHoldStrategy,
            ['QQQ', '^VXN'],
            start_date=config.get('start'),
            end_date=config.get('end'),
            initial_capital=config.get('capital'),
            use_stops=False,
            track_dates=False,
            market='QQQ',
            iv_idx='^VXN'
            )
    
        
        strategy_port, regime_detector = run_backtest(
            StatArbStrategy,
            valid_tickers,
            start_date=config.get('start'),
            end_date=config.get('end'),
            initial_capital=config.get('capital'),
            lookback=252,
            rebalance=21,
            n_pairs=5,
            use_stops=False,
            track_dates=False,
            market='QQQ',
            iv_idx='^VXN'
        )
    
        return bnh_port, strategy_port