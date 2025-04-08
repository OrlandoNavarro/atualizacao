import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, filename="preprocessor.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def preprocessar_dados(df):
    """
    Realiza pré-processamento dos dados:
      - Preenchimento de valores faltantes;
      - Conversão para numérico;
      - Normalização de colunas (ex.: 'Peso dos Itens', 'Volume', 'Distância').
    """
    df.fillna(0, inplace=True)
    for coluna in ['Peso dos Itens', 'Volume', 'Distância']:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
            max_val = df[coluna].max()
            if max_val > 0:
                df[coluna] = df[coluna] / max_val
    return df