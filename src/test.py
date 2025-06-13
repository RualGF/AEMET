import pandas as pd
import sys
from sqlalchemy import create_engine
import streamlit as st
import conectar
import unicodedata
import re # Asegúrate de que re esté importado

# --- Environment Check for popular.py ---
# ... (tu código de Environment Check existente) ...
# --- End Environment Check for popular.py ---


df = pd.read_csv(r".\data\temperaturas_limpias.csv")
provincias = pd.read_sql_table("provincias", con=conectar.conexion())

print("--- Provincias DataFrame Loaded ---")
print(provincias.head())

# --- Función de Normalización de Cadenas MEJORADA ---
# Esta versión es más agresiva: elimina todo lo que no sea letra o número, excepto espacios.
# Luego normaliza espacios.
def normalize_string(s):
    if pd.isna(s):
        return s
    s = str(s).lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')
    # NUEVO: Elimina cualquier carácter que no sea letra (a-z), número (0-9) o espacio (\s)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # NUEVO: Reemplaza múltiples espacios con uno solo y quita espacios al inicio/final
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# --- Mapeo Manual para Discrepancias Conocidas ---
# Este diccionario mapea el nombre NORMALIZADO de tu DF que no coincide,
# al nombre NORMALIZADO de la tabla de provincias con el que SÍ debería coincidir.
manual_province_map = {
    "sta cruz de tenerife": "santa cruz de tenerife", # Para STA. CRUZ DE TENERIFE
    "baleares": "illes balears",                       # Para BALEARES, aunque debería funcionar con 'contains', lo forzamos.
    # Añade aquí más mapeos si surgen otros nombres problemáticos:
    # "otra abreviatura": "nombre completo normalizado",
    # "nombre incorrecto": "nombre correcto normalizado",
}


# --- APLICAR NORMALIZACIÓN A LAS COLUMNAS ---
print("\n--- Normalizando nombres de provincia para el mapeo ---")
df['provincia_normalized'] = df['provincia'].apply(normalize_string)
provincias['nombre_normalized'] = provincias['nombre'].apply(normalize_string)

# --- APLICAR MAPEO MANUAL a la columna normalizada de df ---
# Esto sobrescribe los valores normalizados de df si están en el diccionario de mapeo.
df['provincia_normalized'] = df['provincia_normalized'].replace(manual_province_map)


# --- ESTRATEGIA PARA EL "MERGE" DE CONTENIDO (CONTAINS) ---

# Función para encontrar el codigo_prov basado en si provincia_normalized
# está contenida en nombre_normalized (esta función no cambia, ya está bien)
def get_codigo_prov_by_contains(provincia_name_df, provincias_df_lookup):
    if pd.isna(provincia_name_df) or not isinstance(provincia_name_df, str):
        return None

    search_pattern = re.escape(provincia_name_df) # Escapar caracteres especiales de regex
    matches = provincias_df_lookup[provincias_df_lookup['nombre_normalized'].str.contains(search_pattern, na=False)]

    if not matches.empty:
        return matches['codigo_prov'].iloc[0]
    return None

# Aplicar la función de búsqueda para crear la columna 'codigo_prov' directamente en df
print("\n--- Realizando mapeo por 'contiene' para codigo_prov (esto puede tardar)... ---")
df['codigo_prov'] = df['provincia_normalized'].apply(lambda x: get_codigo_prov_by_contains(x, provincias))

# Limpiar las columnas redundantes: la original 'provincia' y la normalizada 'provincia_normalized'.
valores_insertar = df.drop(columns=["provincia", "provincia_normalized"])


# --- Manejo de valores NaN en 'codigo_prov' (sigue siendo CRÍTICO) ---
initial_rows = len(valores_insertar)
valores_insertar.dropna(subset=["codigo_prov"], inplace=True)
dropped_rows = initial_rows - len(valores_insertar)
if dropped_rows > 0:
    print(f"\nINFO: Se eliminaron {dropped_rows} filas donde 'provincia' no tuvo un 'codigo_prov' coincidente (incluso después de la búsqueda por 'contiene').")
    print(f"Filas restantes para la inserción: {len(valores_insertar)}")

# Convertir 'codigo_prov' a tipo entero
valores_insertar['codigo_prov'] = valores_insertar['codigo_prov'].astype(int)


print("\n--- head de valores_insertar después del mapeo y limpieza ---")
print(valores_insertar.head())
print("\n--- info de valores_insertar después del mapeo y limpieza ---")
print(valores_insertar.info())
print("Valores nulos en 'codigo_prov' después de la limpieza:", valores_insertar['codigo_prov'].isnull().sum())


# --- Inserción de Datos (usando un chunksize más pequeño) ---
print(f"\nIniciando inserción de {len(valores_insertar)} filas usando valores_insertar.to_sql()...")
valores_insertar.to_sql(
    name="datos_meteorologicos",
    con=conectar.conexion(),
    if_exists="replace",
    index=False,
    method="multi",
    chunksize=500,
)
print("¡Inserción de datos completada con éxito!")