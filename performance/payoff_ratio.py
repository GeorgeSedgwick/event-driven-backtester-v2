import numpy as np

def display_payoff_ratio(strategy_port):
    trade_pnl_wins = []
    trade_pnl_losses = []

    for id in strategy_port.id_list:
        pnl = strategy_port.trades[id]['pnl']
        if pnl is None:
            continue
        if pnl > 0:
            trade_pnl_wins.append(pnl)
        elif pnl < 0:
            trade_pnl_losses.append(pnl)
        else:
            continue

    if len(trade_pnl_losses) > 0:
        payoff_ratio = np.mean(trade_pnl_wins) / abs(np.mean(trade_pnl_losses))
    else:
        payoff_ratio = float('inf')
    
    print(f"Avg Win / Avg Loss: {payoff_ratio:.2f}")


    avg_win = np.mean(trade_pnl_wins)
    avg_loss = abs(np.mean(trade_pnl_losses))

    win_rate = len(trade_pnl_wins) / (len(trade_pnl_wins) + len(trade_pnl_losses))
    loss_rate = len(trade_pnl_losses) / (len(trade_pnl_wins) + len(trade_pnl_losses))

    if len(trade_pnl_losses) > 0:
        ev = (win_rate * avg_win) - (loss_rate * avg_loss)
    else:
        ev = float('inf')
    
    print(f"Expected Value: {ev:.2f}")