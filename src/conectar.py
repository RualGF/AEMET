import streamlit as st

from sqlalchemy import create_engine


def conexion():
    """Retorna una nueva conexión desde el motor."""
    usuario = st.secrets["database"]["user"]
    pw = st.secrets["database"]["password"]
    bd = st.secrets["database"]["dbname"]
    servidor = st.secrets["database"]["host"]
    puerto = st.secrets["database"]["port"]

    #motor = create_engine(f"mysql+pymysql://{usuario}:{pw}@{servidor}:{puerto}/{bd}")
    motor = create_engine(f"postgresql+psycopg2://{usuario}:{pw}@{servidor}:{puerto}/{bd}?sslmode=require")
    # Abrir una conexión
    conectar = motor.connect()
    
    return conectar
