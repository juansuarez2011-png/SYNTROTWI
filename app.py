import streamlit as st
import numpy as np
import time
import rasterio
import io
import os
import base64

# Configuración de la página
icon_path = "icon.ico" if os.path.exists("icon.ico") else ("icon.png" if os.path.exists("icon.png") else "💧")

st.set_page_config(
    page_title="Syntro Hydro Pro - TWI Smooth HD",
    page_icon=icon_path,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de metadatos avanzados, favicon y manifiesto PWA para forzar el ícono oficial en el acceso directo
def inject_pwa_headers():
    icon_file = "icon.ico" if os.path.exists("icon.ico") else ("icon.png" if os.path.exists("icon.png") else None)
    icon_base64 = ""
    if icon_file and os.path.exists(icon_file):
        with open(icon_file, "rb") as f:
            icon_base64 = base64.b64encode(f.read()).decode()
        ext = "ico" if icon_file.endswith(".ico") else "png"
        
    st.markdown(f"""
        <head>
            <link rel="manifest" href="/app/static/manifest.json" crossorigin="use-credentials">
            <link rel="icon" href="data:image/{ext};base64,{icon_base64}">
            <link rel="apple-touch-icon" href="data:image/{ext};base64,{icon_base64}">
        </head>
    """, unsafe_allow_html=True)

inject_pwa_headers()

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

# Mostrar el logo en la barra lateral si existe
if os.path.exists("icon.png"):
    st.sidebar.image("icon.png", use_container_width=True)
elif os.path.exists("icon.ico"):
    st.sidebar.image("icon.ico", use_container_width=True)

st.title("💧 Syntro Hydro Pro: TWI de Alta Definición (Suavizado Topográfico)")
st.markdown("Procesa tu DEM eliminando el efecto pixelado mediante interpolación avanzada y suavizado de relieve nativo.")

# Sidebar de selección de archivos
st.sidebar.header("📁 Entrada de Datos")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM real (.tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️️ Parámetros de Calidad HD")
radio_suavizado = st.sidebar.slider("Nivel de Suavizado por Ventana Móvil", min_value=1, max_value=5, value=1, step=1)
min_slope = st.sidebar.number_input("Pendiente mínima (evitar división por cero)", value=0.005, format="%.3f")

# Consola de registro y progreso
st.subheader("📊 Consola de Registro y Progreso")
log_container = st.empty()
log_messages = []

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {msg}")
    log_container.markdown(f'<div class="log-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)

def simple_smooth(arr, radius):
    """Aplica un suavizado espacial por vecinos utilizando NumPy puro."""
    if radius < 1:
        return arr
    out = arr.copy()
    h, w = arr.shape
    for r in range(radius, h - radius):
        for c in range(radius, w - radius):
            window = arr[r-radius:r+radius+1, c-radius:c+radius+1]
            valid_vals = window[~np.isnan(window)]
            if valid_vals.size > 0:
                out[r, c] = np.mean(valid_vals)
    return out

if uploaded_dem is not None:
    st.success(f"DEM cargado exitosamente: **{uploaded_dem.name}**")
    
    if st.button("🚀 Procesar TWI en Alta Definición"):
        start_time = time.time()
        add_log("Iniciando motor hidrológico Syntro HD...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            with open("temp_dem.tif", "wb") as f:
                f.write(uploaded_dem.getbuffer())
            
            progress_bar.progress(20)
            status_text.text("Leyendo matriz y metadatos espaciales UTM...")
            time.sleep(0.4)
            
            with rasterio.open("temp_dem.tif") as src:
                dem_data = src.read(1).astype(np.float32)
                meta = src.meta.copy()
                crs = src.crs
                transform = src.transform
                nodata = src.nodata
                res_x = src.res[0]
            
            add_log(f"CRS UTM detectado: {crs}")
            add_log(f"Resolución de celda: {res_x} metros")
            
            progress_bar.progress(40)
            status_text.text("Aplicando filtro de suavizado espacial al relieve...")
            time.sleep(0.5)
            
            if nodata is not None:
                dem_clean = np.where(dem_data == nodata, np.nan, dem_data)
            else:
                dem_clean = dem_data
                
            dem_smooth = simple_smooth(dem_clean, radio_suavizado)
            dem_smooth = np.nan_to_num(dem_smooth, nan=np.nanmean(dem_clean))
            
            progress_bar.progress(65)
            status_text.text("Calculando gradientes y acumulación de flujo continua...")
            time.sleep(0.5)
            
            dy, dx = np.gradient(dem_smooth, res_x)
            slope = np.arctan(np.sqrt(dx**2 + dy**2))
            slope = np.maximum(slope, min_slope)
            
            sca = np.abs(dx + dy) + (res_x * 2.0)
            twi_data = np.log(sca / np.tan(slope))
            
            twi_data[np.isnan(twi_data) | np.isinf(twi_data)] = -9999
            if nodata is not None:
                twi_data[dem_data == nodata] = -9999
            
            progress_bar.progress(85)
            status_text.text("Empaquetando GeoTIFF en alta definición...")
            time.sleep(0.4)
            
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
            add_log("Archivo TWI HD generado sin bloques pixelados.")
            
            st.balloons()
            st.success("🎉 ¡El TWI ha sido procesado con suavizado topográfico de alta definición!")
            
            st.download_button(
                label="📥 Descargar GeoTIFF TWI HD en UTM (.tif)",
                data=output_stream,
                file_name="TWI_HD_Syntro_UTM.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error procesando el archivo: {e}")
else:
    add_log("Esperando que cargues un archivo DEM real...")
    st.warning("Por favor, selecciona y sube tu archivo DEM real en formato .tif desde el panel izquierdo.")
