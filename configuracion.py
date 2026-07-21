import streamlit as st
import pandas as pd
import hashlib
from io import BytesIO
from datetime import datetime

class ModuloConfiguracion:
    def __init__(self, db):
        """
        Inicializa el módulo de configuración de RAV System.
        :param db: Instancia segura de SQLiteHelper/SupabaseHelper compartida desde main.py
        """
        self.db = db 
        self.tabla_perfiles = "perfiles"
        self.tabla_inventario = "productos"
        self.tabla_logs = "logs_sistema" 
        self.roles_disponibles = ["usuario", "supervisor", "administrador", "master_it"]
        self._inicializar_tabla_config()

    def _inicializar_tabla_config(self):
        """Crea la tabla de configuración local si no existe para hacer el sistema multipropósito."""
        try:
            query_tabla = """
                CREATE TABLE IF NOT EXISTS config_empresa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT UNIQUE,
                    valor TEXT,
                    actualizado_en TEXT
                )
            """
            self.db.ejecutar_consulta(query_tabla)
            
            query_init = "INSERT OR IGNORE INTO config_empresa (clave, valor, actualizado_en) VALUES (?, ?, ?)"
            self.db.ejecutar_consulta(query_init, ("nombre_comercial", "SONIX LTD.", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            print(f"Error al inicializar tabla config: {e}")

    def obtener_nombre_empresa(self):
        """Retorna el nombre de la empresa configurado de forma segura usando la interfaz unificada."""
        try:
            query = "SELECT valor FROM config_empresa WHERE clave = 'nombre_comercial'"
            row = self.db.ejecutar_consulta(query)
            if row and len(row) > 0:
                valor = row[0].get('valor') if isinstance(row[0], dict) else row[0][0]
                return str(valor).upper()
        except Exception as e:
            print(f"Error al obtener nombre de empresa: {e}")
        return "SONIX LTD."

    def registrar_log(self, accion, modulo, detalle):
        """Registra la actividad utilizando el helper centralizado."""
        try:
            self.db.registrar_log(accion, modulo, detalle)
        except Exception as e:
            print(f"Error al direccionar log: {e}")

    def _hashear_password(self, password_plana):
        """Genera un hash SHA-256 consistente con el inicio de sesión."""
        return hashlib.sha256(password_plana.encode('utf-8')).hexdigest()

    def render(self):
        # SEGURIDAD: Permite acceso estricto a Master IT y Administrador
        user_info = st.session_state.get('user_data')
        if not user_info or user_info.get('rol') not in ["master_it", "administrador"]:
            st.error("🚫 Acceso Denegado. Se requiere perfil autorizado para realizar cambios de sistema.")
            return

        st.markdown("<h2 style='color: #1a365d; font-weight: bold;'>⚙️ Panel de Control del Sistema</h2>", unsafe_allow_html=True)
        
        tab_usuarios, tab_importacion, tab_logs, tab_sistema, tab_migracion = st.tabs([
            "👥 Usuarios", 
            "📊 Carga Masiva Local", 
            "📜 Auditoría Global", 
            "🛡️ Sistema",
            "🔄 Migración Inicial Supabase"
        ])

        # --- PESTAÑA 1: GESTIÓN DE USUARIOS LOCALES BLINDADA ---
        with tab_usuarios:
            col_form, col_lista = st.columns([1, 1.3])

            with col_form:
                if "edit_user" not in st.session_state:
                    st.session_state.edit_user = None

                modo_edicion = st.session_state.edit_user is not None
                titulo_form = "📝 Editar Usuario" if modo_edicion else "➕ Crear Nuevo Acceso"
                
                with st.form("f_usuario", clear_on_submit=not modo_edicion):
                    st.subheader(titulo_form)
                    def_val = st.session_state.edit_user if modo_edicion else {}
                    
                    u = st.text_input("Usuario (Login)", value=def_val.get('usuario', ''), disabled=modo_edicion).lower().strip()
                    p = st.text_input("Contraseña", type="password", help="Dejar en blanco para conservar la contraseña actual si está editando")
                    n = st.text_input("Nombre Completo", value=def_val.get('nombre_completo', def_val.get('nombre', '')))
                    rol_idx = self.roles_disponibles.index(def_val.get('rol')) if def_val.get('rol') in self.roles_disponibles else 0
                    r = st.selectbox("Rol del Sistema", self.roles_disponibles, index=rol_idx)
                    
                    btn_label = "Actualizar Usuario" if modo_edicion else "Registrar Usuario"
                    submit = st.form_submit_button(btn_label, use_container_width=True)
                    
                    if submit:
                        if u and n:
                            try:
                                if modo_edicion:
                                    if p.strip():
                                        p_hash = self._hashear_password(p.strip())
                                        query_upd = "UPDATE perfiles SET nombre_completo=?, rol=?, clave=? WHERE id=?"
                                        params_upd = (n, r, p_hash, def_val['id'])
                                    else:
                                        query_upd = "UPDATE perfiles SET nombre_completo=?, rol=? WHERE id=?"
                                        params_upd = (n, r, def_val['id'])
                                    
                                    self.db.ejecutar_consulta(query_upd, params_upd)
                                    self.registrar_log("MODIFICACION", "USUARIOS", f"Editado local: {u}")
                                    st.success("Usuario actualizado correctamente.")
                                    st.session_state.edit_user = None
                                else:
                                    if not p.strip(): 
                                        st.error("La contraseña es obligatoria para nuevos usuarios.")
                                    else:
                                        p_hash = self._hashear_password(p.strip())
                                        query_ins = "INSERT INTO perfiles (usuario, clave, nombre_completo, rol) VALUES (?, ?, ?, ?)"
                                        params_ins = (u, p_hash, n, r)
                                        
                                        self.db.ejecutar_consulta(query_ins, params_ins)
                                        self.registrar_log("CREACIÓN", "USUARIOS", f"Creado local: {u}")
                                        st.success("Usuario registrado con éxito en la base local.")
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al procesar la solicitud en la base local: {e}")
                        else:
                            st.error("Por favor completa los campos obligatorios (Usuario y Nombre Completo).")

                if modo_edicion:
                    if st.button("❌ Cancelar Edición", use_container_width=True):
                        st.session_state.edit_user = None
                        st.rerun()

            with col_lista:
                st.subheader("Usuarios Registrados")
                try:
                    usuarios_db = self.db.fetch(self.tabla_perfiles)
                    if usuarios_db:
                        for user in usuarios_db:
                            with st.container(border=True):
                                c_info, c_edit, c_del = st.columns([3, 0.5, 0.5])
                                nombre_u = user.get('nombre_completo') or user.get('nombre', 'Sin nombre')
                                c_info.write(f"👤 **{nombre_u}**\n`{user.get('rol')}` | @{user.get('usuario')}")
                                
                                if c_edit.button("📝", key=f"edit_{user.get('id')}", help="Editar usuario"):
                                    st.session_state.edit_user = user
                                    st.rerun()
                                    
                                if c_del.button("🗑️", key=f"del_{user.get('id')}", help="Eliminar usuario"):
                                    query_del = "DELETE FROM perfiles WHERE id=?"
                                    self.db.ejecutar_consulta(query_del, (user.get('id'),))
                                    self.registrar_log("ELIMINACIÓN", "USUARIOS", f"Eliminado de base local: {user.get('usuario')}")
                                    st.rerun()
                    else:
                        st.info("No hay usuarios registrados localmente.")
                except Exception as e:
                    st.error(f"Error al cargar usuarios: {e}")

        # --- PESTAÑA 2: CARGA MASIVA LOCAL (OPTIMIZADA) ---
        with tab_importacion:
            st.subheader("Carga Masiva de Datos Automatizada (SQLite Local)")
            lista_tablas = ["productos", "clientes", "perfiles", "ventas", "cotizaciones"]
            
            tabla_seleccionada = st.selectbox("Seleccione la tabla destino para la importación", lista_tablas)
            file = st.file_uploader(f"Subir archivo Excel para la tabla '{tabla_seleccionada}' (.xlsx)", type=["xlsx"])
            
            if file:
                try:
                    df_load = pd.read_excel(file)
                    # Normalización estricta de nombres de columnas a minúsculas
                    df_load.columns = [str(c).strip().lower() for c in df_load.columns]
                    df_load = df_load.astype(object).where(pd.notnull(df_load), None)
                    
                    if tabla_seleccionada == "productos" and "cantidad" in df_load.columns:
                        df_load["cantidad"] = df_load["cantidad"].apply(
                            lambda x: int(float(x)) if x is not None and str(x).strip() != "" else 0
                        )
                    
                    # MODIFICACIÓN: Mostrar la data COMPLETA cargada en memoria sin truncar a 5 filas
                    st.write(f"📋 **Vista previa de TODOS los datos a procesar ({len(df_load)} registros detectados):**")
                    st.dataframe(df_load, use_container_width=True)

                    if st.button(f"🚀 Ejecutar Carga Masiva Local en {tabla_seleccionada.upper()}", type="primary"):
                        try:
                            if tabla_seleccionada == "perfiles" and "clave" in df_load.columns:
                                df_load["clave"] = df_load["clave"].apply(lambda x: self._hashear_password(str(x)) if x else None)

                            # Modificado para trabajar de la mano con la API simulada de Supabase en main.py
                            registros_insertados = 0
                            for _, fila in df_load.iterrows():
                                datos_fila = fila.dropna().to_dict()
                                # Conmutación de columnas para respetar mayúsculas de llaves primarias en productos si fuese necesario
                                if tabla_seleccionada == "productos" and "referencia" in datos_fila:
                                    datos_fila["REFERENCIA"] = datos_fila.pop("referencia")
                                    
                                self.db.table(tabla_seleccionada).insert(datos_fila)
                                registros_insertados += 1

                            self.registrar_log("IMPORTACIÓN MASIVA", tabla_seleccionada, f"Carga masiva local de {registros_insertados} registros.")
                            st.success(f"¡Carga completada localmente! {registros_insertados} filas añadidas de forma segura en `{tabla_seleccionada}`.")
                            st.balloons()
                        except Exception as sql_err:
                            st.error(f"❌ Error de tipos o inserción en la base de datos local: {sql_err}")
                except Exception as e:
                    st.error(f"Error al interpretar archivo Excel: {e}")

        # --- PESTAÑA 3: AUDITORÍA GLOBAL LOCAL ---
        with tab_logs:
            st.subheader("📜 Historial de Auditoría Local")
            try:
                logs_db = self.db.fetch(self.tabla_logs)
                if logs_db:
                    df_logs = pd.DataFrame(logs_db)
                    if "id" in df_logs.columns:
                        df_logs = df_logs.sort_values(by="id", ascending=False)
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                else:
                    st.info("El historial de auditoría local se encuentra vacío.")
            except Exception as e:
                st.warning(f"Error al conectar con la bitácora de logs local: {e}")

        # --- PESTAÑA 4: SISTEMA Y MANTENIMIENTO ---
        with tab_sistema:
            st.subheader("🏢 Identidad de la Empresa actual")
            
            nombre_actual = self.obtener_nombre_empresa()
            with st.form("form_identidad_empresa"):
                nuevo_nombre = st.text_input("Nombre Comercial de la Empresa (Para Facturas/Cotizaciones):", value=nombre_actual).upper().strip()
                btn_guardar_identidad = st.form_submit_button("💾 Guardar Configuración de Empresa", use_container_width=True)
                
                if btn_guardar_identidad:
                    if nuevo_nombre:
                        try:
                            query_upsert = """
                                INSERT INTO config_empresa (clave, valor, actualizado_en)
                                VALUES ('nombre_comercial', ?, datetime('now', 'localtime'))
                                ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor, actualizado_en=excluded.actualizado_en
                            """
                            self.db.ejecutar_consulta(query_upsert, (nuevo_nombre,))
                            st.session_state['nombre_empresa'] = nuevo_nombre
                            self.registrar_log("MANTENIMIENTO", "CONFIG", f"Cambio de nombre comercial a: {nuevo_nombre}")
                            st.success(f"¡Configuración guardada exitosamente! Identidad del sistema: **{nuevo_nombre}**")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar la identidad local: {e}")
                    else:
                        st.error("El nombre de la empresa no puede estar vacío.")

            st.divider()
            st.subheader("Acciones de Respaldo y Mantenimiento Local")
            
            if st.button("💾 Generar Copia de Seguridad Completa (Inventario SQLite Actual)"):
                try:
                    data_inv = self.db.fetch(self.tabla_inventario)
                    if data_inv:
                        df_exp = pd.DataFrame(data_inv)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_exp.to_excel(writer, sheet_name='INVENTARIO_LOCAL', index=False)
                        st.download_button("📥 Descargar Archivo .xlsx", output.getvalue(), "respaldo_local_inventario.xlsx", use_container_width=True)
                    else:
                        st.warning("La tabla de inventario está vacía localmente.")
                except Exception as e:
                    st.error(f"Error al compilar respaldo: {e}")

            st.divider()
            st.error("Zona de Peligro Local")
            
            if st.button("🗑️ Vaciar Por Completo Tabla de Inventario Local"):
                try:
                    query_trunc = "DELETE FROM productos"
                    self.db.ejecutar_consulta(query_trunc)
                    self.registrar_log("MANTENIMIENTO", "DB", "Vaciado total preventivo de productos en SQLite.")
                    st.success("Se ha ejecutado el vaciado de la tabla de inventario local de forma segura.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo purgar la tabla local: {e}")

        # --- PESTAÑA 5: MIGRACIÓN INICIAL SUPABASE ---
        with tab_migracion:
            st.subheader("🔄 Puente de Sincronización Inicial (Clonador Cloud)")
            st.info("""
                Utiliza esta herramienta la primera vez que montes el sistema RAV System en esta computadora. 
                Se conectará de forma segura a Supabase mediante llamadas directas, leerá la estructura de los campos 
                y descargará los registros directo a tu archivo local de base de datos (`local.db`).
            """)
            
            with st.form("form_clonador_cloud"):
                url_input = st.text_input("Supabase URL:", placeholder="https://xxxxxxxxx.supabase.co")
                key_input = st.text_input("Supabase ANON/SERVICE KEY:", type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6...")
                
                boton_clonar = st.form_submit_button("🚀 Iniciar Clonación Masiva de Datos", use_container_width=True)
                
                if boton_clonar:
                    if not url_input.strip() or not key_input.strip():
                        st.error("❌ Por favor, ingrese tanto la URL como la KEY de su panel de Supabase.")
                    else:
                        with st.spinner("Estableciendo comunicación híbrida segura..."):
                            try:
                                exito = self.db.clonar_desde_supabase(url_input.strip(), key_input.strip())
                                if exito:
                                    self.registrar_log("MIGRACION", "SISTEMA", "Clonación completa de base de datos desde Supabase.")
                                    st.success("✨ ¡Clonación Exitosa! Toda la estructura y datos de Supabase han sido replicados localmente.")
                                    st.balloons()
                                    st.info("ℹ️ Ya puedes cerrar sesión e iniciar sesión con las cuentas del equipo descargadas.")
                                else:
                                    st.error("❌ La sincronización no devolvió un estado exitoso. Verifique las credenciales de red.")
                            except Exception as e:
                                st.error(f"❌ Error durante el puente de migración cloud: {e}")