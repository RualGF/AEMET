import pandas as pd

from datetime import datetime
from sqlalchemy import func

from src.conectar import conexion_a_bd
from src.poblar import tabla_dm, poblar_datos_meteorologicos
from src.ETL import run_etl


motor = conexion_a_bd()

df = run_etl()
poblar_datos_meteorologicos(motor.connect(), df)


# Pensábamos hacerlo por timestamp, pero decidimos hacer los últimos 3 días, por la falta de cohesión en la periodicidad de la Aemet
def obtener_ultimo_timestamp() -> datetime | None:
    """
    Consulta la tabla 'datos_meteorologicos' para encontrar el último
    timestamp de extracción.
    """
    print("Consultando el último timestamp registrado en la base de datos...")
    # Usamos func.max para obtener el valor máximo de la columna timestamp
    consulta = func.max(tabla_dm.c.timestamp_extraccion)
    motor = conexion_a_bd()
    with motor.connect() as conector:
        ultimo_timestamp = conector.execute(consulta).scalar_one_or_none()
    if ultimo_timestamp:
        print(f"Último timestamp encontrado: {ultimo_timestamp}")
        return ultimo_timestamp
    else:
        print(
            "No se encontraron registros. Se devolverá None para indicar una carga completa."
        )
        return None


def descargar_nuevos_datos_aemet() -> pd.DataFrame:
    """
    Función principal para descargar datos nuevos.
    Orquesta la obtención de la fecha de inicio y la llamada a la API.
    """
    ultimo_timestamp = obtener_ultimo_timestamp()


    if ultimo_timestamp is None:
        print(
            "La base de datos parece estar vacía. Ejecuta primero el script 'popular.py' para la carga inicial."
        )
        return pd.DataFrame()

    print(f"Iniciando descarga de datos posteriores a {ultimo_timestamp}.")

    #df = run_etl(ultimo_timestamp)
  
    #poblar_datos_meteorologicos(motor.connect(), df)

    return pd.DataFrame()
