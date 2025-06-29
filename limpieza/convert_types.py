import pandas as pd
import logging

def convert_types(df, numeric_cols=None):
    """
    Convierte las columnas en tipos de datos apropiados y selecciona columnas requeridas.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
        numeric_cols (list, optional): Lista de columnas numéricas. Defaultea a lista predefineda.
    
    Returns:
        pd.DataFrame: DataFrame with converted types and expected columns.
    """
    expected_columns = [
        "id_descarga", "indicativo", "nombre", "provincia", "altitud", "fecha",
        "tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia",
        "timestamp_extraccion"
    ]
    if numeric_cols is None:
        numeric_cols = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia", "altitud"]
    
    missing_cols = [col for col in numeric_cols if col not in df.columns]
    if missing_cols:
        logging.warning(f"Columnas faltantes: {missing_cols}")
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    if "timestamp_extraccion" in df.columns:
        df["timestamp_extraccion"] = pd.to_datetime(df["timestamp_extraccion"], errors="coerce")
    
    existing_columns = [col for col in expected_columns if col in df.columns]
    return df[existing_columns]