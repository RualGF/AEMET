import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib # Para cargar scalers

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Para tus modelos de Deep Learning, necesitarás tensorflow, keras, etc.
# Descomenta las líneas de importación y la lógica de carga de modelos/scalers
# cuando tengas tus modelos pre-entrenados.
try:
    # Usar la ruta de Keras integrada en TensorFlow es más estándar
    from keras.models import load_model as load_keras_model
    pass  # Placeholder para las importaciones reales de DL
except ImportError:
    st.error(
        "Por favor, asegúrate de tener las librerías necesarias para modelos DL (ej. TensorFlow, Keras)."
    )
    st.stop()

from src.extraer_datos import obtener_estaciones_para_prediccion, obtener_datos_historicos_estacion
from src.personalizacion import load_css

st.set_page_config(
    page_title="Modelos de Deep Learning",
    page_icon="🤖", # Icono para modelos DL
    layout="wide",
    initial_sidebar_state="expanded"

)    

load_css("src/estilos.css")
st.spinner("Cargando modelos de Deep Learning...")

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

@st.cache_data(ttl=60) # Cachear por 1 hora
def load_time_series_data(indicativo_estacion: str):
    """
    Carga los datos de series temporales para una estación específica desde la base de datos.
    El DataFrame debe tener una columna 'ds' (datetime) y 'y' (valor numérico).
    """
    # Usamos datos de ejemplo para la demostración. Reemplázalo con tu carga de datos.
    #st.write(f"Cargando datos históricos para la estación {indicativo_estacion}...")
    # Aquí se llama a la función real que extrae de la base de datos
    df = obtener_datos_historicos_estacion(indicativo_estacion, target_col='tmed') # Asumimos 'tmed' como objetivo

    if df.empty:
        st.warning(f"No se encontraron datos históricos para la estación {indicativo_estacion}. Usando datos de ejemplo.")
        # El fallback a datos de ejemplo debe ser manejado con cuidado o eliminado si no es compatible.
        # Por ahora, devolvemos un DF vacío para que el flujo principal lo maneje.
        return pd.DataFrame()

    # --- Limpieza de datos ---
    # Es crucial eliminar filas con valores nulos en las columnas que usará el modelo,
    # ya que el scaler y el modelo no pueden manejar NaNs.
    features_needed = ['altitud', 'tmed', 'tmin', 'tmax', 'prec', 'racha', 'hrMedia', 'fecha']
    
    missing_cols = [col for col in features_needed if col not in df.columns]
    if missing_cols:
        st.error(f"Faltan las siguientes columnas en los datos cargados: {', '.join(missing_cols)}. No se puede continuar.")
        return pd.DataFrame()

    rows_before = len(df)
    # Eliminar filas donde CUALQUIERA de las características necesarias (excluyendo la fecha) sea NaN
    df_cleaned = df.dropna(subset=[col for col in features_needed if col != 'fecha'])
    rows_after = len(df_cleaned)
    
    if rows_after < rows_before:
        st.warning(f"Se eliminaron {rows_before - rows_after} filas con datos faltantes. La última fecha con datos completos es {df_cleaned['fecha'].max().strftime('%Y-%m-%d')}.")

    return df_cleaned

@st.cache_resource
def load_model_and_metrics(model_name, cluster_id):
    """
    Carga un modelo pre-entrenado de Deep Learning y sus métricas.
        Aquí cargarías tus archivos .h5 (modelo Keras), .pkl (scaler), etc.
    
    NOTA: Los modelos DL se entrenan por clúster.
    Esta función necesitaría el `cluster_id` para cargar el modelo y scaler correctos.
    Por simplicidad en la demo, se asume que hay un modelo y scaler genérico por `model_name`.
    Deberías adaptar esto para cargar el modelo del clúster asociado a la estación seleccionada.
    """
    # Métricas de ejemplo. Cárgalas desde un archivo o defínelas aquí.
    metrics = {
        "GRU": {"RMSE": 6.5, "MAE": 4.9, "R²": 0.82}, # Estas métricas deberían ser reales del modelo cargado
        "NN": {"RMSE": 7.1, "MAE": 5.5, "R²": 0.79}, # Estas métricas deberían ser reales del modelo cargado
    }

    model = None
    scaler = None

    # --- Lógica para cargar modelos Keras y Scalers ---
    # Asegúrate de que tus modelos y scalers estén guardados en la ruta correcta.
    
    # Ejemplo de cómo cargar un modelo y scaler por cada clúster:
    model_path = f'modelos/modelos_dl/{model_name}_cluster_{cluster_id}.keras'
    scaler_path = f'modelos/modelos_dl/{model_name}_scaler_cluster_{cluster_id}.pkl'
    
    try:
        model = load_keras_model(model_path)
        scaler = joblib.load(scaler_path)
        st.success(f"Modelo {model_name} y scaler para cluster {cluster_id} cargados exitosamente.")
    except Exception as e:
        st.warning(f"No se pudo cargar el modelo {model_name} o su scaler de {model_path}/{scaler_path}. Error: {e}")
        st.warning("Las predicciones serán simuladas.")

        # Si la carga falla, los placeholders de abajo se usarán para la simulación
        # Placeholder para la demostración si no se cargan los modelos reales:

        model = f"Placeholder para el modelo pre-entrenado de {model_name}"
        scaler = "Placeholder para el scaler"  # Los modelos DL a menudo necesitan un scaler

    return model, scaler, pd.DataFrame([metrics[model_name]])


def make_dl_prediction(model, scaler, data, periods, mae, look_back=30, model_name=None):
    """
    Realiza predicciones con modelos de Deep Learning (GRU/NN) de forma recursiva.
    Ahora incluye predicciones "in-sample" para mostrar el ajuste del modelo.

    Args:
        model: El modelo Keras cargado.
        scaler: El scaler (MinMaxScaler) usado para normalizar los datos.
        data (pd.DataFrame): DataFrame con los datos históricos.
        periods (int): Número de pasos a predecir.
        mae (float): Error Absoluto Medio del modelo para construir el intervalo de confianza.
        look_back (int): Tamaño de la ventana de entrada para el modelo.
    
    Returns:
        pd.DataFrame: DataFrame con fechas y predicciones ('fecha', 'yhat', 'yhat_lower', 'yhat_upper').
    """
    # --- 1. Definición de Características y Setup ---
    # ¡CRÍTICO! El orden y el contenido de esta lista deben coincidir EXACTAMENTE
    # con las columnas del DataFrame que se usó para entrenar (hacer .fit()) el scaler.
    columna_objetivo = 'tmed'
    if model_name == "GRU":
        features_to_scale = ['altitud', 'tmed', 'tmin', 'tmax', 'prec', 'racha', 'hrMedia']
        features_for_model = [col for col in features_to_scale if col != columna_objetivo]
    else:
        features_to_scale = ['tmed']
        features_for_model = [columna_objetivo]
    
    
    # Las características para el modelo son todas menos el objetivo.
    

    # El índice de la columna objetivo dentro de la lista completa de características escaladas
    tmed_feature_index_in_scaler = features_to_scale.index(columna_objetivo)
    
    look_back = model.input_shape[1] # Obtiene la longitud de la secuencia de entrada del modelo
    
    # --- 2. Predicción In-Sample (sobre datos históricos para ver el ajuste) ---
    scaled_data_full = scaler.transform(data[features_to_scale])
    scaled_df_full = pd.DataFrame(scaled_data_full, columns=features_to_scale)

      # Crear secuencias para los datos históricos según el tipo de modelo (univariado vs multivariado)
    if model_name == "NN": # Caso univariado: la entrada es solo la columna objetivo
        X_hist_list = []
        for i in range(len(scaled_df_full) - look_back):
            # Reshape a (look_back, 1) para entrada univariada
            X_hist_list.append(scaled_df_full[columna_objetivo].iloc[i:i+look_back].values.reshape(look_back, 1))
        X_hist = np.array(X_hist_list)
    else: # GRU (Caso multivariado)
        X_hist, _ = create_sequences(scaled_df_full, columna_objetivo, look_back)
    yhat_hist_scaled = model.predict(X_hist, verbose=1)
    
    dummy_for_descale = np.zeros((len(yhat_hist_scaled), len(features_to_scale)))
    dummy_for_descale[:, tmed_feature_index_in_scaler] = yhat_hist_scaled.flatten()
    yhat_hist_original = scaler.inverse_transform(dummy_for_descale)[:, tmed_feature_index_in_scaler]

    hist_pred_dates = data['fecha'].iloc[look_back:].reset_index(drop=True)
    df_in_sample = pd.DataFrame({'fecha': hist_pred_dates, 'yhat': yhat_hist_original})

    # --- 3. Predicción Out-of-Sample (Pronóstico futuro recursivo) ---

    # Selecciona las últimas 'look_back' filas de TODAS las características necesarias
    if model_name == "NN": # Caso univariado: solo tmed es relevante para la última secuencia
        last_sequence_full_features = data[[columna_objetivo]].values[-look_back:]
    else: # GRU (Caso multivariado)
        last_sequence_full_features = data[features_to_scale].values[-look_back:]

    last_sequence_scaled_full = scaler.transform(last_sequence_full_features)  
    
    # Obtiene los índices de las columnas que el modelo necesita como entrada (ej. 7 características)

    model_input_indices_in_scaler = [features_to_scale.index(f) for f in features_for_model]    

    current_input_sequence = last_sequence_scaled_full[:, model_input_indices_in_scaler]

    current_input_sequence = np.expand_dims(current_input_sequence, axis=0)

    predicciones = []
    

    df_hist_copy = data.copy() 
    df_hist_copy['mes'] = df_hist_copy['fecha'].dt.month 
    
    # Las características para las que calcularemos promedios estacionales son
    # todas las del modelo, excepto la altitud (que es constante).
    avg_seasonal_features_cols = [f for f in features_for_model if f != 'altitud']
     # Calcula los promedios mensuales
    avg_seasonal_features = df_hist_copy.groupby('mes')[avg_seasonal_features_cols].mean()

   # --- DEPURACIÓN: IMPRIMIR PROMEDIOS ESTACIONALES ---
    # print("\n--- Promedios Estacionales (avg_seasonal_features): ---")
    # print(avg_seasonal_features)
    # print("-----------------------------------------------------")

    # Obtener la altitud del último registro histórico, ya que es constante para una estación
    last_known_altitud = df_hist_copy['altitud'].iloc[-1]

    # Generar las fechas futuras a partir de la última fecha conocida
    last_date = df_hist_copy['fecha'].max().normalize() # Normaliza para quitar la hora
    
    start_date_for_forecast = last_date + pd.Timedelta(days=1)
    fecha_prediccion = pd.date_range(start=start_date_for_forecast, periods=periods, freq='D')
    
    for i in range(periods):

        next_step_scaled_tmed = model.predict(current_input_sequence, verbose=0)

        dummy_row_scaled = np.copy(last_sequence_scaled_full[-1, :]).reshape(1, -1)  
        
        dummy_row_scaled[0, tmed_feature_index_in_scaler] = next_step_scaled_tmed[0, 0]
        

        next_step_original = scaler.inverse_transform(dummy_row_scaled)[0]
        # print(f"Desescalado: {next_step_original}")
        
        predicted_tmed = next_step_original[tmed_feature_index_in_scaler]
        predicciones.append(predicted_tmed)
        
        # --- ¡Punto de Depuración Adicional aquí! ---
        # if i < 5 or i >= periods - 5: # Para no imprimir demasiado, las 5 primeras y las 5 últimas
        #     print(f"Predicción paso {i+1}: Escala={next_step_scaled_tmed[0, 0]:.4f}, Original={predicted_tmed:.2f}")
        # if np.isnan(predicted_tmed) or np.isinf(predicted_tmed):
        #     print(f"¡ADVERTENCIA! Valor de predicción no válido en el paso {i+1}: {predicted_tmed}")
        # --- Fin de la depuración ---


        # --- Actualizar la secuencia de entrada para la siguiente predicción ---
        
        current_forecast_date = fecha_prediccion[i]

        next_features_original_for_input_dict = {}
        
        if model_name == "GRU": # Solo para modelos multivariados, estas características son entradas
            next_features_original_for_input_dict['altitud'] = last_known_altitud
            current_month = current_forecast_date.month
        
        # --- DEPURACIÓN: IMPRIMIR VALORES FUTUROS DE LAS ENTRADAS ---
        #current_step_features_info = {f: None for f in avg_seasonal_features_cols} # Para almacenar los valores que se usarán
        
             
            # Estas características estacionales solo son relevantes para GRU (multivariado)
            for feat in avg_seasonal_features_cols:
                if current_month in avg_seasonal_features.index:
                    value = avg_seasonal_features.loc[current_month, feat]
                    next_features_original_for_input_dict[feat] = value
                else:
                    value = df_hist_copy[feat].mean()
                    next_features_original_for_input_dict[feat] = value
            
            # Para GRU, next_features_original_for_input incluye todas las características exógenas
            next_features_original_for_input = np.array([next_features_original_for_input_dict[f] for f in features_for_model])
            
        else: # model_name == "NN" (Univariado)
            # Para NN, la única entrada es la tmed predicha del paso anterior.
            # No se usan otras características externas como entrada al modelo.
            next_features_original_for_input = np.array([predicted_tmed]) # Solo tmed como entrada
        
        dummy_row_original_for_scaler = np.zeros(len(features_to_scale)) 

        for j, feature_name in enumerate(features_for_model):
            idx_in_scaler = features_to_scale.index(feature_name)
            dummy_row_original_for_scaler[idx_in_scaler] = next_features_original_for_input[j]

        next_input_row_scaled_full = scaler.transform(dummy_row_original_for_scaler.reshape(1, -1))
        
        next_input_row_scaled_model = next_input_row_scaled_full[0, model_input_indices_in_scaler]   

        current_input_sequence = np.roll(current_input_sequence, -1, axis=1)
        current_input_sequence[0, -1, :] = next_input_row_scaled_model

 
    df_out_of_sample = pd.DataFrame({
        'fecha': fecha_prediccion,
        'yhat': predicciones
    })
    
    # --- 4. Combinar predicciones y finalizar ---
    forecast_df = pd.concat([df_in_sample, df_out_of_sample], ignore_index=True)
    forecast_df['yhat_lower'] = forecast_df['yhat'] - mae
    forecast_df['yhat_upper'] = forecast_df['yhat'] + mae

    return forecast_df



# --- Aplicación de Streamlit ---


def dl_models_page():
    
    st.subheader("Modelos de Deep Learning (GRU y Red Neuronal) 🤖") 

    st.markdown(
        "Seleccione una estación, un modelo y un horizonte de tiempo en la barra lateral para generar un pronóstico."
    )
    
    st.markdown("Estaciones cargadas desde la base de datos.") # Mover este mensaje
    df_estaciones = obtener_estaciones_para_prediccion()
    #df_estaciones = pd.read_sql_table(tabla_est.name, motor)

    if df_estaciones.empty:
        st.error("No se pudieron cargar las estaciones desde la base de datos o el archivo CSV.")
        st.stop()

    # --- Controles en la Sidebar ---
    with st.sidebar: 
        st.header("Configuración de Predicción")
        estaciones_dict = pd.Series(df_estaciones.codigo_indicativo.values, index=df_estaciones.nombre_estacion.str.title()).to_dict()
        
        nombre_estacion_seleccionada = st.selectbox(
            "Seleccione la Estación a predecir",
            sorted(list(estaciones_dict.keys())),
        )

        model_options = {
            "GRU": "GRU",
            "Red Neuronal (NN)": "NN"
        }
        model_display_name = st.selectbox(
            "Seleccione el Modelo",
            list(model_options.keys()),
        )
        model_name_key = model_options[model_display_name]

        horizon_options = {"1 día": 1, "1 semana": 7, "2 semanas": 14, "1 mes": 30}
        horizon_selection = st.radio(
            "Seleccione el Horizonte de Predicción", list(horizon_options.keys())
        )
        
        run_prediction = st.button(f"Generar Predicción para {nombre_estacion_seleccionada}", type="primary")
        if st.button("Limpiar Cache de Datos"):
            st.cache_data.clear()
            st.success("Cache de datos limpiado. Por favor, vuelva a generar la predicción.")

    # --- Lógica de predicción y visualización (FUERA de la sidebar) ---
    if run_prediction:
        indicativo_seleccionado = estaciones_dict[nombre_estacion_seleccionada]
        periods_to_forecast = horizon_options[horizon_selection]
        
        df_hist = load_time_series_data(indicativo_seleccionado)
        cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]

        # Asegúrate de que 'cluster' esté en df_estaciones. Si no, necesitarás obtenerlo de otra forma.
        # Por ejemplo, podrías cargar un mapeo de estación a clúster.
        if 'cluster' in df_estaciones.columns and not df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].empty:
            cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]
        else:
            # Fallback si no se encuentra el clúster (por ejemplo, usar un clúster por defecto)
            cluster_id = 0 # O maneja el error adecuadamente
            st.warning(f"No se encontró el ID de clúster para la estación {indicativo_seleccionado}. Usando clúster por defecto (0).")
        
        model, scaler, df_metrics = load_model_and_metrics(model_name_key, cluster_id)
        
        # Solo procede si el modelo y scaler se cargaron realmente (no son placeholders)
        if isinstance(model, str) or isinstance(scaler, str):
            st.error("No se pudo cargar un modelo o scaler real. No se generará una predicción con datos reales.")
        else:
            with st.spinner(f"Generando predicción de {horizon_selection} con el modelo {model_display_name}..."):
                # Asegúrate de pasar el DataFrame 'df_hist' a make_dl_prediction
                # con todas las columnas necesarias ('fecha', 'tmed', 'altitud', ...)
                mae_historico = df_metrics['MAE'].iloc[0]
                forecast_df = make_dl_prediction(model, scaler, df_hist, periods_to_forecast, mae=mae_historico, model_name=model_name_key)

            st.markdown(f"### Resultados para **{nombre_estacion_seleccionada}** (Modelo: {model_display_name})")

            # Filtrar último tramo real del histórico (que debería coincidir con la longitud del forecast)
            y_real = df_hist["tmed"].iloc[-periods_to_forecast:].values
            y_pred = forecast_df["yhat"].values

            # Si hay suficiente solapamiento
        df_merge = pd.merge(df_hist, forecast_df, on="fecha", how="inner")

        if not df_merge.empty and len(df_merge) >= 2:
            y_real = df_merge["tmed"]
            y_pred = df_merge["yhat"]

            try:
                mae = mean_absolute_error(y_real, y_pred)
                mse = mean_squared_error(y_real, y_pred)
                r2 = r2_score(y_real, y_pred)
            except Exception as e:
                st.warning(f"Error calculando métricas: {e}")
                mae, mse, r2 = np.nan, np.nan, np.nan
        else:
            st.warning("⚠️ No hay suficientes datos reales para comparar con las predicciones.")
            mae, mse, r2 = np.nan, np.nan, np.nan       
                
            df_metrics = pd.DataFrame([{
                "MAE": mae,
                "MSE": mse,
                "R²": r2
            }])
       
         
        # Asegúrate de que df_hist tenga la columna 'fecha' y 'tmed' para el gráfico
        # --- Gráfico de Resultados con Plotly ---
        # Este gráfico es más personalizable y visualmente atractivo que st.line_chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_hist["fecha"], 
            y=df_hist["tmed"], 
            mode="lines", 
            name="Datos Históricos",
            line=dict(color='royalblue')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_df["fecha"],
            y=forecast_df["yhat"], 
            mode="lines+markers", 
            name="Predicción", 
            line=dict(color="orange", 
                      dash="dash")))
        
        if "yhat_lower" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df["fecha"],
                y=forecast_df["yhat_upper"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df["fecha"],
                y=forecast_df["yhat_lower"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(255, 165, 0, 0.2)",
                name="Intervalo de Confianza",
            )) 
        # fig.add_trace(go.Scatter(
        #     x=df_hist["fecha"], 
        #     y=df_hist["tmed"], 
        #     mode="lines", 
        #     name="Datos Históricos"))
        # fig.add_trace(go.Scatter(
        #     x=forecast_df["fecha"], 
        #     y=forecast_df["tmed_predicted"], 
        #     mode="markers+lines" if len(forecast_df) > 1 else "markers",            
        #     name="Predicción", 
        #     line=dict(color="orange", 
        #               dash="dash")))

        fig.update_layout(
            title=f"Predicción vs. Datos Históricos ({model_display_name} - {nombre_estacion_seleccionada}). Pronóstico de {horizon_selection}",
            xaxis_title="Fecha",
            yaxis_title="Temperatura Media (°C)",
            legend_title="Leyenda"
        )

        # --- Aplicar "Zoom" Adaptativo al gráfico ---
        # Define cuánto contexto histórico mostrar en relación con el pronóstico.
        CONTEXT_MULTIPLIER = 10 
        MIN_CONTEXT_DAYS = 90   # Mostrar al menos 3 meses de contexto
        MAX_CONTEXT_DAYS = 365  # Mostrar como máximo 1 año de contexto

        # Calcula los días de contexto a mostrar
        context_days = min(
            max(periods_to_forecast * CONTEXT_MULTIPLIER, MIN_CONTEXT_DAYS),
            MAX_CONTEXT_DAYS
        )

        # Define el rango de fechas para el zoom
        start_zoom_date = df_hist['fecha'].max() - pd.DateOffset(days=int(context_days))
        end_zoom_date = forecast_df['fecha'].max()

        # Asegurarse de no ir más allá del inicio de los datos históricos
        if start_zoom_date < df_hist['fecha'].min():
            start_zoom_date = df_hist['fecha'].min()

        fig.update_xaxes(range=[start_zoom_date, end_zoom_date])

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Métricas del Modelo")
        st.dataframe(df_metrics.style.format("{:.2f}"), hide_index = True, use_container_width=True) # Ocultar índice
    
    # --- Sección Explicativa ---
    st.markdown("---")
    st.markdown("### ¿Cómo afecta el tiempo a la precisión del modelo?")
    st.info(
        """
        **A corto plazo (ej. 1 día, 1 semana):** Los modelos suelen ser bastante precisos. Se basan en los datos más recientes, que son un buen indicador del futuro inmediato. La incertidumbre es baja.

        **A mediano y largo plazo (ej. 2 semanas, 1 mes):** La precisión tiende a disminuir a medida que aumenta el horizonte de predicción. Esto se debe a varias razones:
        - **Acumulación de Errores:** Especialmente en modelos como GRU y redes neuronales que predicen de forma recursiva (usando predicciones anteriores para generar nuevas), cualquier pequeño error en una predicción temprana se propaga y magnifica en las predicciones futuras.
        - **Incertidumbre Creciente:** El futuro es inherentemente incierto. Cuanto más nos alejamos en el tiempo, mayor es la probabilidad de que ocurran eventos imprevistos (cambios en el mercado, nuevos factores no vistos en los datos históricos) que el modelo no puede anticipar.
        - **Deriva del Modelo (Model Drift):** Las relaciones y patrones en los datos pueden cambiar con el tiempo. Un modelo entrenado con datos de hace un año podría no ser tan efectivo para predecir el comportamiento dentro de un mes si las condiciones subyacentes han cambiado.

        En resumen, **a mayor horizonte de predicción, menor es la confianza y la precisión esperada del modelo.**
        """
    )


# Se llama a la función principal para renderizar la página
dl_models_page()