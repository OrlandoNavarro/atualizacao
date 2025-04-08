import numpy as np
import pandas as pd
from geopy.distance import geodesic
from sklearn.cluster import KMeans
import streamlit as st

def calcular_distancia(coord1, coord2):
    """
    Calcula a distância em quilômetros entre duas coordenadas.
    """
    try:
        return geodesic(coord1, coord2).km
    except Exception as e:
        st.write(f"Erro calculando distância: {e}")
        return float('inf')

def gerar_matriz_distancias(pedidos_df):
    """
    Gera uma matriz de distâncias entre os pedidos com base em suas coordenadas.
    """
    coords = list(zip(pedidos_df['Latitude'], pedidos_df['Longitude']))
    n = len(coords)
    matriz = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                matriz[i][j] = calcular_distancia(coords[i], coords[j])
            else:
                matriz[i][j] = 0
    return matriz

def tsp_nearest_neighbor(pedidos_df):
    """
    Utiliza a heurística do vizinho mais próximo para resolver o TSP e retorna a ordem dos índices.
    """
    matriz = gerar_matriz_distancias(pedidos_df)
    n = len(matriz)
    if n == 0:
        return []
    start = 0
    visited = [False] * n
    rota = [start]
    visited[start] = True
    ultimo = start
    for _ in range(n - 1):
        proximos = [(matriz[ultimo][j], j) for j in range(n) if not visited[j]]
        if not proximos:
            break
        next_index = min(proximos, key=lambda x: x[0])[1]
        rota.append(next_index)
        visited[next_index] = True
        ultimo = next_index
    return rota

def route_distance(rota, matriz):
    """
    Calcula a distância total da rota usando a matriz de distâncias.
    """
    dist = 0
    for i in range(len(rota) - 1):
        dist += matriz[rota[i]][rota[i+1]]
    return dist

def otimizacao_2opt(rota, matriz):
    """
    Melhora uma rota TSP utilizando a heurística 2-opt,
    invertendo segmentos para reduzir a distância total.
    """
    best = rota
    improved = True
    while improved:
        improved = False
        for i in range(1, len(rota) - 2):
            for j in range(i + 1, len(rota)):
                if j - i == 1:
                    continue
                new_route = best[:]
                new_route[i:j] = best[j - 1:i - 1:-1]
                if route_distance(new_route, matriz) < route_distance(best, matriz):
                    best = new_route
                    improved = True
        rota = best
    return best

def agrupar_por_regiao(pedidos_df, n_clusters=3):
    """
    Agrupa os pedidos em regiões usando K-Means com base em Latitude e Longitude.
    Adiciona a coluna 'Regiao' ao dataframe.
    """
    if pedidos_df.empty:
        return pedidos_df
    coords = pedidos_df[['Latitude', 'Longitude']].values
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    pedidos_df['Regiao'] = kmeans.fit_predict(coords)
    return pedidos_df

# INTERFACE STREAMLIT

# Tenta ler a planilha de pedidos (supondo que ela esteja em "database/Pedidos.xlsx")
try:
    pedidos_df = pd.read_excel("database/Pedidos.xlsx", engine="openpyxl")
except Exception as e:
    st.error("Planilha de Pedidos não encontrada. Envie a planilha de pedidos.")
    pedidos_df = pd.DataFrame()  # ou interrompa a execução

if st.button("Roteirizar"):
    st.write("Roteirização em execução...")
    
    # Agrupa os pedidos em regiões
    pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters=3)
    
    # Seleciona os pedidos da primeira região para otimização
    pedidos_regiao = pedidos_df[pedidos_df['Regiao'] == 0].reset_index(drop=True)
    
    if not pedidos_regiao.empty:
        rota = tsp_nearest_neighbor(pedidos_regiao)
        matriz = gerar_matriz_distancias(pedidos_regiao)
        rota_otimizada = otimizacao_2opt(rota, matriz)
        rota_enderecos = " → ".join(pedidos_regiao.loc[i, 'Endereço Completo'] for i in rota_otimizada)
        st.success(f"Rota Otimizada: {rota_enderecos}")
    else:
        st.error("Não há pedidos na região selecionada para roteirização.")