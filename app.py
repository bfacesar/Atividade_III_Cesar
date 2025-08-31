


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Caminho local para o arquivo Employee.csv
employee_df = pd.read_csv(r"C:\Users\Consultor\OneDrive\Desktop\CESAR\4.Análise e Visualização de Dados\Employee.csv")

print(employee_df.head())


#Deixando strings vazias com valores nulos, para facilitar a remoção
employee_df.replace('', np.nan, inplace=True)

print("Valores nulos antes da limpeza:")
print(employee_df.isnull().sum())

employee_df.dropna(inplace=True)

print("\nValores nulos depois da limpeza:")
print(employee_df.isnull().sum())


#Removendo duplicidades
print("\nQuantidade de linhas duplicadas antes da remoção", employee_df.duplicated().sum())

employee_df.drop_duplicates(inplace=True)

print("Quantidade de linhas duplicada depois da remoção ", employee_df.duplicated().sum())

# Redefinindo a coluna Education
education_map = {
    'Bachelors': 1,
    'Masters': 2,
    'PHD': 3
}

employee_df['Education'] = employee_df['Education'].map(education_map)

print("Coluna 'Education' atualizada:")
print(employee_df['Education'].head())  
print(employee_df.head())                



#Redefinindo a gender
employee_df['Female'] = employee_df['Gender'].apply(lambda x: 1 if x == 'Female' else 0)
print(employee_df[['Gender', 'Female']].head())

#employee_df = employee_df.drop('Gender', axis=1)
print(employee_df.head())


def get_years_service(joining_year):
    return 2023 - joining_year

employee_df['years_of_service'] = employee_df['JoiningYear'].apply(get_years_service)

print(employee_df.head())