import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import os
import joblib
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

from keras import Input
from keras.models import Sequential
from keras.layers import GRU, Dense
from keras.callbacks import EarlyStopping

from sqlalchemy import select
from src.extraer_datos import tabla_dm
from src.conectar import conexion_a_bd

pio.renderers.default = "browser"

# === CONFIGURACIÓN ===
TARGET_COL = "tmed"
WINDOW_SIZE = 30
LOSS_FUNCTION = "mae"
EPOCHS = 50
BATCH_SIZE = 64
motor = conexion_a_bd()
RUTA_CSV = "data/estaciones.csv"
OUTPUT_DIR = "modelos_cluster"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === FUNCIONES AUXILIARES ===


# def create_sequences(data, target_column, window_size):
#     X, y = [], []
#     for i in range(len(data) - window_size):
#         sequence = data.iloc[i : i + window_size].drop(columns=target_column).values
#         label = data.iloc[i + window_size][target_column]
#         X.append(sequence)
#         y.append(label)
#     return np.array(X), np.array(y)
def create_sequences(data, target_column, window_size):
   # Extraer los datos como arrays de numpy para máxima eficiencia
    feature_data = data.drop(columns=target_column).values
    target_data = data[target_column].values

    n_sequences = len(data) - window_size
    n_features = feature_data.shape[1]

    # Pre-generar los índices para todas las secuencias de una vez
    # Esto evita el bucle de Python y es mucho más rápido
    shape = (n_sequences, window_size, n_features)
    strides = (feature_data.strides[0], feature_data.strides[0], feature_data.strides[1])
    X = np.lib.stride_tricks.as_strided(feature_data, shape=shape, strides=strides)

    # Las etiquetas son simplemente los valores que siguen a cada ventana
    y = target_data[window_size:]

    return X, y

def predict_one_step(model, input_window):
    input_window = np.expand_dims(input_window, axis=0)
    prediction = model.predict(input_window, verbose=1)
    return prediction[0][0]


def inverse_transform_single_value(value, scaler, column_index):
    dummy = np.zeros((1, scaler.n_features_in_))
    dummy[0, column_index] = value
    inv = scaler.inverse_transform(dummy)
    return inv[0, column_index]


# === 1. CARGAR DATOS ===

print("Cargando estaciones...")
df_estaciones = pd.read_csv(RUTA_CSV)
# print("Cargando datos meteorológicos...")
# df = pd.read_sql_table(tabla_dm.name, motor)

# === 2. OBTENER CLÚSTERES ===
clusters = df_estaciones["cluster"].unique()
resultados = []

for clust in clusters:
    print(f"\n--- Procesando clúster {clust} ---")

    indicativos = df_estaciones[df_estaciones["cluster"] == clust][
        "indicativo"
    ].tolist()
    indicativos = df_estaciones.loc[df_estaciones["cluster"] == clust, "indicativo"].tolist()

    if not indicativos:
        print(f"⚠️  Clúster {clust} no tiene estaciones. Saltando.")
        continue
    else:
        # --- MEJORA: Usar SQLAlchemy para filtrar en la base de datos ---
        print(f"Consultando datos para {len(indicativos)} estaciones del clúster {clust}...")
        stmt = select(tabla_dm).where(tabla_dm.c.codigo_indicativo.in_(indicativos))
    
    # pd.read_sql puede tomar directamente la sentencia de SQLAlchemy
    df_clust = pd.read_sql(stmt, motor)
    df_clust = df_clust.drop(
        columns=["id_descarga", "timestamp_extraccion", "codigo_indicativo", "codigo_prov"], errors="ignore"
    )
    
    df_numeric = df_clust.select_dtypes(include=[np.number])

    if len(df_numeric) <= WINDOW_SIZE:
        print(f"⚠️  Clúster {clust} ignorado por insuficientes datos.")
        continue

    if TARGET_COL not in df_numeric.columns:
        print(f"⚠️  Clúster {clust} no tiene '{TARGET_COL}' válido.")
        continue

    # Normalizar
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df_numeric)
    scaled_df = pd.DataFrame(scaled_data, columns=df_numeric.columns)

    # Crear secuencias
    X, y = create_sequences(scaled_df, TARGET_COL, WINDOW_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, shuffle=False, random_state=42
    )

    # Modelo GRU
    model = Sequential(
        [Input(shape=(X_train.shape[1], X_train.shape[2])), GRU(64), Dense(1)])
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1))
        

    model.compile(
        optimizer="adam",
        loss=LOSS_FUNCTION,
    )

    parada = EarlyStopping(
        monitor='val_loss', patience=10, restore_best_weights=True, verbose=1
    )

    print(f"Entrenando modelo para clúster {clust}...")
    history = model.fit(
        X_train,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_val, y_val),
        callbacks=[parada],
        verbose="1"
    )

    # Predicción ONE-STEP
    last_window = X_val[-1]
    next_value_norm = predict_one_step(model, last_window)
    target_index = df_numeric.columns.get_loc(TARGET_COL)
    next_value_real = inverse_transform_single_value(
        next_value_norm, scaler, target_index
    )

    resultados.append((clust, next_value_real))

    # Guardar modelo y scaler
    model.save(f"{OUTPUT_DIR}/modelo_cluster_{clust}.keras")
    joblib.dump(scaler, f"{OUTPUT_DIR}/scaler_cluster_{clust}.pkl")

    print(f"✅ Clúster {clust} → Predicción tmed: {next_value_real:.1f}°C")

# === 3. VISUALIZACIÓN DE RESULTADOS ===

if resultados:
    df_resultados = pd.DataFrame(resultados, columns=["cluster", "tmed_predicho"]).sort_values("cluster")
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_resultados["cluster"].astype(str),
            y=df_resultados["tmed_predicho"],
            name="Predicción tmed",
            marker_color="orange",
        )
    )

    fig.update_layout(
        title="📊 Predicción ONE-STEP de tmed por clúster",
        xaxis_title="Clúster",
        yaxis_title="tmed (°C)",
        template="plotly_dark",
    )

    fig.show()
else:
    print("No se generaron predicciones válidas.")
