import dash
import dash_bootstrap_components as dbc  # Import Dash Bootstrap components
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io

app = dash.Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP]
)  # Import Bootstrap CSS

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
                            },  # Changed style to display button
                        ),
                        dbc.FormText("Choose a CSV file to upload.", className="mt-2"),
                    ],
                    width={
                        "size": 6,
                        "offset": 3,
                    },  # size of the column and offset from the left
                )
            ]
        ),
        html.Div(id="output-data-upload"),
        dbc.InputGroup(
            [
                dbc.Input(
                    id="plotly-code-input",
                    type="text",
                    placeholder="Enter Plotly code...",
                ),
                dbc.Button("Plot", id="plot-button"),
            ],
            className="mb-3",
        ),
        dcc.Graph(id="plot-output"),
    ],
    className="p-5",  # padding
)


def parse_contents(contents):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.read_csv(io.StringIO(decoded.decode("utf-8")))


@app.callback(
    Output("output-data-upload", "children"),
    [Input("upload-data", "contents")],
)
def update_output(contents):
    if contents is None:
        return
    df = parse_contents(contents)
    return html.Div([html.H5("Data"), html.Pre(df.head().to_string(index=False))])


@app.callback(
    Output("plot-output", "figure"),
    [Input("plot-button", "n_clicks")],
    [
        State("upload-data", "contents"),
        State("plotly-code-input", "value"),
    ],
)
def update_graph(n, contents, code):
    if n is None or contents is None or code is None:
        return go.Figure()
    df = parse_contents(contents)
    exec(code, globals(), locals())
    return locals()["fig"]


if __name__ == "__main__":
    app.run_server(debug=True)
