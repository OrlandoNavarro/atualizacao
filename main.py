import streamlit as st
import pandas as pd
from streamlit_folium import folium_static

from gerenciamento_frota import cadastrar_caminhoes
from subir_pedidos import processar_pedidos, salvar_coordenadas
import ia_analise_pedidos as ia

def main():
    st.title("Roteirizador de Pedidos")
    
    # Injetar CSS para remover os marcadores do radio e adicionar espaçamento entre os itens
    st.markdown(
        """
        <style>
        /* Remove bullets e adiciona espaço entre os itens */
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
    
    # Menu lateral com três opções
    menu_opcao = st.sidebar.radio("Menu", options=[
        "Dashboard", 
        "Cadastro de Frota e Upload de Planilha", 
        "IA para Análise de Pedidos"
    ])
    
    if menu_opcao == "Dashboard":
        st.header("Dashboard - Envio de Pedidos")
        st.write("Bem-vindo ao Dashboard! Envie a planilha de pedidos para iniciar:")
        
        # Processa a planilha de pedidos
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
            salvar_coordenadas(coordenadas_salvas)
            if pedidos_df['Latitude'].isnull().any() or pedidos_df['Longitude'].isnull().any():
                st.error("Alguns endereços não obtiveram coordenadas. Verifique os dados.")
                return
            st.dataframe(pedidos_df)
            
    elif menu_opcao == "Cadastro de Frota e Upload de Planilha":
        st.header("Cadastro de Caminhões e Upload de Pedidos")
        
        # Aba de cadastro de caminhões
        if st.checkbox("Cadastrar Caminhões"):
            cadastrar_caminhoes()
        
        # Seção de upload de planilha de pedidos
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
            salvar_coordenadas(coordenadas_salvas)
            if pedidos_df['Latitude'].isnull().any() or pedidos_df['Longitude'].isnull().any():
                st.error("Alguns endereços não obtiveram coordenadas. Verifique os dados.")
                return
            
            # Carrega frota
            try:
                caminhoes_df = pd.read_excel("database/caminhoes_frota.xlsx", engine="openpyxl")
            except FileNotFoundError:
                st.error("Nenhum caminhão cadastrado. Cadastre a frota na opção de cadastro.")
                return

            # Configurações para roteirização
            n_clusters = st.slider("Número de regiões para agrupar", min_value=1, max_value=10, value=5)
            percentual_frota = st.slider("Capacidade da frota a ser usada (%)", min_value=0, max_value=100, value=100)
            max_pedidos = st.slider("Número máximo de pedidos por veículo", min_value=1, max_value=20, value=10)
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
    
    elif menu_opcao == "IA para Análise de Pedidos":
        st.header("IA para Análise de Pedidos")
        st.write("Envie a planilha de pedidos para análise e salve os dados no diretório 'database':")
        # Processo similar ao de cadastro/upload: upload, obtenção de coordenadas e salvamento no database
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
            salvar_coordenadas(coordenadas_salvas)
            if pedidos_df['Latitude'].isnull().any() or pedidos_df['Longitude'].isnull().any():
                st.error("Alguns endereços não obtiveram coordenadas. Verifique os dados.")
                return
            
            st.dataframe(pedidos_df)
            # Salva a planilha de análise da IA no diretório database com um nome específico
            output_file_path = "database/ia_pedidos.xlsx"
            pedidos_df.to_excel(output_file_path, index=False)
            st.write(f"Planilha de IA salva: {output_file_path}")
            with open(output_file_path, "rb") as file:
                st.download_button(
                    "Baixar planilha de IA",
                    data=file, 
                    file_name="ia_pedidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()