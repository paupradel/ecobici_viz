import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from tools.funciones import quitar_ceros, obtenergeo_json_df

# Inicio de app en Dash
app = dash.Dash(__name__)

# Inicio de servidor
server = app.server

# Personalización del template de html (head, footer, favicon, etc.)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css?family=Raleway:300,400,500,600&display=swap" rel="stylesheet">
        <link href="/assets/css/all.css" rel="stylesheet">
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

# ---------------------------------CALLBACKS-------------------------------#
ageb_inicial_default = 70
ageb_final_default = 11

# Leer shapefile y csv
geodataframe = gpd.read_file('./data/production_data/ageb_geometry/ageb_geometria.shp')
dataframe = pd.read_csv('./data/production_data/distancias_agebs.csv', index_col=0)
df_ve = pd.read_csv('./data/production_data/viajes_ecobici.csv')

# ---------------------- ESTRUCTURACIÓN DE DATAFRAMES-----------------------#
df_ve['Hora_Retiro_bin'] = df_ve['Hora_Retiro_bin_']
geodataframe = quitar_ceros(geodataframe, 'CVE_AGEB')


# ---------------------------------MAPA--------------------------------------#

def dibujar_mapa(primer_ageb):
    primer_ageb_str = str(primer_ageb)
    geodf_jdata = obtenergeo_json_df(dataframe, geodataframe, 'CVE_AGEB', primer_ageb)

    geodf = geodf_jdata[0]
    jdata = geodf_jdata[1]

    z = geodf[primer_ageb_str].tolist()

    locations = geodf['CVE_AGEB'].tolist()

    trace_mapa = go.Choroplethmapbox(z=z,
                                     locations=locations,
                                     colorscale='magma',
                                     colorbar={'thicknessmode': 'pixels',
                                               'thickness': 7,
                                               'outlinecolor': 'white',
                                               'title': {'text': 'km',
                                                         'side': 'bottom'}},
                                     reversescale=True,
                                     geojson=jdata,
                                     hoverinfo='location',
                                     marker_line_width=0.1,
                                     marker_opacity=0.7)

    layout_mapa = go.Layout(mapbox={'center': {'lat': 19.404730,
                                               'lon': -99.172845},
                                    'style': 'carto-positron',
                                    'zoom': 12},
                            margin={'l': 0,
                                    'r': 0,
                                    't': 5,
                                    'b': 15},
                            clickmode='event+select')

    figura_mapa = go.Figure(data=[trace_mapa], layout=layout_mapa)

    return figura_mapa


figure_mapa = dibujar_mapa(ageb_inicial_default)


# -----------------------------------SANKEY----------------------------------------#
def duplicate_target(indices_arribo, n):
    return [element for element in indices_arribo for _ in range(n)]


def dibujar_sankey(primer_ageb, segundo_ageb):
    # Leer archivo para datos de sankey
    df_sankey = pd.read_csv('./data/production_data/viajes_ecobici_entre_estaciones.csv')

    # Filtrar dataframe
    df_sankey = df_sankey[
        (df_sankey['CVE_AGEB_retiro'] == primer_ageb) & (df_sankey['CVE_AGEB_arribo'] == segundo_ageb)]

    # Estructura de sankey
    estaciones_retiro = df_sankey['nombre_estacion_retiro'].unique().tolist()
    estaciones_arribo = df_sankey['nombre_estacion_arribo'].unique().tolist()

    label = estaciones_retiro + estaciones_arribo

    indices_retiro = list(range(len(estaciones_retiro)))
    indices_arribo = list(range(len(estaciones_retiro), len(label)))

    source = indices_retiro * len(indices_arribo)

    target = duplicate_target(indices_arribo, len(indices_retiro))

    value = df_sankey['Numero_de_viajes'].tolist()

    # Dibujar sankey

    data_sankey = go.Sankey(node={'pad': 15,
                                  'thickness': 10,
                                  'line': {'color': 'black',
                                           'width': 0.5},
                                  'label': label,
                                  'color': '#00b386'},
                            link={'source': source,
                                  'target': target,
                                  'value': value},
                            textfont={'family': 'Raleway'})

    layout_sankey = go.Layout(title_text='Viajes entre estaciones (retiro a arribo)',
                              font={'family': 'Raleway'},
                              margin={'l': 0,
                                      'r': 5,
                                      't': 25,
                                      'b': 5},
                              plot_bgcolor='#f9f9f9')

    figure_sankey = go.Figure(data=data_sankey, layout=layout_sankey)

    return (figure_sankey)


figure_sankey = dibujar_sankey(ageb_inicial_default, ageb_final_default)


# --------------------------------- Big number y porcentaje por género------------------------------------#

# Leer archivo de viajes de ecobici
def edad(primer_ageb, segundo_ageb, df_ve=df_ve):
    df_ve = df_ve[(df_ve['CVE_AGEB_retiro_'] == primer_ageb) & (df_ve['CVE_AGEB_arribo_'] == segundo_ageb)]

    if len(df_ve.Edad_Usuario_mean.value_counts() > 0):
        edad_promedio_usuario = int(round(df_ve['Edad_Usuario_mean'].mean()))
        return edad_promedio_usuario
    else:
        edad_promedio_usuario = float('NaN')
        return edad_promedio_usuario


def nombre_archivo_cascos(primer_ageb, df_ve=df_ve):
    """
    Mostrar una imagen dependiendo del porcentaje de hombres y mujeres que hacen viajes en ecobici entre agebs
    """

    df_ve = df_ve[df_ve['CVE_AGEB_retiro_'] == primer_ageb]
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

    porcentaje_genero = app.get_asset_url("cascos/" + archivo)
    return porcentaje_genero


obtener_cascos = nombre_archivo_cascos(ageb_inicial_default)

edad_seleccion = edad(ageb_inicial_default, ageb_final_default)


# ---------------------------------Grafica de barras-------------------------------#

# Asignar bote
def asignar_bote(df, columna='Hora_Retiro_bin'):
    if df[columna] == '7-10':
        return 0
    if df[columna] == '10-13':
        return 1
    if df[columna] == '13-16':
        return 2
    if df[columna] == '16-19':
        return 3
    if df[columna] == '19-22':
        return 4
    if df[columna] == '22-1':
        return 5


def dibujar_barras(primer_ageb, segundo_ageb, df_ve=df_ve):
    # Datos uber
    df_uber = pd.read_csv('./data/production_data/viajes_uber.csv')

    # Asignar columna de periodo y reordenar dataframes
    df_uber['periodo'] = df_uber.apply(asignar_bote, axis=1)
    df_ve['periodo'] = df_ve.apply(asignar_bote, axis=1)

    # Filtrar datos
    df_uber = df_uber[(df_uber['sourceid'] == primer_ageb) & (df_uber['dstid'] == segundo_ageb)]
    df_ve = df_ve[(df_ve['CVE_AGEB_retiro_'] == primer_ageb) & (df_ve['CVE_AGEB_arribo_'] == segundo_ageb)]

    df_uber = df_uber.sort_values(by='periodo', ascending=True)
    df_ve = df_ve.sort_values(by='periodo', ascending=True)

    # Establecer datos en x y y
    x_uber = df_uber['Hora_Retiro_bin']
    y_uber = df_uber['mean_travel_time']
    x_ecobici = df_ve['Hora_Retiro_bin']
    y_ecobici = df_ve['duracion_viaje_minutos_mean']

    # Datos y layout
    data_bar = [go.Bar(name='ecobici', x=x_ecobici, y=y_ecobici, marker_color='#00b386'),
                go.Bar(name='uber', x=x_uber, y=y_uber, marker_color='purple')]

    layout_bar = go.Layout(title_text='Auto VS Bicicleta',
                           barmode='group',
                           xaxis={'type': 'category',
                                  'title': 'periodo del día',
                                  'titlefont_size': 12},
                           yaxis={'title': 'tiempo en minutos',
                                  'titlefont_size': 12},
                           font={'family': 'Raleway'},
                           margin={'l': 5,
                                   'r': 5,
                                   't': 25,
                                   'b': 8},
                           plot_bgcolor='#f9f9f9')

    figure_bar = go.Figure(data=data_bar, layout=layout_bar)

    return figure_bar


figure_bar = dibujar_barras(ageb_inicial_default, ageb_final_default)

# ---------------------------------------------------------------------------------------------------------------------#

click_data_inicial = {
    'points': [{'curveNumber': 0, 'pointNumber': 103, 'pointIndex': 103, 'location': ageb_inicial_default, 'z': 3.67}]}

# ------------------------------------------------- MODAL WINDOWS -----------------------------------------------------#

contenido_pop_up_0 = '¡Bienvenido!'

contenido_pop_up_1 = 'En este sitio encontrarás los lugares de la Ciudad de México donde opera el programa Ecobici. ' \
                     'Cada sección del mapa está divido en un AGEB (Área GeoEstadística Básica) y congrega las colonias ' \
                     'donde se encuentran distintas cicloestaciones de ecobici.'

contenido_pop_up_2 = 'Haz click en un AGEB para conocer la edad promedio y porcentaje de género de los usuarios. Puedes ' \
                     'dar click en otra AGEB para encontrar el número de viajes que se realizaron entre las estaciones ' \
                     'de las AGEBs seleccionadas. También podrás comparar el tiempo de viaje (en minutos) entre un auto y ' \
                     'una bicicleta de las AGEBs elegidas (si es que hay datos).'

contenido_pop_up_3 = 'Para encontrar el listado de estaciones que hay en cada AGEB puedes dar click' + ' '

contenido_pop_up_4 = 'El mapa tiene dos AGEBs elegidas por default, la 70 como punto de partida, y la 11 como punto ' \
                     'de llegada. Al seleccionar una tercer AGEB entonces tu punto de partida será la AGEB 11 y el de ' \
                     'llegada la AGEB que hayas elegido. Así sucesivamente podrás conocer la información de todas las ' \
                     'AGEB que hay en el programa.'

contenido_pop_up_5 = 'Si tienes alguna sugerencia o problema con esta aplicación web, nos puedes escribir a ' \
                     'pradel.paulina@gmail.com, o bien puedes levantar un "issue" en el repositorio de github ' \
                     'de este proyecto.'

contenido_pop_up_6 = '¡Gracias!'

modal_content = [html.H1(contenido_pop_up_0),
                 html.P(contenido_pop_up_1),
                 html.P(contenido_pop_up_2),
                 html.P([contenido_pop_up_3,
                         html.A('aquí',
                                href='https://docs.google.com/spreadsheets/d/1s16phPf9PjVXzgqwWSm2sfDq5vrvaq6LGNfSCs_O8hs/edit?usp=sharing')]),
                 html.P(contenido_pop_up_4),
                 html.P(contenido_pop_up_5),
                 html.H2(contenido_pop_up_6)]

# ---------------------------------------------------LAYOUT APP--------------------------------------------------------#
estilo_graficas = {'responsive': True,
                   'autosizable': True,
                   'displaylogo': False}

# app.layout = html.Div([html.Div(html.Div([html.Div([html.H1(contenido_pop_up_0),
#                                                     html.P(contenido_pop_up_1),
#                                                     html.P(contenido_pop_up_2),
#                                                     html.P([contenido_pop_up_3,
#                                                             html.A('aquí', href='https://www.sopitas.com/')]),
#                                                     html.P(contenido_pop_up_4),
#                                                     html.P(contenido_pop_up_5),
#                                                     html.H2(contenido_pop_up_6)]),
#                                           html.Hr(),
#                                           html.Button('Ir a la aplicación', id='modal-close-button',
#                                                       className='modal-close-button')],
#                                          id='modal-content',
#                                          className='modal-content'),
#                                 id='modal',
#                                 className='modal'),
#                        dcc.Store(id='memory'),
#                        html.Header([html.Div([html.Button([html.Div(className='bar1'),
#                                                            html.Div(className='bar2'),
#                                                            html.Div(className='bar3')],
#                                                           id='myBtn', className='dropbtn'),
#                                               html.Div(
#                                                   [html.Button(html.Span('Instrucciones'), id='instrucciones_button',
#                                                                n_clicks_timestamp=0, className='button'),
#                                                    html.Button(html.Span('Cicloestaciones'),
#                                                                id='cicloestaciones_button', n_clicks_timestamp=0,
#                                                                className='button')], id='myDropdown',
#                                                   className='dropdown-content')], className='dropdown'),
#                                     html.Div([html.H1('¿Ecobici o Auto? Que te conviene más')], id='titulo-app',
#                                              className='titulo-app'),
#                                     html.A([html.Img(src=app.get_asset_url('github.png'), alt='logo github',
#                                                      className='logo')],
#                                            href='https://github.com/paupradel/ecobici_viz')]),
#                        html.Div(
#                            [html.Div(dcc.Graph(figure=figure_mapa, id='mapa-graph', className='mapa-graph',
#                                                clickData=click_data_inicial,
#                                                config=estilo_graficas), id='mapa', className='mapa'),
#                             html.Div([html.P('Edad'),
#                                       html.H1(edad_seleccion, id='edad', className='edad')], id='edades',
#                                      className='mini_container-grid-2'),
#                             html.Div([html.P('Género', className='titulo-genero'),
#                                       html.Img(src=obtener_cascos, id='genero', alt='porcentaje_genero',
#                                                className='imagen-genero')],
#                                      id='genero-cont', className='genero'),
#                             html.Div(dcc.Graph(figure=figure_sankey, id='sankey', className='sankey-graph',
#                                                config=estilo_graficas),
#                                      className='sankey'),
#                             html.Div(dcc.Graph(figure=figure_bar, id='hora_recorrido', className='hora-recorrido-graph',
#                                                config=estilo_graficas),
#                                      className='hora-recorrido')],
#                            className='contenedor-ecobici')
#                        ])


app.layout = html.Div([html.Div(html.Div([html.Div(modal_content),
                                          html.Hr(),
                                          html.Button('Ir a la aplicación', id='modal-close-button',
                                                      className='modal-close-button')],
                                         id='modal-content',
                                         className='modal-content'),
                                id='modal_1',
                                className='modal'),
                       dcc.Store(id='memory'),
                       html.Header([html.Div([html.H1('¿Ecobici o Auto? Que te conviene más')], id='titulo-app',
                                             className='titulo-app'),
                                    html.Div([html.Div(
                                        [html.I(id='instrucciones_button', n_clicks=0,
                                                className='fas fa-info-circle fa-2x'),
                                         dbc.Modal([dbc.ModalBody(modal_content),
                                                    html.Hr(),
                                                    dbc.ModalFooter(dbc.Button('Ir a la aplicación', id='close_2',
                                                                               className='modal-close-button'))],
                                                   id='modal_2')]),

                                        html.A([html.Img(src=app.get_asset_url('github.png'), alt='logo github',
                                                         className='logo')],
                                               href='https://github.com/paupradel/ecobici_viz')], className='iconos')
                                    ]),
                       html.Div(
                           [html.Div(dcc.Graph(figure=figure_mapa, id='mapa-graph', className='mapa-graph',
                                               clickData=click_data_inicial,
                                               config=estilo_graficas), id='mapa', className='mapa'),
                            html.Div([html.P('Edad'),
                                      html.H1(edad_seleccion, id='edad', className='edad')], id='edades',
                                     className='mini_container-grid-2'),
                            html.Div([html.P('Género', className='titulo-genero'),
                                      html.Img(src=obtener_cascos, id='genero', alt='porcentaje_genero',
                                               className='imagen-genero')],
                                     id='genero-cont', className='genero'),
                            html.Div(dcc.Graph(figure=figure_sankey, id='sankey', className='sankey-graph',
                                               config=estilo_graficas),
                                     className='sankey'),
                            html.Div(dcc.Graph(figure=figure_bar, id='hora_recorrido', className='hora-recorrido-graph',
                                               config=estilo_graficas),
                                     className='hora-recorrido')],
                           className='contenedor-ecobici')
                       ])


@app.callback(Output('modal_1', 'style'),
              [Input('modal-close-button', 'n_clicks')])
def close_modal(n):
    if (n is not None) and (n > 0):
        return {'display': 'none'}


@app.callback(Output('modal_2', 'is_open'),
              [Input('instrucciones_button', 'n_clicks'),
               Input('close_2', 'n_clicks')],
              [State('modal_2', 'is_open')])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback([Output('mapa-graph', 'figure'),
               Output('sankey', 'figure'),
               Output('edad', 'children'),
               Output('genero', 'src'),
               Output('hora_recorrido', 'figure'),
               Output('memory', 'data')],
              [Input('mapa-graph', 'clickData')],
              [State('memory', 'data')])
def select_ageb(clickData, data):
    if data is None:
        data = {'ageb_inicial': ageb_inicial_default, 'ageb_final': ageb_final_default}
    else:
        data['ageb_inicial'] = data['ageb_final']
        data['ageb_final'] = clickData['points'][0]['location']

    figura_mapa_actualizado = dibujar_mapa(data['ageb_final'])
    figure_sankey_actualizado = dibujar_sankey(data['ageb_inicial'], data['ageb_final'])
    edad_actualizado = edad(data['ageb_inicial'], data['ageb_final'])
    cascos_actualizado = nombre_archivo_cascos(data['ageb_inicial'])
    figura_barras_actualizado = dibujar_barras(data['ageb_inicial'], data['ageb_final'])

    return figura_mapa_actualizado, figure_sankey_actualizado, edad_actualizado, cascos_actualizado, figura_barras_actualizado, data


if __name__ == '__main__':
    app.run_server(debug=True)
