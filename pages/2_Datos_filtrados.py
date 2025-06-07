import pandas as pd
import streamlit as st
from datetime import date


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
        st.write_stream(fecha)
    
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
            opcion_elegida = st.multiselect(
                "Elige la provincia: ",
                provincias_filtradas["nombre"],
                default=None,
                placeholder="Elige las provincias que quieras ver"
            )
        else:
            #opcion_elegida = None
            opcion_elegida = st.multiselect(
                "Elige la provincia: ",
                df_provincias["nombre"],
                default=None,
                placeholder="Elige las provincias que quieras ver"
                )
    st.sidebar.divider()

    if opcion_elegida:
        st.sidebar.write(opcion_elegida)
        st.dataframe(df_provincias[df_provincias["nombre"].isin(opcion_elegida)], hide_index=True)

if __name__ == "__main__":
    main()

