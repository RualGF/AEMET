import logging
import pandas as pd

def add_info(df, estaciones_path="data/estaciones.csv"):
    """
    Agregar atributos necesarios para imputar a partir de estaciones.csv: latitude_dd, longitude_dd, start_date, end_date y cluster.
    
    Args:
        df (pd.DataFrame): Input DataFrame con columna 'indicativo'.
        estaciones_path (str): Path al CSV de estaciones.
    
    Returns:
        pd.DataFrame: DataFrame con el agregado de 'latitud_dd', 'longitud_dd', 'start_date', 'end_date', 'cluster' columns.
    
    Raises:
        Archivo estaciones.csv no encontrado. Estaciones sin coordenadas o sin cluster.
    """
    try:
        estaciones = pd.read_csv(estaciones_path)
        cols = ['indicativo', 'latitud_dd', 'longitud_dd', 'cluster']
        if 'start_date' in estaciones.columns and 'end_date' in estaciones.columns:
            cols.extend(['start_date', 'end_date'])
            estaciones['start_date'] = pd.to_datetime(estaciones['start_date'], errors='coerce')
            estaciones['end_date'] = pd.to_datetime(estaciones['end_date'], errors='coerce')
        coords = estaciones[cols]
        df = df.merge(coords, on='indicativo', how='left')
        unmatched_coords = df[df['latitud_dd'].isna()]['indicativo'].unique()
        unmatched_cluster = df[df['cluster'].isna()]['indicativo'].unique()
        if len(unmatched_coords) > 0:
            logging.warning(f"Estaciones sin coordenadas: {unmatched_coords}")
            raise ValueError(f"Estaciones sin coordenadas en estaciones.csv: {unmatched_coords}")
        if len(unmatched_cluster) > 0:
            logging.warning(f"Estaciones sin cluster: {unmatched_cluster}")
            raise ValueError(f"Estaciones sin cluster en estaciones.csv: {unmatched_cluster}")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Archivo de estaciones no encontrado: {estaciones_path}")