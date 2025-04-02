import pandas as pd
import requests
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
from geopy.distance import geodesic

# Endereço de partida fixo
endereco_partida = "Avenida Antonio Ortega, 3604 - Pinhal, Cabreúva - SP"
# Coordenadas geográficas do endereço de partida
endereco_partida_coords = (-23.0838, -47.1336)  # Exemplo de coordenadas para Cabreúva, SP

# Função para obter coordenadas geográficas de um endereço usando OpenStreetMap API
def obter_coordenadas_osm(endereco):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={endereco}&format=json&limit=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                location = data[0]
                return (float(location['lat']), float(location['lon']))
            else:
                st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}")
                return None
        elif response.status_code == 403:
            st.error("Erro 403: Acesso negado. Verifique se você tem permissão para acessar a API.")
            return None
        else:
            st.error(f"Erro ao tentar obter as coordenadas: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro ao tentar obter as coordenadas: {e}")
        return None

# Função para calcular distância entre dois endereços usando a fórmula de Haversine
def calcular_distancia(coords_1, coords_2):
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
    G.add_node(endereco_partida, pos=endereco_partida_coords)
    
    for endereco in enderecos:
        coords = (pedidos_df.loc[pedidos_df['Endereço Completo'] == endereco, 'Latitude'].values[0],
                  pedidos_df.loc[pedidos_df['Endereço Completo'] == endereco, 'Longitude'].values[0])
        G.add_node(endereco, pos=coords)
    
    for (endereco1, endereco2) in permutations([endereco_partida] + list(enderecos), 2):
        coords_1 = G.nodes[endereco1]['pos']
        coords_2 = G.nodes[endereco2]['pos']
        distancia = calcular_distancia(coords_1, coords_2)
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
    pedidos_df['Placa'] = None
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
        pedidos_df.loc[pedidos_alocados.index, 'Placa'] = caminhao['Placa']
        
        capacidade_peso -= pedidos_alocados['Peso dos Itens'].sum()
        capacidade_caixas -= pedidos_alocados['Qtde. dos Itens'].sum()
        
        carga_numero += 1
    
    return pedidos_df

# Função para agrupar por região usando KMeans
def agrupar_por_regiao(pedidos_df, n_clusters=5):
    kmeans = KMeans(n_clusters=n_clusters)
    pedidos_df['Regiao'] = kmeans.fit_predict(pedidos_df[['Latitude', 'Longitude']])
    
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
        caminhoes_df = pd.DataFrame(columns=['Placa', 'Transportador', 'Descrição Veículo', 'Capac. Cx', 'Capac. Kg', 'Disponível'])
    
    # Upload do arquivo Excel de Caminhões
    uploaded_caminhoes = st.file_uploader("Escolha o arquivo Excel de Caminhões", type=["xlsx", "xlsm"])
    
    if uploaded_caminhoes is not None:
        novo_caminhoes_df = pd.read_excel(uploaded_caminhoes, engine='openpyxl')
        
        # Verificar se as colunas necessárias estão presentes
        colunas_caminhoes = ['Placa', 'Transportador', 'Descrição Veículo', 'Capac. Cx', 'Capac. Kg', 'Disponível']
        
        if not all(col in novo_caminhoes_df.columns for col in colunas_caminhoes):
            st.error("As colunas necessárias não foram encontradas na planilha de caminhões.")
            return
        
        # Botão para carregar a frota
        if st.button("Carregar Frota"):
            caminhoes_df = pd.concat([caminhoes_df, novo_caminhoes_df], ignore_index=True)
            caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
            st.success("Frota carregada com sucesso!")

    # Botão para limpar a frota
    if st.button("Limpar Frota"):
        caminhoes_df = pd.DataFrame(columns=['Placa', 'Transportador', 'Descrição Veículo', 'Capac. Cx', 'Capac. Kg', 'Disponível'])
        caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
        st.success("Frota limpa com sucesso!")
    
    # Exibir caminhões cadastrados
    st.subheader("Caminhões Cadastrados")
    st.dataframe(caminhoes_df)

# Função para subir planilhas de roteirizações
def subir_roterizacoes():
    st.title("Upload de Planilhas de Roteirizações")
    
    # Carregar DataFrame existente ou criar um novo
    try:
        roterizacao_df = pd.read_excel("roterizacao_dados.xlsx", engine='openpyxl')
    except FileNotFoundError:
        roterizacao_df = pd.DataFrame(columns=['Placa', 'Nº Carga', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Qtde. dos Itens', 'Peso dos Itens'])
    
    # Upload do arquivo Excel de Roteirizações
    uploaded_roterizacao = st.file_uploader("Escolha o arquivo Excel de Roteirizações", type=["xlsx", "xlsm"])
    
    if uploaded_roterizacao is not None:
        novo_roterizacao_df = pd.read_excel(uploaded_roterizacao, engine='openpyxl')
        
        # Verificar se as colunas necessárias estão presentes
        colunas_roterizacao = ['Placa', 'Nº Carga', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Qtde. dos Itens', 'Peso dos Itens']
        
        colunas_faltando = [col for col in colunas_roterizacao if col not in novo_roterizacao_df.columns]
        if colunas_faltando:
            st.error(f"As seguintes colunas estão faltando na planilha de roteirizações: {', '.join(colunas_faltando)}")
            return
        
        # Botão para carregar a roteirização
        if st.button("Carregar Roteirização"):
            roterizacao_df = pd.concat([roterizacao_df, novo_roterizacao_df], ignore_index=True)
            roterizacao_df.to_excel("roterizacao_dados.xlsx", index=False)
            st.success("Roteirização carregada com sucesso!")
        
    # Botão para limpar a roteirização
    if st.button("Limpar Roteirização"):
        roterizacao_df = pd.DataFrame(columns=colunas_roterizacao)
        roterizacao_df.to_excel("roterizacao_dados.xlsx", index=False)
        st.success("Roteirização limpa com sucesso!")
    
    # Exibir dados da planilha de roteirizações
    st.subheader("Dados da Roteirização")
    st.dataframe(roterizacao_df)

# Função principal para o painel interativo
def main():
    st.title("Roteirizador de Pedidos")
    
    # Upload do arquivo Excel de Pedidos
    uploaded_pedidos = st.file_uploader("Escolha o arquivo Excel de Pedidos", type=["xlsx", "xlsm"])
    
    if uploaded_pedidos is not None:
        # Leitura das planilhas
        pedidos_df = pd.read_excel(uploaded_pedidos, engine='openpyxl')
        
        # Formar o endereço completo
        pedidos_df['Endereço Completo'] = pedidos_df['Endereço de Entrega'] + ', ' + pedidos_df['Bairro de Entrega'] + ', ' + pedidos_df['Cidade de Entrega']
        
        # Obter coordenadas geográficas
        def obter_coordenadas_com_fallback(endereco):
            coords = obter_coordenadas_osm(endereco)
            if coords is None:
                # Coordenadas manuais para endereços específicos
                coordenadas_manuais = {
                    "Rua Araújo Leite, 146, Centro, Piedade": (-23.71241093449893, -47.41796911054548)
                }
                coords = coordenadas_manuais.get(endereco, (None, None))
            return coords
        
        pedidos_df['Latitude'] = pedidos_df['Endereço Completo'].apply(lambda x: obter_coordenadas_com_fallback(x)[0])
        pedidos_df['Longitude'] = pedidos_df['Endereço Completo'].apply(lambda x: obter_coordenadas_com_fallback(x)[1])
        
        # Carregar dados da frota cadastrada
        try:
            caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
        except FileNotFoundError:
            st.error("Nenhum caminhão cadastrado. Por favor, cadastre caminhões primeiro.")
            return
        
        # Verificar se as colunas necessárias estão presentes
        colunas_pedidos = ['Nº Carga', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Qtde. dos Itens', 'Peso dos Itens']
        
        colunas_faltando_pedidos = [col for col in colunas_pedidos if col not in pedidos_df.columns]
        if colunas_faltando_pedidos:
            st.error(f"As seguintes colunas estão faltando na planilha de pedidos: {', '.join(colunas_faltando_pedidos)}")
            return
        
        colunas_caminhoes = ['Placa', 'Transportador', 'Descrição Veículo', 'Capac. Cx', 'Capac. Kg', 'Disponível']
        colunas_faltando_caminhoes = [col for col in colunas_caminhoes if col not in caminhoes_df.columns]
        if colunas_faltando_caminhoes:
            st.error(f"As seguintes colunas estão faltando na planilha da frota: {', '.join(colunas_faltando_caminhoes)}")
            return
        
        # Filtrar caminhões ativos
        caminhoes_df = caminhoes_df[caminhoes_df['Disponível'] == 'Ativo']
        
        # Mostrar opções de roteirização após o upload da planilha
        if st.button("Roteirizar"):
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

    # Opção para cadastrar caminhões
    if st.checkbox("Cadastrar Caminhões"):
        cadastrar_caminhoes()
    
    # Opção para subir planilhas de roteirizações
    if st.checkbox("Subir Planilhas de Roteirizações"):
        subir_roterizacoes()

main()
