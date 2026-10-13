import uuid
import json
import pandas as pd
from datetime import date, timedelta, datetime, timezone
import logging
from cliente_aemet import (
    cargar_inventario,
    configurar_logging,
    obtener_api_key,
    obtener_url_datos,
    solicitar_datos_aemet,
)
from repositorio_archivos import (
    CARPETA_DATA,
    construir_rutas_bloque,
    eliminar_archivo_temporal,
    guardar_bloque_csv,
    preparar_archivos_bloque,
)


logger = logging.getLogger(__name__)

API_KEY = obtener_api_key()

hoy = date.today()
URL_DATOS_DIARIOS = (
    "https://opendata.aemet.es/opendata/api/valores/"
    "climatologicos/diarios/datos/fechaini/{inicio}/fechafin/{fin}/estacion/{codigo}"
)


def cargar_estaciones_ordenadas(ordenar = False):
    estaciones = cargar_inventario(API_KEY).dropna(subset = ["indicativo"])
    if ordenar:
        estaciones = estaciones.sort_values("indicativo")
    logger.info(f"Cargué {len(estaciones)} estaciones")
    return estaciones


def construir_bloques_ultimos_tres_dias():
    return [
        (f"{(hoy - timedelta(days = i)).isoformat()}T00:00:00UTC",
        f"{(hoy - timedelta(days = i)).isoformat()}T00:00:00UTC")
        for i in range(1, 4)
    ]


def extraer_ultimos_tres_dias():
    df_estaciones = cargar_estaciones_ordenadas()
    bloques_fechas = construir_bloques_ultimos_tres_dias()
    return extraer_datos_aemet(df_estaciones, bloques_fechas)


def construir_bloques_por_anyo(anyos):
    bloques = []
    for anyo in anyos:
        bloques.append((f"{date(anyo, 1, 1)}T00:00:00UTC", f"{date(anyo, 6, 30)}T00:00:00UTC"))
        if anyo != hoy.year:
            bloques.append((f"{date(anyo, 7, 1)}T00:00:00UTC", f"{date(anyo, 12, 31)}T00:00:00UTC"))
    return bloques


def extraer_por_anyos():
    df_estaciones = cargar_estaciones_ordenadas(ordenar = True)
    anyos = list(range(2016, hoy.year + 1))
    bloques_fechas = construir_bloques_por_anyo(anyos)
    return extraer_datos_aemet(df_estaciones, bloques_fechas, etiqueta = f"{anyos[0]}_a_{anyos[-1]}")


def construir_url_meta(codigo, inicio, fin):
    return URL_DATOS_DIARIOS.format(inicio = inicio, fin = fin, codigo = codigo)


def obtener_registros_desde_respuesta(datos, codigo):
    try:
        registros = datos.json()
        if isinstance(registros, str):
            registros = json.loads(registros)
        return registros
    except Exception:
        logger.exception(f"  Error al decodificar JSON para estacion={codigo}")
        return None


def es_valor_tabular_valido(valor):
    return not isinstance(valor, (dict, list, tuple, set))


def validar_registro_para_dataframe(registro, codigo, contexto):
    if not isinstance(registro, dict):
        logger.warning(f"Registro descartado antes del DataFrame para estacion={codigo}: no es un dict")
        return False

    claves_invalidas = [
        clave for clave, valor in registro.items()
        if not isinstance(clave, str) or not es_valor_tabular_valido(valor)
    ]
    if claves_invalidas:
        logger.warning(
            f"Registro descartado antes del DataFrame para {contexto}: claves invalidas={claves_invalidas}"
        )
        return False

    return True


def filtrar_registros_validos_para_dataframe(registros, codigo, contexto):
    return [
        registro for registro in registros
        if validar_registro_para_dataframe(registro, codigo, contexto)
    ]


def enriquecer_registros(registros, codigo, nombre, id_descarga):
    filas = []
    for registro in registros:
        if not isinstance(registro, dict):
            logger.warning(f"  Registro no es dict: {registro[:50]}...")
            continue
        registro.update({
            "indicativo": codigo,
            "nombre_estacion": nombre,
            "timestamp_extraccion": datetime.now(timezone.utc).isoformat(),
            "id_descarga": id_descarga
        })
        filas.append(registro)
    return filas


def procesar_bloque_estacion(codigo, nombre, inicio, fin, id_descarga, etiqueta):
    fecha_inicio, fecha_fin, archivo_tmp, archivo_csv = construir_rutas_bloque(codigo, inicio, fin)
    contexto = f"estacion={codigo}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}"

    if not preparar_archivos_bloque(archivo_tmp, archivo_csv):
        return archivo_csv

    meta = solicitar_datos_aemet(construir_url_meta(codigo, inicio, fin), parametros = {"api_key": API_KEY})
    if not meta:
        logger.error(f"No se pudo obtener la metainformacion de datos para {contexto}")
        return None

    url_datos = obtener_url_datos(meta)
    if not url_datos:
        logger.warning(f"No hay URL de datos para {contexto}")
        return None

    datos = solicitar_datos_aemet(url_datos)
    if not datos:
        logger.error(f"No se pudieron descargar los datos para {contexto}")
        return None

    registros = obtener_registros_desde_respuesta(datos, codigo)
    if registros is None:
        logger.error(f"No se pudieron decodificar los datos JSON para {contexto}")
        return None

    filas = enriquecer_registros(registros, codigo, nombre, id_descarga)
    if not filas:
        logger.warning(f"Sin datos validos para {contexto}")
        return None

    filas_validas = filtrar_registros_validos_para_dataframe(filas, codigo, contexto)
    if not filas_validas:
        logger.warning(f"Todos los registros quedaron descartados antes de crear el DataFrame para {contexto}")
        eliminar_archivo_temporal(archivo_tmp)
        return None

    df_bloque = pd.DataFrame(filas_validas)
    if df_bloque.empty:
        logger.warning(f"Ningun dato valido en etiqueta={etiqueta} para {contexto}. No guardo CSV.")
        eliminar_archivo_temporal(archivo_tmp)
        return None

    guardar_bloque_csv(df_bloque, archivo_tmp, archivo_csv)
    return archivo_csv


def extraer_datos_aemet(df_estaciones, bloques, etiqueta = "multi"):
    id_descarga = str(uuid.uuid4())
    archivos_generados = []

    for _, fila in df_estaciones.iterrows():
        codigo = fila["indicativo"]
        nombre = fila.get("nombre", "")

        for inicio, fin in bloques:
            archivo_generado = procesar_bloque_estacion(codigo, nombre, inicio, fin, id_descarga, etiqueta)
            if archivo_generado:
                archivos_generados.append(archivo_generado)
    return archivos_generados


if __name__ == "__main__":
    configurar_logging()
    extraer_por_anyos()
