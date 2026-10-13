import pandas as pd
import glob
import os
from tqdm import tqdm

# Directorio donde guardaste los datos
DATA_DIR = "aemet_data"

# 1. Encontrar todos los ficheros CSV descargados
# El patrón '*.csv' buscará todos los archivos que terminen en .csv
csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

# 2. Leer cada fichero y guardarlo en una lista
# Usamos tqdm para ver una barra de progreso, ya que puede tardar un poco
dataframes = []
for file in tqdm(csv_files, desc="Cargando ficheros CSV"):
    df = pd.read_csv(file)
    dataframes.append(df)

# 3. Concatenar (unir) todos los DataFrames en uno solo
print("\nConcatenando todos los datos en un único DataFrame...")
df_total = pd.concat(dataframes, ignore_index=True)

# 4. ¡Verificar el resultado!
print("\n¡Proceso completado!")
print(f"Dimensiones del DataFrame final (filas, columnas): {df_total.shape}")
print("\nPrimeras 5 filas del conjunto de datos unificado:")
print(df_total.head())
print("\nÚltimas 5 filas del conjunto de datos unificado:")
print(df_total.tail())

# 5. (Opcional) Guardar el fichero unificado
# ¡Cuidado! Este fichero será grande (cientos de MB).
# Guardarlo puede tardar unos minutos.
print("\nGuardando el fichero unificado en 'aemet_total.csv'...")
df_total.to_csv("aemet_total.csv", index=False)
print("Fichero guardado.")