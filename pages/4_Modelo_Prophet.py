import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pickle
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from prophet import Prophet
except ImportError:
    st.error(
        "Por favor, instala Prophet (`pip install prophet`) para que el modelo de ejemplo funcione."
    )
    st.stop()

from src.personalizacion import load_css
from src.extraer_datos import obtener_estaciones_para_prediccion, obtener_datos_historicos_estacion

st.set_page_config(
    page_title = "Modelo Prophet",
    page_icon = "🔮",  # Icono para Prophet
    layout = "wide",
    initial_sidebar_state = "expanded"
)
load_css("src/estilos.css")


@st.cache_data(ttl = 60) 
def load_time_series_data(indicativo_estacion: str) -> pd.DataFrame:
    """
    Carga los datos de series temporales para una estación específica desde la base de datos.
    El DataFrame debe tener una columna 'ds' (datetime) y 'y' (valor numérico).
    Garantiza continuidad temporal diaria sin huecos para evitar líneas rectas artificiales.
    """
    df = obtener_datos_historicos_estacion(indicativo_estacion)
    
    if df.empty:
        st.warning(f"No se encontraron datos históricos para la estación {indicativo_estacion}. Usando datos de ejemplo.")
        dates = pd.to_datetime(pd.date_range(start = "2022-01-01", end = "2023-12-31", freq = "D"))
        values = np.sin(np.arange(len(dates)) * 0.1) * 15 + np.arange(len(dates)) * 0.1 + np.random.randn(len(dates)) * 2 + 50
        df = pd.DataFrame({"ds": dates, "y": values})
    else:
        df = df.rename(columns = {"fecha": "ds", "tmed": "y"})
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'], errors = 'coerce')
        df = df.dropna(subset = ['ds']).sort_values('ds').drop_duplicates('ds')

        # Garantizar regularidad diaria (evitar saltos temporales y líneas rectas en periodos sin registros)
        if len(df) > 1:
            idx = pd.date_range(df['ds'].min(), df['ds'].max(), freq='D')
            df = df.set_index('ds').reindex(idx)
            df['y'] = df['y'].interpolate(method='time').ffill().bfill()
            df = df.reset_index().rename(columns={'index': 'ds'})
    return df


@st.cache_resource
def load_model_and_metrics_prophet(poblacion: str, cluster_id: int) -> tuple:
    """
    Carga las métricas para el modelo Prophet pre-entrenado para un clúster específico.
    """
    model = None
    metrics = {"Prophet": {"RMSE": np.nan, "MAE": np.nan, "R²": np.nan}}

    model_path = f'modelos/prophet/cluster_model_{cluster_id}.pkl'
     
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    except FileNotFoundError:
        model = None

    return model, pd.DataFrame([metrics["Prophet"]])


def make_prophet_prediction(
    df: pd.DataFrame, 
    periods: int, 
    m: Prophet | None = None, 
    modo: str = "estacion", 
    weekly_seasonality: bool = False,
    corregir_inercia: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame, Prophet]:
    """
    Realiza una predicción con Prophet.
    - Si modo == 'estacion', entrena Prophet directamente sobre la serie histórica local de la estación (~0.5s).
      Esto captura el microclima y nivel térmico exacto de la estación, sin el sesgo regional.
    - Si modo == 'cluster', utiliza el modelo pre-entrenado para el clúster climático.
    - Si corregir_inercia == True, modela la persistencia térmica reciente (AR-Prophet), evitando que la
      predicción caiga bruscamente a la media estacional histórica si hay una ola de calor o anomalía térmica.
    """
    if modo == "estacion" or m is None or not isinstance(m, Prophet):
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=False,
            interval_width=0.95,
            changepoint_prior_scale=0.05
        )
        # Ajuste local con la serie observada
        m.fit(df[['ds', 'y']])
    
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)

    # Inercia térmica reciente (AR Residual Decay)
    if corregir_inercia and not df.empty:
        ultima_fecha = df['ds'].max()
        ultimo_real = df[df['ds'] == ultima_fecha]['y'].iloc[0]
        pred_match = forecast[forecast['ds'] == ultima_fecha]
        if not pred_match.empty:
            pred_ultimo = pred_match['yhat'].iloc[0]
            residual = ultimo_real - pred_ultimo
            
            mask_futuro = forecast['ds'] > ultima_fecha
            if mask_futuro.any() and abs(residual) > 0.1:
                pasos = np.arange(1, mask_futuro.sum() + 1)
                # Persistencia atmosférica típica a corto plazo (0.8 diario)
                decay = 0.8 ** pasos
                ajuste = residual * decay
                forecast.loc[mask_futuro, 'yhat'] += ajuste
                forecast.loc[mask_futuro, 'yhat_lower'] += ajuste
                forecast.loc[mask_futuro, 'yhat_upper'] += ajuste

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]], forecast, m


def _calcular_fecha_corte(ventana: str, ultima_fecha: pd.Timestamp, primera_fecha: pd.Timestamp) -> pd.Timestamp:
    if ventana == "Últimos 3 meses":
        return ultima_fecha - pd.DateOffset(months=3)
    if ventana == "Últimos 6 meses (Recomendado)":
        return ultima_fecha - pd.DateOffset(months=6)
    if ventana == "Último año":
        return ultima_fecha - pd.DateOffset(years=1)
    return primera_fecha


def _renderizar_grafico_prophet(df_hist_plot, forecast_plot, ultima_fecha_hist, df_futuro, horizon_selection, nombre_estacion, df_hist):
    fig = go.Figure()

    # 1. Datos históricos observados
    fig.add_trace(go.Scatter(
        x=df_hist_plot["ds"], 
        y=df_hist_plot["y"], 
        mode="lines", 
        name="Datos Históricos Reales",
        line={"color": "#3366CC", "width": 2}
    ))

    # 2. Ajuste histórico del modelo (línea discontinua)
    df_ajuste_plot = forecast_plot[forecast_plot["ds"] <= ultima_fecha_hist]
    if not df_ajuste_plot.empty:
        fig.add_trace(go.Scatter(
            x=df_ajuste_plot["ds"], 
            y=df_ajuste_plot["yhat"], 
            mode="lines", 
            name="Ajuste del Modelo", 
            line={"color": "rgba(255, 127, 14, 0.6)", "dash": "dot", "width": 1.5}
        ))

    # 3. Pronóstico futuro (destacado con marcadores)
    if not df_futuro.empty:
        ultimo_punto = pd.DataFrame({
            "ds": [ultima_fecha_hist],
            "yhat": [df_hist[df_hist["ds"] == ultima_fecha_hist]["y"].iloc[0]],
            "yhat_lower": [df_hist[df_hist["ds"] == ultima_fecha_hist]["y"].iloc[0]],
            "yhat_upper": [df_hist[df_hist["ds"] == ultima_fecha_hist]["y"].iloc[0]]
        })
        df_futuro_plot = pd.concat([ultimo_punto, df_futuro], ignore_index=True)

        fig.add_trace(go.Scatter(
            x=df_futuro_plot["ds"],
            y=df_futuro_plot["yhat_upper"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=df_futuro_plot["ds"],
            y=df_futuro_plot["yhat_lower"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(255, 127, 14, 0.25)",
            name="Intervalo Confianza (95%)",
        ))
        fig.add_trace(go.Scatter(
            x=df_futuro_plot["ds"], 
            y=df_futuro_plot["yhat"], 
            mode="lines+markers", 
            name=f"Pronóstico Futuro ({horizon_selection})", 
            line={"color": "#FF6F00", "width": 3},
            marker={"size": 7, "color": "#FF6F00"}
        ))

    fig.update_layout(
        title=f"Pronóstico de Temperatura Media - {nombre_estacion} ({horizon_selection})",
        xaxis_title="Fecha",
        yaxis_title="Temp. Media (°C)",
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1}
    )
    st.plotly_chart(fig, use_container_width=True)


def _renderizar_tabla_futuro(df_futuro: pd.DataFrame):
    if df_futuro.empty:
        return
    st.markdown("#### 📅 Detalle del Pronóstico de los Próximos Días")
    dias_semana = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    df_tabla_futuro = pd.DataFrame({
        "Fecha": df_futuro["ds"].dt.strftime("%Y-%m-%d"),
        "Día": df_futuro["ds"].dt.dayofweek.map(dias_semana),
        "Temp. Prevista (°C)": df_futuro["yhat"].round(1),
        "Mínima esperada (°C)": df_futuro["yhat_lower"].round(1),
        "Máxima esperada (°C)": df_futuro["yhat_upper"].round(1)
    })
    st.dataframe(df_tabla_futuro, hide_index=True, use_container_width=True)


def _renderizar_metricas_ajuste(df_hist: pd.DataFrame, forecast_df: pd.DataFrame):
    df_merge = pd.merge(df_hist, forecast_df, on="ds", how="inner", validate="one_to_one")
    if df_merge.empty:
        return

    y_true = df_merge["y"]
    y_pred = df_merge["yhat"]

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    df_metrics = pd.DataFrame([{
        "MAE (°C)": mae,
        "RMSE (°C)": np.sqrt(mse),
        "R²": r2
    }])
    st.markdown("#### Métricas de Ajuste Histórico del Modelo")
    st.dataframe(df_metrics.style.format("{:.2f}"), hide_index=True, use_container_width=True)


def _renderizar_descomposicion(model_fitted, forecast_full):
    with st.expander("📊 Descomposición del Modelo (Tendencia y Ciclo Estacional Anual)"):
        try:
            from prophet.plot import plot_components_plotly
            fig_comp = plot_components_plotly(model_fitted, forecast_full)
            fig_comp.update_layout(height=450)
            st.plotly_chart(fig_comp, use_container_width=True)
        except Exception as e:
            st.info(f"No se pudo generar el gráfico de descomposición: {e}")


# --- Aplicación de Streamlit ---


def prophet_page():
    st.subheader("Modelo Prophet 🔮 - Predicción de Series Temporales")
    st.markdown("Genere un pronóstico con el modelo Prophet para diferentes horizontes de tiempo.")

    df_estaciones = obtener_estaciones_para_prediccion()
    if df_estaciones.empty:
        st.error("No se pudieron cargar las estaciones desde la base de datos o los archivos locales.")
        return

    with st.sidebar:
        st.header("Configuración de Predicción")
        estaciones_dict = pd.Series(df_estaciones.codigo_indicativo.values, index=df_estaciones.nombre_estacion.str.title()).to_dict()
        
        nombre_estacion_seleccionada = st.selectbox(
            "Seleccione la Estación a predecir",
            sorted(list(estaciones_dict.keys())),
        )

        st.write("Modelo seleccionado: **Prophet**")

        tipo_ajuste = st.radio(
            "Tipo de Ajuste del Modelo",
            ["Específico de la estación (Recomendado)", "Regional por clúster climático"],
            help="El ajuste específico modela la estación local en ~0.5s capturando su microclima exacto. El regional utiliza el clúster pre-entrenado."
        )

        corregir_inercia = st.checkbox(
            "Inercia térmica reciente (AR Residual)",
            value=True,
            help="Prophet es un modelo estacional/climatológico. Si la atmósfera atraviesa una ola de calor o anomalía térmica respecto a la media de los últimos 10 años, esta opción amortigua suavemente el salto para que el pronóstico inicial sea coherente con la temperatura observada ayer."
        )

        incluir_semanal = st.checkbox(
            "Incluir estacionalidad semanal",
            value=False,
            help="Desactivado por defecto. En meteorología, la temperatura se rige por estaciones anuales y frentes atmosféricos; desactivarlo evita vaivenes y oscilaciones artificiales de lunes a domingo."
        )

        horizon_options = {"1 día": 1, "1 semana": 7, "2 semanas": 14, "1 mes": 30}
        horizon_selection = st.radio(
            "Seleccione el Horizonte de Predicción", list(horizon_options.keys())
        )
        
        run_prediction = st.button(f"Generar Predicción para {nombre_estacion_seleccionada}", type="primary")
    
        if st.button("Limpiar Cache de Datos"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Caché limpiado. Por favor, vuelva a generar la predicción.")
    
    if not (run_prediction and nombre_estacion_seleccionada):
        return

    indicativo_seleccionado = estaciones_dict[nombre_estacion_seleccionada]
    horizon_key = str(horizon_selection) if horizon_selection else "1 día"
    periods_to_forecast = horizon_options.get(horizon_key, 1)
    cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]

    df_hist = load_time_series_data(indicativo_seleccionado)
    model_preentrenado, _ = load_model_and_metrics_prophet(indicativo_seleccionado, cluster_id)

    tipo_str = str(tipo_ajuste or "")
    modo_elegido = "estacion" if "Específico" in tipo_str else "cluster"

    with st.spinner(f"Generando predicción de {horizon_selection} para {nombre_estacion_seleccionada}..."):
        forecast_df, forecast_full, model_fitted = make_prophet_prediction(
            df=df_hist,
            periods=periods_to_forecast,
            m=model_preentrenado,
            modo=modo_elegido,
            weekly_seasonality=incluir_semanal,
            corregir_inercia=corregir_inercia
        )

    st.markdown(f"### Resultados para **{nombre_estacion_seleccionada}** (Modelo: Prophet)")
    if modo_elegido == "estacion":
        st.caption("⚡ *Modelo ajustado con los datos meteorológicos específicos de esta estación.*")
    else:
        st.caption(f"🌐 *Modelo regional precalculado para el Clúster {cluster_id}.*")

    if corregir_inercia:
        st.caption("🌡️ *Inercia térmica activa: conecta la anomalía atmosférica reciente con la tendencia estacional.*")

    ultima_fecha_hist = df_hist["ds"].max()
    df_futuro = forecast_df[forecast_df["ds"] > ultima_fecha_hist].copy()

    ventana_grafico = st.radio(
        "Ventana temporal a mostrar en el gráfico:",
        ["Últimos 3 meses", "Últimos 6 meses (Recomendado)", "Último año", "Todo el histórico"],
        index=1,
        horizontal=True
    )
    fecha_corte = _calcular_fecha_corte(str(ventana_grafico), ultima_fecha_hist, df_hist["ds"].min())

    df_hist_plot = df_hist[df_hist["ds"] >= fecha_corte]
    forecast_plot = forecast_df[forecast_df["ds"] >= fecha_corte]

    _renderizar_grafico_prophet(
        df_hist_plot, forecast_plot, ultima_fecha_hist, df_futuro, 
        horizon_selection, nombre_estacion_seleccionada, df_hist
    )
    _renderizar_tabla_futuro(df_futuro)
    _renderizar_metricas_ajuste(df_hist, forecast_df)
    _renderizar_descomposicion(model_fitted, forecast_full)


# --- Sección Explicativa ---
st.markdown("---")
st.markdown("### ¿Cómo afecta el tiempo a la precisión del modelo?")
st.info(
    """
    **A corto plazo (ej. 1 día, 1 semana):** Los modelos suelen ser bastante precisos. Se basan en los datos más recientes, que son un buen indicador del futuro inmediato. La incertidumbre es baja.

    **A mediano y largo plazo (ej. 2 semanas, 1 mes):** La precisión tiende a disminuir a medida que aumenta el horizonte de predicción. Esto se debe a varias razones:
    - **Acumulación de Errores:** Especialmente en modelos como GRU y redes neuronales que predicen de forma recursiva (usando predicciones anteriores para generar nuevas), cualquier pequeño error en una predicción temprana se propaga y magnifica en las predicciones futuras.
    - **Incertidumbre Creciente:** El futuro es inherentemente incierto. Cuanto más nos alejamos en el tiempo, mayor es la probabilidad de que ocurran eventos imprevistos que el modelo no puede anticipar.
    - **Deriva del Modelo (Model Drift):** Las relaciones y patrones en los datos pueden cambiar con el tiempo. Un modelo entrenado con datos de hace un año podría no ser tan efectivo para predecir el comportamiento dentro de un mes si las condiciones subyacentes han cambiado.

    En resumen, **a mayor horizonte de predicción, menor es la confianza y la precisión esperada del modelo.** Los intervalos de confianza (como los que muestra Prophet) se ensanchan visiblemente para reflejar esta creciente incertidumbre.
    """
)

prophet_page()
