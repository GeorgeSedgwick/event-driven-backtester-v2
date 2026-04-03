from queue import Queue, Empty
from datetime import datetime

from data.datahandler import HistoricCSVDataHandler

from core.portfolio import NaivePortfolio
from core.execution import SimulatedExecutionHandler




def run_backtest(strategy_name, ticker_list, start_date, end_date, initial_capital, lookback, use_shorts):
    events = Queue()

    bars = HistoricCSVDataHandler(events, csv_dir='/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents', ticker_list=ticker_list, start_date=start_date, end_date=end_date, verbose=False)

    strategy = strategy_name(bars, events, lookback=lookback, use_shorts=use_shorts, verbose=False)

    port = NaivePortfolio(bars, events, start_date, initial_capital, verbose=True)
    
    broker = SimulatedExecutionHandler(events, bars, verbose=True)

    while True:
        if bars.continue_backtest:
            bars.update_bars()
        else:
            break


        while True:
            try:
                event = events.get(False)
            except Empty:
                break
            else:
                if event is not None:
                    if event.type == 'MARKET':
                        print(f"============= {event.datetime} ===========")
                        broker.execute_order()
                        strategy.calc_signals(event)
                        port.update_timeindex(event)

                    elif event.type == 'SIGNAL':
                        port.update_signal(event)
                        

                    elif event.type == 'ORDER':
                        #broker.execute_order(event)
                        broker.queue_order_for_execution(event)
                        

                    elif event.type == 'FILL':
                        port.update_fill(event)
    
    port.create_equity_curve_dataframe()

    return port