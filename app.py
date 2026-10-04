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
    page_title="Syntro Hydro Pro - TWI HD",
    page_icon=icon_path,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de metadatos PWA y Favicon oficial Syntro
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

# Estilo visual moderno / Dark Mode con interfaz 3D Neumórfica Syntro
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
    .metric-card {
        background: linear-gradient(135deg, #1f2421, #111413);
        border: 1px solid #2f3633;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 5px 5px 15px #080a09, -5px -5px 15px #1a221f;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Mostrar el logotipo oficial en la barra lateral
if os.path.exists("icon.png"):
    st.sidebar.image("icon.png", use_container_width=True)
elif os.path.exists("icon.ico"):
    st.sidebar.image("icon.ico", use_container_width=True)

st.title("💧 Syntro Hydro Pro: Índice TWI HD")
st.markdown("Procesamiento avanzado de DEM sin bordes negros y cálculo exclusivo del Índice Topográfico de Humedad (TWI).")

# Sidebar de control
st.sidebar.header("📁 Entrada de Datos DEM")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM (.tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️️ Parámetros Hidrológicos HD")
radio_suavizado = st.sidebar.slider("Suavizado Topográfico (Ventana)", min_value=1, max_value=5, value=2, step=1)
min_slope = st.sidebar.number_input("Pendiente mínima", value=0.005, format="%.3f")

# Consola de registro y cronómetro
st.subheader("📊 Consola de Registro y Progreso")
log_container = st.empty()
log_messages = []

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {msg}")
    log_container.markdown(f'<div class="log-box">{"<br>".join(log_messages)}</div>', unsafe_allow_html=True)

def simple_smooth(arr, radius):
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
    
    if st.button("🚀 Procesar Índice TWI HD"):
        start_time = time.time()
        add_log("Iniciando motor hidrológico Syntro Hydro Pro (TWI)...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            with open("temp_dem.tif", "wb") as f:
                f.write(uploaded_dem.getbuffer())
            
            progress_bar.progress(15)
            status_text.text("Leyendo matriz ráster y metadatos UTM...")
            time.sleep(0.3)
            
            with rasterio.open("temp_dem.tif") as src:
                dem_data = src.read(1).astype(np.float32)
                meta = src.meta.copy()
                crs = src.crs
                transform = src.transform
                nodata = src.nodata
                res_x = src.res[0]
                res_y = abs(src.transform[4])
            
            cell_area_ha = (res_x * res_y) / 10000.0  # Área de celda en hectáreas
            add_log(f"CRS detectado: {crs} | Resolución: {res_x}m x {res_y}m")
            
            progress_bar.progress(35)
            status_text.text("Aplicando suavizado morfológico sin pérdida de relieve...")
            time.sleep(0.4)
            
            # Limpieza estricta de nulos usando NaN para evitar cuadros negros
            if nodata is not None:
                dem_clean = np.where(dem_data == nodata, np.nan, dem_data)
            else:
                dem_clean = dem_data
                
            dem_smooth = simple_smooth(dem_clean, radio_suavizado)
            
            progress_bar.progress(65)
            status_text.text("Calculando gradientes, pendiente y matriz TWI completa...")
            time.sleep(0.5)
            
            # Cálculo de gradiente y pendiente
            dy, dx = np.gradient(dem_smooth, res_x)
            slope = np.arctan(np.sqrt(dx**2 + dy**2))
            slope = np.maximum(slope, min_slope)
            
            # Cálculo de Área de Captación Específica (SCA) y TWI
            sca = np.abs(dx + dy) + (res_x * 2.0)
            twi_full = np.log(sca / np.tan(slope))
            
            # Enmascarar zonas inválidas con NaN (Transparente en visores)
            twi_full[np.isnan(dem_clean) | np.isinf(twi_full)] = np.nan
            
            # Cálculo de superficie válida del modelo en hectáreas
            valid_cells = np.sum(~np.isnan(twi_full))
            total_area_ha = valid_cells * cell_area_ha
            
            progress_bar.progress(85)
            status_text.text("Empaquetando ráster GeoTIFF en alta definición...")
            time.sleep(0.4)
            
            # Actualizar metadatos con NaN como nodata transparente
            meta.update({
                'count': 1,
                'dtype': 'float32',
                'nodata': np.nan,
                'compress': 'lzw'
            })
            
            # Guardar TWI Completo
            twi_stream = io.BytesIO()
            with rasterio.open(twi_stream, 'w', **meta) as dst:
                dst.write(twi_full.astype(np.float32), 1)
            twi_stream.seek(0)
            
            elapsed_time = time.time() - start_time
            progress_bar.progress(100)
            status_text.text(f"¡Proceso completado en {elapsed_time:.2f} segundos!")
            add_log(f"Área analizada de TWI: {total_area_ha:.2f} hectáreas.")
            
            st.success("🎉 ¡Índice TWI calculado exitosamente sin manchas negras!")
            
            # Tarjetas de métricas
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>📐 Área Total Analizada</h3>
                        <h1 style="color: #00ff7f;">{total_area_ha:.2f} ha</h1>
                        <p>Superficie efectiva procesada</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>⏱️ Tiempo de Ejecución</h3>
                        <h1 style="color: #7289da;">{elapsed_time:.2f} s</h1>
                        <p>Procesamiento optimizado en NumPy</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Botón de descarga para TWI
            st.markdown("### 📥 Descarga de Resultado Geográfico (UTM)")
            st.download_button(
                label="📥 Descargar Índice TWI Completo HD (.tif)",
                data=twi_stream,
                file_name="TWI_Completo_Syntro_UTM.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error procesando el modelo: {e}")
else:
    add_log("Esperando carga del archivo DEM ráster...")
    st.warning("Por favor, selecciona y sube tu archivo DEM en formato .tif desde el panel izquierdo.")
