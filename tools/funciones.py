import geopandas as gpd
import pandas as pd
import json


def quitar_ceros(geodataframe, columna):
    '''Coregir ceros a la izquierda'''
    geodataframe[columna] = [''.join(filter(lambda x: x.isdigit(), row)) for row in geodataframe[columna]]
    geodataframe[columna] = geodataframe[columna].astype(int)
    return geodataframe

def checar_geojson(jdata):
    if 'id' not in jdata['features'][0].keys():
        if 'properties' in jdata['features'][0].keys():
            if 'id' in jdata['features'][0]['properties'] and jdata['features'][0]['properties']['id'] is not None:
                for k, feat in enumerate(jdata['features']):
                    jdata['features'][k]['id']= feat['properties']['id']
            else:
                for k in range(len(jdata['features'])):
                    jdata['features'][k]['id']= k
    return jdata

def obtener_geojson(dataframe, geodataframe, columna, primer_ageb):
    '''Reestructurar el dataframe y hacer merge con el dataframe, para obtener el geojson adecuado'''
    primer_ageb_str= str(primer_ageb)

    # Filtrar el dataframe y unir con el geodataframe
    dataframe = dataframe.loc[:, dataframe.columns.isin([columna, primer_ageb_str])]
    geodataframe = geodataframe.merge(dataframe, on=columna)

    # Renombrar la columna por si no se llama id
    geodataframe['id'] = geodataframe[columna]

    # Convertir el geodataframe en geojson
    #geodataframe.to_file('./data/production_data/ageb_geometry/ageb_distancias.json', driver='GeoJSON')
    with open('./data/production_data/ageb_geometry/ageb_distancias.json') as geofile:
        jdata = json.load(geofile)

    # Revisar el geojson
    jdata = checar_geojson(jdata)

    return geodataframe, jdata









