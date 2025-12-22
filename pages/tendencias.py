import streamlit as st
import pandas as pd
from mongo import get_mongo_client

# =============================
# CONFIGURACIÓN
# =============================
st.title("📈 Tendencias y Patrones del Nivel de Atención")

st.markdown(
    """
    En esta sección se analizan las tendencias temporales y los patrones recurrentes
    del nivel de atención estudiantil, permitiendo identificar comportamientos
    según la hora, el día y la sesión académica.
    """
)

# =============================
# OBTENER DATOS (REUTILIZA CONEXIÓN)
# =============================
client = get_mongo_client()   # conexión cacheada
db = client["Base"]
coleccion = db["registros_atencion"]

data = list(coleccion.find({}, {"_id": 0}))

if not data:
    st.warning("⚠️ No existen registros suficientes para analizar tendencias.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# =============================
# PREPARACIÓN DE VARIABLES TEMPORALES
# =============================
df["hora"] = df["timestamp"].dt.hour
df["dia_semana"] = df["timestamp"].dt.day_name()

st.divider()

# =============================
# TENDENCIA POR HORA DEL DÍA
# =============================
st.subheader("⏰ Tendencia del Nivel de Atención por Hora")

df_hora = (
    df.groupby("hora")["nivel_atencion"]
      .mean()
)

st.line_chart(df_hora, height=300)

st.caption(
    "Promedio del nivel de atención según la hora del día. "
    "Permite identificar franjas horarias con mayor o menor concentración."
)

st.divider()

# =============================
# PATRÓN POR DÍA DE LA SEMANA
# =============================
st.subheader("📅 Patrón de Atención por Día de la Semana")

orden_dias = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

df_dia = (
    df.groupby("dia_semana")["nivel_atencion"]
      .mean()
      .reindex(orden_dias)
)

st.bar_chart(df_dia)

st.caption(
    "Comparación del nivel promedio de atención según el día de la semana."
)

st.divider()

# =============================
# TENDENCIA POR SESIÓN
# =============================
st.subheader("🏫 Tendencia del Nivel de Atención por Sesión")

df_sesion = (
    df.groupby("sesion_id")["nivel_atencion"]
      .mean()
      .sort_values(ascending=False)
)

st.bar_chart(df_sesion)

st.caption(
    "Promedio del nivel de atención registrado en cada sesión académica."
)

st.divider()

# =============================
# PATRÓN SEGÚN ASIGNATURA Y CARRERA
# =============================
st.subheader("📚🎓 Patrón de Atención por Asignatura y Carrera")

df_combo = (
    df.groupby(["asignatura", "carrera"])["nivel_atencion"]
      .mean()
      .reset_index()
)

st.dataframe(
    df_combo,
    use_container_width=True
)

st.caption(
    "Tabla comparativa que permite identificar combinaciones de asignatura y carrera "
    "con mayor o menor nivel de atención."
)
