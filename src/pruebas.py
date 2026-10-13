
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sys
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJydWFsZ2ZAZ21haWwuY29tIiwianRpIjoiN2Q5M2RjMDMtNWY5Yi00YzYwLWJmYTAtNTc2MTNiNDgyZjkxIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NDg0NDQ5MzIsInVzZXJJZCI6IjdkOTNkYzAzLTVmOWItNGM2MC1iZmEwLTU3NjEzYjQ4MmY5MSIsInJvbGUiOiIifQ.lb02yR53ROH4319ZiiHDjel7j_ingoIqmTswzt2d6uc"  # pon tu clave aquí
BASE_URL = "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"

DATA_DIR = "aemet_data"
LOG_FILE = "log.txt"

os.makedirs(DATA_DIR, exist_ok=True)


def fetch_and_save_block(fecha_ini, fecha_fin, max_retries=5):
    """
    Descarga un bloque y lo guarda en un CSV.
    Incluye backoff progresivo en caso de fallo.
    USA HEADERS PARA LA API KEY Y CONTRA CACHÉ.
    """
    filename = os.path.join(DATA_DIR, f"aemet_{fecha_ini.split('T')[0]}_{fecha_fin.split('T')[0]}.csv")
    if os.path.exists(filename):
        return ("skip", f"⏩ Ya descargado {fecha_ini} - {fecha_fin}")

    delay = 10
    for attempt in range(1, max_retries + 1):
        try:
            # --- CAMBIOS CLAVE AQUÍ ---
            url = f"{BASE_URL}/fechaini/{fecha_ini}/fechafin/{fecha_fin}/todasestaciones"
            headers = {
                'cache-control': "no-cache",
                'api_key': API_KEY  # La clave ahora va en el header
            }
            
            # 1. Petición inicial para obtener la URL de los datos
            # quitamos el 'params' y usamos 'headers'
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            response_json = r.json()
            
            # La API devuelve un estado 200 pero puede indicar que no hay datos
            if response_json.get("estado") == 404:
                 return ("nodata", f"⚠️ Sin datos (respuesta 404 de la API) en {fecha_ini} - {fecha_fin}")

            data_url = response_json.get("datos")
            if not data_url:
                return ("nodata", f"⚠️ Sin datos (URL no encontrada) en {fecha_ini} - {fecha_fin}")

            # 2. Descarga real de los datos desde la URL obtenida
            # Esta segunda petición no necesita headers
            r_data = requests.get(data_url, timeout=60)
            r_data.raise_for_status()
            data = r_data.json()

            if not data:
                return ("nodata", f"⚠️ Sin datos (fichero JSON vacío) en {fecha_ini} - {fecha_fin}")

            # Guardamos CSV
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            return ("ok", f"✅ Guardados {len(df)} registros de {fecha_ini} - {fecha_fin}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return ("nodata", f"⚠️ Sin datos (HTTP 404) en {fecha_ini} - {fecha_fin}")
            # Otros errores HTTP se reintentan
            if attempt >= max_retries:
                 with open(LOG_FILE, "a") as f:
                    f.write(f"{fecha_ini},{fecha_fin}\n")
                 return ("fail", f"❌ Error HTTP en {fecha_ini} - {fecha_fin}: {e}")
            time.sleep(delay)
            delay *= 2

        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
            else:
                with open(LOG_FILE, "a") as f:
                    f.write(f"{fecha_ini},{fecha_fin}\n")
                return ("fail", f"❌ Error general en {fecha_ini} - {fecha_fin} tras {max_retries} intentos: {e}")


def load_failed_ranges():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    return [tuple(line.strip().split(",")) for line in lines if line.strip()]


def clear_log():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)


def build_intervals(hoy, hace_10):
    intervals = []
    fecha_fin = hoy
    while fecha_fin > hace_10:
        fecha_ini = fecha_fin - timedelta(days=15)
        if fecha_ini < hace_10:
            fecha_ini = hace_10
        # Formato AEMET: AAAA-MM-DDTHH:MM:SSUTC
        intervals.append((
            fecha_ini.strftime("%Y-%m-%dT00:00:00UTC"),
            fecha_fin.strftime("%Y-%m-%dT23:59:59UTC")
        ))
        fecha_fin = fecha_ini - timedelta(days=1)
    return intervals


def process_intervals(intervals, workers=3):
    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_and_save_block, fi, ff): (fi, ff) for fi, ff in intervals}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Procesando bloques"):
            status, msg = future.result()
            results.append(status)
            tqdm.write(msg)

    return results


def main(retries_only=False, workers=3):
    start_time = time.time()

    if retries_only:
        failed = load_failed_ranges()
        if not failed:
            print("✅ No hay intervalos pendientes en log.txt")
            return
        tqdm.write(f"🔄 Reintentando {len(failed)} intervalos fallidos...")
        clear_log()
        results = process_intervals(failed, workers=workers)
    else:
        
        hoy = datetime.today() - timedelta(days=1)
        hace_10 = hoy - timedelta(days=365*10)

        intervals = build_intervals(hoy, hace_10)
        failed = load_failed_ranges()

        if failed:
            tqdm.write(f"🔄 Reintentando {len(failed)} intervalos fallidos previos...")
            intervals = failed + intervals
            clear_log()

        results = process_intervals(intervals, workers=workers)

    # 📊 Resumen final
    total = len(results)
    ok = results.count("ok")
    skip = results.count("skip")
    nodata = results.count("nodata")
    fail = results.count("fail")
    elapsed = time.time() - start_time

    print("\n📊 Resumen de ejecución:")
    print(f"   ✅ Éxito: {ok}")
    print(f"   ⏩ Saltados (ya estaban): {skip}")
    print(f"   ⚠️ Sin datos: {nodata}")
    print(f"   ❌ Fallidos (guardados en log.txt): {fail}")
    print(f"   ⏱️ Tiempo total: {elapsed/60:.2f} minutos")


if __name__ == "__main__":
    retries_only = "--retries" in sys.argv
    workers = 3  # ⚙️ recomendable mantener bajo (2-3) para no saturar la API
    main(retries_only=retries_only, workers=workers)


