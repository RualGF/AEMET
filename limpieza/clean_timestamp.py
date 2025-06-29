import logging

def clean_timestamps(df):
    """
    Limpiar filas sin 'fecha', 'timestamp_extraccion','indicativo' en datos AEMET.

    Args:
        df (pd.DataFrame): Input DataFrame de AEMET conteniendo 'fecha' y 'time_stamp_extraccion'.

    Returns:
        pd.DataFrame: DataFrame sin filas NaN en 'fecha', 'indicativo', 'time_stamp_extraccion'

    """
    
    # Validate 'fecha' 'timestamp_extraccion' 'indicativo'
    columns_to_check = ['fecha', 'timestamp_extraccion', 'indicativo']
    
    if df[columns_to_check].isna().any().any():
        nan_counts = df[columns_to_check].isna().sum()
        logging.warning(f"Valores NaN en estas columnas: {nan_counts[nan_counts > 0].to_dict()}. Retiro de estas filas.")
        df = df.dropna(subset=columns_to_check)   
    return df