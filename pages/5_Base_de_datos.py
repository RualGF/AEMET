import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.personalizacion import load_css


st.set_page_config(page_title = "Base de Datos", 
                   page_icon = "🗄️", 
                   layout = "wide", 
                   initial_sidebar_state = "collapsed")

def main():
    load_css('src/estilos.css')
    st.title("Arquitectura de la Base de Datos")

    st.image(image="images/MER.png", caption="Arquitectura de la Base de Datos")

    st.markdown("""
    En este proyecto, se implementó una base de datos relacional para almacenar y gestionar la información relacionada con datos meteorológicos. 
    La base de datos consta de las siguientes tablas:

    ### Tabla `comunidades`

    Esta tabla almacena la información de las comunidades y ciudades autónomas de España.
                

    | Columna      | Tipo de Dato         | Descripción                                                   |
    |--------------|----------------------|---------------------------------------------------------------|
    | `codigo_ca`  | TINYINT UNSIGNED     | Clave primaria, identificador único de la comunidad autónoma. |
    | `nombre`     | VARCHAR(50) NOT NULL | Nombre de la comunidad autónoma.                              |


    ### Tabla `provincias`

    Esta tabla almacena la información de las provincias y ciudades autónomas de España.
                

    | Columna      | Tipo de Dato             | Descripción                                          |
    |--------------|--------------------------|------------------------------------------------------|
    | `codigo_prov`| TINYINT UNSIGNED         | Clave primaria, identificador único de la provincia. |
    | `nombre`     | VARCHAR(50) NOT NULL     | Nombre de la provincia.                              |
    | `codigo_ca`  | TINYINT UNSIGNED         | Clave foránea que referencia a la comunidad autónoma.|
    | |`FOREIGN KEY (codigo_ca) REFERENCES comunidades(codigo_ca)`  |                                |

    
    ### Tabla `datos_meteorologicos`

    Esta tabla almacena los datos meteorológicos recogidos de la AEMET
                

    | Columna                | Tipo de Dato         | Descripción                                                                                                      |
    |------------------------|----------------------|------------------------------------------------------------------------------------------------------------------|
    | `id_descarga`          | VARCHAR(50) NOT NULL | Identificador de la descarga que puede coincidir con otros datos.                                                |
    | `fecha`                | DATE PRIMARY KEY     | Fecha de la toma de mediciones de la estación meteorológica.                                                     |
    | `codigo_indicativo`    | VARCHAR(10) NOT NULL | Indicativo de la estación meteorológica. Parte de la clave primaria de la tabla.                                 |
    | `codigo_prov`          | TINYINT UNSIGNED     | Clave foránea que referencia a la provincia donde se sitúa la estación meteorológica.                            |
    | `altitud`              | FLOAT                | Altitud de la estación meteorológica.                                                                            |
    | `tmed`                 | FLOAT                | Temperatura media registrada en la estación meteorológica.                                                       |
    | `tmin`                 | FLOAT                | Temperatura mínima registrada en la estación meteorológica.                                                      |
    | `tmax`                 | FLOAT                | Temperatura máxima registrada en la estación meteorológica.                                                      |
    | `prec`                 | FLOAT                | Precipitación registrada en la estación meteorológica.                                                           |
    | `velmedia`             | FLOAT                | Velocidad media del viento registrada en la estación meteorológica.                                              |
    | `racha`                | FLOAT                | Racha máxima del viento registrada en la estación meteorológica.                                                 |
    | `hrMedia`              | FLOAT                | Humedad relativa media registrada en la estación meteorológica.                                                  |
    | `timestamp_extraccion` | TIMESTAMP            | Fecha y hora en la que se extrajeron los datos de la API de la AEMET.                                            |
    | |`FOREIGN KEY (codigo_prov) REFERENCES provincias(codigo_prov)` |                                                                                                | 
    | |`FOREIGN KEY (codigo_indicativo) REFERENCES estaciones(codigo_indicativo)` |                                                                                    |

                
    ### Tabla `estaciones`

    Esta tabla almacena la información de las estaciones meteorológicas.
                

    | Columna                | Tipo de Dato              | Descripción                                                                                                      |
    |------------------------|---------------------------|------------------------------------------------------------------------------------------------------------------|
    | `codigo_indicativo`    | VARCHAR(10) NOT NULL      | Clave primaria, identificador único de la estación meteorológica.                                                |
    | `nombre_estacion`      | VARCHAR(100) NOT NULL     | Nombre de la estación meteorológica.                                                                             |
    | `codigo_prov`          | TINYINT UNSIGNED          | Clave foránea que referencia a la provincia donde se sitúa la estación meteorológica.                            |
    | `cluster`              | TINYINT UNSIGNED NOT NULL | Clúster de la estación meteorológica.                                                                            |
    | `start_date`           | DATE                      | Columna para limpieza y clusterización.                                                                          |
    | `end_date`             | DATE                      | Columna para limpieza y clusterización.                                                                          |
    | `latitud_dd`           | FLOAT                     | Columna para limpieza y clusterización.                                                                          |
    | `longitud_dd`          | FLOAT                     | Columna para limpieza y clusterización.                                                                          |
    | |`FOREIGN KEY (codigo_prov) REFERENCES provincias(codigo_prov)` |
    
    """
    )

if __name__ == "__main__":
    main()