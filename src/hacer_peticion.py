import streamlit as st
import os
import time
import uuid
import requests
import pandas as pd
from datetime import date, timedelta, datetime
import logging
logger = logging.getLogger(__name__)

API_KEY = st.secrets["API_KEY"]
if not API_KEY:
    raise RuntimeError("No encontré la clave AEMET_API_KEY en las variables de entorno.")

def hacer_peticion(url, params=None, timeout=30, reintentos=5):
    """
    Hago una petición GET con reintentos y espera progresiva.
    Ignoro timeouts
    """
    espera = 10
    for intento in range(1, reintentos + 1):
        try:
            print(f"[{intento}/{reintentos}] solicitando {url}")
            respuesta = requests.get(url, params=params, timeout=timeout)
            codigo = respuesta.status_code
            if codigo in (429, 500, 502, 503, 504):
                print(f"  respuesta {codigo}, espero {espera}s e intento otra vez")
                time.sleep(espera)
                espera *= 2
                continue
            respuesta.raise_for_status()
            return respuesta
        except (requests.ReadTimeout, requests.ConnectionError) as e:
            print(f"  fallo {type(e).__name__}, espero {espera}s e intento otra vez")
            time.sleep(espera)
            espera *= 2
        except requests.HTTPError as e:
            print(f"  error HTTP {e.response.status_code}, no intento más")
            return None
    print("  se acabaron los reintentos")
    return None

def extraer_ultimos_tres_dias():
    # Descargo el inventario de estaciones 
    ruta_cache = "data/inventario_estaciones.json"
    url_inventario = (
        "https://opendata.aemet.es/opendata/api/"
        "valores/climatologicos/inventarioestaciones/todasestaciones"
    )
    estaciones = None
    if os.path.exists(ruta_cache):
        logger.info("Inventario en caché encontrado, intentando usar caché")
        try:
            estaciones = pd.read_json(ruta_cache).to_dict(orient="records")
            logger.info("Inventario cargado desde caché")
        except Exception as e:
            logger.error(f"Error al leer caché: {e}, intentando API")
    
    if not estaciones:
        respuesta = hacer_peticion(url_inventario, params={"api_key": API_KEY})
        if not respuesta:
            raise RuntimeError ("Sin respuesta del inventario de estaciones y no hay caché")
        try:
            response_json = respuesta.json()
            datos_url = response_json.get("datos", "")
            if not datos_url or not datos_url.startswith("http"):
                raise RuntimeError(f"URL de datos inválida: {datos_url}")
            inventario = hacer_peticion(datos_url)
            if inventario:
                estaciones = inventario.json()
                os.makedirs("data", exist_ok=True)
                with open(ruta_cache, "w") as f:
                    f.write(inventario.text)
                logger.info("Inventario descargado y guardado")
            else:
                raise RuntimeError("No pude descargar el inventario de la AEMET.")
        except ValueError as e:
            logger.error({f"Error al parsear la respuesta JSON: {e}"})
            raise RuntimeError("Error en la respuesta JSON y no hay caché invalida")
    else:
        if os.path.exists(ruta_cache):
            print("Uso el inventario guardado en caché")
            estaciones = pd.read_json(ruta_cache).to_dict(orient="records")
        else:
            raise RuntimeError("No tengo inventario y tampoco hay caché.")

    df_estaciones = pd.DataFrame(estaciones).dropna(subset=["indicativo"])
    print(f"Cargué {len(df_estaciones)} estaciones")

    # Defino bloques de fecha para los últimos 3 días
    hoy = date.today()
    bloques = []
    for i in range(1, 4):
        dia = hoy - timedelta(days=i)
        iso = dia.isoformat()
        bloques.append((f"{iso}T00:00:00UTC", f"{iso}T00:00:00UTC"))

    # Recorro cada estación y extraigo datos
    todas_las_filas = []
    id_descarga = str(uuid.uuid4())
    for _, fila in df_estaciones.iterrows():
        codigo = fila["indicativo"]
        nombre = fila.get("nombre", "")
        for inicio, fin in bloques:
            url_meta = (
                "https://opendata.aemet.es/opendata/api/valores/"
                f"climatologicos/diarios/datos/fechaini/{inicio}/fechafin/{fin}/estacion/{codigo}"
            )
            meta = hacer_peticion(url_meta, params={"api_key": API_KEY})
            if not meta:
                continue
            url_datos = meta.json().get("datos", "")
            if not url_datos:
                print(f"No hay datos para {codigo} en {inicio[:10]}")
                continue
            datos = hacer_peticion(url_datos)
            if not datos:
                continue

            for registro in datos.json():
                registro.update({
                    "indicativo": codigo,
                    "nombre_estacion": nombre,
                    "fecha": inicio[:10],
                    "timestamp_extraccion": datetime.utcnow().isoformat(),
                    "id_descarga": id_descarga
                })
                todas_las_filas.append(registro)

            time.sleep(2)
        
    if todas_las_filas:
        df_salida = pd.DataFrame(todas_las_filas)
        return df_salida
    else:
        print("No obtuve datos en los últimos 3 días.")
        return pd.DataFrame()
if __name__ == "__main__":
    extraer_ultimos_tres_dias()