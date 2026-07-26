from research.benchmarking import compare_to_benchmark
from research.wfo import run_wfo

from performance.dashboard import app, equity_data
from threading import Thread
import time
import webbrowser
import logging



def run_dash():
    app.run(debug=False, use_reloader=False)

live_chart="ON"

if live_chart=="ON":
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    Thread(target=run_dash, daemon=True).start()
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8050')




if __name__ == "__main__":
    MODE = "benchmark" # "benchmark" | "wfo"

    if MODE == "benchmark":
        compare_to_benchmark()

    elif MODE == "wfo":
        run_wfo()







