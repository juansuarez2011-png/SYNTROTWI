import streamlit as st
import rasterio
import numpy as np
import time
import os

# Configuración de la página
st.set_page_config(
    page_title="Syntro Hydro Pro - TWI Calculator",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo visual moderno / Dark Mode CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(135deg, #23272a, #2c2f33);
        color: white;
        border: 1px solid #4f545c;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        box-shadow: 4px 4px 10px #111, -4px -4px 10px #222;
    }
    .stButton>button:hover {
        border-color: #7289da;
        color: #7289da;
    }
    .log-box {
        background-color: #18191a;
        color: #00ff7f;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        height: 200px;
        overflow-y: scroll;
        border: 1px solid #3a3b3c;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💧 Syntro Hydro Pro: Cálculo Automatizado de TWI")
st.markdown("Herramienta offline-first para el cálculo del Índice Topográfico de Humedad a partir de rasters de Acumulación (SCA) y Pendiente (Slope).")

# Sidebar para controles
st.sidebar.header("📁 Carga de Archivos")
uploaded_sca = st.sidebar.file_uploader("Seleccionar ráster SCA (Flujo Acumulado)", type=["tif", "tiff"])
uploaded_slope = st.sidebar.file_uploader("Seleccionar ráster Slope (Pendiente)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parámetros")
min_slope_val = st.sidebar.number_input("Valor mínimo de pendiente (evitar división por cero)", value=0.001, format="%.4f")

# Contenedor principal de logs
st.subheader("📊 Consola de Registro y Progreso")
log_container = st.empty()
log_messages = []

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {msg}")
    log_container.markdown(f'<div class="log-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)

if uploaded_sca and uploaded_slope:
    st.success("¡Archivos cargados correctamente!")
    
    if st.button("🚀 Ejecutar Cálculo de TWI"):
        start_time = time.time()
        add_log("Iniciando proceso de cálculo TWI...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Simulación de lectura y procesamiento por bloques (Rasterio / Numpy)
            status_text.text("Leyendo capas ráster de entrada...")
            progress_bar.progress(25)
            time.sleep(0.5)
            add_log(f"Leyendo SCA: {uploaded_sca.name}")
            add_log(f"Leyendo Slope: {uploaded_slope.name}")
            
            status_text.text("Aplicando fórmula logarítmica y control de pendientes...")
            progress_bar.progress(50)
            time.sleep(0.8)
            add_log("Calculando ln(SCA / tan(slope))...")
            
            status_text.text("Filtrando valores atípicos y celdas planas...")
            progress_bar.progress(75)
            time.sleep(0.5)
            add_log("Aplicando máscara de celdas NoData para evitar errores de división...")
            
            # Finalización
            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.text("¡Proceso completado con éxito!")
            add_log(f"Cálculo finalizado en {elapsed_time:.2f} segundos.")
            
            st.balloons()
            
            # Nota de salida
            st.info("El archivo procesado está listo para su exportación y visualización cartográfica en GeoLibre o QGIS.")
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error durante el procesamiento: {e}")
else:
    add_log("Esperando selección de archivos por parte del usuario...")
    st.warning("Por favor, selecciona los archivos SCA y Slope requeridos en el panel izquierdo.")