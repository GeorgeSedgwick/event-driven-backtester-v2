import numpy as np
import pandas as pd
from queue import Queue
from datetime import datetime
from .base import Strategy
from core.event import SignalEvent


class BuyAndHoldStrategy(Strategy):
    """
   testing mechanism for the strategy class, goes long and will never exit a position
    """

    def __init__(self, bars, events, use_shorts=False, verbose=False, **kwargs):
        self.bars = bars
        self.ticker_list = self.bars.ticker_list
        self.events = events
        self.use_shorts = use_shorts
        self.verbose = verbose
        
        self.bull_count = 0
        self.bear_count = 0
        self.transition_count = 0
        self.recovery_count = 0

    def calc_signals(self, event, regime):
        """
        Generate a Long SignalEvent object after the first MarketSignal arrives
        """
        if regime == "BULL": self.bull_count += 1
        if regime == "BEAR": self.bear_count += 1
        if regime == "TRANSITION": self.transition_count += 1
        if regime == "RECOVERY": self.recovery_count += 1

        if event.type == "MARKET":
            for ticker in self.ticker_list:
                if ticker == '^VIX':
                    continue

                bars = self.bars.get_latest_bars(ticker, N=1)

                if bars is None or bars == []:
                    continue
            
                dt = bars[0].datetime
                close = bars[0].close

                signal = SignalEvent(ticker, dt, 'LONG', use_risk_manager=False, price=close)
                self.events.put(signal) # Append the Queue() object with the Signal

