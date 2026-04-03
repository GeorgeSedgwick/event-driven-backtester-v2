"""
OrderManager Class:

This class is used to avoid giving portfolio access to price data,
allowing for cleaner separation of concerns throughout the system.

It has 3 duties:

- can_reserve() | Compares cash available to cash required for order. Deny order if it exceeds.

- reserve() | Reserves the cash required for the trade, allowinng an order.

- release() | Releases the cash reserved, at time of fill.


can_reserve() + reserve() are both called in portfolio.update_signal(), right before an order is made.

release() is called in update_holdings_from_fill()

"""

from abc import abstractmethod, ABC

class OrderManager(ABC):

    @abstractmethod
    def can_reserve():

        raise NotImplementedError("Should implement can_reserve() func.")


    @abstractmethod
    def reserve():

        raise NotImplementedError("Should implement reserve() func.")

    @abstractmethod
    def release():

        raise NotImplementedError("Should implement release() func.")



class BasicOrderManager(OrderManager):
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.reserved_cash = 0

    def can_reserve(self, cost):
        available_cash = self.portfolio.current_holdings['cash'] - self.reserved_cash
        return cost <= available_cash



    def reserve(self, cost):
        if self.can_reserve(cost):
            self.reserved_cash += cost
            return True
        return False


    def release(self, cost):
        self.reserved_cash -= cost
        if self.reserved_cash < 0:
            self.reserved_cash = 0
