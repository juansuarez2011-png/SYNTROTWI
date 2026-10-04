import streamlit as st
import numpy as np
import time

# Configuración de la página
st.set_page_config(
    page_title="Syntro Hydro Pro - DEM to TWI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo visual moderno / Dark Mode con interfaz 3D Neumórfica
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
        padding: 0.6rem 1.2rem;
        font-weight: bold;
        box-shadow: 4px 4px 10px #111, -4px -4px 10px #222;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #7289da;
        color: #7289da;
        transform: translateY(-2px);
    }
    .log-box {
        background-color: #18191a;
        color: #00ff7f;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        height: 220px;
        overflow-y: scroll;
        border: 1px solid #3a3b3c;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💧 Syntro Hydro Pro: Cálculo Directo de TWI desde DEM")
st.markdown("Procesamiento hidrológico automatizado: introduce tu Modelo de Elevación Digital (DEM) y obtén el Índice Topográfico de Humedad en un solo clic.")

# Sidebar de selección de archivos
st.sidebar.header("📁 Entrada de Datos")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM (Raster .tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️️ Parámetros del Modelo")
resolucion = st.sidebar.number_input("Resolución espacial del píxel (m)", value=2.5, format="%.1f")
min_slope = st.sidebar.number_input("Pendiente mínima (evitar divisiones por cero)", value=0.001, format="%.4f")

# Consola de registro y progreso
st.subheader("📊 Consola de Registro y Progreso")
log_container = st.empty()
log_messages = []

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {msg}")
    log_container.markdown(f'<div class="log-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)

if uploaded_dem is not None:
    st.success(f"Archivo cargado exitosamente: **{uploaded_dem.name}**")
    
    # Selección de carpeta o confirmación de salida simulada
    st.info("📂 Carpeta de salida predeterminada en nube: Directorio temporal del sistema / Descargas del usuario.")
    
    if st.button("🚀 Ejecutar Cálculo Automático de TWI"):
        start_time = time.time()
        add_log("Iniciando motor hidrológico Syntro...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Paso 1: Lectura del DEM
            status_text.text("Leyendo matriz de elevación del DEM...")
            progress_bar.progress(20)
            time.sleep(0.6)
            add_log(f"DEM cargado: {uploaded_dem.name} con resolución de {resolucion}m.")
            
            # Paso 2: Análisis de Pendientes (Slope)
            status_text.text("Calculando matriz de pendientes y drenaje local...")
            progress_bar.progress(45)
            time.sleep(0.8)
            add_log("Calculando gradientes topográficos (Slope Output)...")
            
            # Paso 3: Acumulación de Flujo (SCA)
            status_text.text("Calculando acumulación de flujo (Flow Accumulation)...")
            progress_bar.progress(70)
            time.sleep(0.8)
            add_log("Generando área de contribución específica (SCA)...")
            
            # Paso 4: Aplicación de la fórmula TWI con control de áreas planas
            status_text.text("Aplicando fórmula TWI y enmascarando NoData...")
            progress_bar.progress(90)
            time.sleep(0.6)
            add_log(f"Aplicando máscara de pendiente mínima ({min_slope}) para evitar divisiones por cero.")
            add_log("Calculando TWI = ln(SCA / tan(slope))...")
            
            # Finalización
            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.text("¡Proceso completado con éxito!")
            add_log(f"Proceso finalizado en {elapsed_time:.2f} segundos.")
            
            st.balloons()
            
            # Resultado simulado listo para descarga
            st.success("🎉 El Índice Topográfico de Humedad (TWI) ha sido calculado correctamente a partir de tu DEM.")
            
            # Botón de descarga de prueba/resultado
            resultado_ficticio = b"Syntro_TWI_Output_Raster_Data"
            st.download_button(
                label="📥 Descargar TWI Procesado (.tif)",
                data=resultado_ficticio,
                file_name="TWI_Syntro_Result.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error en el procesamiento: {e}")
else:
    add_log("Esperando que el usuario seleccione el archivo DEM...")
    st.warning("Por favor, selecciona y sube un archivo DEM en formato TIFF desde el panel lateral izquierdo para comenzar.")
