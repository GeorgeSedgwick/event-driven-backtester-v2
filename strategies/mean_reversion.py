import numpy as np
import pandas as pd
from .base import Strategy
from core.event import SignalEvent

class MeanReversionStrategy(Strategy):
    def __init__(self, bars, events, lookback): 
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.bought, self.short = self._calc_inital_bought()
        self.short_period, self.med_period = 50, 200
        self.lookback = lookback
        self.z_condition = 2
        self.z_exit_threshold = 1
        self.entry_bar = {s: None for s in self.ticker_list}

    def _calc_inital_bought(self):
        bought = {}
        short = {}
        for s in self.ticker_list:
            bought[s] = False
            short[s] = False

        
        return bought, short
    

    def check_regime(self, s):
            bars = self.bars.get_latest_bars(s, N=self.med_period)
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
                    return "FLAT"


    def calc_signals(self, event):
        if event.type == "MARKET":

            for s in self.ticker_list:
                    regime = self.check_regime(s)
                    bars = self.bars.get_latest_bars(s, N=self.lookback)
                    
                    if bars is not None and bars != []:
                        if len(bars) >= self.lookback:
                            z_period_closes = np.array([bar[4] for bar in bars])
                            sma = np.mean(z_period_closes)
                            std = np.std(z_period_closes)
                            z_score = (z_period_closes[-1] - sma) / std

                    
                            
                            if regime == "BULL":

                                if z_score < -self.z_condition and not self.bought[s]:
                                    signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG_ENTRY', use_risk_manager=True)
                                    self.events.put(signal)
                                    
                                    self.bought[s] = True
                                    self.short[s] = False
                                    self.entry_bar[s] = bars[-1][1]
                                
                                elif abs(z_score) < self.z_exit_threshold:
                                    current_bar = bars[-1][1]

                                    if self.bought[s] and current_bar > self.entry_bar[s]:
                                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG_EXIT')
                                        self.events.put(signal)
                                        self.bought[s] = False
                                        self.entry_bar[s] = None
                                        
                                    if self.short[s] and (current_bar < self.entry_bar[s] or abs(z_score) < self.z_exit_threshold):
                                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'SHORT_EXIT')
                                        self.events.put(signal)
                                        self.short[s] = False
                                        self.entry_bar[s] = None
                                
                                
                            elif regime == "BEAR":

                                if z_score > self.z_condition and not self.short[s]:
                                    signal = SignalEvent(bars[-1][0], bars[-1][1], 'SHORT_ENTRY', use_risk_manager=True)
                                    self.events.put(signal)
                                    self.short[s] = True
                                    self.bought[s] = False
                                    self.entry_bar[s] = bars[-1][1]

                                elif abs(z_score) < self.z_exit_threshold:
                                    current_bar = bars[-1][1]

                                    if self.bought[s] and current_bar > self.entry_bar[s]:
                                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'LONG_EXIT')
                                        self.events.put(signal)
                                        self.bought[s] = False
                                        self.entry_bar[s] = None
                                        
                                    if self.short[s] and (current_bar < self.entry_bar[s] or abs(z_score) < self.z_exit_threshold):
                                        signal = SignalEvent(bars[-1][0], bars[-1][1], 'SHORT_EXIT')
                                        self.events.put(signal)
                                        self.short[s] = False
                                        self.entry_bar[s] = None
                                
                        












