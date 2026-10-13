# Pipeline de Datos Meteorológicos y Predicción Climática (AEMET)

[![Python](https://img.shields.io/badge/Python-3.10%2B%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-ff69b4.svg)](https://streamlit.io)
[![MySQL / MariaDB](https://img.shields.io/badge/MySQL%20%2F%20MariaDB-Relacional-orange.svg)](https://mariadb.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-blue.svg)](https://pandas.pydata.org/)
[![TensorFlow / Keras](https://img.shields.io/badge/Keras-3.x-red.svg)](https://keras.io/)
[![Prophet](https://img.shields.io/badge/Prophet-Meta-purple.svg)](https://facebook.github.io/prophet/)

## 📌 Descripción

Proyecto integral de ingeniería de datos y ciencia de datos orientado a la ingesta, limpieza, modelado y explotación interactiva de datos meteorológicos históricos y en tiempo real de España a través de la API OpenData de la **AEMET**.

El sistema procesa **más de 2,5 millones de registros diarios** (periodo 2016–2026) distribuidos en más de 900 estaciones meteorológicas, aplicando técnicas avanzadas de imputación y normalización, almacenamiento en una base de datos relacional optimizada (MySQL/MariaDB) y modelos de predicción basados tanto en **Deep Learning recurrente (GRU y RNN)** como en **modelos aditivos estacionales (Facebook Prophet)**.

Toda la solución se despliega en una aplicación web interactiva construida con **Streamlit** y gráficos dinámicos con **Plotly**.

---

## 📊 Arquitectura del Sistema

```text
       AEMET OpenData API (REST)
                  ↓
   Extracción por bloques incrementales (14 días máx. con rate limiting)
                  ↓
   Pipeline ETL: Limpieza, normalización territorial e imputación (KNN + Splines)
                  ↓
       Almacenamiento Consolidado
     ┌────────────┴────────────┐
     ↓                         ↓
  MySQL / MariaDB      data/*.pkl (Master Dataset)
     │                         │
     │                         ↓
     │               Modelos Predictivos
     │          ┌──────────────┴──────────────┐
     │          ↓                             ↓
     │   Deep Learning (GRU/NN)        Prophet + AR Residual
     │   (Memoria secuencial 30d)      (Ajuste local y estacional)
     │          └──────────────┬──────────────┘
     ↓                         ↓
    Dashboard Interactivo (Streamlit + Plotly)
       • Análisis Exploratorio (EDA Coroplético CCAA/Provincias)
       • Comparador Bianual de Métricas
       • Pronósticos en Vivo con Intervalos de Confianza
       • Actualización Incremental en 1 Clic
```

---

## ⚙️ Funcionalidades Principales

* **Ingesta incremental automática:** Sincronización continua con la API de AEMET sin límite de días, detectando la última fecha almacenada y descargando únicamente los bloques pendientes.
* **Limpieza e imputación robusta:** Tratamiento de valores anómalos y nulos mediante combinación de imputación por vecinos más cercanos (KNN) e interpolación temporal continua.
* **Análisis Exploratorio de Datos (EDA):** Mapas coropléticos interactivos de España a nivel de comunidad autónoma y provincia, con selector temporal y filtros por métricas (temperatura media, máxima, mínima, precipitación, viento, etc.).
* **Comparador de métricas interanual:** Comparación visual y estadística de tendencias estacionales entre dos años distintos para una provincia determinada.
* **Predicción con Deep Learning (GRU y Redes Neuronales):**
  * Modelos **GRU multicapa** entrenados con secuencias de 30 días y 6 características físicas (humedad, presiones, temperaturas).
  * Redes recurrentes univariantes para predicción ágil a corto plazo.
* **Predicción con Prophet + Corrección de Inercia Térmica (AR Residual):**
  * **Ajuste local en vivo por estación:** Modelado ultrarrápido (~0.5 s) del microclima específico de cada estación.
  * **Amortiguación de inercia térmica:** Incorpora persistencia autorregresiva para evitar caídas bruscas hacia la media climática ante olas de calor o anomalías atmosféricas.
  * **Descomposición explicable:** Gráficos interactivos de la tendencia multianual y el ciclo estacional anual.
* **Visualización del Esquema Relacional:** Consulta gráfica del modelo entidad-relación (MER) y estado de las tablas de la base de datos.

---

## 📁 Estructura del Proyecto

```text
AEMET/
│
├── .streamlit/
│   └── secrets.toml             # Credenciales locales de BD y API AEMET (ignorado en Git)
│
├── data/                        # GeoJSON y datasets procesados
│   ├── spain-provinces.geojson
│   ├── spain-comunidad-autonoma.geojson
│   └── temperaturas_limpias_10_años_final.pkl # Dataset maestro consolidado
│
├── images/                      # Diagramas MER y recursos visuales
│
├── limpieza/                    # Scripts de preparación y estandarización de datos
│   ├── knn_impute.py            # Algoritmos de imputación KNN
│   └── standarize_provinces.py  # Normalización de códigos y nombres de provincias/CCAA
│
├── modelos/                     # Pesos y escaladores de modelos pre-entrenados
│   ├── modelos_dl/              # Modelos Keras (.keras) y escaladores MinMaxScaler (.pkl)
│   └── prophet/                 # Modelos serializados de Prophet por clúster (.pkl)
│
├── pages/                       # Módulos de navegación de Streamlit
│   ├── 1_EDA.py                 # Mapas coropléticos y análisis exploratorio
│   ├── 2_Comparador.py          # Comparador temporal entre años
│   ├── 3_Modelos_DL.py          # Interfaz de predicción Deep Learning (GRU / NN)
│   ├── 4_Modelo_Prophet.py      # Interfaz de predicción Prophet + AR Residual
│   ├── 5_Base_de_datos.py       # Visor del esquema y estructura de la BD
│   └── 6_Sobre_Nosotros.py      # Información del equipo y proyecto
│
├── src/                         # Núcleo de lógica y módulos reutilizables
│   ├── actualizar_api.py        # Descarga y actualización incremental para la BD
│   ├── actualizar_historico_aemet.py # Actualización del dataset PKL maestro
│   ├── reentrenar_todos_modelos.py   # Reentrenamiento global de todos los modelos (GRU/NN/Prophet)
│   ├── cliente_aemet.py         # Cliente HTTP y consulta de inventario de estaciones
│   ├── conectar.py              # Gestión del pool de conexiones SQLAlchemy
│   ├── dibujar.py               # Generación de mapas y gráficas Plotly
│   ├── ETL.py                   # Pipeline de transformación de datos brutos
│   ├── extraer_datos.py         # Consultas SQL dinámicas optimizadas
│   ├── personalizacion.py       # Estilos CSS y temas de la interfaz
│   └── poblar.py                # Definición DDL y carga por lotes (upsert)
│
├── Inicio.py                    # Punto de entrada de la aplicación Streamlit
├── requirements.txt             # Dependencias del proyecto
└── README.md                    # Documentación principal
```

---

## 🚀 Instalación y Configuración

### Pre-requisitos
* **Python 3.10 o superior** (probado y optimizado en Python 3.12).
* Servidor de **MySQL 8.0+** o **MariaDB 10.5+** en ejecución local o remoto.
* **Git**.

### 1. Clonar el repositorio
```bash
git clone https://github.com/RualGF/AEMET.git
cd AEMET
```

### 2. Crear y activar el entorno virtual

* **En Linux / macOS (bash / zsh):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

* **En Linux (fish shell):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate.fish
  ```

* **En Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales (`secrets.toml`)
Crea el archivo `.streamlit/secrets.toml` en la raíz del proyecto:

```toml
[database]
user = "tu_usuario"
password = "tu_password"
host = "localhost"
port = 3306
name = "aemet"

[api_aemet]
API_KEY = "tu_api_key_obtenida_en_opendata_aemet"
```

> Obtén tu clave API gratuita en el portal oficial: [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/altaUsuario).

### 5. Crear las tablas e inicializar la base de datos
Asegúrate de que la base de datos exista en tu servidor MySQL/MariaDB (`CREATE DATABASE aemet;`) y ejecuta:

```bash
python src/poblar.py --tabla todas
```

Este comando generará las tablas de dimensiones (`comunidades`, `provincias`, `estaciones`) y la tabla de hechos (`datos_meteorologicos`) mediante inserciones optimizadas por lotes.

---

## 💻 Uso de la Aplicación

Inicia el servidor interactivo de Streamlit:

```bash
streamlit run Inicio.py
```

Abre tu navegador en `http://localhost:8501`.

* **Desde la barra lateral:** puedes actualizar los datos con un solo clic pulsando **«🔄 Actualizar Datos desde API»**, lo que sincronizará la base de datos con los registros más recientes publicados por AEMET y limpiará la caché automáticamente.

---

## 🛠️ Mantenimiento y Reentrenamiento de Modelos (CLI)

Si deseas realizar tareas de mantenimiento directamente por terminal:

* **Descargar y actualizar el dataset maestro (.pkl):**
  ```bash
  python src/actualizar_historico_aemet.py
  ```

* **Reentrenar todos los modelos (GRU, NN y Prophet):**
  ```bash
  python src/reentrenar_todos_modelos.py
  ```
  *(Reentrena y guarda los 6 modelos GRU, 6 Redes Neuronales y 6 modelos Prophet en ~1-2 minutos).*

---

## 🧰 Tecnologías Utilizadas

* **Framework Web:** [Streamlit](https://streamlit.io)
* **Motor de Base de Datos:** MySQL / MariaDB (SQLAlchemy, PyMySQL)
* **Manipulación y Análisis:** Pandas, NumPy
* **Visualización Dinámica:** Plotly Express & Graph Objects
* **Modelos Predictivos:**
  * Keras / TensorFlow (GRU y Redes Neuronales recurrentes)
  * Facebook Prophet (CmdStanPy)
  * Scikit-Learn (KNN Imputer, MinMaxScaler, métricas MAE/RMSE/R²)
* **Protocolos e Ingesta:** Requests con políticas de reintento exponencial y control de cuota

---

## 👥 Autores

Proyecto desarrollado y ampliado a partir del Data Science & IA Bootcamp:

* **Raúl Guillén Flores**: [GitHub](https://github.com/RualGF) | [LinkedIn](https://www.linkedin.com/in/ra%C3%BAl-guill%C3%A9n-flores-014957a0/)
* **Augusto Pablo Salonio Carbó**: [GitHub](https://github.com/ASalonio) | [LinkedIn](https://www.linkedin.com/in/augusto-salonio-carb%C3%B3-442621132/)
* **Jorge Rivero de los Ríos**: [GitHub](https://github.com/Jorge-rivero-94) | [LinkedIn](https://www.linkedin.com/in/jorge-rivero-de-los-r%C3%ADos-b9188b22b/)
