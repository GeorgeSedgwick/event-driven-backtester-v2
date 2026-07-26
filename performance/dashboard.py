import datetime

import dash
from dash import Dash, dcc, html, Input, Output, dash_table
from collections import deque
import plotly.graph_objects as go
from threading import Thread
from datetime import datetime

equity_data = deque(maxlen=1000)
position_data = deque(maxlen=1000)

app = Dash(__name__)

app.layout=html.Div([
    html.H4('Live Backtest'),
    dcc.Graph(id='live-equity'),
    dcc.Interval(id='interval', interval=500, n_intervals=0),
])



@app.callback(
    Output('live-equity', 'figure'),
    Input('interval', 'n_intervals')
)
def update_graph(n):
    if not equity_data:
        return go.Figure()
    
    dates = [d['datetime'] for d in equity_data]
    values = [d['total'] for d in equity_data]

    fig = go.Figure(go.Scatter(
        x=dates,
        y=values,
        mode='lines'
    ))


    fig.update_layout(title='', xaxis_title='Date', yaxis_title='Value ($)')

    return fig