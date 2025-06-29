import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib # Para cargar escalaradores
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Intentamos importar Keras, pero si falla... avisamos y detenemos todo
try:
    from keras.models import load_model as load_keras_model
    pass 
except ImportError:
    st.error(
        "Falta TensorFlow/Keras para modelos DL. Verifica tu entorno."
    )
    st.stop()

from src.extraer_datos import obtener_estaciones_para_prediccion, obtener_datos_historicos_estacion
from src.personalizacion import load_css

st.set_page_config(
    page_title = "Modelos de Deep Learning",
    page_icon = "🤖",
    layout = "wide",
    initial_sidebar_state = "expanded"

)    

load_css("src/estilos.css")
st.spinner("Cargando modelos de Deep Learning...")


@st.cache_data(ttl = 60)
def crear_secuencias(datos: pd.DataFrame, columna_objetivo: str, ventana: int) -> np.ndarray:
    """
    Función para armar secuencias a partir de datos de series temporales
    """
   
    datos_entrada = datos.drop(columns = columna_objetivo).values
    datos_objetivo = datos[columna_objetivo].values

    n_secuencias = len(datos) - ventana
    n_caracteristicas = datos_entrada.shape[1]

    # Pre-generar los índices para todas las secuencias de una vez
    
    forma = (n_secuencias, ventana, n_caracteristicas)
    saltos = (datos_entrada.strides[0], datos_entrada.strides[0], datos_entrada.strides[1])
    X = np.lib.stride_tricks.as_strided(datos_entrada, shape = forma, strides = saltos)

    # Las etiquetas son simplemente los valores que siguen a cada ventana
    y = datos_objetivo[ventana:]

    return X, y


@st.cache_data(ttl = 60)
def cargar_datos_series(indicativo_estacion: str) -> pd.DataFrame:
    """
    Carga los datos de series temporales para una estación específica desde la base de datos.
    El DataFrame debe tener una columna 'fecha' (datetime) e 'y' (valor numérico).
    """
    df = obtener_datos_historicos_estacion(indicativo_estacion)

    if df.empty:
        st.warning(f"No hay datos para la estación {indicativo_estacion}. Retornando DataFrame vacío.")
        
        return pd.DataFrame()

    
    columnas_necesarias = ['altitud', 'tmed', 'tmin', 'tmax', 'prec', 'racha', 'hrMedia', 'fecha']
    
    columnas_faltantes = [col for col in columnas_necesarias if col not in df.columns]
    if columnas_faltantes:
        st.error(f"Faltan columnas: {', '.join(columnas_faltantes)}")
        return pd.DataFrame()

    filas_antes = len(df)
    # Eliminar filas donde CUALQUIERA de las características necesarias (excluyendo la fecha) sea NaN
    df_limpio = df.dropna(subset = [col for col in columnas_necesarias if col != 'fecha'])
    filas_despues = len(df_limpio)
    
    if filas_despues < filas_antes:
        st.warning(f"Se eliminaron {filas_antes - filas_despues} filas con datos faltantes. \
                   La última fecha con datos completos es {df_limpio['fecha'].max().strftime('%Y-%m-%d')}.")

    return df_limpio

@st.cache_resource
def cargar_modelo_y_escalador(nombre_modelo: str, id_cluster: int) -> tuple:
    """
    Carga un modelo Keras pre-entrenado y su correspondiente scaler.
            
    NOTA: Los modelos DL se entrenan por clúster.

    """
  
    ruta_modelo = f'modelos/modelos_dl/{nombre_modelo}_cluster_{id_cluster}.keras'
    ruta_escalador = f'modelos/modelos_dl/{nombre_modelo}_scaler_cluster_{id_cluster}.pkl'
    
    try:
        modelo = load_keras_model(ruta_modelo)
        escalador = joblib.load(ruta_escalador)
        st.success(f"Modelo {nombre_modelo} para clúster {id_cluster} cargado.")
    except Exception as e:
        st.warning(f"No se pudo cargar modelo o escalador: {e}")
        st.warning("Las predicciones serán simuladas.")

        # Si la carga falla, los placeholders de abajo se usarán para la simulación
        # Placeholder para la demostración si no se cargan los modelos reales:

        modelo = f"modelo_simulado_{nombre_modelo}"
        escalador = "escalador_simulado"

    return modelo, escalador


def hacer_prediccion_dl(modelo, escalador, datos: pd.DataFrame, periodos: int, tam_ventana: int = 30, nombre_modelo: object = None) -> pd.DataFrame:
    """
    Realiza predicciones con modelos de Deep Learning (GRU/NN) de forma recursiva.
    Ahora incluye predicciones "in-sample" para mostrar el ajuste del modelo.

    Args:
        modelo: El modelo Keras cargado.
        escalador: El scaler (MinMaxScaler) usado para normalizar los datos.
        datos: DataFrame con los datos históricos.
        periodos: Número de pasos a predecir.
        tam_ventana: Tamaño de la ventana de entrada para el modelo.
    
    Returns:
        pd.DataFrame: DataFrame con fechas y predicciones ('fecha', 'ypred', 'ypred_inferior', 'ypred_superior').
    
    ¡CRÍTICO! El orden y el contenido de esta lista deben coincidir EXACTAMENTE
    con las columnas del DataFrame que se usó para entrenar (hacer .fit()) el scaler.
    """
    columna_objetivo = 'tmed'
    if nombre_modelo == "GRU":
        caracteristicas_a_escalar = ['altitud', 'tmed', 'tmin', 'tmax', 'prec', 'racha', 'hrMedia']
        caracteristicas_para_modelo = [col for col in caracteristicas_a_escalar if col != columna_objetivo]
    else:
        caracteristicas_a_escalar = ['tmed']
        caracteristicas_para_modelo = [columna_objetivo]
    
    # El índice de la columna objetivo dentro de la lista completa de características escaladas
    indice_escalador_tmed = caracteristicas_a_escalar.index(columna_objetivo)
    
    tam_ventana = modelo.input_shape[1] 
    
    datos_escalados = escalador.transform(datos[caracteristicas_a_escalar])
    df_escalado = pd.DataFrame(datos_escalados, columns = caracteristicas_a_escalar)

    # Crear secuencias para los datos históricos según el tipo de modelo
    if nombre_modelo == "NN": 
        X_hist_lista = []
        for i in range(len(df_escalado) - tam_ventana):
            
            X_hist_lista.append(df_escalado[columna_objetivo].iloc[i : i + tam_ventana].values.reshape(tam_ventana, 1))
        X_hist = np.array(X_hist_lista)
    else: 
        X_hist, _ = crear_secuencias(df_escalado, columna_objetivo, tam_ventana)
    
    ypred_hist_escalado = modelo.predict(X_hist, verbose = 1)
    
    dummy_para_desescalar = np.zeros((len(ypred_hist_escalado), len(caracteristicas_a_escalar)))
    dummy_para_desescalar[:, indice_escalador_tmed] = ypred_hist_escalado.flatten()
    ypred_hist_original = escalador.inverse_transform(dummy_para_desescalar)[:, indice_escalador_tmed]

    fechas_pred_hist = datos['fecha'].iloc[tam_ventana:].reset_index(drop = True)
    df_in_sample = pd.DataFrame({'fecha': fechas_pred_hist, 'ypred': ypred_hist_original})
 
    if nombre_modelo == "NN": 
        ultima_secuencia = datos[[columna_objetivo]].values[-tam_ventana:]
    else: 
        ultima_secuencia = datos[caracteristicas_a_escalar].values[-tam_ventana:]

    ultima_secuencia_escalada = escalador.transform(ultima_secuencia)  
    
    # Obtiene los índices de las columnas que el modelo necesita como entrada

    indices_entrada = [caracteristicas_a_escalar.index(f) for f in caracteristicas_para_modelo]

    secuencia_actual = ultima_secuencia_escalada[:, indices_entrada]

    secuencia_actual = np.expand_dims(secuencia_actual, axis = 0)

    predicciones = []
    

    df_hist_copia = datos.copy() 
    df_hist_copia['mes'] = df_hist_copia['fecha'].dt.month 
    
    # Las características para las que calcularemos promedios estacionales son
    # todas las del modelo, excepto la altitud (que es constante).
    media_estacional_columnas = [f for f in caracteristicas_para_modelo if f != 'altitud']
     # Calcula los promedios mensuales
    media_estacional_caracteristicas = df_hist_copia.groupby('mes')[media_estacional_columnas].mean()

    
    ultima_altitud_conocida = df_hist_copia['altitud'].iloc[-1]

    # Generar las fechas futuras a partir de la última fecha conocida
    ultima_fecha = df_hist_copia['fecha'].max().normalize() # Normaliza para quitar la hora
    
    fecha_inicio_prediccion = ultima_fecha + pd.Timedelta(days = 1)
    fecha_prediccion = pd.date_range(start = fecha_inicio_prediccion, periods = periodos, freq = 'D')
    
    for i in range(periodos):

        sig_paso_tmed_escalada = modelo.predict(secuencia_actual, verbose = 0)

        dummy_fila_escalada = np.copy(ultima_secuencia_escalada[-1, :]).reshape(1, -1)  
        
        dummy_fila_escalada[0, indice_escalador_tmed] = sig_paso_tmed_escalada[0, 0]
        

        sig_paso_original = escalador.inverse_transform(dummy_fila_escalada)[0]
        # print(f"Desescalado: {next_step_original}")
        
        tmed_predecida = sig_paso_original[indice_escalador_tmed]
        predicciones.append(tmed_predecida)
        
        # --- Actualizar la secuencia de entrada para la siguiente predicción ---
        
        fecha_actual_prediccion = fecha_prediccion[i]

        dict_fechas_futuras = {}
        
        if nombre_modelo == "GRU": # Solo para modelos multivariados, estas características son entradas
            dict_fechas_futuras['altitud'] = ultima_altitud_conocida
            mes_actual = fecha_actual_prediccion.month
        
        # --- DEPURACIÓN: IMPRIMIR VALORES FUTUROS DE LAS ENTRADAS ---
        #current_step_features_info = {f: None for f in avg_seasonal_features_cols} # Para almacenar los valores que se usarán
        
             
            
            for hito in media_estacional_columnas:
                if mes_actual in media_estacional_caracteristicas.index:
                    valor = media_estacional_caracteristicas.loc[mes_actual, hito]
                    dict_fechas_futuras[hito] = valor
                else:
                    valor = df_hist_copia[hito].mean()
                    dict_fechas_futuras[hito] = valor
            
            
            fechas_futuras = np.array([dict_fechas_futuras[f] for f in caracteristicas_para_modelo])
            
        else: 
            # Para NN, la única entrada es la tmed predicha del paso anterior.
           
            fechas_futuras = np.array([tmed_predecida]) # Solo tmed como entrada
        
        dummy_fila_original_para_escalador = np.zeros(len(caracteristicas_a_escalar)) 

        for j, feature_name in enumerate(caracteristicas_para_modelo):
            idx_in_scaler = caracteristicas_a_escalar.index(feature_name)
            dummy_fila_original_para_escalador[idx_in_scaler] = fechas_futuras[j]

        sig_fila_escalada = escalador.transform(dummy_fila_original_para_escalador.reshape(1, -1))
        
        next_input_row_scaled_model = sig_fila_escalada[0, indices_entrada]   

        current_input_sequence = np.roll(secuencia_actual, -1, axis = 1)
        current_input_sequence[0, -1, :] = next_input_row_scaled_model

 
    df_out_of_sample = pd.DataFrame({
        'fecha': fecha_prediccion,
        'ypred': predicciones
    })
    
    # --- 4. Combinar predicciones y finalizar ---
    df_predicciones = pd.concat([df_in_sample, df_out_of_sample], ignore_index=True)


    return df_predicciones



# --- Aplicación de Streamlit ---


def modelos_dl():
    
    st.subheader("Modelos de Deep Learning (GRU y Red Neuronal) 🤖") 

    st.markdown(
        "Seleccione una estación, un modelo y un horizonte de tiempo en la barra lateral para generar un pronóstico."
    )
    
    df_estaciones = obtener_estaciones_para_prediccion()
   
    if df_estaciones.empty:
        st.error("No se pudieron cargar las estaciones desde la base de datos o el archivo CSV.")
        st.stop()

    # --- Controles en la Sidebar ---
    with st.sidebar: 
        st.header("Configuración de predicción")
        estaciones_dict = pd.Series(df_estaciones.codigo_indicativo.values, index = df_estaciones.nombre_estacion.str.title()).to_dict()
        
        nombre_estacion_seleccionada = st.selectbox(
            "Seleccione la Estación a predecir",
            sorted(list(estaciones_dict.keys())),
        )

        opciones_modelo = {
            "GRU": "GRU",
            "Red Neuronal (NN)": "NN"
        }

        nombre_visible_modelo = st.selectbox(
            "Seleccione el Modelo",
            list(opciones_modelo.keys()),
        )

        clave_modelo = opciones_modelo[nombre_visible_modelo]

        opciones_horizonte = {"1 día": 1, "1 semana": 7, "2 semanas": 14, "1 mes": 30}
        seleccion_horizonte = st.radio(
            "Seleccione el horizonte de predicción", list(opciones_horizonte.keys())
        )
        
        ejecutar_prediccion = st.button(f"Generar predicción para {nombre_estacion_seleccionada}", type = "primary")
        if st.button("Limpiar Cache de Datos"):
            st.cache_data.clear()
            st.success("Cache de datos limpiado. Por favor, vuelva a generar la predicción.")

    # --- Lógica de predicción y visualización (FUERA de la sidebar) ---
    if ejecutar_prediccion:
        indicativo_seleccionado = estaciones_dict[nombre_estacion_seleccionada]
        periodos_a_predecir = opciones_horizonte[seleccion_horizonte]
        
        df_hist = cargar_datos_series(indicativo_seleccionado)
        cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]

       
        if 'cluster' in df_estaciones.columns and not df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].empty:
            cluster_id = df_estaciones[df_estaciones['codigo_indicativo'] == indicativo_seleccionado]['cluster'].iloc[0]
        else:
            # Fallback si no se encuentra el clúster ( usar un clúster por defecto)
            cluster_id = 0 
            st.warning(f"No se encontró el ID de clúster para la estación {indicativo_seleccionado}. Usando clúster por defecto (0).")
        
        modelo, escalador = cargar_modelo_y_escalador(clave_modelo, cluster_id)
        
        # Solo procede si el modelo y scaler se cargaron realmente
        if modelo is None or escalador is None:
            st.error("No se pudo cargar un modelo o escalador real. No se generará una predicción con datos reales.")
        else:
            with st.spinner(f"Generando predicción de {seleccion_horizonte} con el modelo {nombre_visible_modelo}..."):
                
                
                df_predicciones = hacer_prediccion_dl(modelo, escalador, df_hist, periodos_a_predecir, nombre_modelo = clave_modelo)

            st.markdown(f"### Resultados para **{nombre_estacion_seleccionada}** (Modelo: {nombre_visible_modelo})")

            # --- Cálculo de métricas y del intervalo de confianza ---
            # Las métricas se calculan comparando las predicciones "in-sample" (sobre el histórico)
            # con los valores reales.
            df_merge = pd.merge(df_hist, df_predicciones, on="fecha", how="inner")

            if not df_merge.empty and len(df_merge) >= 2:
                y_real = df_merge["tmed"]
                y_pred = df_merge["ypred"]
                
                try:
                    mae = mean_absolute_error(y_real, y_pred)
                    mse = mean_squared_error(y_real, y_pred)
                    r2 = r2_score(y_real, y_pred)
                except Exception as e:
                    st.warning(f"Error calculando métricas: {e}")
                    mae, mse, r2 = np.nan, np.nan, np.nan
                
            else:
                st.warning("⚠️ No hay suficientes datos reales para comparar con las predicciones y calcular métricas.")
                mae, mse, r2 = np.nan, np.nan, np.nan
                
        df_metricas = pd.DataFrame([{
            "MAE": mae,
            "MSE": mse,
            "R²": r2
            }])
       
            # Se añade el intervalo de confianza al DataFrame de predicciones usando el MAE calculado
        if not np.isnan(mae):
            df_predicciones['ypred_inferior'] = df_predicciones['ypred'] - mae
            df_predicciones['ypred_superior'] = df_predicciones['ypred'] + mae
        
        # --- Gráfico de Resultados con Plotly ---
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x = df_hist["fecha"], 
            y = df_hist["tmed"], 
            mode = "lines", 
            name = "Datos Históricos",
            line = dict(color = 'royalblue')
        ))
        
        fig.add_trace(go.Scatter(
            x = df_predicciones["fecha"],
            y = df_predicciones["ypred"], 
            mode = "lines+markers", 
            name = "Predicción", 
            line = dict(color = "orange", 
                        dash = "dash")))
        
        if "ypred_inferior" in df_predicciones.columns:
            fig.add_trace(go.Scatter(
                x = df_predicciones["fecha"],
                y = df_predicciones["ypred_superior"],
                mode = "lines",
                line = dict(width=0),
                showlegend = False,
            ))
            fig.add_trace(go.Scatter(
                x = df_predicciones["fecha"],
                y = df_predicciones["ypred_inferior"],
                mode = "lines",
                line = dict(width=0),
                fill = "tonexty",
                fillcolor = "rgba(255, 165, 0, 0.2)",
                name = "Intervalo de confianza",
            )) 
      
        fig.update_layout(
            title = f"Predicción vs. Datos históricos ({nombre_visible_modelo} - {nombre_estacion_seleccionada}). Pronóstico de {seleccion_horizonte}",
            xaxis_title = "Fecha",
            yaxis_title = "Temperatura Media (°C)",
            legend_title = "Leyenda"
        )

        # --- Aplicar "Zoom" Adaptativo al gráfico ---
        
        CONTEXT_MULTIPLIER = 10 
        MIN_CONTEXT_DAYS = 90   
        MAX_CONTEXT_DAYS = 365  

        # Calcula los días de contexto a mostrar
        context_days = min(
            max(periodos_a_predecir * CONTEXT_MULTIPLIER, MIN_CONTEXT_DAYS),
            MAX_CONTEXT_DAYS
            )

        # Define el rango de fechas para el zoom
        start_zoom_date = df_hist['fecha'].max() - pd.DateOffset(days = int(context_days))
        end_zoom_date = df_predicciones['fecha'].max()

        # Asegurarse de no ir más allá del inicio de los datos históricos
        if start_zoom_date < df_hist['fecha'].min():
            start_zoom_date = df_hist['fecha'].min()

        fig.update_xaxes(range = [start_zoom_date, end_zoom_date])

        st.plotly_chart(fig, use_container_width = True)

        st.markdown("#### Métricas del modelo")
        st.dataframe(df_metricas.style.format("{:.2f}"), hide_index = True, use_container_width = True)
    
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
modelos_dl()