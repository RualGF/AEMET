import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px


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
    print(f"Rango de colores fijo: vmin = {vmin:.1f}, vmax = {vmax:.1f}")
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

def dibujar_coropletico_plotly(datos, nombre_columna, texto_titulo, etiqueta_leyenda):

    # gdf_for_centroids = gdf.to_crs(epsg=25830)
    gdf_unido = gdf.merge(datos, on='codigo_prov', how='left')

    # Rango de color
    vmin = datos[nombre_columna].min()
    vmax = datos[nombre_columna].max()
    if vmin == vmax:
        vmin = vmin * 0.9 if vmin != 0 else -1
        vmax = vmax * 1.1 if vmax != 0 else 1

    # Simula provincias sin datos como -999
    datos_plot = datos.copy()
    datos_plot[nombre_columna] = datos_plot[nombre_columna].fillna(-999)

    # Color scale con gris para -999 y luego escala Viridis
    color_scale = [
        [0.0, "lightgrey"],  # Para -999
        [0.00001, px.colors.sequential.Viridis[0]],  # Mismo inicio que la escala real
        [1.0, px.colors.sequential.Viridis[-1]]
    ]

    # Crear mapa
    fig_px = px.choropleth(
        data_frame=datos_plot,
        geojson=gdf_unido,
        locations="codigo_prov",
        featureidkey="properties.cod_prov",
        color=nombre_columna,
        color_continuous_scale=color_scale,
        range_color=(vmin, vmax),
        hover_name="nombre",
        hover_data={nombre_columna: ":.2f"}, # Formato y ocultar 'nombre' duplicado
        labels={nombre_columna: etiqueta_leyenda},
        title=texto_titulo
        #na_color="lightgrey"
    )
    
    # Centrado y zoom ajustado para España
    fig_px.update_geos(
        fitbounds="locations",
        visible=False,
        # center={"lat": 40.4, "lon": -3.7},
        # projection_scale=5,
        # lataxis_range=[34, 44],
        # lonaxis_range=[-10, 5],
        #showland=False,
        #showcountries=True,
        #countrycolor="black",
        #landcolor="lightgray",
        showsubunits=True,
        subunitcolor="darkgray"
    )
    #fig_px.update_traces(marker_line_width=0.5, marker_line_color="black")

    # Layout
    fig_px.update_layout(
        # title=dict(
        #     text=texto_titulo,
        #     font=dict(size=20),
        #     x=0.5,
        #     xanchor='center',
        #     y=0.96,
        #     yanchor='top'
        # ),
        margin=dict(l=0, r=0, t=80, b=0),
        height=900,
        width=900,
        coloraxis_colorbar=dict(
            title=etiqueta_leyenda,
            lenmode='pixels',
            len=200,
            x=1.02,
            y=0.5,
            xanchor='left', # Ancla la barra a la izquierda de la posición X
            yanchor='middle'
        ),
    )

    # Anotaciones: máx y mín
    anotaciones = []
    def añadir_anotacion(texto, punto, dx=1.0, dy=1.0, color="black"):
        anotaciones.append(dict(
            x=punto.x + dx,
            y=punto.y + dy,
            xref="x", yref="y",
            text=texto,
            showarrow=True,
            arrowhead=2,
            ax=-dx * 50, ay=-dy * 50,
            font=dict(size=12, color="black"),
            bgcolor="white",
            bordercolor=color,
            borderwidth=1
        ))
    #datos_validos = datos.dropna(subset=[nombre_columna])
    # Mínimo
    if datos[nombre_columna].notna().any():
        idx_min = datos[nombre_columna].idxmin()
        prov_min = datos.loc[idx_min, 'nombre']
        valor_min = datos.loc[idx_min, nombre_columna]
        p_min = gdf_unido[gdf_unido['nombre'] == prov_min].geometry.centroid.iloc[0]
        añadir_anotacion(f"Mín: {prov_min}<br>{valor_min:.1f}", p_min, dx=-1.0, dy=-1.0)
        
    # Máximo
        idx_max = datos[nombre_columna].idxmax()
        prov_max = datos.loc[idx_max, 'nombre']
        valor_max = datos.loc[idx_max, nombre_columna]
        p_max = gdf_unido[gdf_unido['nombre'] == prov_max].geometry.centroid.iloc[0]
        añadir_anotacion(f"Máx: {prov_max}<br>{valor_max:.1f}", p_max, dx=0.5, dy=0.5)

     # "Sin datos" en Castellón si corresponde
    sin_datos = gdf_unido[gdf_unido[nombre_columna].isna()]
    if not sin_datos.empty and 'Castellón' in sin_datos['nombre'].values:
        p_cas = sin_datos[sin_datos['nombre'] == 'Castellón'].geometry.centroid.iloc[0]
        añadir_anotacion("Sin datos", p_cas, dx=0.7, dy=-0.3, color="gray")

    fig_px.update_layout(annotations=anotaciones)

    return fig_px

