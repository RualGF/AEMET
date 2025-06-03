#Librerías
import pandas as pd

#Importar
df = pd.read_csv("../data/temperaturas_historicas_ampliadas.csv")

#Selección de columnas de interés

df_I = df[['indicativo', 'nombre', 'provincia', 'altitud', 'fecha', 'tmin', 'tmax', 'tmed',
           'hrMedia', 'prec', 'velmedia', 'racha']]

#Check duplicados

df_I.duplicated.any()

#Cast a números y ordenar por estación y fecha

numeric_columns = ["tmin", "tmax", "tmed", "prec", "velmedia", "racha", "altitud"]

for col in numeric_columns:
    df_I[col] = pd.to_numeric(df_I[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")

df_I["fecha"] = pd.to_datetime(df_I["fecha"], format="%Y-%m-%d", errors="coerce")

df_II = df_I.sort_values(["indicativo", "fecha"])

#Reemplazo de NAs
#Premisas
#A. No cambiar la distribución de las variables (Solo reemplazar en periodos de medición interrumpida, o gap_threshold, dentro del periódo de actividad)
#B. Eficiente computacionalmente.
#C. Preservar estructura temporal y espacial (Solo reemplazar NAs durante el período de actividad de la estación)

def smart_impute_respecting_operation(df, numeric_cols, gap_threshold=3):
    df = df.sort_values(["indicativo", "fecha"]).copy()

    station_ranges = df.groupby("indicativo")["fecha"].agg(["min", "max"])

    def fill_gaps(group):
        start, end = station_ranges.loc[group.name]
        group = group[(group["fecha"] >= start) & (group["fecha"] <= end)].copy() #Solo aplicar al periodo de actividad

        for col in numeric_cols:
            series = group[col]
            median_val = series.median()

            is_nan = series.isna()
            groups = (is_nan != is_nan.shift()).cumsum()

            for g in groups[is_nan].unique():
                gap_idx = groups[groups == g].index
                gap_len = len(gap_idx)

                if gap_len <= gap_threshold:
                    group.loc[gap_idx, col] = median_val

            group[col] = group[col].interpolate(method="linear", limit_direction="both")
            group[col] = group[col].fillna(median_val)

        return group

    df_imputed = df.groupby("indicativo").apply(fill_gaps)
    df_imputed.reset_index(drop=True, inplace=True)
    return df_imputed

numeric_cols = ["tmin", "tmax", "tmed", "hrMedia", "prec", "velmedia", "racha"]

df_III = smart_impute(df_II, numeric_cols, gap_threshold=3) #3 dias de interrumpción de medición

#Ajustes finales

df_III['prec'] = df_III['prec'].fillna(0)
df_IV = df_III.dropna(subset = ['tmed'])

#Guardar

ruta_salida = "data/temperaturas_limpias.csv"
df_IV.to_csv(ruta_salida, index=False)
print(":marca_de_verificación_blanca: Datos limpios guardados en:", ruta_salida)
print(":gráfico_de_barras: Dimensiones finales:", df_IV.shape)