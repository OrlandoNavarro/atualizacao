import pandas as pd
import googlemaps
import os
import streamlit as st
from sklearn.cluster import KMeans
from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import networkx as nx
from itertools import permutations
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import folium
from streamlit_folium import folium_static
import streamlit_authenticator as stauth

# Chave da API do Google
api_key = 'AIzaSyCOMqaimUuQq0C7IFyo80jhxmCtxBr5Uio'
gmaps = googlemaps.Client(key=api_key)

# Configuração de autenticação
names = ["Orlando"]
usernames = ["orlando"]
passwords = ["Picole2024@"]

hashed_passwords = [stauth.Hasher().hash(password) for password in passwords]

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "app_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.title(f"Bem-vindo, {name}!")
    
    # Função para calcular distância entre dois endereços usando Google Maps
    def calcular_distancia(endereco1, endereco2):
        result = gmaps.distance_matrix(endereco1, endereco2)
        distancia = result['rows'][0]['elements'][0]['distance']['value']
        return distancia

    # Função para criar o grafo do TSP
    def criar_grafo_tsp(pedidos_df):
        G = nx.Graph()
        enderecos = pedidos_df['Endereço de Entrega'].unique()
        
        for endereco in enderecos:
            G.add_node(endereco)
        
        for (endereco1, endereco2) in permutations(enderecos, 2):
            distancia = calcular_distancia(endereco1, endereco2)
            G.add_edge(endereco1, endereco2, weight=distancia)
        
        return G

    # Função para resolver o TSP usando Algoritmo Genético
    def resolver_tsp_genetico(G):
        # Implementação do algoritmo genético para TSP
        pass

    # Função para resolver o VRP usando OR-Tools
    def resolver_vrp(pedidos_df, caminhoes_df):
        # Implementação do VRP usando OR-Tools
        pass

    # Função para otimizar o aproveitamento da frota usando programação linear
    def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota):
        # Implementação da função de otimização do aproveitamento da frota usando programação linear
        pass

    # Função para calcular o melhor custo usando programação linear
    def calcular_melhor_custo(pedidos_df, caminhoes_df):
        # Implementação da função de cálculo do melhor custo usando programação linear
        pass

    # Função para definir a quantidade média de pedidos por região usando Machine Learning
    def definir_media_pedidos_por_regiao(pedidos_df, media_pedidos):
        # Implementação da função para definir a quantidade média de pedidos por região usando Machine Learning
        pass

    # Função para agrupar por região usando KMeans
    def agrupar_por_regiao(pedidos_df, n_clusters=5):
        pedidos_df['Coordenada X'] = pedidos_df['Cidade de Entrega'].apply(lambda x: hash(x) % 100)
        pedidos_df['Coordenada Y'] = pedidos_df['Bairro de Entrega'].apply(lambda x: hash(x) % 100)
        
        kmeans = KMeans(n_clusters=n_clusters)
        pedidos_df['Regiao'] = kmeans.fit_predict(pedidos_df[['Coordenada X', 'Coordenada Y']])
        
        return pedidos_df

    # Função para criar um mapa com folium
    def criar_mapa(pedidos_df):
        mapa = folium.Map(location=[-23.55052, -46.633308], zoom_start=10)
        
        for _, row in pedidos_df.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=row['Endereço de Entrega']
            ).add_to(mapa)
        
        return mapa

    # Função principal para o painel interativo
    def main():
        st.title("Roteirizador de Pedidos")
        
        # Upload do arquivo Excel
        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xlsm"])
        
        if uploaded_file is not None:
            # Leitura das planilhas
            pedidos_df = pd.read_excel(uploaded_file, sheet_name='Pedidos', engine='openpyxl')
            caminhoes_df = pd.read_excel(uploaded_file, sheet_name='Caminhoes', engine='openpyxl')
            
            # Processamento dos dados
            pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
            
            # Opções de agrupamento por região
            n_clusters = st.slider("Número de regiões para agrupar", min_value=2, max_value=10, value=5)
            pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
            
            # Montagem de carga
            cargas = pedidos_df.groupby(['Regiao', 'COM017.Placas']).agg({
                'Qtde. dos Itens': 'sum',
                'Peso dos Itens': 'sum'
            }).reset_index()
            
            # Opções de roteirização
            rota_tsp = st.checkbox("Aplicar TSP")
            rota_vrp = st.checkbox("Aplicar VRP")
            
            if rota_tsp:
                G = criar_grafo_tsp(pedidos_df)
                melhor_rota, menor_distancia = resolver_tsp_genetico(G)
                st.write(f"Melhor rota TSP: {melhor_rota}")
                st.write(f"Menor distância TSP: {menor_distancia}")
                pedidos_df['Ordem de Entrega TSP'] = pedidos_df['Endereço de Entrega'].apply(lambda x: melhor_rota.index(x) + 1)
            
            if rota_vrp:
                melhor_rota_vrp = resolver_vrp(pedidos_df, caminhoes_df)
                st.write(f"Melhor rota VRP: {melhor_rota_vrp}")
            
            # Exibir resultado
            st.write("Dados dos pedidos:")
            st.dataframe(pedidos_df)
            
            # Criar e exibir mapa
            mapa = criar_mapa(pedidos_df)
            folium_static(mapa)
            
            # Gerar arquivo Excel com a roteirização feita
            output_file_path = os.path.join(os.path.dirname(__file__), 'roterizacao_resultado.xlsx')
            pedidos_df.to_excel(output_file_path, index=False)
            st.write(f"Arquivo Excel com a roteirização feita foi salvo em: {output_file_path}")

    main()

elif authentication_status == False:
    st.error("Nome de usuário ou senha incorretos")
elif authentication_status == None:
    st.warning("Por favor, insira seu nome de usuário e senha")
