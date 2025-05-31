#!/usr/bin/env python
# coding: utf-8

# Predicciones Meteorológicas (AEMET) - SPRINT I

# Parte 1 - Extracción de Datos
# 
# Navegar la documentación de la API de AEMET y explorar los endpoints
# 
# Desarrollar un script que extraiga la información histórica de todas las provincias.
# 
# Ejecutar el script para extraer los datos de los últimos dos años y verificar que todo
# funcione correctamente.
# 
# En el modelo de datos, cada registro debe tener un timestamp de extracción y un
# identificador para que se pueda manejar el sistema de actualización.

# In[81]:


import os
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AEMET_API_KEY")
CSV_ESTACIONES = "data/estaciones_filtradas.csv"
ARCHIVO_SALIDA = "data/temperaturas_historicas_ampliadas.csv"

# Definimos los 4 rangos de fechas para cubrir 2 años
FECHAS = [
    ("2023-05-29T00:00:00UTC", "2023-11-28T00:00:00UTC"),
    ("2023-11-29T00:00:00UTC", "2024-05-28T00:00:00UTC"),
    ("2024-05-29T00:00:00UTC", "2024-11-28T00:00:00UTC"),
    ("2024-11-29T00:00:00UTC", "2025-05-28T00:00:00UTC")
]

# Si existe el archivo, cargamos los idema descargados
if os.path.exists(ARCHIVO_SALIDA):
    datos_existentes = pd.read_csv(ARCHIVO_SALIDA)
    estaciones_descargadas = set(datos_existentes["idema"].unique())
else:
    estaciones_descargadas = set()

estaciones = pd.read_csv(CSV_ESTACIONES)

# Guardamos todos los datos en una lista
todas_las_filas = []

print("Cargando estaciones...")

for _, fila in estaciones.iterrows():
    codigo = fila["indicativo"]
    nombre = fila["nombre"]

    if codigo in estaciones_descargadas:
        continue

    print(f"Procesando estación: {codigo} - {nombre}")

    datos_estacion = []
    for fecha_inicio, fecha_fin in FECHAS:
        url_meta = (
            f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/"
            f"datos/fechaini/{fecha_inicio}/fechafin/{fecha_fin}/estacion/{codigo}"
        )

        try:
            respuesta_meta = requests.get(url_meta, params={"api_key": API_KEY})
            if respuesta_meta.status_code != 200:
                continue

            url_datos = respuesta_meta.json().get("datos")
            if not url_datos:
                continue

            respuesta_datos = requests.get(url_datos)
            if respuesta_datos.status_code != 200:
                continue

            datos_json = respuesta_datos.json()
            for fila in datos_json:
                fila["idema"] = codigo
                fila["nombre_estacion"] = nombre
                datos_estacion.append(fila)

            time.sleep(1.5)  

        except Exception:
            continue

    todas_las_filas.extend(datos_estacion)

# Finalmente convertimos a DataFrame y guardamos
if todas_las_filas:
    df = pd.DataFrame(todas_las_filas)

    if os.path.exists(ARCHIVO_SALIDA):
        df.to_csv(ARCHIVO_SALIDA, mode="a", index=False, header=False)
    else:
        df.to_csv(ARCHIVO_SALIDA, index=False)

    print("Los datos se han guardado correctamente.")
else:
    print("No se obtuvieron datos nuevos.")


# In[79]:


import pandas as pd

df = pd.read_csv("../data/temperaturas_historicas_ampliadas.csv")

print("\n Dimensiones del DataFrame:", df.shape)

# Columnas
print("\n Columnas:")
print(df.columns.tolist())

# Valores nulos
print("\n Valores nulos por columna:")
print(df.isna().sum())

print("\n Primeras 5 filas:")
print(df.head())


