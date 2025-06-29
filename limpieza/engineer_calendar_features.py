import numpy as np
import pandas as pd

def engineer_calendar_features(df):
    """
    Agregar atributos estacionales basados en la columna 'fecha'
    
    Args:
        df (pd.DataFrame): Input DataFrame con columnas 'fecha' e 'indicativo'.
    
    Returns:
        pd.DataFrame: DataFrame con atributos de estacionalidad agregados.
    
    """
    
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.sort_values(["indicativo", "fecha"]).reset_index(drop=True)
    df['month'] = df['fecha'].dt.month
    df['day_of_year'] = df['fecha'].dt.dayofyear
    df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    
    df[['month', 'day_of_year', 'sin_day', 'cos_day']] = df[['month', 'day_of_year', 'sin_day', 'cos_day']].fillna(0)
    return df