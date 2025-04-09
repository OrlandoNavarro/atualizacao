import sqlite3
import pandas as pd
import os

def conectar_banco():
    conn = sqlite3.connect('banco_de_dados.db')
    return conn

def criar_tabelas():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endereco TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        peso_itens REAL,
        ordem_entrega INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo TEXT NOT NULL,
        capacidade REAL NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def inserir_pedido(endereco, latitude, longitude, peso_itens, ordem_entrega):
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO pedidos (endereco, latitude, longitude, peso_itens, ordem_entrega)
    VALUES (?, ?, ?, ?, ?)
    ''', (endereco, latitude, longitude, peso_itens, ordem_entrega))
    
    conn.commit()
    conn.close()

def atualizar_pedido(id, endereco, latitude, longitude, peso_itens, ordem_entrega):
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE pedidos
    SET endereco = ?, latitude = ?, longitude = ?, peso_itens = ?, ordem_entrega = ?
    WHERE id = ?
    ''', (endereco, latitude, longitude, peso_itens, ordem_entrega, id))
    
    conn.commit()
    conn.close()

def inserir_caminhao(modelo, capacidade):
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO frota (modelo, capacidade)
    VALUES (?, ?)
    ''', (modelo, capacidade))
    
    conn.commit()
    conn.close()

def consultar_pedidos():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pedidos')
    resultados = cursor.fetchall()
    
    conn.close()
    return resultados

def consultar_frota():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM frota')
    resultados = cursor.fetchall()
    
    conn.close()
    return resultados

def carregar_coordenadas_salvas(arquivo):
    """
    Carrega as coordenadas salvas de um arquivo Excel.
    
    Parâmetros:
      arquivo (str): Caminho do arquivo Excel.
      
    Retorna:
      dict: Dicionário com coordenadas salvas.
    """
    if os.path.exists(arquivo):
        df = pd.read_excel(arquivo)
        if 'Endereco' in df.columns and 'Latitude' in df.columns and 'Longitude' in df.columns:
            return dict(zip(df['Endereco'], zip(df['Latitude'], df['Longitude'])))
    return {}

def salvar_coordenadas(coordenadas_salvas, arquivo):
    """
    Salva as coordenadas em um arquivo Excel.
    
    Parâmetros:
      coordenadas_salvas (dict): Dicionário com coordenadas salvas.
      arquivo (str): Caminho do arquivo Excel.
    """
    df = pd.DataFrame(coordenadas_salvas.items(), columns=['Endereco', 'Coordenadas'])
    df[['Latitude', 'Longitude']] = pd.DataFrame(df['Coordenadas'].tolist(), index=df.index)
    df.drop(columns=['Coordenadas'], inplace=True)
    df.to_excel(arquivo, index=False)

def obter_coordenadas_com_fallback(endereco, coordenadas_salvas):
    """
    Tenta obter as coordenadas de um endereço a partir de um arquivo salvo.
    Se não encontrar, consulta a API e salva as novas coordenadas.
    
    Parâmetros:
      endereco (str): Endereço completo.
      coordenadas_salvas (dict): Dicionário com coordenadas salvas.
      
    Retorna:
      tuple: (latitude, longitude)
    """
    # Verifica se o endereço já tem coordenadas salvas
    if endereco in coordenadas_salvas:
        return coordenadas_salvas[endereco]
    
    # Se não encontrar, consulta a API (substitua pela sua lógica de consulta)
    latitude, longitude = consulta_api_para_coordenadas(endereco)
    
    # Salva as novas coordenadas no dicionário
    coordenadas_salvas[endereco] = (latitude, longitude)
    
    return (latitude, longitude)

def consulta_api_para_coordenadas(endereco):
    """
    Consulta a API para obter as coordenadas de um endereço.
    (Substitua pela sua lógica de consulta à API)
    
    Parâmetros:
      endereco (str): Endereço completo.
      
    Retorna:
      tuple: (latitude, longitude)
    """
    # Exemplo de coordenadas fictícias (substitua pela sua implementação real)
    latitude = -23.55052
    longitude = -46.633308
    return (latitude, longitude)

criar_tabelas()
