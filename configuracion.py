import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

class ModuloConfiguracion:
    def __init__(self, db):
        # DETECCIÓN DE INTERFAZ: Si es el Helper personalizado, extraemos el cliente nativo de Supabase
        if hasattr(db, 'client'):
            self.supabase_nativo = db.client
        else:
            self.supabase_nativo = db
            
        self.db = db 
        self.tabla_perfiles = "perfiles"
        self.tabla_inventario = "productos"
        self.tabla_logs = "logs_sistema" 
        self.roles_disponibles = ["usuario", "supervisor", "administrador", "master_it"]

    def registrar_log(self, accion, modulo, detalle):
        """Registra la actividad del usuario en la tabla de auditoría"""
        try:
            session_data = st.session_state.get('user_data', {})
            log_data = {
                "usuario": session_data.get('usuario', 'Sistema'),
                "accion": str(accion).upper(),
                "modulo": str(modulo).upper(),
                "detalle": str(detalle)
            }
            # Usamos el cliente nativo para asegurar la compatibilidad de métodos encadenados
            self.supabase_nativo.table(self.tabla_logs).insert(log_data).execute()
        except Exception as e:
            print(f"Error al registrar log: {e}")

    def render(self):
        # SEGURIDAD: Solo Master IT puede acceder a esta configuración
        user_info = st.session_state.get('user_data')
        if not user_info or user_info.get('rol') != "master_it":
            st.error("🚫 Acceso Denegado. Se requiere perfil Master IT para realizar cambios de sistema.")
            return

        st.markdown("<h2 style='color: #4A4A4A;'>⚙️ Panel de Control Master IT</h2>", unsafe_allow_html=True)
        
        tab_usuarios, tab_importacion, tab_logs, tab_sistema = st.tabs([
            "👥 Usuarios", 
            "📊 Carga Masiva Multi-Tabla", 
            "📜 Auditoría Global", 
            "🛡️ Sistema"
        ])

        # --- PESTAÑA 1: GESTIÓN DE USUARIOS (CREAR, MODIFICAR, ELIMINAR) ---
        with tab_usuarios:
            col_form, col_lista = st.columns([1, 1.3])

            with col_form:
                if "edit_user" not in st.session_state:
                    st.session_state.edit_user = None

                modo_edicion = st.session_state.edit_user is not None
                titulo_form = "📝 Editar Usuario" if modo_edicion else "➕ Crear Nuevo Acceso"
                
                with st.form("f_usuario"):
                    st.subheader(titulo_form)
                    def_val = st.session_state.edit_user if modo_edicion else {}
                    
                    u = st.text_input("Usuario (Login)", value=def_val.get('usuario', ''), disabled=modo_edicion).lower().strip()
                    p = st.text_input("Contraseña", type="password", help="Dejar en blanco para conservar la contraseña actual si está editando")
                    n = st.text_input("Nombre Completo", value=def_val.get('nombre_completo', ''))
                    car = st.text_input("Cargo", value=def_val.get('cargo', ''))
                    rol_idx = self.roles_disponibles.index(def_val.get('rol')) if def_val.get('rol') in self.roles_disponibles else 0
                    r = st.selectbox("Rol del Sistema", self.roles_disponibles, index=rol_idx)
                    
                    btn_label = "Actualizar Usuario" if modo_edicion else "Registrar Usuario"
                    submit = st.form_submit_button(btn_label, use_container_width=True)
                    
                    if modo_edicion:
                        if st.form_submit_button("❌ Cancelar Edición", use_container_width=True):
                            st.session_state.edit_user = None
                            st.rerun()

                    if submit:
                        if u and n:
                            try:
                                datos = {
                                    "usuario": u, 
                                    "nombre_completo": n, 
                                    "cargo": car, 
                                    "rol": r
                                }
                                if p: 
                                    datos["clave"] = p

                                if modo_edicion:
                                    self.supabase_nativo.table(self.tabla_perfiles).update(datos).eq("id", def_val['id']).execute()
                                    self.registrar_log("MODIFICACION", "USUARIOS", f"Editado: {u}")
                                    st.success("Usuario actualizado correctamente.")
                                    st.session_state.edit_user = None
                                else:
                                    if not p: 
                                        st.error("La contraseña es obligatoria para nuevos usuarios.")
                                    else:
                                        self.supabase_nativo.table(self.tabla_perfiles).insert(datos).execute()
                                        self.registrar_log("CREACIÓN", "USUARIOS", f"Creado: {u}")
                                        st.success("Usuario registrado con éxito.")
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al procesar la solicitud: {e}")
                        else:
                            st.error("Por favor completa los campos obligatorios (Usuario y Nombre Completo).")

            with col_lista:
                st.subheader("Usuarios Registrados")
                try:
                    usuarios_db = self.supabase_nativo.table(self.tabla_perfiles).select("*").order("usuario").execute().data
                    if usuarios_db:
                        for user in usuarios_db:
                            with st.container(border=True):
                                c_info, c_edit, c_del = st.columns([3, 0.5, 0.5])
                                c_info.write(f"👤 **{user.get('nombre_completo')}**\n`{user.get('rol')}` | @{user.get('usuario')}")
                                
                                if c_edit.button("📝", key=f"edit_{user.get('id')}", help="Editar usuario"):
                                    st.session_state.edit_user = user
                                    st.rerun()
                                    
                                if c_del.button("🗑️", key=f"del_{user.get('id')}", help="Eliminar usuario"):
                                    self.supabase_nativo.table(self.tabla_perfiles).delete().eq("id", user.get('id')).execute()
                                    self.registrar_log("ELIMINACIÓN", "USUARIOS", f"Eliminado: {user.get('usuario')}")
                                    st.rerun()
                    else:
                        st.info("No hay usuarios registrados.")
                except Exception as e:
                    st.error(f"Error al cargar usuarios: {e}")

        # --- PESTAÑA 2: CARGA MASIVA DINÁMICA MULTI-TABLA ---
        with tab_importacion:
            st.subheader("Carga Masiva de Datos Automatizada")
            
            try:
                # Usamos de forma segura el rpc mapeado nativamente
                tablas_db = self.supabase_nativo.rpc("obtener_tablas_publicas").execute().data
                lista_tablas = [t.get("nombre_tabla") for t in tablas_db] if tablas_db else []
            except Exception as e:
                st.error(f"Error al conectar con el mapeador de tablas. {e}")
                lista_tablas = [self.tabla_inventario, self.tabla_perfiles]

            if lista_tablas:
                tabla_seleccionada = st.selectbox("Seleccione la tabla destino para la importación", lista_tablas)
                
                col_conflicto = "id"
                if "producto" in tabla_seleccionada or "inventario" in tabla_seleccionada:
                    col_conflicto = "REFERENCIA"
                elif "perfil" in tabla_seleccionada or "usuario" in tabla_seleccionada:
                    col_conflicto = "usuario"

                st.caption(f"💡 El sistema utilizará la columna **`{col_conflicto}`** para comprobar duplicados (On Conflict Update).")
                
                file = st.file_uploader(f"Subir archivo Excel para la tabla '{tabla_seleccionada}' (.xlsx)", type=["xlsx"])
                
                if file:
                    try:
                        df_load = pd.read_excel(file)
                        df_load.columns = [str(c).strip() for c in df_load.columns]
                        
                        st.write("📋 Vista previa de los datos detectados:")
                        st.dataframe(df_load.head(5), use_container_width=True)

                        if st.button(f"🚀 Ejecutar Carga Masiva en {tabla_seleccionada.upper()}", type="primary"):
                            df_load = df_load.replace({np.nan: None})
                            lote_datos = df_load.to_dict(orient='records')
                            
                            try:
                                # El método upsert requiere la instancia de cliente nativa expuesta aquí
                                self.supabase_nativo.table(tabla_seleccionada).upsert(lote_datos, on_conflict=col_conflicto).execute()
                                self.registrar_log("IMPORTACIÓN MASIVA", tabla_seleccionada, f"Carga de {len(lote_datos)} registros.")
                                st.success(f"¡Carga completada! {len(lote_datos)} filas actualizadas/insertadas en `{tabla_seleccionada}`.")
                                st.balloons()
                            except Exception as db_err:
                                st.error(f"Error de base de datos en inserción: {db_err}")
                                st.info("Verifique que los nombres de las columnas coincidan de forma exacta con los campos en Supabase.")
                    except Exception as e:
                        st.error(f"Error al interpretar archivo Excel: {e}")
            else:
                st.warning("No se detectaron tablas públicas editables en la base de datos.")

        # --- PESTAÑA 3: AUDITORÍA GLOBAL DEL SISTEMA ---
        with tab_logs:
            st.subheader("📜 Historial de Auditoría de Operaciones")
            st.write("Visualiza las últimas actividades, ediciones y cargas masivas ejecutadas en la plataforma.")
            
            try:
                logs_db = self.supabase_nativo.table(self.tabla_logs).select("*").order("id", desc=True).limit(250).execute().data
                
                if logs_db:
                    df_logs = pd.DataFrame(logs_db)
                    
                    columnas_ordenadas = ["created_at", "usuario", "accion", "modulo", "detalle"]
                    columnas_presentes = [col for col in columnas_ordenadas if col in df_logs.columns]
                    df_logs = df_logs[columnas_presentes]
                    
                    df_logs.columns = [col.upper().replace("_", " ") for col in df_logs.columns]
                    
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                else:
                    st.info("El historial de auditoría se encuentra vacío temporalmente.")
            except Exception as e:
                st.warning(f"Error al conectar con la bitácora de logs: {e}")

        # --- PESTAÑA 4: SISTEMA Y MANTENIMIENTO ---
        with tab_sistema:
            st.subheader("Acciones de Respaldo y Mantenimiento")
            
            if st.button("💾 Generar Copia de Seguridad Completa (Inventario Actual)"):
                try:
                    data_inv = self.supabase_nativo.table(self.tabla_inventario).select("*").execute().data
                    if data_inv:
                        df_exp = pd.DataFrame(data_inv)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_exp.to_excel(writer, sheet_name='INVENTARIO_RESPALDO', index=False)
                        st.download_button("📥 Descargar Archivo .xlsx", output.getvalue(), "respaldo_inventario.xlsx", use_container_width=True)
                    else:
                        st.warning("La tabla está vacía, no hay nada que respaldar.")
                except Exception as e:
                    st.error(f"Error al compilar respaldo: {e}")

            st.divider()
            st.error("Zona de Peligro (Acciones de Restablecimiento)")
            
            if st.button("🗑️ Vaciar Por Completo Tabla de Inventario"):
                try:
                    self.supabase_nativo.table(self.tabla_inventario).delete().neq("REFERENCIA", "VACIO_CRITICO_SISTEMA_BYPASS").execute()
                    self.registrar_log("MANTENIMIENTO", "DB", "Vaciado total preventivo de la tabla de productos.")
                    st.success("Se ha ejecutado el vaciado de la tabla de inventario de manera satisfactoria.")
                    st.rerun()
                except Exception as e:
                    st.error(f"La base de datos denegó la purga masiva de datos: {e}")