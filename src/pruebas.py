
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sys
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

API_KEY = os.getenv("AEMET_API_KEY", "")
BASE_URL = "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"

DATA_DIR = "aemet_data"
LOG_FILE = "log.txt"

os.makedirs(DATA_DIR, exist_ok=True)


def _peticion_datos_aemet(fecha_ini, fecha_fin):
    url = f"{BASE_URL}/fechaini/{fecha_ini}/fechafin/{fecha_fin}/todasestaciones"
    headers = {
        'cache-control': "no-cache",
        'api_key': API_KEY
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    response_json = r.json()
    if response_json.get("estado") == 404:
        return None
    data_url = response_json.get("datos")
    if not data_url:
        return None
    r_data = requests.get(data_url, timeout=60)
    r_data.raise_for_status()
    return r_data.json()


def fetch_and_save_block(fecha_ini, fecha_fin, max_retries=5):
    """
    Descarga un bloque y lo guarda en un CSV.
    Incluye backoff progresivo en caso de fallo.
    """
    filename = os.path.join(DATA_DIR, f"aemet_{fecha_ini.split('T')[0]}_{fecha_fin.split('T')[0]}.csv")
    if os.path.exists(filename):
        return ("skip", f"⏩ Ya descargado {fecha_ini} - {fecha_fin}")

    delay = 10
    for attempt in range(1, max_retries + 1):
        try:
            data = _peticion_datos_aemet(fecha_ini, fecha_fin)
            if not data:
                return ("nodata", f"⚠️ Sin datos en {fecha_ini} - {fecha_fin}")

            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            return ("ok", f"✅ Guardados {len(df)} registros de {fecha_ini} - {fecha_fin}")

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return ("nodata", f"⚠️ Sin datos (HTTP 404) en {fecha_ini} - {fecha_fin}")
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
    ok = results.count("ok")
    skip = results.count("skip")
    nodata = results.count("nodata")
    fail = results.count("fail")
    elapsed = time.time() - start_time

    print(f"\n📊 Resumen de ejecución ({len(results)} intervalos totales):")
    print(f"   ✅ Éxito: {ok}")
    print(f"   ⏩ Saltados (ya estaban): {skip}")
    print(f"   ⚠️ Sin datos: {nodata}")
    print(f"   ❌ Fallidos (guardados en log.txt): {fail}")
    print(f"   ⏱️ Tiempo total: {elapsed/60:.2f} minutos")


if __name__ == "__main__":
    retries_only = "--retries" in sys.argv
    workers = 3  # ⚙️ recomendable mantener bajo (2-3) para no saturar la API
    main(retries_only=retries_only, workers=workers)


