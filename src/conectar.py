import streamlit as st

#from snowflake.snowpark.session import Session
from sqlalchemy import create_engine

@st.cache_resource(show_spinner="Conectando a la base de datos...")
def conexion_a_bd(seccion = "database"):
    """Retorna una nueva conexión desde el motor."""
    config_bd = st.secrets[seccion]
    usuario = config_bd["user"]
    pw = config_bd["password"]
    bd = config_bd["name"]
    servidor = config_bd["host"]
    puerto = config_bd["port"]

    # Conexión para Mysql local
    motor = create_engine(f"mysql+pymysql://{usuario}:{pw}@{servidor}:{puerto}/{bd}")
    # Conexión para supabase
    # motor = create_engine(f"postgresql+psycopg2://{usuario}:{pw}@{servidor}:{puerto}/{bd}?sslmode=require")
    
    #Conexión para snowflake
    # motor = Session.builder.configs(
    #     {
    #         "account": st.secrets["snowflake"]["account"],
    #         "user": st.secrets["snowflake"]["user"],
    #         "password": st.secrets["snowflake"]["password"],
    #         "role": "ACCOUNTADMIN",
    #         "warehouse": "COMPUTE_WH",
    #         "database": st.secrets["snowflake"]["database"],
    #         "schema": "public",
    #     }
    # ).create()

    # Abrir una conexión
    #conn = motor.connect()
    
    return motor
