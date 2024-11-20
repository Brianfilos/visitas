import pandas as pd
import streamlit as st
import plotly.express as px
import json

# Cargar archivos
uploaded_file_1 = st.file_uploader("Sube el archivo principal (Excel)", type=["xlsx"])
uploaded_file_2 = st.file_uploader("Sube el archivo con información CIIU (Excel)", type=["xlsx"])

if uploaded_file_1 and uploaded_file_2:
    # Leer los archivos Excel
    df = pd.read_excel(uploaded_file_1, sheet_name="datos")
    ciiu_df = pd.read_excel(uploaded_file_2)

    # Asegurarse de que la columna "Códigos CIIU" no tenga nulos y sea tipo string
    df['Códigos CIIU'] = df['Códigos CIIU'].fillna('').astype(str)

    # Separar número y descripción en "Códigos CIIU"
    df[['Código CIIU', 'Descripción CIIU']] = df['Códigos CIIU'].str.split(' - ', 1, expand=True)

    # Convertir "Código CIIU" a numérico
    df['Código CIIU'] = pd.to_numeric(df['Código CIIU'], errors='coerce')

    # Convertir "CIIU 4" a numérico
    ciiu_df['CIIU 4'] = pd.to_numeric(ciiu_df['CIIU 4'], errors='coerce')

    # Hacer el cruce por "Código CIIU" y "CIIU 4"
    df = df.merge(ciiu_df[['CIIU 4', 'TIPO']], left_on='Código CIIU', right_on='CIIU 4', how='left')

    # Gráfica: Cantidad de códigos por "TIPO"
    tipo_counts = df['TIPO'].value_counts().reset_index()
    tipo_counts.columns = ['TIPO', 'Cantidad']

    st.header("Gráfica de códigos por tipo")
    fig_tipo = px.bar(tipo_counts, x="TIPO", y="Cantidad", text="Cantidad", title="Cantidad de códigos por TIPO")
    fig_tipo.update_traces(textposition='outside')
    st.plotly_chart(fig_tipo)

    # Tabla resumen: Cantidad por "TIPO"
    st.header("Tabla resumen: Cantidad por tipo")
    st.dataframe(tipo_counts)

    # Top 10 códigos más recurrentes
    top_ciiu = df['Código CIIU'].value_counts().head(10).reset_index()
    top_ciiu.columns = ['Código CIIU', 'Cantidad']
    top_ciiu = top_ciiu.merge(df[['Código CIIU', 'Descripción CIIU']].drop_duplicates(), on='Código CIIU', how='left')

    st.header("Top 10 códigos más recurrentes")
    st.dataframe(top_ciiu)

    # Continuar con las funcionalidades existentes
    df["Fecha de la visita"] = pd.to_datetime(df["Fecha de la visita"], errors="coerce")
    valid_dates = df["Fecha de la visita"].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        st.sidebar.header("Filtrar por fecha")
        start_date = st.sidebar.date_input("Fecha inicial", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("Fecha final", value=max_date, min_value=min_date, max_value=max_date)

        if start_date and end_date:
            mask = (df["Fecha de la visita"].dt.date >= start_date) & (df["Fecha de la visita"].dt.date <= end_date)
            filtered_df = df[mask]

            if not filtered_df.empty:
                filtered_df["Mes"] = filtered_df["Fecha de la visita"].dt.to_period("M").astype(str)
                pivot_table = filtered_df.pivot_table(index="Profesional", columns="Mes", aggfunc="size", fill_value=0)

                st.header("Cantidad de visitas por profesional por mes")
                st.dataframe(pivot_table)

                visit_counts = filtered_df["Profesional"].value_counts().reset_index()
                visit_counts.columns = ["Profesional", "Cantidad de visitas"]

                st.header("Gráfica de visitas por profesional")
                fig = px.bar(visit_counts, x="Profesional", y="Cantidad de visitas", text="Cantidad de visitas", title="Cantidad de visitas por profesional")
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig)

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
                    map_data = map_data.rename(columns={"lat": "latitude", "lng": "longitude"})
                    st.map(map_data, zoom=12)
                else:
                    st.warning("No hay coordenadas válidas para mostrar en el mapa.")
            else:
                st.warning("No hay datos en el rango de fechas seleccionado.")
    else:
        st.error("No hay fechas válidas en la columna 'Fecha de la visita'.")
