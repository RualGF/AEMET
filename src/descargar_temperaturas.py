import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AEMET_API_KEY")

CSV_ESTACIONES = "data/estaciones_filtradas.csv"
CSV_SALIDA = "data/temperaturas_historicas.csv"

FECHAS = [
    ("2023-05-29T00:00:00UTC", "2023-11-28T00:00:00UTC"),
    ("2023-11-29T00:00:00UTC", "2024-05-28T00:00:00UTC"),
    ("2024-05-29T00:00:00UTC", "2024-11-28T00:00:00UTC"),
    ("2024-11-29T00:00:00UTC", "2025-05-28T00:00:00UTC"),
]

def obtener_datos_estacion(indicativo, fecha_inicio, fecha_fin):
    url = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/"
        f"datos/fechaini/{fecha_inicio}/fechafin/{fecha_fin}/estacion/{indicativo}"
    )
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return []
    
    datos_url = r.json().get("datos", None)
    if not datos_url:
        return []

    r_datos = requests.get(datos_url)
    if r_datos.status_code == 200:
        try:
            return r_datos.json()
        except Exception:
            return []
    return []

def cargar_estaciones():
    df = pd.read_csv(CSV_ESTACIONES)
    return df[["indicativo", "nombre"]].drop_duplicates()

def guardar_datos(df, append=True):
    modo = "a" if append and os.path.exists(CSV_SALIDA) else "w"
    header = not (append and os.path.exists(CSV_SALIDA))
    df.to_csv(CSV_SALIDA, index=False, mode=modo, header=header)

def main():
    print("📥 Cargando estaciones filtradas...")
    estaciones = cargar_estaciones()

    for _, row in estaciones.iterrows():
        indicativo = row["indicativo"]
        nombre = row["nombre"]
        print(f"📡 Procesando estación: {indicativo} - {nombre}")

        for fecha_inicio, fecha_fin in FECHAS:
            try:
                datos = obtener_datos_estacion(indicativo, fecha_inicio, fecha_fin)
                if datos:
                    df = pd.DataFrame(datos)
                    df["idema"] = indicativo
                    df["nombre"] = nombre
                    guardar_datos(df, append=True)
                    print(f"✅ Datos guardados para {indicativo} ({fecha_inicio} a {fecha_fin})")
                else:
                    print(f"⚠️ Sin datos para {indicativo} ({fecha_inicio} a {fecha_fin})")
            except Exception as e:
                print(f"❌ Error inesperado con {indicativo}: {e}")

            time.sleep(1.5)  # evitar sobrecargar la API

if __name__ == "__main__":
    main()

