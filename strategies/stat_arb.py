import numpy as np
import pandas as pd
from datetime import datetime, timezone
import itertools
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm



from core.event import SignalEvent
from .base import Strategy
from utils.data_fetch import match_sector_pairs

class StatArbStrategy(Strategy):
    def __init__(self, bars, events, lookback, rebalance, n_pairs):
        self.bars = bars
        self.ticker_list = [x for x in self.bars.ticker_list if x != "SPY" and x != "^VIX"]
        self.events = events
        self.lookback_period = lookback
        self.rebalance_freq = rebalance
        self.n_pairs = n_pairs


        self.days_since_rebalance = 0
        self.warmup_complete = False
    
        

        

    def should_rebalance(self):
        return self.days_since_rebalance >= self.rebalance_freq and self.warmup_complete == True

    def get_pairs(self):
    
        pairs = list(itertools.combinations(self.ticker_list, 2))
        filtered_pairs, individuals = match_sector_pairs(pairs)
        price_series = dict.fromkeys(individuals)

        pair_pvalues = dict.fromkeys(filtered_pairs)

        bars_dict = dict.fromkeys(individuals)
        for ticker in bars_dict.keys():
            bars_dict[ticker] = self.bars.get_latest_bars(ticker=ticker, N=self.lookback_period)
        
        for pair in filtered_pairs:
            bars_A = bars_dict[pair[0]]
            bars_B = bars_dict[pair[1]]

            if not bars_A[-1].datetime == bars_B[-1].datetime and len(bars_A) >= self.lookback_period:
                continue
            else:
                dt = bars_A[-1].datetime
                closes_A = pd.Series(bar.close for bar in bars_A)
                closes_B = pd.Series(bar.close for bar in bars_B)
                
                if closes_A.empty or closes_B.empty:
                    continue

                if price_series[pair[0]] is None:
                    price_series[pair[0]] = closes_A
                
                if price_series[pair[1]] is None:
                    price_series[pair[1]] = closes_B


                data = pd.concat([closes_A, closes_B], axis=1)
                data.columns = ['A', 'B']

                data = data[(data['A'] > 0) & (data['B'] > 0)]

                y0 = np.log(data['A'].values)
                y1 = np.log(data['B'].values)


                score, pvalue, _ = coint(y0, y1)

                if score < -4 and pvalue <= 0.05:
                    pair_pvalues[pair] = pvalue



        none_list = []
        
        for key in pair_pvalues.keys():
            if pair_pvalues[key] == None:
                none_list.append(key)


        for key in none_list:
            try:
                del pair_pvalues[key]
            except KeyError:
                continue

        
        
        sorted_final_pairs = sorted(pair_pvalues.items(), key=lambda x: x[1])

        used_tickers = set()
        final_pairs = []

        for pair, pvalue in sorted_final_pairs:
            ticker_A, ticker_B = pair
            if ticker_A in used_tickers or ticker_B in used_tickers:
                continue

            final_pairs.append(pair)
            used_tickers.add(ticker_A)
            used_tickers.add(ticker_B)
            
            if len(final_pairs) == self.n_pairs:
                break       
            

        return final_pairs, price_series, dt
    


    def get_spreads(self, pairs, price_series):
        pair_spreads = {pair: {"beta": None, "spread": None} for pair in pairs}
        for pair in pairs:
            x = np.log(price_series[pair[0]].values)
            y = np.log(price_series[pair[1]].values)

            X = sm.add_constant(x)

            model = sm.OLS(y, X).fit()


            beta = model.params[1]
            spread = x - (beta * y)


            pair_spreads[pair] = {"beta": beta, "spread": spread}
        
        return pair_spreads
    

    def get_spread_z_scores(self, pair_spreads_and_betas):
        spread_z_scores = dict.fromkeys(pair_spreads_and_betas)
        for pair in pair_spreads_and_betas.keys():
            spreads = pair_spreads_and_betas[pair]["spread"]
            z = (spreads[-1] - np.mean(spreads)) / np.std(spreads)
            spread_z_scores[pair] = z

        
        return spread_z_scores


            
            

    




    def calc_signals(self, event, regime_and_prob):
            
        if self.warmup_complete == False and self.days_since_rebalance < self.lookback_period:
            self.days_since_rebalance += 1
        else:
            self.warmup_complete = True
                    
            if self.should_rebalance():
                print(f"Days since rebalance: {self.days_since_rebalance}")
                
                pairs, price_series, dt = self.get_pairs()
                


                pair_spreads_and_betas = self.get_spreads(pairs, price_series)
                spread_z_scores = self.get_spread_z_scores(pair_spreads_and_betas)
                pairs_signal_count = 0


                for pair in pairs:
                    if pairs_signal_count >= self.n_pairs:
                        break
                    else:
                        signal_A = None
                        signal_B = None


                        if regime_and_prob == None:
                            regime = ""
                            prob = 0
                            size = 0

                        else:
                            regime = regime_and_prob[0]
                            prob = regime_and_prob[1]
                            size = regime_and_prob[2]




                        if regime != "":
                            if spread_z_scores[pair] < -1.5:

                                print(f"Regime: {regime} | Trade: {pair} | Z-score: {spread_z_scores[pair]}")
                            
                                signal_A = SignalEvent(pair[0], 
                                                    dt, 
                                                    "LONG", 
                                                    use_risk_manager=True, 
                                                    price=price_series[pair[0]].iloc[-1],
                                                    regime=regime, 
                                                    starb_details=pair_spreads_and_betas[pair], 
                                                    starb_label="A",
                                                    starb_pairing=pair,
                                                    size=size)
                                
                                print(f"Signal sent for {pair[0]}: LONG")
                                


                                signal_B = SignalEvent(pair[1], 
                                                    dt,
                                                    "SHORT", 
                                                    use_risk_manager=True, 
                                                    price=price_series[pair[1]].iloc[-1],
                                                    regime=regime,
                                                    starb_details=pair_spreads_and_betas[pair],
                                                    starb_label="B",
                                                    starb_pairing=pair)
                            
                                print(f"Signal sent for {pair[1]}: SHORT")

                            elif spread_z_scores[pair] > 1.5:

                                print(f"Regime: {regime} | Trade: {pair} | Z-score: {spread_z_scores[pair]}")

                                signal_A = SignalEvent(pair[0],
                                                    dt,
                                                    "SHORT",
                                                    use_risk_manager=True,
                                                    price=price_series[pair[0]].iloc[-1],
                                                    regime=regime,
                                                    starb_details=pair_spreads_and_betas[pair],
                                                    starb_label="A",
                                                    starb_pairing=pair)
                                
                                print(f"Signal sent for {pair[0]}: SHORT")
                                
                                signal_B = SignalEvent(pair[1],
                                                    dt,
                                                    "LONG",
                                                    use_risk_manager=True,
                                                    price=price_series[pair[1]].iloc[-1],
                                                    regime=regime,
                                                    starb_details=pair_spreads_and_betas[pair],
                                                    starb_label="B",
                                                    starb_pairing=pair,
                                                    size=size)
                                
                                print(f"Signal sent for {pair[1]}: LONG")
                                
                            else:
                                signal_A = SignalEvent(pair[0],
                                                    dt,
                                                    "FLAT")


                                print(f"Signal sent for {pair[0]}: EXIT (OOM)")
                                
                                signal_B = SignalEvent(pair[1],
                                                    dt,
                                                    "FLAT")

                                print(f"Signal sent for {pair[1]}: EXIT (OOM)")
                                    
                                
                            

                        
                            if signal_A is not None and signal_B is not None:
                                
                                self.events.put(signal_A)
                                self.events.put(signal_B)
                                pairs_signal_count += 1
                









                self.days_since_rebalance = 0
            else:
                self.days_since_rebalance += 1







