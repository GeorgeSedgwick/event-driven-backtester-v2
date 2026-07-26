import plotly.graph_objects as go

def display_walkforward_curve(combined_equity_curve, comb_bnh_eq, display_curve):
    """
    Reveives a combined equity curve (Pandas Series) and creates a graph.
    """
    strat_dfs = {
        "Strategy_EQ": combined_equity_curve,
        "Buy_And_Hold_EQ": comb_bnh_eq
    }

    fig = go.Figure()
    for strat in strat_dfs:
        fig = fig.add_trace(go.Scatter(x=strat_dfs[strat].index,
                                    y=strat_dfs[strat],
                                    name=f""))
    
    fig.update_layout(title_text=f"S&P 500 Universe 2018 - 2026 | Combined equity curve")
    fig.update_layout(legend_title="Strategy")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Portfolio Value")

    if display_curve == True:
        fig.show()