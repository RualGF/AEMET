import streamlit as st
import os
import time
import uuid
import requests
import pandas as pd
from datetime import date, timedelta, datetime, timezone
import logging
logger = logging.getLogger(__name__)

#API_KEY = st.secrets["API_KEY"]
API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJydWFsZ2ZAZ21haWwuY29tIiwianRpIjoiN2Q5M2RjMDMtNWY5Yi00YzYwLWJmYTAtNTc2MTNiNDgyZjkxIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NDg0NDQ5MzIsInVzZXJJZCI6IjdkOTNkYzAzLTVmOWItNGM2MC1iZmEwLTU3NjEzYjQ4MmY5MSIsInJvbGUiOiIifQ.lb02yR53ROH4319ZiiHDjel7j_ingoIqmTswzt2d6uc'
if not API_KEY:
    raise RuntimeError("No encontré la clave AEMET_API_KEY en las variables de entorno.")
hoy = date.today()


def hacer_peticion(url, parametros = None, timeout = 30, reintentos = 5):
    """
    Hago una petición GET con reintentos y espera progresiva.
    Ignoro timeouts
    """
    espera = 10
    for intento in range(1, reintentos + 1):
        try:
            print(f"[{intento}/{reintentos}] solicitando {url}")
            respuesta = requests.get(url, params = parametros, timeout = timeout)
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

def cargar_inventario(api_key):
    ruta_cache = "data/inventario_estaciones.json"
    url_inventario = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"

    if os.path.exists(ruta_cache):
        logger.info("Inventario en caché encontrado, intentando usar caché")
        try:
            return pd.read_json(ruta_cache)
        except Exception:
            pass

    respuesta = hacer_peticion(url_inventario, parametros = {"api_key": api_key})
    if not respuesta:
        raise RuntimeError("Sin respuesta del inventario de estaciones y no hay caché")

    datos_url = respuesta.json().get("datos", "")
    if not datos_url.startswith("http"):
        raise RuntimeError("URL de datos inválida")

    inventario = hacer_peticion(datos_url)
    if inventario:
        os.makedirs("data", exist_ok = True)
        with open(ruta_cache, "w") as f:
            f.write(inventario.text)
        return pd.read_json(ruta_cache)

    raise RuntimeError("No se pudo descargar el inventario")


def extraer_ultimos_tres_dias():
    df_estaciones = cargar_inventario(API_KEY).dropna(subset = ["indicativo"])
    print(f"Cargué {len(df_estaciones)} estaciones")

    # Defino bloques de fecha para los últimos 3 días
    
    bloques = [
        (f"{(hoy - timedelta(days = i)).isoformat()}T00:00:00UTC",
         f"{(hoy - timedelta(days = i)).isoformat()}T00:00:00UTC")
        for i in range(1, 4)
    ]
     # for i in range(1, 4):
    #     dia = hoy - timedelta(days=i)
    #     iso = dia.isoformat()
    #bloques.append((f"{iso}T00:00:00UTC", f"{iso}T00:00:00UTC"))
    return extraer_datos_aemet(df_estaciones, bloques)

def extraer_por_años():
    df_estaciones = cargar_inventario(API_KEY).dropna(subset=["indicativo"]).sort_values("indicativo")
    print(f"Cargué {len(df_estaciones)} estaciones")

    años = list(range(2016, hoy.year + 1))

    bloques = []
    for año in años:
        if año == hoy.year:
            bloques.append((f"{date(año, 1, 1)}T00:00:00UTC", f"{date(año, 6, 30)}T00:00:00UTC"))
        else:
            bloques.append((f"{date(año, 1, 1)}T00:00:00UTC", f"{date(año, 6, 30)}T00:00:00UTC"))
            bloques.append((f"{date(año, 7, 1)}T00:00:00UTC", f"{date(año, 12, 31)}T00:00:00UTC"))
    return extraer_datos_aemet(df_estaciones, bloques, etiqueta = f"{años[0]}_a_{años[-1]}")   

def extraer_datos_aemet(df_estaciones, bloques, etiqueta = "multi"):
    
    id_descarga = str(uuid.uuid4())
    archivos_generados = []

    for _, fila in df_estaciones.iterrows():
        codigo = fila["indicativo"]
        nombre = fila.get("nombre", "")
        
        for inicio, fin in bloques:
            fecha_inicio = inicio[:10]
            fecha_fin = fin[:10]
            carpeta="data"
            
            archivo_tmp = os.path.join(carpeta, f"{codigo}_{fecha_inicio}_a_{fecha_fin}.tmp")
            archivo_csv = os.path.join(carpeta, f"{codigo}_{fecha_inicio}_a_{fecha_fin}.csv")
            
            # Si ya existe el archivo final, saltar
            if os.path.exists(archivo_csv):
                print(f"Ya existe: {archivo_csv}, usando el archivo existente.")
                archivos_generados.append(archivo_csv)
                continue

            # Verificar si hay un temporal que quedó de un fallo previo
            if os.path.exists(archivo_tmp):
                print(f"TMP antiguo detectado en {archivo_tmp}, lo elimino antes de continuar.")
                os.remove(archivo_tmp)


            url_meta = (
                "https://opendata.aemet.es/opendata/api/valores/"
                f"climatologicos/diarios/datos/fechaini/{inicio}/fechafin/{fin}/estacion/{codigo}"
            )
            meta = hacer_peticion(url_meta, parametros = {"api_key": API_KEY})
            if not meta:
                continue

            url_datos = meta.json().get("datos", "")
            if not url_datos:
                print(f"No hay datos para {codigo} en {inicio[:10]}")
                continue
            
            datos = hacer_peticion(url_datos)
            if not datos:
                continue
            
            try:
                registros = datos.json()
                if isinstance(registros, str):
                    import json
                    registros = json.loads(registros)
            except Exception as e:
                print(f"  Error al decodificar JSON para {codigo}: {e}")
                continue
            
            filas =[]
            for registro in registros:
                if not isinstance(registro, dict):
                    print(f"  Registro no es dict: {registro[:50]}...")
                    continue
                registro.update({
                    "indicativo": codigo,
                    "nombre_estacion": nombre,
                    "timestamp_extraccion": datetime.now(timezone.utc).isoformat(),
                    "id_descarga": id_descarga
                })
                filas.append(registro)

            if not filas:
                print(f"Sin datos válidos para {codigo} entre {fecha_inicio} y {fecha_fin}")
                continue
            
            df_bloque = pd.DataFrame(filas)

            if not df_bloque.empty:
                df_bloque.to_csv(archivo_tmp, index=False)
                os.rename(archivo_tmp, archivo_csv)
                archivos_generados.append(archivo_csv)
                print(f"Bloque guardado correctamente en {archivo_csv}")
                time.sleep(2)
            else:
                print(f"Ningún dato válido en {etiqueta}. No guardo CSV.")
                if os.path.exists(archivo_tmp):
                    os.remove(archivo_tmp)
    return archivos_generados

            

        
if __name__ == "__main__":
    extraer_por_años()