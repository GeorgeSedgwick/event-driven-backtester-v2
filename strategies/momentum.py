import numpy as np
import pandas as pd

from core.event import SignalEvent
from .base import Strategy

class MomentumStrategy(Strategy):
    def __init__(self, bars, events, lookback=252, use_shorts=False, verbose=False):
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.entry_bar = {s: None for s in self.ticker_list}
        self.lookback_period = lookback
        self.rebalance_period = 21
        self.days_since_rebalance = 0
        self.short_period, self.med_period = 30, 75
        self.use_shorts = use_shorts


        self.verbose = verbose

    def should_rebalance(self):
        return self.days_since_rebalance == 0 or self.days_since_rebalance >= self.rebalance_period

    def check_regime(self):
        bars = self.bars.get_latest_bars("SPY", N=self.med_period)
        if bars is not None and bars != []:

            if len(bars) >= self.med_period:
                closes_med = np.array([bar[4] for bar in bars])
                closes_short = np.array([bar[4] for bar in bars[-self.short_period:]])
                sma_med = np.mean(closes_med)
                sma_short = np.mean(closes_short)

                if sma_short < sma_med:
                    return "BEAR"
                elif sma_short > sma_med:
                    return "BULL"

                else:
                    return "FLAT"
                
            else:
                #print(f"Not enough bars to compute regime.")
                return "FLAT"

    


    def get_rankings(self):
        rankings = {}
        for s in self.ticker_list:
            if s == "SPY":
                continue
            bars = self.bars.get_latest_bars(s, N=self.lookback_period)

            if bars is not None and bars != []:
                if len(bars) >= self.lookback_period:
                    closes = np.array([bar[4] for bar in bars])
                    momentum = np.log(closes[-1] / closes[0])
                    rankings[s] = momentum
        return rankings

                    
    def calc_signals(self, event):
        if event.type == "MARKET":

            if self.should_rebalance():

                rankings = self.get_rankings()
                sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
                top5_tuples = sorted_rankings[:5]
                bottom5_tuples = sorted_rankings[-5:]

                top5 = [i[0] for i in top5_tuples]
                bottom5 = [i[0] for i in bottom5_tuples]

                regime = self.check_regime()


                for ticker in self.ticker_list:
                    
                    bars = self.bars.get_latest_bars(ticker, N=1)

                    if bars is None or bars == []:
                        continue

                    dt = bars[0][1]
                    close = bars[0][4]


                    if regime == "BULL" and ticker in top5:
                        signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close)
                    elif regime == "BEAR" and ticker in bottom5:
                        signal = SignalEvent(ticker, dt, 'SHORT', use_risk_manager=True, price=close)
                    else:
                        signal = SignalEvent(ticker, dt, "FLAT")

                    self.events.put(signal)


            
                self.days_since_rebalance = 0


            self.days_since_rebalance += 1
