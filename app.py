import dash
import dash_core_components as dcc
import dash_html_components as html
import geopandas as gpd
import pandas as pd
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
primer_ageb= 790
primer_ageb_str= str(primer_ageb)
segundo_ageb= 822



#--------------------------------- MAPA -----------------------------------#
# Leer shapefile y csv
geodf= gpd.read_file('./data/production_data/ageb_geometry/ageb_geometria.shp')
df_mapa= pd.read_csv('./data/production_data/distancias_agebs.csv', index_col=0)

# Corregir ceros a la izquierda
geodf['CVE_AGEB'] = [''.join(filter(lambda x: x.isdigit(), row)) for row in geodf['CVE_AGEB']]
geodf['CVE_AGEB'] = geodf['CVE_AGEB'].astype(int)

# Reestructurar el dataframe con el ageb seleccionado
df_mapa= df_mapa.loc[:, df_mapa.columns.isin(['CVE_AGEB', primer_ageb_str])]

# Unir ambos dataframes
geodf = geodf.merge(df_mapa, on='CVE_AGEB')
#geodf.set_index('CVE_AGEB', inplace=True)
geodf['id'] = geodf['CVE_AGEB']

# Convertir geodataframe en geo json y checar su estructura
geodf.to_file('./data/production_data/ageb_geometry/ageb_geometria.json', driver= 'GeoJSON')
with open ('./data/production_data/ageb_geometry/ageb_geometria.json') as geofile:
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

jdata = check_geojson(jdata)

# Establecer parámetros del mapa

z = geodf[primer_ageb_str].tolist()
locations = geodf['CVE_AGEB'].tolist()

# Dibujar mapa
trace_mapa = go.Choroplethmapbox(z = z,
                                 locations=locations,
                                 colorscale= 'Viridis',
                                 colorbar= {'thicknessmode': 'pixels',
                                            'thickness': 7,
                                            'outlinecolor': 'white',
                                            'title': {'text': 'km',
                                                      'side': 'bottom'}},
                                 reversescale=True,
                                 geojson=jdata,
                                 hoverinfo= 'location',
                                 marker_line_width=0.1,
                                 marker_opacity=0.5)

layout_mapa= go.Layout(mapbox= {'center': {'lat': 19.404730,
                                           'lon': -99.172845},
                                'style': 'carto-positron',
                                'zoom': 12},
                       margin= {'l': 0,
                                'r': 0,
                                't': 5,
                                'b': 0})

figure_mapa= go.Figure(data=[trace_mapa], layout=layout_mapa)

#-----------------------------------SANKEY----------------------------------------#

# Leer archivo para datos de sankey
df_sankey= pd.read_csv('./data/production_data/viajes_ecobici_entre_estaciones.csv')

# Filtrar dataframe
df_sankey= df_sankey[(df_sankey['CVE_AGEB_retiro']==primer_ageb) & (df_sankey['CVE_AGEB_arribo']==segundo_ageb)]

# Estructura de sankey
estaciones_retiro= df_sankey['nombre_estacion_retiro'].unique().tolist()
estaciones_arribo= df_sankey['nombre_estacion_arribo'].unique().tolist()

label= estaciones_retiro + estaciones_arribo

indices_retiro= list(range(len(estaciones_retiro)))
indices_arribo= list(range(len(estaciones_retiro), len(label)))

source= indices_retiro*len(indices_arribo)

def duplicate_target(indices_arribo, n):
    return [element for element in indices_arribo for _ in range(n)]

target= duplicate_target(indices_arribo, len(indices_retiro))

value= df_sankey['Numero_de_viajes'].tolist()

# Dibujar sankey

data_sankey= go.Sankey(node= {'pad': 15,
                              'thickness': 20,
                              'line': {'color': 'black',
                                       'width': 0.5},
                              'label': label,
                              'color': 'blue'},
                       link= {'source': source,
                              'target': target,
                              'value': value})

layout_sankey=go.Layout(title_text= 'Sankey')

figure_sankey= go.Figure(data= data_sankey, layout= layout_sankey)

#--------------------------------- Big number y porcentaje por género------------------------------------#

#Leer archivo de viajes de ecobici
df_ve= pd.read_csv('./data/production_data/viajes_ecobici.csv')
df_ve['Hora_Retiro_bin']=df_ve['Hora_Retiro_bin_']

df_ve= df_ve[(df_ve['CVE_AGEB_retiro_']==primer_ageb) & (df_ve['CVE_AGEB_arribo_']==segundo_ageb)]

#Establecer variable para la edad promedio del usuario
edad_promedio_usuario= int(round(df_ve['Edad_Usuario_mean'].mean()))


def nombre_archivo_cascos():
    """
    Mostrar una imagen dependiendo del porcentaje de hombres y mujeres que hacen viajes en ecobici entre agebs
    """
    query_genero = df_ve[["porcentage_hombres", "porcentage_mujeres"]].mean().round().astype(int)
    numero_hombres = query_genero[0]

    if numero_hombres == 0:
        archivo = "10m-0h.png"
    elif numero_hombres == 1:
        archivo = "9m-1h.png"
    elif numero_hombres == 2:
        archivo = "8m-2h.png"
    elif numero_hombres == 3:
        archivo = "7m-3h.png"
    elif numero_hombres == 4:
        archivo = "6m-4h.png"
    elif numero_hombres == 5:
        archivo = "5m-5h.png"
    elif numero_hombres == 6:
        archivo = "4m-6h.png"
    elif numero_hombres == 7:
        archivo = "3m-7h.png"
    elif numero_hombres == 8:
        archivo = "2m-8h.png"
    elif numero_hombres == 9:
        archivo = "1m-9h.png"
    elif numero_hombres == 10:
        archivo = "0m-1h.png"

    return str("cascos/" + archivo)

porcentaje_genero= str(nombre_archivo_cascos())

#---------------------------------Grafica de barras-------------------------------#

# Datos uber
df_uber = pd.read_csv('./data/production_data/viajes_uber.csv')

# Asignar bote
def asignar_bote(df, columna= 'Hora_Retiro_bin'):
    if df[columna]=='7-10':
        return 0
    if df[columna]=='10-13':
        return 1
    if df[columna]=='13-16':
        return 2
    if df[columna]=='16-19':
        return 3
    if df[columna]=='19-22':
        return 4
    if df[columna]=='22-1':
        return 5

# Asignar columna de periodo y reordenar dataframes
df_uber['periodo']= df_uber.apply(asignar_bote, axis=1)
df_ve['periodo']= df_ve.apply(asignar_bote, axis=1)

# Filtrar datos
df_uber = df_uber[(df_uber['sourceid'] == primer_ageb) & (df_uber['dstid'] == segundo_ageb)]

df_uber= df_uber.sort_values(by='periodo', ascending=True)
df_ve= df_ve.sort_values(by='periodo', ascending=True)

# Establecer datos en x y y
x_uber=df_uber['Hora_Retiro_bin']
y_uber=df_uber['mean_travel_time']
x_ecobici=df_ve['Hora_Retiro_bin']
y_ecobici=df_ve['duracion_viaje_minutos_mean']

#Datos y layout
data_bar= [go.Bar(name= 'ecobici',x=x_ecobici,y=y_ecobici),
           go.Bar(name= 'uber', x=x_uber, y=y_uber)]

layout_bar= go.Layout(xaxis= {'type': 'category'})

figure_bar= go.Figure(data=data_bar, layout= layout_bar)

#--------------------------------- Layout de la app-------------------------------#
# app.layout= html.Div([html.Div([html.Header([html.H1('Ecobici'),
#                                             html.Img(src=app.get_asset_url('github_120.png'))],
#                                             id='titulo-app', className='titulo-app'),
#                                 html.Div([dcc.Graph(figure=figure_mapa)],
#                                          id='mapa', className='mapa')],
#                                id='espacio-mapa', className='espacio-mapa'),
#                       html.Div([html.Div([html.H2(edad_promedio_usuario),
#                                           html.Img(src=app.get_asset_url(porcentaje_genero), alt='porcentaje_genero', className='genero')]
#                                          ,id='edad-genero', className='edad-genero'),
#                                 html.Div([dcc.Graph(figure=figure_sankey)],id='sankey', className='sankey'),
#                                 html.Div([dcc.Graph(figure=figure_bar)],id='hora-recorrido', className='hora-recorrido')], id= 'espacio-narrativa', className='espacio-narrativa')])

estilo_graficas= {'responsive': True,
                  'autosizable': True,
                  'displaylogo': False}

app.layout= html.Div([html.Header([html.Div([html.H1('Ecobici')], id='titulo-app', className='titulo-app'),
                                   html.A([html.Img(src=app.get_asset_url('github.png'), alt='logo github',
                                                    className='logo-github')], href='https://github.com/paupradel/ecobici_viz')]),
                      html.Div([dcc.Graph(figure=figure_mapa, id='mapa', className='mapa', config=estilo_graficas),
                                html.Div([html.P('Edad'),
                                          html.H1(edad_promedio_usuario, className='edad')], id='edades', className='mini_container-grid-2'),
                                html.Div([html.P('Género', className='titulo-genero'),
                                          html.Img(src=app.get_asset_url(porcentaje_genero), id='genero', alt='porcentaje_genero', className='imagen-genero')],
                                         id='genero-cont', className='genero'),
                                dcc.Graph(figure=figure_sankey, id='sankey', className='sankey', config=estilo_graficas),
                                dcc.Graph(figure=figure_bar, id='hora_recorrido', className='hora_recorrido', config=estilo_graficas)], className='contenedor-ecobici')
                      ])




if __name__ == '__main__':
    app.run_server(debug=True)
