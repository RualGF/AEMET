import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import extract, bindparam, func, select


from src.conectar import conexion_a_bd
from src.personalizacion import load_css
from src.extraer_datos import (
    construir_consulta_general, ejecutar_consulta_a_dataframe,
    df_provincias, tabla_dm
)

# Configuración de la página
st.set_page_config(
    page_title = "Comparador",
    page_icon = "📊",
    layout = "wide",
    initial_sidebar_state = "collapsed"
    )

# Sidebar, solo para resetear cosas si se cuelga
with st.sidebar:
    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

load_css('src/estilos.css')
motor = conexion_a_bd()

metricas = {
    "tmed":    {"nombre": "Temperatura media",   "unidad": "°C"},
    "tmin":    {"nombre": "Temperatura mínima",  "unidad": "°C"},
    "tmax":    {"nombre": "Temperatura máxima",  "unidad": "°C"},
    "prec":    {"nombre": "Precipitación",       "unidad": "mm"},
    "hrMedia": {"nombre": "Humedad relativa",    "unidad": "%"},
    "racha":   {"nombre": "Racha de viento",     "unidad": "km/h"}
}
# Mapeo de meses para que los meses se vean bonitos en vez de como números
meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

def obtener_anios_disponibles() -> list:
    """
    Obtiene los años disponibles en la tabla de datos meteorológicos para introducirlos en el multiselect.
    """
    consulta_stmt = select(func.year(tabla_dm.c.fecha).label("anio")).distinct().order_by("anio")
    df = ejecutar_consulta_a_dataframe(consulta_stmt)
    return sorted(df["anio"].dropna().astype(int).tolist())

def cargar_meteo_filtrada(codigo_prov: str, anios: list, columnas = None) -> pd.DataFrame:
    """
    Extrae los datos meteorológicos filtrados por provincia, métricas y años.
    """
    columnas = columnas or ["fecha", "codigo_prov", "tmed", "tmin", "tmax", "prec", "hrMedia", "racha"]

    filtros = [
        tabla_dm.c.codigo_prov == bindparam("codigo_prov"),
        extract("year", tabla_dm.c.fecha).in_(bindparam("anios", expanding = True))
    ]

    consulta_stmt = construir_consulta_general({
        "select": [tabla_dm.c[col] for col in columnas],
        "filters": filtros,
        "order_by": [tabla_dm.c.fecha]
    })

    return ejecutar_consulta_a_dataframe(consulta_stmt, codigo_prov = codigo_prov, anios = anios)

def calcular_estadisticas_por_mes(df: pd.DataFrame, columna_valor: str) -> pd.DataFrame:
    """
    Extrae las estadísticas por mes para graficar
    """
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    estadisticas = df.groupby(["anio", "mes"])[columna_valor].agg(
        media = "mean",
        mediana = "median",
        minimo = "min",
        maximo = "max"
    ).reset_index()

    return estadisticas

def configurar_figura(fig: go.Figure, nombre_metrica: str, unidad: str, nombre_provincia: str, titulo_leyenda: str):
    """
    Función auxiliar para configurar el layout común de las figuras.
    """
    fig.update_layout(
        title=dict(
            text = f"{nombre_metrica} mensual en {nombre_provincia} ({unidad})",
            x = 0.5, 
            xanchor = 'center', 
            font = dict(size = 20)
        ),
        xaxis = dict(title = dict(text = "Mes", font = dict(size = 16)), 
                     tickfont = dict(size = 14)),
        yaxis = dict(title = dict(text = f"{nombre_metrica} ({unidad})", 
                                  font = dict(size = 16)), 
                    tickfont = dict(size = 14)),
        legend_title = titulo_leyenda,
        legend = dict(font = dict(size = 14)),
        height = 600,
        template = "plotly_white"
    )

def graficar_lineas(df_estadisticas: pd.DataFrame, clave_metrica: str, nombre_provincia: str) -> go.Figure:
    """
    Genera un gráfico de líneas para comparar tendencias.
    """
    cfg = metricas[clave_metrica]
    nombre_metrica = cfg["nombre"]
    unidad = cfg["unidad"]
    
    df_estadisticas["mes_nombre"] = df_estadisticas["mes"].map(meses)
    
    fig = go.Figure()
    
    # Paletas de colores por año. Una gama de azules/verdes y otra de rojos/naranjas.
    paletas = [
        {"media": "royalblue", "mediana": "skyblue", "minimo": "lightseagreen", "maximo": "midnightblue"},
        {"media": "crimson",   "mediana": "tomato",    "minimo": "lightsalmon",   "maximo": "darkred"}
        ]

    # Usamos enumerate para asignar una paleta a cada año
    for i, anio in enumerate(sorted(df_estadisticas["anio"].unique())):
       
        paleta_actual = paletas[i % len(paletas)]
        datos_anio = df_estadisticas[df_estadisticas["anio"] == anio]
        
        for estadistica in ["media", "mediana", "minimo", "maximo"]:
            
            # La media resalta: línea sólida, más gruesa y opaca.
            if estadistica == "media":
                line_style = dict(color = paleta_actual[estadistica], width = 3, dash = 'solid')
                opacity = 1.0
            
            # Las demás estadísticas son más sutiles: línea punteada, más fina y semitransparente.
            else:
                line_style = dict(color=paleta_actual[estadistica], width = 1.5, dash = 'dot')
                opacity = 0.7
            
            fig.add_trace(go.Scatter(
                x = datos_anio["mes_nombre"],
                y = datos_anio[estadistica].round(2),
                mode = "lines+markers",
                name = f"{estadistica.capitalize()} {anio}",
                line = line_style,
                opacity = opacity
                ))
    
    configurar_figura(fig, nombre_metrica, unidad, nombre_provincia, "Estadísticas por año")
    return fig

def graficar_barras_agrupadas(df_estadisticas: pd.DataFrame, clave_metrica: str, nombre_provincia: str) -> go.Figure:
    """
    Genera un gráfico de barras agrupadas para comparación directa.
    """
    cfg = metricas[clave_metrica]
    nombre_metrica = cfg["nombre"]
    unidad = cfg["unidad"]
    fig = go.Figure()

    df_estadisticas["mes_nombre"] = df_estadisticas["mes"].map(meses)

    colores = ['royalblue', 'crimson']
    for i, anio in enumerate(sorted(df_estadisticas["anio"].unique())):
        datos_anio = df_estadisticas[df_estadisticas["anio"] == anio]
        fig.add_trace(go.Bar(
            x = datos_anio["mes_nombre"],
            y = datos_anio["media"].round(2),
            name = str(anio),
            marker_color = colores[i % len(colores)]
        ))

    configurar_figura(fig, f"Media de {nombre_metrica}", unidad, nombre_provincia, "Año")
    fig.update_layout(barmode = 'group')
    return fig

def graficar_cajas(df_sin_procesar: pd.DataFrame, clave_metrica: str, nombre_provincia: str) -> go.Figure:
    """
    Genera un gráfico de cajas (box plot) para ver la distribución.
    """
    cfg = metricas[clave_metrica]
    nombre_metrica = cfg["nombre"]
    unidad = cfg["unidad"]
    fig = go.Figure()

    df_sin_procesar["fecha"] = pd.to_datetime(df_sin_procesar["fecha"])
    df_sin_procesar["anio"] = df_sin_procesar["fecha"].dt.year
    df_sin_procesar["mes_nombre"] = df_sin_procesar["fecha"].dt.month.map(meses)

    colores = ['royalblue', 'crimson']
    for i, anio in enumerate(sorted(df_sin_procesar["anio"].unique())):
        datos_anio = df_sin_procesar[df_sin_procesar["anio"] == anio]
        fig.add_trace(go.Box(
            y = datos_anio[clave_metrica],
            x = datos_anio["mes_nombre"],
            name = str(anio),
            marker_color = colores[i % len(colores)]
        ))

    configurar_figura(fig, f"Distribución de {nombre_metrica}", unidad, nombre_provincia, "Año")
    fig.update_layout(boxmode = 'group')
    return fig

def mostrar_comparador(df_provincias: pd.DataFrame):
    st.title("📊 Comparador anual de métricas meteorológicas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
            provincia = st.selectbox("Selecciona una provincia", df_provincias["nombre_prov"])
            codigo_prov = df_provincias[df_provincias["nombre_prov"] == provincia]["codigo_prov"].values[0]

    with col2:
        clave_metrica = st.selectbox(
            "Métrica a comparar",
            options = list(metricas.keys()),
            format_func = lambda k: metricas[k]["nombre"]        )

    with col3:
        anios_disponibles = obtener_anios_disponibles()

        anios_sel = st.multiselect("Selecciona dos años a comparar", anios_disponibles, default = anios_disponibles[:2])
        if len(anios_sel) != 2:
            st.warning("Selecciona exactamente dos años.")
            return
    
    st.divider()
    
    tipo_grafica = st.radio(
        "Selecciona el tipo de gráfica:",
        ["Líneas (Tendencia)", "Barras (Comparación)", "Cajas (Distribución)"],
        horizontal = True, key = "tipo_grafica"
        )

    st.html("<center>ℹ️ Puedes cerrar los menús desplegables haciendo clic fuera sin seleccionar más opciones.</center>")

    st.html("<center>💡 <strong>Consejo:</strong> puedes activar o desactivar opciones en la gráfica haciendo clic sobre las etiquetas en la leyenda.</center>")


    with st.spinner("Consultando datos..."):
        df_meteo = cargar_meteo_filtrada(
            codigo_prov, anios_sel, columnas = ["fecha", "codigo_prov", clave_metrica]
)

    if df_meteo.empty:
        st.warning("No se encontraron datos para esa provincia y años.")
        return

    if tipo_grafica == "Líneas (Tendencia)":
        df_stats = calcular_estadisticas_por_mes(df_meteo, clave_metrica)
        fig = graficar_lineas(df_stats, clave_metrica, provincia)
    elif tipo_grafica == "Barras (Comparación)":
        df_stats = calcular_estadisticas_por_mes(df_meteo, clave_metrica)
        fig = graficar_barras_agrupadas(df_stats, clave_metrica, provincia)
    elif tipo_grafica == "Cajas (Distribución)":
        fig = graficar_cajas(df_meteo, clave_metrica, provincia)

    st.plotly_chart(fig, use_container_width = True)



def main():
    
    mostrar_comparador(df_provincias)
    
    
    st.divider()
    if st.button("Volver a Inicio", key = "volver_inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    main()