import dash
import dash_html_components as html

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


#--------------------------------- Layout de la app-------------------------------#
app.layout= html.Div([html.Div([html.Header(html.H1('Ecobici'), id='titulo-app', className='titulo-app'),
                                html.Div( id='mapa', className='mapa')], id='espacio-mapa', className='espacio-mapa'),
                      html.Div([html.Div( id='edad-genero', className='edad-genero'),
                                html.Div( id='sankey', className='sankey'),
                                html.Div( id='hora-recorrido', className='hora-recorrido')], id= 'espacio-narrativa', className='espacio-narrativa')])

if __name__ == '__main__':
    app.run_server(debug=True)
