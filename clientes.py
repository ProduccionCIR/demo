# clientes.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utilidades import check_permiso  # <-- INTEGRACIÓN DEL CANDADO DE SEGURIDAD

class ModuloClientes:
    def __init__(self, db):
        self.db = db
        self.tabla = "clientes"

    def registrar_log(self, accion, detalle):
        """Registra la actividad en la tabla central unificada de auditoría en SQLite."""
        try:
            user_info = st.session_state.get('user_data', {})
            usuario = user_info.get('usuario', st.session_state.get('usuario', 'Sistema'))
            
            query = """
                INSERT INTO logs_sistema (modulo, usuario, accion, detalle, creado_en)
                VALUES (?, ?, ?, ?, ?)
            """
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.ejecutar_consulta(query, ("CLIENTES", usuario, str(accion).upper(), str(detalle), fecha_actual))
        except Exception:
            pass  # Los fallos en logs no deben romper el flujo principal

    def render(self):
        st.header("👥 Cartera de Clientes")
        user_info = st.session_state.get('user_data', {})
        usuario_actual = user_info.get('usuario', 'Admin_Clientes')

        # Evaluación de los permisos requeridos para las operaciones del módulo
        puede_ingresar = check_permiso("ingresar")
        puede_modificar = check_permiso("modificar")
        puede_eliminar = check_permiso("eliminar")

        # --- 1. FORMULARIO DE REGISTRO (Local) ---
        with st.expander("➕ Registrar Nuevo Cliente", expanded=False):
            with st.form("form_nuevo_cliente", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre / Razón Social").strip().upper()
                id_fiscal = c2.text_input("Identificación (RUC / Cédula / Pasaporte)").strip().upper()
                
                tel = c1.text_input("Teléfono / WhatsApp").strip()
                mail = c2.text_input("Correo Electrónico").strip()
                dir_cliente = st.text_area("Dirección").strip().upper()

                btn_guardar = st.form_submit_button(
                    "💾 Guardar Cliente", 
                    use_container_width=True,
                    disabled=not puede_ingresar,
                    help="🔒 Inicie sesión con una cuenta autorizada para registrar clientes." if not puede_ingresar else None
                )

                if btn_guardar and puede_ingresar:
                    if nombre and id_fiscal:
                        query = f"""
                            INSERT INTO {self.tabla} (nombre, identificacion, telefono, email, direccion, registrado_por, fecha_registro)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                        params = (nombre, id_fiscal, tel, mail, dir_cliente, usuario_actual, fecha_hoy)
                        
                        try:
                            self.db.ejecutar_consulta(query, params)
                            self.registrar_log("Creación", f"Cliente {nombre} registrado por {usuario_actual}")
                            st.success(f"✅ Cliente {nombre} guardado correctamente de manera local.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar localmente: {e}")
                    else:
                        st.warning("⚠️ Nombre e Identificación son requeridos.")

        # --- 2. BÚSQUEDA Y LISTADO LOCAL OPTIMIZADO ---
        st.markdown("---")
        busqueda = st.text_input("🔍 Buscar cliente (Nombre, ID o Email)...").strip().upper()
        
        res = []
        try:
            if busqueda:
                query_select = f"SELECT * FROM {self.tabla} WHERE nombre LIKE ? OR identificacion LIKE ? OR email LIKE ? ORDER BY nombre ASC"
                term = f"%{busqueda}%"
                res = self.db.ejecutar_consulta(query_select, (term, term, term))
            else:
                query_select = f"SELECT * FROM {self.tabla} ORDER BY nombre ASC"
                res = self.db.ejecutar_consulta(query_select)
        except Exception as e:
            st.error(f"Error al leer la tabla local '{self.tabla}': {e}")
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # --- 3. PANEL DE GESTIÓN DE CUENTA COHERENTE ---
            st.subheader("🛠️ Gestión de Cuenta")
            
            opciones = {f"{c['nombre']} [{c['identificacion']}]": c['id'] for c in res}
            
            sel = st.selectbox(
                "Seleccione un cliente para editar o ver su estado de cuenta:", 
                ["-- Seleccionar --"] + list(opciones.keys()),
                key="crm_cliente_selector"
            )

            if sel != "-- Seleccionar --":
                id_cliente_sel = opciones[sel]
                
                # Búsqueda segura por ID
                cli_res = self.db.ejecutar_consulta(f"SELECT * FROM {self.tabla} WHERE id = ?", (id_cliente_sel,))
                if not cli_res:
                    st.error("No se pudieron cargar los datos del cliente seleccionado.")
                    return
                cli = cli_res[0]

                tab_editar, tab_estado = st.tabs(["📝 Editar / Eliminar", "📑 Estado de Cuenta"])

                with tab_editar:
                    with st.form(f"edit_cli_{cli['id']}"):
                        st.write(f"✍️ Editando: **{cli['nombre']}**")
                        e_nom = st.text_input("Nombre", value=cli['nombre'])
                        e_id = st.text_input("Identificación", value=cli['identificacion'])
                        e_tel = st.text_input("Teléfono", value=cli.get('telefono', ''))
                        e_cor = st.text_input("Email", value=cli.get('email', ''))
                        e_dir = st.text_area("Dirección", value=cli.get('direccion', ''))
                        
                        btn_actualizar = st.form_submit_button(
                            "💾 Actualizar Información", 
                            use_container_width=True,
                            disabled=not puede_modificar,
                            help="🔒 Requiere nivel de Supervisor o superior para modificar datos maestros." if not puede_modificar else None
                        )

                        if btn_actualizar and puede_modificar:
                            query_upd = f"""
                                UPDATE {self.tabla} 
                                SET nombre=?, identificacion=?, telefono=?, email=?, direccion=?
                                WHERE id=?
                            """
                            params_upd = (e_nom.upper(), e_id.upper(), e_tel, e_cor, e_dir.upper(), cli['id'])
                            
                            self.db.ejecutar_consulta(query_upd, params_upd)
                            self.registrar_log("Edición", f"Datos de {e_nom} actualizados por {usuario_actual}")
                            st.success("✅ Cambios guardados localmente.")
                            st.rerun()

                    # 🚫 ELIMINACIÓN RESTRINGIDA POR CANDADO CENTRALIZADO
                    if puede_eliminar:
                        st.markdown("---")
                        st.error("⚠️ Zona de Eliminación")
                        confirmar = st.checkbox(f"Confirmo que deseo ELIMINAR a {cli['nombre']}", key=f"del_chk_{cli['id']}")
                        
                        btn_eliminar = st.button("🗑️ Eliminar Registro", type="primary", disabled=not confirmar, use_container_width=True)
                        
                        if btn_eliminar and confirmar:
                            query_del = f"DELETE FROM {self.tabla} WHERE id=?"
                            self.db.ejecutar_consulta(query_del, (cli['id'],))
                            
                            self.registrar_log("Eliminación", f"Cliente {cli['nombre']} borrado por {usuario_actual}")
                            st.error("Cliente eliminado de la base local.")
                            st.rerun()
                    else:
                        st.markdown("---")
                        st.info("ℹ️ Tienes permiso para visualizar/editar según tu nivel, pero la eliminación de registros está restringida a niveles administrativos.")

                with tab_estado:
                    st.write(f"### 📊 Estado de Cuenta: {cli['nombre']}")
                    try:
                        ventas_cliente = self.db.ejecutar_consulta("SELECT * FROM ventas WHERE id_cliente = ?", (str(cli['id']),))
                        
                        if ventas_cliente:
                            df_v = pd.DataFrame(ventas_cliente)
                            
                            if 'estado' not in df_v.columns: 
                                df_v['estado'] = 'PENDIENTE'
                            
                            df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0.0)
                            
                            c1, c2 = st.columns(2)
                            pend = df_v[df_v['estado'].str.upper() == 'PENDIENTE']['total'].sum()
                            pago = df_v[df_v['estado'].str.upper() == 'PAGADA']['total'].sum()
                            
                            c1.metric("Saldo Pendiente", f"${pend:,.2f}", delta="- CxC", delta_color="inverse")
                            c2.metric("Total Cobrado", f"${pago:,.2f}")
                            
                            cols_v = [c for c in ['fecha', 'nro_factura', 'usuario', 'total', 'estado'] if c in df_v.columns]
                            st.dataframe(df_v[cols_v], use_container_width=True, hide_index=True)
                        else:
                            st.info("No hay historial de facturación local para este cliente.")
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo cargar el estado de cuenta: {e}")
        else:
            st.info("No se encontraron clientes registrados en la base de datos local.")