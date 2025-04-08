import requests
import streamlit as st
import random
import networkx as nx
from itertools import permutations
from geopy.distance import geodesic
from sklearn.cluster import KMeans
import folium
from config import endereco_partida, endereco_partida_coords

def obter_coordenadas_opencage(endereco):
    try:
        api_key = "6f522c67add14152926990afbe127384"  # Sua chave de API do OpenCage
        url = f"https://api.opencagedata.com/geocode/v1/json?q={endereco}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        if 'status' in data and data['status']['code'] == 200 and 'results' in data:
            location = data['results'][0]['geometry']
            return (location['lat'], location['lng'])
        else:
            st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}.")
            return None
    except Exception as e:
        st.error(f"Erro ao tentar obter as coordenadas: {e}")
        return None

def obter_coordenadas_com_fallback(endereco, coordenadas_salvas):
    if endereco in coordenadas_salvas:
        return coordenadas_salvas[endereco]
    
    coords = obter_coordenadas_opencage(endereco)
    if coords is None:
        # Coordenadas manuais para endereços específicos
        coordenadas_manuais = {
            "Rua Araújo Leite, 146, Centro, Piedade, São Paulo, Brasil": (-23.71241093449893, -47.41796911054548)
        }
        coords = coordenadas_manuais.get(endereco, (None, None))
    
    if coords:
        coordenadas_salvas[endereco] = coords
    
    return coords

def calcular_distancia(coords_1, coords_2):
    if coords_1 and coords_2:
        return geodesic(coords_1, coords_2).meters
    return None

def criar_grafo_tsp(pedidos_df):
    G = nx.Graph()
    enderecos = pedidos_df['Endereço Completo'].unique()
    G.add_node(endereco_partida, pos=endereco_partida_coords)
    for endereco in enderecos:
        coords = (
            pedidos_df.loc[pedidos_df['Endereço Completo'] == endereco, 'Latitude'].values[0],
            pedidos_df.loc[pedidos_df['Endereço Completo'] == endereco, 'Longitude'].values[0]
        )
        G.add_node(endereco, pos=coords)
    for (end1, end2) in permutations([endereco_partida] + list(enderecos), 2):
        distancia = calcular_distancia(G.nodes[end1]['pos'], G.nodes[end2]['pos'])
        if distancia is not None:
            G.add_edge(end1, end2, weight=distancia)
    return G

def resolver_tsp_genetico(G):
    def fitness(route):
        return sum(G.edges[route[i], route[i+1]]['weight'] for i in range(len(route) - 1)) + \
               G.edges[route[-1], route[0]]['weight']

    def mutate(route):
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
        return route

    def crossover(route1, route2):
        size = len(route1)
        start, end = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[start:end] = route1[start:end]
        pointer = 0
        for i in range(size):
            if route2[i] not in child:
                while child[pointer] is not None:
                    pointer += 1
                child[pointer] = route2[i]
        return child

    def genetic_algorithm(population, generations=1000, mutation_rate=0.01):
        for _ in range(generations):
            population = sorted(population, key=lambda route: fitness(route))
            next_generation = population[:2]
            for _ in range(len(population) // 2 - 1):
                parents = random.sample(population[:10], 2)
                child = crossover(parents[0], parents[1])
                if random.random() < mutation_rate:
                    child = mutate(child)
                next_generation.append(child)
            population = next_generation
        return population[0], fitness(population[0])

    nodes = list(G.nodes)
    population = [random.sample(nodes, len(nodes)) for _ in range(100)]
    best_route, best_distance = genetic_algorithm(population)
    return best_route, best_distance

def resolver_vrp(pedidos_df, caminhoes_df):
    # Implementação do VRP usando OR-Tools (a implementar)
    pass

def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, max_pedidos, n_clusters):
    pedidos_df['Nº Carga'] = 0
    pedidos_df['Placa'] = ""
    carga_numero = 1
    
    # Ajusta a capacidade da frota
    caminhoes_df['Capac. Kg'] *= (percentual_frota / 100)
    caminhoes_df['Capac. Cx'] *= (percentual_frota / 100)
    caminhoes_df = caminhoes_df[caminhoes_df['Disponível'] == 'Ativo']
    
    pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
    
    for regiao in pedidos_df['Regiao'].unique():
        pedidos_regiao = pedidos_df[pedidos_df['Regiao'] == regiao]
        for _, caminhao in caminhoes_df.iterrows():
            capacidade_peso = caminhao['Capac. Kg']
            capacidade_caixas = caminhao['Capac. Cx']
            pedidos_alocados = pedidos_regiao[
                (pedidos_regiao['Peso dos Itens'] <= capacidade_peso) & 
                (pedidos_regiao['Qtde. dos Itens'] <= capacidade_caixas)
            ]
            pedidos_alocados = pedidos_alocados.sample(n=min(max_pedidos, len(pedidos_alocados)))
            if not pedidos_alocados.empty:
                pedidos_df.loc[pedidos_alocados.index, 'Nº Carga'] = carga_numero
                pedidos_df.loc[pedidos_alocados.index, 'Placa'] = caminhao['Placa']
                capacidade_peso -= pedidos_alocados['Peso dos Itens'].sum()
                capacidade_caixas -= pedidos_alocados['Qtde. dos Itens'].sum()
                carga_numero += 1
    
    if pedidos_df['Placa'].isnull().any() or pedidos_df['Nº Carga'].isnull().any():
        st.error("Não foi possível atribuir placas ou números de carga a alguns pedidos.")
    
    return pedidos_df

def agrupar_por_regiao(pedidos_df, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters)
    pedidos_df['Regiao'] = kmeans.fit_predict(pedidos_df[['Latitude', 'Longitude']])
    return pedidos_df

def criar_mapa(pedidos_df):
    mapa = folium.Map(location=endereco_partida_coords, zoom_start=12)
    for _, row in pedidos_df.iterrows():
        popup_text = f"<b>Placa: {row['Placa']}</b><br>Endereço: {row['Endereço Completo']}"
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=popup_text,
            icon=folium.Icon(color='blue')
        ).add_to(mapa)
    folium.Marker(
        location=endereco_partida_coords,
        popup="Endereço de Partida",
        icon=folium.Icon(color='red')
    ).add_to(mapa)
    return mapa