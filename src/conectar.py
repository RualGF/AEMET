import streamlit as st

from sqlalchemy import create_engine


def conexion():
    """Retorna una nueva conexión desde el motor."""
    usuario = st.secrets["snowflake"]["user"]
    pw = st.secrets["snowflake"]["password"]
    bd = st.secrets["snowflake"]["name"]
    servidor = st.secrets["snowflake"]["host"]
    puerto = st.secrets["snowflake"]["port"]

    motor = create_engine(f"mysql+pymysql://{usuario}:{pw}@{servidor}:{puerto}/{bd}")
    # Abrir una conexión
    conectar = motor.connect()
    return conectar
