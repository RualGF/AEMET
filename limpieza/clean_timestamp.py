import logging
import pandas as pd

def clean_timestamps(df):
    """
    Limpiar filas sin 'fecha', 'timestamp_extraccion','indicativo' en datos AEMET.
    Eliminar duplicados para estas columnas

    Args:
        df (pd.DataFrame): Input DataFrame de AEMET conteniendo 'fecha' y 'time_stamp_extraccion'.

    Returns:
        pd.DataFrame: DataFrame sin duplicados y sin filas NaN en 'fecha', 'indicativo', 'time_stamp_extraccion'

    """
    
    # Validar 'fecha' 'timestamp_extraccion' 'indicativo'
    columns_to_check = ['fecha', 'timestamp_extraccion', 'indicativo']
    
    if df[columns_to_check].isna().any().any():
        nan_counts = df[columns_to_check].isna().sum()
        logging.warning(f"Valores NaN en estas columnas: {nan_counts[nan_counts > 0].to_dict()}. Retiro de estas filas.")
        df = df.dropna(subset=columns_to_check)

    # Eliminar duplicados basados en las columnas clave
    initial_shape = df.shape[0]
    df = df.drop_duplicates(subset=columns_to_check)
    final_shape = df.shape[0]
    num_duplicates = initial_shape - final_shape

    if num_duplicates > 0:
        logging.info(f"Se eliminaron {num_duplicates} filas duplicadas basadas en las columnas {columns_to_check}.")   
    return df