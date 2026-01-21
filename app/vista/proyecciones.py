import streamlit as st
import pandas as pd
import numpy as np
from bd.mongo import get_cliente_mongo
from sklearn.linear_model import LinearRegression

# =============================
# CONFIGURACIÓN
# =============================
st.title("🔮 Proyecciones del Nivel de Atención Estudiantil")

st.markdown(
    """
    En esta sección se presentan proyecciones del nivel de atención estudiantil
    a partir de los registros históricos capturados por el sistema, utilizando
    modelos estadísticos simples para estimar el comportamiento futuro.
    """
)

# =============================
# OBTENER DATOS (REUTILIZA CONEXIÓN)
# =============================
client = get_cliente_mongo()   # conexión cacheada
db = client["Base"]
coleccion = db["registros_atencion"]

data = list(coleccion.find({}, {"_id": 0}))

if len(data) < 10:
    st.warning("⚠️ No existen suficientes registros para generar proyecciones confiables.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

st.divider()

# =============================
# PREPARACIÓN DE DATOS
# =============================
df["tiempo"] = (df["timestamp"] - df["timestamp"].min()).dt.total_seconds()

X = df[["tiempo"]]
y = df["nivel_atencion"]

# =============================
# ENTRENAMIENTO DEL MODELO
# =============================
modelo = LinearRegression()
modelo.fit(X, y)

# =============================
# PROYECCIÓN FUTURA
# =============================
horizonte_min = st.slider(
    "Horizonte de proyección (minutos)",
    min_value=5,
    max_value=60,
    value=15,
    step=5
)

futuro_seg = np.arange(
    X["tiempo"].max(),
    X["tiempo"].max() + horizonte_min * 60,
    60
).reshape(-1, 1)

predicciones = modelo.predict(futuro_seg)

df_futuro = pd.DataFrame({
    "timestamp": pd.date_range(
        start=df["timestamp"].max(),
        periods=len(predicciones),
        freq="1min"
    ),
    "nivel_atencion": predicciones
})

st.divider()

# =============================
# VISUALIZACIÓN
# =============================
st.subheader("📉 Proyección del Nivel de Atención")

df_plot = pd.concat([
    df[["timestamp", "nivel_atencion"]],
    df_futuro
])

df_plot = df_plot.set_index("timestamp")

st.line_chart(
    df_plot,
    height=350
)

st.caption(
    "La proyección se basa en una regresión lineal simple aplicada a los datos históricos. "
    "Los valores futuros representan una estimación del comportamiento esperado del nivel de atención."
)

st.divider()

# =============================
# INTERPRETACIÓN
# =============================
st.subheader("🧠 Interpretación del Modelo")

st.write(
    f"""
    - Tendencia estimada: **{'creciente' if modelo.coef_[0] > 0 else 'decreciente'}**
    - Pendiente del modelo: **{modelo.coef_[0]:.6f}**
    - Nivel de atención esperado al final del horizonte:
      **{predicciones[-1]:.2f}**
    """
)

st.info(
    "Estas proyecciones tienen un carácter orientativo y dependen de la calidad y cantidad "
    "de los datos históricos disponibles."
)
