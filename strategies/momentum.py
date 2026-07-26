import numpy as np
import pandas as pd
from datetime import datetime, timezone
from time import sleep
from core.event import SignalEvent
from .base import Strategy
from statsmodels.tsa.stattools import coint

class MomentumStrategy(Strategy):
    def __init__(self, bars, events, lookback, rebalance, top_n, use_shorts, verbose=False):
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.entry_bar = {s: None for s in self.ticker_list}

        self.lookback_period = lookback
        self.rebalance_period = rebalance
        self.top_n = top_n

        self.days_since_rebalance = 0
        self.short_period, self.med_period = 30, 75

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
                    momentum = np.log(closes[-1] / closes[0])
                    
                    
                    
                    #momentum_1 = momentum - np.log(closes[-1] / closes[(self.lookback_period - 22)])
                    #momentum_2 = momentum - np.log(closes[-1] / closes[(self.lookback_period - 44)])



                    rankings[s] = momentum
        return rankings




                    
    def calc_signals(self, event, regime_and_prob):

        if regime_and_prob == None:
            regime = ""
            prob = 0
            size = 0
            #print(f"Highest probregime: {regime} | Prob: {prob}")
        else:
            regime = regime_and_prob[0]
            prob = regime_and_prob[1]
            size = regime_and_prob[2]
            if self.verbose: print(f"Highest prob regime: {regime} | Prob: {prob}")


        if regime == "BULL": self.bull_count += 1
        if regime == "BEAR": self.bear_count += 1
        if regime == "TRANSITION": self.transition_count += 1
        if regime == "RECOVERY": self.recovery_count += 1

        if event.type == "MARKET":

            if self.should_rebalance():

                rankings = self.get_rankings()
                sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
                top = []
                """if rankings:
                    t_score = np.percentile(list(rankings.values()), 99)
                    t_dict = {ticker: score for ticker, score in rankings.items() if score >= t_score}
                    t_sorted = sorted(t_dict.items(), key=lambda x: x[1], reverse=True)

                    t_list = [ticker[0] for ticker in t_sorted]
                    print(t_list)
                    top = t_list
                    print(len(top))
                    #print(len(top))"""

                top_tuples = sorted_rankings[:self.top_n]
                bottom_tuples = sorted_rankings[-self.top_n:]

                top = [i[0] for i in top_tuples]
                print(f"Regime on date {event.datetime}: {regime}")
                print(top)

                    
                bottom = [i[0] for i in bottom_tuples]

                for ticker in self.ticker_list:
                    bars = self.bars.get_latest_bars(ticker, N=1)

                    if bars is None or bars == []:
                        continue

                    dt = bars[0].datetime
                    close = bars[0].close
                    
                    if top != []:

                        
                        if regime == "BULL" and prob >= 0.0 and ticker in top: # and rankings[ticker] > 0.5:
                            signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close, regime=regime, size=size)
                        elif regime == "BEAR" and prob >= 0.0 and ticker in top: #and self.use_shorts==True:
                            signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close, regime=regime, size=size)
                        elif regime == "RECOVERY" and prob >= 0.0 and ticker in top: # and rankings[ticker] > 0.5:
                            signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close, regime=regime, size=size)
                        elif regime == "TRANSITION" and prob >= 0.0 and ticker in top:# and rankings[ticker] > 0.8:
                            signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close, regime=regime, size=size)


                        elif regime == "BEAR" and prob >= 0.0 and ticker in bottom and self.use_shorts==True:
                            signal = SignalEvent(ticker, dt, 'SHORT', use_risk_manager=True, price=close, regime=regime, size=size)
                        elif regime == "TRANSITION" and prob >= 0.0 and ticker in bottom and self.use_shorts==True:
                            signal = SignalEvent(ticker, dt, 'SHORT', use_risk_manager=True, price=close, regime=regime, size=size)


                        else:
                            signal = SignalEvent(ticker, dt, "FLAT")

                    else:
                        signal = SignalEvent(ticker, dt, "FLAT")

                            



                    self.events.put(signal)



                self.days_since_rebalance = 0


            self.days_since_rebalance += 1
