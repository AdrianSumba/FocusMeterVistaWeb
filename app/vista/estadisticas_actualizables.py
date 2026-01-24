import streamlit as st
from bd import mongo  

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Acceso no autorizado")
    st.stop()

st.title("📊 Estadísticas")


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
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False, ttl=120)
def _cargar_carreras():
    return mongo.listar_carreras()


@st.cache_data(show_spinner=False, ttl=120)
def _cargar_registros(carrera_id=None):
    return mongo.obtener_registros_atencion_enriquecidos(carrera_id=carrera_id)


def _fmt_num(valor, dec=2):
    try:
        v = float(valor)
        return f"{v:.{dec}f}".replace(".", ",")
    except Exception:
        return "0,00" if dec else "0"


def _build_figures(registros):
    import pandas as pd  
    import plotly.express as px 
    import plotly.graph_objects as go  

    if not registros:
        return None

    df = pd.DataFrame(registros)


    df["num_estudiantes_detectados"] = pd.to_numeric(
        df.get("num_estudiantes_detectados", 0), errors="coerce"
    ).fillna(0)
    df["porcentaje_estimado_atencion"] = pd.to_numeric(
        df.get("porcentaje_estimado_atencion", 0), errors="coerce"
    ).fillna(0)


    promedio_atencion = float(df["porcentaje_estimado_atencion"].mean()) if len(df) else 0.0
    total_estudiantes = int(df["num_estudiantes_detectados"].sum()) if len(df) else 0


    conteo = {}
    for etiquetas in df.get("etiquetas", []):
        if isinstance(etiquetas, dict):
            for k, v in etiquetas.items():
                if str(k).strip().lower() == "atento":
                    continue
                conteo[k] = conteo.get(k, 0) + int(v or 0)
    principal_distractor = max(conteo.items(), key=lambda x: x[1])[0] if conteo else "—"

 
    df_rank = (
        df.groupby("carrera", dropna=False)["porcentaje_estimado_atencion"]
        .mean()
        .reset_index()
        .sort_values("porcentaje_estimado_atencion", ascending=False)
    )
    fig_rank = px.bar(
        df_rank,
        x="carrera",
        y="porcentaje_estimado_atencion",
        labels={"carrera": "Carrera", "porcentaje_estimado_atencion": "Promedio Atención"},
    )
    fig_rank.update_traces(marker_color="#1E88E5")
    fig_rank.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)


    dias_orden = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    df_h = df.dropna(subset=["hora_inicio", "dia"]).copy()

    if len(df_h):
        piv = (
            df_h.pivot_table(
                index="hora_inicio",
                columns="dia",
                values="porcentaje_estimado_atencion",
                aggfunc="mean",
            )
            .reindex(columns=[d for d in dias_orden if d in df_h["dia"].unique()])
            .sort_index()
        )
        piv["Total"] = piv.mean(axis=1)
        total_row = piv.mean(axis=0).to_frame().T
        total_row.index = ["Total"]
        piv_tot = pd.concat([piv, total_row], axis=0)
    else:
        piv_tot = pd.DataFrame()

    if len(piv_tot):
        x = list(piv_tot.columns)
        y = list(piv_tot.index)
        z = piv_tot.values

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=z,
                x=x,
                y=y,
                colorscale="OrRd",
                colorbar=dict(title=""),
                hovertemplate="Hora: %{y}<br>Día: %{x}<br>Promedio: %{z:.2f}<extra></extra>",
            )
        )

  
        ann = []
        for i, yy in enumerate(y):
            for j, xx in enumerate(x):
                val = z[i][j]
                if pd.isna(val):
                    continue
                ann.append(
                    dict(
                        x=xx,
                        y=yy,
                        text=f"{val:.2f}".replace(".", ","),
                        showarrow=False,
                        font=dict(size=10),
                    )
                )
        fig_heat.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            xaxis=dict(side="top"),
            annotations=ann,
        )
    else:
        fig_heat = go.Figure()

 
    serie = {}
    for etiquetas in df.get("etiquetas", []):
        if isinstance(etiquetas, dict):
            for k, v in etiquetas.items():
                if str(k).strip().lower() == "atento":
                    continue
                serie[k] = serie.get(k, 0) + int(v or 0)

    if serie:
        df_pie = (
            pd.DataFrame({"etiqueta": list(serie.keys()), "conteo": list(serie.values())})
            .sort_values("conteo", ascending=False)
        )
        fig_pie = px.pie(df_pie, names="etiqueta", values="conteo")
        fig_pie.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320)
    else:
        fig_pie = go.Figure()

 
    df_sc = df.dropna(subset=["asignatura"]).copy()
    fig_scatter = px.scatter(
        df_sc,
        x="num_estudiantes_detectados",
        y="porcentaje_estimado_atencion",
        color="asignatura",
        labels={
            "num_estudiantes_detectados": "Número de estudiantes",
            "porcentaje_estimado_atencion": "Promedio Atención",
            "asignatura": "Asignatura",
        },
    )
    fig_scatter.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=320,
        legend_title_text="Asignatura",
    )

    return {
        "kpi_promedio": promedio_atencion,
        "kpi_total": total_estudiantes,
        "kpi_distractor": principal_distractor,
        "fig_rank": fig_rank,
        "fig_heat": fig_heat,
        "fig_pie": fig_pie,
        "fig_scatter": fig_scatter,
    }


with st.spinner("Cargando estadísticas..."):
    carreras = _cargar_carreras()

left, right = st.columns([1, 1], gap="small")

with left:
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with right:
    opciones = ["Todas"] + [c["nombre"] for c in carreras]
    seleccion = st.selectbox("Carrera", opciones, index=0, label_visibility="collapsed")

carrera_id = None
if seleccion != "Todas":
    carrera_id = next((c["id"] for c in carreras if c["nombre"] == seleccion), None)

with st.spinner("Cargando registros..."):
    registros = _cargar_registros(carrera_id=carrera_id)

with st.spinner("Generando figuras..."):
    figs = _build_figures(registros)

if not figs:
    st.info("No hay datos disponibles para mostrar.")
    st.stop()


k1, k2, k3 = st.columns(3)

with k1:
    st.markdown(
        f"<div class='kpi-wrap'><div class='kpi-val'>{_fmt_num(figs['kpi_promedio'], 2)}</div><div class='kpi-lbl'>Promedio Atención</div></div>",
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"<div class='kpi-wrap'><div class='kpi-val'>{figs['kpi_total']}</div><div class='kpi-lbl'>Total de etiquetas analizadas</div></div>",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"<div class='kpi-wrap'><div class='kpi-val'>{figs['kpi_distractor']}</div><div class='kpi-lbl'>Principal Distractor</div></div>",
        unsafe_allow_html=True,
    )


colA, colB = st.columns([1.2, 1])
with colA:
    st.subheader("Ranking de Atención Académica")
    st.plotly_chart(figs["fig_rank"], use_container_width=True, config={"displayModeBar": False})
with colB:
    st.subheader(" ")
    st.plotly_chart(figs["fig_heat"], use_container_width=True, config={"displayModeBar": False})

colC, colD = st.columns([1, 1.2])
with colC:
    st.subheader("Análisis de Fugas de Atención")
    st.plotly_chart(figs["fig_pie"], use_container_width=True, config={"displayModeBar": False})
with colD:
    st.subheader("Impacto del Aforo en el Rendimiento")
    st.plotly_chart(figs["fig_scatter"], use_container_width=True, config={"displayModeBar": False})
