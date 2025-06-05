import pandas as pd
import streamlit as st


from src import conectar 

def main():
    conexion = conectar.conexion()

    st.title("Datos históricos de la AEMET")
    st.divider()

    with st.spinner("Cargando datos históricos... Por favor, espera."):
        df = pd.read_sql_query(
            "SELECT provincia, " \
            "AVG(altitud) AS 'Altitud media (m)', " \
            "AVG(tmed) AS 'Temperatura media (ºC)', " \
            "AVG(tmin) AS 'Temperatura mínima (ºC)', " \
            "AVG(tmax) AS 'Temperatura máxima (ºC)', " \
            "AVG(prec) AS 'Precipitación (mm)', " \
            "AVG(racha) AS 'Velocidad del viento (km/h)', " \
            "AVG(hrMedia) AS 'Humedad relativa media' " \
            "FROM datos_meteorologicos_table " \
            "GROUP BY provincia", 
            con = conexion)
    
    st.dataframe(df, hide_index=True, use_container_width=True)
if __name__ == "__main__":
    main()