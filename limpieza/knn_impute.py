import pandas as pd
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer

def knn_impute(df, numeric_cols=None):
    """
    Imputar valores NaN remanentes de la interpolacion, utilizando KNN dentro del periodo de activida de cada estación
    
    Args:
        df (pd.DataFrame): Input DataFrame.
        numeric_cols (list, optional): List of numeric columns to impute.
    
    Returns:
        pd.DataFrame: DataFrame with imputed values.
    
    Raises:
        ValueError: Si faltan las columnas requeridas.
    """
    if numeric_cols is None:
        numeric_cols = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia"]
    
    features = ['tmin', 'tmax', 'tmed', "prec", "velmedia", "racha", "hrMedia",
                'latitud_dd', 'longitud_dd', 'altitud',
                'month', 'day_of_year', 'sin_day', 'cos_day', 'cluster']
    required_cols = features + ['indicativo', 'fecha', 'start_date', 'end_date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan las columnas requeridas: {missing_cols}")
    
    # Máscara para identificar las filas dentro del período de actividad de cada estación.
    # Esta máscara tiene la misma longitud que el DataFrame original.
    active_mask = (df['fecha'] >= df['start_date']) & (df['fecha'] <= df['end_date'])
    
    # Máscara para identificar las filas que son activas Y tienen valores NaN.
    # Esta también tiene la misma longitud que el DataFrame original, solucionando el IndexError.
    rows_to_impute_mask = active_mask & df[numeric_cols].isna().any(axis=1)

    if rows_to_impute_mask.any():
        logging.info(f"Aplicando imputación KNN a {rows_to_impute_mask.sum()} filas...")
        df_knn = df[features].copy()
        
        # Rellenar NaNs en columnas no objetivo (geo, fecha) para que el scaler funcione
        for col in ['latitud_dd', 'longitud_dd', 'altitud', 'month', 'day_of_year', 'sin_day', 'cos_day', 'cluster']:
            df_knn[col] = df_knn[col].fillna(df_knn[col].median())
        
        scaler = StandardScaler()
        df_knn_scaled = scaler.fit_transform(df_knn)
        
        imputer = KNNImputer(n_neighbors=5, weights='distance')
        imputed_values = imputer.fit_transform(df_knn_scaled)
        
        # Crear un DataFrame completo con los valores imputados y desescalados
        imputed_full_df = pd.DataFrame(scaler.inverse_transform(imputed_values), columns=features, index=df.index)
        
        # Actualizar el DataFrame original solo en las filas y columnas necesarias
        df.loc[rows_to_impute_mask, numeric_cols] = imputed_full_df.loc[rows_to_impute_mask, numeric_cols]
    
    columns_to_drop = ["month", "day_of_year", 'sin_day', 'cos_day', "start_date", "end_date", "latitud_dd", "longitud_dd", "cluster"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    return df