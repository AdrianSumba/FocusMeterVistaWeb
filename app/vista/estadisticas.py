import streamlit as st
import streamlit.components.v1 as components

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Acceso no autorizado")
    st.stop()

st.title("📊 Estadísticas")

embed_url = "https://app.powerbi.com/view?r=eyJrIjoiYzQxMjJiM2QtMmFjNi00ZWJlLWFiMDQtMThiNzgyZTYxZWY1IiwidCI6IjI1NzM5YzY1LWM3OWYtNDAxYy1iYWIwLWQ3NTVlOTBhNjY2MiIsImMiOjR9"

components.html(
    f"""
    <iframe 
        title="Call Center Performance Report" 
        width="100%" 
        height="600" 
        src="{embed_url}" 
        frameborder="0" 
        allowFullScreen="true">
    </iframe>
    """,
    height=600,
)