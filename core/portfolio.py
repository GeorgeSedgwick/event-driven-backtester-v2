import datetime
import numpy as np
import pandas as pd
from queue import Queue
from random import randbytes

from abc import ABC, abstractmethod
from math import floor
from .event import FillEvent, OrderEvent
from .risk import RiskManager, StatArbRiskManager
from .oms import BasicOrderManager
from strategies import MomentumStrategy, BuyAndHoldStrategy, StatArbStrategy
from performance import *
from performance.dashboard import equity_data, position_data


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


    def __init__(self, strategy, bars, events, start_date, initial_capital, verbose=False):
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
        
        self.risk_manager = RiskManager(self) if strategy == MomentumStrategy or strategy == BuyAndHoldStrategy else StatArbRiskManager(self)
        self.order_manager = BasicOrderManager(self)
        self.trades = {}
        self.trade_ids = dict.fromkeys(self.ticker_list, None) # Temp
        self.id_list = [] # Permanent
        self.verbose = verbose

        self.all_positions = self.construct_all_positions() # Stores list of all previous positions recorded at a timestamp of a data event.
        self.current_positions = {s: {'quantity': 0, 'price_high_or_low': 0} for s in self.ticker_list}
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
        d = dict.fromkeys(self.ticker_list, 0)
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
        d = dict.fromkeys(self.ticker_list, 0)
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['slippage'] = 0.0
        d['total'] = self.initial_capital
        #print(f"Dict1 total = {d['total']}") # Just 100,000 (inital capital)
        return d
    

    def update_timeindex(self, event):
        """
        - Creates a dictionary: bars{}
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
            positions_snapshot[ticker] = self.current_positions[ticker]['quantity']

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

            market_value = self.current_positions[ticker]['quantity'] * ticker_bar[0].close
            holdings_snapshot[ticker] = market_value
            holdings_snapshot['total'] += market_value

            qty = self.current_positions[ticker]['quantity']
            if qty > 0:
                direction = "LONG"
            elif qty < 0:
                direction = "SHORT"
            else:
                continue

            position_data.append({'ticker': ticker, 'direction': direction, 'quantity': qty})

        self.current_holdings['total'] = holdings_snapshot['total']
        equity_data.append({'datetime': holdings_snapshot['datetime'], 'total': self.current_holdings['total']})
        position_data.clear()

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
        
        pos = self.current_positions[fill.ticker]

        prev_qty = pos['quantity']
        change = fill_dir * fill.quantity
        new_qty = prev_qty + change

        pos['quantity'] = new_qty

        if prev_qty == 0 and new_qty != 0:
            pos['price_high_or_low'] = fill.fill_price
        """        if self.current_positions[fill.ticker]['quantity'] == 0:
            self.current_positions[fill.ticker]['price_high'] = fill.fill_price
        self.current_positions[fill.ticker]['quantity'] += fill_dir*fill.quantity
        """



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

    def track_trade(self, event):
        if event.type == 'FILL':
            # Start tracking new long position
            if self.trade_ids[event.ticker] == None and event.action == "OPEN" and event.direction == "BUY":
                id = randbytes(n=10)

                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': event.quantity,
                    'direction': 'LONG',
                    'regime': event.regime,
                    'entry_price': event.fill_price,
                    'exit_datetime': None,
                    'exit_price': None,
                    'pnl': 0
                }                
                self.trades[id] = trade_entry
                self.trade_ids[event.ticker] = id
                self.id_list.append(id)

            # Track and adjust for increased exposure to long position
            elif self.trade_ids[event.ticker] != None and event.action == "ADD" and event.direction == "BUY":
                id = self.trade_ids[event.ticker]
                prev_qty = self.trades[id]['quantity'] 
                new_pos_qty = self.trades[id]['quantity'] + event.quantity

                prev_weight = 1 - prev_qty / (new_pos_qty)
                curr_weight = 1 - event.qty / (new_pos_qty)                

                new_avg_price = (prev_weight * self.trades[id]['entry_price']) + (curr_weight * event.quantity)
                self.trades[id].update({
                    'quantity': new_pos_qty,
                    'entry_price': new_avg_price
                })

            # Track and adjust for decreased exposure to long position
            elif self.trade_ids[event.ticker] != None and event.action == "REDUCE" and event.direction == "SELL":
                id = self.trade_ids[event.ticker]
                prev_qty = self.trades[id]['quantity']
                new_pos_qty = prev_qty - event.quantity

                partial_pnl = event.fill_price - self.trades[id]['entry_price'] * prev_qty

                self.trades[id].update({
                    'quantity': new_pos_qty,
                    'pnl': partial_pnl
                })
                



            elif self.trade_ids[event.ticker] != None and event.action == "CLOSE" and event.direction == "SELL":
                id = self.trade_ids[event.ticker]
                pnl = self.trades[id]['pnl'] + ((event.fill_price - self.trades[id]['entry_price']) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
    
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })

                self.trade_ids[event.ticker] = None


            elif self.trade_ids[event.ticker] != None and event.action == "NET" and event.direction == "SELL":
                id = self.trade_ids[event.ticker]
                
                pnl = self.trades[id]['pnl'] + ((event.fill_price - self.trades[id]['entry_price']) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })


                new_trade_quantity = self.trades[id]['quantity'] - event.quantity
                new_trade_id = randbytes(n=10)
                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': new_trade_quantity,
                    'direction': 'SHORT',
                    'regime': event.regime,
                    'entry_price': event.fill_price,
                    'exit_datetime': None,
                    'exit_price': None,
                    'pnl': 0
                }                
                self.trades[new_trade_id] = trade_entry
                self.trade_ids[event.ticker] = new_trade_id
                self.id_list.append(new_trade_id)

            
            elif self.trade_ids[event.ticker] == None and event.action == "OPEN" and event.direction == "SELL":
                id = randbytes(n=10)

                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': event.quantity,
                    'direction': 'SHORT',
                    'regime': event.regime,
                    'entry_price': event.fill_price,
                    'exit_datetime': None,
                    'exit_price': None,
                    'pnl': 0
                }                
                self.trades[id] = trade_entry
                self.trade_ids[event.ticker] = id
                self.id_list.append(id)

            elif self.trade_ids[event.ticker] != None and event.action == "ADD" and event.direction == "SELL":
                id = self.trade_ids[event.ticker]
                prev_qty = self.trades[id]['quantity'] 
                new_pos_qty = self.trades[id]['quantity'] + event.quantity

                prev_weight = 1 - prev_qty / (new_pos_qty)
                curr_weight = 1 - event.qty / (new_pos_qty)                

                new_avg_price = (prev_weight * self.trades[id]['entry_price']) + (curr_weight * event.quantity)
                self.trades[id].update({
                    'quantity': new_pos_qty,
                    'entry_price': new_avg_price
                })

            
            elif self.trade_ids[event.ticker] != None and event.action == "REDUCE" and event.direction == "BUY":
                id = self.trade_ids[event.ticker]
                prev_qty = self.trades[id]['quantity']
                new_pos_qty = prev_qty - event.quantity

                partial_pnl = (self.trades[id]['entry_price'] - event.fill_price) * self.trades[id]['quantity']

                self.trades[id].update({
                    'quantity': new_pos_qty,
                    'pnl': partial_pnl
                })



            elif self.trade_ids[event.ticker] != None and event.action == "CLOSE" and event.direction == "BUY":
                id = self.trade_ids[event.ticker]
                print(f"Closing short for: {event.ticker}: Trade ID: {id}")

                pnl = self.trades[id]['pnl'] + ((self.trades[id]['entry_price'] - event.fill_price) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
    
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })

                self.trade_ids[event.ticker] = None   


            elif self.trade_ids[event.ticker] != None and event.action == "NET" and event.direction == "BUY":
                id = self.trade_ids[event.ticker]

                pnl = self.trades[id]['pnl'] + ((self.trades[id]['entry_price'] - event.fill_price) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })

                new_trade_quantity = event.quantity - self.trades[id]['quantity']

                new_trade_id = randbytes(n=10)
                trade_entry = {
                    'entry_datetime': event.timeindex,
                    'ticker': event.ticker,
                    'quantity': new_trade_quantity,
                    'direction': 'LONG',
                    'regime': event.regime,
                    'entry_price': event.fill_price,
                    'exit_datetime': None,
                    'exit_price': None,
                    'pnl': 0
                }                
                self.trades[new_trade_id] = trade_entry
                self.trade_ids[event.ticker] = new_trade_id
                self.id_list.append(new_trade_id)

            elif self.trade_ids[event.ticker] != None and event.action == "STOP" and event.direction == "BUY":
                id = self.trade_ids[event.ticker]
                pnl = self.trades[id]['pnl'] + ((self.trades[id]['entry_price'] - event.fill_price) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
    
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })

                print(f"STOP TRACKED FOR {event.ticker}: {event.timeindex}")

                self.trade_ids[event.ticker] = None   


            elif self.trade_ids[event.ticker] != None and event.action == "STOP" and event.direction == "SELL":
                id = self.trade_ids[event.ticker]
                pnl = self.trades[id]['pnl'] + ((event.fill_price - self.trades[id]['entry_price']) * self.trades[id]['quantity'])
                trade_return = pnl / (self.trades[id]['entry_price'] * self.trades[id]['quantity'])
    
                holding_period = (event.timeindex - self.trades[id]['entry_datetime'] )
                
                self.trades[id].update({
                    'exit_price': event.fill_price,
                    'exit_datetime': event.timeindex,
                    'pnl': pnl,
                    'return': trade_return,
                    'holding_period': holding_period
                })


                print(f"STOP TRACKED FOR {event.ticker}: {event.timeindex}")

                self.trade_ids[event.ticker] = None



                




        




    def update_fill(self, event):
        """
        Update current positions and holdings from FillEvent object
        """
        if event.type == 'FILL':

            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            self.track_trade(event)
            #print(self.current_positions)



    def generate_naive_order(self, signal, net_quantity, current_pos):

        order = None

        ticker = signal.ticker
        order_type = 'MKT'
        order_quantity = abs(net_quantity)




        if net_quantity > 0:
            # Open long position
            if current_pos == 0:
                direction = 'BUY'
                action = "OPEN"

            # Increase exposure on long position
            if current_pos > 0:
                direction = 'BUY'
                action = "ADD"

            # Close a short position
            if current_pos < 0 and current_pos + net_quantity == 0:
                direction = 'BUY'
                action = 'CLOSE'

            # Flip a short position
            if current_pos < 0 and current_pos + net_quantity > 0:
                direction = 'BUY'
                action = 'NET'




        elif net_quantity < 0:
            # Open a short position
            if current_pos == 0:
                direction = 'SELL'
                action = 'OPEN'

            # Increase exposure on a short position
            if current_pos < 0:
                direction = 'SELL'
                action = 'ADD'
            
            # Close a long position
            if current_pos > 0 and current_pos + net_quantity == 0:
                direction = 'SELL'
                action = 'CLOSE'

            # Flip a long position
            if current_pos > 0 and current_pos + net_quantity < 0:
                direction = 'SELL'
                action = 'NET' 


        else:
            return None


        order = OrderEvent(ticker, order_type, order_quantity, direction, signal.regime, action=action)
        #order_data.append({'ticker': ticker, 'direction': direction, 'quantity': quantity})
        return order



    def calc_max_shares(self, ticker):
        bars = self.bars.get_latest_bars(ticker, N=1)
        close_price = bars[0].close
        print(ticker)
        print(close_price)

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
                    print(event.datetime)
                    order_size = self.calc_max_shares(ticker)

                if order_size is not None:

                    target_pos = None
                    current_pos = self.current_positions[event.ticker]['quantity']



                    

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
                                    order_event = self.generate_naive_order(event, net_quantity, current_pos)
                                    if self.verbose: print(f"PORT: Order submitted for {event.ticker}: {event.signal_type}")


                            else:
                                order_event = self.generate_naive_order(event, net_quantity, current_pos)
                                if self.verbose: print(f"PORT: Order submitted for {event.ticker}: {event.signal_type}")




            elif event.signal_type == 'FLAT':
                current_pos = self.current_positions[event.ticker]['quantity']
                net_quantity = -current_pos

                if net_quantity != 0:
                    order_event = self.generate_naive_order(event, net_quantity, current_pos)


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

