import pandas as pd
from performance import *

def get_regime_stats(trades):
    grouped = trades.groupby('regime')

    stats = pd.DataFrame({
        "total_return": grouped['return'].sum(),
        "mean_return": grouped['return'].mean(),
        "median_return": grouped['return'].median(),
        "std_return": grouped['return'].std(),
        "total_pnl": grouped['pnl'].sum(),
        "win_rate": grouped.apply(lambda x: (x["pnl"] > 0).mean()),
        "avg_holdding": grouped['holding_period'].mean(),
        "median_holding": grouped['holding_period'].median(),
        "trade_count": grouped.size(),
        "sharpe": grouped['return'].apply(create_sharpe_ratio)
    })

    return stats.sort_values("mean_return", ascending=False)