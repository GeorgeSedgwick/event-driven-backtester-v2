

"""
Decides whether a trade is allowed, and if so, how big - without
knowing or caring about the strategy logic.


Exposure is applied to remaining capital, not total capital.
Creating a dynamic allocation system.

"""


class RiskManager(object):
    def __init__(self, portfolio, verbose=False):
        self.portfolio = portfolio
        self.max_portfolio_exposure = 0.25 # Sets the maximum exposure of a single trade
        self.verbose = verbose

    def size_order(self, signal):
        cash = self.portfolio.current_holdings['cash']
        available_cash = (cash - self.portfolio.order_manager.reserved_cash) * self.max_portfolio_exposure
        if self.verbose:
            print(f"RiskManager | Effective available cash: {available_cash}")

        if signal.regime is not None:
            if signal.regime == "BULL":
                regime_multiplier = 1.0
            elif signal.regime == "BEAR":
                regime_multiplier = 0.2
            elif signal.regime == "RECOVERY":
                regime_multiplier = 0.8
            elif signal.regime == "TRANSITION":
                regime_multiplier = 0.5

            order_size = int((available_cash / signal.price) * regime_multiplier)
        else:
            regime_multiplier = 0.7 # If No Regime, reduce exposure (combat uncertainty)
            order_size = int((available_cash / signal.price) * regime_multiplier)

        return order_size if order_size >= 1 else None
    






