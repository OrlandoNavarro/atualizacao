import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import requests

from gerenciamento_frota import cadastrar_caminhoes
from subir_pedidos import processar_pedidos, salvar_coordenadas
import ia_analise_pedidos as ia

def main():
    st.title("Roteirizador de Pedidos")
    
    # Injetar CSS para remover os marcadores do radio e adicionar espaçamento entre os itens
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
            salvar_coordenadas(coordenadas_salvas)
            if pedidos_df['Latitude'].isnull().any() or pedidos_df['Longitude'].isnull().any():
                st.error("Alguns endereços não obtiveram coordenadas. Verifique os dados.")
                return
            st.dataframe(pedidos_df)
            
            # Botão para acionar a roteirização dos pedidos
            if st.button("Roteirizar"):
                # Aqui você pode chamar sua função de roteirização (ex: algoritmo genético)
                # Exemplo simplificado:
                st.write("Roteirização em execução...")
                # Resultado fictício para demonstração
                rota_otimizada = "Exemplo de Rota Otimizada: Endereço1 -> Endereço2 -> Endereço3"
                st.success(rota_otimizada)
    
    elif menu_opcao == "Cadastro da Frota":
        st.header("Cadastro da Frota")
        if st.checkbox("Cadastrar Caminhões"):
            cadastrar_caminhoes()
        # Caso deseje manter o upload dos pedidos como parte deste menu, insira as chamadas necessárias,
        # ou remova se não for mais necessário.
    
    elif menu_opcao == "IA Analise":
        st.header("IA Analise")
        st.write("Envie a planilha de pedidos para análise e salve os dados no diretório 'database':")
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