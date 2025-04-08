import os
import pandas as pd
import numpy as np
import logging
from functools import lru_cache
from geopy.geocoders import Nominatim
from config import DATABASE_FOLDER, GEOCODER_USER_AGENT

# Configuração do logging para geocodificação
logging.basicConfig(level=logging.INFO, filename="geocoding.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT)

@lru_cache(maxsize=128)
def geocode_endereco(endereco):
    """
    Converte um endereço em latitude/longitude.
    Usa LRU cache para evitar chamadas repetidas.
    """
    try:
        local = geolocator.geocode(endereco)
        if local:
            return (local.latitude, local.longitude)
    except Exception as e:
        logging.error(f"Erro na geocodificação do endereço '{endereco}': {e}")
    return None

def converter_enderecos(df, endereco_coluna="Endereço Completo", cache_filename="coordenadas_cache.xlsx"):
    """
    Atualiza o DataFrame com colunas 'Latitude' e 'Longitude' para cada endereço,
    utilizando um arquivo de cache para evitar geocodificação repetida.
    """
    cache_file = os.path.join(DATABASE_FOLDER, cache_filename)
    if os.path.exists(cache_file):
        try:
            cache_df = pd.read_excel(cache_file, engine="openpyxl")
            cache = dict(zip(cache_df['Endereço'], zip(cache_df['Latitude'], cache_df['Longitude'])))
        except Exception as e:
            logging.error(f"Erro ao ler o cache: {e}")
            cache = {}
    else:
        cache = {}

    latitudes = []
    longitudes = []
    for endereco in df[endereco_coluna]:
        if endereco in cache:
            lat, lon = cache[endereco]
        else:
            latlon = geocode_endereco(endereco)
            if latlon is None:
                lat, lon = (np.nan, np.nan)
            else:
                lat, lon = latlon
            cache[endereco] = (lat, lon)
        latitudes.append(lat)
        longitudes.append(lon)

    df['Latitude'] = latitudes
    df['Longitude'] = longitudes

    try:
        cache_df = pd.DataFrame(list(cache.items()), columns=['Endereço', 'Coordenadas'])
        cache_df[['Latitude', 'Longitude']] = pd.DataFrame(cache_df['Coordenadas'].tolist(), index=cache_df.index)
        cache_df.drop(columns=['Coordenadas'], inplace=True)
        cache_df.to_excel(cache_file, index=False)
    except Exception as e:
        logging.error(f"Erro ao atualizar o cache: {e}")

    return df