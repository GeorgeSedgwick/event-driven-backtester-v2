import numpy as np
import pandas as pd
from queue import Queue

from .base import Strategy
from core.event import SignalEvent

class SMA_CrossoverStrategy(Strategy):
    def __init__(self, bars, events):

        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.bought, self.short = self._calc_initial_bought()
        self.period = 30

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
                bars = self.bars.get_latest_bars(s, N=self.period)
                
                if bars is not None and bars != []:
                    if len(bars) >= self.period:
                        
                        closes = [bar[4] for bar in bars[-self.period:]]
                        sma = sum(closes) / self.period
                        
                        if closes[-1] > sma and self.bought[s] == False:
                            
                            signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG', use_risk_manager=True)
                            self.events.put(signal)
                            self.bought[s] = True

                        elif closes[-1] < sma and self.bought[s] == True:
                            signal = SignalEvent(bars[-1][0], bars[-1][1], 'EXIT')
                            self.events.put(signal)
                            self.bought[s] = False
                        
                        else:
                            continue
