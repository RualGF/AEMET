import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pickle
import os

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Para que el código de demostración funcione, necesitarás Prophet.
# pip install prophet
try:
    from prophet import Prophet
    # import pickle # Si vas a cargar un modelo Prophet pre-entrenado
except ImportError:
    st.error(
        "Por favor, instala Prophet (`pip install prophet`) para que el modelo de ejemplo funcione."
    )
    st.stop()

from src.personalizacion import load_css
from src.extraer_datos import obtener_estaciones_para_prediccion, obtener_datos_historicos_estacion

st.set_page_config(
    page_title="Modelo Prophet",
    page_icon="🔮",  # Icono para Prophet
    layout="wide",
    initial_sidebar_state="expanded"
)
load_css("src/estilos.css")

# --- Funciones de Ayuda (Reemplazar con tu lógica) ---
# Estas funciones son placeholders. Debes adaptarlas para cargar tus datos y modelos reales.


@st.cache_data(ttl=300) # Cachear por 1 hora
def load_time_series_data(indicativo_estacion: str):

    """
    Carga los datos de series temporales para una estación específica desde la base de datos.
    El DataFrame debe tener una columna 'ds' (datetime) y 'y' (valor numérico).
    """
    # Usamos datos de ejemplo para la demostración. Reemplázalo con tu carga de datos.
    # st.write(f"Cargando datos de ejemplo para Prophet en {poblacion}...")

    # dates = pd.to_datetime(
    #     pd.date_range(start="2022-01-01", end="2023-12-31", freq="D")
    # )
    # # Simula datos diferentes para cada población cambiando el valor base
    # base_value = 50
    # if poblacion == "Madrid":
    #     base_value = 70
    # elif poblacion == "Barcelona":
    #     base_value = 65
    # elif poblacion == "Valencia":
    #     base_value = 60

    # # Una onda sinusoidal con ruido y una tendencia ascendente
    # values = (
    #     np.sin(np.arange(len(dates)) * 0.1) * 15
    #     + np.arange(len(dates)) * 0.1
    #     + np.random.randn(len(dates)) * 2
    #     + 50
    # )
    # df = pd.DataFrame({"ds": dates, "y": values})
    st.write(f"Cargando datos históricos para la estación {indicativo_estacion}...")
    # Aquí se llama a la función real que extrae de la base de datos
    df = obtener_datos_historicos_estacion(indicativo_estacion, target_col='tmed') # Asumimos 'tmed' como objetivo
    
    if df.empty:
        st.warning(f"No se encontraron datos históricos para la estación {indicativo_estacion}. Usando datos de ejemplo.")
        # Fallback a datos de ejemplo si no hay datos reales
        dates = pd.to_datetime(pd.date_range(start="2022-01-01", end="2023-12-31", freq="D"))
        values = np.sin(np.arange(len(dates)) * 0.1) * 15 + np.arange(len(dates)) * 0.1 + np.random.randn(len(dates)) * 2 + 50
        df = pd.DataFrame({"ds": dates, "y": values})
    else:
         # ✅ Renombrar columnas al formato que Prophet espera
        df = df.rename(columns={"fecha": "ds", "tmed": "y"})
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
        df = df.dropna(subset=['ds', 'y'])
    return df


@st.cache_resource
def load_model_and_metrics_prophet(poblacion, cluster_id):
    """
    Carga las métricas para el modelo Prophet para una población específica.
    En un escenario real, aquí cargarías un modelo Prophet pre-entrenado si no lo entrenas al vuelo.
    """
    # --- Carga de modelo Prophet pre-entrenado y sus métricas ---
    # En un escenario real, los modelos Prophet se entrenarían por estación o por clúster.
    # Aquí, `poblacion` se usaría para identificar el modelo correcto.
    # Por ejemplo, si `poblacion` es el `indicativo` de la estación o el `cluster_id`.
    
    model = None
    metrics = {"Prophet": {"RMSE": np.nan, "MAE": np.nan, "R²": np.nan}} # Valores por defecto

    # Ejemplo de cómo cargar un modelo Prophet guardado y sus métricas
    # Asegúrate de que tus modelos y métricas estén guardados en la ruta correcta.
    # Por ejemplo, si guardas un modelo por cada estación:
    model_path = f'modelos/prophet/cluster_model_{cluster_id}.pkl'
    # model_path = f'models/prophet_models/prophet_model_{poblacion}.pkl'
    # metrics_path = f'models/prophet_models/metrics_{poblacion}.json' # O de donde sea que cargues las métricas
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        st.write("Ruta absoluta buscada:", os.path.abspath(model_path))
        st.write("¿Existe?", os.path.exists(model_path))
        # Cargar métricas reales (ej. de un archivo JSON)
        # with open(metrics_path, 'r') as f:
        #     metrics = json.load(f)
        st.success(f"Modelo Prophet para {poblacion} cargado exitosamente.")
    except FileNotFoundError:
        st.warning(f"Modelo Prophet para {poblacion} no encontrado en {model_path}. Se entrenará al vuelo.")
        # Si no se encuentra el modelo pre-entrenado, se entrenará al vuelo en `make_prophet_prediction`.

    model = f"Modelo Prophet para {poblacion} (entrenado al vuelo para la demo)"  # Placeholder


    return model, pd.DataFrame([metrics["Prophet"]])


def make_prophet_prediction(df, periods, m):
    """
    Realiza una predicción con Prophet.
    Para la demo, entrenamos un modelo al vuelo. En tu caso, cargarías uno ya entrenado.
    """
    # Si `model` ya fue cargado en `load_model_and_metrics_prophet`, úsalo aquí.
    # Si `model` es None (porque no se encontró el pre-entrenado), entonces entrena uno nuevo.
    if m is None or not isinstance(m, Prophet):
        m = Prophet(interval_width=0.95) # Puedes ajustar el intervalo de confianza
        m.fit(df)
    st.info("🔁 Usando modelo Prophet precargado")
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]


# --- Aplicación de Streamlit ---


def prophet_page():

    st.subheader("Modelo Prophet 🔮 - Predicción de Series Temporales")
    st.markdown(
        "Genere un pronóstico con el modelo Prophet para diferentes horizontes de tiempo."
    )

    # Obtener estaciones reales de la base de datos
    df_estaciones = obtener_estaciones_para_prediccion()
    if df_estaciones.empty:
        st.error("No se pudieron cargar las estaciones desde la base de datos o los archivos locales.")

    
    # --- Controles en la Sidebar ---
    with st.sidebar:
        st.header("Configuración de Predicción")
        estaciones_dict = pd.Series(df_estaciones.codigo_indicativo.values, index=df_estaciones.nombre_estacion.str.title()).to_dict()
        
        
        nombre_estacion_seleccionada = st.selectbox(
            "Seleccione la Estación a predecir",
            sorted(list(estaciones_dict.keys())),
        )

        st.write("Modelo seleccionado: **Prophet**")

        horizon_options = {"1 día": 1, "1 semana": 7, "2 semanas": 14, "1 mes": 30}
        horizon_selection = st.radio(
            "Seleccione el Horizonte de Predicción", list(horizon_options.keys())
        )
        
        run_prediction = st.button(f"Generar Predicción para {nombre_estacion_seleccionada}", type="primary")

    if run_prediction:
        indicativo_seleccionado = estaciones_dict[nombre_estacion_seleccionada]
        periods_to_forecast = horizon_options[horizon_selection]
        cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]

        df_hist = load_time_series_data(indicativo_seleccionado)
        model, df_metrics = load_model_and_metrics_prophet(indicativo_seleccionado, cluster_id)

        with st.spinner(f"Generando predicción de {horizon_selection} para {nombre_estacion_seleccionada}..."):
            forecast_df = make_prophet_prediction(df_hist, periods_to_forecast, model)
    
            #forecast_df = make_prophet_prediction(df_hist, periods_to_forecast)

        st.markdown(f"### Resultados para **{nombre_estacion_seleccionada}** (Modelo: Prophet)")

        # Gráfico de resultados
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_hist["ds"], 
            y=df_hist["y"], 
            mode="lines", 
            name="Datos Históricos"))
        
        fig.add_trace(go.Scatter(
            x=forecast_df["ds"], 
            y=forecast_df["yhat"], 
            mode="lines", 
            name="Predicción", 
            line=dict(color="orange", 
                      dash="dash")))
        
        if "yhat_lower" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df["ds"],
                y=forecast_df["yhat_upper"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df["ds"],
                y=forecast_df["yhat_lower"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(255, 165, 0, 0.2)",
                name="Intervalo de Confianza",
            ))          
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['yhat'], name="Pronóstico", line=dict(color='blue')))
        # fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['yhat_upper'], name="Límite superior", line=dict(color='lightblue'), fill=None))
        # fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['yhat_lower'], name="Límite inferior", line=dict(color='lightblue'), fill='tonexty'))
        # fig.add_trace(go.Scatter(x=df_hist['ds'], y=df_hist['y'], name="Histórico", line=dict(color='black')))
        # fig.update_layout(title=f"Pronóstico {horizon_selection} días - {nombre_estacion_seleccionada}", xaxis_title="Fecha", yaxis_title="Temperatura media")
        
        # st.plotly_chart(fig)
        fig.update_layout(
            title=f"Predicción vs. Datos Históricos (Prophet - {nombre_estacion_seleccionada}). Pronóstico de {horizon_selection}",
            xaxis_title="Fecha",
            yaxis_title="Valor",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Métricas del modelo
        
        df_merge = pd.merge(
            df_hist, forecast_df, on="ds", how="inner"
            )

        if not df_merge.empty:
            y_true = df_merge["y"]
            y_pred = df_merge["yhat"]

            mae = mean_absolute_error(y_true, y_pred)
            mse = mean_squared_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)

            df_metrics = pd.DataFrame([{
                "MAE": mae,
                "MSE": mse,
                "R²": r2
            }])
        else:
            df_metrics = pd.DataFrame([{
                "MAE": np.nan,
                "MSE": np.nan,
                "R²": np.nan
            }])

        if df_metrics.dropna().empty:
            st.warning("⚠️ No hay suficientes datos reales para calcular métricas.")
        else:
            st.markdown("#### Métricas del Modelo")
            st.dataframe(df_metrics.style.format("{:.2f}"), hide_index=True, use_container_width=True)

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

        En resumen, **a mayor horizonte de predicción, menor es la confianza y la precisión esperada del modelo.** Los intervalos de confianza (como los que muestra Prophet) se ensanchan visiblemente para reflejar esta creciente incertidumbre.
        """
    )


# Se llama a la función principal para renderizar la página
prophet_page()
