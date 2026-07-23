from typing import Optional
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

class ModuloConfiguracion:
    def __init__(self, db):
        # Detección de cliente nativo de Supabase
        if hasattr(db, 'client'):
            self.supabase_nativo = db.client
        else:
            self.supabase_nativo = db
            
        self.db = db 
        self.tabla_perfiles = "perfiles"
        self.tabla_inventario = "productos"
        self.tabla_logs = "logs_sistema"
        
        self.roles_disponibles = ["usuario", "supervisor", "administrador", "master_it"]
        self.modulos_sistema = ["Acceso", "USUARIOS", "INVENTARIO", "VENTAS", "SISTEMA"]

    def registrar_log(self, accion: str, modulo: str, detalle: str, usuario_alt: Optional[str] = None):
        """Registra automáticamente cualquier movimiento u operación en la bitácora de logs"""
        try:
            session_data = st.session_state.get('user_data', {})
            usuario_actual = usuario_alt or session_data.get('usuario', 'masterit')
            rol_actual = session_data.get('rol', 'master_it')
            
            log_data = {
                "usuario": usuario_actual,
                "rol": rol_actual,
                "accion": str(accion).upper(),
                "modulo": str(modulo).upper(),
                "detalle": str(detalle),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.supabase_nativo.table(self.tabla_logs).insert(log_data).execute()
        except Exception as e:
            print(f"Error al registrar log de movimiento: {e}")

    def render(self):
        # SEGURIDAD: Control de acceso por rol
        user_info = st.session_state.get('user_data')
        if not user_info or user_info.get('rol') != "master_it":
            st.error("🚫 Acceso Denegado. Se requiere perfil Master IT para realizar cambios de sistema.")
            return

        st.markdown("<h2 style='color: #4A4A4A;'>⚙️ Panel de Control del Sistema</h2>", unsafe_allow_html=True)
        
        # Estructura limpia de pestañas sin Caja como título independiente
        tab_usuarios, tab_importacion, tab_logs, tab_sistema, tab_migracion = st.tabs([
            "👥 Usuarios", 
            "📊 Carga Masiva Local", 
            "📜 Auditoría Global", 
            "🛡️ Sistema",
            "🔄 Migración Inicial Supabase"
        ])

        # ==========================================
        # --- PESTAÑA 1: GESTIÓN DE USUARIOS ---
        # ==========================================
        with tab_usuarios:
            col_form, col_lista = st.columns([1, 1.3])

            if "edit_user" not in st.session_state:
                st.session_state.edit_user = None

            modo_edicion = st.session_state.edit_user is not None
            titulo_form = "📝 Editar Usuario" if modo_edicion else "➕ Crear Nuevo Acceso"
            def_val: dict = st.session_state.edit_user if modo_edicion and st.session_state.edit_user else {}

            with col_form:
                form_key = f"f_usuario_{def_val.get('id', 'nuevo')}"
                
                with st.form(form_key, clear_on_submit=not modo_edicion):
                    st.subheader(titulo_form)
                    
                    u_val = st.text_input("Usuario (Login)", value=def_val.get('usuario', ''), disabled=modo_edicion)
                    u = u_val.lower().strip() if u_val else ''
                    p = st.text_input("Contraseña", type="password", help="Dejar en blanco para conservar la actual al editar")
                    n = st.text_input("Nombre Completo", value=def_val.get('nombre_completo', ''))
                    car = st.text_input("Cargo", value=def_val.get('cargo', ''))
                    
                    rol_actual = def_val.get('rol')
                    rol_idx = self.roles_disponibles.index(rol_actual) if rol_actual in self.roles_disponibles else 0
                    r = st.selectbox("Rol del Sistema", self.roles_disponibles, index=rol_idx)
                    
                    btn_label = "Actualizar Usuario" if modo_edicion else "Registrar Usuario"
                    submit = st.form_submit_button(btn_label, use_container_width=True)

                if modo_edicion:
                    if st.button("❌ Cancelar Edición", use_container_width=True):
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
                                self.registrar_log("MODIFICACION", "USUARIOS", f"Editado usuario @{u}")
                                st.success(f"Usuario {u} actualizado correctamente.")
                                st.session_state.edit_user = None
                            else:
                                if not p: 
                                    st.error("La contraseña es obligatoria para nuevos usuarios.")
                                    st.stop()
                                
                                self.supabase_nativo.table(self.tabla_perfiles).insert(datos).execute()
                                self.registrar_log("CREACIÓN", "USUARIOS", f"Creado usuario @{u}")
                                st.success(f"Usuario {u} registrado con éxito.")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al procesar la solicitud: {e}")
                    else:
                        st.error("Por favor completa los campos obligatorios.")

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
                                    self.registrar_log("ELIMINACIÓN", "USUARIOS", f"Eliminado usuario @{user.get('usuario')}")
                                    st.rerun()
                    else:
                        st.info("No hay usuarios registrados.")
                except Exception as e:
                    st.error(f"Error al cargar usuarios: {e}")

        # ==========================================
        # --- PESTAÑA 2: CARGA MASIVA LOCAL ---
        # ==========================================
        with tab_importacion:
            st.subheader("📊 Carga Masiva de Datos Automatizada")
            
            try:
                tablas_db = self.supabase_nativo.rpc("obtener_tablas_publicas").execute().data
                lista_tablas = [t.get("nombre_tabla") for t in tablas_db] if tablas_db else []
            except Exception:
                lista_tablas = [self.tabla_inventario, self.tabla_perfiles]

            if lista_tablas:
                tabla_seleccionada = st.selectbox("Seleccione la tabla destino", lista_tablas)
                col_conflicto = "REFERENCIA" if "producto" in tabla_seleccionada or "inventario" in tabla_seleccionada else "id"
                
                file = st.file_uploader(f"Subir archivo Excel (.xlsx) para '{tabla_seleccionada}'", type=["xlsx"])
                if file:
                    try:
                        df_load = pd.read_excel(file)
                        st.dataframe(df_load.head(5), use_container_width=True)

                        if st.button(f"🚀 Ejecutar Carga Masiva en {tabla_seleccionada.upper()}", type="primary"):
                            df_clean = df_load.replace({np.nan: None})
                            lote_datos = df_clean.to_dict(orient='records')
                            
                            self.supabase_nativo.table(tabla_seleccionada).upsert(lote_datos, on_conflict=col_conflicto).execute()
                            self.registrar_log("IMPORTACIÓN MASIVA", "INVENTARIO", f"Carga de {len(lote_datos)} registros en {tabla_seleccionada}")
                            st.success(f"¡Carga completada! {len(lote_datos)} registros actualizados.")
                            st.balloons()
                    except Exception as e:
                        st.error(f"Error al procesar archivo: {e}")

        # ==========================================
        # --- PESTAÑA 3: AUDITORÍA GLOBAL (MUESTRA TODOS LOS MOVIMIENTOS) ---
        # ==========================================
        with tab_logs:
            st.subheader("📜 Historial de Auditoría Local / Movimientos")
            
            # Filtros superiores
            c_filtro_mod, c_filtro_limite = st.columns([2.5, 1])
            with c_filtro_mod:
                modulos_unicos = ["Acceso", "USUARIOS", "INVENTARIO", "VENTAS", "SISTEMA"]
                filtro_modulo = st.multiselect("Filtrar por Módulo", options=modulos_unicos, default=[])
            with c_filtro_limite:
                limite_registros = st.slider("Cantidad de registros", min_value=10, max_value=500, value=150, step=10)

            try:
                query = self.supabase_nativo.table(self.tabla_logs).select("*")
                if filtro_modulo:
                    query = query.in_("modulo", filtro_modulo)
                    
                logs_db = query.order("id", desc=True).limit(limite_registros).execute().data
                
                if logs_db:
                    df_logs = pd.DataFrame(logs_db)
                    
                    # Mapeo estandarizado de campos
                    col_map = {
                        "created_at": "fecha",
                        "usuario": "usuario",
                        "rol": "rol",
                        "accion": "accion",
                        "modulo": "modulo",
                        "detalle": "detalle"
                    }
                    df_logs = df_logs.rename(columns=col_map)
                    
                    # Formato en Mayúsculas para columnas clave según Foto 1/Foto 2
                    for c in ["usuario", "rol", "accion", "modulo", "detalle", "fecha"]:
                        if c in df_logs.columns:
                            df_logs.rename(columns={c: c.upper()}, inplace=True)

                    # Reordenación exacta de columnas
                    columnas_deseadas = ["id", "FECHA", "USUARIO", "ROL", "ACCION", "MODULO", "DETALLE"]
                    columnas_presentes = [c for c in columnas_deseadas if c in df_logs.columns]
                    resto_cols = [c for c in df_logs.columns if c not in columnas_presentes]
                    
                    df_logs = df_logs[columnas_presentes + resto_cols]
                    
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                    
                    # Descarga en CSV
                    csv_logs = df_logs.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Descargar Reporte de Auditoría (CSV)",
                        data=csv_logs,
                        file_name=f"reporte_movimientos_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No hay movimientos registrados en la bitácora.")
            except Exception as e:
                st.warning(f"Error al consultar la bitácora de movimientos: {e}")

        # ==========================================
        # --- PESTAÑA 4: SISTEMA Y MANTENIMIENTO ---
        # ==========================================
        with tab_sistema:
            st.subheader("🛡️ Mantenimiento y Respaldo")
            
            if st.button("💾 Generar Copia de Seguridad Completa"):
                try:
                    data_inv = self.supabase_nativo.table(self.tabla_inventario).select("*").execute().data
                    if data_inv:
                        df_exp = pd.DataFrame(data_inv)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_exp.to_excel(writer, sheet_name='RESPALDO', index=False)
                        
                        output.seek(0)
                        st.download_button(
                            label="📥 Descargar Archivo .xlsx", 
                            data=output.getvalue(), 
                            file_name="respaldo_inventario.xlsx", 
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        self.registrar_log("RESPALDO", "SISTEMA", "Generado respaldo de base de datos")
                except Exception as e:
                    st.error(f"Error al exportar: {e}")

        # ==========================================
        # --- PESTAÑA 5: MIGRACIÓN SUPABASE ---
        # ==========================================
        with tab_migracion:
            st.subheader("🔄 Migración Inicial Supabase")
            st.info("Módulo para procesos directos de sincronización y migración inicial.")