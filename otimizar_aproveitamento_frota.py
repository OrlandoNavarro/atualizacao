import streamlit as st

def otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, max_pedidos, n_clusters=3):
    inicializar_colunas(pedidos_df)
    ajustar_capacidade_frota(caminhoes_df, percentual_frota)
    caminhoes_df = filtrar_caminhoes_disponiveis(caminhoes_df)
    pedidos_df = agrupar_por_regiao(pedidos_df, n_clusters)
    
    for regiao in pedidos_df['Regiao'].unique():
        pedidos_regiao = pedidos_df[pedidos_df['Regiao'] == regiao]
        alocar_pedidos_aos_caminhoes(pedidos_regiao, caminhoes_df, max_pedidos)
    
    verificar_alocacao(pedidos_df)
    return pedidos_df

def inicializar_colunas(pedidos_df):
    pedidos_df['Carga'] = 0
    pedidos_df['Placa'] = ""
    pedidos_df['carga_numero'] = 1

def ajustar_capacidade_frota(caminhoes_df, percentual_frota):
    caminhoes_df['Capac. Kg'] *= (percentual_frota / 100)
    caminhoes_df['Capac. Cx'] *= (percentual_frota / 100)

def filtrar_caminhoes_disponiveis(caminhoes_df):
    return caminhoes_df[caminhoes_df['Disponível'] == 'Sim']

def alocar_pedidos_aos_caminhoes(pedidos_regiao, caminhoes_df, max_pedidos):
    for _, caminhao in caminhoes_df.iterrows():
        capacidade_peso = caminhao['Capac. Kg']
        capacidade_caixas = caminhao['Capac. Cx']
        
        pedidos_alocados = pedidos_regiao[
            (pedidos_regiao['Peso dos Itens'] <= capacidade_peso) & 
            (pedidos_regiao['Qtde. dos Itens'] <= capacidade_caixas)
        ]
        pedidos_alocados = pedidos_alocados.sample(n=min(max_pedidos, len(pedidos_alocados)))
        
        if not pedidos_alocados.empty():
            atualizar_alocacao(pedidos_alocados, caminhao, pedidos_regiao)

def atualizar_alocacao(pedidos_alocados, caminhao, pedidos_regiao):
    pedidos_regiao.loc[pedidos_alocados.index, 'Carga'] = pedidos_regiao['carga_numero']
    pedidos_regiao.loc[pedidos_alocados.index, 'Placa'] = caminhao['Placa']
    caminhao['Capac. Kg'] -= pedidos_alocados['Peso dos Itens'].sum()
    caminhao['Capac. Cx'] -= pedidos_alocados['Qtde. dos Itens'].sum()
    pedidos_regiao['carga_numero'] += 1

def verificar_alocacao(pedidos_df):
    if pedidos_df['Placa'].isnull().any() or pedidos_df['Carga'].isnull().any():
        st.error("Não foi possível atribuir placas ou números de carga a alguns pedidos. Verifique os dados e tente novamente.")
