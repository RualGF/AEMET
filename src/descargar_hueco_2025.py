import os
import sys
import time
import logging
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from src.actualizar_historico_aemet import (
    obtener_api_key,
    descargar_bloque_todas_estaciones,
    limpiar_y_transformar_nuevos_datos,
)
from src.poblar import poblar_datos_meteorologicos, motor


def descargar_hueco_primer_semestre_2025():
    api_key = obtener_api_key()
    
    fecha_inicio = date(2025, 1, 1)
    fecha_fin = date(2025, 6, 11)
    
    logger.info(f"Descargando hueco de AEMET: del {fecha_inicio} al {fecha_fin}...")

    ventanas = []
    curr_ini = fecha_inicio
    while curr_ini <= fecha_fin:
        curr_fin = min(curr_ini + timedelta(days=13), fecha_fin)
        ventanas.append((curr_ini, curr_fin))
        curr_ini = curr_fin + timedelta(days=1)

    todos_registros = []
    for i, (ini, fin) in enumerate(ventanas, 1):
        logger.info(f"[{i}/{len(ventanas)}] Descargando del {ini} al {fin}...")
        registros = descargar_bloque_todas_estaciones(ini, fin, api_key)
        todos_registros.extend(registros)
        logger.info(f"  -> Obtenidos {len(registros)} registros (Acumulado: {len(todos_registros)})")
        time.sleep(1.0)

    if not todos_registros:
        logger.error("No se descargaron registros de AEMET.")
        return

    logger.info(f"Limpiando y transformando {len(todos_registros)} registros descargados...")
    df_nuevos = pd.DataFrame(todos_registros)
    df_limpio = limpiar_y_transformar_nuevos_datos(df_nuevos)

    # Cargar dataset existente
    pkl_path = BASE_DIR / "data" / "temperaturas_limpias_10_años_final.pkl"
    logger.info(f"Cargando dataset actual de {pkl_path}...")
    df_actual = pd.read_pickle(pkl_path)
    df_actual["fecha"] = pd.to_datetime(df_actual["fecha"])

    # Combinar
    logger.info("Combinando y eliminando duplicados...")
    df_total = pd.concat([df_actual, df_limpio], ignore_index=True)
    assert isinstance(df_total, pd.DataFrame)
    df_total = df_total.drop_duplicates(subset=["indicativo", "fecha"], keep="last")
    df_total = df_total.sort_values(by=["indicativo", "fecha"]).reset_index(drop=True)

    # Interpolar huecos que pudieran quedar en estos nuevos datos
    logger.info("Interpolando series temporales por estación...")
    cols_num = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia"]
    df_total["prec"] = df_total["prec"].fillna(0.0)

    for col in ["tmin", "tmax", "tmed", "velmedia", "racha", "hrMedia"]:
        df_total[col] = df_total.groupby("indicativo")[col].transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
        med_est = df_total.groupby("indicativo")[col].transform("median")
        df_total[col] = df_total[col].fillna(med_est)
        med_clust = df_total.groupby("cluster")[col].transform("median")
        df_total[col] = df_total[col].fillna(med_clust)

    logger.info(f"Guardando dataset consolidado completo sin huecos en {pkl_path}...")
    df_total.to_pickle(pkl_path)
    logger.info(f"✅ Total registros en dataset consolidado: {len(df_total):,}")

    # Sincronizar en MariaDB
    logger.info("Sincronizando nuevos datos en MariaDB...")
    with motor.begin() as conn:
        poblar_datos_meteorologicos(conn, df_total)
    logger.info("✅ ¡Base de datos MariaDB sincronizada!")


if __name__ == "__main__":
    descargar_hueco_primer_semestre_2025()
