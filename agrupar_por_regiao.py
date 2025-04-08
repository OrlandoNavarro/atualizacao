import pandas as pd
from sklearn.cluster import KMeans

def agrupar_por_regiao(pedidos_df, n_clusters=3):
    """
    Agrupa os pedidos em regiões utilizando K-Means com base em Latitude e Longitude.
    Adiciona a coluna 'Regiao' no dataframe.
    """
    if pedidos_df.empty:
        pedidos_df['Regiao'] = []
        return pedidos_df
    coords = pedidos_df[['Latitude', 'Longitude']].values
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    pedidos_df['Regiao'] = kmeans.fit_predict(coords)
    return pedidos_df