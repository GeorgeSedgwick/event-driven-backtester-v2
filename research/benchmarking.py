
from datetime import datetime, timezone, date
import pandas as pd
from performance import *
 
from research.spy_test import run_spy_test
from research.nasdaq_test import run_nq_test

from models.rtn_reg import run_return_regression

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def compare_to_benchmark():
# ================================================================
# =                                                              =
# =                                                              =    
    config = {
        'strategy': 'mom',
        'start': datetime(2005, 1, 1, tzinfo=timezone.utc),
        'end': datetime(2026, 10, 18, tzinfo=timezone.utc),
        'capital': 100000,
        'market': 'SPX',
        'regime_model': "gaussian"
    }                                       
# =                                                              =
# =                                                              =
# ================================================================


















    if config.get('market') == 'SPX':
        bnh_port, strategy_port = run_spy_test(config)

    elif config.get('market') == 'NQ':
        bnh_port, strategy_port = run_nq_test(config)

    

    #run_return_regression(bnh_port.equity_curve, strategy_port.equity_curve)
    #TODO: FIX REGRESSION 
    

    display_benchmark_results(bnh_port, strategy_port, config.get('start'), config.get('end'))
    display_benchmark_curve(bnh_port, strategy_port, display_graph=True)

    trades_df = get_trade_df(strategy_port)
    print(trades_df.sort_values('entry_datetime', ascending=True))
    print(len(trades_df))

    regime_df = get_regime_stats(trades_df)
    print(regime_df)

    #store_backtest("Simple_Momentum", config.get("start"), config.get("end"), strategy_port, trades_df)
    sql_df = read_from_database()
    #print(sql_df)




