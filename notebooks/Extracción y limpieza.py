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

#Selección de columnas de interés

df_I = df[['indicativo', 'nombre', 'provincia', 'altitud', 'fecha', 'tmin', 'tmax', 'tmed',
           'hrMedia', 'prec', 'velmedia', 'racha']]

#Check duplicados

df_I.duplicated.any()

#Cast a números y ordenar por estación y fecha

numeric_columns = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "altitud"]

for col in numeric_columns:
    df_I[col] = pd.to_numeric(df_I[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")

df_I["fecha"] = pd.to_datetime(df_I["fecha"], format="%Y-%m-%d", errors="coerce")

df_I["anio"] = df_I["fecha"].dt.year
df_I["mes"] = df_I["fecha"].dt.month
df_I["dia"] = df_I["fecha"].dt.day

df_II = df_I.sort_values(["indicativo", "fecha"])

#Reemplazo de NAs
#Premisas
#A. No cambiar la distribución de las variables (Solo reemplazar en periodos de medición interrumpida, o gap_threshold, dentro del periódo de actividad)
#B. Eficiente computacionalmente.
#C. Preservar estructura temporal y espacial (Solo reemplazar NAs durante el período de actividad de la estación)

def smart_impute_respecting_operation(df, numeric_cols, gap_threshold=3):
    df = df.sort_values(["indicativo", "fecha"]).copy()

    station_ranges = df.groupby("indicativo")["fecha"].agg(["min", "max"])

    def fill_gaps(group):
        start, end = station_ranges.loc[group.name]
        group = group[(group["fecha"] >= start) & (group["fecha"] <= end)].copy() #Solo aplicar al periodo de actividad

        for col in numeric_cols:
            series = group[col]
            median_val = series.median()

            is_nan = series.isna()
            groups = (is_nan != is_nan.shift()).cumsum()

            for g in groups[is_nan].unique():
                gap_idx = groups[groups == g].index
                gap_len = len(gap_idx)

                if gap_len <= gap_threshold:
                    group.loc[gap_idx, col] = median_val

            group[col] = group[col].interpolate(method="linear", limit_direction="both")
            group[col] = group[col].fillna(median_val)

        return group

    df_imputed = df.groupby("indicativo").apply(fill_gaps)
    df_imputed.reset_index(drop=True, inplace=True)
    return df_imputed

numeric_cols = ["tmin", "tmax", "tmed", "hrMedia", "prec", "velmedia", "racha"]

df_III = smart_impute(df_II, numeric_cols, gap_threshold=3) #3 dias de interrumpción de medición

#Ajustes finales

df_III['prec'] = df_III['prec'].fillna(0)
df_IV = df_III.dropna(subset = ['tmed'])

df_IV.loc[:, "anio"] = df_IV["anio"].astype('int64')
df_IV.loc[:, "mes"] = df_IV["mes"].astype('int64')
df_IV.loc[:, "dia"] = df_IV["dia"].astype('int64')

#Guardar

ruta_salida = "data/temperaturas_limpias.csv"
df_IV.to_csv(ruta_salida, index=False)
print(":marca_de_verificación_blanca: Datos limpios guardados en:", ruta_salida)
print(":gráfico_de_barras: Dimensiones finales:", df_IV.shape)