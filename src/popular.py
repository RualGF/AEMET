import pandas as pd
import sys
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st # Assuming you use st.secrets here
import conectar # Assuming your connection function is in conectar.py

df = pd.read_csv(r".\data\temperaturas_limpias.csv")

provincias = pd.read_sql_table("provincias", con=conectar.conexion())

print(provincias)
valores_insertar = pd.merge(
    df,
    provincias["codigo_prov"],  # <--- Seleccionar solo las columnas necesarias de 'provincias'
    left_on=df["provincia"],  # Columna de unión en df
    right_on=provincias["nombre"],  # Columna de unión en provincias
    how="left"
    )

valores_insertar = valores_insertar.drop(columns=["provincia", "id_limpieza", "key_0"]) #key_0 aparece al hacer el merge, pero la podemos eliminar

orden_columnas = [
    "id_descarga",
    "fecha",
    "indicativo",
    "nombre",
    "codigo_prov",
    "altitud",
    "tmed",
    "tmin",
    "tmax",
    "prec",
    "velmedia",
    "racha",
    "hrMedia",
    "timestamp_extraccion",
    ]

valores_insertar = valores_insertar[orden_columnas]

print(valores_insertar.head())
try:
    print(
        f"Iniciando inserción de {len(valores_insertar)} filas usando valores_insertar.to_sql()..."
    )

    # 'if_exists='append'' significa que añadirá las filas (no reemplaza ni falla si ya existe)
    # 'index=False' para no escribir el índice del DataFrame como una columna
    # 'method='multi'' es bueno para MySQL, inserta múltiples filas por sentencia INSERT.
    # 'chunksize' puede ayudar a gestionar la memoria para DataFrames muy grandes.
    #  Ajusta chunksize según la memoria disponible y el ancho de tus filas.
    valores_insertar.to_sql(
        name="datos_meteorologicos",  # Nombre de la tabla
        con=conectar.conexion(),
        if_exists="append",
        index=False,
        #method="multi",  # Muy importante para el rendimiento con MySQL
        chunksize=1000,  # Inserta en lotes de 10000 filas, ajusta según necesidad
    )
    print(
        f"¡{len(valores_insertar)} filas insertadas correctamente usando valores_insertar.to_sql()!"
    )

except Exception as e:
    print(f"Error durante la inserción con valores_insertar.to_sql(): {e}")
