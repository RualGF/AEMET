import pandas as pd
import streamlit as st 

from sqlalchemy import (
    MetaData, Table,
    Column, String, Date, TIMESTAMP,
    Float, ForeignKey, insert
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.exc import IntegrityError
#from sqlalchemy.orm import sessionmaker

from conectar import conexion_a_bd


# Crea tu engine (ajusta URL según tu BD)
motor = conexion_a_bd()
# Session = sessionmaker(bind=conector)
# session = Session()
meta = MetaData()

tabla_ccaa = Table(
    "comunidades", meta,
    Column("codigo_ca", TINYINT(unsigned=True), primary_key=True),
    Column("nombre_ccaa", String(50), nullable=False),
)

tabla_prov = Table(
    "provincias", meta,
    Column("codigo_prov", TINYINT(unsigned=True), primary_key=True),
    Column("nombre_prov", String(50), nullable=False),
    Column("codigo_ca", TINYINT(unsigned=True), ForeignKey("comunidades.codigo_ca"), nullable=False),
)

tabla_dm = Table(
    "datos_meteorologicos", meta,
    Column("id_descarga", String(50), nullable=False),
    Column("fecha", Date, primary_key=True),
    Column("codigo_indicativo", String(10), primary_key=True),
    Column("codigo_prov", TINYINT(unsigned=True), ForeignKey("provincias.codigo_prov"), nullable=False),
    Column("altitud", Float),
    Column("tmed", Float),
    Column("tmin", Float),
    Column("tmax", Float),
    Column("prec", Float),
    Column("racha", Float),
    Column("hrMedia", Float),
    Column("timestamp_extraccion", TIMESTAMP),
)

tabla_est = Table(
    "estaciones", meta,
    Column("codigo_indicativo", String(10), primary_key=True),
    Column("nombre_estacion", String(100), nullable=False),
    Column("codigo_prov", TINYINT(unsigned=True), ForeignKey("provincias.codigo_prov"), nullable=False),
    Column("cluster", TINYINT(unsigned=True), nullable=False),
    extend_existing=True
)
# Crea tablas nuevas
#meta.create_all(motor) #Descomentar para crear las tablas

# Datos de comunidades (del script SQL)
datos_ccaa = [
    (1, 'Andalucía'), (2, 'Aragón'), (3, 'Illes Balears'), (4, 'Canarias'),
    (5, 'Cantabria'), (6, 'Castilla - La Mancha'), (7, 'Castilla y León'),
    (8, 'Cataluña'), (9, 'Ceuta'), (10, 'Extremadura'), (11, 'Galicia'),
    (12, 'La Rioja'), (13, 'Madrid, Comunidad de'), (14, 'Melilla'),
    (15, 'Murcia, Región de'), (16, 'Navarra, Comunidad Foral de'),
    (17, 'País Vasco'), (18, 'Principado de Asturias'), (19, 'Comunitat Valenciana')
]

# Datos de provincias (del script SQL)
datos_provincias = [
    (1, 'Araba/Álava', 17), (2, 'Albacete', 6), (3, 'Alacant/Alicante', 19),
    (4, 'Almería', 1), (5, 'Ávila', 7), (6, 'Badajoz', 10), (7, 'Illes Balears', 3),
    (8, 'Barcelona', 8), (9, 'Burgos', 7), (10, 'Cáceres', 10), (11, 'Cádiz', 1),
    (12, 'Castelló/Castellón', 19), (13, 'Ciudad Real', 6), (14, 'Córdoba', 1),
    (15, 'A Coruña', 11), (16, 'Cuenca', 6), (17, 'Girona', 8), (18, 'Granada', 1),
    (19, 'Guadalajara', 6), (20, 'Gipuzkoa/Guipúzcoa', 17), (21, 'Huelva', 1),
    (22, 'Huesca', 2), (23, 'Jaén', 1), (24, 'León', 7), (25, 'Lleida', 8),
    (26, 'La Rioja', 12), (27, 'Lugo', 11), (28, 'Madrid', 13),
    (29, 'Málaga', 1), (30, 'Murcia', 15), (31, 'Navarra', 16),
    (32, 'Ourense', 11), (33, 'Asturias', 18), (34, 'Palencia', 7),
    (35, 'Las Palmas', 4), (36, 'Pontevedra', 11), (37, 'Salamanca', 7),
    (38, 'Santa Cruz De Tenerife', 4), (39, 'Cantabria', 5), (40, 'Segovia', 7),
    (41, 'Sevilla', 1), (42, 'Soria', 7), (43, 'Tarragona', 8),
    (44, 'Teruel', 2), (45, 'Toledo', 6), (46, 'València/Valencia', 19),
    (47, 'Valladolid', 7), (48, 'Bizkaia/Vizcaya', 17), (49, 'Zamora', 7),
    (50, 'Zaragoza', 2), (51, 'Ceuta', 9), (52, 'Melilla', 14)
]

# Insertar datos #Descomentar para poblar las tablas comunidades y provincias
# with motor.begin() as conector:
#     conector.execute(tabla_ccaa.insert(), [
#         {"codigo_ca": c[0], "nombre_ccaa": c[1]} for c in datos_ccaa
#     ])
#     conector.execute(tabla_prov.insert(), [
#         {"codigo_prov": p[0], "nombre_prov": p[1], "codigo_ca": p[2]} for p in datos_provincias
#     ])

#     print("✅ Comunidades y provincias insertadas correctamente.")

def validar_provincias_en_bd(df: pd.DataFrame, tabla_prov):
    """
    Verifica si todas las provincias presentes en el DataFrame están en la tabla 'provincias' de la BD.

    Args:
        df (pd.DataFrame): DataFrame que contiene una columna 'provincia' con los nombres.
        engine: Conexión SQLAlchemy.
        tabla_prov: Objeto Table de SQLAlchemy para 'provincias'.

    Returns:
        set: Conjunto de provincias no encontradas en la base de datos.
    """
    provincias_en_datos = set(df["provincia"].dropna().unique())
    
    with motor.begin() as conector:
        resultado = conector.execute(
            tabla_prov.select().with_only_columns(tabla_prov.c.nombre_prov)
        )
        provincias_en_bd = set(row[0] for row in resultado)

    no_encontradas = provincias_en_datos - provincias_en_bd

    if no_encontradas:
        print("⚠️ Provincias no encontradas en la tabla 'provincias':")
        for prov in sorted(no_encontradas):
            print(f"  - {prov}")
    else:
        print("✅ Todas las provincias están correctamente registradas en la base de datos.")

    return no_encontradas

def insertar_por_lotes(tabla, datos, conn, tamaño_lote=100, verbose=True):
    """
    Inserta registros en una tabla SQLAlchemy por lotes, con seguimiento opcional del progreso.

    Args:
        tabla (Table): Objeto SQLAlchemy de la tabla destino.
        datos (list[dict]): Lista de registros (dicts) a insertar.
        conn (Connection): Conexión activa de SQLAlchemy.
        tamaño_lote (int): Número de registros por lote.
        verbose (bool): Si True, imprime el progreso.
    """
    total = len(datos)
    if total == 0:
        if verbose:
            print(f"ℹ️ No hay datos para insertar en '{tabla.name}'.")
        return
    if verbose:
        print(f"🚀 Iniciando inserción de {total} registros en '{tabla.name}' (lotes de {tamaño_lote})...")
    
    try:
        for i in range(0, total, tamaño_lote):
            lote = datos[i:i + tamaño_lote]
            
            if verbose:
                # Imprimir antes de la ejecución para saber qué lote se está intentando
                print(f"📦 Intentando insertar lote en '{tabla.name}': registros {i+1} a {min(i + tamaño_lote, total)} de {total}")
            conn.execute(tabla.insert(), lote) # Mover la ejecución después del print de progreso
            if verbose:
                print(f"🟢 Lote insertado para '{tabla.name}': {min(i + tamaño_lote, total)} / {total} registros.")
        if verbose:
            print(f"✅ Inserción por lotes finalizada para '{tabla.name}': {total} registros procesados.")

    except IntegrityError as eintegry:
            print(eintegry)
    except Exception as e:
        print(e)
            
def cargar_datos_desde_pkl(ruta_pkl: str):
    df = pd.read_pickle(ruta_pkl)
    # no_encontradas = validar_provincias_en_bd(df, tabla_prov)
    # if no_encontradas:
    #     print(no_encontradas)
    
    # Extraer dataframe de estaciones
        # Asegurar que solo haya una entrada por 'indicativo'.
    # Se elige 'last' para ser coherente con la lógica de actualización de 'cluster'
    # en caso de IntegrityError durante la inserción, que efectivamente usa el último valor visto.
    df_est = df[["indicativo", "nombre", "provincia", "cluster"]].drop_duplicates(subset=['indicativo'], keep='last')
    df_est = df_est.rename(columns={
        "indicativo": "codigo_indicativo",
        "nombre": "nombre_estacion",
        "provincia": "nombre_prov_lookup"
    })
    
    # Extraer dataframe de datos meteorológicos
    df_dm = df.rename(columns={
        "indicativo": "codigo_indicativo"
    })
        
    # Obtener valores únicos de provincias y comunidades
    # df_prov = df_est[["nombre_prov"]].drop_duplicates()
    
    # Inserción segura 
    
    # with motor.begin() as conector:
    #     # Insertar provincias si no existen
    #     # for npv in df_prov["nombre_prov"]:
    #     #     existing = conector.execute(
    #     #         tabla_prov.select().where(tabla_prov.c.nombre_prov == npv)
    #     #     ).fetchone()
    #     #     if not existing:
    #     #         # Aquí código_ca debería mapearse con lógica real
    #     #         conector.execute(tabla_prov.insert(), {"nombre_prov": npv, "codigo_ca": None})
    
    #     # En principio si las provincias están limpias no se necesita lo de arriba    
    
    #     # Insertar estaciones #Descomentar lo de abajo para poblar estaciones
     
    #     for row in df_est.to_dict(orient="records"):
            
    #         prov = conector.execute(
    #             tabla_prov.select().where(tabla_prov.c.nombre_prov == row["nombre_prov_lookup"])
    #             ).fetchone()
    
    #         if prov is None:
    #             raise ValueError(f"Provincia no encontrada: {row['provincia']}")  # o manejar como error
    #         # else:
    #         #     print(f"✅ Provincia encontrada: {row}")

    #         codigo_prov = prov.codigo_prov  # ✅ acceso por atributo
            
    #         try:
    #             del row["nombre_prov_lookup"]
    #             row["codigo_prov"] = codigo_prov
                
    #             conector.execute(tabla_est.insert(), row)
    #         except IntegrityError:
    #             conector.execute(
    #                 tabla_est.update()
    #                 .where(tabla_est.c.codigo_indicativo == row["codigo_indicativo"])
    #                 .values(cluster=row["cluster"])
    #             )
    #         except Exception as e:
    #             print(e)
        
    with motor.begin() as conector:    
        # Insertar datos meteorológicos
        print("ℹ️  Iniciando procesamiento de datos meteorológicos...")
        df_provincias = pd.read_sql_table(tabla_prov.name, motor)

        current_records_batch = []
        # Define un tamaño para los lotes de Python antes de llamar a insertar_por_lotes.
        # Este es diferente del tamaño_lote dentro de insertar_por_lotes, que es para los INSERT SQL.
        python_batch_size = 50000  # Por ejemplo, procesar 50,000 registros de Python a la vez
        total_rows_processed = 0
          
        for index, row_series in df_dm.iterrows(): # Iterar fila por fila para ahorrar memoria
            rec_dict = row_series.to_dict() # Convertir la fila actual (Series) a diccionario
            nombre_prov_a_buscar = rec_dict.get("provincia")
            
            if nombre_prov_a_buscar is None:
                print(f"⚠️ Registro DM en índice {index} sin 'provincia'. Saltando.")
                continue
            
            filas_provincia = df_provincias[df_provincias["nombre_prov"] == nombre_prov_a_buscar]
            
            if filas_provincia.empty:
                print(f"⚠️ Provincia '{nombre_prov_a_buscar}' no encontrada en df_provincias para registro DM en índice {index}. Saltando.")
            # Asumimos que nombre_prov es único, tomamos el primer resultado.
            codigo_prov_fk = filas_provincia["codigo_prov"].iloc[0]
            
            # Preparamos el diccionario para la inserción, asegurando solo las columnas de tabla_dm
            dm_record_to_insert = {col.name: rec_dict.get(col.name) for col in tabla_dm.columns if col.name in rec_dict}
            dm_record_to_insert["codigo_prov"] = codigo_prov_fk # Asignamos el codigo_prov correcto
            
            current_records_batch.append(dm_record_to_insert)
            total_rows_processed += 1
            if len(current_records_batch) >= python_batch_size:
                print(f"ℹ️  Enviando lote de {len(current_records_batch)} registros de Python a insertar_por_lotes...")
                insertar_por_lotes(tabla_dm, current_records_batch, conector, tamaño_lote=100) # tamaño_lote aquí es para SQL
                current_records_batch = [] # Resetear el lote de Python
        
        if current_records_batch:
            print(f"ℹ️  Enviando lote final de {len(current_records_batch)} registros de Python a insertar_por_lotes...")
            insertar_por_lotes(tabla_dm, current_records_batch, conector, tamaño_lote=100)
        
        print(f"✅ Total de {total_rows_processed} filas de datos meteorológicos procesadas desde el DataFrame.")



if __name__ == "__main__":
    cargar_datos_desde_pkl("data/temperaturas_limpias_10_años_final.pkl")
    print("Carga completada ✅")


