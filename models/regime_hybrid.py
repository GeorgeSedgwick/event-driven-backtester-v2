from sklearn.ensemble import RandomForestClassifier
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from datetime import timedelta
import numpy as np
import pandas as pd


class GaussianForestHybridRegimeDetector():
    def __init__(self, bars, warmup, retrain_freq, market, iv_idx):
        self.bars = bars
        self.warmup = warmup
        self.retrain_freq = retrain_freq
        self.market = market
        self.iv_idx = iv_idx

        self.spy_bar_history = []
        self.vix_bar_history = []

        self.first_date = None
        self.current_regime = None
        self.last_retrain = None
        self.current_probs = None

        self.warmup_complete = False
        self.forest_model = RandomForestClassifier(n_estimators=500, max_depth=8, random_state=0, class_weight='balanced')
        self.hmm_model = GaussianHMM(n_components=4, covariance_type="full", n_iter=100, random_state=1)

    def get_features(self):
        bars = self.spy_bar_history
        vix_bars = self.vix_bar_history

        # Align date of bars
        bar_dates = {b['date'].date(): b for b in bars}
        vix_dates = {b['date'].date(): b for b in vix_bars}

        same_dates = sorted(set(bar_dates) & set(vix_dates))

        bars = [bar_dates[date] for date in same_dates]
        vix_bars = [vix_dates[date] for date in same_dates]

        assert bars[-1]['date'].date() == vix_bars[-1]['date'].date()


        closes_array = np.array([bar['close'] for bar in bars])
        closes_series = pd.Series(closes_array)

        vix_closes_array = np.array([bar['close'] for bar in vix_bars])
        vix_closes_series = pd.Series(vix_closes_array)


        returns = closes_series.pct_change()
        vol = returns.rolling(window=21).std()
        momentum_20 = closes_series.pct_change(20)
        momentum_30 = closes_series.pct_change(30)
        momentum_60 = closes_series.pct_change(60)
        mean_return_30 = returns.rolling(window=21).mean()
        skew = returns.rolling(window=60).skew()
        dd = closes_series / closes_series.cummax() - 1
        vix_log = np.log(vix_closes_series)

        pred_horizon = 10
        
        df = pd.DataFrame({
            "Close": closes_series,
            "Mean_Return_30": mean_return_30,
            "Returns": returns,
            "Vol": vol,
            "Momentum_20": momentum_20,
            "Momentum_30": momentum_30,
            "Momentum_60": momentum_60,
            "Skew": skew,
            "DD": dd,
            "VIX_Log": vix_log

        })

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)

        momentum_20_mean = df['Momentum_20'].mean()
        momentum_20_std = df['Momentum_20'].std()

        momentum_30_mean = df['Momentum_30'].mean()
        momentum_30_std = df['Momentum_30'].std()

        momentum_60_mean = df['Momentum_60'].mean()
        momentum_60_std = df['Momentum_60'].std()


        df['Momentum_20'] = np.where(df["Momentum_20"] > momentum_20_mean + 3 * momentum_20_std,
                                     momentum_20_mean + 2 * momentum_20_std,
                                     df['Momentum_20'])
        df['Momentum_20'] = np.where(df["Momentum_20"] < momentum_20_mean - 3 * momentum_20_std,
                                     momentum_20_mean - 2 * momentum_20_std,
                                     df['Momentum_20'])


        df['Momentum_30'] = np.where(df["Momentum_30"] > momentum_30_mean + 3 * momentum_30_std,
                                     momentum_30_mean + 2 * momentum_30_std,
                                     df['Momentum_30'])
        df['Momentum_30'] = np.where(df["Momentum_30"] < momentum_30_mean - 3 * momentum_30_std,
                                     momentum_30_mean - 2 * momentum_30_std,
                                     df['Momentum_30'])


        df['Momentum_60'] = np.where(df["Momentum_60"] > momentum_60_mean + 3 * momentum_60_std,
                                     momentum_60_mean + 2 * momentum_60_std,
                                     df['Momentum_60'])
        df['Momentum_60'] = np.where(df["Momentum_60"] < momentum_60_mean - 3 * momentum_60_std,
                                     momentum_60_mean - 2 * momentum_60_std,
                                     df['Momentum_60'])

        df['Future_Return'] = df['Close'].shift(-pred_horizon) / df['Close'] - 1
        df['Future_Vol'] = df['Returns'].rolling(pred_horizon).std().shift(-pred_horizon)

        conditions = [

            (df['DD'] < -0.10) & (df['Future_Return'] > 0.05),
            (df['Future_Return'] > 0.05),
            (df['Future_Return'] < -0.02)
        ]

        choices = [
            "RECOVERY",
            "BULL",
            "BEAR",
        ]

        df['Regime'] = np.select(conditions, choices, default="TRANSITION")

        df.loc[df['Future_Return'].isna(), "Regime"] = np.nan

        raw_features = df[['Mean_Return_30', 'Returns', 'Vol', 'Momentum_20', 'Momentum_30', 'Momentum_60', 'Skew', 'DD', 'VIX_Log']]
        target = df['Regime']

        return raw_features, target


    def update(self):

        bar = self.bars.get_latest_bars(ticker=self.market, N=1)[0]
        vix_bar = self.bars.get_latest_bars(ticker=self.iv_idx, N=1)[0]

        self.spy_bar_history.append({
            'date': bar.datetime,
            'close': bar.close
        })

        self.vix_bar_history.append({
            'date': vix_bar.datetime,
            'close': vix_bar.close
        })

        dt = bar.datetime

        # self.first_date is given a value to track when the warmup period starts (and ends)
        if self.first_date != None:
            pass
        else: self.first_date = dt

        # Warmup is insufficient (not enough bars accumulated), return None
        if min(len(self.spy_bar_history), len(self.vix_bar_history)) < self.warmup:
            return None

        if self.last_retrain is None or dt - self.last_retrain >= timedelta(days=self.retrain_freq):
            raw_features, target = self.get_features()

            # This mask is really cool because it applies a true or false for Value or NaN
            train_mask = target.notna()

            # It can then be used to select only matchin rows from X and y (raw features and target)
            # ensuring RFC only trains on examples where 10-day-forward regime has actually happened:
            X_train = raw_features.loc[train_mask]
            y_train = target.loc[train_mask]

            X_latest = raw_features.iloc[[-1]]

            self.model.fit(X_train, y_train)

            self.last_retrain = dt


            regime_probs = dict(zip(self.model.classes_, self.model.predict_proba(X_latest)[0]))

            predict_regime = self.model.predict(X_latest)[0]

            state_prob_size_tuple = self.create_state_prob_size_tuple(predict_regime, regime_probs)

            return state_prob_size_tuple
        else:
            raw_features, _ = self.get_features()

            X_latest = raw_features.iloc[[-1]]

            regime_probs = dict(zip(self.model.classes_, self.model.predict_proba(X_latest)[0]))

            predict_regime = self.model.predict(X_latest)[0]

            state_prob_size_tuple = self.create_state_prob_size_tuple(predict_regime, regime_probs)

            return state_prob_size_tuple



    def create_state_prob_size_tuple(self, predict_regime, regime_probs):
        """
        For now i'm keeping the output the same as the HMM, this means
        producing a 3-piece tuple containing the following information:

        [0]: The most likely regime
        [1]: The probability of that regime
        [2]: A combine position size multiplier

        """

        regime = predict_regime
        prob = regime_probs[regime]
        size = (
                1 * regime_probs["BULL"] +
                0 * regime_probs["BEAR"]
                + 0.5 * regime_probs["TRANSITION"]
                + 0.7 * regime_probs["RECOVERY"]
                )

        return (regime, prob, size)


    def prepare_for_new_fold(self, bars):
        self.bars = bars