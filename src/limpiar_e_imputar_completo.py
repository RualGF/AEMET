import logging
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def limpiar_e_imputar_dataset():
    pkl_path = BASE_DIR / "data" / "temperaturas_limpias_10_años_final.pkl"
    logger.info(f"Cargando dataset desde {pkl_path}...")
    df = pd.read_pickle(pkl_path)
    
    logger.info(f"Total registros cargados: {len(df):,}")
    cols_numericas = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "hrMedia"]
    
    nulos_inicio = df[cols_numericas].isna().sum()
    logger.info(f"Nulos antes de imputar:\n{nulos_inicio}")
    
    if nulos_inicio.sum() == 0:
        logger.info("El dataset no tiene valores nulos. No es necesario imputar.")
        return df

    # 1. Asegurar orden cronológico por estación
    df = df.sort_values(by=["indicativo", "fecha"]).reset_index(drop=True)

    # 2. Precipitación nula = 0
    df["prec"] = df["prec"].fillna(0.0)

    # 3. Interpolar linealmente por estación
    logger.info("Interpolando series temporales por estación...")
    def interpolar_estacion(grp):
        grp = grp.copy()
        for col in cols_numericas:
            if col == "prec":
                continue
            # Interpolar linealmente
            grp[col] = grp[col].interpolate(method="linear", limit_direction="both")
            # Si aún quedan nulos en la estación, usar la mediana de la estación
            mediana_estacion = grp[col].median()
            if pd.notna(mediana_estacion):
                grp[col] = grp[col].fillna(mediana_estacion)
        return grp

    df = df.groupby("indicativo", group_keys=False).apply(interpolar_estacion)

    # 4. Imputar nulos remanentes con la mediana del clúster climático
    nulos_despues_estacion = df[cols_numericas].isna().sum()
    if nulos_despues_estacion.sum() > 0:
        logger.info(f"Nulos remanentes tras interpolación por estación:\n{nulos_despues_estacion}")
        logger.info("Imputando restantes por mediana de clúster...")
        for col in cols_numericas:
            if df[col].isna().sum() > 0:
                # Mediana por cluster
                medianas_cluster = df.groupby("cluster")[col].transform("median")
                df[col] = df[col].fillna(medianas_cluster)
                # Fallback global si algún cluster estuviera totalmente vacío
                if df[col].isna().sum() > 0:
                    df[col] = df[col].fillna(df[col].median())

    # 5. Si tmin > tmax tras imputaciones, ajustar tmed
    temp_invalida = (df["tmin"] > df["tmax"]) & df["tmin"].notna() & df["tmax"].notna()
    if temp_invalida.sum() > 0:
        logger.info(f"Corrigiendo {temp_invalida.sum()} filas con tmin > tmax...")
        # Intercambiar
        df.loc[temp_invalida, ["tmin", "tmax"]] = df.loc[temp_invalida, ["tmax", "tmin"]].values

    # Asegurar coherencia tmed = (tmin + tmax) / 2 si tmed quedó fuera de rango
    tmed_fuera = (df["tmed"] < df["tmin"]) | (df["tmed"] > df["tmax"])
    if tmed_fuera.sum() > 0:
        df.loc[tmed_fuera, "tmed"] = ((df.loc[tmed_fuera, "tmin"] + df.loc[tmed_fuera, "tmax"]) / 2).round(1)

    nulos_final = df[cols_numericas].isna().sum()
    logger.info(f"Nulos finales tras ETL completo:\n{nulos_final}")

    # Guardar dataset limpio
    logger.info(f"Guardando dataset limpio en {pkl_path}...")
    df.to_pickle(pkl_path)
    logger.info("✅ Dataset limpio guardado con éxito.")

    return df


if __name__ == "__main__":
    limpiar_e_imputar_dataset()
