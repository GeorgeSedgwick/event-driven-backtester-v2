"""
Class hierarchy based on a DataHandler object, which gives all subclasses an interface
for providing market data to the remaining components within the system.

In this way, any subclass data handler can be 'swapped out', without affecting strategy
or portfolio calculation.


Example subclasses: HistoricCSVDataHandler, QuandlDataHandler, SecuritiesMasterDataHandler, InteractiveBrokersMarketFeedDataHandler etc.

This backtester:
- Creates a historic CSV data handler
- Loads intraday CSV data for equities in an OLHCV set of bars
- Drip feed on a bar-by-bar basis into Strategy, and Portfolio on every system 'heartbeat', avoiding lookahead bias.

"""


from datetime import datetime
import os, os.path
import pandas as pd
import yfinance as yf


from abc import ABC, abstractmethod

from core.event import MarketEvent # From event.py, import the MarketEvent subclass



class DataHandler(ABC):

    @abstractmethod
    def get_latest_bars(self, ticker, N=1):

        """
        returns the last N bars from the latest_ticker list.
        """

        raise NotImplementedError("Should implement get_latest_bar()")
    

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure for all tickers in the ticker list.
        """

        raise NotImplementedError("Should implement updates_bars()")
    


class HistoricCSVDataHandler(DataHandler):
    """
    Reads CSV files for each requested ticker and provides an interface  to obtain the "latest" bar
    in an identical manner to a live trading interface.
    """

    def __init__(self, events, csv_dir, ticker_list, start_date=None, end_date=None, verbose=False):

        """
        initialises the datahandler by requesting the location of the CSV files and a list of symbols
        
        It will be assumd that all files are of the form 'ticker.csv', where  ticker is a string in the list.


        Parameters:
        events - The Event Queue.
        csv_dir - Absolute directory path to the CSV fils.
        ticker_list - A list of ticker strings.
        
        
        """
        
        self.events = events
        self.csv_dir = csv_dir
        self.ticker_list = ticker_list
        self.start_date = start_date
        self.end_date = end_date

        self.ticker_data = {}
        self.latest_ticker_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

        self.latest_ticker_data = {s: [] for s in self.ticker_list} #Initialise latest bars for each ticker, stops KeyError occurring.
        self._generators = {s: self._get_new_bar(s) for s in self.ticker_list} #Generator for each ticker


        self.verbose = verbose

    def _open_convert_csv_files(self):
        """Opens the CSV files from the data directory, converts them into pandas DataFrames within a ticker dictionary"""
        """
        The idea is to get the data and merge them into 1 timeline.
        """

        comb_index = None
        for s in self.ticker_list:
            # Load the CSV file with no header information, indexed on date
            #print(s)
            self.ticker_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header=0, index_col=0, parse_dates=True,
                names=[ # Override the CSV column names and replace with these, for robustness and reusability.
                    'datetime', 'open', 'high',
                    'low', 'close', 'adj_close', 'volume'
                ],
                usecols=[0, 1, 2, 3, 4, 5, 6]
            )
            self.ticker_data[s].sort_index(inplace=True)
            self.ticker_data[s].index = pd.to_datetime(self.ticker_data[s].index, utc=True)

            if self.start_date is not None:
                self.ticker_data[s] = self.ticker_data[s][self.ticker_data[s].index >= self.start_date]
            if self.end_date is not None:
                self.ticker_data[s] = self.ticker_data[s][self.ticker_data[s].index <= self.end_date]
            #print(self.ticker_data[s].close)
            #I've got the whole CSV of data fine.

    def _get_new_bar(self, ticker):
        """
        Returns the latest bar from the data feed as a
        tuple of:

        (ticler, datetime, open, low, high, close, volume)
        """
        for row in self.ticker_data[ticker].itertuples():
            yield (
                ticker,
                row.Index,
                row.open,
                row.high,
                row.low,
                row.close,
                row.volume
            )
            # itertuples() is the pandas method for iterating over rows in a DataFrame



    def get_latest_bars(self, ticker, N=1):
        """
        Returns the last N bars from the latest_ticker list
        or N-k if less available.
        """

        try:
            bars_list = self.latest_ticker_data[ticker]
            
        except KeyError:
            if self.verbose:
                print(f"That ticker: {ticker} is not available in the historical data set.")
        else:
            return bars_list[-N:]
        

    def get_latest_bar_datetime(self, ticker):
        try:
            bars_list = self.latest_ticker_data[ticker]
        except KeyError:
            if self.verbose:
                print(f"That ticker {ticker} is not available in historical data set.")
            raise
        else:
            return bars_list[-1][1]
        
    def update_bars(self):
        """
        Pushes the latest bar to the latest_ticker_data structure
        for all tickers in the ticker list.
        """
        #print("UPDATE BARS CALLED")
        bars_added = False
        for s in self.ticker_list:
            try:
                bar = next(self._generators[s])
            except StopIteration:
                continue

            if bar is not None:
                self.latest_ticker_data[s].append(bar)
                bars_added = True

            
        if bars_added:
            latest_datetime = self.get_latest_bar_datetime(self.ticker_list[0])
            self.events.put(MarketEvent(latest_datetime))
        else:
            self.continue_backtest = False


    def get_all_bars(self, ticker):
        return self.ticker_data[ticker]
            


        
        