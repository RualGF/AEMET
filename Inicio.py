import streamlit as st

from src.personalizacion import load_css


st.set_page_config(
    page_title="Proyecto Grupo D",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
    )

with st.sidebar:
    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()
        
def main():
    # Get base64 strings for images
    

    load_css('src/estilos.css')

    st.title("Bienvenido al Dashboard Meteorológico de AEMET")
    
    st.divider()

    st.markdown("""
    Explora los datos meteorológicos de la Agencia Estatal de Meteorología (AEMET) con esta aplicación interactiva. 
    Navega por las siguientes secciones para obtener información detallada:
    """)

    st.subheader("Secciones Disponibles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Datos Históricos de la AEMET**  
        Visualiza estadísticas promedio de variables meteorológicas (temperatura, precipitación, humedad, etc.) 
        por provincia en España.  
        """)
        if st.button("Ir a Datos Históricos", key="historicos", use_container_width=True):
            st.switch_page("pages/1_Datos_historicos.py")
    
    with col2:
        st.markdown("""
        **Datos Meteorológicos Filtrados**  
        Filtra datos meteorológicos por comunidad autónoma, provincia y rango de fechas para un análisis personalizado.  
        """)
        if st.button("Ir a Datos Filtrados", key="filtrados", use_container_width=True):
            st.switch_page("pages/1_EDA.py")

    st.markdown("""
    **Predicciones de Temperatura Media**  
    Accede a predicciones de temperatura media basadas en modelos o datos históricos.  
    """)
    if st.button("Ir a Predicciones", key="predicciones", use_container_width=True):
        st.switch_page("pages/3_Modelos.py")

    st.divider()
    
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

    # Button to return to the home page
    if st.button("Volver a Inicio", key="volver_inicio"):
        st.switch_page("inicio.py")

if __name__ == "__main__":
    main()

