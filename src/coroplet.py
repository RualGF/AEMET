import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import streamlit as st


@st.cache_data
def cargar_geojson_con_canarias_reubicadas(ruta_geojson):
    with open(ruta_geojson, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    codigos_provincias_canarias = {"35", "38"}  # Las dos provincias insulares
    codigos_ccaa_canarias = {"04"}  # Código de la CCAA Canarias en el GeoJSON de CCAA


    def desplazar_coords(coords):
        return [
            [[x + 5, y + 7] for x, y in ring if isinstance(ring, list)]
            for ring in coords if isinstance(ring, list)
        ]

    for feature in geojson["features"]:
        props = feature["properties"]
        geom = feature["geometry"]

        cod_prov = props.get("cod_prov")
        cod_ccaa = props.get("cod_ccaa")

        if cod_prov:  # GeoJSON de provincias
            cod = str(cod_prov).zfill(2)
            if cod in codigos_provincias_canarias:
                if geom["type"] == "Polygon":
                    geom["coordinates"] = desplazar_coords(geom["coordinates"])
                elif geom["type"] == "MultiPolygon":
                    geom["coordinates"] = [
                        [
                            [[x + 5, y + 7] for x, y in ring if isinstance(ring, list)]
                            for ring in polygon if isinstance(ring, list)
                        ]
                        for polygon in geom["coordinates"] if isinstance(polygon, list)
                    ]
        elif cod_ccaa:  # GeoJSON de CCAA
            cod = str(cod_ccaa).zfill(2)
            if cod in codigos_ccaa_canarias:
                if geom["type"] == "Polygon":
                    geom["coordinates"] = desplazar_coords(geom["coordinates"])
                elif geom["type"] == "MultiPolygon":
                    geom["coordinates"] = [
                        [
                            [[x + 5, y + 7] for x, y in ring if isinstance(ring, list)]
                            for ring in polygon if isinstance(ring, list)
                        ]
                        for polygon in geom["coordinates"] if isinstance(polygon, list)
                    ]

        # Asignar ID en todos los casos
        feature["id"] = str(cod_prov or cod_ccaa).zfill(2)

    return geojson
 
def dibujar_coropletico_plotly(datos, nombre_columna, texto_titulo, nivel='provincias'):
    """
    Visualización coroplética interactiva con Plotly.

    datos: DataFrame con columnas ['codigo_prov', 'nombre', nombre_columna].
    nombre_columna: columna de valores numéricos a mapear.
    texto_titulo: título del gráfico.
    etiqueta_leyenda: texto para la barra de color.
    """
    
    variables_config = {
        'tmed':    {'color': 'RdBu_r', 'label': 'Temp. media',     'unidad': '°C'},
        'tmin':    {'color': 'RdBu_r', 'label': 'Temp. mínima',    'unidad': '°C'},
        'tmax':    {'color': 'RdBu_r', 'label': 'Temp. máxima',    'unidad': '°C'},
        'prec':    {'color': 'Blues',  'label': 'Precipitación',   'unidad': 'mm'},
        'hrMedia': {'color': 'Purples','label': 'Humedad relativa','unidad': '%'},
        'racha':   {'color': 'Oranges','label': 'Racha viento',    'unidad': 'km/h'},
        'altitud': {'color': 'Greens', 'label': 'Altitud',         'unidad': 'm'}
    }

    geojson_provincias = cargar_geojson_con_canarias_reubicadas('data/spain-provinces.geojson')
    geojson_ccaa = cargar_geojson_con_canarias_reubicadas('data/spain-comunidad-autonoma.geojson')
    #geojson_ccaa = pd.read_json('data/spain-comunidad-autonoma.geojson')


    # Asegurarse de que los códigos sean string con ceros a la izquierda
    if nivel == 'ccaa':
        geojson_data = geojson_ccaa
        geojson_key = 'properties.cod_ccaa'
        location_col = 'cod_ccaa'
        base = pd.DataFrame([
            {'cod_ccaa': feature['properties']['cod_ccaa']}
            for feature in geojson_data['features']
        ])
        base['cod_ccaa'] = base['cod_ccaa'].astype(str).str.zfill(2)
        
        
        datos['cod_ccaa'] = datos['cod_ccaa'].astype(str).str.zfill(2)
        
        datos = datos.merge(base, on='cod_ccaa', how='left')
        
    else:
        geojson_data = geojson_provincias
        geojson_key = 'properties.cod_prov'
        location_col = 'codigo_prov'
        base = pd.DataFrame([
            {'codigo_prov': feature['properties']['cod_prov'], 'nombre': feature['properties']['name']}
            for feature in geojson_data['features']
        ])
        base['codigo_prov'] = base['codigo_prov'].astype(str).str.zfill(2)
        
        
        datos['codigo_prov'] = datos['codigo_prov'].astype(str).str.zfill(2)
        
        datos = base.merge(datos, on=['codigo_prov', 'nombre'], how='left')
    
    # Añadir columna auxiliar para gestionar NaN con color gris
    datos['_valor_plot'] = datos[nombre_columna].copy().fillna(-9999)
    unidad = variables_config.get(nombre_columna, {}).get('unidad', '')
    datos['_hover_valor'] = datos[nombre_columna].apply(
        lambda x: f"{x:.1f} {unidad}" if pd.notna(x) else "Sin datos")

    # Rango de color excluyendo el valor -9999
    vmin = datos.loc[datos['_valor_plot'] != -9999, '_valor_plot'].min()
    vmax = datos.loc[datos['_valor_plot'] != -9999, '_valor_plot'].max()
 
    if vmin == vmax:
        vmin = vmin * 0.9 if vmin != 0 else -1
        vmax = vmax * 1.1 if vmax != 0 else 1

    if "nombre" not in datos.columns:
        print("Columnas disponibles:", datos.columns)
        raise ValueError("El DataFrame debe tener una columna 'nombre' para el hover.")
    custom_cols = ['_hover_valor']
    if 'nombre' in datos.columns:
        custom_cols.insert(0, 'nombre')
     # Crear el mapa coroplético con hover customizado
    fig = px.choropleth(
        datos,
        geojson=geojson_data,
        locations=location_col,
        featureidkey=geojson_key,
        color='_valor_plot',
        color_continuous_scale=variables_config.get(nombre_columna, {}).get('color', 'RdBu_r'),
        range_color=(vmin, vmax),
        custom_data=custom_cols,
        title=texto_titulo
    )

    cfg = variables_config.get(nombre_columna, {})
    nombre_amigable = cfg.get('label', nombre_columna)
    string_para_hover_template = f"<b>%{{customdata[0]}}</b><br>{nombre_amigable}: %{{customdata[1]}}<extra></extra>"
    fig.update_traces(hovertemplate=string_para_hover_template)

    # Añadir capa para provincias sin datos (gris)
    for i, row in datos.iterrows():
        if row['_valor_plot'] == -9999:
            fig.add_trace(go.Choropleth(
                geojson=geojson_data,
                locations=[row[location_col]],
                z=[0],
                colorscale=[[0, 'lightgrey'], [1, 'lightgrey']],
                showscale=False,
                featureidkey=geojson_key,
                hoverinfo='skip'
            ))

    # Ajustes del mapa para asegurar buen tamaño
    fig.update_geos(fitbounds="geojson", visible=False)

    # Anotaciones para máximos y mínimos (si hay datos)
    if datos[nombre_columna].notna().any():
       
        idx_max = datos[nombre_columna].idxmax()
        entidad_max = datos.loc[idx_max, 'nombre']
        valor_max = datos.loc[idx_max, nombre_columna]

        idx_min = datos[nombre_columna].idxmin()
        entidad_min = datos.loc[idx_min, 'nombre']
        valor_min = datos.loc[idx_min, nombre_columna]

        resumen_extremos = f"📈 Máx: {entidad_max} ({valor_max:.1f} {unidad})    📉 Mín: {entidad_min} ({valor_min:.1f} {unidad})"
        
        fig.update_layout(
            title=dict(
                text=f"{texto_titulo}<br><sub>{resumen_extremos}</sub>",
                x=0.5, xanchor='center'
            ),
        coloraxis_colorbar=dict(
            title=f"{cfg.get('label', nombre_columna)} ({cfg.get('unidad', '')})",
            tickvals=np.linspace(vmin, vmax, 7).round(1)
        ),
        margin={"r":0,"t":80,"l":0,"b":0},
        height=700
    )

    return fig
