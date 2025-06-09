import streamlit as st
import os
import base64

def get_base64_of_bin_file(bin_file):
    """Convert binary file to base64 string for embedding in HTML"""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

def main():
    # Get base64 strings for images
    background_b64 = get_base64_of_bin_file("images/background.jpg")
    logo_b64 = get_base64_of_bin_file("images/descarga.png")
    
    # Apply CSS for background image, white text, and AEMET logo
    css_style = """
        <style>
        /* Hide sidebar completely */
        .css-1d391kg, .css-1lcbmhc, .css-1outpf7, .css-12oz5g7, 
        section[data-testid="stSidebar"], .stSidebar, .css-1cypcdb {
            display: none !important;
        }
        
        /* Remove top white stripe and header padding */
        .stApp > header, .css-18e3th9, .css-1rs6os, .css-1v0mbdj,
        header[data-testid="stHeader"], .stAppHeader {
            display: none !important;
            height: 0px !important;
        }
        
        /* Adjust main content area */
        .main .block-container, .css-k1vhr4, .css-1y4p8pa {
            padding-top: 1rem !important;
            max-width: 100% !important;
        }
        
        .stApp {
            color: white;
            margin-top: 0px !important;
            padding-top: 0px !important;
        }
        """
    
    # Add background if available
    if background_b64:
        css_style += f"""
        .stApp {{
            background-image: url('data:image/jpeg;base64,{background_b64}');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        """
    
    # Add logo styling if available
    if logo_b64:
        css_style += f"""
        .aemet-logo {{
            position: fixed;
            top: 10px;
            right: 20px;
            width: 80px;
            height: auto;
            z-index: 9999;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 5px;
            backdrop-filter: blur(5px);
        }}
        """
    
    css_style += """
        /* Improve text readability on background */
        .stMarkdown, .stTitle, .stSubheader {
            text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
        }
        
        /* Style buttons */
        .stButton > button {
            background-color: rgba(0, 120, 180, 0.8);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: rgba(0, 120, 180, 1);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        /* Style dividers */
        .stDivider {
            background-color: rgba(255, 255, 255, 0.3);
        }
        </style>
    """
    
    st.markdown(css_style, unsafe_allow_html=True)

    # Add the small AEMET logo in the top-right corner if available
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" class="aemet-logo">',
            unsafe_allow_html=True
        )

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
            st.switch_page("pages/Datos_historicos.py")
    
    with col2:
        st.markdown("""
        **Datos Meteorológicos Filtrados**  
        Filtra datos meteorológicos por comunidad autónoma, provincia y rango de fechas para un análisis personalizado.  
        """)
        if st.button("Ir a Datos Filtrados", key="filtrados", use_container_width=True):
            st.switch_page("pages/Datos_filtrados.py")

    st.markdown("""
    **Predicciones de Temperatura Media**  
    Accede a predicciones de temperatura media basadas en modelos o datos históricos.  
    """)
    if st.button("Ir a Predicciones", key="predicciones", use_container_width=True):
        st.switch_page("pages/Predicciones_temperatura_media.py")

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

    # Fallback: Show logo at bottom if files aren't found
    logo_path = "images/descarga.png"
    if not logo_b64 and os.path.exists(logo_path):
        st.image(logo_path, caption="Logo AEMET", width=200)
    elif not logo_b64:
        st.image("https://www.aemet.es/imagenes_en/cabecera/logo_aemet_128.png", 
                caption="Logo AEMET", width=200)

# Button to return to the home page
if st.button("Volver a Inicio", key="volver_inicio"):
    st.switch_page("inicio.py")

if __name__ == "__main__":
    main()