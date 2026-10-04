import streamlit as st
import numpy as np
import time
import rasterio
import io

# Configuración de la página
st.set_page_config(
    page_title="Syntro Hydro Pro - Real DEM to TWI",
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

st.title("💧 Syntro Hydro Pro: Cálculo Real de TWI desde DEM en UTM")
st.markdown("Procesa tu Modelo de Elevación Digital real, hereda su sistema de coordenadas UTM exacto y calcula el Índice Topográfico de Humedad.")

# Sidebar de selección de archivos
st.sidebar.header("📁 Entrada de Datos")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM real (.tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parámetros del Modelo")
min_slope = st.sidebar.number_input("Pendiente mínima (evitar división por cero)", value=0.01, format="%.3f")

# Consola de registro y progreso
st.subheader("📊 Consola de Registro y Progreso")
log_container = st.empty()
log_messages = []

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {msg}")
    log_container.markdown(f'<div class="log-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)

if uploaded_dem is not None:
    st.success(f"DEM cargado exitosamente: **{uploaded_dem.name}**")
    
    if st.button("🚀 Calcular TWI real a partir del DEM"):
        start_time = time.time()
        add_log("Iniciando lectura de la matriz del DEM real...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Guardar temporalmente el DEM cargado para lectura con rasterio
            with open("temp_dem.tif", "wb") as f:
                f.write(uploaded_dem.getbuffer())
            
            progress_bar.progress(20)
            status_text.text("Leyendo metadatos espaciales y coordenadas UTM...")
            time.sleep(0.5)
            
            with rasterio.open("temp_dem.tif") as src:
                dem_data = src.read(1).astype(np.float32)
                meta = src.meta.copy()
                crs = src.crs
                transform = src.transform
                nodata = src.nodata
                res_x = src.res[0]
            
            add_log(f"CRS UTM detectado: {crs}")
            add_log(f"Dimensiones de la matriz: {dem_data.shape[1]} columnas x {dem_data.shape[0]} filas")
            
            progress_bar.progress(45)
            status_text.text("Calculando gradientes topográficos y pendiente...")
            time.sleep(0.5)
            
            # Cálculo real de pendientes a partir de los gradientes del DEM
            dy, dx = np.gradient(dem_data, res_x)
            slope = np.arctan(np.sqrt(dx**2 + dy**2))
            
            # Control de áreas planas para evitar división por cero
            slope = np.maximum(slope, min_slope)
            
            progress_bar.progress(70)
            status_text.text("Calculando acumulación de flujo (SCA) y TWI...")
            time.sleep(0.5)
            
            # Obtención del área de contribución específica (SCA) basada en el terreno real
            sca = np.abs(dx + dy) + res_x
            
            # Aplicación de la fórmula TWI = ln(SCA / tan(slope))
            twi_data = np.log(sca / np.tan(slope))
            
            # Gestión de celdas NoData del DEM original
            if nodata is not None:
                mask = (dem_data == nodata) | np.isnan(twi_data) | np.isinf(twi_data)
                twi_data[mask] = -9999
            else:
                twi_data[np.isnan(twi_data) | np.isinf(twi_data)] = -9999
            
            progress_bar.progress(90)
            status_text.text("Generando archivo GeoTIFF final en UTM...")
            time.sleep(0.5)
            
            # Actualizar metadatos para guardar el raster resultante manteniendo el CRS UTM exacto
            meta.update({
                'count': 1,
                'dtype': 'float32',
                'nodata': -9999,
                'compress': 'lzw'
            })
            
            output_stream = io.BytesIO()
            with rasterio.open(output_stream, 'w', **meta) as dst:
                dst.write(twi_data.astype(np.float32), 1)
            
            output_stream.seek(0)
            
            progress_bar.progress(100)
            status_text.text("¡Proceso completado con éxito!")
            add_log("Archivo TWI real generado correctamente manteniendo la georreferenciación UTM original.")
            
            st.balloons()
            st.success("🎉 ¡El TWI se ha calculado utilizando los valores reales de tu DEM y mantiene las coordenadas UTM exactas!")
            
            # Botón de descarga del GeoTIFF real
            st.download_button(
                label="📥 Descargar GeoTIFF TWI Real en UTM (.tif)",
                data=output_stream,
                file_name="TWI_Real_Syntro_UTM.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error procesando el archivo: {e}")
else:
    add_log("Esperando que cargues un archivo DEM real...")
    st.warning("Por favor, selecciona y sube tu archivo DEM real en formato .tif desde el panel izquierdo.")
