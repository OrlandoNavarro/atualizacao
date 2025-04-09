import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import requests
import time
import datetime
import os  # Importa o módulo para verificar a existência de arquivos

from gerenciamento_frota import cadastrar_caminhoes
from subir_pedidos import processar_pedidos, salvar_coordenadas
import ia_analise_pedidos as ia

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
            pedidos_df, coordenadas_salvas = pedidos_result
            
            with st.spinner("Obtendo coordenadas..."):
                pedidos_df['Latitude'] = pedidos_df['Endereço Completo'].apply(
                    lambda x: ia.obter_coordenadas_com_fallback(x, coordenadas_salvas)[0]
                )
                pedidos_df['Longitude'] = pedidos_df['Endereço Completo'].apply(
                    lambda x: ia.obter_coordenadas_com_fallback(x, coordenadas_salvas)[1]
                )
            pedidos_df['Latitude'] = pedidos_df['Latitude'].fillna(0)
            pedidos_df['Longitude'] = pedidos_df['Longitude'].fillna(0)
            salvar_coordenadas(coordenadas_salvas)
            
            st.write("Cabeçalho da planilha:", list(pedidos_df.columns))
            st.markdown("### Configurações para Roteirização")
            n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=1)
            percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
            max_pedidos = st.slider("Número máximo de pedidos por veículo", min_value=1, max_value=30, value=12)
            
            # Checkbox para aplicar o algoritmo TSP (Traveling Salesman Problem)
            aplicar_tsp = st.checkbox("Aplicar TSP")

            # Checkbox para aplicar o algoritmo VRP (Vehicle Routing Problem)
            aplicar_vrp = st.checkbox("Aplicar VRP")
            
            # Garante que as colunas 'Placa' e 'Carga' existam no DataFrame
            if 'Placa' not in pedidos_df.columns:
                st.warning("A coluna 'Placa' não foi encontrada. Ela será criada com valores vazios.")
                pedidos_df['Placa'] = ""

            if 'Carga' not in pedidos_df.columns:
                st.warning("A coluna 'Carga' não foi encontrada. Ela será criada com valores padrão.")
                pedidos_df['Carga'] = pedidos_df.index  # Define cada pedido como uma carga única por padrão

            # Se a coluna 'Placa' existir, aplica formatação para destacar as placas em rodízio
            if 'Placa' in pedidos_df.columns:
                today = datetime.datetime.now().weekday()  # Monday=0, ..., Sunday=6
                rodizio_map = {
                    0: {'1', '2'},
                    1: {'3', '4'},
                    2: {'5', '6'},
                    3: {'7', '8'},
                    4: {'9', '0'}
                }
                rodizio_numbers = rodizio_map.get(today, set())  # Se hoje for fim de semana, retorna conjunto vazio

                def rodizio_style(val):
                    if isinstance(val, str) and val.strip():
                        last_digit = val.strip()[-1]
                        if last_digit in rodizio_numbers:
                            return 'color: red'
                    return ''
                
                st.dataframe(pedidos_df.style.applymap(rodizio_style, subset=['Placa']))
            else:
                st.dataframe(pedidos_df)
            
if st.button("Roteirizar"):
    st.write("Roteirização em execução...")
    progress_bar = st.empty()
    for progresso in range(100):
        time.sleep(0.05)
        progress_bar.progress(progresso + 1)

    pedidos_df = pedidos_df[pedidos_df['Peso dos Itens'] > 0]
    if 'Placa' not in pedidos_df.columns or 'Carga' not in pedidos_df.columns:
        st.error("As colunas 'Placa' e 'Carga' são necessárias para a roteirização.")
        st.stop()

    cargas_por_placa = pedidos_df.groupby('Carga')['Placa'].nunique()
    cargas_invalidas = cargas_por_placa[cargas_por_placa > 1]
    if not cargas_invalidas.empty:
        st.error("Erro: Cada carga deve estar associada a apenas uma placa. Verifique os dados.")
        for carga, num_placas in cargas_invalidas.items():
            st.write(f"- Carga {carga}: {num_placas} placas associadas")
        st.stop()

    try:
        caminhoes_df = pd.read_excel("database/caminhoes_frota.xlsx", engine="openpyxl")
    except FileNotFoundError:
        st.error("Nenhum caminhão cadastrado. Cadastre a frota na opção 'Cadastro da Frota'.")
        return

    pedidos_df = ia.agrupar_por_regiao(pedidos_df, n_clusters)
    if 'Região' not in pedidos_df.columns or pedidos_df['Região'].isnull().all():
        st.error("A coluna 'Região' não foi criada ou está vazia. Verifique os dados e a função 'ia.agrupar_por_regiao'.")
        st.stop()

    pedidos_df = ia.otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, max_pedidos, n_clusters, distancia_maxima_km=550)
    regioes = pedidos_df['Região'].unique()
    placas_disponiveis = caminhoes_df['Placa'].tolist()
    if len(regioes) > len(placas_disponiveis):
        st.error("O número de regiões excede o número de caminhões disponíveis. Adicione mais caminhões.")
        st.stop()

    regiao_para_placa = {regiao: placas_disponiveis[i] for i, regiao in enumerate(regioes)}
    pedidos_df['Placa'] = pedidos_df['Região'].map(regiao_para_placa)
    regioes_por_caminhao = pedidos_df.groupby('Placa')['Região'].nunique()
    caminhoes_invalidos = regioes_por_caminhao[regioes_por_caminhao > 1]
    if not caminhoes_invalidos.empty():
        st.error("Erro: Um caminhão foi alocado a mais de uma região. Verifique os dados.")
        for placa, num_regioes in caminhoes_invalidos.items():
            st.write(f"- Caminhão {placa}: {num_regioes} regiões associadas")
        st.stop()

    pedidos_df = ia.otimizar_aproveitamento_frota(pedidos_df, caminhoes_df, percentual_frota, max_pedidos, n_clusters, distancia_maxima_km=550)
    for placa in pedidos_df['Placa'].unique():
        pedidos_caminhao = pedidos_df[pedidos_df['Placa'] == placa]
        coordenadas = pedidos_caminhao[['Latitude', 'Longitude']].values
        if not ia.validar_distancias(coordenadas, distancia_maxima_km=550):
            st.error(f"Erro: O caminhão {placa} foi alocado a pedidos muito distantes.")
            st.stop()

    if aplicar_tsp:
        G = ia.criar_grafo_tsp(pedidos_df)
        melhor_rota, menor_distancia = ia.resolver_tsp_genetico(G)
        st.write("Melhor rota TSP:")
        st.write("\n".join(melhor_rota))
        st.write(f"Menor distância TSP: {menor_distancia}")
        pedidos_df = definir_ordem_por_carga(pedidos_df, melhor_rota)

    if aplicar_vrp:
        rota_vrp = ia.resolver_vrp(pedidos_df, caminhoes_df)
        st.write(f"Melhor rota VRP: {rota_vrp}")

    st.write("Dados dos Pedidos:")
    st.dataframe(pedidos_df)
    mapa = ia.criar_mapa(pedidos_df)
    folium_static(mapa)
    output_file_path = "database/roterizacao_resultado.xlsx"
    pedidos_df.to_excel(output_file_path, index=False)
    st.write(f"Arquivo salvo: {output_file_path}")
    with open(output_file_path, "rb") as file:
        st.download_button(
            "Baixar planilha",
            data=file,
            file_name="roterizacao_resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
            st.markdown("**Edite a planilha de Pedidos, se necessário:**")
            dados_editados = st.data_editor(pedidos_df, num_rows="dynamic")
            if st.button("Salvar alterações na planilha"):
                dados_editados.to_excel("database/Pedidos.xlsx", index=False)
                st.success("Planilha editada e salva com sucesso!")
    
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
            pedidos_df, coordenadas_salvas = pedidos_result
            with st.spinner("Atualizando coordenadas..."):
                # Atualiza as coordenadas somente se estiverem faltando ou forem zero
                pedidos_df['Latitude'] = pedidos_df.apply(
                    lambda row: ia.obter_coordenadas_com_fallback(row['Endereço Completo'], coordenadas_salvas)[0]
                        if row.get('Latitude', 0) == 0 else row['Latitude'],
                    axis=1
                )
                pedidos_df['Longitude'] = pedidos_df.apply(
                    lambda row: ia.obter_coordenadas_com_fallback(row['Endereço Completo'], coordenadas_salvas)[1]
                        if row.get('Longitude', 0) == 0 else row['Longitude'],
                    axis=1
                )
            pedidos_df['Latitude'] = pedidos_df['Latitude'].fillna(0)
            pedidos_df['Longitude'] = pedidos_df['Longitude'].fillna(0)
            salvar_coordenadas(coordenadas_salvas)
            
            # Verifica se as colunas necessárias existem; caso contrário, cria-as
            for col in ['Latitude', 'Longitude']:
                if col not in pedidos_df.columns:
                    st.warning(f"A coluna '{col}' não foi encontrada. Ela será criada com valor 0.")
                    pedidos_df[col] = 0

            st.dataframe(pedidos_df)
            if st.button("Salvar alterações na planilha"):
                # Garante que o diretório "database" exista
                os.makedirs("database", exist_ok=True)
                
                # Salva o arquivo no caminho especificado
                pedidos_df.to_excel("database/Pedidos.xlsx", index=False)
                st.success("Planilha editada e salva com sucesso!")
            
            # Verifica se o arquivo existe antes de tentar abri-lo
            if os.path.exists("database/Pedidos.xlsx"):
                with open("database/Pedidos.xlsx", "rb") as file:
                    st.download_button(
                        "Baixar planilha de Pedidos",
                        data=file,
                        file_name="Pedidos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("O arquivo 'Pedidos.xlsx' não foi encontrado. Salve a planilha antes de tentar baixá-la.")
    
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
