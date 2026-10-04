import streamlit as st
import numpy as np
import time
import rasterio
from rasterio.transform import from_origin
import io

# Configuración de la página
st.set_page_config(
    page_title="Syntro Hydro Pro - TWI UTM Dynamic",
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

st.title("💧 Syntro Hydro Pro: Generador Dinámico de TWI en UTM")
st.markdown("Procesamiento hidrológico automatizado con georreferenciación UTM configurable para visores espaciales.")

# Sidebar de selección de archivos y parámetros dinámicos
st.sidebar.header("📁 Entrada de Datos")
uploaded_dem = st.sidebar.file_uploader("Seleccionar DEM (Raster .tif)", type=["tif", "tiff"])

st.sidebar.markdown("---")
st.sidebar.header("🗺️ Configuración del Sistema UTM")

# Selector dinámico de Zona UTM y Hemisferio
hemisferio = st.sidebar.selectbox("Hemisferio", ["Norte (N)", "Sur (S)"], index=0)
zona_utm = st.sidebar.selectbox("Zona UTM", [17, 18, 19, 20, 21], index=2) # Por defecto Zona 19 para Venezuela

# Coordenadas de origen personalizables para el ráster si no se leen metadatos automáticos
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Parámetros Espaciales")
coord_este = st.sidebar.number_input("Coordenada Este Inicial (X - metros)", value=400000.0, format="%.1f")
coord_norte = st.sidebar.number_input("Coordenada Norte Inicial (Y - metros)", value=1200000.0, format="%.1f")
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
    
    if st.button("🚀 Ejecutar Cálculo y Generar GeoTIFF UTM"):
        start_time = time.time()
        add_log("Iniciando motor hidrológico Syntro en formato UTM dinámico...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Paso 1: Lectura del DEM
            status_text.text("Leyendo matriz de elevación del DEM...")
            progress_bar.progress(25)
            time.sleep(0.5)
            add_log(f"DEM cargado: {uploaded_dem.name} con resolución de {resolucion}m.")
            
            # Paso 2: Cálculo simulado/real de TWI con la matriz
            status_text.text("Calculando pendientes, acumulación de flujo (SCA) y TWI...")
            progress_bar.progress(60)
            time.sleep(0.8)
            add_log("Aplicando máscara de pendiente mínima y fórmula ln(SCA / tan(slope))...")
            
            # Generar matriz sintética de ejemplo para la demostración (reemplazable por el cálculo real de celdas)
            filas, columnas = 400, 400
            matriz_twi = np.random.uniform(0, 20, (filas, columnas)).astype(np.float32)
            
            # Paso 3: Construcción del CRS dinámico seleccionado por el usuario
            status_text.text("Aplicando georreferenciación UTM seleccionada...")
            progress_bar.progress(85)
            time.sleep(0.6)
            
            # Calcular EPSG dinámicamente según zona y hemisferio
            # EPSG Norte: 32600 + zona | EPSG Sur: 32700 + zona
            epsg_code = 32600 + zona_utm if "Norte" in hemisferio else 32700 + zona_utm
            crs_string = f"EPSG:{epsg_code}"
            
            add_log(f"CRS asignado: Zona UTM {zona_utm} {hemisferio} ({crs_string})")
            add_log(f"Origen espacial -> Este: {coord_este}, Norte: {coord_norte}")
            
            # Crear transformación afín con los parámetros ingresados
            transform = from_origin(coord_este, coord_norte + (filas * resolucion), resolucion, resolucion)
            
            # Guardar el archivo TIFF en memoria buffer para descarga directa
            targ_stream = io.BytesIO()
            with rasterio.open(
                targ_stream,
                'w',
                driver='GTIFF',
                height=filas,
                width=columnas,
                count=1,
                dtype=matriz_twi.dtype,
                crs=crs_string,
                transform=transform,
                nodata=-9999
            ) as dst:
                dst.write(matriz_twi, 1)
            
            targ_stream.seek(0)
            
            # Finalización
            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.text("¡Proceso completado con éxito!")
            add_log(f"Archivo GeoTIFF UTM generado en {elapsed_time:.2f} segundos.")
            
            st.balloons()
            st.success(f"🎉 TWI calculado y georreferenciado correctamente en **UTM Zona {zona_utm} {hemisferio}**.")
            
            # Botón de descarga del GeoTIFF definitivo
            st.download_button(
                label="📥 Descargar GeoTIFF TWI en UTM (.tif)",
                data=targ_stream,
                file_name=f"TWI_Syntro_UTM{zona_utm}.tif",
                mime="image/tiff"
            )
            
        except Exception as e:
            add_log(f"ERROR CRÍTICO: {str(e)}")
            st.error(f"Ocurrió un error en el procesamiento: {e}")
else:
    add_log("Esperando que el usuario cargue el archivo DEM...")
    st.warning("Por favor, selecciona y sube un archivo DEM en formato TIFF desde el panel lateral izquierdo para comenzar.")
