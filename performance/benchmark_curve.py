
import plotly.graph_objects as go



def display_benchmark_curve(bnh_port, strategy_port, display_graph):
# ======= PLOT EQUITY CURVES =========
    strategy_title = "Momentum"
    strat_dfs = {"Buy and Hold": bnh_port.equity_curve, "Momentum": strategy_port.equity_curve}
    fig = go.Figure()
    for strategy in strat_dfs:
        fig = fig.add_trace(go.Scatter(x = strat_dfs[strategy].index,
                                        y = strat_dfs[strategy]["total"],
                                        name=strategy))
        
    fig.update_layout(legend_title_text="Strategy")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Portfolio Value")

    if display_graph is True:
        fig.show()