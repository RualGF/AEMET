import streamlit as st
from PIL import Image
from src.personalizacion import load_css

st.set_page_config(
    page_title="Sobre Nosotros",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    load_css('src/estilos.css')
    st.title("Sobre Nosotros")

    st.write(
        """
        Somos un equipo apasionado de estudiantes del bootcamp Data Science & IA Bootcamp 2024. Este es el resultado 
        de nuestro esfuerzo y dedicación en el desarrollo de este proyecto final.".
        """
    )

    st.header("Nuestro Equipo")

    # Información de cada miembro del equipo
    team_members = [
        {"nombre": "Augusto Pablo Salonio Carbó", "rol": "Desarrollador", "image": "images/alejandro.jpg"},
        {"nombre": "Jorge Rivero de los Ríos", "rol": "Desarrollador", "image": "images/daniel.jpg"},
        {"nombre": "Raúl Guillén Flores", "rol": "Desarrollador", "image": "images/jose_antonio.jpg"},
    ]

    #https://www.linkedin.com/in/jorge-rivero-de-los-r%C3%ADos-b9188b22b/
    cols = st.columns(len(team_members))

    for i, member in enumerate(team_members):
        with cols[i]:
            try:
                image = Image.open(member["image"])
                st.image(image, caption=member["nombre"], use_column_width=True)
            except FileNotFoundError:
                st.write(f"Imagen no encontrada para {member['nombre']}")
            st.subheader(member["nombre"])
            st.write(member["rol"])

    st.header("Nuestro Proyecto: Análisis de Sentimiento en Reseñas de Películas")

    st.write(
        """
        Este proyecto tiene como objetivo principal aplicar técnicas de minería de datos 
        para analizar el sentimiento expresado en reseñas de películas. Hemos utilizado 
        diversos algoritmos y herramientas para clasificar las reseñas como positivas, 
        negativas o neutras, proporcionando una visión general del sentimiento del público.

        A través de esta aplicación, podrás:
        - Explorar visualizaciones de datos sobre el sentimiento de las reseñas.
        - Analizar el sentimiento de reseñas individuales.
        - Comprender mejor cómo se aplican los
        """)

if __name__ == "__main__":
    main()