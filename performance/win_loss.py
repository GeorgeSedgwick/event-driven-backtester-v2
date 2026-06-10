def display_win_loss(strategy_port):
    wins = even = losses = 0
    for id in strategy_port.id_list:
        if strategy_port.trades[id]['pnl'] is None:
            continue
        if strategy_port.trades[id]['pnl'] > 0:
            wins += 1
        elif strategy_port.trades[id]['pnl'] == 0:
            even += 1
        else:
            losses += 1
    print(f"Wins: {wins} | Losses: {losses} | Even: {even}")