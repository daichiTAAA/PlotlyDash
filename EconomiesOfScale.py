import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

# Load the data
data_path = "./csv_files/EconomiesOfScale.csv"
data = pd.read_csv(data_path)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the web application
app.layout = html.Div(
    [
        html.H1("Economies of Scale Visualization"),
        dcc.Graph(id="scatter-plot"),
    ]
)


# Define callback to update graph
@app.callback(
    dash.dependencies.Output("scatter-plot", "figure"),
    [dash.dependencies.Input("scatter-plot", "hoverData")],
)
def update_graph(hoverData):
    fig = px.scatter(
        data,
        x="Number of Units",
        y="Manufacturing Cost",
        title="Manufacturing Cost vs. Number of Units",
    )
    return fig


# Run the application
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
