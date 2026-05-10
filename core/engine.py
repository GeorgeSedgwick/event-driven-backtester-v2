from queue import Queue, Empty
from datetime import datetime

from data.datahandler import HistoricCSVDataHandler

from core.portfolio import NaivePortfolio
from core.execution import SimulatedExecutionHandler

from models.gaussian import GaussianMarketRegimeDetector




def run_backtest(strategy_name, ticker_list, start_date, end_date, initial_capital, track_dates, **kwargs):
    events = Queue()

    bars = HistoricCSVDataHandler(events, csv_dir='/Users/george/python-projects/ed-backtest/backtester/data/sp_constitutents', ticker_list=ticker_list, start_date=start_date, end_date=end_date, verbose=False)

    market_regime = GaussianMarketRegimeDetector(bars, warmup_freq=252, retrain_freq=21, n_components=4)

    strategy = strategy_name(bars, events, **kwargs)

    port = NaivePortfolio(bars, events, start_date, initial_capital, verbose=False)
    
    broker = SimulatedExecutionHandler(events, bars, verbose=False)

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
                        if track_dates: print(f"============= {event.datetime} ===========")
                        broker.execute_order()
                        regime = market_regime.update()
                        strategy.calc_signals(event, regime)
                        port.update_timeindex(event)

                    elif event.type == 'SIGNAL':
                        port.update_signal(event)
                        

                    elif event.type == 'ORDER':
                        #broker.execute_order(event)
                        broker.queue_order_for_execution(event)
                        

                    elif event.type == 'FILL':
                        port.update_fill(event)
    
    #print(f"Total Slippage: ${broker.total_slippage:.2f}")
    port.create_equity_curve_dataframe()

    return port