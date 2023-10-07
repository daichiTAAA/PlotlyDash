import base64
import io
import json
import math
import re

import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_leaflet as dl
import gpxpy
from lxml import etree
import pandas as pd
import plotly.express as px


app = dash.Dash(__name__)

title_div = html.Div(
    children=html.H1("Apple Watch Data Visualization", style={"textAlign": "center"})
)

app.layout = html.Div(
    [
        html.Div(id="title", children=title_div),
        dcc.Upload(
            id="upload-data",
            children=html.Button("ファイルを選択"),
            multiple=False,
            style={"width": "200px", "margin": "auto", "display": "block"},
        ),
        dcc.Dropdown(
            id="time_dropdown",
            options=[
                {"label": "Daily", "value": "D"},
                {"label": "Weekly", "value": "W"},
                {"label": "Monthly", "value": "M"},
                {"label": "Yearly", "value": "Y"},
            ],
            value="M",  # デフォルト値
            style={"width": "200px", "margin": "auto", "display": "block"},
        ),
        dcc.Loading(
            id="loading",
            type="circle",
            children=[
                html.Div(id="output-data-upload"),
                dl.Map(id="map"),
            ],
        ),
        dcc.Interval(
            id="interval-component",
            interval=1 * 1000,  # 1 second intervals
            n_intervals=0,
        ),
        html.Div(
            id="viewport-size", style={"display": "none"}
        ),  # Div to store the viewport size
    ]
)


def extract_device_name(device_info):
    match = re.search(r"name:([^,]+),", str(device_info))
    return match.group(1).strip() if match else None


def add_row_number(df):
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Row Number"}, inplace=True)
    return df


def process_csv(df):
    df = add_row_number(df)
    return df


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    data_str = decoded.decode("utf-8")

    if "csv" in filename:
        # CSVファイルの場合
        delimiter = "\0"
        df = pd.read_csv(io.StringIO(data_str), delimiter=delimiter)
        df = process_csv(df)
    elif "xls" in filename:
        # Excelファイルの場合
        df = pd.read_excel(io.BytesIO(data_str))
    elif "xml" in filename:
        # lxml.etreeを使ってXML文字列を解析
        root = etree.fromstring(decoded)
        data = []
        for item in root.iter():  # iterメソッドを使ってすべてのエレメントを反復処理
            data_elem = {
                "tag": item.tag,
                "text": item.text,
                "attributes": dict(item.attrib),
            }
            data.append(data_elem)
        # データの整形
        df = pd.DataFrame(data)
    elif "gpx" in filename:
        # GPXファイルの場合
        gpx = gpxpy.parse(io.BytesIO(decoded))
        latlon_data = []
        data = []
        for track in gpx.tracks:
            for segment in track.segments:
                segment_data = []
                for point in segment.points:
                    segment_data.append([point.latitude, point.longitude])
                    data.append(
                        {
                            "Latitude": point.latitude,
                            "Longitude": point.longitude,
                            "Elevation": point.elevation,
                        }
                    )
                latlon_data.append(segment_data)
        df = pd.DataFrame(data)
        return df, latlon_data, content_type  # latlon_dataを返す
    else:
        raise Exception("Unsupported file type")
    return df, None, content_type


def calculate_center(positions):
    latitudes = []
    longitudes = []
    for pair in positions:
        latitudes.append(pair[0])
        longitudes.append(pair[1])
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)
    return [center_lat, center_lon]


def calculate_zoom(positions, map_width, map_height):
    latitudes = []
    longitudes = []
    for pair in positions:
        latitudes.append(pair[0])
        longitudes.append(pair[1])
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    map_width_in_tiles = map_width / 256
    map_height_in_tiles = map_height / 256
    zoom_x = math.log(map_width_in_tiles / lon_range) / math.log(2)
    zoom_y = math.log(map_height_in_tiles / lat_range) / math.log(2)
    zoom = min(zoom_x, zoom_y)
    return zoom


@app.callback(
    [
        Output("title", "children"),
        Output("output-data-upload", "children"),
        Output("map", "children"),
    ],
    [Input("upload-data", "contents"), Input("time_dropdown", "value")],
    [
        State("upload-data", "filename"),
        State("viewport-size", "children"),
    ],
)
def update_output(contents, selected_value, filename, viewport_size_json):
    if contents is None:
        return title_div, html.Div(["No data uploaded yet"]), []
    file_info_div = html.Div(f"File: {filename}")
    df, latlon_data, content_type = parse_contents(contents, filename)
    print(f"content_type: {content_type}")
    if latlon_data:
        positions = latlon_data[0]
        center = calculate_center(positions)
        if viewport_size_json:
            viewport_size = json.loads(viewport_size_json)
            map_width = viewport_size["width"]
            map_height = viewport_size["height"] * 0.5  # Convert 50vh to pixels
            zoom = calculate_zoom(positions, map_width, map_height)
        else:
            zoom = 10  # Default zoom level
        return (
            title_div,
            html.Div([file_info_div]),
            dl.Map(
                children=[
                    dl.TileLayer(),
                    dl.Polyline(positions=positions, color="blue"),
                    # dl.Marker(position=center, children=dl.Tooltip("Center")),
                ],
                center=center,
                zoom=zoom,
                style={"height": "50vh", "margin": "auto", "display": "block"},
            ),
        )
    elif "text/csv" in content_type:
        # Row Number列が9以降のデータをフィルタリング
        filtered_df = df[df["Row Number"] >= 9]
        # 名前列をfloat型に変換
        filtered_df["名前"] = filtered_df["名前"].astype(float)
        # 散布図の作成
        fig = px.line(
            filtered_df,
            x="Row Number",
            y="名前",
            title="Line chart for Row Number >= 9",
        )
        return (
            title_div,
            html.Div([file_info_div, dcc.Graph(figure=fig)]),
            [],
        )
    elif "text/xml" in content_type:
        # attributes列の辞書をJSON文字列に変換
        df["attributes"] = df["attributes"].apply(json.dumps)
        # "HKQuantityTypeIdentifierDistanceWalkingRunning"と'unit="km"'を含む行をフィルタリングします。
        df = df[
            (
                df.loc[:, "attributes"].str.contains(
                    "HKQuantityTypeIdentifierDistanceWalkingRunning"
                )
            )
        ]
        # df["attributes"]の要素をjson.loads関数を使用して辞書に変換します。
        df["attributes"] = df["attributes"].apply(json.loads)
        # json_normalize関数を使用して辞書を展開します。
        attribute_list = df["attributes"].values.tolist()
        df = pd.json_normalize(attribute_list)
        # エクスポート
        df.to_parquet(f"./export/{filename}.parquet", engine="pyarrow")
        # 必要な列のみを抽出
        df = df[["startDate", "endDate", "value", "unit", "device"]]
        # csvファイルにエクスポート
        df.to_csv(f"./export/{filename}.csv", index=False)
        # 欠損値の処理
        df = df.dropna(subset=["value"])
        # 'startDate'カラムをdatetime型に変換
        df["startDate"] = pd.to_datetime(df["startDate"], format="%Y-%m-%d %H:%M:%S %z")
        # 日時を指定された形式に変換します。
        df["startDate"] = df["startDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
        # 'value'カラムをfloat型に変換
        df["value"] = df["value"].astype(float)
        # 散布図の作成
        fig_scatter = px.scatter(
            df,
            x="startDate",
            y="value",
            title="Walking Distance Over Time Scatter",
            labels={"value": "(km)", "startDate": "startDate"},
        )
        # デバイスごとにグループ化して縦積み棒グラフを作成
        df["startDate"] = pd.to_datetime(df["startDate"], errors="coerce")
        df["duration"] = df["startDate"].dt.to_period(selected_value)
        df["simple_device"] = df["device"].apply(extract_device_name)
        grouped_df = (
            df.groupby(["duration", "simple_device"])["value"].sum().reset_index()
        )
        # 日時を指定された形式に変換します。
        grouped_df["duration"] = grouped_df["duration"].astype(str)
        # Create a Plotly Express figure
        fig_bar = px.bar(
            grouped_df,
            x="duration",
            y="value",
            color="simple_device",
            title=f"Values per Device ({selected_value})",
            labels={"value": "(km)", "duration": "duration"},
            height=600,
        )
        # Customize aspect of the layout
        fig_bar.update_layout(barmode="stack")
        # 選択された期間でデータをリサンプリング
        df_sum = df[["startDate", "value"]].copy()
        df_sum["startDate"] = pd.to_datetime(
            df_sum["startDate"]
        )  # startDate列を再度日時形式に変換
        df_sum.set_index("startDate", inplace=True)  # startDate列をインデックスに設定
        resampled_data = df_sum.resample(selected_value).sum()
        resampled_data.reset_index(inplace=True)  # インデックスをリセットして新しい'startDate'列を作成

        # プロットの作成
        fig_sum = px.line(
            resampled_data,
            x="startDate",
            y="value",
            title=f"Walking Distance Over Time ({selected_value})",
            labels={"value": "(km)", "startDate": "startDate"},
        )

        return (
            title_div,
            html.Div(
                [
                    file_info_div,
                    dcc.Graph(figure=fig_sum),
                    dcc.Graph(figure=fig_scatter),
                    dcc.Graph(figure=fig_bar),
                ]
            ),
            [],
        )
    else:
        return (
            title_div,
            html.Div(
                [
                    file_info_div,
                    dash_table.DataTable(
                        data=df.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in df.columns],
                        page_size=1000,
                    ),
                ]
            ),
            [],
        )


app.clientside_callback(
    """
    function updateViewportSize(n_intervals) {
        var viewportWidth = window.innerWidth;
        var viewportHeight = window.innerHeight;
        return JSON.stringify({width: viewportWidth, height: viewportHeight});
    }
    """,
    Output("viewport-size", "children"),
    Input("interval-component", "n_intervals"),
)

if __name__ == "__main__":
    app.run_server(debug=True)
