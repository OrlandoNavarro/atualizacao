from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import io
import folium
import numpy as np
from geopy.geocoders import Nominatim
import random
from datetime import datetime

app = Flask(__name__)

DATABASE_FOLDER = "database"
if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)

# ---------- Funções de Leitura e Validação de Planilhas ----------

def ler_planilha(nome_arquivo, colunas_obrigatorias):
    """
    Lê um arquivo .xlsx e valida as colunas obrigatórias.
    Retorna o dataframe lido ou lança exceção caso falte alguma coluna.
    """
    caminho = os.path.join(DATABASE_FOLDER, nome_arquivo)
    df = pd.read_excel(caminho, engine="openpyxl")
    for coluna in colunas_obrigatorias:
        if coluna not in df.columns:
            raise ValueError(f"Coluna obrigatória '{coluna}' não encontrada no arquivo {nome_arquivo}.")
    return df

# ---------- Geocodificação com Fallback e Cache ----------

geolocator = Nominatim(user_agent="logistica_app")

def geocode_endereco(endereco):
    """
    Converte endereço em latitude/longitude.
    Se falhar, retorna None.
    """
    try:
        local = geolocator.geocode(endereco)
        if local:
            return (local.latitude, local.longitude)
    except Exception as e:
        print(f"Erro na geocodificação: {e}")
    return None

def converter_enderecos(df, endereco_coluna="Endereço Completo", cache_path="coordenadas_cache.xlsx"):
    """
    Converte os endereços do dataframe e atualiza as colunas 'Latitude' e 'Longitude'.
    Utiliza um arquivo de cache para não repetir geocodificação.
    """
    cache_file = os.path.join(DATABASE_FOLDER, cache_path)
    if os.path.exists(cache_file):
        cache_df = pd.read_excel(cache_file, engine="openpyxl")
        cache = dict(zip(cache_df['Endereço'], zip(cache_df['Latitude'], cache_df['Longitude'])))
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
    # Atualiza cache (salva)
    cache_df = pd.DataFrame(list(cache.items()), columns=['Endereço', 'Coordenadas'])
    cache_df[['Latitude','Longitude']] = pd.DataFrame(cache_df['Coordenadas'].tolist(), index=cache_df.index)
    cache_df.drop(columns=['Coordenadas'], inplace=True)
    cache_df.to_excel(cache_file, index=False)
    return df

# ---------- Pré-processamento de Dados ----------

def preprocessar_dados(df):
    """
    Realiza pré-processamento:
    - Conversão de dados categóricos;
    - Normalização de volume, peso e distância (exemplo);
    - Tratamento de dados faltantes.
    """
    df.fillna(0, inplace=True)
    for coluna in ['Peso dos Itens', 'Volume', 'Distância']:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
            if df[coluna].max() > 0:
                df[coluna] = df[coluna] / df[coluna].max()
    return df

# ---------- Algoritmo Genético para Montagem de Cargas ----------

def populacao_inicial(pedidos_df, caminhoes_df, tamanho=50):
    """
    Inicializa uma população aleatória de soluções viáveis.
    Cada indivíduo é representado por um dicionário mapeando IDs de pedidos para IDs de caminhões.
    """
    population = []
    pedidos_ids = pedidos_df.index.tolist()
    caminhoes_ids = caminhoes_df.index.tolist()
    for _ in range(tamanho):
        sol = {pedido: random.choice(caminhoes_ids) for pedido in pedidos_ids}
        population.append(sol)
    return population

def avaliacao_fitness(solucao, pedidos_df, caminhoes_df):
    """
    Avalia uma solução com base em critérios:
    - Economia, ocupação dos caminhões e distância.
    (Ajuste esta função conforme os requisitos reais.)
    """
    fitness = 0
    for pedido, caminhao in solucao.items():
        fitness += pedidos_df.loc[pedido, "Peso dos Itens"]
    return 1.0 / (fitness + 1e-6)

def selecionar(population, fitnesses, num=10):
    sorted_population = [sol for _, sol in sorted(zip(fitnesses, population), key=lambda x: x[0], reverse=True)]
    return sorted_population[:num]

def cruzar(sol1, sol2):
    filho = {}
    for key in sol1.keys():
        filho[key] = sol1[key] if random.random() < 0.5 else sol2[key]
    return filho

def mutacao(solucao, caminhoes_ids, taxa=0.1):
    for pedido in solucao.keys():
        if random.random() < taxa:
            solucao[pedido] = random.choice(caminhoes_ids)
    return solucao

def run_genetic_algorithm(pedidos_df, caminhoes_df, geracoes=100, tamanho_pop=50):
    population = populacao_inicial(pedidos_df, caminhoes_df, tamanho=tamanho_pop)
    pedidos_ids = pedidos_df.index.tolist()
    caminhoes_ids = caminhoes_df.index.tolist()
    melhor_solucao = None
    melhor_fitness = -np.inf
    for _ in range(geracoes):
        fitnesses = [avaliacao_fitness(sol, pedidos_df, caminhoes_df) for sol in population]
        melhores = selecionar(population, fitnesses, num=10)
        nova_pop = []
        for _ in range(tamanho_pop):
            sol1, sol2 = random.sample(melhores, 2)
            filho = cruzar(sol1, sol2)
            filho = mutacao(filho, caminhoes_ids)
            nova_pop.append(filho)
        population = nova_pop
        melhor_iter = max(fitnesses)
        if melhor_iter > melhor_fitness:
            melhor_fitness = melhor_iter
            melhor_solucao = population[fitnesses.index(melhor_iter)]
    return {"solucao": melhor_solucao, "fitness": melhor_fitness}

# ---------- IA de Aprendizado Supervisionado (Placeholder) ----------

def treinar_modelo_ia(ia_df):
    modelo = {"modelo": "dummy", "treinado_em": datetime.now().isoformat()}
    return modelo

def ajustar_fitness_com_ia(solucao, modelo):
    solucao["ajuste_ia"] = "simulação"
    return solucao

# ---------- Função para Gerar Mapa Interativo com Folium ----------

def gerar_mapa(pedidos_df):
    if pedidos_df.empty:
        return folium.Map(location=[0, 0], zoom_start=2)
    centro = [pedidos_df.iloc[0]['Latitude'], pedidos_df.iloc[0]['Longitude']]
    mapa = folium.Map(location=centro, zoom_start=12)
    for _, row in pedidos_df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row.get("Endereço Completo", "Sem endereço"),
            icon=folium.Icon(color="blue")
        ).add_to(mapa)
    return mapa

# ---------- Endpoints da API REST ----------

@app.route('/upload', methods=['POST'])
def upload_files():
    """
    POST /upload: Recebe os arquivos Pedidos.xlsx, Caminhoes.xlsx, IA.xlsx e os salva na pasta database.
    """
    result = {}
    for nome in ["Pedidos.xlsx", "Caminhoes.xlsx", "IA.xlsx"]:
        if nome in request.files:
            file = request.files[nome]
            caminho = os.path.join(DATABASE_FOLDER, nome)
            file.save(caminho)
            result[nome] = "Arquivo enviado com sucesso"
        else:
            result[nome] = "Arquivo não enviado"
    return jsonify(result)

@app.route('/resultado', methods=['GET'])
def get_resultado():
    """
    GET /resultado: Lê os arquivos de Pedidos e Caminhões, pré-processa os dados,
    executa o algoritmo genético e retorna a solução gerada.
    """
    try:
        pedidos_df = ler_planilha("Pedidos.xlsx", ["Endereço de Entrega", "Bairro de Entrega", "Cidade de Entrega", "Peso dos Itens"])
        caminhoes_df = ler_planilha("Caminhoes.xlsx", ["Placa", "Capac. Kg", "Capac. Cx", "Disponível"])
    except Exception as e:
        return jsonify({"error": f"Erro na leitura dos arquivos: {str(e)}"}), 400

    pedidos_df["Endereço Completo"] = pedidos_df["Endereço de Entrega"] + ", " + pedidos_df["Bairro de Entrega"] + ", " + pedidos_df["Cidade de Entrega"]
    pedidos_df = converter_enderecos(pedidos_df)
    pedidos_df = preprocessar_dados(pedidos_df)

    solucao = run_genetic_algorithm(pedidos_df, caminhoes_df)
    try:
        ia_df = ler_planilha("IA.xlsx", ["Referencia"])
        modelo = treinar_modelo_ia(ia_df)
        solucao = ajustar_fitness_com_ia(solucao, modelo)
    except Exception as e:
        print("Erro no treinamento do modelo IA:", e)

    return jsonify(solucao)

@app.route('/mapa', methods=['GET'])
def get_mapa():
    """
    GET /mapa: Gera um mapa interativo (HTML) com as rotas otimizadas com base na planilha de pedidos.
    """
    try:
        pedidos_df = ler_planilha("Pedidos.xlsx", ["Endereço de Entrega", "Bairro de Entrega", "Cidade de Entrega"])
        pedidos_df["Endereço Completo"] = pedidos_df["Endereço de Entrega"] + ", " + pedidos_df["Bairro de Entrega"] + ", " + pedidos_df["Cidade de Entrega"]
        pedidos_df = converter_enderecos(pedidos_df)
    except Exception as e:
        return jsonify({"error": f"Erro ao ler ou processar os pedidos: {str(e)}"}), 400

    mapa = gerar_mapa(pedidos_df)
    return mapa._repr_html_()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)