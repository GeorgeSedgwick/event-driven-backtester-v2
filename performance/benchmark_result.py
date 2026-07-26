import pandas as pd
from .payoff_ratio import display_payoff_ratio
from .win_loss import display_win_loss
def display_benchmark_results(bnh_port, strategy_port, start_date, end_date):
    print(f"\n\n---- Test Date | {start_date} : {end_date}----\n")
    print(f"\n---- Buy And Hold Strategy Results ----\n")
    print(f"Total Portfolio Value: ${bnh_port.current_holdings['total']:.2f}")
    stats = bnh_port.output_summary_stats()
    print(f"Total return: {stats['total_return']:.2f}%")
    print(f"Sharpe: {stats['sharpe']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2f}%")
    print(f"Drawdown duration: {stats['drawdown_duration']:.2f}\n\n")
   
    print("---- Momentum Strategy Results ----\n")
    print(f"Total Portfolio Value: ${strategy_port.current_holdings['total']:.2f}")
    stats = strategy_port.output_summary_stats()
    print(f"Total return: {stats['total_return']:.2f}%")
    print(f"Sharpe: {stats['sharpe']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2f}%")
    print(f"Drawdown duration: {stats['drawdown_duration']:.2f}")
    print(f"Total Commission: ${strategy_port.current_holdings['commission']:.2f}")
    print(f"Total Slippage: ${strategy_port.current_holdings['slippage']:.2f}")
    display_win_loss(strategy_port)
    display_payoff_ratio(strategy_port)
    print("\n\n")


    # EV = P(W) * R + P(L) * L