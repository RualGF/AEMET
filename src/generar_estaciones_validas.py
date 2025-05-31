import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Cargar la API key
load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

# Cargar las estaciones filtradas previamente
df = pd.read_csv("data/estaciones_filtradas.csv")

# Crear lista para las estaciones válidas
estaciones_validas = []

# Revisar cada estación
for _, row in df.iterrows():
    idema = row["idema"]
    url = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/2023-01-01/fechafin/2023-12-31/estacion/{idema}"
    headers = {"accept": "application/json", "api_key": API_KEY}

    try:
        respuesta = requests.get(url, headers=headers)
        datos = respuesta.json()
        if "datos" in datos:
            estaciones_validas.append(row)
            print(f"✅ Estación {idema} válida.")
        else:
            print(f"⚠️ Estación {idema} sin datos.")
    except Exception as e:
        print(f"❌ Error con estación {idema}: {e}")

# Guardar CSV si hay datos
if estaciones_validas:
    df_validas = pd.DataFrame(estaciones_validas)
    os.makedirs("data", exist_ok=True)
    df_validas.to_csv("data/estaciones_validas.csv", index=False)
    print("✅ Estaciones válidas guardadas en data/estaciones_validas.csv")
else:
    print("⚠️ No se encontraron estaciones válidas.")

