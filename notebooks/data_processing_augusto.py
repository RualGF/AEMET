# src/data_processing.py
import streamlit as st
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import uuid
import time
import logging
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed
import yaml
from src.mapa_provincias import get_provincia_mappings
from src.conectar import conexion
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(filename=Path("..") / "data" / "extraction_logs.txt", level=logging.INFO)

# Load API key from .entorno
load_dotenv(dotenv_path=Path("..") / ".entorno")
API_KEY = os.getenv("AEMET_API_KEY") or st.secrets.get("AEMET", {}).get("API_KEY")
if not API_KEY:
    raise RuntimeError("No se encontró AEMET_API_KEY en .entorno o secrets.toml.")

# Load configuration (rango de valores para variables numéricas)
CONFIG_PATH = Path("..") / "config" / "config.yaml"
if not CONFIG_PATH.exists():
    raise RuntimeError(f"Archivo de configuración {CONFIG_PATH} no encontrado.")
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)
THRESHOLDS = config.get("thresholds", {})

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def obtener_inventario_completo():
    """
    Retrieve the complete inventory of AEMET weather stations.
    """
    url = (
        "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    )
    r = requests.get(url, params={"api_key": API_KEY}, timeout=15)
    r.raise_for_status()
    datos_meta = r.json().get("datos")
    if not datos_meta:
        raise RuntimeError("No se pudo obtener URL de datos del inventario.")
    r2 = requests.get(datos_meta, timeout=15)
    r2.raise_for_status()
    estaciones = r2.json()
    df = pd.DataFrame(estaciones)
    if not all(col in df.columns for col in ["indicativo", "nombre"]):
        raise ValueError("Inventario no contiene las columnas esperadas.")
    return df

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def descargar_para_una_estacion(indicativo: str, nombre: str, id_descarga: str, bloques_fechas) -> list:
    """
    Download weather data for a single station.
    """
    filas = []
    for fecha_ini, fecha_fin in bloques_fechas:
        url = (
            f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{indicativo}"
        )
        try:
            r = requests.get(url, params={"api_key": API_KEY}, timeout=15)
            if r.status_code != 200:
                logging.warning(f"Status {r.status_code} para {indicativo} ({fecha_ini} a {fecha_fin})")
                continue
            datos_meta = r.json()
            url_real = datos_meta.get("datos")
            if not url_real:
                continue
            rd = requests.get(url_real, timeout=15)
            if rd.status_code != 200:
                logging.warning(f"Status {rd.status_code} para datos reales de {indicativo}")
                continue
            lista_json = rd.json()
            for rec in lista_json:
                rec["nombre"] = nombre
                rec["timestamp_extraccion"] = datetime.utcnow().isoformat()
                rec["id_descarga"] = id_descarga
                filas.append(rec)
            time.sleep(1.2)
        except requests.RequestException as e:
            logging.error(f"Error downloading {indicativo} for {fecha_ini} to {fecha_fin}: {e}")
            continue
    return filas

def extract_data():
    """
    Extract weather data for all stations, incrementally for new dates.
    """
    logging.info("📥 Iniciando extracción...")
    estaciones_df = obtener_inventario_completo()
    estaciones_df = estaciones_df.dropna(subset=["indicativo"]).reset_index(drop=True)
    hoy = datetime.utcnow().date()
    hace_dos_años = hoy - timedelta(days=730)
    
    # Default full range blocks for new stations
    full_bloques_fechas = []
    inicio = hace_dos_años
    while inicio <= hoy:
        fin = min(inicio + timedelta(days=182), hoy)
        full_bloques_fechas.append((f"{inicio.isoformat()}T00:00:00UTC", f"{fin.isoformat()}T00:00:00UTC"))
        inicio = fin + timedelta(days=1)
    
    ARCHIVO_SALIDA = Path("..") / "data" / "temperaturas_historicas_todas.csv"
    station_date_ranges = {}  # Map indicativo to (last_date, needs_update)
    if ARCHIVO_SALIDA.exists():
        try:
            df_prev = pd.read_csv(ARCHIVO_SALIDA, dtype=str, usecols=["indicativo", "fecha"])
            df_prev["fecha"] = pd.to_datetime(df_prev["fecha"], errors="coerce")
            for indicativo in df_prev["indicativo"].unique():
                fechas = df_prev[df_prev["indicativo"] == indicativo]["fecha"]
                if fechas.empty or fechas.isna().all():
                    continue
                last_date = fechas.max().date()
                if last_date >= hoy:
                    station_date_ranges[indicativo] = (last_date, False)  # No update needed
                else:
                    station_date_ranges[indicativo] = (last_date, True)  # Update needed
        except Exception as e:
            logging.error(f"Error al leer {ARCHIVO_SALIDA}: {e}")
    
    id_descarga = str(uuid.uuid4())
    logging.info(f"Starting extraction with ID: {id_descarga}")
    logging.info(f"Total de estaciones: {len(estaciones_df)}")
    todas_las_filas = []
    for idx, row in estaciones_df.iterrows():
        indicativo = row["indicativo"]
        nombre = row.get("nombre", "")
        if indicativo in station_date_ranges and not station_date_ranges[indicativo][1]:
            logging.info(f"Skipping station {indicativo} (data up to date until {station_date_ranges[indicativo][0]})")
            continue
        
        # Determine date range for extraction
        if indicativo in station_date_ranges and station_date_ranges[indicativo][1]:
            # Incremental update: extract from last_date + 1 to hoy
            last_date = station_date_ranges[indicativo][0]
            start_date = last_date + timedelta(days=1)
            if start_date > hoy:
                logging.info(f"Skipping station {indicativo} (no new dates to extract)")
                continue
            bloques_fechas = [(f"{start_date.isoformat()}T00:00:00UTC", f"{hoy.isoformat()}T00:00:00UTC")]
            logging.info(f"Processing station {indicativo} - {nombre} ({idx + 1}/{len(estaciones_df)}) for dates {start_date} to {hoy}")
        else:
            # Full range for new or incomplete stations
            bloques_fechas = full_bloques_fechas
            logging.info(f"Processing station {indicativo} - {nombre} ({idx + 1}/{len(estaciones_df)}) for full range")
        
        filas_est = descargar_para_una_estacion(indicativo, nombre, id_descarga, bloques_fechas)
        todas_las_filas.extend(filas_est)
    
    if todas_las_filas:
        df = pd.DataFrame(todas_las_filas)
        ARCHIVO_SALIDA.parent.mkdir(exist_ok=True)
        mode = 'a' if ARCHIVO_SALIDA.exists() else 'w'
        df.to_csv(ARCHIVO_SALIDA, mode=mode, index=False, header=not ARCHIVO_SALIDA.exists())
        logging.info(f"Extracción completa. Guardado en: {ARCHIVO_SALIDA}")
        logging.info(f"Filas nuevas: {len(df)}")
        return df
    logging.info("No se obtuvieron datos nuevos.")
    return pd.DataFrame()

def rellenar_por_estacion(grupo):
    """
    Fill missing values in a station's data using median and interpolation.
    """
    inicio, fin = grupo["fecha"].min(), grupo["fecha"].max()
    grupo = grupo[(grupo["fecha"] >= inicio) & (grupo["fecha"] <= fin)].copy()
    columnas_a_imputar = [
        "tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia"
    ]
    for col in columnas_a_imputar:
        if col in grupo.columns:
            serie = grupo[col]
            mediana = serie.median()
            es_nan = serie.isna()
            bloques = (es_nan != es_nan.shift()).cumsum()
            for b in bloques[es_nan].unique():
                idx_bloque = bloques[bloques == b].index
                if len(idx_bloque) <= 3:
                    grupo.loc[idx_bloque, col] = mediana
            grupo[col] = grupo[col].interpolate(method="linear", limit_direction="both")
            grupo[col] = grupo[col].fillna(mediana)
    return grupo

def clean_data(df):
    """
    Clean and transform extracted data to match datos_meteorologicos_table schema.
    """
    if df.empty:
        logging.warning("No data to clean.")
        return df
    
    # Convert numeric columns, handling commas
    columnas_num = [
        "tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia", "altitud"
    ]
    for col in columnas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=True), errors="coerce")
    
    # Convert dates
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    df["timestamp_extraccion"] = pd.to_datetime(df["timestamp_extraccion"], errors="coerce")
    
    # Map province to normalized name, codigo_provincia, and codigo_ca
    try:
        mappings = df["provincia"].apply(get_provincia_mappings)
        df["provincia"] = mappings.apply(lambda x: x[0])
        df["codigo_provincia"] = mappings.apply(lambda x: x[1])
        df["codigo_ca"] = mappings.apply(lambda x: x[2])
        df["codigo_provincia"] = df["codigo_provincia"].astype("Int64")  # Nullable TINYINT
        if df["codigo_provincia"].isna().any() or df["codigo_ca"].isna().any():
            unmapped = df[df["codigo_provincia"].isna() | df["codigo_ca"].isna()]["provincia"].unique()
            logging.warning(f"Unmapped provinces: {unmapped}")
    except Exception as e:
        logging.error(f"Error mapping provinces: {e}")
        raise
    
    # Generate id_limpieza
    df["id_limpieza"] = range(1, len(df) + 1)
    
    # Select and rename columns
    df = df[
        [
            "id_descarga",
            "indicativo",
            "nombre",
            "provincia",
            "codigo_provincia",
            "codigo_ca",
            "altitud",
            "fecha",
            "tmin",
            "tmax",
            "tmed",
            "prec",
            "velmedia",
            "racha",
            "hrMedia",
            "timestamp_extraccion",
            "id_limpieza"
        ]
    ].copy()
    
    # Ensure data types
    for col in ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia", "altitud"]:
        df[col] = df[col].astype(float, errors="ignore")
    df["id_limpieza"] = df["id_limpieza"].astype(int)
    
    # Apply configurable thresholds
    for col, limits in THRESHOLDS.items():
        if col in df.columns:
            try:
                if limits.get("min") is not None:
                    df.loc[df[col] < limits["min"], col] = pd.NA
                if limits.get("max") is not None:
                    df.loc[df[col] > limits["max"], col] = pd.NA
            except Exception as e:
                logging.error(f"Error applying thresholds for {col}: {e}")
    
    # Validate temperature consistency
    df.loc[df["tmin"] > df["tmax"], ["tmin", "tmax", "tmed"]] = pd.NA
    
    # Impute missing values
    df = df.groupby("indicativo", group_keys=False).apply(rellenar_por_estacion).reset_index(drop=True)
    
    # Final cleaning
    df = df.dropna(subset=["tmed"]).reset_index(drop=True)
    df["prec"] = df["prec"].fillna(0)
    
    # Deduplicate by primary key
    df = df.drop_duplicates(subset=["fecha", "indicativo"], keep="last").reset_index(drop=True)
    
    # Save cleaned CSV
    ARCHIVO_LIMPIO = Path("..") / "data" / "temperaturas_limpias.csv"
    ARCHIVO_LIMPIO.parent.mkdir(exist_ok=True)
    df.to_csv(ARCHIVO_LIMPIO, index=False)
    logging.info(f"Cleaned CSV saved to: {ARCHIVO_LIMPIO}")
    logging.info(f"Final data shape: {df.shape}")
    return df

def load_data(df):
    """
    Load cleaned data into the database.
    """
    if df.empty:
        logging.warning("No data to load.")
        return
    try:
        logging.info(f"Iniciando inserción de {len(df)} filas usando df.to_sql()...")
        conn = conexion()
        df.to_sql(
            name="datos_meteorologicos",
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=10000
        )
        logging.info(f"¡{len(df)} filas insertadas correctamente usando df.to_sql()!")
        conn.close()
    except Exception as e:
        logging.error(f"Error durante la inserción con df.to_sql(): {e}")
        raise

def main():
    """
    Run the ETL pipeline.
    """
    try:
        df = extract_data()
        if not df.empty:
            df = clean_data(df)
            load_data(df)
        else:
            logging.info("No data to process.")
    except Exception as e:
        logging.error(f"ETL pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()