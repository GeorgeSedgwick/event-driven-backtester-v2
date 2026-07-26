# Import relevant modules.
from queue import Queue, Empty
from datetime import datetime, date, timezone
from strategies import BuyAndHoldStrategy, MomentumStrategy
from data.datahandler import HistoricCSVDataHandler

from core.portfolio import NaivePortfolio
from core.execution import SimulatedExecutionHandler

from models.gaussian import GaussianMarketRegimeDetector

from tqdm import tqdm

from performance.dashboard import equity_data, position_data
"""
Runs the backtest engine loop.

Params:

- strategy_name: The user's chosen strategy.
- ticker_list: List of tickers wished to trade/assess.
- start_date: The date from which the backtester should start.
- end_date: The date at which the backtester should end.
- initial_capital: Set the value of initial capital to trade with.
- regime_detector (default=None): if user has a regime detector they wish to pass they may, otherwise one will be instantiated inside the engine.
- **kwargs: any other arguments that a specific strategy may require.

"""

# Run the backtest engine.
def run_backtest(strategy_name, ticker_list, start_date, end_date, initial_capital, use_stops, track_dates, market, iv_idx, regime_detector=None, **kwargs):
    
    equity_data.clear()
    position_data.clear()
    pbar = tqdm(desc='Backtesting', unit=" bars")

    # Instantiate the main event queue.
    events = Queue()



    # Instantiate the DataHandler (bars)
    if market == 'SPY':
        bars = HistoricCSVDataHandler(events, csv_dir='/Users/george/python-projects/ed-backtest/backtester/data/sp_constituents', ticker_list=ticker_list, start_date=start_date, end_date=end_date, verbose=False)
    elif market == 'QQQ':
        bars = HistoricCSVDataHandler(events, csv_dir='/Users/george/python-projects/ed-backtest/backtester/data/nasdaq_constituents', ticker_list=ticker_list, start_date=start_date, end_date=end_date, verbose=False)
        

    # Instantiate the RegimeDetector (or accept the one passed in and reset the models DataHandler object).
    if regime_detector == None:
        regime_detector = GaussianMarketRegimeDetector(bars, warmup_freq=126, retrain_freq=21, n_components=4, market=market, iv_idx=iv_idx)
    else:
        regime_detector = regime_detector
        regime_detector.prepare_for_new_fold(bars)

    # Instantiate the user's chosen Strategy object
    strategy = strategy_name(bars, events, **kwargs)

    # Instantiate the Portfolio object
    port = NaivePortfolio(strategy_name, bars, events, start_date, initial_capital, verbose=False)
    
    # Instantiate the ExecutionHandler object
    broker = SimulatedExecutionHandler(events, bars, verbose=False)

    # Run loop indefinitely.
    while True:
        if bars.continue_backtest:
            bars.update_bars()
            pbar.update(1)
        # Unless bars.continue_backtest==False, then end the loop (backtest has complete).
        else:
            pbar.close()
            break

        # Second loop, retrieve events from the event queue previously instantiated.
        while True:
            try:
                event = events.get(False)
            # Queue empty? No more events to process, end the backtest.
            except Empty:
                break
            else:
                if event is not None:
                    # MarketEvent object is received.
                    if event.type == 'MARKET':
                        if track_dates: print(f"============= {event.datetime} ===========")

                        # Execute all pending orders (stored in ExecutionHandler queue, enters at today's open (T+1)).
                        broker.execute_order()

                        # Retrieves a tuple consisting of the highest probable regime and its probability (for pos sizing).
                        regime_and_prob = regime_detector.update()

                        # Check stops if enabled
                        if strategy_name != BuyAndHoldStrategy and use_stops != False: port.risk_manager.check_stops(bars, events, regime_and_prob)

                        # Calculates signals from prices, uses prob of regime for degree of confidence in trade.
                        strategy.calc_signals(event, regime_and_prob)

                        # Update the timeindex.
                        port.update_timeindex(event)

                    # SignalEvent object is received.
                    elif event.type == 'SIGNAL':
                        port.update_signal(event)
                        
                    # OrderEvent object is received.
                    elif event.type == 'ORDER':
                        # Add Order to ExecutionHandler's queue, store for tomorrow's open.
                        broker.queue_order_for_execution(event)
                        
                    # FillEvent object is received.
                    elif event.type == 'FILL':
                        # Update portfolio from FillEvent.
                        port.update_fill(event)
    
    # Create EQ Curve DataFrame.
    port.create_equity_curve_dataframe()


        
    

    # Return PortfolioObject, and RegimeDetector object (for potential reuse).
    return port, regime_detector
