import streamlit as st

from src.personalizacion import load_css


st.set_page_config(page_title="Base de Datos", page_icon="🗄️", 
                   layout="wide", initial_sidebar_state="collapsed")

def main():
    load_css('src/estilos.css')
    st.title("Arquitectura de la Base de Datos")

    st.image(image="images/MER.png", caption="Arquitectura de la Base de Datos")

    st.markdown("""
    En este proyecto, se implementó una base de datos relacional para almacenar y gestionar la información relacionada con datos meteorológicos. 
    La base de datos consta de las siguientes tablas:

    ### Tabla `comunidades`

    Esta tabla almacena la información de las comunidades y ciudades autónomas de España.

    | Columna      | Tipo de Dato     | Descripción                                                   |
    |--------------|------------------|---------------------------------------------------------------|
    | `codigo_ca`  | TINYINT UNSIGNED | Clave primaria, identificador único de la comunidad autónoma. |
    | `nombre`     | VARCHAR(50)      | Nombre de la comunidad autónoma.                              |


    ### Tabla `provincias`

    Esta tabla almacena la información de las provincias y ciudades autónomas de España.

    | Columna      | Tipo de Dato     | Descripción                                          |
    |--------------|------------------|------------------------------------------------------|
    | `codigo_prov`| TINYINT UNSIGNED | Clave primaria, identificador único de la provincia. |
    | `nombre`     | VARCHAR(50)      | Nombre de la provincia.                              |
    | `codigo_ca`  | TINYINT UNSIGNED | Clave foránea que referencia a la comunidad autónoma.|
    | `FOREIGN KEY (codigo_ca)` | `REFERENCES` | `comunidades(codigo_ca)`                    |

    ### Tabla `datos_meteorologicos`

    Esta tabla almacena los datos meteorológicos recogidos de la AEMET

    | Columna                | Tipo de Dato      | Descripción                                                                                                      |
    |------------------------|-------------------|------------------------------------------------------------------------------------------------------------------|
    | `id_descarga`          | VARCHAR(50)       | Identificador de la descarga que puede coincidir con otros datos.                                                |
    | `fecha`                | DATE              | Fecha de la toma de mediciones de la estación meteorológica.                                                     |
    | `indicativo`           | VARCHAR(10)       | Indicativo de la estación meteorológica. Parte de la clave primaria de la tabla.                                 |
    | `nombre`               | VARCHAR(100)      | Nombre de la población o lugar donde se sitúa la estación meteorológica. Parte de la clave primaria de la tabla. |
    | `codigo_prov`          | TINYINT UNSIGNED  | Clave foránea que referencia a la provincia donde se sitúa la estación meteorológica.                            |
    | `altitud`              | SMALLINT UNSIGNED | Altitud de la estación meteorológica.                                                                            |
    | `tmed`                 | DECIMAL (4,1)     | Temperatura media registrada en la estación meteorológica.                                                       |
    | `tmin`                 | DECIMAL (4,1)     | Temperatura mínima registrada en la estación meteorológica.                                                      |
    | `tmax`                 | DECIMAL (4,1)     | Temperatura máxima registrada en la estación meteorológica.                                                      |
    | `prec`                 | DECIMAL (5,1)     | Precipitación registrada en la estación meteorológica.                                                           |
    | `velmedia`             | DECIMAL (4,1)     | Velocidad media del viento registrada en la estación meteorológica.                                              |
    | `racha`                | DECIMAL (4,1)     | Racha máxima del viento registrada en la estación meteorológica.                                                 |
    | `hrMedia`              | SMALLINT          | Humedad relativa media registrada en la estación meteorológica.                                                  |
    | `timestamp_extraccion` | DATETIME          | Fecha y hora en la que se extrajeron los datos de la API de la AEMET.                                            |
    | |FOREIGN KEY (codigo_prov) REFERENCES provincias(codigo_prov) |                                                                                               |

    """
    )

if __name__ == "__main__":
    main()