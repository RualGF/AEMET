import os
import sys
import time
import json
import uuid
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def obtener_api_key() -> str:
    """Obtiene la API key de variables de entorno o de secrets.toml."""
    api_key = os.getenv("AEMET_API_KEY")
    if api_key:
        return api_key

    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
            return secrets.get("api_aemet", {}).get("API_KEY", "")
        except Exception as e:
            logger.warning(f"No se pudo leer secrets.toml: {e}")

    raise RuntimeError("No se encontró AEMET_API_KEY en variables de entorno ni en secrets.toml")


def solicitar_con_reintentos(url: str, params: dict | None = None, max_reintentos: int = 5) -> requests.Response | None:
    """Realiza una petición GET con reintentos y manejo de límites de tasa."""
    espera = 2.0
    headers = {"cache-control": "no-cache"}
    
    for intento in range(1, max_reintentos + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                return resp
            elif resp.status_code in (429, 500, 502, 503, 504):
                logger.warning(f"HTTP {resp.status_code}. Reintentando en {espera:.1f}s (intento {intento}/{max_reintentos})...")
                time.sleep(espera)
                espera = min(espera * 1.5, 30.0)
            else:
                logger.error(f"Error HTTP inesperado: {resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            logger.warning(f"Excepción en petición ({e}). Reintentando en {espera:.1f}s...")
            time.sleep(espera)
            espera = min(espera * 1.5, 30.0)

    logger.error(f"Se agotaron los reintentos para URL: {url}")
    return None


def descargar_bloque_todas_estaciones(fecha_ini: date, fecha_fin: date, api_key: str) -> list[dict]:
    """
    Descarga los datos de todas las estaciones para un rango <= 14 días.
    """
    inicio_str = f"{fecha_ini.isoformat()}T00:00:00UTC"
    fin_str = f"{fecha_fin.isoformat()}T23:59:59UTC"
    url = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{inicio_str}/fechafin/{fin_str}/todasestaciones"

    resp = solicitar_con_reintentos(url, params={"api_key": api_key})
    if not resp:
        return []

    try:
        data_meta = resp.json()
        if data_meta.get("estado") != 200 or "datos" not in data_meta:
            logger.warning(f"AEMET aviso para bloque {fecha_ini} a {fecha_fin}: {data_meta.get('descripcion')}")
            return []

        url_datos = data_meta["datos"]
        resp_datos = solicitar_con_reintentos(url_datos)
        if not resp_datos:
            return []

        registros = resp_datos.json()
        if isinstance(registros, str):
            registros = json.loads(registros)
        return registros if isinstance(registros, list) else []
    except Exception:
        logger.exception(f"Error parseando respuesta para bloque {fecha_ini} a {fecha_fin}")
        return []


def limpiar_y_transformar_nuevos_datos(df_nuevos: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las transformaciones necesarias para igualar el esquema de temperaturas_limpias_10_años_final.pkl:
    ['id_descarga', 'timestamp_extraccion', 'indicativo', 'nombre', 'provincia',
     'altitud', 'fecha', 'tmin', 'tmax', 'tmed', 'prec', 'velmedia', 'racha', 'hrMedia', 'cluster']
    """
    if df_nuevos.empty:
        return df_nuevos

    df = df_nuevos.copy()

    # 1. Metadatos de extracción si faltan
    if "id_descarga" not in df.columns:
        df["id_descarga"] = str(uuid.uuid4())
    if "timestamp_extraccion" not in df.columns:
        df["timestamp_extraccion"] = datetime.now(timezone.utc)

    # 2. Fechas
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["fecha", "indicativo"])

    # 3. Estandarizar provincias
    mapa_path = BASE_DIR / "data" / "mapa_provincia.json"
    if mapa_path.exists():
        with open(mapa_path, "r", encoding="utf-8") as f:
            mapa = json.load(f)
        df["provincia"] = df["provincia"].map(mapa).fillna(df["provincia"])

    # 4. Conversión de campos numéricos (reemplazar coma decimal)
    columnas_numericas = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia", "altitud"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        else:
            df[col] = pd.NA

    # 5. Filtrado físico de valores imposibles
    df.loc[(df["tmin"] > 45) | (df["tmin"] < -25), "tmin"] = pd.NA
    df.loc[(df["tmax"] > 50) | (df["tmax"] < -25), "tmax"] = pd.NA
    df.loc[(df["tmed"] > 45) | (df["tmed"] < -20), "tmed"] = pd.NA
    df.loc[(df["prec"] > 300) | (df["prec"] < 0), "prec"] = pd.NA
    df.loc[(df["velmedia"] > 35) | (df["velmedia"] < 0), "velmedia"] = pd.NA
    df.loc[(df["racha"] > 60) | (df["racha"] < 0), "racha"] = pd.NA
    df.loc[(df["hrMedia"] < 5) | (df["hrMedia"] > 100), "hrMedia"] = pd.NA

    temp_invalida = (df["tmin"] > df["tmax"]) & df["tmin"].notna() & df["tmax"].notna()
    df.loc[temp_invalida, ["tmin", "tmax", "tmed"]] = pd.NA

    # 6. Asignar cluster climático desde data/estaciones.csv
    estaciones_path = BASE_DIR / "data" / "estaciones.csv"
    if estaciones_path.exists():
        df_estaciones = pd.read_csv(estaciones_path)
        if "indicativo" in df_estaciones.columns and "cluster" in df_estaciones.columns:
            mapa_cluster = dict(zip(df_estaciones["indicativo"], df_estaciones["cluster"]))
            df["cluster"] = df["indicativo"].map(mapa_cluster)
            df["cluster"] = df["cluster"].fillna(-1).astype(int)

    # 7. Asegurar las columnas exactas del dataset original
    columnas_finales = [
        "id_descarga", "timestamp_extraccion", "indicativo", "nombre", "provincia",
        "altitud", "fecha", "tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia", "cluster"
    ]
    for col in columnas_finales:
        if col not in df.columns:
            df[col] = None

    return df[columnas_finales]


def ejecutar_actualizacion_completa():
    api_key = obtener_api_key()
    pkl_path = BASE_DIR / "data" / "temperaturas_limpias_10_años_final.pkl"

    if not pkl_path.exists():
        logger.error(f"No existe el archivo {pkl_path}")
        return

    logger.info(f"Leyendo dataset histórico desde {pkl_path}...")
    df_historico = pd.read_pickle(pkl_path)
    ultima_fecha_dt = pd.to_datetime(df_historico["fecha"]).max()
    ultima_fecha = ultima_fecha_dt.date()
    hoy = date.today()

    logger.info(f"Última fecha registrada en el histórico: {ultima_fecha}")
    logger.info(f"Fecha objetivo (hoy): {hoy}")

    fecha_inicio = ultima_fecha + timedelta(days=1)
    if fecha_inicio >= hoy:
        logger.info("Los datos ya están completamente actualizados hasta la fecha de hoy.")
        return

    logger.info(f"Descargando rango pendiente: del {fecha_inicio} al {hoy}")

    # Generar ventanas de 14 días
    ventanas = []
    curr_ini = fecha_inicio
    while curr_ini <= hoy:
        curr_fin = min(curr_ini + timedelta(days=13), hoy)
        ventanas.append((curr_ini, curr_fin))
        curr_ini = curr_fin + timedelta(days=1)

    logger.info(f"Total de bloques a descargar: {len(ventanas)}")

    todos_registros = []
    id_descarga_global = str(uuid.uuid4())
    ts_ahora = datetime.now(timezone.utc)

    for i, (ini, fin) in enumerate(ventanas, 1):
        logger.info(f"[{i}/{len(ventanas)}] Descargando del {ini} al {fin}...")
        registros = descargar_bloque_todas_estaciones(ini, fin, api_key)
        for r in registros:
            r["id_descarga"] = id_descarga_global
            r["timestamp_extraccion"] = ts_ahora
        todos_registros.extend(registros)
        logger.info(f"  -> Obtenidos {len(registros)} registros (Acumulado: {len(todos_registros)})")
        time.sleep(1.0)  # Cortesía para rate limit de AEMET

    if not todos_registros:
        logger.warning("No se recibieron nuevos registros desde la API de AEMET.")
        return

    logger.info(f"Procesando y transformando {len(todos_registros)} nuevos registros...")
    df_nuevos_brutos = pd.DataFrame(todos_registros)
    df_nuevos_limpios = limpiar_y_transformar_nuevos_datos(df_nuevos_brutos)

    # Backup del archivo histórico antes de sobreescribir
    backup_path = BASE_DIR / "data" / f"temperaturas_limpias_backup_{ultima_fecha}.pkl"
    if not backup_path.exists():
        logger.info(f"Creando copia de seguridad en {backup_path}...")
        df_historico.to_pickle(backup_path)

    logger.info("Combinando histórico con datos nuevos...")
    df_total = pd.concat([df_historico, df_nuevos_limpios], ignore_index=True)
    assert isinstance(df_total, pd.DataFrame)
    # Evitar posibles duplicados de (fecha, indicativo)
    df_total = df_total.drop_duplicates(subset=["fecha", "indicativo"], keep="last")
    df_total = df_total.sort_values(by=["fecha", "indicativo"]).reset_index(drop=True)

    logger.info(f"Guardando nuevo dataset consolidado en {pkl_path}...")
    df_total.to_pickle(pkl_path)
    logger.info(f"✅ ¡Actualización completada! Registros totales: {len(df_total)} (nuevos añadidos: {len(df_nuevos_limpios)})")
    logger.info(f"Nuevo rango temporal: {df_total['fecha'].min().date()} a {df_total['fecha'].max().date()}")


if __name__ == "__main__":
    ejecutar_actualizacion_completa()
