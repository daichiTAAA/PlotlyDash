import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Load the data
data_path = "./csv_files/Car Data.csv"
data = pd.read_csv(data_path)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the web application
app.layout = html.Div(
    [
        html.H1("Car Data Visualization"),
        dcc.Dropdown(
            id="column-dropdown",
            options=[{"label": i, "value": i} for i in data.columns],
            value="Brand",
            multi=False,
        ),
        dcc.Graph(id="bar-plot"),
    ]
)


# Define callback to update graph
@app.callback(Output("bar-plot", "figure"), [Input("column-dropdown", "value")])
def update_graph(selected_column):
    if pd.api.types.is_numeric_dtype(data[selected_column]):
        # If the data type is numeric, show a histogram
        fig = px.histogram(
            data, x=selected_column, title=f"Histogram of {selected_column}"
        )
    else:
        # If the data type is categorical, show a bar chart of value counts
        counts = data[selected_column].value_counts().reset_index()
        counts.columns = [selected_column, "count"]  # Explicitly name columns
        fig = px.bar(
            counts,
            x=selected_column,
            y="count",
            title=f"Bar Chart of {selected_column}",
        )
        fig.update_layout(xaxis_title=selected_column, yaxis_title="Count")
    return fig


# Run the application
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
