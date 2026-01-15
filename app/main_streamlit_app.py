import streamlit as st

# =====================
# CONFIGURACIÓN
# =====================
st.set_page_config(
    page_title="Focus Meter Web",
    layout="wide"
)

# =====================
# CREDENCIALES QUEMADAS
# =====================
USUARIO = "admin"
PASSWORD = "1234"

# =====================
# SESSION STATE
# =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =====================
# ESTILOS
# =====================
st.markdown(
    """
    <style>
        header {
            visibility: hidden;
            height: -200px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================
# LOGIN
# =====================
def login():
    st.title("🔐 Login - Focus Meter")

    with st.form("login_form"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar sesión")

    if submit:
        if user == USUARIO and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Sesión iniciada")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")


# =====================
# LOGOUT
# =====================
def logout():
    st.session_state.logged_in = False
    st.rerun()


# =====================
# APP PRINCIPAL
# =====================
if not st.session_state.logged_in:
    login()
    st.stop()

# =====================
# BARRA SUPERIOR
# =====================
with st.sidebar:
    st.success("🟢 Sesión activa")
    if st.button("🚪 Cerrar sesión"):
        logout()

# =====================
# NAVEGACIÓN PROTEGIDA
# =====================
pg = st.navigation([
    st.Page("vista/home.py", title="🏠 Home"),
    st.Page("vista/semaforo.py", title="🚦 Semáforo"),
    st.Page("vista/estadisticas.py", title="📊 Estadísticas"),
    st.Page("vista/docs.py", title="📖 Documentación"),
])

pg.run()
