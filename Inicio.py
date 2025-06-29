import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.personalizacion import load_css

# Importamos las funciones necesarias para la actualización de datos
from src.conectar import conexion_a_bd
from src.poblar import poblar_datos_meteorologicos
from src.actualizar_api import descargar_nuevos_datos_aemet



st.set_page_config(
    page_title = "Proyecto Grupo D",
    page_icon = "🌡️",
    layout = "wide",
    initial_sidebar_state = "collapsed",
)

with st.sidebar:
    st.header("Administración")
    if st.button("🔄 Actualizar Datos desde API"):
        try:
            with st.spinner("Buscando nuevos datos y actualizando la base de datos..."):
                df_nuevos_datos = descargar_nuevos_datos_aemet()

                if not df_nuevos_datos.empty:
                    motor = conexion_a_bd()
                    with motor.begin() as conector:
                        poblar_datos_meteorologicos(conector, df_nuevos_datos)

                    st.success(
                        f"¡Se han insertado {len(df_nuevos_datos)} nuevos registros!"
                    )
                    # Limpiar caché para que las páginas reflejen los datos nuevos
                    st.cache_data.clear()
                    st.cache_resource.clear()
                else:
                    st.info("La base de datos ya estaba actualizada.")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")

    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()


def main():
    # Get base64 strings for images

    load_css("src/estilos.css")

    st.title("Bienvenido al Dashboard Meteorológico de AEMET")

    st.divider()

    st.markdown("""
    Explora los datos meteorológicos de la Agencia Estatal de Meteorología (AEMET) con esta aplicación interactiva.
    
    Navega por las siguientes secciones para obtener información detallada, aunque también podrás hacerlo con el menú lateral,
                donde también encontrarás utilidades para actualizar la base de datos y limpiar la caché de la aplicación.
    
    """)

  
    st.subheader("Navegación Principal")
    
    col1, col2, col3 = st.columns(3, gap = "large")
    with col1:
        with st.container(border = True):
            st.markdown("##### 📈 Análisis Exploratorio (EDA)")
            st.markdown("Filtra y visualiza datos meteorológicos por comunidad, provincia y fechas para un análisis personalizado.")
            if st.button("Ir a análisis", key = "eda", use_container_width = True):
                st.switch_page("pages/1_EDA.py")
      
    with col2:
        with st.container(border = True):
            st.markdown("##### 📊 Comparador de métricas por provincia  y cada 2 años")
            st.markdown("Filtra y visualiza métricas de dos años de una provincia seleccionada.")
            if st.button("Ir a comparador", key="comparador", use_container_width=True):
                st.switch_page("pages/2_Comparador.py")
  
    with col3:
        with st.container(border = True):
            st.markdown("##### 🗄️ Base de datos")
            st.markdown("Estructura y esquema de la base de datos")
            if st.button("Ir a base de datos", key="bd", use_container_width=True):
                st.switch_page("pages/5_Base_de_datos.py")
    

    st.divider()
    col4, col5, col6 = st.columns(3, gap = "large")
    with col4:
         with st.container(border = True):
            st.markdown("##### 🤖 Modelos GRU y NN")
            st.markdown("Modelos precargados de deep learning para predicciones")
            if st.button("Ir a modelos", key="modelos", use_container_width=True):
                st.switch_page("pages/3_Modelos_DL.py")
    with col5:
        with st.container(border = True):
            st.markdown("##### 🔮 Modelos Prophet")
            st.markdown("Modelos precargados de prophet para predicciones")
            if st.button("Ir a propeth", key="prophet", use_container_width=True):
                st.switch_page("pages/4_Modelo_Prophet.py")
    with col6:
        with st.container(border = True):
            st.markdown("##### 👥 Sobre nosotros")
            st.markdown("Información sobre los desarrolladores del proyecto")
            if st.button("Ir a sobre nosotros", key="nosotros", use_container_width=True):
                st.switch_page("pages/6_Sobre_nosotros.py")
    
    st.markdown("""
    ### Sobre esta aplicación
    Esta herramienta fue diseñada para facilitar el acceso y análisis de datos meteorológicos de AEMET. 
    Utiliza una interfaz intuitiva para explorar datos históricos, filtrar información específica y consultar predicciones.
    
    **Características principales:**
    - Datos oficiales de AEMET
    - Visualizaciones interactivas
    - Filtros personalizables
    - Interfaz responsive
    """)


if __name__ == "__main__":
    main()
