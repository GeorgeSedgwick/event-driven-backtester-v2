from .event import SignalEvent
from.event import OrderEvent

"""
Decides whether a trade is allowed, and if so, how big - without
knowing or caring about the strategy logic.


Exposure is applied to remaining capital, not total capital.
Creating a dynamic allocation system.

"""



class StatArbRiskManager():
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.max_portfolio_exposure = 0.01
        self.pairs_positions = {}
        print(f"StatArb Risk Manager instantiated.")

    

    
    def size_order(self, signal):
        starb_details = signal.starb_details
        starb_label = signal.starb_label
        pair = signal.starb_pairing

        print(pair)


        if starb_label == "A":
            self.pairs_positions.setdefault(pair, {"size": None, "price": None})
            if signal.signal_type == "LONG":
                cash = self.portfolio.current_holdings['cash']
            
                available_cash = (cash - self.portfolio.order_manager.reserved_cash) * self.max_portfolio_exposure

                
                print(f"LONG ORDER SIZING AVAILABLE CASH: {available_cash}")

                order_size = int((available_cash / signal.price) * signal.size)
                self.pairs_positions[pair]['size'] = order_size
                self.pairs_positions[pair]['price'] = signal.price
                return order_size if order_size >= 1 else None



            elif signal.signal_type == "SHORT":
                cash = self.portfolio.current_holdings['cash']
                available_cash = (cash - self.portfolio.order_manager.reserved_cash) * self.max_portfolio_exposure
                print(f"SHORT ORDER SIZING (A): AVAILABLE CASH: {available_cash}")



                order_size = int((available_cash / signal.price))
                self.pairs_positions[pair]['size'] = order_size
                self.pairs_positions[pair]['price'] = signal.price
                return order_size if order_size >= 1 else None



        
        elif starb_label == "B":
            if signal.signal_type == "LONG":
                if self.pairs_positions[pair]['size'] is None or signal.starb_pairing not in self.pairs_positions.keys():
                    return None
                else:
                    A_order_size = self.pairs_positions[pair]['size']
                    A_signal_price = self.pairs_positions[pair]['price']

                    beta = starb_details['beta']
                    if beta <= 0 or beta > 10:
                        return None
    
                    order_size = int((A_order_size * A_signal_price * beta) / signal.price)

                    print(f"LONG ORDER SIZING (B): COST: {signal.price * order_size}")

                    return order_size if order_size >= 1 else None



            elif signal.signal_type == "SHORT":
                if self.pairs_positions[pair]['size'] is None or signal.starb_pairing not in self.pairs_positions.keys():
                    return None
                else:
                    A_order_size = self.pairs_positions[pair]['size']
                    A_signal_price = self.pairs_positions[pair]['price']

                    beta = starb_details['beta']
                    if beta <= 0 or beta > 10:
                        return None
                    order_size = int((A_order_size * A_signal_price * beta) / signal.price)
                    print(f"SHORT ORDER SIZING (B): COST: {signal.price * order_size}")

                    return order_size if order_size >= 1 else None


        else:
            return None




    def check_stops(self, bars, events, regime_and_prob):

        stop_loss = 0.20

        if regime_and_prob is not None:
            regime = regime_and_prob[0]
        else:
            regime = None

        
        current_tickers = {ticker: data for ticker, data in self.portfolio.current_positions.items() if data['quantity'] != 0 }

        tickers = list(current_tickers.keys())
        pairs = []
        for ticker in tickers:
            for pair in self.pairs_positions:
                 if ticker in pair:
                    if pair not in pairs:
                        pairs.append(pair)

        


        pair_stops_hit = []
        cover_direction = None
    

        for pair in pairs:
            ticker_A = pair[0]
            ticker_B = pair[1]

            if pair in pair_stops_hit:
                continue

            ticker_A_bar = bars.get_latest_bars(ticker_A, N=1)[0]
            ticker_A_close = ticker_A_bar.close

            ticker_B_bar = bars.get_latest_bars(ticker_B, N=1)[0]
            ticker_B_close = ticker_B_bar.cl0se
            
            dt = ticker_A_bar.datetime


    
            current_qty = 0

            if cover_direction != None:
                order = OrderEvent(ticker, "MKT", abs(current_qty), cover_direction, regime=regime, action="STOP")
                events.put(order)
                pair_stops_hit.append(ticker)













class RiskManager(object):
    def __init__(self, portfolio, verbose=False):
        self.portfolio = portfolio
        self.max_portfolio_exposure = 0.1 # Sets the maximum exposure of a single trade
        self.stops_triggered = 0
        self.stop_losses = []
        self.stop_losses_pct = []
        

        self.verbose = verbose

    def size_order(self, signal):
        cash = self.portfolio.current_holdings['cash']
        available_cash = (cash - self.portfolio.order_manager.reserved_cash) * self.max_portfolio_exposure
        if self.verbose:
            print(f"RiskManager | Effective available cash: {available_cash}")

        if signal.regime is not None:
            if signal.regime == "BULL":
                regime_multiplier = 1
            elif signal.regime == "BEAR":
                regime_multiplier = 0
            elif signal.regime == "RECOVERY":
                regime_multiplier = 1
            elif signal.regime == "TRANSITION":
                regime_multiplier = 1

            order_size = int((available_cash / signal.price) * signal.size) # signal.size or regime_multiplier
            #print(order_size)
        else:
            regime_multiplier = 0.0 # If No Regime, reduce exposure to 0
            order_size = int((available_cash / signal.price) * regime_multiplier)


        
        if signal.signal_type == "SHORT":
            order_size = order_size // 2
        

        return order_size if order_size >= 1 else None
    

    def check_stops(self, bars, events, regime_and_prob):

        stop_loss = 0.2

        if regime_and_prob is not None:
            regime = regime_and_prob[0]
        else:
            regime = None

        
        current_tickers = {ticker: data for ticker, data in self.portfolio.current_positions.items() if data['quantity'] != 0 }

        tickers = list(current_tickers.keys())
        stops_hit = []
        cover_direction = None
    

        for ticker in tickers:

            if ticker in stops_hit:
                continue

            latest_bar = bars.get_latest_bars(ticker, N=1)[0]
            close = latest_bar.close
            dt = latest_bar.datetime

            if current_tickers[ticker]['quantity'] > 0:
                prev_high = self.portfolio.current_positions[ticker]['price_high_or_low']
                self.portfolio.current_positions[ticker]['price_high_or_low'] = max(prev_high, close)

                if close < self.portfolio.current_positions[ticker]['price_high_or_low'] * (1 - stop_loss):
                    cover_direction = "SELL"

            
            if current_tickers[ticker]['quantity'] < 0:
                prev_low = self.portfolio.current_positions[ticker]['price_high_or_low']
                self.portfolio.current_positions[ticker]['price_high_or_low'] = min(prev_low, close)

                if close > self.portfolio.current_positions[ticker]['price_high_or_low'] * (1 + stop_loss):
                    cover_direction = "BUY"


            current_qty = self.portfolio.current_positions[ticker]['quantity']

    


            if cover_direction != None:
                order = OrderEvent(ticker, "MKT", abs(current_qty), cover_direction, regime=regime, action="STOP")
                events.put(order)
                stops_hit.append(ticker)
                    



"""
    print(f"Stops Triggered: {strategy_port.risk_manager.stops_triggered}")
    stop_losses_pct = strategy_port.risk_manager.stop_losses_pct
    stop_losses = strategy_port.risk_manager.stop_losses
    print(f"Average Stop Loss ($): {np.mean(stop_losses)}$")
    print(f"Average Stop Loss (%): {np.mean(stop_losses_pct) * 100}%")

"""