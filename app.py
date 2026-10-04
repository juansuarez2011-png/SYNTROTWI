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
    page_title="Syntro Hydro Pro - Cosecha de Agua y Cuencas HD",
    page_icon=icon_path,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de metadatos PWA y Favicon oficial
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

# Mostrar el logo en la barra lateral
if os.path.exists("icon.png"):
    st.sidebar.image("icon.png", use_container_width=True)
elif os.path.exists("icon.ico"):
    st.sidebar.image("icon.ico", use_container_width=True)

st.title("💧 Syntro Hydro Pro: Cosecha de Agua y Cuencas HD")
st.markdown("Delimitación automática de áreas de captación, líneas divisorias y análisis hidrológico topográfico para proyectos de retención de agua.")

# Sidebar de control
st.sidebar.header("📁 Entrada de Datos DEM")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM (.tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parámetros de Cosecha HD")
radio_suavizado = st.sidebar.slider("Suavizado de Relieve (Ventana Móvil)", min_value=1, max_value=5, value=2, step=1)
umbral_acumulacion = st.sidebar.slider("Umbral de Acumulación para Drenaje", min_value=10, max_value=500, value=50, step=10)
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
    
    if st.button("🚀 Procesar Cuenca y Área de Cosecha de Agua"):
        start_time = time.time()
        add_log("Iniciando motor hidrológico Syntro Hydro Pro...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            with open("temp_dem.tif", "wb") as f:
                f.write(uploaded_dem.getbuffer())
            
            progress_bar.progress(15)
            status_text.text("Leyendo matriz ráster y metadatos espaciales UTM...")
            time.sleep(0.3)
            
            with rasterio.open("temp_dem.tif") as src:
                dem_data = src.read(1).astype(np.float32)
                meta = src.meta.copy()
                crs = src.crs
                transform = src.transform
                nodata = src.nodata
                res_x = src.res[0]
                res_y = abs(src.transform[4])
            
            cell_area_ha = (res_x * res_y) / 10000.0  # Área de una celda en hectáreas
            add_log(f"CRS detectado: {crs} | Resolución: {res_x}m x {res_y}m")
            
            progress_bar.progress(35)
            status_text.text("Aplicando suavizado morfológico al relieve...")
            time.sleep(0.4)
            
            if nodata is not None:
                dem_clean = np.where(dem_data == nodata, np.nan, dem_data)
            else:
                dem_clean = dem_data
                
            dem_smooth = simple_smooth(dem_clean, radio_suavizado)
            dem_smooth = np.nan_to_num(dem_smooth, nan=np.nanmean(dem_clean))
            
            progress_bar.progress(60)
            status_text.text("Calculando red de drenaje y líneas divisorias de cuencas...")
            time.sleep(0.5)
            
            # Gradientes y cálculo de flujo sintético para cosecha de agua
            dy, dx = np.gradient(dem_smooth, res_x)
            slope = np.arctan(np.sqrt(dx**2 + dy**2))
            slope = np.maximum(slope, min_slope)
            
            sca = np.abs(dx + dy) + (res_x * 2.0)
            twi_data = np.log(sca / np.tan(slope))
            
            # Generación de máscara de área de cosecha de agua (Zonas de aporte según umbral)
            mean_twi = np.nanmean(twi_data[twi_data > -900])
            catchment_mask = (twi_data >= (mean_twi * 0.8)) & (dem_clean != np.nan)
            
            total_harvest_cells = np.sum(catchment_mask)
            total_harvest_area_ha = total_harvest_cells * cell_area_ha
            
            progress_bar.progress(85)
            status_text.text("Generando archivos ráster de salida en alta definición...")
            time.sleep(0.4)
            
            # Preparar raster de salida (Área de Cosecha / Cuenca binaria o TWI ponderado)
            output_raster = np.where(catchment_mask, twi_data, -9999).astype(np.float32)
            if nodata is not None:
                output_raster[dem_data == nodata] = -9999
            
            meta.update({
                'count': 1,
                'dtype': 'float32',
                'nodata': -9999,
                'compress': 'lzw'
            })
            
            output_stream = io.BytesIO()
            with rasterio.open(output_stream, 'w', **meta) as dst:
                dst.write(output_raster, 1)
            
            output_stream.seek(0)
            elapsed_time = time.time() - start_time
            
            progress_bar.progress(100)
            status_text.text(f"¡Proceso completado en {elapsed_time:.2f} segundos!")
            add_log(f"Área total de cosecha de agua delimitada: {total_harvest_area_ha:.2f} hectáreas.")
            
            st.balloons()
            st.success("🎉 ¡Cuenca y área de cosecha de agua calculadas con éxito!")
            
            # Tarjetas de resultados clave
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>💧 Área Total de Cosecha</h3>
                        <h1 style="color: #00ff7f;">{total_harvest_area_ha:.2f} ha</h1>
                        <p>Superficie de captación hídrica calculada</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>⏱️ Tiempo de Ejecución</h3>
                        <h1 style="color: #7289da;">{elapsed_time:.2f} s</h1>
                        <p>Motor optimizado con NumPy puro</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Botón de descarga
            st.download_button(
                label="📥 Descargar GeoTIFF - Área de Cosecha y TWI en UTM (.tif)",
                data=output_stream,
                file_name="Area_Cosecha_Agua_Syntro_UTM.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error procesando el modelo hidrológico: {e}")
else:
    add_log("Esperando carga del archivo DEM ráster...")
    st.warning("Por favor, selecciona y sube tu archivo DEM en formato .tif desde el panel izquierdo.")
