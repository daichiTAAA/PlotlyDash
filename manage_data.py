import os
import io
import base64
import dash
from dash import html, dcc, dash_table, Input, Output, State
import pandas as pd

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Upload(
            id="upload-data", children=html.Button("Upload File"), multiple=False
        ),
        html.Div(id="output-data-upload"),
        dcc.Input(id="filter-input", type="text", placeholder="Filter files..."),
        html.Div(id="file-list"),
    ]
)


@app.callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def upload_file(contents, filename):
    if contents is None:
        return "Please upload a file."

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        if "csv" in filename:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            df.to_parquet(
                f"./parquet_files/{filename.replace('.csv', '.parquet')}",
                engine="pyarrow",
            )
            return "File uploaded and saved as a Parquet file!"
        else:
            return "Unsupported file type. Please upload a CSV file."
    except Exception as e:
        return f"Error processing file: {str(e)}"


@app.callback(
    Output("file-list", "children"),
    [Input("output-data-upload", "children"), Input("filter-input", "value")],
)
def update_file_list(upload_message, filter_value):
    parquet_files_path = "./parquet_files"

    if not os.path.exists(parquet_files_path):
        return "No files uploaded yet."

    parquet_files = [
        f for f in os.listdir(parquet_files_path) if f.endswith(".parquet")
    ]

    # Apply filtering if filter_value is not None and not empty
    if filter_value:
        parquet_files = [f for f in parquet_files if filter_value.lower() in f.lower()]

    file_list_components = []

    for fname in parquet_files:
        df = pd.read_parquet(f"{parquet_files_path}/{fname}")

        table_preview = dash_table.DataTable(
            data=df.head(5).to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
        )

        file_list_components.append(
            html.Div(
                [html.H5(fname), table_preview],
                style={
                    "border": "1px solid black",
                    "margin-bottom": "10px",
                    "padding": "10px",
                },
            )
        )

    return file_list_components


if __name__ == "__main__":
    app.run_server(debug=True)
