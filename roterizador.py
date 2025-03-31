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
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Inicializar o geolocalizador
geolocator = Nominatim(user_agent="myGeocoder")

# Chave da API do Google
api_key = 'AIzaSyBz5rK-DhKuU2jcekmTqh8bRNPMv0wP0Sc'
gmaps = googlemaps.Client(key=api_key)

# Endereço de partida fixo
endereco_partida = "Avenida Antonio Ortega, 3604 - Pinhal, Cabreúva - SP"

# Função para obter coordenadas geográficas de um endereço
def obter_coordenadas(endereco):
    location = geolocator.geocode(endereco)
    if location:
        return (location.latitude, location.longitude)
    else:
        st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}")
        return None

# Função para calcular distância entre dois endereços usando a fórmula de Haversine
def calcular_distancia(endereco1, endereco2):
    coords_1 = obter_coordenadas(endereco1)
    coords_2 = obter_coordenadas(endereco2)
    if coords_1 and coords_2:
        distancia = geodesic(coords_1, coords_2).meters
        return distancia
    else:
        return None

# Função para criar o grafo do TSP
def criar_grafo_tsp(pedidos_df):
    G = nx.Graph()
    enderecos = pedidos_df['Endereço de Entrega'].unique()
    
    # Adicionar o endereço de partida
    G.add_node(endereco_partida)
    
    for endereco in enderecos:
        G.add_node(endereco)
    
    for (endereco1, endereco2) in permutations([endereco_partida] + list(enderecos), 2):
        distancia = calcular_distancia(endereco1, endereco2)
        if distancia is not None:
            G.add_edge(endereco1, endereco2, weight=distancia)
    
    return G

# Função para resolver o TSP usando Algoritmo Genético
def resolver_tsp_genetico(G):
    # Implementação do algoritmo genético para TSP
    pass

# Função para resolver o VRP usando OR-Tools
def resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao):
    # Implementação do VRP usando OR-Tools
    pass

# Função para otimizar o aproveitamento da frota usando programação linear
def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos):
    pedidos_df['Nº Carga'] = None
    pedidos_df['Placas'] = None
    carga_numero = 1
    
    # Ajustar a capacidade da frota
    caminhoes_df['Capac. Kg'] *= (percentual_frota / 100)
    caminhoes_df['Capac. Cx'] *= (percentual_frota / 100)
    
    for _, caminhao in caminhoes_df.iterrows():
        capacidade_peso = caminhao['Capac. Kg']
        capacidade_caixas = caminhao['Capac. Cx']
        
        pedidos_alocados = pedidos_df[(pedidos_df['Peso dos Itens'] <= capacidade_peso) & (pedidos_df['Qtde. dos Itens'] <= capacidade_caixas)]
        pedidos_alocados = pedidos_alocados.sample(frac=(percentual_pedidos / 100))
        
        pedidos_df.loc[pedidos_alocados.index, 'Nº Carga'] = carga_numero
        pedidos_df.loc[pedidos_alocados.index, 'Placas'] = caminhao['Placas']
        
        capacidade_peso -= pedidos_alocados['Peso dos Itens'].sum()
        capacidade_caixas -= pedidos_alocados['Qtde. dos Itens'].sum()
        
        carga_numero += 1
    
    return pedidos_df

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
    
    if 'Latitude' in pedidos_df.columns and 'Longitude' in pedidos_df.columns:
        for _, row in pedidos_df.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=row['Endereço de Entrega']
            ).add_to(mapa)
    else:
        st.error("As colunas 'Latitude' e 'Longitude' não foram encontradas no DataFrame.")
    
    return mapa

# Função para cadastrar caminhões
def cadastrar_caminhoes():
    st.title("Cadastro de Caminhões da Frota")
    
    # Carregar DataFrame existente ou criar um novo
    try:
        caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
    except FileNotFoundError:
        caminhoes_df = pd.DataFrame(columns=['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo'])
    
    # Formulário para cadastrar novo caminhão
    with st.form("cadastrar_caminhao"):
        st.subheader("Cadastrar Novo Caminhão")
        num_carga = st.text_input("Número de Carga")
        placas = st.text_input("Placas")
        capac_cx = st.number_input("Capacidade em Caixas", min_value=0)
        capac_kg = st.number_input("Capacidade em Quilogramas", min_value=0)
        descricao_veiculo = st.text_input("Descrição do Veículo")
        transportador = st.text_input("Transportador")
        ativo = st.selectbox("Status", ["Ativo", "Inativo"])
        
        submit_button = st.form_submit_button("Cadastrar")
        
        if submit_button:
            novo_caminhao = {
                'Nº Carga': num_carga,
                'Placas': placas,
                'Capac. Cx': capac_cx,
                'Capac. Kg': capac_kg,
                'Descrição Veículo': descricao_veiculo,
                'Transportador': transportador,
                'Ativo': ativo
            }
            caminhoes_df = caminhoes_df.append(novo_caminhao, ignore_index=True)
            caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
            st.success("Caminhão cadastrado com sucesso!")
    
    # Exibir caminhões cadastrados
    st.subheader("Caminhões Cadastrados")
    st.dataframe(caminhoes_df)
    
    # Formulário para atualizar status de caminhão
    with st.form("atualizar_status"):
        st.subheader("Atualizar Status de Caminhão")
        placas_atualizar = st.selectbox("Selecione a Placa do Caminhão", caminhoes_df['Placas'].unique())
        novo_status = st.selectbox("Novo Status", ["Ativo", "Inativo"])
        
        atualizar_button = st.form_submit_button("Atualizar Status")
        
        if atualizar_button:
            caminhoes_df.loc[caminhoes_df['Placas'] == placas_atualizar, 'Ativo'] = novo_status
            caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
            st.success("Status do caminhão atualizado com sucesso!")

# Função principal para o painel interativo
def main():
    st.title("Roteirizador de Pedidos")
    
    # Opção para cadastrar caminhões
    if st.checkbox("Cadastrar Caminhões"):
        cadastrar_caminhoes()
    
    # Upload dos arquivos Excel
    uploaded_pedidos = st.file_uploader("Escolha o arquivo Excel de Pedidos", type=["xlsm"])
    uploaded_caminhoes = st.file_uploader("Escolha o arquivo Excel da Frota", type=["xlsm"])
    
    if uploaded_pedidos is not None and uploaded_caminhoes is not None:
        # Leitura das planilhas
        pedidos_df = pd.read_excel(uploaded_pedidos, engine='openpyxl')
        caminhoes_df = pd.read_excel(uploaded_caminhoes, engine='openpyxl')
        
                # Verificar se as colunas necessárias estão presentes
        colunas_pedidos = ['Nº Carga', 'Placas', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Região Logística', 'Qtde. dos Itens', 'Peso dos Itens']
        colunas_caminhoes = ['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo']
        
        if not all(col in pedidos_df.columns for col in colunas_pedidos):
            st.error("As colunas necessárias não foram encontradas na planilha de pedidos.")
            return
        
        if not all(col in caminhoes_df.columns for col in colunas_caminhoes):
            st.error("As colunas necessárias não foram encontradas na planilha da frota.")
            return
        
        # Filtrar caminhões ativos
        caminhoes_df = caminhoes_df[caminhoes_df['Ativo'] == 'Ativo']
        
        # Processamento dos dados
        pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
        
        # Opções de agrupamento por região
        n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=5)
        pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
        
        # Definir capacidade da frota
        percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
        
        # Definir percentual de pedidos alocados por veículo
        percentual_pedidos = st.slider("Percentual de pedidos alocados por veículo (%)", min_value=0, max_value=100, value=100)
        
        # Parâmetros de roteirização
        modo_roteirizacao = st.selectbox("Modo de roteirização", ["Frota Mínima", "Balanceado"])
        criterio_otimizacao = st.selectbox("Critério de otimização", ["Menor Tempo", "Menor Distância", "Menor Custo"])
        
        # Alocar pedidos nos caminhões respeitando os limites de peso e quantidade de caixas
        pedidos_df = otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos)
        
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
            melhor_rota_vrp = resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao)
            st.write(f"Melhor rota VRP: {melhor_rota_vrp}")
        
        # Exibir resultado
        st.write("Dados dos pedidos:")
        st.dataframe(pedidos_df)
        
        # Criar e exibir mapa
        mapa = criar_mapa(pedidos_df)
        folium_static(mapa)
        
        # Gerar arquivo Excel com a roteirização feita
        output_file_path = 'roterizacao_resultado.xlsx'
        pedidos_df.to_excel(output_file_path, index=False)
        st.write(f"Arquivo Excel com a roteirização feita foi salvo em: {output_file_path}")
        
        # Botão para baixar o arquivo Excel
        with open(output_file_path, "rb") as file:
            btn = st.download_button(
                label="Baixar planilha",
                data=file,
                file_name="roterizacao_resultado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

main()
