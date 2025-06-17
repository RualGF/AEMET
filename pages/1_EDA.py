import pandas as pd
import streamlit as st
from datetime import date

from src.extraer_datos import ejecutar_consulta_a_dataframe
from src.coroplet import dibujar_coropletico_plotly
from src import conectar
from src.personalizacion import load_css

st.set_page_config(
    page_title="Proyecto Grupo D",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    conexion = conectar.conexion()
    load_css('src/estilos.css')

    st.title("Datos meteorológicos filtrados")
    st.divider()

    df_provincias = pd.read_sql_table("provincias", conexion)
    df_comunidades = pd.read_sql_table("comunidades", conexion)

    tab_provincias, tab_ccaa = st.tabs(["Por provincias", "Por comunidades autónomas"])

    metricas_disponibles = {
        "Altitud media (m)": {"original_col": "AVG(d.altitud)", "new_col": "altitud", "unidad": "m"},
        "Temp. media (ºC)": {"original_col": "AVG(d.tmed)", "new_col": "tmed", "unidad": "ºC"},
        "Temp. mínima (ºC)": {"original_col": "AVG(d.tmin)", "new_col": "tmin", "unidad": "ºC"},
        "Temp. máxima (ºC)": {"original_col": "AVG(d.tmax)", "new_col": "tmax", "unidad": "ºC"},
        "Precip. media (mm)": {"original_col": "AVG(d.prec)", "new_col": "prec", "unidad": "mm"},
        "Racha media (km/h)": {"original_col": "AVG(d.racha) * 3.6", "new_col": "racha", "unidad": "km/h"},
        "Humedad media (%)": {"original_col": "AVG(d.hrMedia)", "new_col": "hrMedia", "unidad": "%"},
    }
    
    columnas_st={
        "altitud": st.column_config.NumberColumn(label="Altitud media (m)", format="%.2f",),
        "tmed": st.column_config.NumberColumn(label="Temp. media (ºC)", format="%.2f", help="Temperatura media"),
        "tmin": st.column_config.NumberColumn(label="Temp. mínima (ºC)", format="%.2f", help="Temperatura mínima"),
        "tmax": st.column_config.NumberColumn(label="Temp. máxima (ºC)", format="%.2f", help="Temperatura máxima"),
        "prec": st.column_config.NumberColumn(label="Precip. media (mm)", format="%.2f", help="Precipitación media"),
        "racha": st.column_config.NumberColumn(label="Racha media (km/h)", format="%.2f", help="Velocidad media del viento"),
        "hrMedia": st.column_config.NumberColumn(label="Humedad media (%)", format="%.2f", help="Humedad relativa media")
    } 

    with tab_provincias:
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_prov = st.date_input(
                "Selecciona una fecha:",
                value=(date(2023, 5, 29), date(2025, 5, 28)),
                min_value=date(2023, 5, 29),
                max_value=date(2025, 5, 28),
                format="DD/MM/YYYY",
                key="fecha_prov"
            )
        with col2:
            opcion_provincia = st.multiselect(
                "Elige la provincia:",
                df_provincias["nombre"],
                default=None,
                placeholder="Elige las provincias que quieras ver"
            )
        with col3:
            metrica_seleccionada = st.selectbox(
                "Selecciona la métrica a visualizar en el mapa:",
                metricas_disponibles,
                index=0
            )

        if fecha_prov and len(fecha_prov) == 2:
            parametros = {"fecha_inicio": fecha_prov[0], "fecha_fin": fecha_prov[1]}
            
            if 'df_prov' not in st.session_state or st.session_state['prov_params'] != parametros:
                if 'df_ccaa' not in st.session_state or st.session_state['ccaa_params'] != parametros:
                    df = ejecutar_consulta_a_dataframe(params=parametros)
                    st.session_state['df_ccaa'] = df
                    st.session_state['ccaa_params'] = parametros
                else:
                    df = st.session_state['df_ccaa']
                    st.session_state['df_prov'] = df
                    st.session_state['prov_params'] = parametros
            else:
                df = st.session_state['df_prov']
            
            fecha_inicio_str = fecha_prov[0].strftime("%d/%m/%Y")
            fecha_fin_str = fecha_prov[1].strftime("%d/%m/%Y")
            titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada desde {fecha_inicio_str} hasta {fecha_fin_str}"
        
        elif fecha_prov:
            parametros = {"fecha": fecha_prov[0]}
            if 'df_prov' not in st.session_state or st.session_state['prov_params'] != parametros:
                if 'df_ccaa' not in st.session_state or st.session_state['ccaa_params'] != parametros:
                    df = ejecutar_consulta_a_dataframe(params=parametros)
                    st.session_state['df_ccaa'] = df
                    st.session_state['ccaa_params'] = parametros
                else:
                    df = st.session_state['df_ccaa']
                    st.session_state['df_prov'] = df
                    st.session_state['prov_params'] = parametros
            else:
                df = st.session_state['df_prov']
            fecha_str = fecha_prov[0].strftime("%d/%m/%Y")
            titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada en {fecha_str}"
        else:
            st.write("No se ha seleccionado ninguna fecha.")
            df = pd.DataFrame()
            titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada"

        if not df.empty:
            df = df.rename(columns={v["original_col"]: v["new_col"] for v in metricas_disponibles.values()})
            columna_seleccionada = metricas_disponibles[metrica_seleccionada]["new_col"]
            
            if opcion_provincia:
                df = df[df["nombre"].isin(opcion_provincia)]
            
            df = df.sort_values(by=columna_seleccionada, ascending=False)

            st.dataframe(df, hide_index=True, use_container_width=True, column_config=
                         {"nombre": st.column_config.TextColumn("Nombre de la provincia"),
                        "codigo_prov": None,
                        **columnas_st})
            with st.spinner("Generando el mapa..."):
                if 'fig_prov' not in st.session_state or st.session_state['prov_fig_params'] != (columna_seleccionada, titulo_mapa):
                    fig = dibujar_coropletico_plotly(df, columna_seleccionada, titulo_mapa, nivel="provincias")
                    st.session_state['fig_prov'] = fig
                    st.session_state['prov_fig_params'] = (columna_seleccionada, titulo_mapa)
                else:
                    fig = st.session_state['fig_prov']
            st.plotly_chart(fig, use_container_width=True)

    with tab_ccaa:
        col4, col5, col6 = st.columns(3)
        with col4:
            fecha_ccaa = st.date_input(
                "Selecciona una fecha:",
                value=(date(2023, 5, 29), date(2025, 5, 28)),
                min_value=date(2023, 5, 29),
                max_value=date(2025, 5, 28),
                format="DD/MM/YYYY",
                key="fecha_ccaa"
            )
        with col5:
            opcion_comunidad = st.selectbox(
                "Elige la comunidad:",
                df_comunidades["nombre"],
                index=None,
                placeholder="Elige una comunidad"
            )
        with col6:
            metrica_seleccionada = st.selectbox(
                "Selecciona la métrica a visualizar en el mapa:",
                metricas_disponibles,
                index=0,
                key='select_metrica_ccaa'
            )

        if fecha_ccaa and len(fecha_ccaa) == 2:
            parametros = {"fecha_inicio": fecha_ccaa[0], "fecha_fin": fecha_ccaa[1]}
            if 'df_ccaa' not in st.session_state or st.session_state['ccaa_params'] != parametros:
                df = ejecutar_consulta_a_dataframe(params=parametros)
                st.session_state['df_ccaa'] = df
                st.session_state['ccaa_params'] = parametros
            else:
                 df = st.session_state['df_ccaa']
            fecha_inicio_str = fecha_ccaa[0].strftime("%d/%m/%Y")
            fecha_fin_str = fecha_ccaa[1].strftime("%d/%m/%Y")
            titulo_mapa = f"Promedio de {metrica_seleccionada} por comunidad autónoma seleccionada desde {fecha_inicio_str} hasta {fecha_fin_str}"
        
        elif fecha_ccaa:
            parametros = {"fecha": fecha_ccaa[0]}
            
            if 'df_ccaa' not in st.session_state or st.session_state['ccaa_params'] != parametros:
                df = ejecutar_consulta_a_dataframe(params=parametros)
                st.session_state['df_ccaa'] = df
                st.session_state['ccaa_params'] = parametros
            else:
                 df = st.session_state['df_ccaa']
            fecha_str = fecha_ccaa[0].strftime("%d/%m/%Y")
            titulo_mapa = f"Promedio de {metrica_seleccionada} por comunidad autónoma seleccionada en {fecha_str}"
        else:
            st.write("No se ha seleccionado ninguna fecha.")
            df = pd.DataFrame()
            titulo_mapa = f"Promedio de {metrica_seleccionada} por comunidad autónoma seleccionada"

        if not df.empty:
            df = df.rename(columns={v["original_col"]: v["new_col"] for v in metricas_disponibles.values()})
            columna_seleccionada = metricas_disponibles[metrica_seleccionada]["new_col"]

            df_ccaa = df.merge(df_provincias[["codigo_prov", "codigo_ca"]], on="codigo_prov", how="left")
            df_ccaa = df_ccaa.drop(columns=["nombre"])
            
            df_ccaa = df_ccaa.merge(df_comunidades[["codigo_ca", "nombre"]], on="codigo_ca", how="left")
            

            # if opcion_comunidad:
                # codigo_seleccionado = df_comunidades[df_comunidades["nombre"] == opcion_comunidad]["codigo_ca"].iloc[0]
                # df_ccaa = df_ccaa[df_ccaa["codigo_ca"] == codigo_seleccionado]

            columnas_agrupables = [v['new_col'] for v in metricas_disponibles.values() if v['new_col'] in df_ccaa.columns]
            df_ccaa = df_ccaa.groupby(["codigo_ca", "nombre"], as_index=False)[columnas_agrupables].mean()
            
            
            df_ccaa = df_ccaa[["nombre"] + [col for col in df_ccaa.columns if col not in ["nombre"]]]

            df_ccaa = df_ccaa.sort_values(by=columna_seleccionada, ascending=False)
            
            st.dataframe(df_ccaa, hide_index=True, use_container_width=True, column_config=
                         {"nombre": st.column_config.TextColumn("Nombre de la comunidad autónoma"),
                        "codigo_ca": None,
                        **columnas_st})
            
            with st.spinner("Generando el mapa..."):
                df_ccaa = df_ccaa.rename(columns={"codigo_ca": "cod_ccaa"})
                
                if 'fig_ccaa' not in st.session_state or st.session_state['ccaa_fig_params'] != (columna_seleccionada, titulo_mapa):
                    fig = dibujar_coropletico_plotly(df_ccaa, columna_seleccionada, titulo_mapa, nivel="ccaa")
                    st.session_state['fig_ccaa'] = fig
                    st.session_state['ccaa_fig_params'] = (columna_seleccionada, titulo_mapa)
                else:
                    fig = st.session_state['fig_ccaa']
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    if st.button("Volver a Inicio", key="volver_inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    main()
