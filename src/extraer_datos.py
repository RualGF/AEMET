import pandas as pd
from sqlalchemy import text

import conectar


# Cadena de conexión para MySQL usando PyMySQL
try:
    motor = conectar.conexion()
    print("Conexión a la base de datos establecida correctamente.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()


# Función para ejecutar una consulta y obtener un DataFrame
def ejecutar_query_a_dataframe(consulta_recibida: str) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL en la base de datos y devuelve los resultados en un DataFrame de pandas.

    Args:
        query_sql (str): La consulta SQL a ejecutar.

    Returns:
        pd.DataFrame: Un DataFrame de pandas con los resultados de la consulta.
                      Devuelve un DataFrame vacío si no hay resultados o si ocurre un error.
    """
    try:
        df_resultado = pd.read_sql(text(consulta_recibida), motor)
        print(
            f"\nConsulta ejecutada con éxito. Se recuperaron {len(df_resultado)} filas."
        )
        return df_resultado
    except Exception as e:
        print(f"Error al ejecutar la consulta:\n{consulta_recibida}\nError: {e}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de error


# Ejemplos de Queries (Consultas)
def armar_consulta(params: dict):
    """
    Armado de consulta con parámetros recibidos de streamlit
    """
    consulta = """
    SELECT
        fecha,
        indicativo,
        tmed
    FROM
        datos_meteorologicos_table
    WHERE
        fecha = %(fecha)s
    ORDER BY
        indicativo;
    """
    try:
        # 'motor' es la conexión global establecida en extraer_datos.py
        df_resultado = pd.read_sql(text(consulta), motor, params=params)
        print(f"Consulta parametrizada ejecutada. Filas: {len(df_resultado)}")
        return df_resultado
    except Exception as e:
        print(f"Error al ejecutar la consulta parametrizada: {consulta} con params {params}. Error: {e}")
        return pd.DataFrame()

# Ejemplo 1: Seleccionar todas las columnas de la tabla datos_meteorologicos
print("\n--- Ejemplo 1: Seleccionar las primeras 5 filas de datos_meteorologicos ---")
query_1 = """
SELECT *
FROM datos_meteorologicos_table
LIMIT 5;
"""
df_ejemplo_1 = ejecutar_query_a_dataframe(query_1)
if not df_ejemplo_1.empty:
    print(df_ejemplo_1)

# Ejemplo 2: Obtener la temperatura media diaria por estación en una fecha específica
print("\n--- Ejemplo 2: Temperatura media por estación para el '2023-01-15' ---")
query_2 = """
SELECT
    fecha,
    indicativo,
    tmed
FROM
    datos_meteorologicos_table
WHERE
    fecha = '2024-01-20'
ORDER BY
    indicativo;
"""
df_ejemplo_2 = ejecutar_query_a_dataframe(query_2)
if not df_ejemplo_2.empty:
    print(df_ejemplo_2)

# Ejemplo 3: Contar el número de registros por provincia, uniendo con la tabla de provincias
print("\n--- Ejemplo 3: Conteo de registros por provincia (últimos 10) ---")
query_3 = """
SELECT
    p.nombre AS nombre_provincia,
    COUNT(dm.provincia) AS total_registros
FROM
    datos_meteorologicos_table AS dm
JOIN
    provincias AS p ON dm.provincia = p.nombre
GROUP BY
    p.nombre
ORDER BY
    total_registros DESC
LIMIT 10;
"""
df_ejemplo_3 = ejecutar_query_a_dataframe(query_3)
if not df_ejemplo_3.empty:
    print(df_ejemplo_3)

# Ejemplo 4: Estaciones con la temperatura máxima más alta registrada
print("\n--- Ejemplo 4: Estaciones con la temperatura máxima más alta (ejemplo) ---")
query_4 = """
SELECT
    nombre,
    MAX(cast(tmax AS DECIMAL)) AS temp_max_historica
FROM
    datos_meteorologicos_table
WHERE
    tmax IS NOT NULL
GROUP BY
    nombre
ORDER BY
    temp_max_historica DESC
LIMIT 5;
"""
df_ejemplo_4 = ejecutar_query_a_dataframe(query_4)
if not df_ejemplo_4.empty:
    print(df_ejemplo_4)

# --- 4. Puedes añadir tus propias consultas aquí ---
# Por ejemplo, una consulta para encontrar la precipitación total por provincia en un rango de fechas.
# print("\n--- Mi Consulta Personalizada ---")
# my_custom_query = """
# SELECT
#     p.nombre AS provincia,
#     SUM(dm.precipitacion) AS precipitacion_total
# FROM
#     datos_meteorologicos AS dm
# JOIN
#     provincias AS p ON dm.codigo_provincia = p.codigo_ine
# WHERE
#     dm.fecha BETWEEN '2023-01-01' AND '2023-12-31'
# GROUP BY
#     p.nombre
# ORDER BY
#     precipitacion_total DESC
# LIMIT 5;
# """
# df_custom = ejecutar_query_a_dataframe(my_custom_query)
# if not df_custom.empty:
#     print(df_custom)

# --- 5. Cerrar la conexión ( SQLAlchemy maneja esto automáticamente con 'with motor.connect()') ---
# No es necesario un motor.dispose() explícito aquí a menos que tengas un caso de uso muy específico
# y quieras forzar la desconexión de todas las conexiones en el pool.
print("\nScript de extracción de datos finalizado.")
