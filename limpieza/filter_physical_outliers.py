import pandas as pd
import logging

def filter_physical_outliers(df):
    """
    Converitir a NaN valores implausibles de las columnas con datos meteorológicas.
    En caso de prec, redondear a dos decimales.
    
    Args:
        df (pd.DataFrame): Input DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame con los outliers convertidos a NaN.
    """
    required_cols = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia"]
    for col in required_cols:
        if col not in df.columns:
            continue
        before = df[col].isna().sum()
        if col == "tmin":
            df.loc[(df["tmin"] > 45) | (df["tmin"] < -25), "tmin"] = pd.NA
        elif col == "tmax":
            df.loc[(df["tmax"] > 50) | (df["tmax"] < -25), "tmax"] = pd.NA
        elif col == "tmed":
            df.loc[(df["tmed"] > 45) | (df["tmed"] < -20), "tmed"] = pd.NA
        elif col == "prec":
            df.loc[(df["prec"] > 300) | (df["prec"] < 0), "prec"] = pd.NA
        elif col == "velmedia":
            df.loc[(df["velmedia"] > 25) | (df["velmedia"] < 0), "velmedia"] = pd.NA
        elif col == "racha":
            df.loc[(df["racha"] > 50) | (df["racha"] < 0), "racha"] = pd.NA
        elif col == "hrMedia":
            df.loc[(df["hrMedia"] < 5) | (df["hrMedia"] > 100), "hrMedia"] = pd.NA
        after = df[col].isna().sum()
        logging.info(f"Outliers filtrados: {after - before} en {col}")
    
    if "tmin" in df.columns and "tmax" in df.columns:
        temp_invalida = df["tmin"] > df["tmax"]
        logging.info(f"Filtradas {temp_invalida.sum()} filas donde tmin > tmax")
        df.loc[temp_invalida, ["tmin", "tmax", "tmed"]] = pd.NA

    if 'prec' in df.columns:
        df['prec'] = df['prec'].round(2)
        logging.info("Redondear 'prec' a 2 decimales places y clip de valores negativos")
    
    if 'velmedia' in df.columns:
        df['velmedia'] = df['velmedia'].round(2)
        logging.info("Redondear 'velmedia' a 2 decimales places y clip de valores negativos")
    return df