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
import random

# Inicializar o geolocalizador com um tempo de timeout maior
geolocator = Nominatim(user_agent="myGeocoder", timeout=10)

# Chave da API do Google
api_key = 'AIzaSyBz5rK-DhKuU2jcekmTqh8bRNPMv0wP0Sc'
gmaps = googlemaps.Client(key=api_key)

# Endereço de partida fixo
endereco_partida = "Avenida Antonio Ortega, 3604 - Pinhal, Cabreúva - SP"
# Coordenadas geográficas do endereço de partida
endereco_partida_coords = (-23.0838, -47.1336)  # Exemplo de coordenadas para Cabreúva, SP

# Função para obter coordenadas geográficas de um endereço usando a API do Google Maps
def obter_coordenadas_google(endereco):
    try:
        geocode_result = gmaps.geocode(endereco)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}")
            return None
    except Exception as e:
        st.error(f"Erro ao tentar obter as coordenadas: {e}")
        return None

# Função para transformar colunas G, H e I em um único endereço com delimitador e obter coordenadas
def transformar_e_obter_coordenadas(pedidos_df):
    # Verificar se as colunas 'G', 'H' e 'I' existem
    if all(col in pedidos_df.columns for col in ['G', 'H', 'I']):
        # Concatenar colunas G, H e I para formar o endereço completo
        pedidos_df['Endereço Completo'] = pedidos_df.apply(lambda row: f"{row['G']}, {row['H']}, {row['I']}", axis=1)
        
        # Adicionar colunas de Latitude e Longitude
        pedidos_df['Latitude'] = pedidos_df['Endereço Completo'].apply(lambda x: obter_coordenadas_google(x)[0] if obter_coordenadas_google(x) else None)
        pedidos_df['Longitude'] = pedidos_df['Endereço Completo'].apply(lambda x: obter_coordenadas_google(x)[1] if obter_coordenadas_google(x) else None)
    else:
        st.error("As colunas 'G', 'H' e 'I' não foram encontradas no DataFrame.")
    
    return pedidos_df

# Função para calcular distância entre dois endereços usando a fórmula de Haversine
def calcular_distancia(endereco1, endereco2):
    if endereco1 == endereco_partida:
        coords_1 = endereco_partida_coords
    else:
        coords_1 = obter_coordenadas_google(endereco1)
    
    coords_2 = obter_coordenadas_google(endereco2)
    
    if coords_1 and coords_2:
        distancia = geodesic(coords_1, coords_2).meters
        return distancia
    else:
        return None

# Função para criar o grafo do TSP
def criar_grafo_tsp(pedidos_df):
    G = nx.Graph()
    enderecos = pedidos_df['Endereço Completo'].unique()
    
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
def resolver_tsp_genetico(G, population_size=100, generations=500, mutation_rate=0.01):
    def create_route(nodes):
        route = random.sample(nodes, len(nodes))
        return route

    def initial_population(population_size, nodes):
        return [create_route(nodes) for _ in range(population_size)]

    def route_distance(route):
        distance = 0
        for i in range(len(route)):
            distance += G[route[i-1]][route[i]]['weight']
        return distance

    def rank_routes(population):
        return sorted(population, key=lambda route: route_distance(route))

    def selection(population, elite_size):
        ranked_population = rank_routes(population)
        return ranked_population[:elite_size]

    def crossover(parent1, parent2):
        child = []
        childP1 = []
        childP2 = []

        geneA = int(random.random() * len(parent1))
        geneB = int(random.random() * len(parent1))

        startGene = min(geneA, geneB)
        endGene = max(geneA, geneB)

        for i in range(startGene, endGene):
            childP1.append(parent1[i])

        childP2 = [item for item in parent2 if item not in childP1]

        child = childP1 + childP2
        return child

   )):
            if random.random() < mutation_rate:
                swapWith = int(random.random() * len(route))

                city1 = route[swapped]
                city2 = route[swapWith]

                route[swapped] = city2
                route[swapWith] = city1
        return route

    def next_generation(current_gen, elite_size, mutation_rate):
        elite = selection(current_gen, elite_size)
        children = []

        for i in range(len(elite)):
           [i])

        non_elite = current_gen[elite_size:]
        for i in range(len(non_elite)):
            parent1 = random.choice(elite)
            parent2 = random.choice(non_elite)
            child = crossover(parent1, parent2)
            children.append(child)

        next_gen = [mutate(child, mutation_rate) for child in children]
        return next_gen

    nodes = list(G.nodes)
    population = initial_population(population_size, nodes)
    elite_size = int(0.2 * population_size)

    for _ in range(generations):
        population = next_generation(population, elite_size, mutation_rate)

    best_route = rank_routes(population)[0]
    best_distance = route_distance(best_route)

    return best_route, best_distance

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
                popup=row['Endereço Completo']
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
def atualizar_status_caminhao(caminhoes_df):
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
    
    # Upload do arquivo Excel de Pedidos
    uploaded_pedidos = st.file_uploader("Escolha o arquivo Excel de Pedidos", type=["xlsm"])
    
    if uploaded_pedidos is not None:
        # Leitura das planilhas
        pedidos_df = pd.read_excel(uploaded_pedidos, engine='openpyxl')
        
        # Carregar dados da frota cadastrada
        try:
            caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
        except FileNotFoundError:
            st.error("Nenhum caminhão cadastrado. Por favor, cadastre caminhões primeiro.")
            return
        
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
        
        # Transformar endereços e obter coordenadas
        pedidos_df = transformar_e_obter_coordenadas(pedidos_df)
        
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
            pedidos_df['Ordem de Entrega TSP'] = pedidos_df['Endereço Completo'].apply(lambda x: melhor_rota.index(x) + 1)
        
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
