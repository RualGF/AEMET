import streamlit as st


def main():
    #conexion = conectar.conexion()


    st.set_page_config(
    page_title="Bienvenido",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

    st.title("🌤️ Bienvenido al Dashboard Meteorológico")
    st.markdown(
        """
        Este proyecto recopila, procesa y visualiza datos meteorológicos de AEMET.
        - **Fuente**: API de AEMET (temperaturas, precipitaciones, viento, humedad).
        - **Funcionalidad**: Extracción incremental, limpieza, almacenamiento en base de datos.
        - **Datos**: Guardados en `datos_meteorologicos` y CSVs.

        **Navega usando el menú lateral**:
        - **Datos Históricos**: Ver todos los datos meteorológicos.
        - **Datos Filtrados**: Filtrar datos por provincia, fecha, etc.
        - **Predicciones**: Visualizar predicciones meteorológicas.
        """
    )


if __name__ == "__main__":
    main()

