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

    # Asegurar que la columna "Códigos CIIU" sea string
    df['Códigos CIIU'] = df['Códigos CIIU'].fillna('').astype(str)

    # Crear columnas vacías para manejar casos donde no haya separador
    df['Código CIIU'] = None
    df['Descripción CIIU'] = None

    # Dividir solo donde el separador esté presente
    split_mask = df['Códigos CIIU'].str.contains(' - ')
    df.loc[split_mask, ['Código CIIU', 'Descripción CIIU']] = df.loc[split_mask, 'Códigos CIIU'].str.split(' - ', 1, expand=True)

    # Convertir "Código CIIU" a numérico, dejando NaN en valores no válidos
    df['Código CIIU'] = pd.to_numeric(df['Código CIIU'], errors='coerce')

    # Informar al usuario si hubo filas sin el separador
    invalid_rows = df[~split_mask]
    if not invalid_rows.empty:
        st.warning(f"Se encontraron {len(invalid_rows)} filas sin separador '-' en 'Códigos CIIU'. Estas filas fueron ignoradas en el procesamiento.")

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
