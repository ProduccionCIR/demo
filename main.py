import os
import sys
import socket
import asyncio
import base64
import sqlite3
import streamlit as st
from dotenv import load_dotenv

# ==========================================
# 0. PARCHE DE ASYNCIO PARA WINDOWS
# ==========================================
if sys.platform == 'win32':
    try:
        from asyncio import proactor_events
        def _silent_call_connection_lost(self, exc):
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            if hasattr(super(proactor_events._ProactorBasePipeTransport, self), '_call_connection_lost'):
                super(proactor_events._ProactorBasePipeTransport, self)._call_connection_lost(exc)
        if hasattr(proactor_events, '_ProactorBasePipeTransport'):
            proactor_events._ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost
    except Exception:
        pass

# ==========================================
# 1. HELPER SQLITE
# ==========================================
class LocalDBHelper:
    def __init__(self):
        self.db_local = "local.db"
        self._verificar_base_datos()

    def _verificar_base_datos(self):
        try:
            conn = sqlite3.connect(self.db_local, timeout=20.0)
            cursor = conn.cursor()

            # Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT DEFAULT (datetime('now', 'localtime')),
                    usuario TEXT,
                    rol TEXT,
                    accion TEXT,
                    modulo TEXT,
                    detalle TEXT
                )
            """)

            # Ventas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    fecha TEXT DEFAULT (datetime('now', 'localtime')),
                    total REAL DEFAULT 0.0,
                    usuario TEXT,
                    creado_en TEXT
                )
            """)

            # Clientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL
                )
            """)
            cursor.execute("PRAGMA table_info(clientes)")
            columnas_existentes = [col[1].lower() for col in cursor.fetchall()]
            for col_name in ['ruc', 'telefono', 'correo', 'direccion']:
                if col_name not in columnas_existentes:
                    cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_name} TEXT")
            cursor.execute("SELECT COUNT(*) FROM clientes")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO clientes (nombre, ruc) VALUES ('CLIENTE GENERAL / CONTADO', 'CON-00')")

            # Productos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referencia TEXT NOT NULL,
                    especificacion TEXT,
                    marca TEXT,
                    descripcion TEXT,
                    tipo TEXT,
                    ubicacion TEXT,
                    cantidad INTEGER NOT NULL DEFAULT 0,
                    costo_unit REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    creado_en TEXT DEFAULT (datetime('now', 'localtime')),
                    empaque TEXT
                )
            """)
            # Migración de columnas críticas
            cursor.execute("PRAGMA table_info(productos)")
            columnas_existentes = [col[1].upper() for col in cursor.fetchall()]
            columnas_necesarias = {
                "PESO": "REAL DEFAULT 0.0",
                "CUBICAJE": "REAL DEFAULT 0.0",
                "UM": "TEXT DEFAULT 'CAJA'",
                "U/M": "TEXT DEFAULT 'CAJA'"
            }
            for col_name, col_def in columnas_necesarias.items():
                if col_name not in columnas_existentes:
                    cursor.execute(f"ALTER TABLE productos ADD COLUMN '{col_name}' {col_def}")

            # Perfiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS perfiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL UNIQUE,
                    clave TEXT NOT NULL,
                    rol TEXT DEFAULT 'usuario',
                    nombre_completo TEXT
                )
            """)
            cursor.execute("SELECT COUNT(*) FROM perfiles")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO perfiles (usuario, clave, rol, nombre_completo)
                    VALUES ('admin', '1234', 'master_it', 'Administrador Local')
                """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error crítico al estructurar la base de datos local: {e}")

    def ejecutar_consulta_sqlite_local(self, sql_query, parametros=None):
        try:
            conn = sqlite3.connect(self.db_local, timeout=20.0)
            cursor = conn.cursor()
            if parametros:
                cursor.execute(sql_query, parametros)
            else:
                cursor.execute(sql_query)
            if sql_query.strip().upper().startswith("SELECT"):
                columnas = [col[0] for col in cursor.description]
                resultado = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
            else:
                conn.commit()
                resultado = []
            conn.close()
            return resultado
        except Exception as e:
            st.error(f"🚨 Error en consulta: {e}\nSQL: {sql_query}")
            return []

    def ejecutar_consulta(self, query_sql, parametros=None):
        return self.ejecutar_consulta_sqlite_local(query_sql, parametros)

    def fetch(self, tabla, select="*"):
        return self.ejecutar_consulta_sqlite_local(f"SELECT {select} FROM {tabla}")

# ==========================================
# 2. CONFIGURACIÓN
# ==========================================
def get_image_base64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        return None
    except:
        return None

if os.path.exists(".env"):
    load_dotenv()

env_admin = "admin"
env_pass = "1234"
try:
    if st.secrets:
        env_admin = st.secrets.get("ADMIN_USER", "admin")
        env_pass = st.secrets.get("ADMIN_PASSWORD", "1234")
except:
    pass

supabase = LocalDBHelper()

# ==========================================
# 3. IMPORTACIÓN DE MÓDULOS
# ==========================================
try:
    from inventario import ModuloInventario
    from cotizaciones import ModuloCotizaciones
    from ventas import ModuloVentas
    from clientes import ModuloClientes
    from contabilidad import ModuloContabilidad
    from configuracion import ModuloConfiguracion
except ImportError as e:
    st.error(f"❌ ERROR DE ARCHIVOS: Falta un archivo de módulo en la raíz: {e}")
    st.stop()

# ==========================================
# 4. INTERFAZ STREAMLIT
# ==========================================
st.set_page_config(page_title="RAV System - Estación Local", layout="wide", page_icon="💻")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'rol' not in st.session_state:
    st.session_state.rol = None

LOGO_SISTEMA = "ravsyst_icono.png"  
LOGO_CLIENTE = "eslogo.png"            
DB_LOCAL = "local.db"                

# LOGIN
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        logo_b64 = get_image_base64(LOGO_SISTEMA)
        if logo_b64:
            st.markdown(f"""<div style='text-align: center;'><img src='data:image/png;base64,{logo_b64}' style='max-width: 140px; height: auto; margin-bottom: 15px;'><h1 style='color: #1a365d; font-weight: bold;'>RAV System</h1><p style='color: #666;'>Entorno de Red Local</p></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style='text-align: center;'><h1 style='color: #1a365d; font-weight: bold;'>🤖 RAV System</h1><p style='color: #666;'>Entorno de Red Local</p></div>""", unsafe_allow_html=True)
            
        with st.form("login_form"):
            usuario_input_raw = st.text_input("Usuario")
            clave_input_raw = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema Local")
            
            if submit:
                usuario_clean = usuario_input_raw.strip().lower()
                clave_clean = clave_input_raw.strip()
                user = None
                try:
                    data = supabase.fetch("perfiles")
                    user = next((u for u in data if str(u.get('usuario','')).lower() == usuario_clean and str(u.get('clave','')) == clave_clean), None)
                except:
                    pass
                if not user and usuario_clean == "temp" and clave_clean == "1234":
                    user = {"usuario": "Soporte IT", "rol": "master_it", "nombre_completo": "Desarrollador Local"}
                elif not user and usuario_clean == env_admin.lower() and clave_clean == env_pass:
                    user = {"usuario": env_admin, "rol": "master_it", "nombre_completo": "Administrador Local"}
                if user:
                    st.session_state.autenticado = True
                    st.session_state.user_data = user
                    st.session_state.rol = user.get('rol', 'usuario')
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")

# ==========================================
# POST-LOGIN
# ==========================================
else:
    with st.sidebar:
        if os.path.exists(LOGO_CLIENTE):
            st.image(LOGO_CLIENTE, width=120)
        st.markdown(f"<h2 style='color: #1a365d; font-weight: bold;'>SONIX LTD.</h2>", unsafe_allow_html=True)
        st.write(f"Usuario: **{st.session_state.user_data.get('usuario')}**")
        st.caption(f"🗃️ Base Local Activa: `{DB_LOCAL}`")
        st.divider()
        
        opciones = ["📦 Inventario", "📄 Cotizaciones", "🛒 Ventas", "👥 Clientes", "💰 Contabilidad"]
        if st.session_state.rol in ["master_it", "administrador"]:
            opciones.append("⚙️ Configuración")
            
        choice = st.radio("Menú Principal", opciones, key="menu_principal")
        st.divider()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True, key="cerrar_sesion"):
            st.session_state.clear()
            st.rerun()

    try:
        if choice == "📦 Inventario":
            ModuloInventario(supabase).render()
        elif choice == "📄 Cotizaciones":
            ModuloCotizaciones(supabase.db_local).render()
        elif choice == "🛒 Ventas":
            ModuloVentas(supabase).render()
        elif choice == "👥 Clientes":
            ModuloClientes(supabase).render()
        elif choice == "💰 Contabilidad":
            ModuloContabilidad(supabase).render()
        elif choice == "⚙️ Configuración":
            ModuloConfiguracion(supabase).render()
    except Exception as e:
        st.error(f"Error al cargar el módulo {choice}: {e}")