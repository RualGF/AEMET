import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from src.extraer_datos import ejecutar_consulta_a_dataframe
from src.personalizacion import load_css

st.set_page_config(
    page_title="Proyecto Grupo D",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
    )

def mapear_meses(meses_con_datos):
    mapa_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
    meses_con_datos = [mapa_meses[mes] for mes in meses_con_datos]
    return meses_con_datos


def analyze_temperature_data(df):
    """
    Realizar análisis de temperatura con detección de outliers y crear visualizaciones.
    """

    #Parse feche a datetime
    if 'fecha' not in df.columns or 'tmed' not in df.columns:
        st.error("Los datos deben contener las columnas 'fecha' y 'tmed'")
        return None, None
    
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])
    
    if 'provincia' in df.columns:
        df['provincia'] = df['provincia'].str.strip().str.title()
    
    datos = df['tmed'].dropna()
    
    if len(datos) == 0:
        st.error("No hay datos válidos de temperatura media")
        return None, None
    
    # Detección outliers utilizando Tukey
    q1 = datos.quantile(0.25)
    q3 = datos.quantile(0.75)
    iqr = q3 - q1
    limite_bajo = q1 - 1.5 * iqr
    limite_alto = q3 + 1.5 * iqr
    
    normales = datos[(datos >= limite_bajo) & (datos <= limite_alto)]
    atipicos = datos[(datos < limite_bajo) | (datos > limite_alto)]
    
    puntos = np.linspace(datos.min(), datos.max(), 30)
    
# COMPARADOR DE TEMPERATURAS PARA ESPAÑA (2023 vs 2024)
    # Calculamos para cada fecha: media, mediana, mínimo y máximo de tmed
    estad = (
        df
        .groupby('fecha')['tmed']
        .agg(['mean', 'median', 'min', 'max'])
        .reset_index()
    )
    
    # Separamos en 2023 y en 2024
    estad_2023 = estad[estad['fecha'].dt.year == 2023]
    estad_2024 = estad[estad['fecha'].dt.year == 2024]
    
    # Crear figura con 4 subplots (2 filas, 2 columnas) + comparación temporal
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(3, 2, height_ratios=[1, 1.2, 1.5])
    
    # Plots superiores (análisis original)
    ax_histo = fig.add_subplot(gs[0, 0])
    ax_caja = fig.add_subplot(gs[0, 1])
    
    # Histograma
    ax_histo.hist(normales, bins=puntos, alpha=0.7, label='Días normales (Tukey)', color='skyblue')
    ax_histo.hist(atipicos, bins=puntos, alpha=0.7, label='Días atípicos (Tukey)', color='orange')
    ax_histo.set_title('Histograma de Temperatura Media')
    ax_histo.set_xlabel('Temperatura media (°C)')
    ax_histo.set_ylabel('Cantidad de días')
    ax_histo.legend()
    
    # Boxplot general
    ax_caja.boxplot(
        datos,
        vert=True,
        showfliers=True,
        patch_artist=True,
        boxprops=dict(facecolor='skyblue', color='black'),
        flierprops=dict(marker='o', markerfacecolor='orange', markersize=5, alpha=0.7)
    )
    ax_caja.set_title('Boxplot General de Temperatura Media')
    ax_caja.set_ylabel('Temperatura media (°C)')
    
    # Boxplot mensual
    ax_mensual = fig.add_subplot(gs[1, :])
    
    # Agregar columna de mes
    df['mes'] = df['fecha'].dt.month
    valores_por_mes = [df[df['mes'] == m]['tmed'].dropna() for m in range(1, 13)]
    medias_por_mes = [mes.mean() if not mes.empty else np.nan for mes in valores_por_mes]
    
    meses_con_datos = [i for i, valores in enumerate(valores_por_mes, 1) if not valores.empty]
    valores_filtrados = [valores for valores in valores_por_mes if not valores.empty]
    medias_filtradas = [media for media in medias_por_mes if not np.isnan(media)]
    
    meses_con_datos = mapear_meses(meses_con_datos)
    
    if valores_filtrados:
        ax_mensual.boxplot(valores_filtrados, tick_labels=meses_con_datos, showfliers=True)
        ax_mensual.plot(
            range(1, len(medias_filtradas) + 1), medias_filtradas,
            marker='o', linestyle='-', color='red', label='Media mensual'
        )
        ax_mensual.set_title('Boxplot Mensual de Temperatura Media')
        ax_mensual.set_xlabel('Mes')
        ax_mensual.set_ylabel('Temperatura media (°C)')
        ax_mensual.legend()
    
    # Comparación temporal 2023 vs 2024
    if len(estad_2023) > 0 and len(estad_2024) > 0:
        # Subplot para 2023
        ax_2023 = fig.add_subplot(gs[2, 0])
        ax_2023.plot(estad_2023['fecha'], estad_2023['mean'], color='orange', label='Media 2023', linewidth=2)
        ax_2023.plot(estad_2023['fecha'], estad_2023['median'], color='orange', linestyle='--', label='Mediana 2023')
        ax_2023.fill_between(
            estad_2023['fecha'],
            estad_2023['min'],
            estad_2023['max'],
            color='orange', alpha=0.1,
            label='Rango 2023 (min-max)'
        )
        ax_2023.set_title('España: Temperaturas Diarias 2023', fontsize=12)
        ax_2023.set_ylabel('Temperatura (°C)')
        ax_2023.legend(fontsize=9)
        ax_2023.tick_params(axis='x', rotation=45)
        
        # Subplot para 2024
        ax_2024 = fig.add_subplot(gs[2, 1])
        ax_2024.plot(estad_2024['fecha'], estad_2024['mean'], color='blue', label='Media 2024', linewidth=2)
        ax_2024.plot(estad_2024['fecha'], estad_2024['median'], color='blue', linestyle='--', label='Mediana 2024')
        ax_2024.fill_between(
            estad_2024['fecha'],
            estad_2024['min'],
            estad_2024['max'],
            color='blue', alpha=0.1,
            label='Rango 2024 (min-max)'
        )
        ax_2024.set_title('España: Temperaturas Diarias 2024', fontsize=12)
        ax_2024.set_ylabel('Temperatura (°C)')
        ax_2024.set_xlabel('Fecha')
        ax_2024.legend(fontsize=9)
        ax_2024.tick_params(axis='x', rotation=45)
        
        # Sincronizar escalas Y para mejor comparación
        y_min = min(estad_2023['min'].min(), estad_2024['min'].min()) - 2
        y_max = max(estad_2023['max'].max(), estad_2024['max'].max()) + 2
        ax_2023.set_ylim(y_min, y_max)
        ax_2024.set_ylim(y_min, y_max)

    plt.tight_layout()
    
    return fig, df

def calculate_statistics(df):
    """
    Calcular estadísticas descriptivas para año y mes
    """
    # Agregar columna años
    df['año'] = df['fecha'].dt.year
    
    años = sorted(df['año'].unique())
    
    stats_dict = {}
    for año in años:
        year_data = df[df['año'] == año]['tmed'].describe()
        stats_dict[str(año)] = year_data
    
    # Estadísticas anuales
    stats_dict['Total'] = df['tmed'].describe()
    
    # Crear df de resumen
    resumen = pd.DataFrame(stats_dict)
    
    # Agregar columna de variación
    if len(años) > 1:
        for i in range(1, len(años)):
            col_name = f'Variación {años[i-1]}-{años[i]}'
            resumen[col_name] = resumen[str(años[i])] - resumen[str(años[i-1])]
    
    # Estadísticas mensuales
    resumen_mensual = None
    if len(años) > 1:
        monthly_stats = {}
        for año in años:
            year_monthly = df[df['año'] == año].groupby('mes')['tmed'].describe()
            for col in year_monthly.columns:
                monthly_stats[f'{col}_{año}'] = year_monthly[col]
        
        if monthly_stats:
            resumen_mensual = pd.DataFrame(monthly_stats)
            
            # Agregar variaciones anuales
            if len(años) == 2:
                resumen_mensual[f'Variación_media_{años[0]}-{años[1]}'] = (
                    resumen_mensual[f'mean_{años[1]}'] - resumen_mensual[f'mean_{años[0]}']
                )
    return resumen, resumen_mensual

def display_conclusions():
    """
    Desplegar conclusiones sobre el análisis de temperatura media
    """
    st.subheader("🔍 Conclusiones del Análisis")
    
    # Conclusiones
    st.markdown("### Comparación Interanual (2023 vs 2024)")
    
    with st.container():
        st.markdown("""
        **Tendencia General:**
        - En general, **2024 fue más frío que 2023**: la media bajó casi **3 °C**, como se ve en la fila "mean" de la tabla anual.
        
        **Análisis Mensual:**
        - **Mayor caída de temperatura**: ocurrió en **octubre y junio**, con casi **-2 °C** de diferencia respecto a 2023.
        - **Excepción**: **Noviembre** fue más cálido en 2024 que en 2023, lo que puede sugerir un **retraso en el enfriamiento otoñal**.
        """)
    
    st.divider()
    
    # Registro de temperaturas por provincia
    st.markdown("### Registros de Temperatura por Provincia")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Año 2024", "Agosto 2024", "15 Enero 2024"])
    
    with tab1:
        st.markdown("**Temperatura Media 2024 por Provincia (España)**")
        col1, col2 = st.columns(2)
        with col1:
            st.success("**Mínima**: Castellón **4.5 °C**")
            st.caption("La media anual más baja")
        with col2:
            st.error("**Máxima**: Las Palmas **21.0 °C**")
            st.caption("La más cálida del año")
    
    with tab2:
        st.markdown("**Temperatura Media Agosto 2024 por Provincia (España)**")
        col1, col2 = st.columns(2)
        with col1:
            st.success("**Mínima**: Cantabria **18.0 °C**")
            st.caption("La más fresca del mes")
        with col2:
            st.error("**Máxima**: Jaén **29.6 °C**")
            st.caption("La más calurosa")
    
    with tab3:
        st.markdown("**Temperatura Media el 15 de Enero de 2024**")
        col1, col2 = st.columns(2)
        with col1:
            st.success("**Mínima**: Huesca **6.9 °C**")
            st.caption("La provincia más fría ese día")
        with col2:
            st.error("**Máxima**: Las Palmas **21.5 °C**")
            st.caption("La más templada")
    
    # Observaciones adicionales
    st.divider()
    st.markdown("### Observaciones Adicionales")
    
    with st.expander("Patrones Geográficos"):
        st.markdown("""
        - **Las Palmas** (Canarias) consistentemente registra las temperaturas más altas, tanto en promedios anuales como en días específicos.
        - **Castellón** presenta la media anual más baja, reflejando su clima mediterráneo continental.
        - **Cantabria** muestra temperaturas moderadas en verano debido a su ubicación atlántica.
        - **Huesca** y **Jaén** representan los extremos de las temperaturas invernales y estivales respectivamente.
        """)
    
    with st.expander("📈 Implicaciones Climáticas"):
        st.markdown("""
        - El descenso de **3°C** en la media anual entre 2023 y 2024 sugiere una **variabilidad climática significativa**.
        - El retraso del enfriamiento otoñal (noviembre más cálido) podría indicar **cambios en los patrones estacionales**.
        - La diferencia de **-2°C** en octubre y junio muestra que los **meses de transición** fueron particularmente afectados.
        """)

def main():
    load_css('src/estilos.css')
    st.title("Datos históricos de la AEMET")
    st.divider()

    with st.spinner("Cargando datos históricos... Por favor, espera."):
        df = ejecutar_consulta_a_dataframe()
    
    # Desplegar dataframe principal
    st.subheader("Datos Generales por Provincia")
    st.dataframe(df, hide_index=True, use_container_width=True, column_config={
        "nombre": st.column_config.TextColumn("Nombre de la provincia"),
        "codigo_prov": None,
        "AVG(d.altitud)": st.column_config.NumberColumn(label="Altitud media (m)", format="%.2f",),
        "AVG(d.tmed)": st.column_config.NumberColumn(label="Temp. media (ºC)", format="%.2f", help="Temperatura media"),
        "AVG(d.tmin)": st.column_config.NumberColumn(label="Temp. mínima (ºC)", format="%.2f", help="Temperatura mínima"),
        "AVG(d.tmax)": st.column_config.NumberColumn(label="Temp. máxima (ºC)", format="%.2f", help="Temperatura máxima"),
        "AVG(d.prec)": st.column_config.NumberColumn(label="Precip. media (mm)", format="%.2f", help="Precipitación media"),
        "AVG(d.racha) * 3.6": st.column_config.NumberColumn(label="Racha media (km/h)", format="%.2f", help="Velocidad media del viento"),
        "AVG(d.hrMedia)": st.column_config.NumberColumn(label="Humedad media (%)", format="%.2f", help="Humedad relativa media")
    })
    
    st.divider()
    
    # Analisis de temperatura
    st.subheader("Análisis Detallado de Temperatura")
    
    with st.spinner("Analizando datos de temperatura..."):
            df_a_analizar = ejecutar_consulta_a_dataframe("SELECT * FROM datos_meteorologicos")
            fig, analyzed_df = analyze_temperature_data(df_a_analizar.copy())
                
            if fig is not None:
            # Visualizaciones
                st.subheader("Visualizaciones de Temperatura")
                st.pyplot(fig)
                    
            # Estadisticas
                st.subheader("Estadísticas Descriptivas")
                    
                with st.spinner("Calculando estadísticas..."):
                    resumen, resumen_mensual = calculate_statistics(analyzed_df.copy())
                        
                    st.write("**Estadísticas por Año:**")
                    # Configuration for yearly statistics dataframe
                    yearly_column_config = {}
                    for col in resumen.columns:
                        if col.startswith('Variación'):
                            yearly_column_config[col] = st.column_config.NumberColumn(
                                label=col, 
                                format="%.2f", 
                                help="Diferencia de temperatura entre años (°C)"
                            )
                        elif col in ['2023', '2024', '2025', 'Total']:
                            yearly_column_config[col] = st.column_config.NumberColumn(
                                label=f"Año {col}" if col != 'Total' else col, 
                                format="%.2f", 
                                help="Estadísticas de temperatura (°C)"
                            )
                    
                    st.dataframe(resumen, use_container_width=True, column_config=yearly_column_config)
                        
                    if resumen_mensual is not None:
                        st.write("**Estadísticas Mensuales por Año:**")
                             # Configuration for monthly statistics dataframe
                        monthly_column_config = {}
                        for col in resumen_mensual.columns:
                            if 'Variación' in col:
                                monthly_column_config[col] = st.column_config.NumberColumn(
                                    label=col.replace('_', ' '), 
                                    format="%.2f", 
                                    help="Diferencia mensual de temperatura entre años (°C)"
                                )
                            elif any(stat in col for stat in ['mean', 'std', 'min', '25%', '50%', '75%', 'max']):
                                year = col.split('_')[-1] if '_' in col else ''
                                stat_name = col.split('_')[0] if '_' in col else col
                                stat_labels = {
                                    'mean': 'Media', 'std': 'Desv. Est.', 'min': 'Mínimo',
                                    '25%': 'Q1', '50%': 'Mediana', '75%': 'Q3', 'max': 'Máximo'
                                }
                                label = f"{stat_labels.get(stat_name, stat_name)} {year}".strip()
                                monthly_column_config[col] = st.column_config.NumberColumn(
                                    label=label, 
                                    format="%.2f", 
                                    help=f"Estadística mensual de temperatura para {year} (°C)"
                                )
                            elif 'count' in col:
                                year = col.split('_')[-1] if '_' in col else ''
                                monthly_column_config[col] = st.column_config.NumberColumn(
                                    label=f"Conteo {year}".strip(), 
                                    format="%.0f", 
                                    help="Número de días con datos"
                                )
                        
                        st.dataframe(resumen_mensual, use_container_width=True, column_config=monthly_column_config)
                        
                        st.subheader("Resumen de Outliers")
                        datos = analyzed_df['tmed'].dropna()
                        q1 = datos.quantile(0.25)
                        q3 = datos.quantile(0.75)
                        iqr = q3 - q1
                        limite_bajo = q1 - 1.5 * iqr
                        limite_alto = q3 + 1.5 * iqr
                        
                        normales = datos[(datos >= limite_bajo) & (datos <= limite_alto)]
                        atipicos = datos[(datos < limite_bajo) | (datos > limite_alto)]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Días normales", len(normales))
                        with col2:
                            st.metric("Días atípicos", len(atipicos))
                        with col3:
                            st.metric("% Días atípicos", f"{len(atipicos)/len(datos)*100:.1f}%")
                        
                        #Conclusiones
                        st.divider()
                        display_conclusions()
    
                    else:
                        st.info("Sube un archivo CSV con datos detallados de temperatura para ver análisis adicionales")

    # Agregar Botón de inicio
    st.divider()
    if st.button("Volver a Inicio", key="volver_inicio"):
        st.switch_page("Inicio.py")

if __name__ == "__main__":
    main()