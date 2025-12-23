import streamlit as st
from PIL import Image
from db.mongo import get_mongo_client

st.set_page_config(
    page_title="Sistema de Atención Estudiantil",
    layout="wide"
)

# ===== LOGO CENTRADO =====
logo = Image.open("vista/assets/LOGO-RECTANGULAR_SIN-FONDO.png")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(logo, width=450)

# ===== TÍTULO =====
st.markdown(
    "<h1 style='text-align: center;'>🎓 Sistema de Monitoreo del Nivel de Atención Estudiantil</h1>",
    unsafe_allow_html=True
)

st.markdown("---")

# ===== DESCRIPCIÓN =====

st.markdown(
    """
    <p style='text-align: justify; font-size:17px;'>
    Este proyecto desarrolla un sistema inteligente basado en <strong>vision por computadora
    e inteligencia artificial</strong> para monitorear en tiempo real el nivel de atención
    de los estudiantes durante las clases, utilizando una cámara web para analizar gestos
    faciales y patrones de concentración.  
    La solución ofrece a los docentes una <strong>herramienta visual e intuitiva</strong>,
    representada mediante un <strong>semáforo de atención</strong>, que permite identificar
    estados de alta y baja atención con el fin de optimizar el proceso de enseñanza–aprendizaje.
    </p>
    """,
    unsafe_allow_html=True
)



# ===== INTEGRANTES =====
st.subheader("👨‍💻 Integrantes del Proyecto")
st.markdown("""
- Christian Eduardo Mendieta Tenesaca  
- Freddy Orlando Montalván Quito  
- Jimmy Adrián Sumba Juela  
""")

# ===== TUTOR =====
st.subheader("👩‍🏫 Tutor del Proyecto")
st.write("Ing. Lorena Calle")


# ===== CONEXIÓN A MONGODB =====

st.markdown("---")
st.subheader("🗄️ Estado de la Base de Datos")

try:
    client = get_mongo_client()
    db = client["Base"]
    coleccion = db["registros_atencion"]

    total = coleccion.count_documents({})

    st.success("✅ Conectado correctamente a MongoDB Atlas")
    st.caption(f"Registros almacenados: {total}")

except Exception as e:
    st.error("❌ Error al conectar con MongoDB")
    st.code(str(e))

