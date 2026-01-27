import streamlit as st

from bd import extras


if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Acceso no autorizado")
    st.stop()

st.title("🔮 Proyecciones del Nivel de Atención Estudiantil")


st.markdown(
    """
    <style>
      .block-container {padding-top: 1.0rem;}

      .kpi-wrap {text-align:center; padding: 0.6rem 0.2rem 0.2rem 0.2rem;}
      .kpi-val {font-size: 1.85rem; font-weight: 800; line-height: 1.1;}
      .kpi-lbl {font-size: 0.92rem; opacity: 0.75; margin-top: 0.15rem;}
      h3 {margin-top: 0.2rem;}

      div.stButton > button {
        width: 100%;
        height: 52px;
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.12);
        background: #ffffff;
        white-space: nowrap !important;
        font-weight: 600;
      }
      div.stButton > button:hover {
        border-color: rgba(0,0,0,0.18);
      }

      div[data-baseweb="select"] > div {
        height: 52px !important;
        border-radius: 14px !important;
        background: #EFF2F6 !important;
        border: 1px solid rgba(0,0,0,0.10) !important;
        box-shadow: none !important;
        align-items: center !important;
      }

      div[data-baseweb="select"] span { font-weight: 600 !important; }
      div[data-testid="stSelectbox"] label {display:none;}
      div[data-testid="stDateInput"] label {display:none;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _fmt_num(valor, dec=2):
    try:
        v = float(valor)
        return f"{v:.{dec}f}".replace(".", ",")
    except Exception:
        return "0,00" if dec else "0"


@st.cache_data(show_spinner=False, ttl=120)
def _cargar_carreras():
    return extras.listar_carreras()


@st.cache_data(show_spinner=False, ttl=120)
def _cargar_df(carrera_id=None, fecha_desde=None, fecha_hasta=None):
    return extras.obtener_registros_df(
        carrera_id=carrera_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limite=None,
    )


with st.spinner("Cargando proyecciones..."):
    carreras = _cargar_carreras()

left, mid, right = st.columns([1, 1.2, 1.4], gap="small")

with left:
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with mid:
    opciones = ["Todas"] + [c["nombre"] for c in carreras]
    seleccion = st.selectbox("Carrera", opciones, index=0, label_visibility="collapsed")

with right:
    import datetime as _dt
    hoy = _dt.date.today()
    desde, hasta = st.date_input(
        "Rango",
        value=(hoy - _dt.timedelta(days=45), hoy),
        label_visibility="collapsed",
    )

carrera_id = None
if seleccion != "Todas":
    carrera_id = next((c["id"] for c in carreras if c["nombre"] == seleccion), None)

with st.spinner("Cargando registros..."):
    df = _cargar_df(
        carrera_id=carrera_id,
        fecha_desde=str(desde),
        fecha_hasta=str(hasta),
    )

if df.empty or len(df) < 8:
    st.warning("⚠️ No existen suficientes registros en el rango seleccionado para proyectar.")
    st.stop()



import numpy as np
import pandas as pd
import plotly.graph_objects as go

frecuencia = st.selectbox("Frecuencia de proyección", ["Por día (recomendado)", "Por minuto"], index=0)

if frecuencia == "Por minuto":
   
    s = (
        df.set_index("timestamp")["porcentaje_estimado_atencion"]
          .resample("1min")
          .mean()
          .dropna()
    )
    if len(s) < 20:
        st.info("No hay suficientes puntos por minuto; se usará proyección diaria.")
        frecuencia = "Por día (recomendado)"
else:
    s = None

if frecuencia == "Por día (recomendado)":
    s = (
        df.assign(fecha=pd.to_datetime(df["fecha"].astype(str), errors="coerce"))
          .dropna(subset=["fecha"])
          .groupby("fecha")["porcentaje_estimado_atencion"]
          .mean()
          .sort_index()
    )

if len(s) < 8:
    st.warning("⚠️ La serie temporal es muy corta para proyectar (mínimo 8 puntos).")
    st.stop()

if frecuencia == "Por minuto":
    horizonte = st.slider("Horizonte de proyección (minutos)", min_value=5, max_value=180, value=30, step=5)
    steps = horizonte
    freq = "1min"
else:
    horizonte = st.slider("Horizonte de proyección (días)", min_value=1, max_value=30, value=7, step=1)
    steps = horizonte
    freq = "1D"

with st.spinner("Calculando proyección..."):
    y = s.values.astype(float)
    x = np.arange(len(y), dtype=float)

    a, b = np.polyfit(x, y, 1)
    y_hat = a * x + b

    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    x_f = np.arange(len(y), len(y) + steps, dtype=float)
    y_f = a * x_f + b

    idx_last = s.index[-1]
    idx_fut = pd.date_range(start=idx_last, periods=steps + 1, freq=freq)[1:]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=y,
            mode="lines+markers",
            name="Histórico",
            hovertemplate="%{x}<br>Atención: %{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=idx_fut,
            y=y_f,
            mode="lines+markers",
            name="Proyección",
            hovertemplate="%{x}<br>Proyección: %{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Tiempo",
        yaxis_title="Atención (%)",
    )

    ultimo_real = float(y[-1])
    ultimo_proy = float(y_f[-1]) if len(y_f) else ultimo_real
    tendencia = "creciente" if a > 0 else "decreciente"


    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{_fmt_num(ultimo_real, 2)}%</div><div class='kpi-lbl'>Último valor real</div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{_fmt_num(ultimo_proy, 2)}%</div><div class='kpi-lbl'>Último valor proyectado</div></div>",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{tendencia}</div><div class='kpi-lbl'>Tendencia estimada</div></div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{_fmt_num(r2, 2)}</div><div class='kpi-lbl'>R² (ajuste lineal)</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("📉 Proyección del nivel de atención")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.caption(
    "La proyección se basa en una tendencia lineal simple sobre el histórico filtrado. "
    "Es orientativa y mejora con más datos y series más estables."
)

with st.expander("Ver serie usada para la proyección", expanded=False):
    st.dataframe(s.reset_index().rename(columns={0: "atencion"}), use_container_width=True)
