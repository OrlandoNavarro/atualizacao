import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import requests
import time

from gerenciamento_frota import cadastrar_caminhoes
from subir_pedidos import processar_pedidos, salvar_coordenadas
import ia_analise_pedidos as ia

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
    
    # Menu lateral com quatro opções
    menu_opcao = st.sidebar.radio("Menu", options=[
        "Dashboard", 
        "Cadastro da Frota", 
        "IA Analise",
        "API REST"
    ])
    
    if menu_opcao == "Dashboard":
        st.header("Dashboard - Envio de Pedidos")
        st.write("Bem-vindo ao Dashboard! Envie a planilha de pedidos para iniciar:")
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
            # Se não encontrar as coordenadas, preenche os valores nulos com 0
            pedidos_df['Latitude'] = pedidos_df['Latitude'].fillna(0)
            pedidos_df['Longitude'] = pedidos_df['Longitude'].fillna(0)
            
            salvar_coordenadas(coordenadas_salvas)
            st.dataframe(pedidos_df)
            
            # Botão para acionar a roteirização dos pedidos (simulação)
            if st.button("Roteirizar"):
                st.write("Roteirização em execução...")
                progress_bar = st.progress(0)
                progresso = 0

                # Simulação de progresso (em porcentagem)
                for i in range(100):
                    time.sleep(0.05)
                    progresso += 1
                    progress_bar.progress(progresso)
                
                rota_otimizada = "Exemplo de Rota Otimizada: Endereço1 -> Endereço2 -> Endereço3"
                st.success(rota_otimizada)
                st.write(f"Processo de roteirização concluído: {progresso}%")
                
            # Permitir edição da planilha de pedidos (única planilha)
            st.markdown("**Edite a planilha de Pedidos, se necessário:**")
            dados_editados = st.data_editor(pedidos_df, num_rows="dynamic")
            if st.button("Salvar alterações na planilha"):
                dados_editados.to_excel("database/Pedidos.xlsx", index=False)
                st.success("Planilha editada e salva com sucesso!")
    
    elif menu_opcao == "Cadastro da Frota":
        st.header("Cadastro da Frota")
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
            with st.spinner("Obtendo coordenadas..."):
                pedidos_df['Latitude'] = pedidos_df['Endereço Completo'].apply(
                    lambda x: ia.obter_coordenadas_com_fallback(x, coordenadas_salvas)[0]
                )
                pedidos_df['Longitude'] = pedidos_df['Endereço Completo'].apply(
                    lambda x: ia.obter_coordenadas_com_fallback(x, coordenadas_salvas)[1]
                )
            # Preenche valores nulos com 0
            pedidos_df['Latitude'] = pedidos_df['Latitude'].fillna(0)
            pedidos_df['Longitude'] = pedidos_df['Longitude'].fillna(0)
            
            salvar_coordenadas(coordenadas_salvas)
            st.dataframe(pedidos_df)
            # Nesta aba, utilizamos a mesma planilha "Pedidos.xlsx"
            if st.button("Salvar alterações na planilha"):
                pedidos_df.to_excel("database/Pedidos.xlsx", index=False)
                st.success("Planilha editada e salva com sucesso!")
            with open("database/Pedidos.xlsx", "rb") as file:
                st.download_button(
                    "Baixar planilha de Pedidos",
                    data=file, 
                    file_name="Pedidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    elif menu_opcao == "API REST":
        st.header("Interação com API REST")
        st.write("Teste os seguintes endpoints:")
        st.markdown("""
        - **POST /upload**: Realiza upload dos arquivos (Pedidos.xlsx, Caminhoes.xlsx, IA.xlsx).
        - **GET /resultado**: Retorna a solução gerada pelo algoritmo genético.
        - **GET /mapa**: Exibe o mapa interativo com as rotas otimizadas.
        """)
        if st.button("Testar /resultado"):
            try:
                resposta = requests.get("http://localhost:5000/resultado")
                st.json(resposta.json())
            except Exception as e:
                st.error(f"Erro na requisição: {e}")

if __name__ == "__main__":
    main()