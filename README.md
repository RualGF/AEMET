# Análisis y Predicción de Condiciones Meteorológicas en España

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33-ff69b4.svg)](https://streamlit.io)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-blue.svg)](https://pandas.pydata.org/)
[![Keras](https://img.shields.io/badge/Keras-3.x-red.svg)](https://keras.io/)

## Descripción
Este proyecto es una aplicación web interactiva, desarrollada con Streamlit, para visualizar y analizar datos meteorológicos de España. La aplicación consume datos de la API de AEMET, los procesa a través de un pipeline ETL y los almacena en una base de datos MySQL para su posterior análisis y modelado.

---

## 📜 Índice

- Características Principales
- Estructura del Proyecto
- Instalación y Configuración
  - Pre-requisitos
  - Pasos de Instalación
- Uso de la Aplicación
- Tecnologías Utilizadas
- Autores

---

## ✨ Características Principales

- **Análisis Exploratorio de Datos (EDA)**: Visualiza datos meteorológicos agregados en mapas coropléticos interactivos, con filtros por comunidad autónoma, provincia y rango de fechas.
- **Comparador Anual**: Compara tendencias de métricas específicas (temperatura, precipitación, etc.) entre dos años para una provincia seleccionada.
- **Predicciones con Deep Learning**: Utiliza modelos pre-entrenados (GRU y Redes Neuronales) para pronosticar la temperatura media en estaciones específicas.
- **Predicciones con Prophet**: Implementa el modelo Prophet de Facebook para realizar pronósticos de series temporales.
- **Actualización de Datos**: Funcionalidad para actualizar la base de datos con los datos más recientes de la API de AEMET.
- **Visualización de la Base de Datos**: Muestra el Modelo Entidad-Relación (MER) y la estructura de las tablas de la base de datos.

---

## 📁 Estructura del Proyecto

```
PROYECTO-FINAL/
│
├── .streamlit/
│   └── secrets.toml      # Fichero para credenciales (BD, API keys) - NO INCLUIDO EN GIT
│
├── data/                 # Ficheros de datos estáticos y cacheados
│   ├── spain-provinces.geojson
│   ├── spain-comunidad-autonoma.geojson
│   └── ...
│
├── images/                 # Imágenes y logos para la interfaz
│
├── pages/                  # Páginas de la aplicación Streamlit
│   ├── 1_EDA.py            # Página de Análisis Exploratorio de Datos (EDA)
│   ├── 2_Comparador.py     # Página de comparador anual por métrica y provincia
│   ├── 3_Modelos_DL.py     # Página de modelos de Deep Learning
│   ├── 4_Modelo_Prophet.py # Página de modelo Prophet
│   ├── 5_Base_de_datos.py  # Página de visualización de la estructura de la base de datos
│   └── 6_Sobre_Nosotros.py # Página de sobre nosotros
│
├── src/                   # Código fuente principal
│   ├── actualizar_api.py  # Función para actualizar los datos de datos nuevos de AEMET 
│   ├── borra_tablas.py    # Funciones para borrar tablas de la BD (no integrada en Streamlit)
│   ├── conectar.py        # Lógica de conexión a la BD
│   ├── dibujar.py         # Funciones para generar gráficos
│   ├── ETL.py             # Pipeline de Extracción, Transformación y Carga
│   ├── extraer_datos.py   # Funciones para consultas a la BD
│   ├── hacer_peticion.py  # Lógica para peticiones a la API de AEMET
│   ├── personalizacion.py # Funciones para personalizar los estilos de Streamlit
│   └── poblar.py          # Scripts para crear y poblar tablas
│
├── modelos/
│    ├── modelos_dl/ # Carpeta donde se alojan los modelos de Deep Learning
│    └── prophet/ # Carpeta donde se alojan los modelos de Prophet
│
│
├── notebooks/            # Jupyter Notebooks para exploración y modelado (referencia)
│
├── Inicio.py             # Página principal de la aplicación
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Este fichero
```

---

## 🚀 Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto en tu entorno local.

### Pre-requisitos

- Python 3.10 o superior.
- Un servidor de MySQL en ejecución.
- Git.

### Pasos de Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/Jorge-rivero-94/PROYECTO-FINAL-.git
    cd PROYECTO-FINAL-
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Crear el entorno
    python -m venv .entorno

    # Activar en Windows
    .entorno/Scripts/activate

    # Activar en macOS/Linux
    source .entorno/bin/activate
    ```

3.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar las credenciales (Secrets):**
    Crea una carpeta `.streamlit` en la raíz del proyecto y, dentro de ella, un fichero llamado `secrets.toml`. Añade tus credenciales con el siguiente formato:
    ```toml
    # .streamlit/secrets.toml

    [database]
    user = "tu_usuario_mysql"
    password = "tu_password_mysql"
    host = "localhost"
    port = 3306
    name = "aemet" # O el nombre que le des a tu base de datos

    # NOTA: La API Key de AEMET está hardcodeada en src/hacer_peticion.py
    # pero idealmente también iría aquí.
    # API_KEY = "tu_api_key_aemet"
    ```

5.  **Crear y poblar la base de datos:**
    Asegúrate de que tu servidor MySQL esté corriendo y de haber creado una base de datos con el nombre que especificaste en `secrets.toml` (ej. `aemet`). Luego, ejecuta el script de población desde la raíz del proyecto:
    ```bash
    python src/poblar.py --tabla todas
    ```
    Este comando creará todas las tablas necesarias y las llenará con los datos iniciales del proyecto. Este proceso puede tardar varios minutos.

---

## 💻 Uso de la Aplicación

1.  **Ejecutar la aplicación:**
    Una vez completada la instalación y configuración, inicia la aplicación con Streamlit:
    ```bash
    streamlit run Inicio.py
    ```

2.  **Navegar por la aplicación:**
    Abre la URL que aparece en tu terminal (normalmente `http://localhost:8501`) en tu navegador. Desde la página de inicio o la barra lateral, podrás acceder a todas las funcionalidades descritas en la sección de Características Principales.

---

## 🛠️ Tecnologías Utilizadas

- **Frontend**: Streamlit
- **Backend y Lógica**: Python, Pandas, NumPy
- **Base de Datos**: MySQL (con SQLAlchemy y PyMySQL)
- **Visualización de Datos**: Plotly, GeoJSON
- **Machine Learning**: Scikit-learn, Keras (TensorFlow), Prophet (Facebook)
- **Peticiones API**: Requests

---

## 👥 Autores

Este proyecto fue desarrollado como parte del Data Science & IA Bootcamp 2024 por:

- **Augusto Pablo Salonio Carbó**: [GitHub](https://github.com/ASalonio) | [LinkedIn](https://www.linkedin.com/in/augusto-salonio-carb%C3%B3-442621132/)
- **Jorge Rivero de los Ríos**: [GitHub](https://github.com/Jorge-rivero-94) | [LinkedIn](https://www.linkedin.com/in/jorge-rivero-de-los-r%C3%ADos-b9188b22b/)
- **Raúl Guillén Flores**: [GitHub](https://github.com/RualGF) | [LinkedIn](https://www.linkedin.com/in/ra%C3%BAl-guill%C3%A9n-flores-014957a0/)
