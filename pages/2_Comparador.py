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

st.set_page_config(
    page_title="Comparador",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
    )

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

def obtener_anios_disponibles():
    stmt = select(func.year(tabla_dm.c.fecha).label("anio")).distinct().order_by("anio")
    df = ejecutar_consulta_a_dataframe(stmt)
    return sorted(df["anio"].dropna().astype(int).tolist())

def cargar_meteo_filtrada_sqlalchemy(codigo_prov: str, anios: list, columnas=None):
    columnas = columnas or ["fecha", "codigo_prov", "tmed", "tmin", "tmax", "prec", "hrMedia", "racha"]

    filtros = [
        tabla_dm.c.codigo_prov == bindparam("codigo_prov"),
        extract("year", tabla_dm.c.fecha).in_(bindparam("anios", expanding=True))
    ]

    stmt = construir_consulta_general({
        "select": [tabla_dm.c[col] for col in columnas],
        "filters": filtros,
        "order_by": [tabla_dm.c.fecha]
    })

    return ejecutar_consulta_a_dataframe(stmt, codigo_prov=codigo_prov, anios=anios)

def calcular_estadisticas_por_mes(df, columna_valor):
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    estadisticas = df.groupby(["anio", "mes"])[columna_valor].agg(
        media="mean",
        mediana="median",
        minimo="min",
        maximo="max"
    ).reset_index()

    return estadisticas

def graficar_comparador(df_estadisticas, clave_metrica, nombre_provincia):
    cfg = metricas[clave_metrica]
    nombre_metrica = cfg["nombre"]
    unidad = cfg["unidad"]

    visibles = ["media", "mediana", "minimo", "maximo"]

    fig = go.Figure()
    colores = {
        "media": "royalblue",
        "mediana": "orange",
        "minimo": "lightgreen",
        "maximo": "crimson"
    }

    # Mapeo de meses
    meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    df_estadisticas["mes_nombre"] = df_estadisticas["mes"].map(meses)

    for anio in sorted(df_estadisticas["anio"].unique()):
        datos_anio = df_estadisticas[df_estadisticas["anio"] == anio]
        for estadistica in visibles:
            fig.add_trace(go.Scatter(
                x=datos_anio["mes_nombre"],
                y=datos_anio[estadistica].round(2),
                mode="lines+markers",
                name=f"{estadistica.capitalize()} {anio}",
                line=dict(
                    color=colores[estadistica],
                    dash="solid" if anio == min(df_estadisticas["anio"]) else "dot"
                )
            ))

    fig.update_layout(
        title=dict(
            text=f"{nombre_metrica} mensual en {nombre_provincia} ({unidad})",
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis=dict(title=dict(text="Mes", font=dict(size=16)), tickfont=dict(size=14)),
        yaxis=dict(title=dict(text=f"{nombre_metrica} ({unidad})", font=dict(size=16)), tickfont=dict(size=14)),
        legend_title="Estadísticas por año",
        legend=dict(font=dict(size=14)),
        height=600,
        template="plotly_white"
    )

    return fig



def mostrar_comparador(df_provincias):
    st.title("📊 Comparador anual de métricas meteorológicas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
            provincia = st.selectbox("Selecciona una provincia", df_provincias["nombre_prov"])
            codigo_prov = df_provincias[df_provincias["nombre_prov"] == provincia]["codigo_prov"].values[0]

    with col2:
        clave_metrica = st.selectbox(
            "Métrica a comparar",
            options=list(metricas.keys()),
            format_func=lambda k: metricas[k]["nombre"]
        )

    with col3:
        anios_disponibles = obtener_anios_disponibles()

        anios_sel = st.multiselect("Selecciona dos años a comparar", anios_disponibles, default=anios_disponibles[:2])
        if len(anios_sel) != 2:
            st.warning("Selecciona exactamente dos años.")
            return
    

    st.html("<center>ℹ️ Puedes cerrar los menús desplegables haciendo clic fuera sin seleccionar más opciones.</center>")

    st.html("<center>💡 <strong>Consejo:</strong> puedes activar o desactivar líneas en la gráfica haciendo clic sobre las etiquetas en la leyenda.</center>")


    with st.spinner("Consultando datos..."):
        df_meteo = cargar_meteo_filtrada_sqlalchemy(
            codigo_prov, anios_sel, columnas=["fecha", "codigo_prov", clave_metrica]
)

    if df_meteo.empty:
        st.warning("No se encontraron datos para esa provincia y años.")
        return

    df_stats = calcular_estadisticas_por_mes(df_meteo, clave_metrica)
    fig = graficar_comparador(df_stats, clave_metrica, provincia)

    st.plotly_chart(fig, use_container_width=True)




def main():
    load_css('src/estilos.css')
    
    mostrar_comparador(df_provincias)

    # Agregar Botón de inicio
    st.divider()
    if st.button("Volver a Inicio", key="volver_inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    main()