# PROYECTO-FINAL-
CONDICIONES METEOROLÓGICAS

## Estructura del Proyecto
- `main/Inicio.py`: Página de inicio de la app.
- `/pages/1_Datos_historicos.py`: Página estadística descriptiva.
- `/pages/2_Datos_filtrados.py`: Página datos filtrados por métrica, provincia y fecha.
- `/pages/3_Datos_filtrados.py`: Página de predicciónes temperatura media.
- `/src/conectar.py`: Lógica de conexión MySQL.
- `/src/popular.py`: Carga de datos MySQL.
- `/src/extraer_datos.py`: Queries MySQL.
- `/data/spain-provinces.geojson`: Archivo GeoJSON de provincias españolas.
- `/data/temperaturas_limpias`: Archivo .csv datos API AEMET

## Instalación
1. Create Anaconda environment: `conda create -n PFB python=3.11 -c conda-forge`
2. Activación: `conda activate PFB`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar: `streamlit run ./Inicio.py`