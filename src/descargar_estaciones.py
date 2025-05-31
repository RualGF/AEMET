import os
import requests
from dotenv import load_dotenv

# Cargar API Key desde .env
load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

# Endpoint de estaciones
url = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
headers = {"accept": "application/json", "api_key": API_KEY}

# Obtener URL de descarga de los datos
respuesta = requests.get(url, headers=headers)

if respuesta.status_code == 200:
    datos = respuesta.json()
    url_datos = datos.get("datos")
    if url_datos:
        print(f"🔗 URL con datos reales: {url_datos}")
        respuesta_datos = requests.get(url_datos)
        os.makedirs("data", exist_ok=True)
        with open("data/estaciones_crudas.txt", "w", encoding="ISO-8859-15") as f:
            f.write(respuesta_datos.text)
        print("✅ Estaciones guardadas en data/estaciones_crudas.txt")
    else:
        print("❌ No se encontró la URL de datos.")
else:
    print(f"❌ Error en la petición: {respuesta.status_code}")
