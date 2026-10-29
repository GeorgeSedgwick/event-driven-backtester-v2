from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np
from datetime import date

from utils.data_fetch import get_daily_rf

"""
This function is used to regress the returns of the strategy onto the returns of the market, to understand better whether the 
strategy is actually generating returns on its own, or if it requires the market in order to generate returns.

"""

def run_return_regression(bnh_eq_curve, strategy_eq_curve):


    
    returns_df = pd.DataFrame({
        "BnH_Returns": bnh_eq_curve['returns'], 
        "Strategy_Returns": strategy_eq_curve['returns']}).reindex(strategy_eq_curve.index)



    rf = get_daily_rf(start=returns_df.index.min(), end=returns_df.index.max())

    print(returns_df.index[:5])
    print(rf.index[:5])

    returns_df['rf_Daily'] = rf

   # print(returns_df['rf_Daily'])
    



    returns_df['BnH_Excess'] = returns_df['BnH_Returns'] - rf
    returns_df['Strategy_Excess'] = returns_df['Strategy_Returns'] - rf


    returns_df = returns_df.dropna()

    #print(returns_df['BnH_Excess'].tail())




    X = returns_df[['BnH_Excess']]
    y = returns_df['Strategy_Excess']


    model = LinearRegression().fit(X, y)


    print(model.coef_)

    

    



    
