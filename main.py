#main.py
import os
import streamlit as st
import base64
from dotenv import load_dotenv

# ─── CARGA DE VARIABLES DE ENTORNO ───────────────────────────────────────────
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()
DB_TYPE      = (os.environ.get("DB_TYPE") or "supabase").strip().lower()

# ─── CONFIGURACIÓN DE INTERFAZ (antes de cualquier st.*) ─────────────────────
st.set_page_config(page_title="RAV System", layout="wide", page_icon="🤖")

# ─── IMPORTACIONES DE MÓDULOS PROPIOS ────────────────────────────────────────
try:
    from utilidades import verify_password, hash_password, is_hashed, check_permiso
    from database import SQLiteClient, iniciar_hilo_sincronizacion, hay_internet_rapido
    from inventario import ModuloInventario
    from cotizaciones import ModuloCotizaciones
    from ventas import ModuloVentas
    from clientes import ModuloClientes
    from recibos import ModuloRecibos
    from contabilidad import ModuloContabilidad
    from configuracion import ModuloConfiguracion
except ImportError as e:
    st.error(f"❌ ERROR DE MÓDULOS: {e}")
    st.stop()

# ─── INICIALIZACIÓN DEL CLIENTE DE BASE DE DATOS ─────────────────────────────
if DB_TYPE == "sqlite":
    # Modo local / escritorio
    db = SQLiteClient("rav_system.db")
    ONLINE = False
else:
    # Modo online (Supabase) — verificar credenciales
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ ERROR CRÍTICO: Las credenciales de Supabase no están configuradas.")
        st.info("Ve a 'Environment' en Render y agrega SUPABASE_URL y SUPABASE_KEY.")
        st.stop()
    try:
        from supabase import create_client, Client
        from supabase_helper import SupabaseHelper
        raw_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        db = SupabaseHelper(raw_client)
        ONLINE = True
    except Exception as e:
        # Si Supabase falla, intentar fallback a SQLite local
        st.warning(f"⚠️ No se pudo conectar con Supabase. Iniciando en modo local. ({e})")
        db = SQLiteClient("rav_system.db")
        ONLINE = False

# ─── HILO DE SINCRONIZACIÓN (solo si hay SQLite + Supabase configurado) ──────
if DB_TYPE == "sqlite" and SUPABASE_URL and SUPABASE_KEY and not st.session_state.get("_sync_thread_started"):
    try:
        from supabase import create_client
        supa_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Validación de tipo estricta para resolver el error del analizador estático
        if isinstance(db, SQLiteClient):
            iniciar_hilo_sincronizacion(db, supa_client, SUPABASE_URL, intervalo_seg=60)
    except Exception:
        pass  # Sin internet o sin credenciales: modo puramente offline

# ─── FUNCIÓN PARA CONVERTIR IMAGEN A BASE64 ──────────────────────────────────
def get_image_base64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        return None
    except Exception:
        return None

# ─── INICIALIZACIÓN DE SESSION STATE ─────────────────────────────────────────
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'rol' not in st.session_state:
    st.session_state.rol = None

# ─── LÓGICA DE ACCESO (LOGIN) ─────────────────────────────────────────────────
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        logo_path = "ravsyst_icono.png"
        logo_b64 = get_image_base64(logo_path)

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
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 10px;">
                    <h1 style='color: #1a365d; font-weight: bold; margin: 0; padding: 0; font-size: 26pt;'>🤖 RAV System</h1>
                    <p style='color: #666; margin: 5px 0 20px 0; font-size: 13pt; font-style: italic;'>Gestión que impulsa tu éxito</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ── Formulario de Login ────────────────────────────────────────────
        with st.form("login_form"):
            usuario_input_raw = st.text_input("Usuario")
            clave_input_raw = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)

            if submit:
                try:
                    perfiles = db.fetch("perfiles")
                    usuario_clean = usuario_input_raw.strip().lower()
                    clave_clean = clave_input_raw.strip()

                    # Buscar el usuario en la lista de perfiles
                    user_encontrado = next(
                        (u for u in perfiles if str(u.get('usuario', '')).lower() == usuario_clean),
                        None
                    )

                    if user_encontrado:
                        clave_bd = str(user_encontrado.get('clave', ''))
                        acceso_ok = verify_password(clave_clean, clave_bd)

                        if acceso_ok:
                            # ── Auto-migración: si la clave está en texto plano, hashearla ──
                            if not is_hashed(clave_bd):
                                try:
                                    nuevo_hash = hash_password(clave_clean)
                                    db.client.table("perfiles").update(
                                        {"clave": nuevo_hash}
                                    ).eq("id", user_encontrado.get("id")).execute()
                                except Exception:
                                    pass  # Fallback: si no se puede hashear, el login sigue igual

                            st.session_state.autenticado = True
                            st.session_state.user_data = user_encontrado
                            st.session_state.rol = str(user_encontrado.get('rol', 'usuario')).lower().strip()

                            try:
                                db.client.table("logs_sistema").insert({
                                    "usuario": user_encontrado.get('usuario'),
                                    "accion": "Login",
                                    "modulo": "Acceso",
                                    "detalle": f"Usuario {user_encontrado.get('usuario')} ingresó al sistema"
                                }).execute()
                            except Exception:
                                pass

                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas. Verifique usuario y contraseña.")
                    else:
                        st.error("❌ Usuario no encontrado.")

                except Exception as e:
                    st.error(f"Error de acceso al validar credenciales: {e}")

        # ── Aviso legal ───────────────────────────────────────────────────
        st.markdown("""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background-color: #f8fafc;
                    text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-top: 15px; margin-bottom: 20px;">
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
        """, unsafe_allow_html=True)

# ─── INTERFAZ PRINCIPAL (POST-LOGIN) ─────────────────────────────────────────
else:
    rol_actual = st.session_state.rol or "usuario"

    with st.sidebar:
        st.markdown("<h2 style='color: #707070; font-weight: bold;'> Dana Internacional </h2>", unsafe_allow_html=True)
        
        # Protección contra errores de tipo 'NoneType' en la UI
        usuario_actual = st.session_state.user_data.get('usuario', 'N/A') if st.session_state.user_data else 'N/A'
        st.write(f"Usuario: **{usuario_actual}**")
        st.write(f"Perfil: `{rol_actual}`")

        # ── Estado de conexión ────────────────────────────────────────────
        if DB_TYPE == "sqlite":
            online = hay_internet_rapido(SUPABASE_URL) if SUPABASE_URL else False
            if online:
                st.success("🟢 Sincronizado con la nube")
            else:
                st.warning("📁 Modo Local / Offline")
        else:
            st.success("🌐 Online (Supabase)")

        st.divider()

        # ── Menú según rol ──
        opciones = ["📦 Inventario", "📄 Cotizaciones", "🛒 Ventas", "👥 Clientes", "💵 Caja"]

        if rol_actual in ["contador", "administrador", "master_it"]:
            opciones.append("💰 Contabilidad")

        if rol_actual in ["master_it"]:
            opciones.append("⚙️ Configuración")

        choice = st.radio("Menú Principal", opciones)

        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            try:
                db.client.table("logs_sistema").insert({
                    "usuario": usuario_actual,
                    "accion": "Logout",
                    "modulo": "Acceso",
                    "detalle": "Sesión cerrada por el usuario"
                }).execute()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

    # ── Enrutador de módulos ───────────────────────────────────────────────
    try:
        if choice == "📦 Inventario":
            ModuloInventario(db).render()
        elif choice == "📄 Cotizaciones":
            ModuloCotizaciones(db).render()
        elif choice == "🛒 Ventas":
            ModuloVentas(db).render()
        elif choice == "👥 Clientes":
            ModuloClientes(db).render()
        elif choice == "💵 Caja":
            ModuloRecibos(db).render()
        elif choice == "💰 Contabilidad":
            if check_permiso("contabilidad", "ver"):
                ModuloContabilidad(db).render()
            else:
                st.error("🚫 Acceso denegado. No tienes permiso para acceder a Contabilidad.")
        elif choice == "⚙️ Configuración":
            ModuloConfiguracion(db).render()
    except Exception as e:
        st.error(f"Error al cargar el módulo '{choice}': {e}")
        st.info("Contacte al soporte técnico de CIR Panamá.")