import streamlit as st

st.set_page_config(
    page_title="Sistema de Atención Estudiantil",
    layout="wide"
)

pg = st.navigation([
    st.Page("pages/home.py", title="🏠 Home"),
    st.Page("pages/monitoreo.py", title="📹 Monitoreo"),
    st.Page("pages/analisis.py", title="📊 Análisis"),
    st.Page("pages/tendencias.py", title="📈 Tendencias"),
    st.Page("pages/proyecciones.py", title="🔮 Proyecciones"),
    st.Page("pages/metodologia.py", title="📚 Metodología"),
])

pg.run()


