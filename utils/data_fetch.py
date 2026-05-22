import yfinance as yf
import pandas as pd
import requests
import io
import os
import json

def get_snp500_tickers():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url, headers=headers)
        table = pd.read_html(io.StringIO(response.text))
        tickers = table[0]['Symbol'].to_list()

        tickers = [ticker.replace('.', '-') for ticker in tickers]

        with open("tickers.json", "w") as f:
            json.dump(tickers, f)

        return tickers


    except Exception as e:
        print(f"Error collecting ticker_list from URL!")
        print(f"Trying locally stored tickers.")

        with open("tickers.json", "r") as f:
            tickers = json.load(f)
            return tickers
        

def get_valid_tickers(tickers, csv_dir, start_date, end_date):
    valid_tickers = []
    start = start_date.replace(tzinfo=None)
    end = end_date.replace(tzinfo=None)

    for t in tickers:
        path = os.path.join(csv_dir, f'{t}.csv')
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None)
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]
            if len(df) >= 30:
                valid_tickers.append(t)
        
        except Exception as e:
            print(f"{t}: Error - {e}")
    
    if "SPY" not in valid_tickers:
        valid_tickers.insert(0, "SPY")

    if "^VIX" not in valid_tickers:
        valid_tickers.append("^VIX")
        
    return valid_tickers
 