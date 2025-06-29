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
    
    active_mask = (df['fecha'] >= df['start_date']) & (df['fecha'] <= df['end_date'])
    remaining_missing = df[active_mask][numeric_cols].isna().any(axis=1)
    if remaining_missing.any():
        logging.info(f"Aplicando imputación KNN a {remaining_missing.sum()} filas...")
        df_knn = df[features].copy()
        
        for col in ['latitud_dd', 'longitud_dd', 'altitud', 'month', 'day_of_year', 'sin_day', 'cos_day']:
            df_knn[col] = df_knn[col].fillna(df_knn[col].median())
        
        scaler = StandardScaler()
        df_knn_scaled = scaler.fit_transform(df_knn)
        df_knn_scaled = pd.DataFrame(df_knn_scaled, columns=df_knn.columns)
        
        imputer = KNNImputer(n_neighbors=5, weights='distance')
        imputed_values = imputer.fit_transform(df_knn_scaled)
        imputed_numeric = scaler.inverse_transform(imputed_values)[:, [features.index(col) for col in numeric_cols]]
        
        df.loc[active_mask & remaining_missing, numeric_cols] = imputed_numeric[remaining_missing[active_mask].to_numpy()]
    
    columns_to_drop = ["month", "day_of_year", 'sin_day', 'cos_day', "start_date", "end_date", "latitud_dd", "longitud_dd", "cluster"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    return df