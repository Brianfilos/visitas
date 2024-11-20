import pandas as pd
import streamlit as st
import plotly.express as px
import json

# Cargar el archivo
uploaded_file = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="datos")

    # Convertir "Fecha de la visita" a datetime
    df["Fecha de la visita"] = pd.to_datetime(df["Fecha de la visita"], errors="coerce")

    # Extraer solo fechas válidas
    valid_dates = df["Fecha de la visita"].dropna()

    if not valid_dates.empty:
        # Obtener el rango mínimo y máximo de fechas
        min_date = valid_dates.min().date()  # Solo la fecha
        max_date = valid_dates.max().date()  # Solo la fecha

        # Selección de rango de fechas
        st.sidebar.header("Filtrar por fecha")
        start_date = st.sidebar.date_input("Fecha inicial", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("Fecha final", value=max_date, min_value=min_date, max_value=max_date)

        if start_date and end_date:
            # Filtrar datos por rango de fechas
            mask = (df["Fecha de la visita"].dt.date >= start_date) & (df["Fecha de la visita"].dt.date <= end_date)
            filtered_df = df[mask]

            if not filtered_df.empty:
                # Crear columna para agrupar por mes
                filtered_df["Mes"] = filtered_df["Fecha de la visita"].dt.to_period("M").astype(str)

                # Tabla dinámica: cantidad de visitas por profesional y mes
                pivot_table = filtered_df.pivot_table(index="Profesional", columns="Mes", aggfunc="size", fill_value=0)

                st.header("Cantidad de visitas por profesional por mes")
                st.dataframe(pivot_table)

                # Gráfica: total de visitas por profesional con etiquetas
                visit_counts = filtered_df["Profesional"].value_counts().reset_index()
                visit_counts.columns = ["Profesional", "Cantidad de visitas"]

                st.header("Gráfica de visitas por profesional")
                fig = px.bar(
                    visit_counts, 
                    x="Profesional", 
                    y="Cantidad de visitas", 
                    title="Cantidad de visitas por profesional",
                    text="Cantidad de visitas"  # Agregar etiquetas fijas
                )
                fig.update_traces(textposition='outside')  # Etiquetas fuera de las barras
                fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')  # Ajustar texto si es necesario
                st.plotly_chart(fig)

                # Mapa interactivo
                st.header("Mapa interactivo de visitas")
                def parse_coordinates(coord):
                    try:
                        parsed = json.loads(coord)
                        return parsed["lat"], parsed["lng"]
                    except:
                        return None, None

                filtered_df["lat"], filtered_df["lng"] = zip(*filtered_df["Georeferencia"].apply(parse_coordinates))
                map_data = filtered_df.dropna(subset=["lat", "lng"])[["lat", "lng", "Barrio / Vereda /paraje"]]

                if not map_data.empty:
                    # Renombrar columnas para st.map
                    map_data = map_data.rename(columns={"lat": "latitude", "lng": "longitude"})
                    st.map(map_data, zoom=12)
                else:
                    st.warning("No hay coordenadas válidas para mostrar en el mapa.")
            else:
                st.warning("No hay datos en el rango de fechas seleccionado.")
    else:
        st.error("No hay fechas válidas en la columna 'Fecha de la visita'.")

