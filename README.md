# PROYECTO-FINAL-
CONDICIONES METEOROLÓGICAS

## Descripción
Este proyecto es una aplicación web desarrollada con Streamlit que permite visualizar y analizar datos meteorológicos de provincias españolas. Incluye análisis estadístico descriptivo de temperaturas, filtrado de datos por métricas, provincias y fechas, así como predicciones de temperatura media. Los datos se obtienen de la API de AEMET y se almacenan en una base de datos MySQL.

## Estructura
- `main/Inicio.py`: Página de inicio de la app.
- `/pages/1_Datos_historicos.py`: Página estadística descriptiva temperatura.
- `/pages/2_Datos_filtrados.py`: Página datos filtrados por métrica, provincia y fecha.
- `/pages/3_Predicciones.py`: Página de predicciónes temperatura media.
- `/src/conectar.py`: Lógica de conexión MySQL.
- `/src/popular.py`: Carga de datos MySQL.
- `/src/extraer_datos.py`: Queries MySQL.
- `/data/spain-provinces.geojson`: Archivo GeoJSON de provincias españolas.
- `/data/temperaturas_limpias`: Archivo .csv datos API AEMET
- `/notebooks`: Bitácora de Extracción y Limpieza (no ejecutar)

## Instalación
1. Crear un entorno virtual : `python -m venv .entorno`
2. Activar el entorno virtual: en Windows `.entorno\Scripts\activate` en macOS/Linux `.entorno/bin/activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar: `streamlit run ./Inicio.py`


## Uso

Ejecuta la aplicación con el comando anterior.
Abre el enlace proporcionado por Streamlit en tu navegador (normalmente http://localhost:8501).
Navega entre las páginas de la aplicación para:
1. Ver estadísticas descriptivas de temperaturas.
2. Filtrar datos por métricas, provincias y fechas.
3. Consultar predicciones de temperatura media.

## Notas

Configura la conexión a MySQL en /src/conectar.py con las credenciales de tu servidor MySQL.
Los datos en /data/temperaturas_limpias.csv deben estar preprocesados desde la API de AEMET.
Los notebooks en /notebooks son solo para referencia y no deben ejecutarse como parte de la aplicación.
