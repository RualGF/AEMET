import logging
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
from sqlalchemy import func

from src.conectar import conexion_a_bd
from src.poblar import tabla_dm
from src.actualizar_historico_aemet import (
    obtener_api_key,
    descargar_bloque_todas_estaciones,
    limpiar_y_transformar_nuevos_datos,
)

logger = logging.getLogger(__name__)


def obtener_ultima_fecha_bd() -> date | None:
    """
    Consulta la tabla 'datos_meteorologicos' para encontrar la última
    fecha de datos registrada en la base de datos.
    """
    consulta = func.max(tabla_dm.c.fecha)
    motor = conexion_a_bd()
    with motor.connect() as conector:
        ultima_fecha = conector.execute(consulta).scalar_one_or_none()
    
    if ultima_fecha:
        if isinstance(ultima_fecha, str):
            ultima_fecha = pd.to_datetime(ultima_fecha).date()
        elif hasattr(ultima_fecha, "date"):
            ultima_fecha = ultima_fecha.date()
        return ultima_fecha
    return None


def descargar_nuevos_datos_aemet() -> pd.DataFrame:
    """
    Función llamada desde el botón de la barra lateral en Inicio.py.
    Determina la última fecha en la base de datos y descarga/procesa
    los días pendientes hasta hoy mediante bloques de todasestaciones.
    """
    ultima_fecha = obtener_ultima_fecha_bd()
    hoy = date.today()

    if ultima_fecha is None:
        logger.warning("La base de datos parece no tener registros. Ejecuta primero poblar.py.")
        return pd.DataFrame()

    fecha_inicio = ultima_fecha + timedelta(days=1)
    if fecha_inicio >= hoy:
        logger.info("La base de datos ya está completamente al día.")
        return pd.DataFrame()

    logger.info(f"Descargando datos nuevos desde {fecha_inicio} hasta {hoy}...")
    api_key = obtener_api_key()

    # Generar ventanas de hasta 14 días
    ventanas = []
    curr_ini = fecha_inicio
    while curr_ini <= hoy:
        curr_fin = min(curr_ini + timedelta(days=13), hoy)
        ventanas.append((curr_ini, curr_fin))
        curr_ini = curr_fin + timedelta(days=1)

    todos_registros = []
    for ini, fin in ventanas:
        registros = descargar_bloque_todas_estaciones(ini, fin, api_key)
        todos_registros.extend(registros)

    if not todos_registros:
        logger.info("No se encontraron registros nuevos en AEMET para el rango solicitado.")
        return pd.DataFrame()

    df_nuevos = pd.DataFrame(todos_registros)
    df_limpio = limpiar_y_transformar_nuevos_datos(df_nuevos)
    
    # Renombrar indicativo a codigo_indicativo para compatibilidad con poblar_datos_meteorologicos
    if "indicativo" in df_limpio.columns and "codigo_indicativo" not in df_limpio.columns:
        df_limpio = df_limpio.rename(columns={"indicativo": "codigo_indicativo"})

    return df_limpio
