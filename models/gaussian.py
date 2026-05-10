from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from datetime import timedelta, datetime, timezone
import pandas as pd
import numpy as np


class GaussianMarketRegimeDetector():
    def __init__(self, bars, warmup_freq, retrain_freq, n_components):
        self.bars = bars
        self.warmup_freq = warmup_freq
        self.retrain_freq = retrain_freq
        self.n_components = n_components

        self.first_date = None
        self.current_regime = None
        self.last_retrain = None

        self.model = GaussianHMM(n_components=n_components, covariance_type="full", n_iter=100, random_state=1)
        self.scaler = StandardScaler()

    def get_features(self, fit_scaler):
        bars = self.bars.get_latest_bars(ticker='SPY', N=1000)
        closes_array = np.array([bar.close for bar in bars])
        closes_series = pd.Series(closes_array)

        returns = closes_series.pct_change()

        mean_returns = returns.rolling(window=21).mean()
        vol = returns.rolling(window=21).std()
        skew = returns.rolling(window=21).skew()
        momentum_5_day = closes_series.pct_change(5)

        df = pd.DataFrame({"Mean_Returns": mean_returns, 
                            "Vol": vol,
                            "Skew": skew, 
                            "5_Day_Momentum": momentum_5_day})

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)

        momentum_mean = df['5_Day_Momentum'].mean()
        momentum_std = df['5_Day_Momentum'].std()

        df['5_Day_Momentum'] = np.where(df['5_Day_Momentum'] > momentum_mean + 3 * momentum_std,
                                        momentum_mean + 2 * momentum_std,
                                        df['5_Day_Momentum'])
        df['5_Day_Momentum'] = np.where(df['5_Day_Momentum'] < momentum_mean - 3 * momentum_std,
                                        momentum_mean - 2 * momentum_std,
                                        df['5_Day_Momentum'])
        
        X = df[['Mean_Returns', 'Vol', 'Skew', '5_Day_Momentum']]
        if fit_scaler == True:
            X_new = self.scaler.fit_transform(X)
        else:
            X_new = self.scaler.transform(X)

        return X_new
    
    def assign_labels(self):
        # Assign labels to the regimes identified for strategy logic
        # High vol, high returns = recovery
        # High vol, negative/low returns = bear
        # Low vol, high returns = bull
        # Low vol, weaker returns = weak bull

        bull = np.argmax(self.model.means_[:, 0])
        bear = np.argmin(self.model.means_[:, 0])

        remaining = [i for i in range(self.n_components) if i != bull and i != bear]
        recovery = remaining[np.argmax(self.model.means_[remaining, 1])]

        remaining.remove(recovery)
        flat = remaining[0]

        regime_labels = {
            bull: 'BULL',
            bear: 'BEAR',
            recovery: 'RECOVERY',
            flat: 'FLAT'
        }

        self.regime_labels = regime_labels




    def update(self):
        # Fetch the latest bar
        bars = self.bars.get_latest_bars(ticker='SPY', N=1)

        # Datetime of said bar
        dt = bars[0].datetime

        # To track when retrain should occur, and when warmup period ends, store the first dt of the backtester
        if self.first_date is not None:
            pass

        else:
            self.first_date = dt

        # Check if the warmup frequency is over, if not, return market regime as None
        if dt - self.first_date <= timedelta(days=self.warmup_freq):
            return None
        
        # Check if the retrain frequency if retrain hasn't happened yet, or if retrain is due 
        elif self.last_retrain is None or dt - self.last_retrain >= timedelta(days=self.retrain_freq):
            X = self.get_features(fit_scaler=True)

            self.model.fit(X)
            self.last_retrain = dt

            self.assign_labels()

            hidden_states = self.model.predict(X)
            self.current_regime = hidden_states[-1]
            
            return self.regime_labels[self.current_regime]

        else:
            X = self.get_features(fit_scaler=False)

            hidden_states = self.model.predict(X)
            self.current_regime = hidden_states[-1]

            return self.regime_labels[self.current_regime]
            


