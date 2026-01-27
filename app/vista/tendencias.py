import streamlit as st

from bd import extras


if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Acceso no autorizado")
    st.stop()

st.title("📈 Tendencias y Patrones del Nivel de Atención")


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

      div[data-baseweb="select"] span {
        font-weight: 600 !important;
      }

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


with st.spinner("Cargando tendencias..."):
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
        value=(hoy - _dt.timedelta(days=30), hoy),
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

if df.empty:
    st.info("No hay datos disponibles para mostrar en el rango seleccionado.")
    st.stop()


with st.spinner("Generando visualizaciones..."):
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    promedio = float(df["porcentaje_estimado_atencion"].mean()) if len(df) else 0.0
    total_est = int(df["num_estudiantes_detectados"].sum()) if len(df) else 0
    total_reg = int(len(df))


    df_dia = (
        df.groupby("dia_semana", dropna=False)["porcentaje_estimado_atencion"]
          .mean()
          .reset_index()
          .sort_values("porcentaje_estimado_atencion", ascending=False)
    )
    mejor_dia = df_dia.iloc[0]["dia_semana"] if len(df_dia) else "—"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{_fmt_num(promedio, 2)}%</div><div class='kpi-lbl'>Promedio Atención</div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{total_est}</div><div class='kpi-lbl'>Total de etiquetas analizadas</div></div>",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{total_reg}</div><div class='kpi-lbl'>Registros analizados</div></div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"<div class='kpi-wrap'><div class='kpi-val'>{mejor_dia}</div><div class='kpi-lbl'>Mejor día (promedio)</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()


    df_ts = (
        df.assign(fecha=pd.to_datetime(df["fecha"].astype(str), errors="coerce"))
          .dropna(subset=["fecha"])
          .groupby("fecha")["porcentaje_estimado_atencion"]
          .mean()
          .reset_index()
          .sort_values("fecha")
    )
    fig_line = px.line(
        df_ts,
        x="fecha",
        y="porcentaje_estimado_atencion",
        labels={"fecha": "Fecha", "porcentaje_estimado_atencion": "Promedio de Atención"},
    )
    fig_line.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)


    df_hora = (
        df.groupby("hora")["porcentaje_estimado_atencion"]
          .mean()
          .reset_index()
          .sort_values("hora")
    )
    fig_hora = px.line(
        df_hora,
        x="hora",
        y="porcentaje_estimado_atencion",
        markers=True,
        labels={"hora": "Hora del día", "porcentaje_estimado_atencion": "Promedio de Atención"},
    )
    fig_hora.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)


    fig_dia = px.bar(
        df_dia.sort_values("dia_semana"),
        x="dia_semana",
        y="porcentaje_estimado_atencion",
        labels={"dia_semana": "Día", "porcentaje_estimado_atencion": "Promedio de Atención"},
    )
    fig_dia.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)

    piv = (
        df.pivot_table(
            index="hora",
            columns="dia_semana",
            values="porcentaje_estimado_atencion",
            aggfunc="mean",
        )
        .reindex(columns=[c for c in ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"] if c in df["dia_semana"].astype(str).unique()])
        .sort_index()
    )

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=piv.values if len(piv) else [],
            x=list(piv.columns) if len(piv) else [],
            y=list(piv.index) if len(piv) else [],
            hovertemplate="Hora: %{y}<br>Día: %{x}<br>Promedio: %{z:.2f}<extra></extra>",
        )
    )
    fig_heat.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)


    df_asig = (
        df.dropna(subset=["asignatura"])
          .groupby("asignatura")["porcentaje_estimado_atencion"]
          .mean()
          .reset_index()
          .sort_values("porcentaje_estimado_atencion", ascending=False)
          .head(10)
    )
    fig_asig = px.bar(
        df_asig,
        x="asignatura",
        y="porcentaje_estimado_atencion",
        labels={"asignatura": "Asignatura", "porcentaje_estimado_atencion": "Promedio de Atención"},
    )
    fig_asig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
    fig_asig.update_xaxes(tickangle=25)


    fig_sc = px.scatter(
        df,
        x="num_estudiantes_detectados",
        y="porcentaje_estimado_atencion",
        color="asignatura" if "asignatura" in df.columns else None,
        labels={
            "num_estudiantes_detectados": "Número de estudiantes",
            "porcentaje_estimado_atencion": "Atención (%)",
            "asignatura": "Asignatura",
        },
    )
    fig_sc.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)


    row1a, row1b = st.columns([1.25, 1], gap="small")
    with row1a:
        st.subheader("📆 Tendencia diaria (promedio)")
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    with row1b:
        st.subheader("⏰ Tendencia por hora (promedio)")
        st.plotly_chart(fig_hora, use_container_width=True, config={"displayModeBar": False})

    row2a, row2b = st.columns([1, 1.25], gap="small")
    with row2a:
        st.subheader("📅 Patrón por día de la semana")
        st.plotly_chart(fig_dia, use_container_width=True, config={"displayModeBar": False})
    with row2b:
        st.subheader("🔥 Mapa de calor (Día vs Hora)")
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    row3a, row3b = st.columns([1.2, 1], gap="small")
    with row3a:
        st.subheader("📚 Top 10 asignaturas por atención promedio")
        st.plotly_chart(fig_asig, use_container_width=True, config={"displayModeBar": False})
    with row3b:
        st.subheader("🎯 Aforo vs Atención")
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver tabla (datos filtrados)", expanded=False):
        st.dataframe(df, use_container_width=True)
