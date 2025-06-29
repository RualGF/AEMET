import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pandas as pd
import streamlit as st
from datetime import date, datetime

# from snowflake.snowpark.session import Session
from sqlalchemy import select, MetaData, func, bindparam
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import Select, Executable


from src.conectar import conexion_a_bd

try:
    motor = conexion_a_bd()

    meta = MetaData()
    meta.reflect(bind = motor)


    # Reflejar la estructura de la BD de una vez
    tabla_dm = meta.tables["datos_meteorologicos"]
    tabla_prov = meta.tables["provincias"]
    tabla_ccaa = meta.tables["comunidades"]
    tabla_est = meta.tables["estaciones"]

    df_provincias = pd.read_sql_table(tabla_prov.name, motor)
    df_comunidades = pd.read_sql_table(tabla_ccaa.name, motor)
    df_estaciones = pd.read_sql_table(tabla_est.name, motor)


except OperationalError as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()


# Función para ejecutar una consulta y obtener un DataFrame

def construir_consulta_general(parametros: dict) -> Select:
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

    # Se reduce el nombre de las variables, para no liar demasiado el código en las consultas
    dm = tabla_dm
    pr = tabla_prov
    ca = tabla_ccaa
    from_clause = dm

    if "join" in parametros:
        if "provincia" in parametros["join"]:
            from_clause = from_clause.join(pr, dm.c.codigo_prov == pr.c.codigo_prov)
        if "ccaa" in parametros["join"]:
            from_clause = from_clause.join(ca, pr.c.codigo_ca == ca.c.codigo_ca)

    consulta_stmt = select(*parametros.get("select", [dm])).select_from(from_clause)

    if "filters" in parametros:
        for condition in parametros["filters"]:
            consulta_stmt = consulta_stmt.where(condition)

    if "group_by" in parametros:
        consulta_stmt = consulta_stmt.group_by(*parametros["group_by"])

    if "order_by" in parametros:
        consulta_stmt = consulta_stmt.order_by(*parametros["order_by"])

    return consulta_stmt

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


def generar_df_cache(clave_df: str, clave_parametros: str, stmt_conf: dict, **parametros: dict) -> pd.DataFrame:
    """
    Devuelve un DataFrame ejecutando una consulta si no hay cache o cambian los parámetros.

    - clave_df: nombre para guardar el DataFrame en session_state
    - clave_params: nombre para guardar los parámetros previos
    - stmt_conf: configuración de la consulta SQL
    - params: parámetros como fecha_inicio, fecha_fin, etc.
    """
    with st.sidebar:
        if (clave_df not in st.session_state) or (st.session_state.get(clave_parametros) != parametros):
            consulta = construir_consulta_general(stmt_conf)
            with st.expander(f"Ejecutando consulta SQL para '{clave_df}' con parámetros:"):
                st.write(parametros)
            #st.write(f"Ejecutando consulta SQL para '{clave_df}' con parámetros:", parametros)
            
            df = ejecutar_consulta_a_dataframe(consulta, **parametros)
            st.session_state[clave_df] = df
            st.session_state[clave_parametros] = parametros
        else:
            #st.write(f"Usando cache para '{clave_df}'")
            st.expander(f"Usando cache para '{clave_df}'")
        return st.session_state[clave_df]


def obtener_rango_de_fechas():
    """
    Consulta la base de datos para obtener la fecha mínima y máxima de los registros.
    Usa el cache de Streamlit para eficiencia.
    """
    try:
        with motor.connect() as conector:
            # Construye la consulta para obtener min y max fecha
            consulta_stmt = select(func.min(tabla_dm.c.fecha), func.max(tabla_dm.c.fecha))
            resultado = conector.execute(consulta_stmt).fetchone()

            if resultado and resultado[0] and resultado[1]:
                # Asegura que los valores devueltos sean objetos `date`
                fecha_minima_db = (
                    resultado[0].date() if isinstance(resultado[0], datetime) else resultado[0]
                )
                fecha_maxima_db = (
                    resultado[1].date() if isinstance(resultado[1], datetime) else resultado[1]
                )
                return fecha_minima_db, fecha_maxima_db
            else:
                # Fallback si la tabla está vacía
                return date(2023, 1, 1), date.today()
    except Exception as e:
        st.error(f"Error al consultar rango de fechas: {e}")
        # Fallback en caso de error de conexión
        return date(2023, 1, 1), date.today()


def obtener_estaciones_para_prediccion():
    """
    Consulta la base de datos para obtener las estaciones disponibles para predicción,
    aunque utilizaremos solo su nombre, indicativo y cluster.
    """

    try:

        df_estaciones = pd.read_sql_table(tabla_est.name, motor)
        
        if not df_estaciones.empty:
            st.info("Estaciones cargadas desde la base de datos.")
            return df_estaciones
        else:
            st.warning(
                "La tabla 'estaciones' en la base de datos está vacía. Intentando fallback a archivos locales."
            )
    except Exception as e:
        st.warning(
            f"No se pudo consultar la tabla 'estaciones' en la BD ({e}). Intentando fallback a archivos locales."
        )

    # Si la BD falló o está vacía, intenta leer desde CSV y JSON
    try:
        df_clusters = pd.read_csv("data/estaciones.csv")
        df_nombres = pd.read_json("data/inventario_estaciones.json")

        df_nombres.rename(columns={"nombre": "nombre_estacion"}, inplace = True)
        df_estaciones_merged = pd.merge(
                df_nombres[["indicativo", "nombre_estacion"]],
                df_clusters[["indicativo", "cluster"]],
                on = "indicativo",
                how = "inner",
                )

        if not df_estaciones_merged.empty:
            # Asegurar que el DataFrame resultante del merge también esté ordenado
            df_estaciones = df_estaciones_merged.sort_values(
                by = "nombre_estacion"
            ).reset_index(drop=True)
            st.info(
                "Estaciones cargadas combinando 'data/estaciones.csv' y 'data/inventario_estaciones.json'."
            )
        else:
            st.error(
                "Los archivos locales (CSV/JSON) no contienen datos válidos o no se pudieron combinar."
            )

        if not df_estaciones.empty:
            st.info(
                "Estaciones cargadas combinando 'data/estaciones.csv' y 'data/inventario_estaciones.json'."
            )
    except Exception as e:
        st.error(f"Error al cargar estaciones desde archivos locales (CSV/JSON): {e}.")
    return df_estaciones


def obtener_datos_historicos_estacion(indicativo: str) -> pd.DataFrame:
    """
    Consulta la base de datos para obtener los datos históricos de una estación específica.
    Retorna un DataFrame con columnas fecha y valor de la métrica objetivo.
    """
    try:
        with motor.connect() as conector:
            consulta_stmt = (
                select(tabla_dm)
                .where(tabla_dm.c.codigo_indicativo == indicativo)
                .order_by(tabla_dm.c.fecha)
            )
            df_hist = pd.read_sql(consulta_stmt, conector)
            df_hist["fecha"] = pd.to_datetime(df_hist["fecha"])
            return df_hist
    except Exception as e:
        st.error(
            f"Error al obtener datos históricos para la estación {indicativo}: {e}"
        )
        return pd.DataFrame()


def obtener_datos_diarios_filtrados(fechas, nivel, filtro_nombres, nombre_metrica):
    """
    Obtiene datos meteorológicos diarios para un rango de fechas, nivel territorial y filtro.
    Retorna un DataFrame con 'fecha', la columna de la métrica, y la columna de nombre territorial.
    """
    select_cols = [tabla_dm.c.fecha, tabla_dm.c[nombre_metrica]]
    join_clauses = ["provincia"]

    if nivel == "provincia":
        select_cols.append(tabla_prov.c.nombre_prov)
    elif nivel == "ccaa":
        select_cols.append(tabla_ccaa.c.nombre_ccaa)
        join_clauses.append("ccaa")
    else:
        raise ValueError("Nivel territorial inválido. Debe ser 'provincia' o 'ccaa'.")

    filtros = [
        tabla_dm.c.fecha.between(bindparam("fecha_inicio"), bindparam("fecha_fin"))
    ]

    if filtro_nombres:
        if nivel == "provincia":
            filtros.append(
                tabla_prov.c.nombre_prov.in_(
                    bindparam("filtro_nombres_list", expanding = True)
                )
            )
        elif nivel == "ccaa":
            filtros.append(
                tabla_ccaa.c.nombre_ccaa.in_(
                    bindparam("filtro_nombres_list", expanding = True)
                )
            )

    consulta_stmt = {
        "select": select_cols,
        "join": join_clauses,
        "filters": filtros,
        "order_by": [tabla_dm.c.fecha]
    }

    parametros = {"fecha_inicio": fechas[0], "fecha_fin": fechas[1]}
    if filtro_nombres:
        parametros["filtro_nombres_list"] = filtro_nombres

    df = ejecutar_consulta_a_dataframe(construir_consulta_general(consulta_stmt), **parametros)

    return df
