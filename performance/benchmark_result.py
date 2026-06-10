import pandas as pd
def display_benchmark_results(bnh_port, strategy_port):
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