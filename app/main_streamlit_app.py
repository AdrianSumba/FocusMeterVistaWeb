import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "extras" / "logo_focusmeter.png"

st.set_page_config(
    page_title="Focus Meter Web",
    page_icon=str(LOGO_PATH),  
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

      div[data-testid="stSidebar"] .session-pill{
        display:flex;
        align-items:center;
        justify-content:center;
        gap: .35rem;
        padding: .50rem .60rem;
        margin: .45rem 0 .30rem 0;
        border-radius: .65rem;
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.25);
        color: rgba(15, 81, 50, 1);
        font-weight: 650;
        font-size: .92rem;
      }

      div[data-testid="stSidebar"] div[data-testid="stButton"] > button{
        width: 100% !important;
        height: 40px !important;
        padding: 0 .70rem !important;
        border-radius: .55rem !important;

        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;

        text-align: left !important;
        justify-content: flex-start !important;
        gap: .45rem !important;

        font-weight: 600 !important;
        font-size: .95rem !important;
        color: inherit !important;
      }

      div[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover{
        background: rgba(0,0,0,0.06) !important;
      }

      div[data-testid="stSidebar"] div[data-testid="stButton"] > button:active{
        background: rgba(0,0,0,0.10) !important;
      }

      div[data-testid="stSidebar"] div[data-testid="stButton"]{
        margin-top: .15rem !important;
        margin-bottom: .15rem !important;
      }
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

try:
    st.logo(str(LOGO_PATH), size="large") 
except TypeError:
    try:
        st.logo(str(LOGO_PATH))
    except Exception:
        pass  


pg = st.navigation(
    [
        st.Page("vista/home.py", title="🏠 Home"),
        st.Page("vista/gestion_horarios.py", title="🗓️ Gestión Académica"),
        st.Page("vista/semaforo.py", title="🚦 Semáforo"),
        st.Page("vista/estadisticas_actualizables.py", title="📊 Estadísticas"),
        st.Page("vista/estadisticas_powerbi.py", title="📊 Estadísticas PowerBI"),
        st.Page("vista/tendencias.py", title="📈 Tendencias"),
        st.Page("vista/proyecciones.py", title="🔮 Proyecciones"),
    ],
    position="sidebar",
)

with st.sidebar:
    st.markdown('<div class="session-pill">🟢 Sesión activa</div>', unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", key="logout_btn", use_container_width=True):
        logout()

pg.run()