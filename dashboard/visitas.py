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

    # Validar y procesar la columna "Códigos CIIU"
    if 'Códigos CIIU' in df.columns:
        df['Códigos CIIU'] = df['Códigos CIIU'].fillna('').astype(str)
        valid_mask = df['Códigos CIIU'].str.contains(' - ')  # Solo filas con el formato válido
        df_valid = df[valid_mask].copy()  # Filtrar solo las filas válidas

        # Separar número y descripción en "Códigos CIIU"
        df_valid[['Código CIIU', 'Descripción CIIU']] = df_valid['Códigos CIIU'].str.split(' - ', 1, expand=True)

        # Convertir "Código CIIU" a numérico
        df_valid['Código CIIU'] = pd.to_numeric(df_valid['Código CIIU'], errors='coerce')

        # Manejo de filas no conformes (opcional)
        df_invalid = df[~valid_mask].copy()
        if not df_invalid.empty:
            st.warning(f"Se ignoraron {len(df_invalid)} filas con valores no válidos en 'Códigos CIIU'.")
    else:
        st.error("La columna 'Códigos CIIU' no está presente en los datos.")
        st.stop()

    # Convertir "CIIU 4" a numérico
    ciiu_df['CIIU 4'] = pd.to_numeric(ciiu_df['CIIU 4'], errors='coerce')

    # Hacer el cruce por "Código CIIU" y "CIIU 4"
    df_valid = df_valid.merge(ciiu_df[['CIIU 4', 'TIPO']], left_on='Código CIIU', right_on='CIIU 4', how='left')

    # Gráfica: Cantidad de códigos por "TIPO"
    tipo_counts = df_valid['TIPO'].value_counts().reset_index()
    tipo_counts.columns = ['TIPO', 'Cantidad']

    st.header("Gráfica de códigos por tipo")
    fig_tipo = px.bar(tipo_counts, x="TIPO", y="Cantidad", text="Cantidad", title="Cantidad de códigos por TIPO")
    fig_tipo.update_traces(textposition='outside')
    st.plotly_chart(fig_tipo)

    # Tabla resumen: Cantidad por "TIPO"
    st.header("Tabla resumen: Cantidad por tipo")
    st.dataframe(tipo_counts)

    # Top 10 códigos más recurrentes
    top_ciiu = df_valid['Código CIIU'].value_counts().head(10).reset_index()
    top_ciiu.columns = ['Código CIIU', 'Cantidad']
    top_ciiu = top_ciiu.merge(df_valid[['Código CIIU', 'Descripción CIIU']].drop_duplicates(), on='Código CIIU', how='left')

    st.header("Top 10 códigos más recurrentes")
    st.dataframe(top_ciiu)

