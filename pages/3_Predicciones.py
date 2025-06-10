import streamlit as st
from src.personalizacion import load_css

st.set_page_config(
    page_title="Proyecto Grupo D",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
    )

def main():
    load_css('src/estilos.css')
    st.title("Predicciones de temperatura")
    st.divider()
    # st.write(st.context.cookies)
    # st.write(st.context.headers)
    st.write("Por hacer")
if __name__ == "__main__":
    main()