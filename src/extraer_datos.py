import pandas as pd
from sqlalchemy import text

from src import conectar


# Cadena de conexión para MySQL usando PyMySQL
try:
    motor = conectar.conexion()
    print("Conexión a la base de datos establecida correctamente.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()


# Función para ejecutar una consulta y obtener un DataFrame
def ejecutar_consulta_a_dataframe(consulta_recibida: str = "", params: dict = {}) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL en la base de datos y devuelve los resultados en un DataFrame de pandas.

    Args:
        consulta_recibida (str): La consulta SQL a ejecutar.

    Returns:
        pd.DataFrame: Un DataFrame de pandas con los resultados de la consulta.
                      Devuelve un DataFrame vacío si no hay resultados o si ocurre un error.
    """
    try:
        if consulta_recibida:
            df_resultado = pd.read_sql(text(consulta_recibida), motor)
            print(
                f"\nConsulta ejecutada con éxito. Se recuperaron {len(df_resultado)} filas."
            )
            return df_resultado
        else:
            consulta = """
            SELECT p.nombre,
            d.codigo_prov,
            AVG(d.altitud), 
            AVG(d.tmed),
            AVG(d.tmin),
            AVG(d.tmax),
            AVG(d.prec),
            AVG(d.racha) * 3.6,
            AVG(d.hrMedia)
            FROM datos_meteorologicos as d, provincias as p
            WHERE (d.codigo_prov = p.codigo_prov)
            """
            if params:
                for p in params:
                    if p == "fecha":
                        consulta = consulta + f" AND (d.fecha = '{params[p]}')"
                    elif p == "fecha_inicio":
                        consulta = consulta + f" AND (d.fecha BETWEEN '{params['fecha_inicio']}' AND '{params['fecha_fin']}')"
            consulta = consulta + " GROUP BY d.codigo_prov, p.nombre ORDER BY d.codigo_prov;"
            df_resultado = ejecutar_consulta_a_dataframe(consulta)
            return df_resultado
    except Exception as e:
        print(f"Error al ejecutar la consulta:\n{consulta_recibida}\nError: {e}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de error
