import pandas as pd
import streamlit as st
from datetime import date
from src.extraer_datos import ejecutar_consulta_a_dataframe

from src import conectar 

def main():
    conexion = conectar.conexion()

    st.title("Datos meteorológicos filtrados")
    st.divider()

    df_provincias = pd.read_sql_table("provincias", conexion)
    df_comunidades = pd.read_sql_table("comunidades", conexion)

    col1, col2, col3 = st.columns(3)
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
    st.sidebar.divider()

    # if opcion_provincia:
    #     st.sidebar.write(opcion_provincia)
    #     st.dataframe(df_provincias[df_provincias["nombre"].isin(opcion_provincia)], hide_index=True)

    with st.spinner("Cargando datos históricos... Por favor, espera."):
        
        df = ejecutar_consulta_a_dataframe()

    if fecha and len(fecha) == 2:
        parametros = {
            "fecha_inicio": fecha[0],
            "fecha_fin": fecha[1]
            }
        df = ejecutar_consulta_a_dataframe(params=parametros)

    elif fecha and len(fecha) == 1:
        parametros = {
            "fecha": fecha[0],
            }
        df = ejecutar_consulta_a_dataframe(params=parametros)
    else:
        st.write("No se ha seleccionado ninguna fecha.")

    if opcion_provincia:
        df = df[df["nombre"].isin(opcion_provincia)]
        
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


if __name__ == "__main__":
    main()

