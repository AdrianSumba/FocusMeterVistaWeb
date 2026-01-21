import streamlit as st


st.set_page_config(
    page_title="Focus Meter Web",
    layout="wide",
    initial_sidebar_state="expanded",
)

USUARIO = "admin"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .block-container { padding-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True
)


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


def logout():
    st.session_state.logged_in = False
    st.rerun()


if not st.session_state.logged_in:
    login()
    st.stop()


with st.sidebar:
    st.success("🟢 Sesión activa")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()


pg = st.navigation(
    [
        st.Page("vista/home.py", title="🏠 Home"),
        st.Page("vista/semaforo.py", title="🚦 Semáforo"),
        st.Page("vista/estadisticas_actualizables.py", title="📊 Estadísticas"),
        st.Page("vista/estadisticas_powerbi.py", title="📊 Estadísticas PowerBI"),
        st.Page("vista/tendencias.py", title="📈 Tendencias"),
        st.Page("vista/proyecciones.py", title="🔮 Proyecciones"),
        st.Page("vista/docs.py", title="📖 Documentación"),
    ],
    position="sidebar",
)

pg.run()