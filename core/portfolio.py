import datetime
import numpy as np
import pandas as pd
from queue import Queue

from abc import ABC, abstractmethod
from math import floor
from .event import FillEvent, OrderEvent
from .risk import RiskManager
from .oms import BasicOrderManager
from research.performance import create_sharpe_ratio, create_drawdowns


class Portfolio(ABC):
    """
    Handles the positions and market value of all instruments
    at a resolution of a 'bar'.
    i.e. secondly, minutely, 5-min. 30-min, 60min or EOD.
    """

    @abstractmethod
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic.
        """
        raise NotImplementedError("Should implement update_signal()")

#all_positions: stores a list of all previous POSITIONS recorded
#at the timestamp of a market data event. (Position is just the quantity of the asset)

#current_positions: stores a dictionary containing the current positions
#for the latest market bar update



class NaivePortfolio(Portfolio):
    """
    Designed to send orders to a brokerage object with a constant
    quantity size blindly, i.e. without any risk management or position sizing.

    Used to test simple strategies
    """


    def __init__(self, bars, events, start_date, initial_capital, verbose=False):
        """
        Initialises the portfolio with bars and an event queue.
        Also includes a starting datetime index and initial capital.
        
        
        Parameters:
        bars: The DataHandler object with current market data.
        events: The Event Queue object.
        start_date: The start date (bar) of the portfolio.
        initial_capital: The starting capital (USD).
        """

        self.bars = bars
        self.events = events
        self.ticker_list = self.bars.ticker_list
        self.initial_capital = initial_capital
        self.total_fills = 0
        self.start_date = start_date
        self.risk_manager = RiskManager(self)
        self.order_manager = BasicOrderManager(self)
        self.trades = []

        self.verbose = verbose

        self.all_positions = self.construct_all_positions() # Stores list of all previous positions recorded at a timestamp of a data event.
        self.current_positions = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] ) 
        # A dictionary of what is held at the time of the heartbeat. 


 
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    
    def construct_all_positions(self):
        """
       Creates a dictionary for each ticker, sets value=0 for each and then datetime
       key is added.
       Then added to a list
        
       Creates the historical record of positions, starting with the
       first bar (start_date)
        """

        d = dict( (k,v) for k, v in [(s, 0) for s in self.ticker_list] )
        d['datetime'] = self.start_date
        return [d]
    

    def construct_all_holdings(self):
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.ticker_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0 # Cumulative accrued
        d['slippage'] = 0.0
        d['total'] = self.initial_capital
        return [d]
    
    def construct_current_holdings(self):
        """
        For every single heartbeat, current market value of all the positions
        held are calculated.

        Live data can skip this, as market data can parsed straight from brokerage.
        For backtesting, these need calculating manually.
        """
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.ticker_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['slippage'] = 0.0
        d['total'] = self.initial_capital
        #print(f"Dict1 total = {d['total']}") # Just 100,000 (inital capital)
        return d
    

    def update_timeindex(self, event):
        """
        - Creates a dictionary bars{}
        - Store a copy of each tickers latest bar as bars[ticker]
        - Creates a snapshot of all current positions and adds to all_positions at latest datetime available
        - Creates a holdings snapshot of all current holdings... ''
        - Updates current_holdings with the latest market values available

        """

    
        bars = {}
        for ticker in self.ticker_list:
            bars[ticker] = self.bars.get_latest_bars(ticker, N=1)


        positions_snapshot = dict.fromkeys(self.ticker_list, 0)
        positions_snapshot['datetime'] = bars[self.ticker_list[0]][0].datetime

        for ticker in self.ticker_list:
            positions_snapshot[ticker] = self.current_positions[ticker]

        self.all_positions.append(positions_snapshot)


        holdings_snapshot = dict.fromkeys(self.ticker_list, 0)
        holdings_snapshot['datetime'] = bars[self.ticker_list[0]][0].datetime
        holdings_snapshot['cash'] = self.current_holdings['cash']
        holdings_snapshot['commission'] = self.current_holdings['commission']
        holdings_snapshot['slippage'] = self.current_holdings['slippage']
        holdings_snapshot['total'] = self.current_holdings['cash']

        for ticker in self.ticker_list:
            ticker_bar = bars[ticker]

            if ticker_bar is None or len(ticker_bar) == 0:
                continue

            market_value = self.current_positions[ticker] * ticker_bar[0].close
            holdings_snapshot[ticker] = market_value
            holdings_snapshot['total'] += market_value
        
        self.current_holdings['total'] = holdings_snapshot['total']
        self.all_holdings.append(holdings_snapshot)

            


    def update_positions_from_fill(self, fill):
        """
        Ensures current_positions dictionary reflects the latesst fills.

        fill = the FillEvent object
        """
        fill_dir = 0

        if fill.direction == 'BUY':
            fill_dir = 1

        elif fill.direction == 'SELL':
            fill_dir = -1
        

        self.current_positions[fill.ticker] += fill_dir*fill.quantity



    def update_holdings_from_fill(self, fill):
        # FillEvent gets passed in and is used to update
        # the holdings matrix, reflective of holdings value

        """
        params = FillEvent object (fill)
        """
        # Check dircttion
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1

            self.order_manager.release(fill.fill_cost)

        elif fill.direction == 'SELL':
            fill_dir = -1

        if self.verbose: print(f"FILL {fill.ticker}: fill_cost {fill.fill_cost:.2f}")
        
        self.current_holdings['slippage'] += fill.slippage
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= fill.fill_cost * fill_dir
        self.current_holdings['cash'] -= fill.commission
        self.total_fills += 1


    def update_fill(self, event):
        """
        Update current positions and holdings from FillEvent object
        """
        if event.type == 'FILL':

            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)


            if event.direction == 'long_entry':
                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': event.quantity,
                    'direction': 'long',
                    'entry_price': event.fill_price,
                    'exit_price': None,
                    'exit_datetime': None,
                    'pnl': None
                }
                self.trades.append(trade_entry)


            elif event.direction == 'short_entry':
                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': event.quantity,
                    'direction': 'short',
                    'entry_price': event.fill_price,
                    'exit_price': None,
                    'exit_datetime': None,
                    'pnl': None
                }
                self.trades.append(trade_entry)


            elif event.direction == 'long_exit':
                for trade in self.trades:
                    if (trade['ticker'] == event.ticker
                        and trade['exit_datetime'] == None
                        and trade['direction'] == 'long'):

                        trade['exit_price'] = event.fill_price
                        trade['exit_datetime'] = event.timeindex
                        trade['pnl'] = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
                        break

            elif event.direction == 'short_exit':
                for trade in self.trades:
                    if (trade['ticker'] == event.ticker
                        and trade['exit_datetime'] == None
                        and trade['direction'] == 'short'):

                        trade['exit_price'] = event.fill_price
                        trade['exit_datetime'] = event.timeindex
                        trade['pnl'] = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
                        break




    def generate_naive_order(self, signal, net_quantity):

        order = None

        ticker = signal.ticker
        order_type = 'MKT'
        
        if net_quantity > 0:
            direction = 'BUY'
        elif net_quantity < 0:
            direction = 'SELL'
        else:
            return None
            
        order = OrderEvent(ticker, order_type, abs(net_quantity), direction)

        return order



    def calc_max_shares(self, ticker):
        bars = self.bars.get_latest_bars(ticker, N=1)
        close_price = bars[0].close
        order_size = int(self.current_holdings['cash'] // close_price)
        return order_size



            
    def update_signal(self, event):
        # Calls above method and adds the generated order to the events queue.
        """
        SignalEvent object is sent to generate_naive_order() for OrderEvent to
        be created.
        
        Uses a netting system to handle direction flips concisely.
        """
        if event.type == 'SIGNAL':
            order_event = None

            if event.signal_type in ['LONG', 'SHORT']:
                if event.use_risk_manager:
                    order_size = self.risk_manager.size_order(event)
                else:
                    ticker = event.ticker # Used for benchmarking, where RiskManager is not used
                    order_size = self.calc_max_shares(ticker)

                if order_size is not None:
                    target_pos = None
                    current_pos = self.current_positions[event.ticker]

                    if event.signal_type == 'LONG':
                        target_pos = current_pos if current_pos > 0 else order_size
                        

                    elif event.signal_type == 'SHORT':
                        target_pos = current_pos if current_pos < 0 else -order_size
                    
                    if target_pos is not None:
                        net_quantity = target_pos - current_pos

                        if self.verbose: print(f"Net: {net_quantity} | Target: {target_pos} | Current: {current_pos}")

                        if net_quantity != 0:
                            
                            if net_quantity > 0:
                                cash_needed = net_quantity * event.price
                                if self.order_manager.reserve(cash_needed):
                                    order_event = self.generate_naive_order(event, net_quantity)
                                    if self.verbose: print(f"PORT: Order submitted for {event.ticker}: {event.signal_type}")
                            else:
                                order_event = self.generate_naive_order(event, net_quantity)
                                if self.verbose: print(f"PORT: Order submitted for {event.ticker}: {event.signal_type}")

            elif event.signal_type == 'FLAT':
                current_pos = self.current_positions[event.ticker]
                net_quantity = -current_pos

                if net_quantity != 0:
                    order_event = self.generate_naive_order(event, net_quantity)
                    if self.verbose: print(f"PORT: Order submitted for {event.ticker}: {event.signal_type}")

            if order_event:
                self.events.put(order_event)


    def create_equity_curve_dataframe(self):
        # Creates a DataFrame from the all_holdings list of dicts.

        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):

        total_return = self.equity_curve['equity_curve'].iloc[-1]
        returns = self.equity_curve['returns'].dropna()
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns)
        max_dd, dd_duration = create_drawdowns(pnl)

        return {
            'total_return': (total_return - 1.0) * 100.0,
            'sharpe': sharpe_ratio,
            'max_drawdown': max_dd,
            'drawdown_duration': dd_duration
        }
    
    def get_trade_points(self):
        
        wins = losses = breakeven = 0

        for trade in self.trades:
            pnl = trade.get('pnl')

            if pnl is None:
                continue

            elif pnl > 0:
                wins += 1
            elif pnl < 0:
                losses += 1
            else:
                breakeven += 1


        return self.trades, wins, losses, breakeven

