from pathlib import Path
import sqlite3
from datetime import datetime
import pandas as pd

def read_from_database():



    db_path = Path("data/backtests.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM backtests", conn)




    conn.close()

    return df



def store_backtest(name, start_date, end_date, port, trades):
    stats = port.output_summary_stats()

    sharpe = stats['sharpe']
    max_drawdown = stats['max_drawdown']
    total_return = stats['total_return']

    trade_count = len(trades)


    db_path = Path("data/backtests.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO backtests (
                   timestamp,
                   start_date,
                   end_date,
                   strategy_name,
                   sharpe,
                   max_drawdown,
                   total_return,
                   trade_count
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        start_date,
        end_date,
        name,
        sharpe,
        max_drawdown,
        total_return,
        trade_count
    ))
    conn.commit()