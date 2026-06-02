import streamlit as st
import pandas as pd
import datetime

class ModuloClientes:
    def __init__(self, db):
        self.db = db
        self.tabla = "clientes"

    def registrar_log(self, accion, detalle):
        """Registra la actividad en la tabla de auditoría global."""
        user_info = st.session_state.get('user_data', {})
        log_data = {
            "usuario": user_info.get('usuario', 'Sistema'),
            "rol": user_info.get('rol', 'N/A'),
            "accion": accion,
            "modulo": "Clientes",
            "detalle": detalle,
            "fecha": datetime.datetime.now().isoformat()
        }
        try:
            self.db.table("logs_sistema").insert(log_data).execute()
        except:
            pass

    def render(self):
        st.header("👥 Cartera de Clientes")
        user_info = st.session_state.get('user_data', {})
        rol_actual = user_info.get('rol')
        usuario_actual = user_info.get('usuario')

        # --- 1. FORMULARIO DE REGISTRO ---
        with st.expander("➕ Registrar Nuevo Cliente", expanded=False):
            with st.form("form_nuevo_cliente", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre / Razón Social").strip().upper()
                id_fiscal = c2.text_input("Identificación (RUC / Cédula / Pasaporte)").strip().upper()
                
                tel = c1.text_input("Teléfono / WhatsApp")
                mail = c2.text_input("Correo Electrónico")
                
                # Opción para definir si es offshore al registrar
                tipo_cliente = st.selectbox("Tipo de Cliente", ["Nacional / Zona Libre (ZLC)", "Offshore (Exportación)"])
                es_offshore_bool = True if tipo_cliente == "Offshore (Exportación)" else False

                dir = st.text_area("Dirección").strip().upper()

                if st.form_submit_button("💾 Guardar Cliente", width="stretch"):
                    if nombre and id_fiscal:
                        nuevo_c = {
                            "nombre": nombre,
                            "identificacion": id_fiscal,
                            "telefono": tel,
                            "email": mail,
                            "direccion": dir,
                            "es_offshore": es_offshore_bool, # Nueva columna en base de datos
                            "registrado_por": usuario_actual,
                            "fecha_registro": datetime.date.today().isoformat()
                        }
                        try:
                            self.db.table(self.tabla).insert(nuevo_c).execute()
                            self.registrar_log("Creación", f"Cliente {nombre} ({tipo_cliente}) registrado por {usuario_actual}")
                            st.success(f"✅ Cliente {nombre} guardado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}. Asegúrese de tener la columna 'es_offshore' (boolean) en Supabase.")
                    else:
                        st.warning("⚠️ Nombre e Identificación son requeridos.")

        # --- 2. BÚSQUEDA Y FILTRADO DE LISTADO ---
        st.markdown("---")
        
        # Filtros superiores en paralelo
        f1, f2 = st.columns([2, 1])
        busqueda = f1.text_input("🔍 Buscar cliente (Nombre, ID o Email)...").strip().upper()
        filtro_tipo = f2.selectbox("📂 Filtrar por Tipo", ["Todos", "Solo Nacionales (ZLC)", "Solo Offshore"])
        
        try:
            res = self.db.table(self.tabla).select("*").order("nombre").execute().data
        except:
            res = []
            st.error("Error al conectar con la tabla 'clientes'.")
        
        if res:
            df = pd.DataFrame(res)
            
            # Asegurar existencia de la columna es_offshore por si hay registros antiguos vacíos
            if 'es_offshore' not in df.columns:
                df['es_offshore'] = False
            else:
                df['es_offshore'] = df['es_offshore'].fillna(False)

            # Aplicar filtro de Tipo de Cliente
            if filtro_tipo == "Solo Nacionales (ZLC)":
                df = df[df['es_offshore'] == False]
            elif filtro_tipo == "Solo Offshore":
                df = df[df['es_offshore'] == True]

            # Aplicar filtro de búsqueda por texto
            if busqueda:
                mask = df.apply(lambda row: busqueda in str(row).upper(), axis=1)
                df = df[mask]
            
            # Reorganizar columnas opcionalmente antes de mostrar el df
            st.dataframe(df, width="stretch", hide_index=True)

            # --- 3. PANEL DE GESTIÓN ---
            st.subheader("🛠️ Gestión de Cuenta")
            
            # El selectbox de gestión se alimenta de los registros ya filtrados para mayor comodidad
            registros_filtrados = df.to_dict(orient="records")
            opciones = {f"{c['nombre']} [{c['identificacion']}]": c for c in registros_filtrados}
            
            sel = st.selectbox("Seleccione un cliente:", ["-- Seleccionar --"] + list(opciones.keys()))

            if sel != "-- Seleccionar --":
                cli = opciones[sel]
                tab_editar, tab_estado = st.tabs(["📝 Editar / Eliminar", "📑 Estado de Cuenta"])

                with tab_editar:
                    with st.form(f"edit_cli_{cli['id']}"):
                        st.write(f"✍️ Editando: **{cli['nombre']}**")
                        e_nom = st.text_input("Nombre", value=cli['nombre'])
                        e_id = st.text_input("Identificación", value=cli['identificacion'])
                        e_tel = st.text_input("Teléfono", value=cli.get('telefono', ''))
                        e_cor = st.text_input("Email", value=cli.get('email', ''))
                        
                        # Opción de edición del tipo de cliente
                        index_tipo = 1 if cli.get('es_offshore', False) else 0
                        e_tipo = st.selectbox("Tipo de Cliente", ["Nacional / Zona Libre (ZLC)", "Offshore (Exportación)"], index=index_tipo)
                        e_offshore_bool = True if e_tipo == "Offshore (Exportación)" else False
                        
                        e_dir = st.text_area("Dirección", value=cli.get('direccion', ''))
                        
                        if st.form_submit_button("💾 Actualizar Información", width="stretch"):
                            upd = {
                                "nombre": e_nom.upper(),
                                "identificacion": e_id.upper(),
                                "telefono": e_tel,
                                "email": e_cor,
                                "es_offshore": e_offshore_bool,
                                "direccion": e_dir.upper()
                            }
                            self.db.table(self.tabla).update(upd).eq("id", cli['id']).execute()
                            self.registrar_log("Edición", f"Datos de {e_nom} actualizados por {usuario_actual}")
                            st.success("Cambios guardados.")
                            st.rerun()

                    if rol_actual in ["administrador", "master_it"]:
                        st.markdown("---")
                        st.error("⚠️ Zona de Eliminación")
                        confirmar = st.checkbox(f"Confirmo que deseo ELIMINAR a {cli['nombre']}")
                        if st.button("🗑️ Eliminar Registro", type="primary", disabled=not confirmar, width="stretch"):
                            self.db.table(self.tabla).delete().eq("id", cli['id']).execute()
                            self.registrar_log("Eliminación", f"Cliente {cli['nombre']} borrado por {usuario_actual}")
                            st.error("Cliente eliminado.")
                            st.rerun()
                    else:
                        st.info("ℹ️ Tienes permiso para editar, pero la eliminación es solo para administradores.")

                with tab_estado:
                    st.write(f"### 📊 Estado de Cuenta: {cli['nombre']}")
                    try:
                        ventas = self.db.table("ventas").select("*").eq("cliente", cli['nombre']).execute().data
                        
                        if ventas:
                            df_v = pd.DataFrame(ventas)
                            
                            if 'estado' not in df_v.columns: 
                                df_v['estado'] = 'PENDIENTE'
                            else:
                                df_v['estado'] = df_v['estado'].fillna('PENDIENTE').str.upper()
                                
                            df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0.0)
                            
                            c1, c2 = st.columns(2)
                            pend = df_v[df_v['estado'] == 'PENDIENTE']['total'].sum()
                            pago = df_v[df_v['estado'] == 'PAGADA']['total'].sum()
                            
                            c1.metric("Saldo Pendiente", f"${pend:,.2f}", delta="- CxC", delta_color="inverse")
                            c2.metric("Total Cobrado", f"${pago:,.2f}")
                            
                            cols_existentes = df_v.columns.tolist()
                            col_factura = 'num_fact' if 'num_fact' in cols_existentes else ('nro_factura' if 'nro_factura' in cols_existentes else 'id')
                            col_fecha = 'fecha' if 'fecha' in cols_existentes else 'created_at'
                            
                            df_mostrar = df_v[[col_fecha, col_factura, 'total', 'estado']].copy()
                            df_mostrar.columns = ['FECHA', 'N° FACTURA', 'TOTAL', 'ESTADO']
                            
                            df_mostrar['TOTAL'] = df_mostrar['TOTAL'].map('${:,.2f}'.format)
                            
                            st.dataframe(df_mostrar, width="stretch", hide_index=True)
                        else:
                            st.info("No hay historial de facturación para este cliente.")
                    except Exception as err:
                        st.warning(f"⚠️ No se pudo procesar el estado de cuenta. Detalles: {err}")
        else:
            st.info("No hay clientes registrados.")