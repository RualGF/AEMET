import pandas as pd
import streamlit as st
from datetime import date

from src.extraer_datos import ejecutar_consulta_a_dataframe
from src.coroplet import dibujar_coropletico, dibujar_coropletico_plotly
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fecha = st.date_input(
            "Selecciona una fecha:",
            value=(date(2023, 5, 29), date(2025, 5, 28)),
            min_value=date(2023, 5, 29),
            max_value=date(2025, 5, 28),
            format="DD/MM/YYYY"
            )
    #    st.write_stream(fecha)
    
    with col2:    
        opcion_comunidad = st.selectbox(
            "Elige la comunidad: ",
            df_comunidades["nombre"],
            index=None,
            placeholder="Elige una comunidad",
            #format_func=lambda x: "Selecciona una comunidad..." if x == "" else x
            )

    with col3:
        if opcion_comunidad:
            comunidad_elegida = df_comunidades[df_comunidades["nombre"] == opcion_comunidad]

            provincias_filtradas = df_provincias[df_provincias["codigo_ca"] == comunidad_elegida["codigo_ca"].iloc[0]]
            opcion_provincia = st.multiselect(
                "Elige la provincia: ",
                provincias_filtradas["nombre"],
                default=None,
                placeholder="Elige las provincias que quieras ver"
            )
        else:
            #opcion_elegida = None
            opcion_provincia = st.multiselect(
                "Elige la provincia: ",
                df_provincias["nombre"],
                default=None,
                placeholder="Elige las provincias que quieras ver"
                )
    
       # if opcion_provincia:
    #     st.sidebar.write(opcion_provincia)
    #     st.dataframe(df_provincias[df_provincias["nombre"].isin(opcion_provincia)], hide_index=True)

    with st.spinner("Cargando datos históricos... Por favor, espera."):
        
        df = ejecutar_consulta_a_dataframe()
    
    with col4:
        metricas_disponibles = {
            "Altitud media (m)": {"original_col": "AVG(d.altitud)", "new_col": "altitud", "unidad": "m"},
            "Temp. media (ºC)": {"original_col": "AVG(d.tmed)", "new_col": "tmed", "unidad": "ºC"},
            "Temp. mínima (ºC)": {"original_col": "AVG(d.tmin)", "new_col": "tmin", "unidad": "ºC"},
            "Temp. máxima (ºC)": {"original_col": "AVG(d.tmax)", "new_col": "tmax", "unidad": "ºC"},
            "Precip. media (mm)": {"original_col": "AVG(d.prec)", "new_col": "prec", "unidad": "mm"},
            "Racha media (km/h)": {"original_col": "AVG(d.racha) * 3.6", "new_col": "racha", "unidad": "km/h"},
            "Humedad media (%)": {"original_col": "AVG(d.hrMedia)", "new_col": "hrMedia", "unidad": "%"},
        }
        metrica_seleccionada = st.selectbox(
            "Selecciona la métrica a visualizar en el mapa:",
            metricas_disponibles,
            index=0 # Por defecto selecciona la primera métrica
        )

    if fecha and len(fecha) == 2:
        parametros = {
            "fecha_inicio": fecha[0],
            "fecha_fin": fecha[1]
            }
        df = ejecutar_consulta_a_dataframe(params=parametros)
        fecha_inicio_str = fecha[0].strftime("%d/%m/%Y")
        fecha_fin_str = fecha[1].strftime("%d/%m/%Y")
        titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada desde {fecha_inicio_str} hasta {fecha_fin_str}"

    elif fecha and len(fecha) == 1:
        parametros = {
            "fecha": fecha[0],
            }
        df = ejecutar_consulta_a_dataframe(params=parametros)
        fecha_str = fecha[0].strftime("%d/%m/%Y")
        titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada en {fecha_str}"
    else:
        st.write("No se ha seleccionado ninguna fecha.")
        titulo_mapa = f"Promedio de {metrica_seleccionada} por provincia seleccionada"

    if opcion_provincia:
        df = df[df["nombre"].isin(opcion_provincia)]

    
    st.divider()

    st.dataframe(df, hide_index=True, use_container_width=True, column_config={
        "nombre": st.column_config.TextColumn("Nombre de la provincia"),
        "codigo_prov": None,
        "AVG(d.altitud)": st.column_config.NumberColumn(label="Altitud media (m)", format="%.2f",),
        "AVG(d.tmed)": st.column_config.NumberColumn(label="Temp. media (ºC)", format="%.2f", help="Temperatura media"),
        "AVG(d.tmin)": st.column_config.NumberColumn(label="Temp. mínima (ºC)", format="%.2f", help="Temperatura mínima"),
        "AVG(d.tmax)": st.column_config.NumberColumn(label="Temp. máxima (ºC)", format="%.2f", help="Temperatura máxima"),
        "AVG(d.prec)": st.column_config.NumberColumn(label="Precip. media (mm)", format="%.2f", help="Precipitación media"),
        "AVG(d.racha) * 3.6": st.column_config.NumberColumn(label="Racha media (km/h)", format="%.2f", help="Velocidad media del viento"),
        "AVG(d.hrMedia)": st.column_config.NumberColumn(label="Humedad media (%)", format="%.2f", help="Humedad relativa media")
    } )

    st.divider()

    if metrica_seleccionada:
        
    # Construir diccionario {columna_original: nueva_columna} para renombrar
        renombrar_columnas = {
        v["original_col"]: v["new_col"]
        for v in metricas_disponibles.values()
        }
        # Renombrar todas las columnas en el DataFrame
        
        df = df.rename(columns=renombrar_columnas)

        columna_seleccionada = metricas_disponibles[metrica_seleccionada]["new_col"]
        
        fig = dibujar_coropletico(
            df,
            columna_seleccionada,
            titulo_mapa,
            f"{metrica_seleccionada}" # Etiqueta de la leyenda
        )
        st.pyplot(fig, use_container_width=True) # Muestra la figura de Matplotlib en Streamlit
        
        # fig_px = dibujar_coropletico_plotly(
        #     df,
        #     columna_seleccionada,
        #     titulo_mapa,
        #     f"{metrica_seleccionada}"
        # )
        # st.plotly_chart(fig_px, use_container_width=True) # Muestra la figura de Plotly en Streamlit
    else:
        st.info("Selecciona una métrica para mostrar el mapa.")

    # Agregar Botón de inicio
    st.divider()
    if st.button("Volver a Inicio", key="volver_inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    main()

