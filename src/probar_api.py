import os
import requests
from dotenv import load_dotenv

# Cargar API Key desde .env
load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

print(f"✅ API Key encontrada: {API_KEY[:5]}...")

# URL base de observaciones
url = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
headers = {"accept": "application/json", "api_key": API_KEY}

print("🔍 Solicitando URL de datos...")
respuesta = requests.get(url, headers=headers)

if respuesta.status_code == 200:
    try:
        datos = respuesta.json()
        print("🔗 URL obtenida:", datos.get("datos"))
    except Exception as e:
        print("❌ Error al interpretar JSON:", e)
else:
    print("❌ Error:", respuesta.status_code, respuesta.text)

