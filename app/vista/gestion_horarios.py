# app/vista/gestion_horarios.py
import datetime as _dt
from collections import defaultdict
from typing import Optional, List, Tuple, Set

import pandas as pd
import streamlit as st

from bd import extras


if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Acceso no autorizado")
    st.stop()


st.title("🗓️ Gestión Académica: Docentes, Asignaturas y Horarios")


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
      div.stButton > button:hover { border-color: rgba(0,0,0,0.18); }

      div[data-baseweb="select"] > div {
        height: 52px !important;
        border-radius: 14px !important;
        background: #EFF2F6 !important;
        border: 1px solid rgba(0,0,0,0.10) !important;
        box-shadow: none !important;
        align-items: center !important;
      }
      div[data-baseweb="select"] span { font-weight: 600 !important; }

      /* Mantener el look & feel, pero sin ocultar etiquetas en selects.
         (El usuario pidió leyendas visuales claras para cada combo.) */
      /* Mostrar etiquetas también en inputs numéricos y de texto */
      div[data-testid="stTextInput"] label,
      div[data-testid="stNumberInput"] label {
        display:block !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        opacity: 0.78 !important;
        margin-bottom: 0.15rem !important;
      }

      .field-label{
        font-size: 0.86rem;
        font-weight: 700;
        opacity: 0.78;
        margin: 0.25rem 0 0.15rem 0;
      }

      div[data-testid="stSelectbox"] label,
      div[data-testid="stMultiSelect"] label {
        display:block !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        opacity: 0.78 !important;
        margin-bottom: 0.15rem !important;
      }

      .chip {
        display:inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: #EFF2F6;
        border: 1px solid rgba(0,0,0,0.08);
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 6px;
        margin-top: 6px;
      }
      .hint {
        font-size: 0.92rem;
        opacity: 0.82;
        margin-top: 0.3rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if "gh_flash" in st.session_state:
    _f = st.session_state.pop("gh_flash")
    kind = _f.get("kind", "info")
    text = _f.get("text", "")
    detail = _f.get("detail")
    try:
        st.toast(text)
    except Exception:
        pass
    if kind == "success":
        st.success(detail or text)
    elif kind == "warning":
        st.warning(detail or text)
    elif kind == "error":
        st.error(detail or text)
    else:
        st.info(detail or text)

if "gh_conflicts" in st.session_state:
    conflicts = st.session_state.get("gh_conflicts") or []
    with st.expander("Ver detalle de solapamientos / errores", expanded=True):
        if conflicts:
            st.dataframe(pd.DataFrame(conflicts), use_container_width=True)
        if st.button("Ocultar detalle", key="btn_hide_conflicts"):
            st.session_state.pop("gh_conflicts", None)
            st.rerun()


def _slot_list(h_ini="07:00", h_fin="21:00", step_min=60):
    t0 = _dt.datetime.strptime(h_ini, "%H:%M")
    t1 = _dt.datetime.strptime(h_fin, "%H:%M")
    slots = []
    t = t0
    while t < t1:
        slots.append(t.strftime("%H:%M"))
        t += _dt.timedelta(minutes=step_min)
    return slots


def _add_minutes(hhmm: str, minutes: int) -> str:
    t = _dt.datetime.strptime(hhmm, "%H:%M") + _dt.timedelta(minutes=minutes)
    return t.strftime("%H:%M")


def _merge_slots(starts, step_min=60):
    if not starts:
        return []
    starts = sorted(starts)
    intervals = []
    cur_s = starts[0]
    cur_e = _add_minutes(cur_s, step_min)
    for s in starts[1:]:
        if s == cur_e:  # consecutivo
            cur_e = _add_minutes(cur_e, step_min)
        else:
            intervals.append((cur_s, cur_e))
            cur_s = s
            cur_e = _add_minutes(s, step_min)
    intervals.append((cur_s, cur_e))
    return intervals


def _df_horario_grid(horarios, slots, dias):
    grid = pd.DataFrame("", index=dias, columns=slots)
    for h in horarios:
        d = h.get("dia")
        hi = h.get("hora_inicio")
        hf = h.get("hora_fin")
        label = f"{h.get('asignatura','')} — {h.get('docente','')} ({h.get('aula','')})"
        for s in slots:
            e = _add_minutes(s, 60)
            if (s < hf) and (e > hi) and d in grid.index and s in grid.columns:
                grid.loc[d, s] = label
    return grid


@st.cache_data(show_spinner=False, ttl=120)
def _cache_catalogos():
    return {
        "periodos": extras.listar_periodos_academicos(),
        "docentes": extras.listar_docentes(),
        "aulas": extras.listar_aulas(),
        "carreras": extras.listar_carreras_simple(),
    }


@st.cache_data(show_spinner=False, ttl=120)
def _cache_asignaturas(periodo=None, carrera=None, docente=None):
    return extras.listar_asignaturas(periodo_academico=periodo, id_carrera=carrera, id_docente=docente)


@st.cache_data(show_spinner=False, ttl=60)
def _cache_horarios(periodo=None, aula=None, docente=None, carrera=None):
    return extras.obtener_horarios_enriquecidos(periodo_academico=periodo, id_aula=aula, id_docente=docente, id_carrera=carrera)


def _ocupados_union(
    periodo: str,
    dia: str,
    aula_id: Optional[str],
    docente_id: Optional[str],
    slots: List[str],
) -> Tuple[Set[str], Set[str]]:
    ocup_aula = set()
    ocup_doc = set()

    if periodo and aula_id:
        hs_a = _cache_horarios(periodo=periodo, aula=aula_id, docente=None, carrera=None)
        for h in hs_a:
            if h.get("dia") != dia:
                continue
            hi, hf = h.get("hora_inicio"), h.get("hora_fin")
            for s in slots:
                e = _add_minutes(s, 60)
                if (s < hf) and (e > hi):
                    ocup_aula.add(s)

    if periodo and docente_id:
        hs_d = _cache_horarios(periodo=periodo, aula=None, docente=docente_id, carrera=None)
        for h in hs_d:
            if h.get("dia") != dia:
                continue
            hi, hf = h.get("hora_inicio"), h.get("hora_fin")
            for s in slots:
                e = _add_minutes(s, 60)
                if (s < hf) and (e > hi):
                    ocup_doc.add(s)

    return ocup_aula, ocup_doc


with st.spinner("Cargando Gestión Académica..."):
    _CATALOGOS = _cache_catalogos()


left, mid, right = st.columns([1, 1.3, 1.2], gap="small")
with left:
    if st.button("🔄 Actualizar catálogos", use_container_width=True):
        st.session_state["gh_flash"] = {
            "kind": "info",
            "text": "🔄 Catálogos actualizados",
            "detail": "Se recargaron catálogos y horarios.",
        }
        st.cache_data.clear()
        st.rerun()
with mid:
    st.markdown('<div class="hint">Crea / selecciona docentes, carreras, aulas y asignaturas, y asigna horarios.</div>', unsafe_allow_html=True)
with right:
    st.markdown(
        '<span class="chip">✔️ Validación</span><span class="chip">⛔ Anti-solapamiento</span><span class="chip">📅 Vista por periodo</span>',
        unsafe_allow_html=True,
    )


tabs = st.tabs(["🧩 Asignar horario", "📚 Catálogos", "📋 Horarios (listado)"])


with tabs[0]:
    data = _CATALOGOS
    periodos = data["periodos"] or ["(Sin periodos)"]
    docentes = data["docentes"]
    aulas = data["aulas"]
    carreras = data["carreras"]

    colA, colB, colC, colD = st.columns([1.15, 1.15, 1.15, 1.15], gap="small")

    with colA:
        periodo = st.selectbox("Periodo académico", periodos, index=0, key="gh_periodo")
    with colB:
        # Carrera
        carrera_op = ["— Seleccionar —"] + [c["nombre"] for c in carreras] + ["➕ Crear nueva carrera…"]
        carrera_sel = st.selectbox("Carrera", carrera_op, index=0, key="gh_carrera_sel")
        carrera_id = None
        if carrera_sel and carrera_sel not in ["— Seleccionar —", "➕ Crear nueva carrera…"]:
            carrera_id = next((c["id"] for c in carreras if c["nombre"] == carrera_sel), None)
    with colC:
        # Docente
        docente_op = ["— Seleccionar —"] + [d["nombre"] for d in docentes] + ["➕ Crear nuevo docente…"]
        docente_sel = st.selectbox("Docente", docente_op, index=0, key="gh_docente_sel")
        docente_id = None
        if docente_sel and docente_sel not in ["— Seleccionar —", "➕ Crear nuevo docente…"]:
            docente_id = next((d["id"] for d in docentes if d["nombre"] == docente_sel), None)
    with colD:
        # Aula
        aula_op = ["— Seleccionar —"] + [a["nombre"] for a in aulas] + ["➕ Crear nueva aula…"]
        aula_sel = st.selectbox("Aula", aula_op, index=0, key="gh_aula_sel")
        aula_id = None
        if aula_sel and aula_sel not in ["— Seleccionar —", "➕ Crear nueva aula…"]:
            aula_id = next((a["id"] for a in aulas if a["nombre"] == aula_sel), None)

    colX, colY, colZ = st.columns([1.2, 1.2, 1.6], gap="small")

    with colX:
        if carrera_sel == "➕ Crear nueva carrera…":
            nueva = st.text_input("Nueva carrera", placeholder="Ej. Big Data", key="gh_new_carrera")
            if st.button("Guardar carrera", use_container_width=True, key="btn_new_carrera"):
                try:
                    with st.spinner("Guardando carrera..."):
                        r = extras.crear_carrera_si_no_existe(nueva)
                    st.session_state["gh_flash"] = {
                        "kind": "success" if r.get("created") else "warning",
                        "text": "Carrera guardada" if r.get("created") else "Carrera ya existe",
                        "detail": "✅ Carrera guardada" if r.get("created") else "ℹ️ Carrera ya existía",
                    }
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with colY:
        if docente_sel == "➕ Crear nuevo docente…":
            nuevo = st.text_input("Nuevo docente", placeholder="Ej. Verónica Chimbo", key="gh_new_docente")
            if st.button("Guardar docente", use_container_width=True, key="btn_new_docente"):
                try:
                    with st.spinner("Guardando docente..."):
                        r = extras.crear_docente_si_no_existe(nuevo)
                    st.session_state["gh_flash"] = {
                        "kind": "success" if r.get("created") else "warning",
                        "text": "Docente guardado" if r.get("created") else "Docente ya existe",
                        "detail": "✅ Docente guardado" if r.get("created") else "ℹ️ Docente ya existía",
                    }
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with colZ:
        if aula_sel == "➕ Crear nueva aula…":
            nuevo = st.text_input("Nueva aula", placeholder="Ej. Laboratorio 1", key="gh_new_aula")
            if st.button("Guardar aula", use_container_width=True, key="btn_new_aula"):
                try:
                    with st.spinner("Guardando aula..."):
                        r = extras.crear_aula_si_no_existe(nuevo)
                    st.session_state["gh_flash"] = {
                        "kind": "success" if r.get("created") else "warning",
                        "text": "Aula guardada" if r.get("created") else "Aula ya existe",
                        "detail": "✅ Aula guardada" if r.get("created") else "ℹ️ Aula ya existía",
                    }
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # Asignatura
    left2, mid2, right2 = st.columns([1.6, 0.9, 1.5], gap="small")
    asignaturas = _cache_asignaturas(periodo=periodo, carrera=carrera_id, docente=docente_id) if (periodo and carrera_id and docente_id) else []
    asig_op = ["— Seleccionar —"] + [f"{a['nombre']} (Ciclo {a.get('num_ciclo','?')})" for a in asignaturas] + ["➕ Crear nueva asignatura…"]
    with left2:
        asig_sel = st.selectbox("Asignatura", asig_op, index=0, key="gh_asig_sel")
    with mid2:
        ciclo = st.number_input("Ciclo", min_value=1, max_value=20, value=1, step=1, key="gh_ciclo")
    with right2:
        nombre_asig = ""
        if asig_sel == "➕ Crear nueva asignatura…":
            nombre_asig = st.text_input("Nueva asignatura", placeholder="Ej. Marcos de Referencia a la Big Data", key="gh_new_asig")

    asig_id = None
    if asig_sel and asig_sel not in ["— Seleccionar —", "➕ Crear nueva asignatura…"]:
        name = asig_sel.split(" (Ciclo")[0].strip()
        asig_id = next((a["id"] for a in asignaturas if a["nombre"] == name and int(a.get("num_ciclo") or 0) == int(ciclo)), None)
        if asig_id is None:
            asig_id = next((a["id"] for a in asignaturas if f"{a['nombre']} (Ciclo {a.get('num_ciclo','?')})" == asig_sel), None)

    create_asig_btn = False
    if asig_sel == "➕ Crear nueva asignatura…":
        c1, c2 = st.columns([1, 1], gap="small")
        with c1:
            create_asig_btn = st.button("Guardar asignatura", use_container_width=True, key="btn_new_asig")
        with c2:
            st.markdown('<div class="hint">Se valida duplicado por nombre + docente + carrera + periodo + ciclo.</div>', unsafe_allow_html=True)

        if create_asig_btn:
            try:
                if not (docente_id and carrera_id and periodo):
                    st.error("Seleccione periodo, carrera y docente antes de crear la asignatura.")
                else:
                    with st.spinner("Guardando asignatura..."):
                        r = extras.crear_asignatura_si_no_existe(
                            nombre_asignatura=nombre_asig,
                            id_docente=docente_id,
                            id_carrera=carrera_id,
                            periodo_academico=periodo,
                            num_ciclo=int(ciclo),
                        )
                    st.session_state["gh_flash"] = {
                        "kind": "success" if r.get("created") else "warning",
                        "text": "Asignatura guardada" if r.get("created") else "Asignatura ya existe",
                        "detail": "✅ Asignatura guardada" if r.get("created") else "ℹ️ Asignatura ya existía",
                    }
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()


    plan_left, plan_mid = st.columns([1.2, 1.8], gap="large")

    with plan_left:
        st.subheader("🛠️ Planificador rápido")
        dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        dia = st.selectbox("Día", dias, index=0, key="gh_dia")

        slots = _slot_list("07:00", "21:00", 60)
        st.caption("Selecciona uno o varios bloques de 1 hora. Se unirán automáticamente si son consecutivos.")

        validar_docente = st.toggle(
            "Validar solapamiento por docente",
            value=True,
            help="Evita que un docente tenga dos clases al mismo tiempo.",
        )
        validar_aula = st.toggle(
            "Validar solapamiento por aula",
            value=True,
            help="Evita que un aula tenga dos clases al mismo tiempo.",
        )

        ocup_aula, ocup_doc = set(), set()
        if periodo and (aula_id or docente_id):
            with st.spinner("Calculando disponibilidad..."):
                ocup_aula, ocup_doc = _ocupados_union(periodo=periodo, dia=dia, aula_id=aula_id, docente_id=docente_id, slots=slots)

        ocupados = set()
        if validar_aula:
            ocupados |= set(ocup_aula)
        if validar_docente:
            ocupados |= set(ocup_doc)

        disponibles = [s for s in slots if s not in ocupados]

        st.markdown(
            f'<div class="hint">Ocupados por aula: <b>{len(ocup_aula)}</b> · por docente: <b>{len(ocup_doc)}</b> · Bloques disponibles: <b>{len(disponibles)}</b></div>',
            unsafe_allow_html=True,
        )

        mostrar_ocupados = st.checkbox("Mostrar también bloques ocupados", value=False)

        def _fmt_slot(x: str) -> str:
            end = _add_minutes(x, 60)
            tags = []
            if validar_aula and x in ocup_aula:
                tags.append("🏫")
            if validar_docente and x in ocup_doc:
                tags.append("👤")
            if tags:
                return f"{x} - {end}  ⛔ {'/'.join(tags)}"
            return f"{x} - {end}"

        opciones_slots = slots if mostrar_ocupados else disponibles
        bloques = st.multiselect(
            "Bloques (elige uno o varios)",
            options=opciones_slots,
            default=[],
            key="gh_bloques",
            format_func=_fmt_slot,
        )

        if validar_aula or validar_docente:
            st.caption("Leyenda: ⛔ ocupada · 🏫 aula ocupada · 👤 docente ocupado")

        if st.button("💾 Guardar horario", use_container_width=True, key="btn_save_schedule"):
            if not periodo:
                st.error("Seleccione un periodo académico.")
            elif not (aula_id and docente_id and carrera_id):
                st.error("Seleccione carrera, docente y aula.")
            elif not asig_id:
                st.error("Seleccione o cree una asignatura.")
            elif not bloques:
                st.error("Seleccione al menos un bloque horario.")
            else:
                bloque_invalido = [b for b in bloques if b in ocupados]
                if bloque_invalido:
                    st.error(
                        "Los siguientes bloques ya están ocupados según la validación activa: "
                        + ", ".join([f"{b}-{_add_minutes(b,60)}" for b in sorted(bloque_invalido)])
                    )
                    st.stop()

                with st.spinner("Guardando horarios..."):
                    intervals = _merge_slots(bloques, 60)
                    total_inserted = 0
                    all_conflicts = []

                    for hi, hf in intervals:
                        try:
                            conflicts = extras.verificar_solapamiento_horario(
                                periodo_academico=periodo,
                                dia=dia,
                                hora_inicio=hi,
                                hora_fin=hf,
                                id_aula=aula_id if validar_aula else None,
                                id_docente=docente_id if validar_docente else None,
                            )
                            if conflicts:
                                all_conflicts.extend(conflicts)
                                continue

                            r = extras.crear_horario(
                                id_asignatura=asig_id,
                                id_aula=aula_id,
                                dia=dia,
                                hora_inicio=hi,
                                hora_fin=hf,
                                periodo_academico=periodo,
                                id_docente=docente_id,
                            )
                            if r.get("inserted"):
                                total_inserted += 1
                            else:
                                all_conflicts.extend(r.get("conflicts", []))
                        except Exception as e:
                            all_conflicts.append({"error": str(e), "dia": dia, "hora_inicio": hi, "hora_fin": hf})

                if total_inserted and not all_conflicts:
                    st.session_state["gh_flash"] = {
                        "kind": "success",
                        "text": "✅ Horario guardado",
                        "detail": f"Se guardaron {total_inserted} bloque(s) / intervalo(s) correctamente.",
                    }
                    st.cache_data.clear()
                    st.rerun()

                if total_inserted and all_conflicts:
                    st.session_state["gh_flash"] = {
                        "kind": "warning",
                        "text": "⚠️ Guardado parcial",
                        "detail": f"Se guardaron {total_inserted} intervalo(s), pero hubo solapamientos/errores en otros.",
                    }
                    st.session_state["gh_conflicts"] = all_conflicts
                    st.cache_data.clear()
                    st.rerun()

                if (not total_inserted) and all_conflicts:
                    st.session_state["gh_flash"] = {
                        "kind": "error",
                        "text": "⛔ No se guardó",
                        "detail": "No se guardó ningún intervalo por solapamientos o errores.",
                    }
                    st.session_state["gh_conflicts"] = all_conflicts
                    st.cache_data.clear()
                    st.rerun()

    with plan_mid:
        st.subheader("📅 Horario del periodo")
        st.caption("Vista rápida (por aula/carrera/docente). Usa los filtros para explorar.")

        f1, f2, f3 = st.columns([1.2, 1.2, 1.2], gap="small")
        with f1:
            filtro_aula = st.selectbox("Filtrar por aula", ["(Todas)"] + [a["nombre"] for a in aulas], index=0, key="gh_f_aula")
        with f2:
            filtro_doc = st.selectbox("Filtrar por docente", ["(Todos)"] + [d["nombre"] for d in docentes], index=0, key="gh_f_doc")
        with f3:
            filtro_car = st.selectbox("Filtrar por carrera", ["(Todas)"] + [c["nombre"] for c in carreras], index=0, key="gh_f_car")

        aula_f_id = None if filtro_aula == "(Todas)" else next((a["id"] for a in aulas if a["nombre"] == filtro_aula), None)
        doc_f_id = None if filtro_doc == "(Todos)" else next((d["id"] for d in docentes if d["nombre"] == filtro_doc), None)
        car_f_id = None if filtro_car == "(Todas)" else next((c["id"] for c in carreras if c["nombre"] == filtro_car), None)

        if periodo:
            with st.spinner("Cargando horario del periodo..."):
                horarios = _cache_horarios(periodo=periodo, aula=aula_f_id, docente=doc_f_id, carrera=car_f_id)
        else:
            horarios = []
        if not horarios:
            st.info("No hay horarios para mostrar con los filtros actuales.")
        else:
            # Grilla
            slots = _slot_list("07:00", "21:00", 60)
            dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
            grid = _df_horario_grid(horarios, slots, dias)

            st.dataframe(grid, use_container_width=True, height=420)

            with st.expander("Ver detalle (tabla)"):
                df = pd.DataFrame(horarios)
                cols = ["dia", "hora_inicio", "hora_fin", "aula", "asignatura", "docente", "carrera", "num_ciclo"]
                st.dataframe(df[cols], use_container_width=True, height=320)

with tabs[1]:
    st.subheader("📚 Altas rápidas ")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("#### 👩‍🏫 Docentes")
        docentes = _CATALOGOS["docentes"]
        st.dataframe(pd.DataFrame(docentes), use_container_width=True, height=260)
        with st.form("form_add_docente"):
            nombre = st.text_input("Nombre del docente", placeholder="Ej. Verónica Chimbo")
            ok = st.form_submit_button("Guardar docente")
        if ok:
            try:
                with st.spinner("Guardando docente..."):
                    r = extras.crear_docente_si_no_existe(nombre)
                st.session_state["gh_flash"] = {
                    "kind": "success" if r.get("created") else "warning",
                    "text": "Docente guardado" if r.get("created") else "Docente ya existe",
                    "detail": "✅ Docente guardado" if r.get("created") else "ℹ️ Docente ya existía",
                }
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("#### 🏫 Aulas")
        aulas = _CATALOGOS["aulas"]
        st.dataframe(pd.DataFrame(aulas), use_container_width=True, height=260)
        with st.form("form_add_aula"):
            nombre = st.text_input("Nombre del aula", placeholder="Ej. Laboratorio 1")
            ok = st.form_submit_button("Guardar aula")
        if ok:
            try:
                with st.spinner("Guardando aula..."):
                    r = extras.crear_aula_si_no_existe(nombre)
                st.session_state["gh_flash"] = {
                    "kind": "success" if r.get("created") else "warning",
                    "text": "Aula guardada" if r.get("created") else "Aula ya existe",
                    "detail": "✅ Aula guardada" if r.get("created") else "ℹ️ Aula ya existía",
                }
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with c2:
        st.markdown("#### 🎓 Carreras")
        carreras = _CATALOGOS["carreras"]
        st.dataframe(pd.DataFrame(carreras), use_container_width=True, height=260)
        with st.form("form_add_carrera"):
            nombre = st.text_input("Nombre de la carrera", placeholder="Ej. Big Data")
            ok = st.form_submit_button("Guardar carrera")
        if ok:
            try:
                with st.spinner("Guardando carrera..."):
                    r = extras.crear_carrera_si_no_existe(nombre)
                st.session_state["gh_flash"] = {
                    "kind": "success" if r.get("created") else "warning",
                    "text": "Carrera guardada" if r.get("created") else "Carrera ya existe",
                    "detail": "✅ Carrera guardada" if r.get("created") else "ℹ️ Carrera ya existía",
                }
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("#### 📘 Asignaturas")

        data = _CATALOGOS
        periodos = data["periodos"] or ["(Sin periodos)"]
        periodo = st.selectbox("Periodo", periodos, index=0, key="cat_periodo")
        carreras = data["carreras"]
        docentes = data["docentes"]
        colx, coly, colz = st.columns([1.1, 1.1, 0.8], gap="small")
        with colx:
            car = st.selectbox("Carrera", ["—"] + [c["nombre"] for c in carreras], index=0, key="cat_car")
        with coly:
            doc = st.selectbox("Docente", ["—"] + [d["nombre"] for d in docentes], index=0, key="cat_doc")
        with colz:
            ciclo = st.number_input("Ciclo", min_value=1, max_value=20, value=1, step=1, key="cat_ciclo")

        car_id = next((c["id"] for c in carreras if c["nombre"] == car), None) if car != "—" else None
        doc_id = next((d["id"] for d in docentes if d["nombre"] == doc), None) if doc != "—" else None

        asigns = _cache_asignaturas(periodo=periodo, carrera=car_id, docente=doc_id) if (periodo and (car_id or doc_id)) else _cache_asignaturas(periodo=periodo)
        st.dataframe(pd.DataFrame(asigns), use_container_width=True, height=260)

        with st.form("form_add_asig"):
            nombre = st.text_input("Nombre de asignatura", placeholder="Ej. Marcos de Referencia a la Big Data")
            ok = st.form_submit_button("Guardar asignatura")
        if ok:
            try:
                if not (periodo and car_id and doc_id):
                    st.error("Seleccione periodo, carrera y docente.")
                else:
                    with st.spinner("Guardando asignatura..."):
                        r = extras.crear_asignatura_si_no_existe(nombre, doc_id, car_id, periodo, int(ciclo))
                    st.session_state["gh_flash"] = {
                        "kind": "success" if r.get("created") else "warning",
                        "text": "Asignatura guardada" if r.get("created") else "Asignatura ya existe",
                        "detail": "✅ Asignatura guardada" if r.get("created") else "ℹ️ Asignatura ya existía",
                    }
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


with tabs[2]:
    st.subheader("📋 Horarios")
    data = _CATALOGOS
    periodos = data["periodos"] or ["(Sin periodos)"]
    periodo = st.selectbox("Periodo académico", periodos, index=0, key="list_periodo")

    docentes = data["docentes"]
    aulas = data["aulas"]
    carreras = data["carreras"]

    c1, c2, c3 = st.columns([1.2, 1.2, 1.2], gap="small")
    with c1:
        aula = st.selectbox("Aula", ["(Todas)"] + [a["nombre"] for a in aulas], index=0, key="list_aula")
    with c2:
        doc = st.selectbox("Docente", ["(Todos)"] + [d["nombre"] for d in docentes], index=0, key="list_doc")
    with c3:
        car = st.selectbox("Carrera", ["(Todas)"] + [c["nombre"] for c in carreras], index=0, key="list_car")

    aula_id = None if aula == "(Todas)" else next((a["id"] for a in aulas if a["nombre"] == aula), None)
    doc_id = None if doc == "(Todos)" else next((d["id"] for d in docentes if d["nombre"] == doc), None)
    car_id = None if car == "(Todas)" else next((c["id"] for c in carreras if c["nombre"] == car), None)

    with st.spinner("Cargando horarios..."):
        horarios = _cache_horarios(periodo=periodo, aula=aula_id, docente=doc_id, carrera=car_id)

    if not horarios:
        st.info("No hay registros de horarios para el filtro seleccionado.")
    else:
        df = pd.DataFrame(horarios)
        # orden y columnas útiles
        cols = ["dia", "hora_inicio", "hora_fin", "aula", "asignatura", "docente", "carrera", "periodo_academico", "num_ciclo"]
        st.dataframe(df[cols], use_container_width=True, height=520)

        st.download_button(
            "⬇️ Descargar CSV",
            data=df[cols].to_csv(index=False).encode("utf-8"),
            file_name=f"horarios_{periodo}.csv",
            mime="text/csv",
            use_container_width=True,
        )