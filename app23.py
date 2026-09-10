import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# A. Configuración inicial
st.set_page_config(page_title="Reporte Ejecutivo - Our World in Data", layout="wide")
st.title("Reporte Ejecutivo con Datos Públicos")
st.caption("Fuente: Our World in Data | Procesamiento: Python + Streamlit")

# B. Fuente de datos
@st.cache_data
def load_data():
    url = "https://ourworldindata.org/grapher/life-expectancy.csv"
    return pd.read_csv(url)

# C. Manejo de errores
try:
    df = load_data()
    st.success("Conexión realizada correctamente con el repositorio público.")
    
    # D. Identificación automática de la variable
    value_col = [col for col in df.columns if col not in ['Entity', 'Code', 'Year']][0]
    
    # E. Selector de países
    entities = sorted(df['Entity'].dropna().unique())
    default_countries = [c for c in ["Mexico", "United States", "Spain"] if c in entities]
    
    selected_countries = st.sidebar.multiselect(
        "Selecciona países", 
        options=entities, 
        default=default_countries
    )
    
    # F. Selector de periodo
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    default_start = max(min_year, max_year - 30)
    
    selected_years = st.sidebar.slider(
        "Rango de años", 
        min_value=min_year, 
        max_value=max_year, 
        value=(default_start, max_year)
    )
    
    # G. Filtrado
    filtered = df[
        (df['Entity'].isin(selected_countries)) & 
        (df['Year'] >= selected_years[0]) & 
        (df['Year'] <= selected_years[1])
    ].copy()
    
    if filtered.empty:
        st.warning("No existen datos para los filtros seleccionados.")
    else:
        # H. Indicadores principales
        st.header("Indicadores principales")
        latest = filtered.sort_values('Year').groupby('Entity').tail(1)
        
        cols = st.columns(len(latest))
        for idx, row in enumerate(latest.itertuples()):
            country = row.Entity
            val = getattr(row, value_col)
            cols[idx].metric(label=country, value=f"{val:.1f} años")
            
        # I. Evolución histórica
        st.header("Evolución histórica")
        fig, ax = plt.subplots(figsize=(10, 5))
        
        for country in selected_countries:
            country_data = filtered[filtered['Entity'] == country]
            if not country_data.empty:
                ax.plot(country_data['Year'], country_data[value_col], label=country)
                
        ax.set_xlabel("Año")
        ax.set_ylabel("Esperanza de vida")
        if not latest.empty:
            ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)
        
        # J. Tabla de datos
        st.header("Tabla de datos")
        st.dataframe(filtered, use_container_width=True)
        
        # K. Descarga
        csv = filtered.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="Descargar datos filtrados en CSV",
            data=csv,
            file_name="reporte_esperanza_vida.csv",
            mime="text/csv"
        )
        
        # L. Conclusión automática
        st.header("Conclusión automática")
        if len(latest) > 0:
            max_row = latest.loc[latest[value_col].idxmax()]
            min_row = latest.loc[latest[value_col].idxmin()]
            
            st.write(
                f"En el último año disponible dentro del rango seleccionado, {max_row['Entity']} "
                f"presenta el valor más alto ({max_row[value_col]:.1f} años), mientras que "
                f"{min_row['Entity']} registra {min_row[value_col]:.1f} años."
            )

except Exception as e:
    st.error("No fue posible cargar o procesar la información.")
    st.exception(e)