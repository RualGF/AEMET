import pandas as pd

#from snowflake.snowpark.session import Session
from sqlalchemy import  select, MetaData, Table

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

except Exception as e:
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