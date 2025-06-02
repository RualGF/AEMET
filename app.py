import pandas as pd
import requests
from time import sleep
import streamlit as st

st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.extremelycoolapp.com/help",
        "Report a bug": "https://www.extremelycoolapp.com/bug",
        "About": "# This is a header. This is an *extremely* cool app!",
    },
)

st.title("Predicciones meteorológicas")
st.divider()

df = pd.read_csv(r"D:\PROYECTO-FINAL-\data\provinvias.csv")

with st.expander("Provincias"):
    # with st.spinner("Cargando provincias..."):
    #     sleep(5)
    st.dataframe(df, hide_index=True)

st.divider()

opcion_elegida = st.sidebar.multiselect(
    "Elige la provincia: ",
    df["nombre"],
    default=None,
    placeholder="Elige las provincias que quieras ver"
)
st.sidebar.divider()
st.sidebar.write(opcion_elegida)
if opcion_elegida:
    st.sidebar.write(opcion_elegida)
    st.dataframe(df[df["nombre"].isin(opcion_elegida)], hide_index=True)

