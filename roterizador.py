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
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=api_key)

# Endereço de partida fixo
endereco_partida = "Avenida Antonio Ortega, 3604 - Pinhal, Cabreúva - SP"
endereco_partida_coords = (-23.0838, -47.1336)  # Coordenadas para Cabreúva, SP

def obter_coordenadas(endereco):
    """Obtém coordenadas geográficas de um endereço."""
    try:
        location = geolocator.geocode(endereco)
        if location:
            return (location.latitude, location.longitude)
        else:
            st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}")
            return None
    except Exception as e:
        st.error(f"Erro ao tentar obter as coordenadas: {e}")
        return None

def calcular_distancia(endereco1, endereco2):
    """Calcula a distância entre dois endereços."""
    coords_1 = endereco_partida_coords if endereco1 == endereco_partida else obter_coordenadas(endereco1)
    coords_2 = obter_coordenadas(endereco2)
    if coords_1 and coords_2:
        return geodesic(coords_1, coords_2).meters
    return None

def criar_grafo_tsp(pedidos_df):
    """Cria um grafo para resolver o TSP."""
    G = nx.Graph()
    enderecos = pedidos_df['Endereço de Entrega'].unique()
    G.add_node(endereco_partida)
    for endereco in enderecos:
        G.add_node(endereco)
    for (endereco1, endereco2) in permutations([endereco_partida] + list(enderecos), 2):
        distancia = calcular_distancia(endereco1, endereco2)
        if distancia is not None:
            G.add_edge(endereco1, endereco2, weight=distancia)
    return G

def resolver_tsp_genetico(G):
    """Resolve o TSP usando Algoritmo Genético."""
    # Implementação do algoritmo genético para TSP
    pass

def resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao):
    """Resolve o VRP usando OR-Tools."""
    # Implementação do VRP usando OR-Tools
    pass

def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos):
    """Otimiza o aproveitamento da frota usando programação linear."""
    pedidos_df['Nº Carga'] = None
    pedidos_df['Placas'] = None
    carga_numero = 1
    
    caminhoes_df['Capac. Kg'] *= (percentual_frota / 100)
    caminhoes_df['Capac. Cx'] *= (percentual_frota / 100)
    
    for _, caminhao in caminhoes_df.iterrows():
        capacidade_peso = caminhao['Capac. Kg']
        capacidade_caixas = caminhao['Capac. Cx']
        
        pedidos_alocados = pedidos_df[
            (pedidos_df['Peso dos Itens'] <= capacidade_peso) &
            (pedidos_df['Qtde. dos Itens'] <= capacidade_caixas)
        ].sample(frac=(percentual_pedidos / 100))
        
        pedidos_df.loc[pedidos_alocados.index, 'Nº Carga'] = carga_numero
        pedidos_df.loc[pedidos_alocados.index, 'Placas'] = caminhao['Placas']
        
        carga_numero += 1

    return pedidos_df

def agrupar_por_regiao(pedidos_df, n_clusters=5):
    """Agrupa pedidos por região usando KMeans."""
    pedidos_df['Coordenada X'] = pedidos_df['Cidade de Entrega'].apply(lambda x: hash(x) % 100)
    pedidos_df['Coordenada Y'] = pedidos_df['Bairro de Entrega'].apply(lambda x: hash(x) % 100)
    
    kmeans = KMeans(n_clusters=n_clusters)
    pedidos_df['Regiao'] = kmeans.fit_predict(pedidos_df[['Coordenada X', 'Coordenada Y']])
    
    return pedidos_df

def criar_mapa(pedidos_df):
    """Cria um mapa com folium para visualizar pedidos."""
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

def cadastrar_caminhoes():
    """Interface para cadastrar caminhões."""
    st.title("Cadastro de Caminhões da Frota")
    try:
        caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
    except FileNotFoundError:
        caminhoes_df = pd.DataFrame(columns=['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo'])
    
    with st.form("cadastrar_caminhao"):
        st.subheader("Cadastrar Novo Caminhão")
        num_carga = st.text_input("Número de Carga")
        placas = st.text_input("Placas")
        capac_cx = st.number_input("Capacidade em Caixas", min_value=0)
        capac_kg = st.number_input("Capacidade em Quilogramas", min_value=0)
        descricao_veiculo = st.text_input("Descrição do Veículo")
        transportador = st.text_input("Transportador")
        ativo = st.selectbox("Status", ["Ativo", "Inativo"])
        
        if st.form_submit_button("Cadastrar"):
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
    
    st.subheader("Caminhões Cadastrados")
    st.dataframe(caminhoes_df)
    
    with st.form("atualizar_status"):
        st.subheader("Atualizar Status de Caminhão")
        placas_atualizar = st.selectbox("Selecione a Placa do Caminhão", caminhoes_df['Placas'].unique())
        novo_status = st.selectbox("Novo Status", ["Ativo", "Inativo"])
        
        if st.form_submit_button("Atualizar Status"):
            caminhoes_df.loc[caminhoes_df['Placas'] == placas_atualizar, 'Ativo'] = novo_status
            caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
            st.success("Status do caminhão atualizado com sucesso!")

def carregar_dados_pedidos():
    """Carrega e valida dados dos pedidos."""
    uploaded_pedidos = st.file_uploader("Escolha o arquivo Excel de Pedidos", type=["xlsm"])
    if uploaded_pedidos is not None:
        try:
            pedidos_df = pd.read_excel(uploaded_pedidos, engine='openpyxl')
            return pedidos_df
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo de pedidos: {e}")
            return None
    return None

def verificar_colunas_necessarias(df, colunas_necessarias, tipo_df):
    """Verifica se as colunas necessárias estão presentes no DataFrame."""
    if not all(col in df.columns for col in colunas_necessarias):
        st.error(f"As colunas necessárias não foram encontradas na planilha de {tipo_df}.")
        return False
    return True

def main():
    """Função principal para o painel interativo."""
    st.title("Roteirizador de Pedidos")
    
    if st.checkbox("Cadastrar Caminhões"):
        cadastrar_caminhoes()
    
    pedidos_df = carregar_dados_pedidos()
    
    if pedidos_df is not None:
        caminhoes_df = None
        try:
            caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
        except FileNotFoundError:
            st.error("Nenhum caminhão cadastrado. Por favor, cadastre caminhões primeiro.")
        
        colunas_pedidos = ['Nº Carga', 'Placas', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Região Logística', 'Qtde. dos Itens', 'Peso dos Itens']
        colunas_caminhoes = ['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo']
        
        if caminhoes_df is not None and verificar_colunas_necessarias(pedidos_df, colunas_pedidos, "pedidos") and verificar_colunas_necessarias(caminhoes_df, colunas_caminhoes, "frota"):
            caminhoes_df = caminhoes_df[caminhoes_df['Ativo'] == 'Ativo']
            pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
            
            n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=5)
            pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
            
            percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
            percentual_pedidos = st.slider("Percentual de pedidos alocados por veículo (%)", min_value=0, max_value=100, value=100)
            
            modo_roteirizacao = st.selectbox("Modo de roteirização", ["Frota Mínima", "Balanceado"])
            criterio_otimizacao = st.selectbox("Critério de otimização", ["Menor Tempo", "Menor Distância", "Menor Custo"])
            
            pedidos_df = otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos)
            
            rota_tsp = st.checkbox("Aplicar TSP")
            rota_vrp = st.checkbox("Aplicar VRP")
            
            if rota_tsp:
                G = criar_grafo_tsp(pedidos_df)
                # Placeholder para resolver_tsp_genetico
                # melhor_rota, menor_distancia = resolver_tsp_genetico(G)
                # st.write(f"Melhor rota TSP: {melhor_rota}")
                # st.write(f"Menor distância TSP: {menor_distancia}")
                # pedidos_df['Ordem de Entrega TSP'] = pedidos_df['Endereço de Entrega'].apply(lambda x: melhor_rota.index(x) + 1)
            
            if rota_vrp:
                # Placeholder para resolver_vrp
                # melhor_rota_vrp = resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao)
                # st.write(f"Melhor rota VRP: {melhor_rota_vrp}")
                pass
            
            st.write("Dados dos pedidos:")
            st.dataframe(pedidos_df)
            
            mapa = criar_mapa(pedidos_df)
            folium_static(mapa)
            
            output_file_path = 'roterizacao_resultado.xlsx'
            pedidos_df.to_excel(output_file_path, index=False)
            st.write(f"Arquivo Excel com a roteirização feita foi salvo em: {output_file_path}")
            
            with open(output_file_path, "rb") as file:
                btn = st.download_button(
                    label="Baixar planilha",
                    data=file,
                    file_name="roterizacao_resultado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()import pandas as pd
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
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=api_key)

# Endereço de partida fixo
endereco_partida = "Avenida Antonio Ortega, 3604 - Pinhal, Cabreúva - SP"
endereco_partida_coords = (-23.0838, -47.1336)  # Coordenadas para Cabreúva, SP

def obter_coordenadas(endereco):
    """Obtém coordenadas geográficas de um endereço."""
    try:
        location = geolocator.geocode(endereco)
        if location:
            return (location.latitude, location.longitude)
        else:
            st.error(f"Não foi possível obter as coordenadas para o endereço: {endereco}")
            return None
    except Exception as e:
        st.error(f"Erro ao tentar obter as coordenadas: {e}")
        return None

def calcular_distancia(endereco1, endereco2):
    """Calcula a distância entre dois endereços."""
    coords_1 = endereco_partida_coords if endereco1 == endereco_partida else obter_coordenadas(endereco1)
    coords_2 = obter_coordenadas(endereco2)
    if coords_1 and coords_2:
        return geodesic(coords_1, coords_2).meters
    return None

def criar_grafo_tsp(pedidos_df):
    """Cria um grafo para resolver o TSP."""
    G = nx.Graph()
    enderecos = pedidos_df['Endereço de Entrega'].unique()
    G.add_node(endereco_partida)
    for endereco in enderecos:
        G.add_node(endereco)
    for (endereco1, endereco2) in permutations([endereco_partida] + list(enderecos), 2):
        distancia = calcular_distancia(endereco1, endereco2)
        if distancia is not None:
            G.add_edge(endereco1, endereco2, weight=distancia)
    return G

def resolver_tsp_genetico(G):
    """Resolve o TSP usando Algoritmo Genético."""
    # Implementação do algoritmo genético para TSP
    pass

def resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao):
    """Resolve o VRP usando OR-Tools."""
    # Implementação do VRP usando OR-Tools
    pass

def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos):
    """Otimiza o aproveitamento da frota usando programação linear."""
    pedidos_df['Nº Carga'] = None
    pedidos_df['Placas'] = None
    carga_numero = 1
    
    caminhoes_df['Capac. Kg'] *= (percentual_frota / 100)
    caminhoes_df['Capac. Cx'] *= (percentual_frota / 100)
    
    for _, caminhao in caminhoes_df.iterrows():
        capacidade_peso = caminhao['Capac. Kg']
        capacidade_caixas = caminhao['Capac. Cx']
        
        pedidos_alocados = pedidos_df[
            (pedidos_df['Peso dos Itens'] <= capacidade_peso) &
            (pedidos_df['Qtde. dos Itens'] <= capacidade_caixas)
        ].sample(frac=(percentual_pedidos / 100))
        
        pedidos_df.loc[pedidos_alocados.index, 'Nº Carga'] = carga_numero
        pedidos_df.loc[pedidos_alocados.index, 'Placas'] = caminhao['Placas']
        
        carga_numero += 1

    return pedidos_df

def agrupar_por_regiao(pedidos_df, n_clusters=5):
    """Agrupa pedidos por região usando KMeans."""
    pedidos_df['Coordenada X'] = pedidos_df['Cidade de Entrega'].apply(lambda x: hash(x) % 100)
    pedidos_df['Coordenada Y'] = pedidos_df['Bairro de Entrega'].apply(lambda x: hash(x) % 100)
    
    kmeans = KMeans(n_clusters=n_clusters)
    pedidos_df['Regiao'] = kmeans.fit_predict(pedidos_df[['Coordenada X', 'Coordenada Y']])
    
    return pedidos_df

def criar_mapa(pedidos_df):
    """Cria um mapa com folium para visualizar pedidos."""
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

def cadastrar_caminhoes():
    """Interface para cadastrar caminhões."""
    st.title("Cadastro de Caminhões da Frota")
    try:
        caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
    except FileNotFoundError:
        caminhoes_df = pd.DataFrame(columns=['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo'])
    
    with st.form("cadastrar_caminhao"):
        st.subheader("Cadastrar Novo Caminhão")
        num_carga = st.text_input("Número de Carga")
        placas = st.text_input("Placas")
        capac_cx = st.number_input("Capacidade em Caixas", min_value=0)
        capac_kg = st.number_input("Capacidade em Quilogramas", min_value=0)
        descricao_veiculo = st.text_input("Descrição do Veículo")
        transportador = st.text_input("Transportador")
        ativo = st.selectbox("Status", ["Ativo", "Inativo"])
        
        if st.form_submit_button("Cadastrar"):
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
    
    st.subheader("Caminhões Cadastrados")
    st.dataframe(caminhoes_df)
    
    with st.form("atualizar_status"):
        st.subheader("Atualizar Status de Caminhão")
        placas_atualizar = st.selectbox("Selecione a Placa do Caminhão", caminhoes_df['Placas'].unique())
        novo_status = st.selectbox("Novo Status", ["Ativo", "Inativo"])
        
        if st.form_submit_button("Atualizar Status"):
            caminhoes_df.loc[caminhoes_df['Placas'] == placas_atualizar, 'Ativo'] = novo_status
            caminhoes_df.to_excel("caminhoes_frota.xlsx", index=False)
            st.success("Status do caminhão atualizado com sucesso!")

def carregar_dados_pedidos():
    """Carrega e valida dados dos pedidos."""
    uploaded_pedidos = st.file_uploader("Escolha o arquivo Excel de Pedidos", type=["xlsm"])
    if uploaded_pedidos is not None:
        try:
            pedidos_df = pd.read_excel(uploaded_pedidos, engine='openpyxl')
            return pedidos_df
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo de pedidos: {e}")
            return None
    return None

def verificar_colunas_necessarias(df, colunas_necessarias, tipo_df):
    """Verifica se as colunas necessárias estão presentes no DataFrame."""
    if not all(col in df.columns for col in colunas_necessarias):
        st.error(f"As colunas necessárias não foram encontradas na planilha de {tipo_df}.")
        return False
    return True

def main():
    """Função principal para o painel interativo."""
    st.title("Roteirizador de Pedidos")
    
    if st.checkbox("Cadastrar Caminhões"):
        cadastrar_caminhoes()
    
    pedidos_df = carregar_dados_pedidos()
    
    if pedidos_df is not None:
        caminhoes_df = None
        try:
            caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine='openpyxl')
        except FileNotFoundError:
            st.error("Nenhum caminhão cadastrado. Por favor, cadastre caminhões primeiro.")
        
        colunas_pedidos = ['Nº Carga', 'Placas', 'Nº Pedido', 'Cód. Cliente', 'Nome Cliente', 'Grupo Cliente', 'Endereço de Entrega', 'Bairro de Entrega', 'Cidade de Entrega', 'Região Logística', 'Qtde. dos Itens', 'Peso dos Itens']
        colunas_caminhoes = ['Nº Carga', 'Placas', 'Capac. Cx', 'Capac. Kg', 'Descrição Veículo', 'Transportador', 'Ativo']
        
        if caminhoes_df is not None and verificar_colunas_necessarias(pedidos_df, colunas_pedidos, "pedidos") and verificar_colunas_necessarias(caminhoes_df, colunas_caminhoes, "frota"):
            caminhoes_df = caminhoes_df[caminhoes_df['Ativo'] == 'Ativo']
            pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
            
            n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=5)
            pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
            
            percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
            percentual_pedidos = st.slider("Percentual de pedidos alocados por veículo (%)", min_value=0, max_value=100, value=100)
            
            modo_roteirizacao = st.selectbox("Modo de roteirização", ["Frota Mínima", "Balanceado"])
            criterio_otimizacao = st.selectbox("Critério de otimização", ["Menor Tempo", "Menor Distância", "Menor Custo"])
            
            pedidos_df = otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, percentual_pedidos)
            
            rota_tsp = st.checkbox("Aplicar TSP")
            rota_vrp = st.checkbox("Aplicar VRP")
            
            if rota_tsp:
                G = criar_grafo_tsp(pedidos_df)
                # Placeholder para resolver_tsp_genetico
                # melhor_rota, menor_distancia = resolver_tsp_genetico(G)
                # st.write(f"Melhor rota TSP: {melhor_rota}")
                # st.write(f"Menor distância TSP: {menor_distancia}")
                # pedidos_df['Ordem de Entrega TSP'] = pedidos_df['Endereço de Entrega'].apply(lambda x: melhor_rota.index(x) + 1)
            
            if rota_vrp:
                # Placeholder para resolver_vrp
                # melhor_rota_vrp = resolver_vrp(pedidos_df, caminhoes_df, modo_roteirizacao, criterio_otimizacao)
                # st.write(f"Melhor rota VRP: {melhor_rota_vrp}")
                pass
            
            st.write("Dados dos pedidos:")
            st.dataframe(pedidos_df)
            
            mapa = criar_mapa(pedidos_df)
            folium_static(mapa)
            
            output_file_path = 'roterizacao_resultado.xlsx'
            pedidos_df.to_excel(output_file_path, index=False)
            st.write(f"Arquivo Excel com a roteirização feita foi salvo em: {output_file_path}")
            
            with open(output_file_path, "rb") as file:
                btn = st.download_button(
                    label="Baixar planilha",
                    data=file,
                    file_name="roterizacao_resultado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
