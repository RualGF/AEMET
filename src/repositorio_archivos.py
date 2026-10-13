import logging
import os
import time

CARPETA_DATA = "data"

logger = logging.getLogger(__name__)


def construir_rutas_bloque(codigo, inicio, fin, carpeta = CARPETA_DATA):
    fecha_inicio = inicio[:10]
    fecha_fin = fin[:10]
    archivo_tmp = os.path.join(carpeta, f"{codigo}_{fecha_inicio}_a_{fecha_fin}.tmp")
    archivo_csv = os.path.join(carpeta, f"{codigo}_{fecha_inicio}_a_{fecha_fin}.csv")
    return fecha_inicio, fecha_fin, archivo_tmp, archivo_csv


def preparar_archivos_bloque(archivo_tmp, archivo_csv):
    if os.path.exists(archivo_csv):
        logger.info(f"Ya existe: {archivo_csv}, usando el archivo existente.")
        return False

    if os.path.exists(archivo_tmp):
        logger.warning(f"TMP antiguo detectado en {archivo_tmp}, lo elimino antes de continuar.")
        os.remove(archivo_tmp)

    return True


def eliminar_archivo_temporal(archivo_tmp):
    if os.path.exists(archivo_tmp):
        os.remove(archivo_tmp)


def guardar_bloque_csv(df_bloque, archivo_tmp, archivo_csv):
    df_bloque.to_csv(archivo_tmp, index = False)
    os.rename(archivo_tmp, archivo_csv)
    logger.info(f"Bloque guardado correctamente en {archivo_csv}")
    time.sleep(2)
