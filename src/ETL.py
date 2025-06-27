import os
from hacer_peticion import extraer_ultimos_tres_dias
from limpieza.clean_timestamp import clean_timestamps
from limpieza.standarize_provinces import standardize_provinces
from limpieza.convert_types import convert_types
from limpieza.engineer_calendar_features import engineer_calendar_features
from limpieza.filter_physical_outliers import filter_physical_outliers
from limpieza.interpolate_missing import interpolate_missing
from limpieza.add_info import add_info
from limpieza.knn_impute import knn_impute
from limpieza.order import order
#from poblar import poblar
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_data():
    """Extract data using provided functions."""
    try:
        logger.info("Starting extraction process")
        extracted_df = extraer_ultimos_tres_dias()
        extract_path = "data/extract.pkl"
        #os.makedirs("data", exist_ok=True)
        extracted_df.to_pickle(path=extract_path)
        logger.info(f"Extracted data saved to {extract_path} ")
        return extracted_df.copy()
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        raise

def transform_data(df):
    """Transform the extracted data through multiple steps."""
    try:
        logger.info("Starting transformation process")
        df = clean_timestamps(df)
        logger.info("Timestamps cleaned")
        
        df = standardize_provinces(df, mapping_path="data/mapa_provincia.json")
        logger.info("Provinces standardized")
        
        df = convert_types(df, numeric_cols=None)
        logger.info("Data types converted")
        
        df = engineer_calendar_features(df)
        logger.info("Calendar features engineered")
        
        df = filter_physical_outliers(df)
        logger.info("Physical outliers filtered")
        
        df = interpolate_missing(df, numeric_cols=None)
        logger.info("Missing values interpolated")
        
        df = add_info(df, estaciones_path="data/estaciones.csv")
        logger.info("Additional info added")
        
        df = knn_impute(df, numeric_cols=None)
        logger.info("KNN imputation completed")
        
        df = order(df)
        logger.info("Data ordered")
        
        return df
    except Exception as e:
        logger.error(f"Error during transformation: {e}")
        raise

#función poblar aqui

def run_etl(save_path="data/output.pkl"):
    """Run the complete ETL pipeline and save to pickle."""
    try:
        # Extract
        df = extract_data()

        
        # Transform
        df_transformed = transform_data(df)
        
        # Load
        #poblar(df_transformed)

        # Save to pickle
        df_transformed.to_pickle(save_path)
        logger.info(f"DataFrame saved to {save_path}")
        
        logger.info("ETL pipeline completed successfully")
        return df_transformed
    except Exception as e:
        logger.error(f"Error in ETL pipeline: {e}")
        raise

if __name__ == "__main__":
    run_etl()