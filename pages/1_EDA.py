from datetime import date
import pandas as pd
import streamlit as st
from sqlalchemy import func, bindparam, Float


from src.extraer_datos import (
    construir_consulta_general, ejecutar_consulta_a_dataframe,
    df_provincias, df_comunidades, tabla_dm
)
from src.coroplet import dibujar_coropletico_plotly
from src.personalizacion import load_css

st.set_page_config(
    page_title="EDA",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
    )
load_css('src/estilos.css')

with st.sidebar:
    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

st.title("Datos meteorológicos filtrados")
st.divider()

velocidad = func.round(func.avg(tabla_dm.c.racha).cast(Float) * 3.6, 2)
metricas_disponibles = {
    "Altitud media (m)": {"col": "altitud", "expr": func.avg(tabla_dm.c.altitud), "unidad": "m"},
    "Temp. media (ºC)": {"col": "tmed", "expr": func.avg(tabla_dm.c.tmed), "unidad": "ºC"},
    "Temp. mínima (ºC)": {"col": "tmin", "expr": func.avg(tabla_dm.c.tmin), "unidad": "ºC"},
    "Temp. máxima (ºC)": {"col": "tmax", "expr": func.avg(tabla_dm.c.tmax), "unidad": "ºC"},
    "Precip. media (mm)": {"col": "prec", "expr": func.avg(tabla_dm.c.prec), "unidad": "mm"},
    "Racha media (km/h)": {"col": "racha", "expr": velocidad, "unidad": "km/h"},
    "Humedad media (%)": {"col": "hrMedia", "expr": func.avg(tabla_dm.c.hrMedia), "unidad": "%"},
}
columnas_agregadas = [
                v["expr"].label(v["col"]) for v in metricas_disponibles.values()
                ]

columnas_st = {
    v["col"]: st.column_config.NumberColumn(label=k, format="%.2f", help=v["unidad"])
    for k, v in metricas_disponibles.items()
}

metricas_orden = [v["col"] for v in metricas_disponibles.values()]

def generar_df_cache(clave_df, clave_params, stmt_conf, **params):
    """
    Devuelve un DataFrame ejecutando una consulta si no hay cache o cambian los parámetros.

    - clave_df: nombre para guardar el DataFrame en session_state
    - clave_params: nombre para guardar los parámetros previos
    - stmt_conf: configuración de la consulta SQL
    - params: parámetros como fecha_inicio, fecha_fin, etc.
    """
    if clave_df not in st.session_state or st.session_state.get(clave_params) != params:
        consulta = construir_consulta_general(stmt_conf)
        st.write(f"Ejecutando consulta SQL para '{clave_df}' con parámetros:", params)
        df = ejecutar_consulta_a_dataframe(consulta, **params)
        st.session_state[clave_df] = df
        st.session_state[clave_params] = params
    else:
        st.write(f"Usando cache para '{clave_df}'")

    return st.session_state[clave_df]

def mostrar_tab_territorial(nivel: str):
    """
    nivel: 'provincia' o 'ccaa'
    """
    assert nivel in ("provincia", "ccaa"), "Nivel territorial inválido"

    # Widgets comunes
    col1, col2, col3 = st.columns(3)
    with col1:
        fechas = st.date_input(
            "Selecciona un rango de fechas:",
            value=(date(2023, 5, 29), date(2025, 5, 28)),
            min_value=date(2023, 5, 29),
            max_value=date(2025, 5, 28),
            format="DD/MM/YYYY",
            key=f"fecha_{nivel}"
        )

    with col3:
        metrica = st.selectbox("Métrica a visualizar:", list(metricas_disponibles.keys()), key=f"metrica_{nivel}")
        metrica_conf = metricas_disponibles[metrica]
        columna = metrica_conf["col"]

    if nivel == "provincia":
        with col2:
            filtro = st.multiselect("Elige la provincia:", df_provincias["nombre_prov"], placeholder="Opcional")
    else:
        with col2:
            filtro = st.multiselect("Elige la comunidad:", df_comunidades["nombre_ccaa"], placeholder="Opcional")

    if fechas and len(fechas) == 2:
        params = {"fecha_inicio": fechas[0], "fecha_fin": fechas[1]}
        stmt = {
            "select": [tabla_dm.c.codigo_prov, *columnas_agregadas],
            "join": ["provincia"],
            "filters": [tabla_dm.c.fecha.between(bindparam("fecha_inicio"), bindparam("fecha_fin"))],
            "group_by": [tabla_dm.c.codigo_prov]
        }

        # Cache independiente por nivel
        cache_df_key = f"df_{nivel}"
        cache_params_key = f"{nivel}_params"
        df = generar_df_cache(cache_df_key, cache_params_key, stmt, **params)

        if not df.empty:
            df = df.merge(df_provincias[["codigo_prov", "nombre_prov", "codigo_ca"]], on="codigo_prov")

            if nivel == "ccaa":
                df = df.merge(df_comunidades[["codigo_ca", "nombre_ccaa"]], on="codigo_ca")

            # Asegurar racha como numérico
            if "racha" in df.columns:
                df["racha"] = pd.to_numeric(df["racha"], errors="coerce")

            # Aplicar filtros
            if nivel == "provincia" and filtro:
                df = df[df["nombre_prov"].isin(filtro)]
            elif nivel == "ccaa" and filtro:
                df = df[df["nombre_ccaa"].isin(filtro)]

            # Agregación para comunidades
            if nivel == "ccaa":
                columnas = [col for col in metricas_orden if col in df.columns]
                df = df.groupby(["codigo_ca", "nombre_ccaa"], as_index=False)[columnas].mean()
                df = df.rename(columns={"codigo_ca": "cod_ccaa"})
                nombre_col = "nombre_ccaa"
                cod_col = "cod_ccaa"
            else:
                nombre_col = "nombre_prov"
                cod_col = "codigo_prov"
                columnas = [col for col in metricas_orden if col in df.columns]

            # Ordenar
            df = df.sort_values(by=columna, ascending=False)
            df = df[[nombre_col, cod_col] + columnas]
            st.write(df_comunidades["nombre_ccaa"])

            st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                nombre_col: st.column_config.TextColumn("Nombre de la comunidad"),
                cod_col: None,
                **columnas_st
            })

            # Mapa
            titulo = f"{metrica} por {nivel} del {fechas[0].strftime('%d/%m/%Y')} al {fechas[1].strftime('%d/%m/%Y')}"
            cache_fig_key = f"fig_{nivel}"
            cache_fig_params_key = f"{nivel}_fig_params"

            filtro_id = tuple(sorted(filtro)) if isinstance(filtro, list) else filtro or ""
            params_fig = (columna, titulo, filtro_id)

            if cache_fig_key not in st.session_state or st.session_state.get(cache_fig_params_key) != params_fig:
                

                fig = dibujar_coropletico_plotly(df, columna, titulo, nivel=nivel)
                st.session_state[cache_fig_key] = fig
                st.session_state[cache_fig_params_key] = params_fig
            
            st.spinner("Cargando mapa...")
            st.write(f"Mostrando {len(df)} registros tras filtros.")
            st.plotly_chart(st.session_state[cache_fig_key], use_container_width=True)


def main():
    tabs = st.tabs(["Por provincias", "Por comunidades autónomas"])
    with tabs[0]:
        mostrar_tab_territorial("provincia")
    with tabs[1]:
        mostrar_tab_territorial("ccaa")

    st.divider()
    if st.button("Volver a Inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    
    main()
