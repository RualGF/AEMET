import logging
import os
import random
import time

import pandas as pd
import requests

CARPETA_DATA = "data"
RUTA_CACHE_INVENTARIO = os.path.join(CARPETA_DATA, "inventario_estaciones.json")
URL_INVENTARIO = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"

logger = logging.getLogger(__name__)


def configurar_logging():
    if logging.getLogger().handlers:
        return

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(levelname)s - %(message)s"
    )


def obtener_api_key():
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise RuntimeError("Falta AEMET_API_KEY en variables de entorno")
    return api_key


def calcular_espera_reintento(espera_actual, factor_backoff, espera_maxima):
    siguiente_espera = espera_actual * factor_backoff
    return min(siguiente_espera, espera_maxima)


def aplicar_jitter(espera_base, jitter_ratio):
    if jitter_ratio <= 0:
        return espera_base

    delta = espera_base * jitter_ratio
    espera_con_jitter = random.uniform(max(0, espera_base - delta), espera_base + delta)
    return espera_con_jitter


def solicitar_datos_aemet(
    url,
    parametros = None,
    timeout = 30,
    reintentos = 5,
    espera_inicial = 10,
    factor_backoff = 2,
    espera_maxima = 120,
    jitter_ratio = 0.1,
):
    """
    Hago una petición GET con reintentos y espera progresiva.
    Ignoro timeouts
    """
    espera = espera_inicial
    for intento in range(1, reintentos + 1):
        try:
            logger.info(f"[{intento}/{reintentos}] solicitando {url}")
            respuesta = requests.get(url, params = parametros, timeout = timeout)
            codigo = respuesta.status_code
            if codigo in (429, 500, 502, 503, 504):
                espera_efectiva = aplicar_jitter(espera, jitter_ratio)
                logger.warning(f"  respuesta {codigo}, espero {espera_efectiva:.2f}s e intento otra vez")
                time.sleep(espera_efectiva)
                espera = calcular_espera_reintento(espera, factor_backoff, espera_maxima)
                continue
            respuesta.raise_for_status()
            return respuesta
        except (requests.ReadTimeout, requests.ConnectionError) as e:
            espera_efectiva = aplicar_jitter(espera, jitter_ratio)
            logger.warning(f"  fallo {type(e).__name__}, espero {espera_efectiva:.2f}s e intento otra vez")
            time.sleep(espera_efectiva)
            espera = calcular_espera_reintento(espera, factor_backoff, espera_maxima)
        except requests.HTTPError:
            logger.exception("  error HTTP en petición, no intento más")
            return None
    logger.error("  se acabaron los reintentos")
    return None


def cargar_json_desde_cache(ruta_cache):
    if not os.path.exists(ruta_cache):
        return None

    logger.info("Inventario en caché encontrado, intentando usar caché")
    try:
        return pd.read_json(ruta_cache)
    except Exception:
        return None


def obtener_url_datos(respuesta):
    return respuesta.json().get("datos", "")


def guardar_texto_en_archivo(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok = True)
    with open(ruta, "w") as f:
        f.write(contenido)


def cargar_inventario(api_key = None):
    inventario_cache = cargar_json_desde_cache(RUTA_CACHE_INVENTARIO)
    if inventario_cache is not None:
        return inventario_cache

    api_key = api_key or obtener_api_key()
    respuesta = solicitar_datos_aemet(URL_INVENTARIO, parametros = {"api_key": api_key})
    if not respuesta:
        raise RuntimeError("Sin respuesta del inventario de estaciones y no hay caché")

    datos_url = obtener_url_datos(respuesta)
    if not datos_url.startswith("http"):
        raise RuntimeError("URL de datos inválida")

    inventario = solicitar_datos_aemet(datos_url)
    if inventario:
        guardar_texto_en_archivo(RUTA_CACHE_INVENTARIO, inventario.text)
        return pd.read_json(RUTA_CACHE_INVENTARIO)

    raise RuntimeError("No se pudo descargar el inventario")
