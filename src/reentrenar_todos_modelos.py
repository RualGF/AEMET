import os
import sys
import pickle
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from keras import Input
from keras.models import Sequential
from keras.layers import GRU, SimpleRNN, Dense
from keras.callbacks import EarlyStopping
from prophet import Prophet


def cargar_datos_procesados() -> pd.DataFrame:
    pkl_path = BASE_DIR / "data" / "temperaturas_limpias_10_años_final.pkl"
    logger.info(f"Cargando dataset para entrenamiento desde {pkl_path}...")
    df = pd.read_pickle(pkl_path)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(by=["cluster", "fecha"]).reset_index(drop=True)
    return df


def crear_secuencias(data: pd.DataFrame, target_col: str, window_size: int):
    feature_data = data.drop(columns=target_col).values
    target_data = data[target_col].values

    n_sequences = len(data) - window_size
    n_features = feature_data.shape[1]

    shape = (n_sequences, window_size, n_features)
    strides = (feature_data.strides[0], feature_data.strides[0], feature_data.strides[1])
    X = np.lib.stride_tricks.as_strided(feature_data, shape=shape, strides=strides)
    y = target_data[window_size:]
    return X, y


def entrenar_modelos_gru(df_total: pd.DataFrame, clusters: list[int]):
    """
    Entrena modelos GRU multivariantes (30 días de ventana, 6 features de entrada)
    para cada clúster climático.
    """
    logger.info("==========================================")
    logger.info("Iniciando entrenamiento de modelos GRU...")
    logger.info("==========================================")
    
    out_dir = BASE_DIR / "modelos" / "modelos_dl"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cols_escalar = ['altitud', 'tmed', 'tmin', 'tmax', 'prec', 'racha', 'hrMedia']
    target_col = 'tmed'
    window_size = 30

    for cl in clusters:
        logger.info(f"\n--- [GRU] Entrenando Clúster {cl} ---")
        df_cl = df_total[df_total["cluster"] == cl].copy()
        
        # Agrupar por fecha para obtener la serie temporal representativa del clúster
        df_serie = df_cl.groupby("fecha")[cols_escalar].mean().reset_index()
        df_serie = df_serie.sort_values("fecha").reset_index(drop=True)
        
        if len(df_serie) <= window_size + 10:
            logger.warning(f"Clúster {cl} con datos insuficientes ({len(df_serie)} filas). Saltando.")
            continue

        # Escalador (7 variables)
        scaler = MinMaxScaler()
        scaled_values = scaler.fit_transform(df_serie[cols_escalar])
        df_scaled = pd.DataFrame(scaled_values, columns=cols_escalar)

        # Secuencias: X (window_size, 6 features), y (tmed)
        X, y = crear_secuencias(df_scaled, target_col, window_size)

        n_train = int(len(X) * 0.85)
        X_train, X_val = X[:n_train], X[n_train:]
        y_train, y_val = y[:n_train], y[n_train:]

        # Arquitectura GRU compatible con 3_Modelos_DL.py
        model = Sequential([
            Input(shape=(X_train.shape[1], X_train.shape[2])),
            GRU(64, return_sequences=False),
            Dense(32, activation="relu"),
            Dense(1)
        ])
        model.compile(optimizer="adam", loss="mae")

        early_stop = EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True, verbose=0)
        
        model.fit(
            X_train, y_train,
            epochs=40,
            batch_size=32,
            validation_data=(X_val, y_val),
            callbacks=[early_stop],
            verbose=0
        )

        # Evaluar
        y_pred = model.predict(X_val, verbose=0).flatten()
        mae = mean_absolute_error(y_val, y_pred)
        logger.info(f"Clúster {cl} GRU -> Val MAE (escalado): {mae:.4f}")

        # Guardar modelo y scaler
        model_path = out_dir / f"GRU_cluster_{cl}.keras"
        scaler_path = out_dir / f"GRU_scaler_cluster_{cl}.pkl"
        model.save(str(model_path))
        joblib.dump(scaler, str(scaler_path))
        logger.info(f"Guardado: {model_path.name} y {scaler_path.name}")


def entrenar_modelos_nn(df_total: pd.DataFrame, clusters: list[int]):
    """
    Entrena modelos NN densos univariantes (7 días de ventana de tmed)
    para cada clúster climático.
    """
    logger.info("==========================================")
    logger.info("Iniciando entrenamiento de modelos NN...")
    logger.info("==========================================")
    
    out_dir = BASE_DIR / "modelos" / "modelos_dl"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    window_size = 7

    for cl in clusters:
        logger.info(f"\n--- [NN] Entrenando Clúster {cl} ---")
        df_cl = df_total[df_total["cluster"] == cl].copy()
        
        df_serie = df_cl.groupby("fecha")[["tmed"]].mean().reset_index()
        df_serie = df_serie.sort_values("fecha").reset_index(drop=True)

        if len(df_serie) <= window_size + 10:
            logger.warning(f"Clúster {cl} con datos insuficientes ({len(df_serie)} filas). Saltando.")
            continue

        scaler = MinMaxScaler()
        scaled_tmed = scaler.fit_transform(df_serie[["tmed"]])

        X_list, y_list = [], []
        for i in range(len(scaled_tmed) - window_size):
            X_list.append(scaled_tmed[i : i + window_size])
            y_list.append(scaled_tmed[i + window_size, 0])

        X = np.array(X_list)  # (N, 7, 1)
        y = np.array(y_list)

        n_train = int(len(X) * 0.85)
        X_train, X_val = X[:n_train], X[n_train:]
        y_train, y_val = y[:n_train], y[n_train:]

        model = Sequential([
            Input(shape=(window_size, 1)),
            SimpleRNN(50),
            Dense(1)
        ])
        model.compile(optimizer="adam", loss="mae")

        early_stop = EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True, verbose=0)

        model.fit(
            X_train, y_train,
            epochs=40,
            batch_size=32,
            validation_data=(X_val, y_val),
            callbacks=[early_stop],
            verbose=0
        )

        y_pred = model.predict(X_val, verbose=0).flatten()
        mae = mean_absolute_error(y_val, y_pred)
        logger.info(f"Clúster {cl} NN -> Val MAE (escalado): {mae:.4f}")

        model_path = out_dir / f"NN_cluster_{cl}.keras"
        scaler_path = out_dir / f"NN_scaler_cluster_{cl}.pkl"
        model.save(str(model_path))
        joblib.dump(scaler, str(scaler_path))
        logger.info(f"Guardado: {model_path.name} y {scaler_path.name}")


def entrenar_modelos_prophet(df_total: pd.DataFrame, clusters: list[int]):
    """
    Entrena y guarda los modelos de Facebook Prophet por clúster climático.
    """
    logger.info("==========================================")
    logger.info("Iniciando entrenamiento de modelos Prophet...")
    logger.info("==========================================")
    
    out_dir = BASE_DIR / "modelos" / "prophet"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cl in clusters:
        logger.info(f"\n--- [Prophet] Entrenando Clúster {cl} ---")
        df_cl = df_total[df_total["cluster"] == cl].copy()
        
        df_serie = df_cl.groupby("fecha")[["tmed"]].mean().reset_index()
        df_serie = df_serie.rename(columns={"fecha": "ds", "tmed": "y"})
        df_serie = df_serie.sort_values("ds").reset_index(drop=True)

        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95
        )
        m.fit(df_serie)

        model_path = out_dir / f"cluster_model_{cl}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(m, f)
        logger.info(f"Guardado modelo Prophet: {model_path.name}")


def main():
    df = cargar_datos_procesados()
    clusters = sorted([c for c in df["cluster"].unique() if c >= 0])
    logger.info(f"Clústeres a entrenar: {clusters}")

    # 1. GRU
    entrenar_modelos_gru(df, clusters)

    # 2. NN
    entrenar_modelos_nn(df, clusters)

    # 3. Prophet
    entrenar_modelos_prophet(df, clusters)

    logger.info("\n🎉 ¡Todos los modelos (GRU, NN y Prophet) han sido reentrenados y guardados con éxito!")


if __name__ == "__main__":
    main()
