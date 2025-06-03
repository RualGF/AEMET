#Librerías
import pandas as pd

#Importar
df = pd.read_csv("../data/temperaturas_historicas_ampliadas.csv")


#Selección de columnas de interés

df_I = df[['id_descarga', 'idema', 'nombre_estacion', 'timestamp_estacion', 'provincia', 'altitud', 'fecha', 'tmin', 'tmax', 'tmed',
           'hrMedia', 'prec', 'velmedia', 'racha']]


#Cast a números y ordenar por estación y fecha

numeric_columns = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "altitud"]
date_columns = ["fecha", "timestamp_extraccion"]

for col in numeric_columns:
    df_I[col] = pd.to_numeric(df_I[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")

for date_col in date_columns:
    df_I.loc[:, date_col] = pd.to_datetime(df_I[date_col], format="%Y-%m-%d", errors="coerce")

df_II = df_I.sort_values(["indicativo", "fecha"])


#Tratamiento de NAs
#Premisas

#A. Preservar la distribución de las variables
#B. Preservar la estructura temporal y espacial de los datos
#C. No reemplazar valores fuera del periodo de actividad de las estaciones

def smart_impute_respecting_operation(df, numeric_cols, gap_threshold=3): # gap_threshold es el limite de días seguidos sin Na para reemplazar por la mediana
    df = df.sort_values(["idema", "fecha"]).copy() #Ordenar por estación y fecha para poder interpolar linealmente

    station_ranges = df.groupby("idema")["fecha"].agg(["min", "max"]) #Definir el periodo de actividad de cada estación

    def fill_gaps(group):
        start, end = station_ranges.loc[group.name]
        group = group[(group["fecha"] >= start) & (group["fecha"] <= end)].copy()

        for col in numeric_cols:
            series = group[col]
            median_val = series.median() #Calcular la mediana para cada variable numérica

            is_nan = series.isna() #Serie booleana de Nas
            groups = (is_nan != is_nan.shift()).cumsum() #Identificar los gaps (bloque continuo de NAs) con shift y cada gap recibe un número de grupo único

            for g in groups[is_nan].unique():
                gap_idx = groups[groups == g].index
                gap_len = len(gap_idx) #Cantidad de días consecutivoss con NAs

                if gap_len <= gap_threshold:
                    group.loc[gap_idx, col] = median_val #Si el periodo consecutivo con NAs (gap) es menor o igual al gap_threshold en el periodo de actividad, entonces replazar con mediana

            group[col] = group[col].interpolate(method="linear", limit_direction="both") #Imputar linealmente en gaps mayores al gap_threshold
            group[col] = group[col].fillna(median_val) #Si quedó algún gap, entonces completar con la mediana

        return group

    df_imputed = df.groupby("idema").apply(fill_gaps) #Agrupar por estación y reemplazar Na
    df_imputed.reset_index(drop=True, inplace=True)

    # Descartar filas que aun preserven valores NA para el target
    df_imputed = df_imputed.dropna(subset=['tmed']).reset_index(drop=True)

    # Reemplazar con valor '0' los Na en la variable precipitación
    if 'prec' in df_imputed.columns:
        df_imputed['prec'] = df_imputed['prec'].fillna(0)

    # Incorporar ID único de limpieza
    df_imputed["id_limpieza"] = range(len(df_imputed))

    # Ordenar output
    ordered_columns = [
        'id_descarga', 'id_limpieza' 'idema', 'nombre_estación', 'timestamp_estacion',
        'provincia', 'altitud', 'fecha', 'tmin', 'tmax', 'tmed',
        'hrMedia', 'prec', 'velmedia', 'racha'
    ]
    final_columns = [col for col in ordered_columns if col in df_imputed.columns]

    return df_imputed[final_columns]


#Ejecutar tratamiento

numeric_cols = ["tmin", "tmax", "tmed", "hrMedia", "prec", "velmedia", "racha"]

df_III = smart_impute_respecting_operation(df_II, numeric_cols, gap_threshold=3) #3 dias de interrumpción de medición

#Guardar

ruta_salida = "data/temperaturas_limpias.csv"
df_III.to_csv(ruta_salida, index=False)
print(":marca_de_verificación_blanca: Datos limpios guardados en:", ruta_salida)
print(":gráfico_de_barras: Dimensiones finales:", df_III.shape)