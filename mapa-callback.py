import dash
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import json
import plotly.graph_objects as go

from dash.dependencies import Input, Output

from urllib.request import urlopen

app = dash.Dash(__name__)
server = app.server

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                   dtype={"fips": str})

data = go.Choroplethmapbox(geojson=counties,
                           locations=df.fips,
                           z=df.unemp,
                           colorscale="Viridis",
                           zmin=0,
                           zmax=12,
                           marker_opacity=0.5,
                           marker_line_width=0)

layout = go.Layout(mapbox_style="carto-positron",
                   mapbox_zoom=3,
                   mapbox_center={"lat": 37.0902, "lon": -95.7129},
                   margin={"r": 0, "t": 0, "l": 0, "b": 0})


figure = go.Figure(data=data, layout=layout)


num_clics = []



app.layout= html.Div(dcc.Graph(id='map', figure=figure), id='map-container')

@app.callback(Output('map', 'figure'),
              [Input('map', 'clickData'),
               Input('map-container', 'n_clicks')])

def select_ageb(clickData, n_clicks):
    num_clics.append(n_clicks)
    print(num_clics)


if __name__ == '__main__':
    app.run_server(debug=True)
