import numpy as np
import pandas as pd
from datetime import datetime, timezone
from time import sleep
from core.event import SignalEvent
from .base import Strategy
from statsmodels.tsa.stattools import coint

class CrossSectionalMomentumStrategy(Strategy):
    def __init__(self, bars, events, lookback, rebalance, top_n, use_shorts, verbose=False):
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.entry_bar = {s: None for s in self.ticker_list}

        self.lookback_period = lookback
        self.rebalance_period = rebalance
        self.top_n = top_n

        self.days_since_rebalance = 0

        self.use_shorts = use_shorts
        self.verbose = verbose

        self.bull_count = 0
        self.bear_count = 0
        self.transition_count = 0
        self.recovery_count = 0

    def should_rebalance(self):
        return self.days_since_rebalance == 0 or self.days_since_rebalance >= self.rebalance_period


    def get_rankings(self):
        rankings = {}
        for s in self.ticker_list:
            if s == "SPY" or s == "^VIX" or s == "QQQ" or s == "^VXN":
                continue
            bars = self.bars.get_latest_bars(s, N=self.lookback_period)
            if bars is not None and bars != []:

                if len(bars) >= self.lookback_period:
                    closes = np.array([bar.close for bar in bars])


                    # Total momentum from lookback
                    momentum = np.log(closes[-1] / closes[0])

                    # 6-month momentum
                    mom_6 = np.log(closes[-1] / closes[self.lookback_period - 127])

                    # 3-month momentum
                    mom_3 = np.log(closes[-1] / closes[self.lookback_period - 64])

                    # 1-month momentum
                    mom_1 = np.log(closes[-1] / closes[self.lookback_period - 22])

                    mom_2_week = np.log(closes[-1] / closes[self.lookback_period - 11])

                    

                    composite_mom = (
                        #0.2 * mom_3 +
                        0.5 * mom_6 +
                        0.5 * momentum)


                    rankings[s] = composite_mom
        return rankings




                    
    def calc_signals(self, event, regime_and_size):

        if regime_and_size == None:
            regime = ""
            size = 0
        else:
            regime = regime_and_size[0]
            size = regime_and_size[1]


        if regime == "BULL": self.bull_count += 1
        if regime == "BEAR": self.bear_count += 1
        if regime == "TRANSITION": self.transition_count += 1
        if regime == "RECOVERY": self.recovery_count += 1

        if event.type == "MARKET":

            if self.should_rebalance():

                rankings = self.get_rankings()
                sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True) # Change to True for real momentum (False for reversals)





                top = []
                top_tuples = sorted_rankings[:self.top_n]
                bottom_tuples = sorted_rankings[-self.top_n:]

                top = [i[0] for i in top_tuples]

                if self.verbose: print(f"Top picks: {top}")

                print(f"Top Picks: {top}")
                bottom = [i[0] for i in bottom_tuples]

                for ticker in self.ticker_list:
                    bars = self.bars.get_latest_bars(ticker, N=1)

                    if bars is None or bars == []:
                        continue

                    dt = bars[0].datetime
                    close = bars[0].close


                    
                    if top != []:

                        if ticker in top: # and rankings[ticker] > 0.5:
                            signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close, regime=regime, size=size)


                        elif ticker in bottom and self.use_shorts==True:
                            signal = SignalEvent(ticker, dt, 'SHORT', use_risk_manager=True, price=close, regime=regime, size=size)
                            

                        else:
                            signal = SignalEvent(ticker, dt, "FLAT")

                    else:
                        signal = SignalEvent(ticker, dt, "FLAT")

                            



                    self.events.put(signal)



                self.days_since_rebalance = 0


            self.days_since_rebalance += 1
