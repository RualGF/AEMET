import os
import pandas as pd
import json

# Cargar el archivo txt (que contiene un JSON)
with open("data/estaciones_crudas.txt", "r", encoding="ISO-8859-15") as f:
    contenido = f.read()
    datos = json.loads(contenido)

# Convertir a DataFrame
df = pd.DataFrame(datos)

# Verificamos columnas clave
if "indicativo" not in df.columns or "provincia" not in df.columns:
    print("❌ Las columnas necesarias no están presentes.")
    print(f"Columnas encontradas: {df.columns.tolist()}")
    exit()

# Eliminar duplicados por 'indicativo'
df = df.drop_duplicates(subset="indicativo")

# Seleccionar columnas útiles
columnas_utiles = ["indicativo", "nombre", "provincia", "latitud", "longitud", "altitud"]
df = df[columnas_utiles]

# Seleccionar una estación representativa por provincia
df_filtrado = df.groupby("provincia").first().reset_index()

# Guardar
os.makedirs("data", exist_ok=True)
df_filtrado.to_csv("data/estaciones_filtradas.csv", index=False)
print("✅ Estaciones filtradas guardadas en data/estaciones_filtradas.csv")

