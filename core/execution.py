
from datetime import datetime, timezone
from queue import Queue
import numpy as np

from abc import ABC, abstractmethod

from .event import FillEvent, OrderEvent
from models.slippage import LogSlippageModel



class ExecutionHandler(ABC):
    # Handles interaction between a set of order objects generated
    # by Portfolio, and the Fill objects that occur in the mkt.


    # Can use to subclass simulated or live brokerage.

    @abstractmethod
    def execute_order(self, event):


        raise NotImplementedError("Should implement execute_order()")
    

    
    


class SimulatedExecutionHandler(ExecutionHandler):
    """
    Converts all order objecs into their equivalent fill
    objects.

    Receive OrderEvent
    Decide an Execution Price
    Compute fill_cost
    Create FillEvent witt the fill cost and commission
    """

    def __init__(self, events, data_handler, verbose=False):

        """
        Param: events - The Queue of Event objects.
               data_handler: the datahandler object
        """
        self.events = events
        self.data_handler = data_handler
        self.pending_orders = Queue()
        self.slippage_model = LogSlippageModel()
        self.total_slippage = 0

        self.verbose = verbose

    def calc_fill_cost(self, ticker, quantity, direction):
        bars = self.data_handler.get_latest_bars(ticker, N=1)
        if bars is None:
            return
        
        open = bars[0][2]
        dt = bars[0][1]
        fill_quantity = quantity

        fill_price = self.slippage_model.calculate(open, quantity, direction)
        
        if self.verbose: print(f"EXEC | Open: {open} | Fill price: {fill_price} | Slippage: {fill_price - open}")
        
        slippage_cost = abs(fill_price - open) * fill_quantity
        self.total_slippage += slippage_cost

        fill_cost = fill_price * fill_quantity


        return dt, fill_price, fill_cost

    
    def calculate_ib_commission(self, fill_cost):
        trade_value = fill_cost # Check if its exceeds 6k
        standard_cost = 3.0 # IB £3 flat rate for all LSE trades under 6k

        if trade_value > 6000:
            commission = (0.05 / 100 * trade_value) + max(trade_value * 0.000045, 0.01) # LSE fee

        else:
            commission = standard_cost + max(trade_value * 0.000045, 0.01) # LSE fee



        return commission
    
    def queue_order_for_execution(self, event):
        """
        Adds the order_event to a different FIFO queue, which delays the execution until the following day's opening value becomes available.

        Thus, removing lookahead bias from the system, as execution occurs at T+1.
        
        """

        if event.type == 'ORDER':
            self.pending_orders.put(event)

    def execute_order(self):
        """
        Converts Order objects into Fill objects.
        """
        while True:
            if self.pending_orders.empty():
                break
            else:

                event = self.pending_orders.get(False)
                if self.verbose: print(f"EXEC: {event.ticker} order taken from new FIFO queue, executing...")

                result = self.calc_fill_cost(event.ticker, event.quantity, event.direction)

                if result != None:
                    current_datetime, fill_price, fill_cost = result

                commission = self.calculate_ib_commission(fill_cost)

                if fill_cost is not None:
                    fill_event = FillEvent(
                        current_datetime,
                        event.ticker,
                        'EXCHANGE',
                        event.quantity,
                        event.direction,
                        fill_price,
                        fill_cost, 
                        commission
                    )

                    self.events.put(fill_event)

# FOR LIVE EXECUTION USE: datetime.now(timezone.utc) instead of current_datetime


    
            