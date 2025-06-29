import streamlit as st
from PIL import Image

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.personalizacion import load_css, get_base64_image

st.set_page_config(
    page_title = "Sobre Nosotros",
    page_icon = "👥",
    layout = "wide",
    initial_sidebar_state = "collapsed"
)

with st.sidebar:
    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

def main():
    load_css('src/estilos.css')
    st.title("Sobre nosotros")

    st.write(
        """
        Somos un equipo apasionado de estudiantes del bootcamp Data Science & IA Bootcamp 2025. Este es el resultado 
        de nuestro esfuerzo y dedicación en el desarrollo de este proyecto final.".
        """
    )

    st.header("Nuestro equipo")

    # Información de cada miembro del equipo
    team_members = [
        {"nombre": "Augusto Pablo Salonio Carbó", 
            "github": "https://github.com/ASalonio",
            "linkedin": "https://www.linkedin.com/in/augusto-salonio-carb%C3%B3-442621132/", 
            "image": "images/augusto.jpg"},
        {"nombre": "Jorge Rivero de los Ríos", 
            "github": "https://github.com/Jorge-rivero-94",
            "linkedin": "https://www.linkedin.com/in/jorge-rivero-de-los-r%C3%ADos-b9188b22b/", 
            "image": "images/jorge.jpg"},
        {"nombre": "Raúl Guillén Flores",
            "github": "https://github.com/RualGF",
            "linkedin": "https://www.linkedin.com/in/ra%C3%BAl-guill%C3%A9n-flores-014957a0/", 
            "image": "images/raul.jpg"},
    ]

    cols = st.columns(len(team_members))
    
    icono_linkedin_base64 = get_base64_image("images/LI-Bug.svg.original.svg")
    icono_github_base64 = get_base64_image("images/github-mark.svg")
    
    for i, member in enumerate(team_members):
        with cols[i]:
            try:
                image = Image.open(member["image"])
                st.image(image, use_container_width = True)
            except FileNotFoundError:
                st.error(f"Imagen no encontrada para {member['nombre']}")
            st.subheader(member["nombre"])
            
            # Enlace de LinkedIn
            if icono_linkedin_base64:
                st.html(
                    f"""
                    <img src="data:image/svg+xml;base64,{icono_linkedin_base64}" alt="LinkedIn" style="height: 20px; vertical-align: middle; margin-right: 5px;">
                    <a href="{member['linkedin']}" target="_blank" rel="noopener noreferrer">Perfil de LinkedIn</a>
                    """
                    
                )
            
            # Enlace de GitHub
            if icono_github_base64:
                st.html(
                    f"""
                    <img src="data:image/svg+xml;base64,{icono_github_base64}" alt="GitHub" style="height: 20px; vertical-align: middle; margin-right: 5px;">
                    <a href="{member['github']}" target="_blank" rel="noopener noreferrer">Perfil de GitHub</a>
                    """,
                    
                )

   
    st.header("Nuestro Proyecto: Análisis y Predicción de Datos Meteorológicos de AEMET")

    st.write(
        """
        Este proyecto se centra en la extracción, procesamiento y análisis de datos meteorológicos
        obtenidos de la API de la Agencia Estatal de Meteorología (AEMET). Nuestro objetivo es
        ofrecer una herramienta interactiva que no solo permita consultar datos históricos, sino también
        visualizarlos de manera intuitiva y acceder a predicciones de temperatura.

        A través de esta aplicación, podrás:
        - **Consultar datos históricos** de múltiples estaciones meteorológicas de España.
        - **Filtrar y visualizar métricas clave** como temperaturas (máximas, mínimas, medias), precipitación y velocidad del viento.
        - **Acceder a un modelo de predicción** que estima las temperaturas para los próximos días en una estación seleccionada.
        - **Explorar análisis detallados** y comparativas entre diferentes ubicaciones para entender mejor las tendencias climáticas.
        """)

if __name__ == "__main__":
    main()