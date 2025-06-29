import os
import sys

# Añadir el directorio raíz del proyecto al path de Python
# para que pueda encontrar el módulo 'limpieza'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.hacer_peticion import extraer_ultimos_tres_dias, extraer_por_años
from limpieza.clean_timestamp import clean_timestamps
from limpieza.standarize_provinces import standardize_provinces
from limpieza.convert_types import convert_types
from limpieza.engineer_calendar_features import engineer_calendar_features
from limpieza.filter_physical_outliers import filter_physical_outliers
from limpieza.interpolate_missing import interpolate_missing
from limpieza.add_info import add_info
from limpieza.knn_impute import knn_impute
from limpieza.order import order
import pandas as pd
import logging

# Set up logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = [
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_data(modo: str = "actualizar"):
    """Extract data using provided functions."""
    try:
        logger.info(f"Starting extraction in '{modo}' mode")

        if modo == "actualizar":
            df = extraer_ultimos_tres_dias()
            extract_path = "data/extract.pkl"
            df.to_pickle(extract_path)
            logger.info(f"Recent data extracted and saved to {extract_path}")
            return df

        elif modo == "masivo":
            csv_paths = extraer_por_años()  # Devuelve lista de CSVs
            return csv_paths

        else:
            raise ValueError(f"Modo no válido: {modo}")

    except Exception as e:
        logger.error(f"Error during extraction ({modo}): {e}")
        raise
    
def transform_data(df):
    """Transform the extracted data through multiple steps."""
    try:
        logger.info("Starting transformation process")
        df = clean_timestamps(df)
        logger.info("Timestamps cleaned")
        
        df = standardize_provinces(df, mapping_path = "data/mapa_provincia.json")
        logger.info("Provinces standardized")
        
        df = convert_types(df, numeric_cols = None)
        logger.info("Data types converted")
        
        df = engineer_calendar_features(df)
        logger.info("Calendar features engineered")
        
        df = filter_physical_outliers(df)
        logger.info("Physical outliers filtered")
        
        df = interpolate_missing(df, numeric_cols = None)
        logger.info("Missing values interpolated")
        
        df = add_info(df, estaciones_path = "data/estaciones.csv")
        logger.info("Additional info added")
        
        df = knn_impute(df, numeric_cols = None)
        logger.info("KNN imputation completed")
        
        df = order(df)
        logger.info("Data ordered")
        
        return df
    except Exception as e:
        logger.error(f"Error during transformation: {e}")
        raise

#función poblar aqui

def run_etl(modo: str = "actualizar", save_path = "data/output.pkl"):
    """Run the complete ETL pipeline."""
    try:
        if modo == "actualizar":
            df = extract_data(modo="actualizar")
            df_transformed = transform_data(df)
            df_transformed.to_pickle(save_path)
            logger.info(f"DataFrame saved to {save_path}")
            logger.info("ETL pipeline (actualizar) completed successfully")
            return df_transformed

        elif modo == "masivo":
            lista_archivos_csv = extract_data(modo = "masivo")

            if not lista_archivos_csv:
                logger.warning("El modo masivo no encontró ni generó ningún archivo CSV para procesar.")
                return pd.DataFrame()

            lista_dfs_transformados = []

            total_archivos = len(lista_archivos_csv)
            for i, archivo_csv in enumerate(lista_archivos_csv):
                logger.info(f"Procesando archivo ({i+1}/{total_archivos}): {archivo_csv}")
                try:
                    bloque_df = pd.read_csv(archivo_csv)
                    if not bloque_df.empty:
                        df_bloque_transformado = transform_data(bloque_df)
                        lista_dfs_transformados.append(df_bloque_transformado)
                except Exception as e:
                    logger.error(f"No se pudo procesar el archivo {archivo_csv}: {e}")
                    continue
            if not lista_dfs_transformados:
                logger.error("No se pudo transformar ningún bloque de datos con éxito.")
                return pd.DataFrame()

            logger.info("Combinando todos los bloques de datos transformados...")
            df_final_transformado = pd.concat(lista_dfs_transformados, ignore_index = True)
            
            df_final_transformado.to_pickle(save_path)
            logger.info(f"DataFrame combinado guardado en {save_path}")
            logger.info("ETL pipeline (masivo) completado con éxito.")
            return df_final_transformado
        else:
            raise ValueError(f"Modo no válido: {modo}")

    except Exception as e:
        logger.error(f"Error in ETL pipeline ({modo}): {e}")
        raise

if __name__ == "__main__":
    run_etl()