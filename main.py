import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import requests
import time
import datetime
import os  # Importa o módulo para verificar a existência de arquivos

from gerenciamento_frota import cadastrar_caminhoes
from subir_pedidos import processar_pedidos
import ia_analise_pedidos as ia
from database.ia_analise_pedidos import atualizar_pedido, carregar_coordenadas_salvas, salvar_coordenadas  # Importa as funções necessárias

# Exemplo de função para definir a ordem de entrega por carga
def definir_ordem_por_carga(pedidos_df, ordem_tsp):
    """
    Define a coluna 'Ordem de Entrega TSP' com base na ordem definida pelo TSP,
    agrupando os pedidos por 'Carga' e atribuindo uma sequência para cada entrega.
    
    Parâmetros:
      pedidos_df (DataFrame): DataFrame que contém a coluna 'Carga' e 'Endereço Completo'.
      ordem_tsp (list): Lista com os endereços na ordem definida pelo algoritmo TSP.
      
    Retorna:
      DataFrame: Com a coluna 'Ordem de Entrega TSP' atualizada.
    """
    # Cria um dicionário para mapeamento do endereço para sua posição na melhor rota
    rota_indices = {endereco: idx for idx, endereco in enumerate(ordem_tsp)}
    
    # Inicializa a coluna de ordem vazia
    pedidos_df['Ordem de Entrega TSP'] = ""
    
    # Para cada carga, ordena os pedidos conforme a posição na melhor rota e atribui uma sequência
    for carga in pedidos_df['Carga'].unique():
        mask = pedidos_df['Carga'] == carga
        df_carga = pedidos_df.loc[mask].copy()
        # Ordena os pedidos desta carga com base na posição encontrada na melhor rota.
        df_carga = df_carga.sort_values(
            by='Endereço Completo', 
            key=lambda col: col.map(lambda x: rota_indices.get(x, float('inf')))
        )
        # Atribui sequência numérica para cada pedido do grupo
        for seq, idx in enumerate(df_carga.index, start=1):
            pedidos_df.at[idx, 'Ordem de Entrega TSP'] = f"{carga}-{seq}"
    
    return pedidos_df

def main():
    st.title("Roteirizador de Pedidos")
    
    st.markdown(
        """
        <style>
        div[data-baseweb="radio"] ul {
            list-style: none;
            padding-left: 0;
        }
        div[data-baseweb="radio"] li {
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Menu lateral
    menu_opcao = st.sidebar.radio("Menu", options=[
        "Dashboard", 
        "Cadastro da Frota", 
        "IA Analise",
        "API REST"
    ])
    
    if menu_opcao == "Dashboard":
        st.header("Dashboard - Envio de Pedidos")
        st.write("Bem-vindo! Envie a planilha de pedidos para iniciar:")
        pedidos_result = processar_pedidos()
        if pedidos_result is None:
            st.info("Aguardando envio da planilha de pedidos.")
        else:
            try:
                pedidos_df, coordenadas_salvas = pedidos_result
                
                # Carrega coordenadas salvas do arquivo
                st.write("Carregando coordenadas salvas...")
                coordenadas_salvas = carregar_coordenadas_salvas("database/coordenadas_salvas.xlsx")
                st.write("Coordenadas carregadas com sucesso.")
                
                with st.spinner("Obtendo coordenadas..."):
                    # Aqui você pode implementar a lógica para obter coordenadas de outra forma
                    # por exemplo, diretamente de um banco de dados ou serviço externo
                    pass
                
                if pedidos_df['Latitude'].isnull().any() or pedidos_df['Longitude'].isnull().any():
                    st.warning("Alguns endereços não obtiveram coordenadas. As correções podem ser feitas posteriormente.")
                
                # Carrega a frota cadastrada
                try:
                    caminhoes_df = pd.read_excel("caminhoes_frota.xlsx", engine="openpyxl")
                except FileNotFoundError:
                    st.error("Nenhum caminhão cadastrado. Cadastre a frota na aba de gerenciamento.")
                    return

                # Opções de configuração
                n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=5)
                percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
                max_pedidos = st.slider("Número máximo de pedidos por veículo", min_value=1, max_value=30, value=12)
                aplicar_tsp = st.checkbox("Aplicar TSP")
                aplicar_vrp = st.checkbox("Aplicar VRP")
                
                if st.button("Roteirizar"):
                    pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
                    pedidos_df = ia.agrupar_por_regiao(pedidos_df, n_clusters)
                    pedidos_df = ia.otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, max_pedidos, n_clusters)
                    
                    if aplicar_tsp:
                        G = ia.criar_grafo_tsp(pedidos_df)
                        melhor_rota, menor_distancia = ia.resolver_tsp_genetico(G)
                        st.write("Melhor rota TSP:")
                        st.write("\n".join(melhor_rota))
                        st.write(f"Menor distância TSP: {menor_distancia}")
                        pedidos_df['Ordem de Entrega TSP'] = pedidos_df['Endereço Completo'].apply(lambda x: melhor_rota.index(x) + 1)
                    
                    if aplicar_vrp:
                        rota_vrp = ia.resolver_vrp(pedidos_df, caminhoes_df)
                        st.write(f"Melhor rota VRP: {rota_vrp}")
                    
                    st.write("Dados dos Pedidos:")
                    st.dataframe(pedidos_df)
                    
                    mapa = ia.criar_mapa(pedidos_df)
                    folium_static(mapa)
                    
                    output_file_path = "roterizacao_resultado.xlsx"
                    pedidos_df.to_excel(output_file_path, index=False)
                    st.write(f"Arquivo salvo: {output_file_path}")
                    with open(output_file_path, "rb") as file:
                        st.download_button("Baixar planilha", data=file, file_name="roterizacao_resultado.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
        
        # Abas para Gerenciamento da Frota e Upload de Roteirizações
        if st.checkbox("Cadastrar Caminhões"):
            cadastrar_caminhoes()
        
        if st.checkbox("Subir Planilhas de Roteirizações"):
            # Aqui você pode incluir funcionalidades extras para roteirizações
            st.info("Funcionalidade de upload de roteirizações a ser implementada.")
    
    elif menu_opcao == "Cadastro da Frota":
        st.header("Cadastro da Frota")
        from gerenciamento_frota import cadastrar_caminhoes
        if st.checkbox("Cadastrar Caminhões"):
            cadastrar_caminhoes()
    
    elif menu_opcao == "IA Analise":
        st.header("IA Analise")
        st.write("Envie a planilha de pedidos para análise e edite os dados, se necessário:")
        pedidos_result = processar_pedidos()
        if pedidos_result is None:
            st.info("Aguardando envio da planilha de pedidos.")
        else:
            try:
                pedidos_df, coordenadas_salvas = pedidos_result
                with st.spinner("Atualizando coordenadas..."):
                    # Aqui você pode implementar a lógica para obter coordenadas de outra forma
                    # por exemplo, diretamente de um banco de dados ou serviço externo
                    pass
                pedidos_df['Latitude'] = pedidos_df['Latitude'].fillna(0)
                pedidos_df['Longitude'] = pedidos_df['Longitude'].fillna(0)
                salvar_coordenadas(coordenadas_salvas, "database/coordenadas_salvas.xlsx")
                
                # Verifica se as colunas necessárias existem; caso contrário, cria-as
                for col in ['Latitude', 'Longitude']:
                    if col not in pedidos_df.columns:
                        st.warning(f"A coluna '{col}' não foi encontrada. Ela será criada com valor 0.")
                        pedidos_df[col] = 0

                st.dataframe(pedidos_df)
                if st.button("Salvar alterações na planilha"):
                    try:
                        # Garante que o diretório "database" exista
                        os.makedirs("database", exist_ok=True)
                        st.write("Diretório 'database' verificado/criado com sucesso.")
                        
                        # Salva o arquivo no caminho especificado
                        pedidos_df.to_excel("database/Pedidos.xlsx", index=False)
                        st.success("Planilha editada e salva com sucesso!")

                        # Atualiza os pedidos no banco de dados
                        for index, row in pedidos_df.iterrows():
                            atualizar_pedido(
                                row['id'],
                                row['Endereço Completo'],
                                row['Latitude'],
                                row['Longitude'],
                                row['Peso dos Itens'],
                                row['Ordem de Entrega TSP']
                            )
                        st.success("Dados atualizados no banco de dados com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar a planilha: {e}")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif menu_opcao == "API REST":
        st.header("Interação com API REST")
        st.write("Teste os endpoints:")
        st.markdown("""
        - **POST /upload**: Faz upload dos arquivos (Pedidos.xlsx, Caminhoes.xlsx, IA.xlsx).
        - **GET /resultado**: Retorna a solução do algoritmo genético.
        - **GET /mapa**: Exibe o mapa interativo.
        """)
        if st.button("Testar /resultado"):
            try:
                resposta = requests.get("http://localhost:5000/resultado")
                st.json(resposta.json())
            except Exception as e:
                st.error(f"Erro na requisição: {e}")

if __name__ == "__main__":
    main()
