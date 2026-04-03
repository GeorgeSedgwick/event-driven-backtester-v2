import numpy as np
import pandas as pd
from queue import Queue

from .base import Strategy
from core.event import SignalEvent

class GoldenCrossStrategy(Strategy):
    def __init__(self, bars, events):

        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.bought, self.short = self._calc_initial_bought()
        self.short_period = 50
        self.med_period = 200

    def _calc_initial_bought(self):

        bought = {}
        for s in self.ticker_list:
            bought[s] = False

        short = {}
        for s in self.ticker_list:
            short[s] = False

        return bought, short
    

    
    def calc_signals(self, event):
        
        if event.type == "MARKET":
            for s in self.ticker_list:
                bars = self.bars.get_latest_bars(s, N=self.med_period)
                
                if bars is not None and bars != []:
                    if len(bars) >= self.med_period:
                        closes_med = [bar[4] for bar in bars]
                        closes_short = [bar[4] for bar in bars[-self.short_period:]]
                        sma_med = sum(closes_med) / self.med_period
                        sma_short = sum(closes_short) / self.short_period
                        
                        if sma_short > sma_med and self.bought[s] == False:
                            print(f"GENERATING BUY SIGNAL FOR {s}")
                            signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG', use_risk_manager=True)
                            self.events.put(signal)
                            self.bought[s] = True

                        elif sma_short < sma_med and self.bought[s] == True:
                            print(f"GENERATING EXIT SIGNAL FOR {s}")
                            signal = SignalEvent(bars[-1][0], bars[-1][1], 'EXIT')
                            self.events.put(signal)
                            self.bought[s] = False