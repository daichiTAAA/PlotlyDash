import base64
import io
import traceback

import dash
import dash_bootstrap_components as dbc  # Import Dash Bootstrap components
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress

app = dash.Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP]
)  # Import Bootstrap CSS

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Upload File"),
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
                        "offset": 0,
                    },  # size of the column and offset from the left
                )
            ],
            style={"backgroundColor": "#f8f9fa"},  # Change background color
            className="mb-3 pb-2 shadow",  # padding
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Original Data"),
                        html.Div(id="input-data"),
                    ]
                )
            ],
            style={"backgroundColor": "#f8f9fa"},  # Change background color
            className="mb-3 pb-2 shadow",  # padding
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Transformed Data"),
                        dbc.InputGroup(
                            [
                                dbc.Textarea(
                                    id="transform-code-input",
                                    placeholder="Enter transformation code...",
                                ),
                                dbc.Button("Transform", id="transform-button"),
                            ],
                            className="mb-3",
                        ),
                        html.Div(id="transformed-data"),
                    ]
                ),
            ],
            style={"backgroundColor": "#f8f9fa"},  # Change background color
            className="mb-3 pb-2 shadow",  # padding
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Visualize Data"),
                        dbc.InputGroup(
                            [
                                dbc.Textarea(
                                    id="plotly-code-input",
                                    placeholder="Enter Plotly code...",
                                ),
                                dbc.Button("Plot", id="plot-button"),
                            ],
                            className="mb-3",
                        ),
                        html.Div(id="plot-output-status"),
                        dcc.Graph(id="plot-output"),
                    ],
                    className="mb-3",
                )
            ],
            style={"backgroundColor": "#f8f9fa"},  # Change background color
            className="mb-3 pb-2 shadow",  # padding
        ),
    ],
    className="p-5",  # padding
)

global_df = None  # A global variable to hold the transformed dataframe


def parse_contents(contents):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.read_csv(io.StringIO(decoded.decode("utf-8")))


@app.callback(
    Output("input-data", "children"),
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
)
def update_input(contents, filename):
    global global_df
    if contents is None:
        return
    df = parse_contents(contents)
    global_df = df.copy()
    df = df.iloc[:5, :]
    return html.Div(
        [
            html.H6(f"File: {filename}"),  # Display filename
            html.Pre(df.head().to_string(index=False)),
            html.H6(f"Ask about Original Data"),
            dbc.InputGroup(
                [
                    dbc.Textarea(
                        id="question-original-data",
                        placeholder="Enter question about original data...",
                    ),
                    dbc.Button("Ask", id="question-original-data-button"),
                ],
                className="mb-3",
            ),
            dbc.Textarea(
                id="answer-original-data",
                placeholder="Answer...",
            ),
        ]
    )


@app.callback(
    Output("transformed-data", "children"),
    [Input("transform-button", "n_clicks")],
    [
        State("upload-data", "contents"),
        State("transform-code-input", "value"),
    ],
)
def update_transform(n, contents, code):
    global global_df
    if n is None or contents is None or code is None:
        return
    local_vars = {"df": global_df}  # Create a dictionary to hold local variables
    print(code)
    try:
        exec(code, globals(), local_vars)  # Execute the transformation code
    except Exception as e:
        error_message = f"{str(e)}\n\n{traceback.format_exc()}"
        return html.Div(
            [
                html.H5("Error"),
                html.Pre(error_message),
            ]
        )
    global_df = local_vars["df"]  # Update the global dataframe from the local variables
    print(global_df.head())
    return html.Div(
        [
            html.Pre(global_df.head().to_string(index=False)),
            html.H6(f"Ask about Transformed Data"),
            dbc.InputGroup(
                [
                    dbc.Textarea(
                        id="question-transformed-data",
                        placeholder="Enter question about transformed data...",
                    ),
                    dbc.Button("Ask", id="question-transformed-data-button"),
                ],
                className="mb-3",
            ),
            dbc.Textarea(
                id="answer-transformed-data",
                placeholder="Answer...",
            ),
        ]
    )


@app.callback(
    [Output("plot-output-status", "children"), Output("plot-output", "figure")],
    [Input("plot-button", "n_clicks")],
    [State("plotly-code-input", "value")],
)
def update_graph(n, code):
    global global_df
    if n is None or code is None or global_df is None:
        return (html.Div(), go.Figure())
    local_vars = {"df": global_df, "fig": None}
    try:
        exec(code, globals(), local_vars)  # Execute the plotting code
    except Exception as e:
        error_message = f"{str(e)}\n\n{traceback.format_exc()}"
        return (
            html.Div(
                [
                    html.H5("Error"),
                    html.Pre(error_message),
                ]
            ),
            go.Figure(),
        )
    return (html.Div(), local_vars["fig"])


if __name__ == "__main__":
    app.run_server(debug=True)
