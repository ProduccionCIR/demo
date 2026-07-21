import streamlit as st
import pandas as pd

class ModuloAdmin:
    def __init__(self, db):
        self.db = db

    def render(self):
        st.header("🛡️ Panel de Control Master IT")
        
        # Pestañas para organizar la administración del sistema híbrido
        tab1, tab2, tab3 = st.tabs(["👤 Gestión de Usuarios", "📜 Auditoría de Logs", "🔄 Sincronización Cloud"])

        with tab1:
            st.subheader("Agregar o Modificar Personal")
            
            # Formulario con diseño limpio
            with st.container(border=True):
                with st.form("registro_usuario", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    
                    id_p = c1.number_input("ID del Perfil (0 para nuevo usuario)", min_value=0, step=1, help="Usa 0 para crear uno nuevo o el ID exacto para editar uno existente.")
                    usuario_n = c1.text_input("Nombre de Usuario / Login", placeholder="ej. jsmith")
                    clave_n = c1.text_input("Contraseña de Acceso", type="password", placeholder="Dejar en blanco si solo editas el rol")
                    
                    nombre_n = c2.text_input("Nombre Completo", placeholder="ej. John Smith")
                    rol_n = c2.selectbox("Nivel de Acceso (Rol)", 
                                       ["usuario", "supervisor", "administrador", "master_it"],
                                       help="Usuario: Solo entrada. Supervisor: Modifica. Administrador: Borra. Master IT: Todo.")
                    
                    st.divider()
                    btn_guardar = st.form_submit_button("💾 Guardar Cambios en Perfil", use_container_width=True)

                    if btn_guardar:
                        if not usuario_n or (id_p == 0 and not clave_n):
                            st.error("Por favor completa los campos obligatorios (Usuario y Contraseña para nuevos).")
                        else:
                            # Mapeo idéntico a las columnas estructurales de SQLite en main.py
                            datos_perfil = {
                                "usuario": usuario_n.strip().lower(),
                                "rol": rol_n,
                                "nombre_completo": nombre_n.strip()
                            }
                            
                            # Solo actualizar o insertar clave si se escribe una nueva
                            if clave_n:
                                datos_perfil["clave"] = clave_n.strip()
                            
                            try:
                                if id_p == 0:
                                    self.db.insert("perfiles", datos_perfil)
                                    st.success(f"✅ Usuario '{usuario_n}' creado exitosamente.")
                                else:
                                    self.db.update("perfiles", datos_perfil, id_p)
                                    st.success(f"✅ Perfil ID {id_p} actualizado correctamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al procesar la base de datos: {e}")

            # Visualización de la tabla actual de perfiles
            st.subheader("Usuarios Registrados en Base de Datos Local")
            perfiles_data = self.db.fetch("perfiles")
            if perfiles_data:
                df_perfiles = pd.DataFrame(perfiles_data)
                
                # Columnas alineadas con el esquema real de producción
                cols = ['id', 'usuario', 'rol', 'nombre_completo']
                cols_visibles = [c for c in cols if c in df_perfiles.columns]
                
                st.dataframe(df_perfiles[cols_visibles], 
                             use_container_width=True, 
                             hide_index=True)
                
                # Opción rápida para eliminación 
                with st.expander("🗑️ Zona de Eliminación de Usuarios"):
                    id_borrar = st.number_input("ID a eliminar", min_value=1, step=1, key="del_user")
                    if st.button("Confirmar Eliminación Temeraria", type="primary", use_container_width=True):
                        self.db.delete("perfiles", id_borrar)
                        st.warning(f"Usuario con ID {id_borrar} eliminado físicamente de la base de datos local.")
                        st.rerun()
            else:
                st.info("No hay usuarios registrados aparte del administrador de rescate.")

        with tab2:
            st.subheader("Historial de Movimientos Locales")
            logs = self.db.fetch("logs_sistema")
            if logs:
                df_logs = pd.DataFrame(logs)
                # Ordenar por ID descendente si existe la columna para ver lo más reciente primero
                if "id" in df_logs.columns:
                    df_logs = df_logs.sort_values(by="id", ascending=False)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.write("No hay logs registrados todavía en el archivo db_sonix1.db.")

        with tab3:
            st.subheader("Pasarela de Sincronización desde la Nube")
            st.info("Esta herramienta descargará la última información estructural y operativa desde Supabase para guardarla de forma local en este dispositivo.")
            
            with st.container(border=True):
                st.markdown("### Ejecutar Clonación de Datos")
                st.caption("Nota: Esto reescribirá las tablas locales con la data fresca de la nube.")
                
                if st.button("🔄 Forzar Descarga y Clonación desde Supabase", type="secondary", use_container_width=True):
                    # Invoca de forma directa al método alojado en el SQLiteHelper de main.py
                    if hasattr(self.db, "clonar_desde_supabase"):
                        with st.spinner("Conectando y reconstruyendo almacenamiento local..."):
                            exito = self.db.clonar_desde_supabase()
                            if exito:
                                st.balloons()
                                st.rerun()
                    else:
                        st.error("El manejador de base de datos actual no tiene implementada la pasarela de clonación.")