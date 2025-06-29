import sys
import os   

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pandas as pd
import streamlit as st
from sqlalchemy import func, bindparam, Float


from src.extraer_datos import (
    df_provincias,
    df_comunidades, 
    tabla_dm, 
    generar_df_cache, 
    obtener_rango_de_fechas, 
    obtener_datos_diarios_filtrados
)

from src.dibujar import dibujar_coropletico_plotly, dibujar_grafico_lineas_evolucion
from src.personalizacion import load_css


# --- Configuración inicial de la app ---
st.set_page_config(
    page_title = "EDA",
    page_icon = "📈",
    layout = "wide",
    initial_sidebar_state = "collapsed"
    )
load_css('src/estilos.css')

# Sidebar con opción de limpieza de caché
with st.sidebar:
    if st.button("🧹 Limpiar caché y reiniciar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

st.title("Exploración de datos")
st.divider()

# La velocidad viene inicialmente en m/s, lo convierto a km/h para mejor entendimiento
velocidad_kmh_expr  = func.round(func.avg(tabla_dm.c.racha).cast(Float) * 3.6, 2)

metricas_disponibles = {
    "Altitud media (m)": {"col": "altitud", "expr": func.avg(tabla_dm.c.altitud), "unidad": "m"},
    "Temp. media (ºC)": {"col": "tmed", "expr": func.avg(tabla_dm.c.tmed), "unidad": "ºC"},
    "Temp. mínima (ºC)": {"col": "tmin", "expr": func.avg(tabla_dm.c.tmin), "unidad": "ºC"},
    "Temp. máxima (ºC)": {"col": "tmax", "expr": func.avg(tabla_dm.c.tmax), "unidad": "ºC"},
    "Precip. media (mm)": {"col": "prec", "expr": func.avg(tabla_dm.c.prec), "unidad": "mm"},
    "Racha media (km/h)": {"col": "racha", "expr": velocidad_kmh_expr , "unidad": "km/h"},
    "Humedad media (%)": {"col": "hrMedia", "expr": func.avg(tabla_dm.c.hrMedia), "unidad": "%"},
}

# Agrupamos expresiones para el SELECT del query
columnas_agregadas = [config["expr"].label(config["col"]) for config in metricas_disponibles.values()]

# Configuración para Streamlit en tabla
config_columnas_st = {
    conf["col"]: st.column_config.NumberColumn(label = nombre, format = "%.2f", help = conf["unidad"])
    for nombre, conf in metricas_disponibles.items()
}

orden_metricas = [conf["col"] for conf in metricas_disponibles.values()]

fecha_minima, fecha_maxima = obtener_rango_de_fechas()

def mostrar_tab_territorial(nivel_region: str) -> None:
    """
    Muestra la tabla y el mapa para provincias o comunidades autónomas.
    nivel_region: puede ser 'provincia' o 'ccaa'
    """
    assert nivel_region in ("provincia", "ccaa"), "Nivel territorial inválido"

    col_izq, col_centro, col_der = st.columns(3)    
    with col_izq:
        rango_fechas = st.date_input(
            "Selecciona un rango de fechas:",
            value = (fecha_minima, fecha_maxima),
            min_value = fecha_minima,
            max_value = fecha_maxima,
            format = "DD/MM/YYYY",
            key = f"fecha_{nivel_region}"
        )

    with col_der:
        metrica_seleccionada = st.selectbox("Métrica a visualizar:", list(metricas_disponibles.keys()), key = f"metrica_{nivel_region}")
        metrica_conf = metricas_disponibles[metrica_seleccionada]
        columna_metrica = metrica_conf["col"]

    if nivel_region == "provincia":
        with col_centro:
            filtro = st.multiselect("Elige la provincia:", df_provincias["nombre_prov"], placeholder="Opcional")
    else:
        with col_centro:
            filtro = st.multiselect("Elige la comunidad:", df_comunidades["nombre_ccaa"], placeholder="Opcional")

    if rango_fechas and len(rango_fechas ) == 2:
        parametros = {"fecha_inicio": rango_fechas [0], "fecha_fin": rango_fechas [1]}
        consulta_stmt = {
            "select": [tabla_dm.c.codigo_prov, *columnas_agregadas],
            "join": ["provincia"],
            "filters": [tabla_dm.c.fecha.between(bindparam("fecha_inicio"), bindparam("fecha_fin"))],
            "group_by": [tabla_dm.c.codigo_prov]
        }

        # Cache independiente por nivel
        clave_cache_df = f"df_{nivel_region}"
        clave_cache_parametros = f"{nivel_region}_params"
        df_resumen = generar_df_cache(clave_cache_df , clave_cache_parametros , consulta_stmt, **parametros)

        if not df_resumen.empty:
            df_resumen  = df_resumen.merge(df_provincias[["codigo_prov", "nombre_prov", "codigo_ca"]], on = "codigo_prov")

            if nivel_region == "ccaa":
                df_resumen  = df_resumen .merge(df_comunidades[["codigo_ca", "nombre_ccaa"]], on="codigo_ca")

            # Asegurar racha como numérico
            if "racha" in df_resumen.columns:
                df_resumen["racha"] = pd.to_numeric(df_resumen["racha"], errors = "coerce")

            # Aplicar filtros
            if nivel_region == "provincia" and filtro:
                df_resumen  = df_resumen [df_resumen ["nombre_prov"].isin(filtro)]
            elif nivel_region == "ccaa" and filtro:
                df_resumen  = df_resumen [df_resumen ["nombre_ccaa"].isin(filtro)]

            # Agregación para comunidades
            if nivel_region == "ccaa":
                columnas_presentes = [col for col in orden_metricas if col in df_resumen.columns]
                df_resumen  = df_resumen .groupby(["codigo_ca", "nombre_ccaa"], as_index = False)[columnas_presentes].mean()
                df_resumen  = df_resumen .rename(columns = {"codigo_ca": "cod_ccaa"})
                etiqueta_nombre = "nombre_ccaa"
                etiqueta_codigo  = "cod_ccaa"
                titulo_columna = "Comunidad Autónoma"
            else:
                etiqueta_nombre = "nombre_prov"
                etiqueta_codigo = "codigo_prov"
                columnas_presentes = [col for col in orden_metricas if col in df_resumen.columns]
                titulo_columna = "Provincia"

            # Ordenar
            df_resumen = df_resumen.sort_values(by = columna_metrica, ascending = False)
            df_resumen = df_resumen[[etiqueta_nombre, etiqueta_codigo] + columnas_presentes]
            
            st.dataframe(df_resumen, use_container_width = True, hide_index = True, column_config = {
                etiqueta_nombre: st.column_config.TextColumn(titulo_columna),
                etiqueta_codigo: None,
                **config_columnas_st
            })

            # Mapa
            titulo_grafico = f"{columna_metrica} por {nivel_region} del {rango_fechas[0].strftime('%d/%m/%Y')} al {rango_fechas[1].strftime('%d/%m/%Y')}"
            clave_cache_fig = f"fig_{nivel_region}"
            clave_cache_fig_parametros = f"{nivel_region}_fig_params"

            filtro_id = tuple(sorted(filtro)) if isinstance(filtro, list) else filtro or ""
            parametros_fig = (columna_metrica, titulo_grafico, filtro_id)

            if clave_cache_fig not in st.session_state or st.session_state.get(clave_cache_fig_parametros) != parametros_fig:
                

                fig = dibujar_coropletico_plotly(df_resumen, columna_metrica, titulo_grafico, nivel = nivel_region)
                st.session_state[clave_cache_fig] = fig
                st.session_state[clave_cache_fig_parametros] = parametros_fig
            
            # --- Obtener datos diarios para el gráfico de líneas ---
            # Necesitamos el nombre de la columna de la métrica (ej. 'tmed')
            columnas_diarias = metrica_conf["col"]
            
            # Determinar la lista de filtros para la consulta de datos diarios
            regiones_filtradas = filtro if filtro else []

            # Llamar a la nueva función para obtener los datos diarios
            df_diario = obtener_datos_diarios_filtrados(rango_fechas, nivel_region, regiones_filtradas, columnas_diarias)

            # Guardar todos los parámetros necesarios para el gráfico de líneas en un único diccionario
            # Solo se guarda si hay elementos seleccionados en el filtro
            if filtro: 
                st.session_state['line_plot_params'] = {
                    "df": df_diario,
                    "metric_col": columnas_diarias,
                    "display_name": metrica_seleccionada,
                    "level": nivel_region,
                    "name_col": etiqueta_nombre 
                }
            else:
                # Si no hay filtro, limpiar los parámetros del gráfico de líneas para que no se muestre
                st.session_state.pop("line_plot_params", None)

            with st.sidebar:
                st.spinner("Cargando mapa...")
                st.write(f"Mostrando {len(df_resumen)} registros tras filtros.")
            st.plotly_chart(st.session_state[clave_cache_fig], use_container_width=True)

            st.divider()

    # # Sección para el gráfico de líneas de evolución (solo si hay parámetros válidos)
    # if 'line_plot_params' in st.session_state:
    #     # El expander se abre automáticamente si hay datos para mostrar
    #     with st.expander("Ver evolución diaria de la métrica seleccionada", expanded = True):
    #         params = st.session_state['line_plot_params']
    #         with st.spinner("Generando gráfico de líneas..."):
    #             fig_lineas = dibujar_grafico_lineas_evolucion(
    #                 params['df'], params['metric_col'], params['display_name'],
    #                 params['level'], params['name_col'], metricas_disponibles
    #             )
    #             st.plotly_chart(fig_lineas, use_container_width=True)

def main() -> None:
      
    pestañas  = st.tabs(["Por provincias", "Por comunidades autónomas"])
    with pestañas [0]:
        mostrar_tab_territorial("provincia")
    with pestañas [1]:
        mostrar_tab_territorial("ccaa")
    
    if st.button("Volver a Inicio"):
            st.switch_page("Inicio.py")

if __name__ == "__main__":
    
    main()
