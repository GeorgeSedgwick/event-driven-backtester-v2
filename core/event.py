# Two loops, outer and inner.

# Inner loop handles capturing of events from the in-memory queue, routing them to the appropriate component.
from datetime import datetime



class Event(object):
    """
    Event provides an interface for all inherited events, that will trigger different events in the system.
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with corresponding bars.
    """

    def __init__(self, datetime):
        """
        Initialises the market event
        """
        self.type = 'MARKET'
        self.datetime = datetime


class SignalEvent(Event):
    """
    Handles the event of sending a signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """

    def __init__(self, ticker, datetime, signal_type, strength=1, use_risk_manager=True, price=None, regime=None, size=None, starb_details=None, starb_label=None, starb_pairing=None):
        """
        Initialises the SignalEvent.

        Receives a ticker, datetime and signal type 
        """

        self.type = 'SIGNAL'
        self.ticker = ticker
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength
        self.use_risk_manager = use_risk_manager
        self.price = price
        self.regime = regime
        self.size = size
        self.starb_details = starb_details
        self.starb_label = starb_label
        self.starb_pairing = starb_pairing


class OrderEvent(Event):
    """
    Handles the event of sending an Order to the execution system.
    The order contains a symbol, a type, quantity and a direction.
    
    """

    def __init__(self, ticker, order_type, quantity, direction, regime, action, stop_loss=None):
        """
        Initialises the order type, setting whether it is a market order or a limit order, has a quantity and its direction (Buy or Sell)

        
        action: Define the action for the order:
            - "OPEN"
            - "CLOSE"
            - "ADD"
            - "REDUCE"
            - "NET"
            - "STOP"

        """

        self.type = 'ORDER'
        self.ticker = ticker
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.regime = regime
        self.action = action
        self.stop_loss = stop_loss


    def print_order(self):
        """
        Outputs the values within the Order
        """

    
        print("Order: Ticker=%s, Type=%s, Quantity=%s, Direction=%s, Regime=%s" % \
        (self.ticker, self.order_type, self.quantity, self.direction, self.regime))
        



class FillEvent(Event):
    """
    Encapsulates the notion of a Filled order, as returned from a brokerage. Stores the quantity of
    an instrument actually filled an at what price. In addition, stores  the commission of the trade from the brokerage.
    """

    def __init__(self, timeindex, ticker, exchange, quantity, direction, fill_price, fill_cost, commission, slippage, regime, action):
        """
        Initialises the FillEvent object, sets the symbol, exchange, quantity, direction, cost of  fill and an optimal commission
        
        If commission is not provided, the Fill object will calculate it based on the trade size and Interactive Broker (the linked brokerage) fees.

        """

        self.type = 'FILL'
        self.timeindex = timeindex
        self.ticker = ticker
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_price = fill_price
        self.fill_cost = fill_cost
        self.commission = commission
        self.slippage = slippage
        self.regime = regime
        self.action = action



# type is just a class that creates other class
# this is known as a MetaClass


# Metaclasses create cleasss in the same way classes create objects.


                

        
            
        





















