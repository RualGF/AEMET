import pandas as pd

from datetime import datetime
from sqlalchemy import func

from src.conectar import conexion_a_bd
from src.poblar import tabla_dm

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

    NOTA: Esta es una simulación. Deberás adaptarla con tu lógica real
    de llamada a la API de AEMET.
    """
    ultimo_timestamp = obtener_ultimo_timestamp()

    # Si no hay timestamp, significa que es la primera carga.
    # Aquí se debería ejecutar la carga masiva desde el PKL, no la API.
    # Por ahora, asumimos que la carga inicial ya se hizo.
    if ultimo_timestamp is None:
        print(
            "La base de datos parece estar vacía. Ejecuta primero el script 'popular.py' para la carga inicial."
        )
        return pd.DataFrame()

    print(f"Iniciando descarga de datos posteriores a {ultimo_timestamp}.")

    # --- SIMULACIÓN DE LLAMADA A API Y PROCESAMIENTO ---
    # Aquí iría tu código para:
    # 1. Obtener los indicativos de las estaciones de la tabla `tabla_est`.
    # 2. Iterar y llamar a la API de AEMET para cada estación, pidiendo datos a partir de `ultimo_timestamp`.
    # 3. Recopilar los resultados en un único DataFrame.
    # 4. Limpiar y transformar el DataFrame para que coincida con la estructura de tu tabla `datos_meteorologicos`.

    # Por ahora, devolvemos un DataFrame vacío como ejemplo.
    # df_nuevos = tu_funcion_real_de_api(ultimo_timestamp)
    # return df_nuevos

    print(
        "Simulación finalizada. En un caso real, aquí se devolverían los datos descargados."
    )

    return pd.DataFrame()
