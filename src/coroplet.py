import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# GeoJSON
gdf = gpd.read_file('data/spain-provinces.geojson')
gdf['codigo_prov'] = gdf['cod_prov'].astype(int)

def dibujar_coropletico(datos, nombre_columna, texto_titulo, etiqueta_leyenda):
    """
    - datos: DataFrame con ['provincia', nombre_columna].
    - nombre_columna: columna a mapear (p.ej. 'tmed_promedio').
    - texto_titulo: título del gráfico.
    - etiqueta_leyenda: texto para la escala de colores.

    Provincias sin datos (NaN) se pintan en gris y la flecha 'Sin datos' apunta a Castellón,
    siempre que Castellón esté en el GeoDataFrame y falte en los datos.
    """
    
    vmin = datos[nombre_columna].min()
    vmax = datos[nombre_columna].max()
    print(f"Rango de colores fijo: vmin = {vmin:.1f}°C, vmax = {vmax:.1f}°C")
    # Unión geográfica
    
    gdf_unido = gdf.merge(datos, on='codigo_prov', how='left')
    
    # Manejo si vmin y vmax son iguales (ej. todos los valores son iguales o solo hay un valor)
    if vmin == vmax:
        vmin = vmin * 0.9 if vmin != 0 else -1
        vmax = vmax * 1.1 if vmax != 0 else 1
    
    # figura y eje
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Dibujamos el coroplético
    gdf_unido.plot(
        column=nombre_columna,
        cmap='coolwarm',
        vmin=vmin,
        vmax=vmax,
        legend=True,
        edgecolor='black',
        linewidth=0.4,
        ax=ax,
        legend_kwds={
            'label': etiqueta_leyenda,
            'shrink': 0.6,
            'ticks': np.linspace(vmin, vmax, 7).round(1) # Asegura que los ticks se ajustan y son legibles
        },
        missing_kwds={
            'color': 'lightgrey',
            'label': 'Sin datos'
        }
    )
    
    # Título y quitamos ejes
    ax.set_title(texto_titulo, fontsize=16, pad=30)
    ax.axis('off')
    
    # Anotamos provincia máxima 
    if datos[nombre_columna].notna().any():
        provincia_max = datos.loc[datos[nombre_columna].idxmax(), 'nombre']
        valor_max = datos[nombre_columna].max()
         # Asegúrate de que la provincia_max existe en gdf_unido
        if provincia_max in gdf_unido['nombre'].values:
            punto_max = gdf_unido[gdf_unido['nombre'] == provincia_max].geometry.centroid.iloc[0]
            ax.annotate(
                f"Máx: {provincia_max}\n{valor_max:.1f}", # Quitamos °C, se espera en la leyenda
                xy=(punto_max.x, punto_max.y),
                xytext=(punto_max.x + 1.0, punto_max.y - 1.0), # Ajusta estos valores para tu mapa
                arrowprops=dict(arrowstyle="->", color='black'),
                fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7)
            )
    
    # Anotamos provincia mínima
    if datos[nombre_columna].notna().any():
        idx_min = datos[nombre_columna].idxmin()
        provincia_min = datos.loc[idx_min, 'nombre']
        valor_min = datos[nombre_columna].min()

        if provincia_min in gdf_unido['nombre'].values:
            punto_min = gdf_unido[gdf_unido['nombre'] == provincia_min].geometry.centroid.iloc[0]
            ax.annotate(
                f"Mín: {provincia_min}\n{valor_min:.1f}", # Quitamos °C
                xy=(punto_min.x, punto_min.y),
                xytext=(punto_min.x - 2.0, punto_min.y + 1.0), # Ajusta estos valores
                arrowprops=dict(arrowstyle="->", color='black'),
                fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7)
            )
    
    # Buscamos el subconjunto de provincias con NaN en nombre_columna
    sin_datos = gdf_unido[gdf_unido[nombre_columna].isna()]
    
    # Verificamos primero si 'Castellón' está en esa lista
    if not sin_datos.empty and 'Castellón' in list(sin_datos['nombre']):
        # Seleccionamos la fila de Castellón
        fila_castellon = sin_datos[sin_datos['nombre'] == 'Castellón'].iloc[0]
        centroide_c = fila_castellon.geometry.centroid
        ax.annotate(
            "Sin datos",
            xy=(centroide_c.x, centroide_c.y),
            xytext=(centroide_c.x + 1.0, centroide_c.y - 1.0),
            arrowprops=dict(arrowstyle="->", color='black'),
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7)
        )
    # Si Castellón no existe (u otra provincia que falte), no se anota nada.
    
    plt.tight_layout()
    return fig
