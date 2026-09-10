import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

DATA_URL = "https://ourworldindata.org/grapher/life-expectancy.csv"


st.set_page_config(
    page_title="Reporte Ejecutivo - Our World in Data",
    layout="wide"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)


st.title("Reporte Ejecutivo con Datos Públicos")
st.caption("Fuente: Our World in Data | Procesamiento: Python + Streamlit")

try:
    # Carga de datos
    df = load_data()

    # Identificación automática de la columna de valores
    base_columns = {"Entity", "Code", "Year"}
    value_columns = [column for column in df.columns if column not in base_columns]

    if not value_columns:
        raise ValueError("No se encontró una columna numérica de esperanza de vida.")

    value_col = next(
        (column for column in value_columns if pd.api.types.is_numeric_dtype(df[column])),
        value_columns[0]
    )

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=["Entity", "Year", value_col]).copy()
    df["Year"] = df["Year"].astype(int)

    # Confirmación de conexión
    st.success("Conexión realizada correctamente con el repositorio público.")

    # Barra lateral: países
    countries = sorted(df["Entity"].dropna().unique().tolist())
    default_countries = [
        country for country in ["Mexico", "United States", "Spain"]
        if country in countries
    ]

    selected_countries = st.sidebar.multiselect(
        "Selecciona países",
        options=countries,
        default=default_countries
    )

    # Barra lateral: periodo
    years = sorted(df["Year"].dropna().unique().tolist())

    if not years:
        raise ValueError("No existen años disponibles en la fuente de datos.")

    min_year = min(years)
    max_year = max(years)

    initial_min_year = max(min_year, max_year - 29)

    selected_year_range = st.sidebar.slider(
        "Rango de años",
        min_value=min_year,
        max_value=max_year,
        value=(initial_min_year, max_year),
        step=1
    )

    # Filtrado
    filtered = df[
        df["Entity"].isin(selected_countries)
        & df["Year"].between(selected_year_range[0], selected_year_range[1])
    ].copy()

    # Indicadores principales
    st.subheader("Indicadores principales")

    if not filtered.empty:
        ordered = filtered.sort_values(["Entity", "Year"]).copy()

        latest = (
            ordered.groupby("Entity", as_index=False)
            .tail(1)
            .sort_values("Entity")
            .reset_index(drop=True)
        )

        metric_columns = st.columns(len(latest))

        for column, (_, row) in zip(metric_columns, latest.iterrows()):
            column.metric(
                label=row["Entity"],
                value=f'{row[value_col]:.1f} años'
            )
    else:
        latest = pd.DataFrame(columns=filtered.columns)
        st.info("No existen datos para los filtros seleccionados.")

    # Evolución histórica
    st.subheader("Evolución histórica")

    if not filtered.empty:
        fig, ax = plt.subplots(figsize=(10, 5))

        for country in selected_countries:
            country_data = filtered[filtered["Entity"] == country].sort_values("Year")

            if not country_data.empty:
                ax.plot(
                    country_data["Year"],
                    country_data[value_col],
                    label=country
                )

        ax.set_xlabel("Año")
        ax.set_ylabel("Esperanza de vida")
        ax.legend()
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No existen datos para los filtros seleccionados.")

    # Tabla de datos
    st.subheader("Tabla de datos")
    st.dataframe(filtered, use_container_width=True)

    # Descarga
    csv_data = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Descargar datos filtrados en CSV",
        data=csv_data,
        file_name="reporte_esperanza_vida.csv",
        mime="text/csv"
    )

    # Conclusión automática
    st.subheader("Conclusión automática")

    if not latest.empty:
        highest = latest.loc[latest[value_col].idxmax()]
        lowest = latest.loc[latest[value_col].idxmin()]
        latest_year = int(latest["Year"].iloc[0])

        conclusion = (
            f'En el último año disponible dentro del rango seleccionado, '
            f'{highest["Entity"]} presenta el valor más alto '
            f'({highest[value_col]:.1f} años), mientras que '
            f'{lowest["Entity"]} registra {lowest[value_col]:.1f} años.'
        )

        st.write(conclusion)
    else:
        st.write("No es posible generar una conclusión porque no existen datos para los filtros seleccionados.")

except Exception as error:
    st.error("No fue posible cargar o procesar la información.")
    st.exception(error)
