import numpy as np
import pandas as pd

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