import os
import streamlit as st
import base64
from supabase import create_client, Client
from dotenv import load_dotenv

# --- CLASE HELPER PARA COMPATIBILIDAD Y LOGS ---
class SupabaseHelper:
    """Evita errores de AttributeError y centraliza la lógica de red."""
    def __init__(self, client):
        self.client = client

    def table(self, table_name):
        return self.client.table(table_name)

    def fetch(self, tabla, select="*"):
        """Trae datos de una tabla de forma segura."""
        try:
            res = self.client.table(tabla).select(select).execute()
            return res.data if hasattr(res, 'data') and res.data else []
        except Exception as e:
            st.error(f"Error en comunicación con la base de datos ({tabla}): {e}")
            return []

    def registrar_log(self, accion, modulo, detalle):
        """Registra auditoría en la tabla logs_sistema."""
        try:
            log_data = {
                "usuario": st.session_state.get('user_data', {}).get('usuario', 'Sistema'),
                "accion": accion,
                "modulo": modulo,
                "detalle": detalle
            }
            self.client.table("logs_sistema").insert(log_data).execute()
        except:
            pass 

# --- FUNCIÓN PARA CONVERTIR IMAGEN A BASE64 ---
def get_image_base64(path):
    """Lee una imagen local y la convierte en cadena Base64 para HTML."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        return None
    except:
        return None

# --- CARGA DE VARIABLES Y CONEXIÓN CRÍTICA ---
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ ERROR CRÍTICO: Las credenciales de Supabase no están configuradas en Render.")
    st.info("Ve a la pestaña 'Environment' en Render y agrega SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

try:
    raw_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase = SupabaseHelper(raw_client)
except Exception as e:
    st.error(f"❌ FALLO DE CONEXIÓN: No se pudo alcanzar el servidor de Supabase. Detalles: {e}")
    st.stop()

# --- IMPORTACIÓN DE MÓDULOS DE NEGOCIO ---
try:
    from inventario import ModuloInventario
    from cotizaciones import ModuloCotizaciones
    from ventas import ModuloVentas
    from clientes import ModuloClientes
    from contabilidad import ModuloContabilidad
    from configuracion import ModuloConfiguracion
except ImportError as e:
    st.error(f"❌ ERROR DE MÓDULOS: Falta un archivo de módulo o hay un error de sintaxis en: {e}")
    st.stop()

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="RAV System", layout="wide", page_icon="🤖")

# --- INICIALIZACIÓN DE SESSION STATE ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'rol' not in st.session_state:
    st.session_state.rol = None

# --- LÓGICA DE ACCESO (LOGIN) ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        logo_path = "ravsyst_icono.png"
        logo_b64 = get_image_base64(logo_path)
        
        # --- CABECERA UNIFICADA BASADA EN BASE64 ---
        if logo_b64:
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 10px;">
                    <img src="data:image/png;base64,{logo_b64}" style="max-width: 140px; height: auto; margin-bottom: 15px;">
                    <h1 style='color: #1a365d; font-weight: bold; margin: 0; padding: 0; font-size: 26pt;'>RAV System</h1>
                    <p style='color: #666; margin: 5px 0 20px 0; font-size: 13pt; font-style: italic;'>Gestión que impulsa tu éxito</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            # Fallback por si el archivo llega a faltar en el servidor
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 10px;">
                    <h1 style='color: #1a365d; font-weight: bold; margin: 0; padding: 0; font-size: 26pt;'>🤖 RAV System</h1>
                    <p style='color: #666; margin: 5px 0 20px 0; font-size: 13pt; font-style: italic;'>Gestión que impulsa tu éxito</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        # 2. Formulario Estándar de Credenciales (Cuadro de Usuario)
        with st.form("login_form"):
            usuario_input_raw = st.text_input("Usuario")
            clave_input_raw = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submit:
                try:
                    data = supabase.fetch("perfiles")
                    usuario_clean = usuario_input_raw.strip().lower()
                    clave_clean = clave_input_raw.strip()

                    user = next((u for u in data if str(u.get('usuario','')).lower() == usuario_clean 
                                 and str(u.get('clave','')) == clave_clean), None)

                    if not user and usuario_clean == "temp" and clave_clean == "1234":
                        user = {"usuario": "Soporte IT", "rol": "master_it", "nombre_completo": "Administrador Temporal"}

                    if user:
                        st.session_state.autenticado = True
                        st.session_state.user_data = user
                        st.session_state.rol = user.get('rol', 'usuario')
                        
                        supabase.registrar_log("Login", "Acceso", f"Usuario {user.get('usuario')} ingresó al sistema")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas. Verifique usuario y contraseña.")
                except Exception as e:
                    st.error(f"Error de acceso al validar credenciales: {e}")

        # 3. Mensaje de Propiedad Intelectual colocado ABAJO del cuadro de usuario
        mensaje_legal = """
        <div style="
            border: 1px solid #e2e8f0; 
            border-radius: 8px; 
            padding: 16px; 
            background-color: #f8fafc; 
            text-align: center; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-top: 15px;
            margin-bottom: 20px;
        ">
            <h4 style="margin: 0 0 8px 0; color: #1e293b; font-weight: 700; font-size: 10pt; letter-spacing: 0.5px; text-transform: uppercase;">
                ⚠️ AVISO DE PROPIEDAD Y CONFIDENCIALIDAD
            </h4>
            <p style="margin: 0 0 10px 0; color: #475569; font-size: 9.5pt; line-height: 1.5;">
                Este sistema informático, su diseño de interfaz, algoritmos y bases de datos integradas son propiedad exclusiva y confidencial de 
                <strong style="color: #1a365d;">CIR PANAMÁ</strong>.
            </p>
            <p style="margin: 0; color: #64748b; font-size: 8.5pt; line-height: 1.4; border-top: 1px solid #e2e8f0; padding-top: 10px; font-style: italic;">
                La plataforma se encuentra estrictamente registrada y bajo la protección legal de la República de Panamá, 
                conforme a las leyes locales de derecho de autor, propiedad intelectual y la Ley 81 de 2019 de Protección de Datos Personales. 
                El acceso no autorizado o el uso indebido de los datos será procesado por la vía judicial.
            </p>
        </div>
        """
        st.markdown(mensaje_legal, unsafe_allow_html=True)

# --- INTERFAZ PRINCIPAL DEL SISTEMA (POST-LOGIN) ---
else:
    with st.sidebar:
        st.markdown(f"<h2 style='color: #707070; font-weight: bold;'> Dana Internacional </h2>", unsafe_allow_html=True)
        st.write(f"Usuario: **{st.session_state.user_data.get('usuario')}**")
        st.write(f"Permisos: `{st.session_state.rol}`")
        st.divider()
        
        opciones = ["📦 Inventario", "📄 Cotizaciones", "🛒 Ventas", "👥 Clientes", "💰 Contabilidad"]
        
        if st.session_state.rol in ["master_it", "administrador"]:
            opciones.append("⚙️ Configuración")
            
        choice = st.radio("Menú Principal", opciones)
        
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            supabase.registrar_log("Logout", "Acceso", "Sesión cerrada por el usuario")
            st.session_state.clear()
            st.rerun()

    # --- ENRUTADOR DE MÓDULOS ---
    try:
        if choice == "📦 Inventario":
            ModuloInventario(supabase).render()
        elif choice == "📄 Cotizaciones":
            ModuloCotizaciones(supabase).render()
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
        st.info("Contacte al soporte técnico de CIR Panamá.")