import dash
import dash_html_components as html
import geopandas as gpd
import json
import plotly.graph_objs as go

# Inicio de app en Dash
app = dash.Dash(__name__)

# Inicio de servidor
server = app.server

# Personalización del template de html (head, footer, favicon, etc.)
app.index_string= '''
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css?family=Raleway:300,400,500,600&display=swap" rel="stylesheet">
        <meta charset= "UTF-8">
        <title>Ecobici</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
    </body>
</html>'''

#---------------------------------CALLBACKS-------------------------------#
primer_ageb= '967'



#--------------------------------- MAPA -----------------------------------#
# Leer el shapefile para coordenadas de los polígonos
geodf= gpd.read_file('/data/production_data/ageb_geometry/ageb_geometria.shp')

# Arreglar ceros a la izquierda
geodf['CVE_AGEB'] = [''.join(filter(lambda x: x.isdigit(), row)) for row in geodf['CVE_AGEB']]
geodf['CVE_AGEB'] = geodf['CVE_AGEB'].astype(int)

# Leer el dataframe para datos de distancias entre agebs
df= pd.read_csv('/data/production_data/distancias_agebs.csv', index_col=0)
df= df.loc[:, df.columns.isin(['CVE_AGEB', primer_ageb])]

# Combinar shapefile con dataframe
geodf= geodf.merge(df, on='CVE_AGEB')
geodf.set_index('CVE_AGEB', inplace=True)
geodf['id']= geodf['CVE_AGEB']

# Convertir geo dataframe en geojson

geodf.to_file('test_uber_json.json', driver= 'GeoJSON')
with open ('test_uber_json.json') as geofile:
    jdata=json.load(geofile)

def check_geojson(jdata):
    if 'id' not in jdata['features'][0].keys():
        if 'properties' in jdata['features'][0].keys():
            if 'id' in jdata['features'][0]['properties'] and jdata['features'][0]['properties']['id'] is not None:
                for k, feat in enumerate(jdata['features']):
                    jdata['features'][k]['id']= feat['properties']['id']
            else:
                for k in range(len(jdata['features'])):
                    jdata['features'][k]['id']= k
    return jdata

jdata= check_geojson(jdata)

# Establecer parámetros de mapa

z = geodf[primer_ageb].tolist()
locations = geodf["CVE_AGEB"].tolist()

trace_mapa= go.Choroplethmapbox(z=z,
                                locations=locations,
                                colorscale='Viridis',
                                geojson=jdata,
                                hoverinfo='all',
                                marker_line_width=0.1,
                                marker_opacity=0.5)

layout_mapa= go.Layout(mapbox= {center: {'lat': 19.410737,
                                         'lon': -99.170879},
                                style: 'carto-positron',
                                zoom: 11.5})

figure_mapa= {'data': trace_mapa,
              'layout': layout_mapa}

#--------------------------------- Layout de la app-------------------------------#
app.layout= html.Div([html.Div([html.Header([html.H1('Ecobici'),
                                            # html.Img(src=app.get_asset_url('github_120.png'))
                                             ],
                                            id='titulo-app', className='titulo-app'),
                                html.Div([dcc.Graph(figure=figure_mapa)],
                                         id='mapa', className='mapa')],
                               id='espacio-mapa', className='espacio-mapa'),
                      html.Div([html.Div(id='edad-genero', className='edad-genero'),
                                html.Div(id='sankey', className='sankey'),
                                html.Div(id='hora-recorrido', className='hora-recorrido')], id= 'espacio-narrativa', className='espacio-narrativa')])

if __name__ == '__main__':
    app.run_server(debug=True)
