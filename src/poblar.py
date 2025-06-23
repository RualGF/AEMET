import argparse
import pandas as pd

from sqlalchemy import (
    MetaData, Table, Column, String, Date, TIMESTAMP, Float, ForeignKey, Connection
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.exc import IntegrityError

from src.conectar import conexion_a_bd



motor = conexion_a_bd()

# --- Definición de Tablas y Metadatos ---
meta = MetaData()

tabla_ccaa = Table(
    "comunidades", meta,
    Column("codigo_ca", TINYINT(unsigned=True), primary_key=True),
        Column("nombre_ccaa", String(50), nullable=False, unique=True),
)

tabla_prov = Table(
    "provincias", meta,
    Column("codigo_prov", TINYINT(unsigned=True), primary_key=True),
    Column("nombre_prov", String(50), nullable=False, unique=True),
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
    Column("velmedia", Float),
    Column("racha", Float),
    Column("hrMedia", Float),
    Column("timestamp_extraccion", TIMESTAMP),
)

tabla_est = Table(
    "estaciones", meta,
    Column("codigo_indicativo", String(10), primary_key=True),
    Column("nombre_estacion", String(100), nullable=False),
    Column("codigo_prov", TINYINT(unsigned=True), ForeignKey("provincias.codigo_prov"), nullable=False),
    Column("start_date", Date),
    Column("end_date", Date),
    Column("latitud_dd", Float),
    Column("longitud_dd", Float),
    Column("cluster", TINYINT(unsigned=True)),
    extend_existing=True
)
# --- Funciones de Inserción por Tabla ---

def poblar_comunidades(conector: Connection):
    """Inserta los datos estáticos de las comunidades autónomas."""
    datos_ccaa = [
        (1, 'Andalucía'), (2, 'Aragón'), (3, 'Illes Balears'), (4, 'Canarias'),
        (5, 'Cantabria'), (6, 'Castilla - La Mancha'), (7, 'Castilla y León'),
        (8, 'Cataluña'), (9, 'Ceuta'), (10, 'Extremadura'), (11, 'Galicia'),
        (12, 'La Rioja'), (13, 'Madrid, Comunidad de'), (14, 'Melilla'),
        (15, 'Murcia, Región de'), (16, 'Navarra, Comunidad Foral de'),
        (17, 'País Vasco'), (18, 'Principado de Asturias'), (19, 'Comunitat Valenciana')
    ]
    registros = [{"codigo_ca": c[0], "nombre_ccaa": c[1]} for c in datos_ccaa]
    print("Poblando tabla 'comunidades'...")
    try:
        # Usamos prefix_with("IGNORE") para que MySQL ignore los duplicados y no lance error
        conector.execute(tabla_ccaa.insert().prefix_with("IGNORE"), registros)
        print("✅ Tabla 'comunidades' poblada/actualizada.")
    except Exception as e:
        print(f"❌ Error al poblar 'comunidades': {e}")

def poblar_provincias(conector: Connection):
    """Inserta los datos estáticos de las provincias."""
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
    registros = [{"codigo_prov": p[0], "nombre_prov": p[1], "codigo_ca": p[2]} for p in datos_provincias]
    print("Poblando tabla 'provincias'...")
    try:
        conector.execute(tabla_prov.insert().prefix_with("IGNORE"), registros)
        print("✅ Tabla 'provincias' poblada/actualizada.")
    except Exception as e:
        print(f"❌ Error al poblar 'provincias': {e}")

def poblar_estaciones(conector: Connection, df_estaciones: pd.DataFrame):
    """
    Inserta o actualiza los datos de las estaciones.
    Realiza un 'upsert': inserta si no existe, actualiza el cluster si ya existe.
    """
    print("ℹ️  Iniciando procesamiento de estaciones...")
    df_provincias_bd = pd.read_sql_table(tabla_prov.name, conector)

    # Unir para obtener codigo_prov de forma eficiente
    df_est_merged = pd.merge(
        df_estaciones,
        df_provincias_bd[['codigo_prov', 'nombre_prov']],
        left_on='nombre_prov',
        right_on='nombre_prov',
        how='left'
    )

    # Validar que todas las provincias se encontraron
    provincias_no_encontradas = df_est_merged[df_est_merged['codigo_prov'].isna()]['nombre_prov'].unique()
    if len(provincias_no_encontradas) > 0:
        print(f"⚠️ Provincias de estaciones no encontradas en la BD: {provincias_no_encontradas}. Se omitirán estas estaciones.")
        df_est_merged.dropna(subset=['codigo_prov'], inplace=True)

    df_est_merged['codigo_prov'] = df_est_merged['codigo_prov'].astype(int)
    
    registros_para_procesar = df_est_merged.to_dict(orient='records')
    
    total = len(registros_para_procesar)
    print(f"🚀 Procesando {total} registros de estaciones...")
    
    for row in registros_para_procesar:
        registro_limpio = {
            "codigo_indicativo": row["codigo_indicativo"],
            "nombre_estacion": row["nombre_estacion"],
            "codigo_prov": row["codigo_prov"],
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            "latitud_dd": row.get("latitud_dd"),
            "longitud_dd": row.get("longitud_dd"),
            "cluster": row.get("cluster")
        }
        
        try:
            conector.execute(tabla_est.insert(), registro_limpio)
        except IntegrityError:
            # Si falla por clave primaria, es que ya existe. Actualizamos el cluster.
            conector.execute(
                tabla_est.update()
                .where(tabla_est.c.codigo_indicativo == registro_limpio["codigo_indicativo"])
                .values(cluster=registro_limpio["cluster"])
            )
        except Exception as e:
            print(f"❌ Error procesando estación {registro_limpio['codigo_indicativo']}: {e}")
            
    print(f"✅ Finalizado procesamiento de estaciones: {total} registros procesados.")

def poblar_datos_meteorologicos(conector: Connection, df_dm: pd.DataFrame):
    """
    Inserta los datos meteorológicos en la base de datos de forma masiva y eficiente.
    """
    print("ℹ️  Iniciando procesamiento de datos meteorológicos...")
    df_provincias_bd = pd.read_sql_table(tabla_prov.name, conector)

    # Optimización: Renombrar columna en df_dm para el merge
    df_dm.rename(columns={'provincia': 'nombre_prov'}, inplace=True)

    # Unir para obtener codigo_prov de forma vectorizada
    df_dm_merged = pd.merge(
        df_dm,
        df_provincias_bd[['codigo_prov', 'nombre_prov']],
        on='nombre_prov',
        how='left'
    )

    # Validar y limpiar
    provincias_no_encontradas = df_dm_merged[df_dm_merged['codigo_prov'].isna()]['nombre_prov'].unique()
    if len(provincias_no_encontradas) > 0:
        print(f"⚠️ Provincias de datos meteorológicos no encontradas en la BD: {provincias_no_encontradas}. Se omitirán estos registros.")
        df_dm_merged.dropna(subset=['codigo_prov'], inplace=True)

    # Seleccionar y ordenar columnas según la tabla de la BD para evitar errores
    columnas_tabla_dm = [c.name for c in tabla_dm.columns]
    df_para_insertar = df_dm_merged[[col for col in columnas_tabla_dm if col in df_dm_merged.columns]]

    # Convertir a lista de diccionarios
    registros = df_para_insertar.to_dict(orient='records')

    # Usar la función de inserción por lotes
    insertar_por_lotes(tabla_dm, registros, conector, tamaño_lote=10000)

def insertar_por_lotes(tabla, datos, conn, tamaño_lote=100, verbose=True):
    """
    Inserta registros en una tabla SQLAlchemy por lotes.
    Usa INSERT IGNORE para evitar fallos por duplicados (específico de MySQL).

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
                print(f"📦 Insertando lote en '{tabla.name}': registros {i+1} a {min(i + tamaño_lote, total)} de {total}")
            conn.execute(tabla.insert().prefix_with("IGNORE"), lote)
        if verbose:
            print(f"✅ Inserción por lotes finalizada para '{tabla.name}': {total} registros procesados.")

    except Exception as e:
                print(f"❌ Error durante la inserción por lotes en '{tabla.name}': {e}")

def main(ruta_pkl: str, tabla_a_poblar: str, ruta_csv_estaciones: str):
    """
    Función principal que orquesta la creación y población de las tablas.

    """
    motor = conexion_a_bd()
    
    # Crear todas las tablas si no existen
    print("Creando tablas si no existen...")
    meta.create_all(motor)
    print("✅ Verificación de tablas completada.")

    with motor.begin() as conector:
        if tabla_a_poblar in ["comunidades", "todas"]:
            poblar_comunidades(conector)

        if tabla_a_poblar in ["provincias", "todas"]:
            poblar_provincias(conector)

        if tabla_a_poblar in ["estaciones", "todas"]:
            print(f"Cargando datos de estaciones desde '{ruta_csv_estaciones}'...")
            df_estaciones_csv = pd.read_csv(ruta_csv_estaciones)
            # Preparamos el DataFrame para que coincida con lo que espera la función de población
            df_est_preparado = df_estaciones_csv.rename(columns={
                "indicativo": "codigo_indicativo",
                "nombre": "nombre_estacion",
                "provincia": "nombre_prov"
            })
            poblar_estaciones(conector, df_est_preparado)

        # La carga de datos meteorológicos masivos se hace desde el PKL
        if tabla_a_poblar in ["datos_meteorologicos", "todas"]:
            print(f"Cargando datos desde '{ruta_pkl}'...")
            df_completo = pd.read_pickle(ruta_pkl)

            df_dm = df_completo.rename(columns={"indicativo": "codigo_indicativo"})
            poblar_datos_meteorologicos(conector, df_dm)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Poblar tablas de la base de datos a partir de un archivo PKL."
    )
    
    parser.add_argument(
        "--tabla",
        choices=["comunidades", "provincias", "estaciones", "datos_meteorologicos", "todas"],
        default="todas",
        help="Especifica la tabla a poblar. 'todas' para poblar todas las tablas (comportamiento por defecto)."
    )
    
    parser.add_argument(
        "--fichero",
        default="data/temperaturas_limpias_10_años_final.pkl",
        help="Ruta al archivo .pkl con los datos."
    )
    
    parser.add_argument(
        "--csv_estaciones",
        default="data/estaciones.csv",
        help="Ruta al archivo .csv con la información de las estaciones."
    )
    args = parser.parse_args()

    main(ruta_pkl=args.fichero, tabla_a_poblar=args.tabla, ruta_csv_estaciones=args.csv_estaciones)
    print(f"Carga de '{args.tabla}' completada ✅")


