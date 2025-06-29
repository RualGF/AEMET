import logging
import pandas as pd

def order(df):
    """
    Reordenar columnas.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame con las columnas seleccionas
    
    Raises:
        ValueError: Si columnas requeridas están faltantes
    """
    orden_columnas = [
        "id_descarga", "fecha", "indicativo", "nombre", "provincia",
        "altitud", "tmed", "tmin", "tmax", "prec", "velmedia",
        "racha", "hrMedia", "timestamp_extraccion"]

    missing_cols = [col for col in orden_columnas if col not in df.columns]
    if missing_cols:
        logging.warning(f"Columnas faltantes: {missing_cols}")
    
    valores_insertar = df[orden_columnas]
    return valores_insertar