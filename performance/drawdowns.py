import pandas as pd

def create_drawdowns(equity_curve):
    equity_curve = equity_curve.dropna()
    
    hwm = [equity_curve.iloc[0]]
    eq_idx = equity_curve.index
    drawdown = pd.Series(index = eq_idx, dtype=float)
    duration = pd.Series(index = eq_idx, dtype=float)

    drawdown.iloc[0] = 0.0
    duration.iloc[0] = 0.0

    for t in range(1, len(eq_idx)):
        cur_hwm = max(hwm[t-1], equity_curve.iloc[t])
        hwm.append(cur_hwm)
        drawdown.iloc[t] = (cur_hwm - equity_curve.iloc[t]) / cur_hwm * 100
        duration.iloc[t] = 0 if drawdown.iloc[t] == 0 else duration.iloc[t-1] + 1
    return drawdown.max(), duration.max()