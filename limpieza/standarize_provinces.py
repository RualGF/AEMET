import json

def standardize_provinces(df, mapping_path="data/mapa_provincia.json"):
    """
    Estandarizar las provincias utilizando un archivo de mapeo JSON.
    
    Args:
        df (pd.DataFrame): DataFrame con columna 'provincia'.
        mapping_path (str): Path al JSON de mapeo.
    
    Returns:
        pd.DataFrame: DataFrame con columna 'provincia' estandarizado.
    
    Raises:
        ValueError: Si columna'provincia' está faltante o  JSON es inválido.
        FileNotFoundError: If mapping file is not found.
    """
    if "provincia" not in df.columns:
        raise ValueError("Columna 'provincia' faltante")
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapa_provincias = json.load(f)
        df["provincia"] = df["provincia"].map(mapa_provincias).fillna(df["provincia"])
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Archivo de mapeo no encontrado: {mapping_path}")
    except json.JSONDecodeError:
        raise ValueError(f"JSON inválido en el archivo: {mapping_path}")