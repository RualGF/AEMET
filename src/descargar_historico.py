# src/descargar_historico.py

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time

# Cargar API Key
load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

# Fechas a consultar
FECHA_INICIO = "2023-01-01"
FECHA_FIN = "2024-12-31"

# Crear carpeta de salida
os.makedirs("data/historico", exist_ok=True)

# Función para descargar los datos de una estación
def descargar_datos_estacion(idema, nombre):
    url = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{FECHA_INICIO}/fechafin/{FECHA_FIN}/estacion/{idema}"
    headers = {"accept": "application/json", "api_key": API_KEY}
    
    try:
        respuesta = requests.get(url, headers=headers)
        if respuesta.status_code == 200:
            respuesta_json = respuesta.json()
            url_datos = respuesta_json.get("datos")
            if url_datos:
                datos = requests.get(url_datos).json()
                df = pd.DataFrame(datos)
                df["nombre_estacion"] = nombre
                df["idema"] = idema
                ruta = f"data/historico/{idema}.csv"
                df.to_csv(ruta, index=False)
                print(f"✅ Datos guardados: {ruta}")
            else:
                print(f"⚠️ Estación {idema} sin datos.")
        else:
            print(f"❌ Error en estación {idema}: {respuesta.status_code}")
    except Exception as e:
        print(f"❌ Excepción en estación {idema}: {e}")

# Ejecutar si es script principal
if __name__ == "__main__":
    print("📥 Cargando estaciones filtradas...")
    estaciones = pd.read_csv("data/estaciones_filtradas.csv")

    for _, row in estaciones.iterrows():
        print(f"�� Procesando estación: {row['indicativo']} - {row['nombre']}")
        descargar_datos_estacion(row["indicativo"], row["nombre"])

    time.sleep(1.5)  # para evitar sobrecargar la API

