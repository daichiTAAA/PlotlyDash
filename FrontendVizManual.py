import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)


app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Upload(
                            id="upload-data",
                            children=dbc.Button(
                                "Upload File",
                                id="upload-data-button",
                                className="mr-2",
                            ),
                            style={
                                "display": "inline-block",
                            },
                        ),
                        dbc.FormText("Choose a CSV file to upload.", className="mt-2"),
                    ],
                    width={
                        "size": 6,
                        "offset": 3,
                    },
                )
            ]
        ),
        html.Div(id="output-data-upload"),
        dbc.InputGroup(
            [
                dbc.Select(
                    id="column-select",
                    options=[],
                    value=None,
                ),
                dbc.RadioItems(
                    id="agg-select",
                    options=[
                        {"label": "Sum", "value": "sum"},
                        {"label": "Mean", "value": "mean"},
                    ],
                    value="sum",
                    inline=True,
                ),
                dbc.RadioItems(
                    id="graph-select",
                    options=[
                        {"label": "Bar", "value": "bar"},
                        {"label": "Line", "value": "line"},
                    ],
                    value="bar",
                    inline=True,
                ),
                dbc.Button("Plot", id="plot-button"),
            ],
            className="mb-3",
        ),
        dcc.Graph(id="plot-output"),
    ],
    className="p-5",
)


def parse_contents(contents):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.read_csv(io.StringIO(decoded.decode("utf-8")))


@app.callback(
    dash.dependencies.Output("output-data-upload", "children"),
    [dash.dependencies.Input("upload-data", "contents")],
)
def update_output(contents):
    if contents is None:
        return
    df = parse_contents(contents)
    columns = [{"label": col, "value": col} for col in df.columns]
    return html.Div(
        [
            html.H5("Data"),
            html.Pre(df.head().to_string(index=False)),
            dcc.Store(id="column-options", data=columns),
        ]
    )


@app.callback(
    dash.dependencies.Output("column-select", "options"),
    [dash.dependencies.Input("column-options", "data")],
)
def update_column_options(columns):
    return columns


@app.callback(
    dash.dependencies.Output("plot-output", "figure"),
    [dash.dependencies.Input("plot-button", "n_clicks")],
    [
        dash.dependencies.State("upload-data", "contents"),
        dash.dependencies.State("column-select", "value"),
        dash.dependencies.State("agg-select", "value"),
        dash.dependencies.State("graph-select", "value"),
    ],
)
def update_graph(n, contents, column, agg, graph_type):
    if n is None or contents is None or column is None:
        return go.Figure()
    df = parse_contents(contents)

    # Ensure the column data is numeric
    try:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    except Exception as e:
        return html.Div(f"Error: Unable to convert column data to numeric. {e}")
    if agg == "sum":
        agg_df = df.groupby(column).sum().reset_index()
    else:
        agg_df = df.groupby(column).mean().reset_index()
    if graph_type == "bar":
        fig = px.bar(agg_df, x=column, y=agg_df.columns[1])
    else:
        fig = px.line(agg_df, x=column, y=agg_df.columns[1])
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
