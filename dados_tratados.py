# dados_tratados.py
# ----------------------------------------------------------
# Lê o Employee.csv da pasta data/ (caminho relativo ao projeto),
# aplica os mesmos tratamentos do seu código e retorna um DataFrame.
# Pronto para uso local e no Streamlit Cloud.
# ----------------------------------------------------------

from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# ======= AJUSTES DO ARQUIVO (se precisar trocar separador/decimal/encoding) =======
CSV_FILENAME = "Employee.csv"   # nome do arquivo dentro de data/
CSV_SEP = ","                   # "," ou ";"
CSV_DECIMAL = "."               # "." ou ","
CSV_ENCODING = "utf-8"          # "utf-8" ou "latin-1" se acentos quebrados
# ================================================================================

def load_data() -> pd.DataFrame:
    # Caminho relativo: <pasta_do_projeto>/data/Employee.csv
    csv_path = Path(__file__).parent / "data" / CSV_FILENAME
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path}")

    # Leitura do CSV
    employee_df = pd.read_csv(csv_path, sep=CSV_SEP, decimal=CSV_DECIMAL, encoding=CSV_ENCODING)

    # ----- (debug opcional) -----
    # print(employee_df.head())

    # Deixando strings vazias como valores nulos
    employee_df.replace('', np.nan, inplace=True)

    # (debug opcional)
    # print("Valores nulos antes da limpeza:")
    # print(employee_df.isnull().sum())

    # Removendo linhas com quaisquer valores nulos
    employee_df.dropna(inplace=True)

    # (debug opcional)
    # print("\nValores nulos depois da limpeza:")
    # print(employee_df.isnull().sum())

    # Removendo duplicidades
    # print("\nDuplicadas antes:", employee_df.duplicated().sum())
    employee_df.drop_duplicates(inplace=True)
    # print("Duplicadas depois:", employee_df.duplicated().sum())

    # Redefinindo a coluna Education (mesma regra que você usou)
    education_map = {'Bachelors': 1, 'Masters': 2, 'PHD': 3}
    # .replace preserva valores não mapeados (se existirem)
    employee_df['Education'] = employee_df['Education'].replace(education_map)
    # Garante numérico (qualquer coisa fora do mapeado vira NaN, mas já tiramos NaN antes)
    employee_df['Education'] = pd.to_numeric(employee_df['Education'], errors='coerce')

    # Criando coluna Female a partir de Gender
    employee_df['Female'] = employee_df['Gender'].apply(lambda x: 1 if x == 'Female' else 0)

    # Tempo de casa: ano atual - JoiningYear
    current_year = datetime.now().year
    # Garante que JoiningYear é numérico
    employee_df['JoiningYear'] = pd.to_numeric(employee_df['JoiningYear'], errors='coerce')
    employee_df['years_of_service'] = current_year - employee_df['JoiningYear']

    # (debug opcional)
    # print(employee_df.head())

    return employee_df


# Validação rápida no terminal:
if __name__ == "__main__":
    try:
        _df = load_data()
        print("✅ load_data() OK")
        print("Shape:", _df.shape)
        print(_df.head(5))
    except Exception as e:
        print("❌ Erro em load_data():", e)
