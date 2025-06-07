import pandas as pd
import streamlit as st


from src import conectar 

def main():
    conexion = conectar.conexion()

    st.title("Datos históricos de la AEMET")
    st.divider()

    with st.spinner("Cargando datos históricos... Por favor, espera."):
        
        consulta = """
            SELECT p.nombre, 
            d.codigo_prov,
            AVG(d.altitud), 
            AVG(d.tmed),
            AVG(d.tmin),
            AVG(d.tmax),
            AVG(d.prec),
            AVG(d.racha) * 3.6,
            AVG(d.hrMedia)
            FROM datos_meteorologicos as d, provincias as p
            WHERE d.codigo_prov = p.codigo_prov
            GROUP BY codigo_prov ; 
            """
        df = pd.read_sql_query(consulta, con = conexion)   
        #df.style.format(na_rep="Sin datos", decimal=",", thousands=".", precision=2) 
        st.divider()
     
    st.dataframe(df, hide_index=True, use_container_width=True, column_config={
        "nombre": st.column_config.TextColumn("Nombre de la provincia"),
        "codigo_prov": None,
        "AVG(d.altitud)": st.column_config.NumberColumn(label="Altitud media (m)", format="%.2f"),
        "AVG(d.tmed)": st.column_config.NumberColumn(label="Temp. media (ºC)", format="%.2f", help="Temperatura media"),
        "AVG(d.tmin)": st.column_config.NumberColumn(label="Temp. mínima (ºC)", format="%.2f", help="Temperatura mínima"),
        "AVG(d.tmax)": st.column_config.NumberColumn(label="Temp. máxima (ºC)", format="%.2f", help="Temperatura máxima"),
        "AVG(d.prec)": st.column_config.NumberColumn(label="Precip. media (mm)", format="%.2f", help="Precipitación media"),
        "AVG(d.racha) * 3.6": st.column_config.NumberColumn(label="Racha media (km/h)", format="%.2f", help="Velocidad media del viento"),
        "AVG(d.hrMedia)": st.column_config.NumberColumn(label="Humedad media (%)", format="%.2f", help="Humedad relativa media")
    } )
if __name__ == "__main__":
    main()