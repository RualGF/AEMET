import streamlit as st
from src.personalizacion import load_css

def main():
    load_css('src/estilos.css')
    st.title("Predicciones de temperatura")
    st.divider()
    # st.write(st.context.cookies)
    # st.write(st.context.headers)
    st.write("Por hacer")
if __name__ == "__main__":
    main()