from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import io
import folium

app = Flask(__name__)

UPLOAD_FOLDER = "database"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Função placeholder para o algoritmo genético de montagem de cargas
def run_genetic_algorithm(pedidos_df, caminhoes_df):
    # Simula uma solução viável
    # Aqui você implementaria: inicialização, fitness, seleção, cruzamento, mutação e critério de parada
    solucao = {
        "solucao": "Alocação otimizada",
        "detalhes": {
            "total_pedidos": len(pedidos_df),
            "total_caminhoes": len(caminhoes_df)
        }
    }
    return solucao

# Função placeholder para gerar um mapa interativo com Folium
def gerar_mapa(pedidos_df):
    # Exemplo: usa a primeira linha como centro do mapa
    if pedidos_df.empty:
        return folium.Map(location=[0,0], zoom_start=2)
    centro = [pedidos_df.iloc[0]['Latitude'], pedidos_df.iloc[0]['Longitude']]
    mapa = folium.Map(location=centro, zoom_start=12)
    for _, row in pedidos_df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row.get('Endereço Completo', 'Sem endereço'),
            icon=folium.Icon(color='blue')
        ).add_to(mapa)
    return mapa

@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Endpoint para receber os arquivos:
      - Pedidos.xlsx
      - Caminhoes.xlsx
      - IA.xlsx
    """
    result = {}
    for nome_arquivo in ["Pedidos.xlsx", "Caminhoes.xlsx", "IA.xlsx"]:
        if nome_arquivo in request.files:
            file = request.files[nome_arquivo]
            caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
            file.save(caminho)
            result[nome_arquivo] = "Uploaded successfully"
        else:
            result[nome_arquivo] = "File missing"
    return jsonify(result)

@app.route('/resultado', methods=['GET'])
def get_resultado():
    """
    Endpoint que retorna a montagem de cargas gerada pelo algoritmo genético
    """
    try:
        pedidos_path = os.path.join(UPLOAD_FOLDER, "Pedidos.xlsx")
        caminhoes_path = os.path.join(UPLOAD_FOLDER, "Caminhoes.xlsx")
        pedidos_df = pd.read_excel(pedidos_path, engine="openpyxl")
        caminhoes_df = pd.read_excel(caminhoes_path, engine="openpyxl")
    except Exception as e:
        return jsonify({"error": f"Erro ao ler os arquivos: {str(e)}"}), 400
    
    # Aqui você pode aplicar pré-processamento, validação e conversão de endereços em coordenadas.
    # Para este exemplo, assumimos que o arquivo Pedidos.xlsx já contém colunas 'Latitude' e 'Longitude'.
    solucao = run_genetic_algorithm(pedidos_df, caminhoes_df)
    return jsonify(solucao)

@app.route('/mapa', methods=['GET'])
def get_mapa():
    """
    Endpoint que gera e retorna um mapa interativo (HTML) com as rotas otimizadas
    """
    try:
        pedidos_path = os.path.join(UPLOAD_FOLDER, "Pedidos.xlsx")
        pedidos_df = pd.read_excel(pedidos_path, engine="openpyxl")
    except Exception as e:
        return jsonify({"error": f"Erro ao ler o arquivo de pedidos: {str(e)}"}), 400
    
    mapa = gerar_mapa(pedidos_df)
    # Retorna o HTML do mapa para ser visualizado no navegador
    return mapa._repr_html_()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)