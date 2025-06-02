import pandas as pd

from sqlalchemy import create_engine, insert, table

import conectar

df = pd.read_csv(r".\data\temperaturas_limpias.csv")

valores_insertar = {}
for col in df.columns:
    valores_insertar.update({col: df[col][0]})

print(valores_insertar)

try:
    print(f"Iniciando inserción de {len(df)} filas usando df.to_sql()...")

    # 'if_exists='append'' significa que añadirá las filas (no reemplaza ni falla si ya existe)
    # 'index=False' para no escribir el índice del DataFrame como una columna
    # 'method='multi'' es bueno para MySQL, inserta múltiples filas por sentencia INSERT.
    # 'chunksize' puede ayudar a gestionar la memoria para DataFrames muy grandes.
    #  Ajusta chunksize según la memoria disponible y el ancho de tus filas.
    df.to_sql(
        name="datos_meteorologicos_table",  # Nombre de la tabla
        con=conectar.conexion(),
        if_exists="append",
        index=False,
        method="multi",  # Muy importante para el rendimiento con MySQL
        chunksize=10000,  # Inserta en lotes de 10000 filas, ajusta según necesidad
    )
    print(f"¡{len(df)} filas insertadas correctamente usando df.to_sql()!")

except Exception as e:
    print(f"Error durante la inserción con df.to_sql(): {e}")
