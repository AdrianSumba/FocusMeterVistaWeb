import streamlit as st
import pandas as pd
from mongo import get_mongo_client

# =============================
# CONFIGURACIÓN DE PÁGINA
# =============================
st.title("📊 Análisis del Nivel de Atención Estudiantil")

st.markdown(
    """
    En esta sección se presenta un análisis estadístico descriptivo de los registros
    obtenidos por el sistema de monitoreo en tiempo real, permitiendo evaluar el
    comportamiento atencional de los estudiantes.
    """
)

# =============================
# OBTENER DATOS (REUTILIZA CONEXIÓN)
# =============================
client = get_mongo_client()        # ← conexión cacheada
db = client["Base"]
coleccion = db["registros_atencion"]

data = list(coleccion.find({}, {"_id": 0}))

if not data:
    st.warning("⚠️ No existen registros de atención disponibles para el análisis.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])

st.divider()

# =============================
# KPIs GENERALES
# =============================
st.subheader("📌 Indicadores Generales")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Nivel promedio de atención",
    f"{df['nivel_atencion'].mean():.2f}"
)

col2.metric(
    "Total de registros",
    len(df)
)

if "estudiantes_detectados" in df.columns:
    col3.metric(
        "Promedio de estudiantes detectados",
        f"{df['estudiantes_detectados'].mean():.0f}"
    )

st.divider()

# =============================
# DISTRIBUCIÓN DE ATENCIÓN
# =============================
st.subheader("📊 Distribución del Nivel de Atención")

st.bar_chart(
    df["nivel_atencion"],
    height=300
)

st.caption(
    "Distribución de los valores de atención capturados por el sistema."
)

st.divider()

# =============================
# EVOLUCIÓN TEMPORAL
# =============================
st.subheader("⏱️ Evolución del Nivel de Atención en el Tiempo")

df_time = (
    df.set_index("timestamp")
      .resample("5min")
      .mean(numeric_only=True)
)

st.line_chart(
    df_time["nivel_atencion"],
    height=300
)

st.caption(
    "Promedio del nivel de atención calculado en intervalos de cinco minutos."
)

st.divider()

# =============================
# ANÁLISIS POR ASIGNATURA
# =============================
st.subheader("📚 Nivel de Atención por Asignatura")

df_asignatura = (
    df.groupby("asignatura")["nivel_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_asignatura)

st.divider()

# =============================
# ANÁLISIS POR CARRERA
# =============================
st.subheader("🎓 Nivel de Atención por Carrera")

df_carrera = (
    df.groupby("carrera")["nivel_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_carrera)

st.caption(
    "Comparación del nivel promedio de atención entre las diferentes carreras."
)
