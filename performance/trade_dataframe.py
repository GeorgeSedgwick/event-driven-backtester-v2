import pandas as pd

def get_trade_df(strategy_port):
    df_trades = pd.DataFrame.from_dict(strategy_port.trades, orient='index')
    df_trades.index.name = "trade_id"
    return df_trades