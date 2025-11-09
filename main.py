import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Dashboard Universitario", layout="wide")

st.title("📊 Dashboard de Admisión, Matrícula y Retención")
st.markdown("Sube el archivo CSV con los datos (por ejemplo `university_student_data.csv`).")

uploaded_file = st.file_uploader("Carga el CSV aquí", type=["csv"])

if uploaded_file is None:
    st.info(
        "Por favor sube el archivo CSV para visualizar el dashboard. "
        "El archivo debe contener columnas como Year, Term, Applications, Admitted, Enrolled, "
        "Retention Rate (%), Student Satisfaction (%), Engineering Enrolled, Business Enrolled, Arts Enrolled, Science Enrolled."
    )
else:
    @st.cache_data
    def load_data(file):
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        if "Year" in df.columns:
            df["Year"] = df["Year"].astype(str)
        return df

    df = load_data(uploaded_file)

    # Mostrar breve descripción de columnas y datos
    st.subheader("Descripción rápida de los datos")
    st.write("Columnas detectadas:", list(df.columns))
    st.dataframe(df.head())

    # Sidebar: filtros
    st.sidebar.header("Filtros")
    years = sorted(df["Year"].unique()) if "Year" in df.columns else []
    selected_years = st.sidebar.multiselect("Año(s)", years, default=years)
    terms = sorted(df["Term"].unique()) if "Term" in df.columns else []
    selected_terms = st.sidebar.multiselect("Término(s)", terms, default=terms)
    dept_options = [c for c in df.columns if c.lower().endswith("enrolled")]
    selected_dept = st.sidebar.selectbox("Departamento (matrícula)", dept_options if dept_options else [None])

    # Filtrar dataframe según selección
    filtered = df.copy()
    if selected_years:
        filtered = filtered[filtered["Year"].isin(selected_years)]
    if selected_terms:
        filtered = filtered[filtered["Term"].isin(selected_terms)]

    # KPI cards
    st.subheader("Indicadores clave")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        apps = int(filtered["Applications"].mean()) if "Applications" in filtered.columns and not filtered["Applications"].isna().all() else "N/A"
        st.metric("Promedio Aplicaciones", apps)
    with col2:
        admitted = int(filtered["Admitted"].mean()) if "Admitted" in filtered.columns and not filtered["Admitted"].isna().all() else "N/A"
        st.metric("Promedio Admitidos", admitted)
    with col3:
        enrolled = int(filtered["Enrolled"].mean()) if "Enrolled" in filtered.columns and not filtered["Enrolled"].isna().all() else "N/A"
        st.metric("Promedio Matriculados", enrolled)
    with col4:
        retention = f"{filtered['Retention Rate (%)'].mean():.1f}%" if "Retention Rate (%)" in filtered.columns and not filtered["Retention Rate (%)"].isna().all() else "N/A"
        st.metric("Retención promedio", retention)

    # Gráfica 1: Tendencia de la tasa de retención (línea)
    if "Retention Rate (%)" in filtered.columns and "Year" in filtered.columns:
        st.subheader("Tendencia de Retención por Año y Término")
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=filtered, x="Year", y="Retention Rate (%)", hue="Term", marker="o", ax=ax1)
        ax1.set_ylabel("Retention Rate (%)")
        ax1.set_xlabel("Year")
        ax1.set_ylim(0, 100)
        plt.tight_layout()
        st.pyplot(fig1)
    else:
        st.warning("No se encontraron las columnas necesarias para la gráfica de retención (Year y Retention Rate (%)).")

    # Gráfica 2: Satisfacción estudiantil por año (barra)
    if "Student Satisfaction (%)" in filtered.columns and "Year" in filtered.columns:
        st.subheader("Satisfacción Estudiantil por Año (promedio)")
        agg_satisfaction = filtered.groupby("Year")["Student Satisfaction (%)"].mean().reset_index()
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.barplot(data=agg_satisfaction, x="Year", y="Student Satisfaction (%)", palette="Blues_d", ax=ax2)
        ax2.set_ylabel("Student Satisfaction (%)")
        ax2.set_xlabel("Year")
        ax2.set_ylim(0, 100)
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.warning("No se encontraron las columnas necesarias para la gráfica de satisfacción (Year y Student Satisfaction (%)).")

    # Gráfica 3: Comparación Spring vs Fall (aplicaciones, admitidos, matriculados)
    st.subheader("Comparación Spring vs Fall")
    compare_cols = [c for c in ["Applications", "Admitted", "Enrolled"] if c in filtered.columns]
    if "Term" in filtered.columns and compare_cols:
        agg_term = filtered.groupby("Term")[compare_cols].mean().reset_index()
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        agg_term_melt = agg_term.melt(id_vars="Term", value_vars=compare_cols, var_name="Metric", value_name="Value")
        sns.barplot(data=agg_term_melt, x="Metric", y="Value", hue="Term", ax=ax3)
        ax3.set_ylabel("Promedio")
        plt.tight_layout()
        st.pyplot(fig3)
    else:
        st.warning("Faltan columnas para comparar términos (Term y alguna de Applications/Admitted/Enrolled).")

    # Gráfica 4: Distribución por departamento (pie/donut) corregida
    if selected_dept and selected_dept in filtered.columns:
        st.subheader("Distribución de Matrícula por Departamento (último año seleccionado)")
        # Seleccionar datos del último año seleccionado si aplica
        last_year = selected_years[-1] if selected_years else None
        if last_year:
            slice_df = filtered[filtered["Year"] == last_year]
        else:
            slice_df = filtered

        # Asegurar que dept_options exista y convertir a numérico
        dept_cols = [c for c in dept_options if c in slice_df.columns]
        if not dept_cols:
            st.warning("No se encontraron columnas de departamento para generar la distribución.")
        else:
            dept_sum = slice_df[dept_cols].apply(pd.to_numeric, errors="coerce").sum()
            # Filtrar columnas con valores no nulos y positivos
            dept_sum = dept_sum.fillna(0)
            dept_sum = dept_sum[dept_sum > 0]

            if dept_sum.empty:
                st.warning("No hay datos positivos para mostrar la distribución por departamento en el año seleccionado.")
            else:
                labels = dept_sum.index.tolist()
                sizes = dept_sum.values

                # Si hay muchos segmentos, agrupar los pequeños en "Other"
                if len(sizes) > 6:
                    sorted_idx = np.argsort(sizes)[::-1]
                    top_idx = sorted_idx[:6]
                    other_idx = sorted_idx[6:]
                    top_labels = [labels[i] for i in top_idx]
                    top_sizes = [sizes[i] for i in top_idx]
                    other_size = sum(sizes[i] for i in other_idx)
                    top_labels.append("Other")
                    top_sizes.append(other_size)
                    labels = top_labels
                    sizes = top_sizes

                fig4, ax4 = plt.subplots(figsize=(6, 4))
                try:
                    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
                except Exception:
                    # Fallback: show horizontal bar chart if pie fails
                    st.warning("No se pudo dibujar el gráfico de pastel; mostrando barras en su lugar.")
                    fig4, ax4 = plt.subplots(figsize=(8, 4))
                    sns.barplot(x=sizes, y=labels, palette="pastel", ax=ax4)
                    ax4.set_xlabel("Number of students")
                    ax4.set_ylabel("")
                    plt.tight_layout()
                    st.pyplot(fig4)
                else:
                    centre_circle = plt.Circle((0, 0), 0.70, fc="white")
                    fig4.gca().add_artist(centre_circle)
                    ax4.axis("equal")
                    plt.tight_layout()
                    st.pyplot(fig4)
    else:
        st.info("Selecciona un departamento en el filtro lateral para ver la distribución por departamento si está disponible.")

    # Mostrar tabla filtrada y estadísticas agregadas
    st.subheader("Datos filtrados y estadísticas agregadas")
    st.dataframe(filtered.reset_index(drop=True))

    st.markdown("### Estadísticas agregadas (por año y término)")
    try:
        agg = filtered.groupby(["Year", "Term"]).agg({
            "Applications": "mean" if "Applications" in filtered.columns else "first",
            "Admitted": "mean" if "Admitted" in filtered.columns else "first",
            "Enrolled": "mean" if "Enrolled" in filtered.columns else "first",
            "Retention Rate (%)": "mean" if "Retention Rate (%)" in filtered.columns else "first",
            "Student Satisfaction (%)": "mean" if "Student Satisfaction (%)" in filtered.columns else "first",
        }).round(2)
        st.dataframe(agg.reset_index())
    except Exception:
        st.write("No se pudieron calcular todas las estadísticas agregadas; verifica las columnas del CSV.")
