import numpy as np
import pandas as pd
from .base import Strategy
from core.event import SignalEvent

class MeanReversionStrategy(Strategy):
    def __init__(self, bars, events, lookback, short_period, long_period, z_condition, z_exit_threshold, use_shorts, verbose=False): 
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.lookback = lookback
        self.short_period = short_period
        self.long_period = long_period
        self.z_condition = z_condition
        self.z_exit_threshold = z_exit_threshold
        self.use_shorts = use_shorts
        self.verbose = verbose

        self.top_percentile = 200
        self.bottom_percentile = 200




    def get_rankings(self):
        rankings = {}
        for s in self.ticker_list:
            if s == "SPY":
                continue
            bars = self.bars.get_latest_bars(s, N=252)

            if bars is not None and bars != []:
                
                if len(bars) >= self.lookback:
                    closes = np.array([bar.close for bar in bars])
                    momentum = np.log(closes[-1] / closes[0])
                    rankings[s] = momentum
        return rankings

    def calc_signals(self, event, regime):
        
        rankings = self.get_rankings()
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
        top_tuples = sorted_rankings[:self.top_percentile]
        bottom_tuples = sorted_rankings[-self.bottom_percentile:]

        top = [i[0] for i in top_tuples]
        bottom = [i[0] for i in bottom_tuples]






        if event.type == "MARKET":

            for ticker in self.ticker_list:
                    bars = self.bars.get_latest_bars(ticker, N=self.lookback)
                    
                    if bars is not None and bars != []:
                        if len(bars) >= self.lookback:


                            dt = bars[0].datetime
                            close = bars[0].close

                            z_period_closes = np.array([bar.close for bar in bars])
                            sma = np.mean(z_period_closes)
                            std = np.std(z_period_closes)
                            if std == 0:
                                continue
                            z_score = (z_period_closes[-1] - sma) / std

                            signal = None
                            if regime == "FLAT":
                                if z_score < -self.z_condition and ticker not in top and ticker not in bottom:
                                    signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=True, price=close)

                                elif z_score > self.z_condition and self.use_shorts == True and ticker not in top and ticker not in bottom:
                                    signal = SignalEvent(ticker, dt, 'SHORT', use_risk_manager=True, price=close)
      
                                elif abs(z_score) < self.z_exit_threshold:
                                    signal = SignalEvent(ticker, dt, 'FLAT')

                            
                            else:
                                signal = SignalEvent(ticker, dt, "FLAT")

                            if signal is not None:
                                self.events.put(signal)











