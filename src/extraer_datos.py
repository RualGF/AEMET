import pandas as pd
import streamlit as st
from datetime import date, datetime

# from snowflake.snowpark.session import Session
from sqlalchemy import select, MetaData, Table, func
from sqlalchemy.exc import OperationalError

from sqlalchemy.sql import Select, Executable


from src.conectar import conexion_a_bd

try:
    motor = conexion_a_bd()

    meta = MetaData()
    # Tablas SQLAlchemy para construir consultas
    tabla_dm = Table("datos_meteorologicos", meta, autoload_with=motor)
    tabla_prov = Table("provincias", meta, autoload_with=motor)
    tabla_ccaa = Table("comunidades", meta, autoload_with=motor)

    df_provincias = pd.read_sql_table(tabla_prov.name, motor)
    df_comunidades = pd.read_sql_table(tabla_ccaa.name, motor)

except OperationalError as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()


# Función para ejecutar una consulta y obtener un DataFrame


def construir_consulta_general(params: dict) -> Select:
    """
    Construye una consulta SQLAlchemy dinámica basada en los parámetros recibidos.

    Args:
        params (dict): Diccionario con claves:
            - select: lista de columnas o expresiones a seleccionar.
            - join: lista con 'provincia' y/o 'ccaa' si se requieren joins.
            - filters: lista de condiciones opcionales.
            - group_by: lista de columnas para agrupamiento.
            - order_by: lista de columnas para ordenar.

    Returns:
        Select: Consulta SQLAlchemy.
    """

    # FROM base
    dm = tabla_dm
    pr = tabla_prov
    ca = tabla_ccaa
    from_clause = dm

    if "join" in params:
        if "provincia" in params["join"]:
            from_clause = from_clause.join(pr, dm.c.codigo_prov == pr.c.codigo_prov)
        if "ccaa" in params["join"]:
            from_clause = from_clause.join(ca, pr.c.codigo_ca == ca.c.codigo_ca)

    stmt = select(*params.get("select", [dm]))  # Por defecto selecciona todo
    stmt = stmt.select_from(from_clause)

    if "filters" in params:
        for condition in params["filters"]:
            stmt = stmt.where(condition)

    if "group_by" in params:
        stmt = stmt.group_by(*params["group_by"])

    if "order_by" in params:
        stmt = stmt.order_by(*params["order_by"])

    return stmt


def ejecutar_consulta_a_dataframe(consulta: Executable, **bindparams) -> pd.DataFrame:
    """
    Ejecuta una consulta SQLAlchemy usando un conector global y devuelve los resultados en un DataFrame.

    Args:
        consulta (Executable): Consulta SQLAlchemy (select, insert, etc.)
        **bindparams: Parámetros para bindparam(), si aplica.

    Returns:
        pd.DataFrame: Resultados de la consulta.
    """
    try:
        with motor.begin() as conn:
            result = conn.execute(consulta, bindparams)
            df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        return df
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        return pd.DataFrame()

def generar_df_cache(clave_df, clave_params, stmt_conf, **params):
    """
    Devuelve un DataFrame ejecutando una consulta si no hay cache o cambian los parámetros.

    - clave_df: nombre para guardar el DataFrame en session_state
    - clave_params: nombre para guardar los parámetros previos
    - stmt_conf: configuración de la consulta SQL
    - params: parámetros como fecha_inicio, fecha_fin, etc.
    """
    if clave_df not in st.session_state or st.session_state.get(clave_params) != params:
        consulta = construir_consulta_general(stmt_conf)
        st.write(f"Ejecutando consulta SQL para '{clave_df}' con parámetros:", params)
        df = ejecutar_consulta_a_dataframe(consulta, **params)
        st.session_state[clave_df] = df
        st.session_state[clave_params] = params
    else:
        st.write(f"Usando cache para '{clave_df}'")

    return st.session_state[clave_df]

@st.cache_data(ttl=3600)  # Cache por 1 hora para no llamar a la BD constantemente
def obtener_rango_de_fechas():
    """
    Consulta la base de datos para obtener la fecha mínima y máxima de los registros.
    Usa el cache de Streamlit para eficiencia.
    """
    try:
        with motor.connect() as connection:
            # Construye la consulta para obtener min y max fecha
            stmt = select(func.min(tabla_dm.c.fecha), func.max(tabla_dm.c.fecha))
            result = connection.execute(stmt).fetchone()

            if result and result[0] and result[1]:
                # Asegura que los valores devueltos sean objetos `date`
                min_db_date = result[0].date() if isinstance(result[0], datetime) else result[0]
                max_db_date = result[1].date() if isinstance(result[1], datetime) else result[1]
                return min_db_date, max_db_date
            else:
                # Fallback si la tabla está vacía
                return date(2023, 1, 1), date.today()
    except Exception as e:
        st.error(f"Error al consultar rango de fechas: {e}")
        # Fallback en caso de error de conexión
        return date(2023, 1, 1), date.today()