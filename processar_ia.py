import pandas as pd

def processar_ia_file(file_path: str = "database/IA.xlsx") -> None:
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
        return

    # Verifica se a coluna de agrupamento existe; ajuste o nome conforme o arquivo
    coluna_chave = "N° Carga"  # ou "Carga" se for esse o nome
    if coluna_chave in df.columns:
        agrupado = df.groupby(coluna_chave).apply(lambda df_grupo: df_grupo.to_dict(orient="records")).to_dict()
        print("Dados agrupados por", coluna_chave)
        for carga, pedidos in agrupado.items():
            print(f"Carga {carga}:")
            for pedido in pedidos:
                print(pedido)
    else:
        print(f"A coluna '{coluna_chave}' não foi encontrada no arquivo.")
        print("Colunas disponíveis:", df.columns.tolist())

if __name__ == "__main__":
    processar_ia_file()