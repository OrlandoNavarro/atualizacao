import numpy as np
import pandas as pd
from geopy.distance import geodesic
from sklearn.cluster import KMeans
from melhorias_roterizacao import tsp_nearest_neighbor, otimizacao_2opt, agrupar_por_regiao, gerar_matriz_distancias
import streamlit as st

def calcular_distancia(coord1, coord2):
    """
    Calcula a distância em quilômetros entre duas coordenadas.
    """
    try:
        return geodesic(coord1, coord2).km
    except Exception as e:
        print(f"Erro calculando distância: {e}")
        return float('inf')

# Tenta ler a planilha de pedidos (supondo que ela esteja em "database/Pedidos.xlsx")
try:
    pedidos_df = pd.read_excel("database/Pedidos.xlsx", engine="openpyxl")
except Exception as e:
    st.error("Planilha de Pedidos não encontrada. Envie a planilha de pedidos.")
    pedidos_df = pd.DataFrame()  # ou retorne para interromper a execução

if st.button("Roteirizar"):
    st.write("Roteirização em execução...")
    
    # Exemplo: agrupa pedidos em 3 regiões
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