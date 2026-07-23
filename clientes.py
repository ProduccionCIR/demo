#clientes.py
import streamlit as st
import pandas as pd
import datetime
import io
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ModuloClientes:
    def __init__(self, db):
        self.db = db
        self.tabla = "clientes"
        
        if hasattr(db, 'client'):
            self.supabase_nativo = db.client
        else:
            self.supabase_nativo = db

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
            self.supabase_nativo.table("logs_sistema").insert(log_data).execute()
        except:
            pass

    def generar_pdf_catalogo(self, productos_list, mostrar_precio=True, fecha_venc_catalogo=None):
        """Genera un catálogo en PDF estilizado incluyendo la composición de materiales."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CatalogTitle', parent=styles['Heading1'], fontSize=24, leading=28,
            textColor=colors.HexColor("#4A4A4A"), alignment=1, spaceAfter=10
        )
        meta_style = ParagraphStyle('ProdMeta', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#555555"))
        venc_style = ParagraphStyle('CatalogVenc', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#D32F2F"), fontName="Helvetica-Bold", alignment=1)
        price_style = ParagraphStyle('ProdPrice', parent=styles['Normal'], fontSize=12, leading=14, textColor=colors.HexColor("#00C853"), fontName="Helvetica-Bold")

        story = []
        story.append(Paragraph("📋 CATÁLOGO EXCLUSIVO DE PRODUCTOS", title_style))
        story.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", meta_style))
        
        if fecha_venc_catalogo:
            story.append(Paragraph(f"⚠️ Ofertas válidas hasta: {fecha_venc_catalogo.strftime('%d/%m/%Y')}", venc_style))
            
        story.append(Spacer(1, 15))
        
        celdas = []
        fila_actual = []
        
        for item in productos_list:
            if not isinstance(item, dict):
                continue
            img_url = item.get('IMAGEN')
            img_flowable = None
            
            if img_url and str(img_url).startswith("http"):
                try:
                    response = requests.get(img_url, timeout=5)
                    if response.status_code == 200:
                        img_data = io.BytesIO(response.content)
                        img_flowable = Image(img_data, width=100, height=100)
                except Exception:
                    img_flowable = None
                    
            if not img_flowable:
                img_flowable = Paragraph("<font color='gray'>[Sin Imagen]</font>", meta_style)

            ref = item.get('REFERENCIA') or "S/R"
            desc = item.get('DESCRIPCION') or ""
            marca = item.get('MARCA') or ""
            costo = item.get('COSTO UNIT') or 0.0
            cb = item.get('codigo_barra') or ""
            comp_quimica = item.get('composicion') or "" # Extracción de la composición química
            
            tag_cb = f"<br/><b>Código:</b> {cb}" if cb else ""
            tag_comp = f"<br/><b>🧪 Composición:</b> {comp_quimica}" if comp_quimica else ""
            
            info_html = f"<b>Ref:</b> {ref}<br/><b>Marca:</b> {marca}<br/>{desc[:50]}...{tag_cb}{tag_comp}"
            precio_html = f"${float(costo):,.2f}" if mostrar_precio else ""
            
            tabla_producto_data = [
                [img_flowable, Paragraph(info_html, meta_style)],
                ['', Paragraph(precio_html, price_style)]
            ]
            
            tarjeta_producto = Table(tabla_producto_data, colWidths=[100, 150])
            tarjeta_producto.setStyle(TableStyle([
                ('SPAN', (0, 0), (0, 1)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            fila_actual.append(tarjeta_producto)
            if len(fila_actual) == 2:
                celdas.append(fila_actual)
                fila_actual = []
                
        if fila_actual:
            fila_actual.append(Paragraph("", meta_style))
            celdas.append(fila_actual)
            
        if celdas:
            tabla_catalogo = Table(celdas, colWidths=[265, 265])
            tabla_catalogo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(tabla_catalogo)
            
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

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
                
                tipo_cliente = st.selectbox("Tipo de Cliente", ["Nacional / Zona Libre (ZLC)", "Offshore (Exportación)"])
                es_offshore_bool = True if tipo_cliente == "Offshore (Exportación)" else False

                dir = st.text_area("Dirección").strip().upper()

                if st.form_submit_button("💾 Guardar Cliente", use_container_width=True):
                    if nombre and id_fiscal:
                        nuevo_c = {
                            "nombre": nombre,
                            "identificacion": id_fiscal,
                            "telefono": tel,
                            "email": mail,
                            "direccion": dir,
                            "es_offshore": es_offshore_bool,
                            "registrado_por": usuario_actual,
                            "fecha_registro": datetime.date.today().isoformat()
                        }
                        try:
                            self.supabase_nativo.table(self.tabla).insert(nuevo_c).execute()
                            self.registrar_log("Creación", f"Cliente {nombre} ({tipo_cliente}) registrado por {usuario_actual}")
                            st.success(f"✅ Cliente {nombre} guardado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}.")
                    else:
                        st.warning("⚠️ Nombre e Identificación son requeridos.")

        # --- 2. BÚSQUEDA Y FILTRADO DE LISTADO ---
        st.markdown("---")
        
        f1, f2 = st.columns([2, 1])
        busqueda = f1.text_input("🔍 Buscar cliente (Nombre, ID o Email)...").strip().upper()
        filtro_tipo = f2.selectbox("📂 Filtrar por Tipo", ["Todos", "Solo Nacionales (ZLC)", "Solo Offshore"])
        
        try:
            res = self.supabase_nativo.table(self.tabla).select("*").order("nombre").execute().data
        except:
            res = []
            st.error("Error al conectar con la tabla 'clientes'.")
        
        if res:
            df = pd.DataFrame(res)
            
            if 'es_offshore' not in df.columns:
                df['es_offshore'] = False
            else:
                df['es_offshore'] = df['es_offshore'].fillna(False)

            if filtro_tipo == "Solo Nacionales (ZLC)":
                df = df[df['es_offshore'] == False]
            elif filtro_tipo == "Solo Offshore":
                df = df[df['es_offshore'] == True]

            if busqueda:
                mask = df.apply(lambda row: busqueda in str(row).upper(), axis=1)
                df = df[mask]
            
            st.dataframe(df, use_container_width=True, hide_index=True)

            # --- 3. PANEL DE GESTIÓN ---
            st.subheader("🛠️ Gestión de Cuenta")
            
            registros_filtrados = df.to_dict(orient="records")
            opciones = {f"{c['nombre']} [{c['identificacion']}]": c for c in registros_filtrados}
            
            sel = st.selectbox("Seleccione un cliente:", ["-- Seleccionar --"] + list(opciones.keys()))

            if sel != "-- Seleccionar --":
                cli = opciones[sel]
                
                tab_editar, tab_estado, tab_historial_prod = st.tabs([
                    "📝 Editar / Eliminar", 
                    "📊 Estado de Cuenta", 
                    "📦 Historial de Consumo y Catálogo"
                ])

                # PESTAÑA 1: EDITAR / ELIMINAR
                with tab_editar:
                    with st.form(f"edit_cli_{cli['id']}"):
                        st.write(f"✍️ Editando: **{cli['nombre']}**")
                        e_nom = st.text_input("Nombre", value=cli['nombre'])
                        e_id = st.text_input("Identificación", value=cli['identificacion'])
                        e_tel = st.text_input("Teléfono", value=cli.get('telefono', ''))
                        e_cor = st.text_input("Email", value=cli.get('email', ''))
                        
                        index_tipo = 1 if cli.get('es_offshore', False) else 0
                        e_tipo = st.selectbox("Tipo de Cliente", ["Nacional / Zona Libre (ZLC)", "Offshore (Exportación)"], index=index_tipo)
                        e_offshore_bool = True if e_tipo == "Offshore (Exportación)" else False
                        
                        e_dir = st.text_area("Dirección", value=cli.get('direccion', ''))
                        
                        if st.form_submit_button("💾 Actualizar Información", use_container_width=True):
                            upd = {
                                "nombre": e_nom.upper(),
                                "identificacion": e_id.upper(),
                                "telefono": e_tel,
                                "email": e_cor,
                                "es_offshore": e_offshore_bool,
                                "direccion": e_dir.upper()
                            }
                            self.supabase_nativo.table(self.tabla).update(upd).eq("id", cli['id']).execute()
                            self.registrar_log("Edición", f"Datos de {e_nom} actualizados por {usuario_actual}")
                            st.success("Cambios guardados.")
                            st.rerun()

                    if rol_actual in ["administrador", "master_it"]:
                        st.markdown("---")
                        st.error("⚠️ Zona de Eliminación")
                        confirmar = st.checkbox(f"Confirmo que deseo ELIMINAR a {cli['nombre']}")
                        if st.button("🗑️ Eliminar Registro", type="primary", disabled=not confirmar, use_container_width=True):
                            self.supabase_nativo.table(self.tabla).delete().eq("id", cli['id']).execute()
                            self.registrar_log("Eliminación", f"Cliente {cli['nombre']} borrado por {usuario_actual}")
                            st.error("Cliente eliminado.")
                            st.rerun()

                # PESTAÑA 2: ESTADO DE CUENTA
                with tab_estado:
                    st.write(f"### 📊 Estado de Cuenta: {cli['nombre']}")
                    ventas = []
                    try:
                        ventas = self.supabase_nativo.table("ventas").select("*").eq("cliente", cli['nombre']).execute().data
                        
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
                            
                            df_mostrar = df_v[['fecha', 'num_fact', 'total', 'estado']].copy()
                            df_mostrar.columns = ['FECHA', 'N° FACTURA', 'TOTAL', 'ESTADO']
                            df_mostrar['TOTAL'] = df_mostrar['TOTAL'].map('${:,.2f}'.format)
                            
                            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                        else:
                            st.info("No hay historial de facturación para este cliente.")
                    except Exception as err:
                        st.warning(f"⚠️ No se pudo procesar el estado de cuenta. Detalles: {err}")

                # PESTAÑA 3: HISTORIAL DE CONSUMO DE PRODUCTOS DESDE EL JSONB DE LA VENTA
                with tab_historial_prod:
                    st.write(f"### 📦 Historial de Consumo de {cli['nombre']}")
                    st.write("Consulta los artículos específicos, cantidades y precios facturados a este cliente.")

                    if ventas:
                        lista_acumulada_productos = []
                        
                        for v in ventas:
                            num_fac = v.get('num_fact', 'S/N')
                            fecha_fac = v.get('fecha', 'S/F')
                            
                            if fecha_fac and fecha_fac != 'S/F':
                                try:
                                    fecha_fac = pd.to_datetime(fecha_fac).strftime('%d/%m/%Y')
                                except:
                                    pass
                            
                            # Desglosar los productos desde la columna JSONB de la tabla ventas
                            items_venta = v.get('productos')
                            if items_venta and isinstance(items_venta, list):
                                for item in items_venta:
                                    if isinstance(item, dict):
                                        p_id = item.get('producto_id') or item.get('ID') or item.get('id')
                                        cant = item.get('cantidad') or item.get('CANTIDAD') or 0
                                        precio = item.get('precio') or item.get('precio_venta') or item.get('precio_unitario') or 0.0
                                        
                                        if p_id:
                                            lista_acumulada_productos.append({
                                                "FECHA": fecha_fac,
                                                "FACTURA": num_fac,
                                                "producto_id": p_id,
                                                "CANTIDAD": cant,
                                                "PRECIO_PACTADO": precio
                                            })

                        if lista_acumulada_productos:
                            df_compras = pd.DataFrame(lista_acumulada_productos)
                            
                            try:
                                prods_master = self.supabase_nativo.table("productos").select("*").execute().data
                                df_prods = pd.DataFrame(prods_master) if prods_master else pd.DataFrame()
                            except:
                                df_prods = pd.DataFrame()

                            if not df_prods.empty:
                                df_compras['producto_id'] = pd.to_numeric(df_compras['producto_id'], errors='coerce').fillna(0).astype(int)
                                df_prods['ID'] = pd.to_numeric(df_prods['ID'], errors='coerce').fillna(0).astype(int)
                                
                                # Combinar información del JSON de la venta con la maestra de productos
                                df_final_compras = pd.merge(df_compras, df_prods, left_on='producto_id', right_on='ID', how='inner')
                                
                                if not df_final_compras.empty:
                                    # Asegurar el campo de composición por si viene vacío o nulo
                                    if 'composicion' in df_final_compras.columns:
                                        df_final_compras['composicion'] = df_final_compras['composicion'].fillna('NO ESPECIFICADO')
                                    else:
                                        df_final_compras['composicion'] = 'NO ESPECIFICADO'

                                    # Mostrar la tabla detallada interactiva solicitada
                                    st.dataframe(
                                        df_final_compras[['FECHA', 'FACTURA', 'REFERENCIA', 'MARCA', 'DESCRIPCION', 'composicion', 'CANTIDAD', 'PRECIO_PACTADO']],
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "FECHA": "📅 Fecha",
                                            "FACTURA": "Factura",
                                            "REFERENCIA": "Referencia",
                                            "MARCA": "Marca",
                                            "DESCRIPCION": "Descripción",
                                            "composicion": "🧪 Composición Química / Material",
                                            "CANTIDAD": "Cant.",
                                            "PRECIO_PACTADO": st.column_config.NumberColumn("Precio Pactado", format="$%.2f")
                                        }
                                    )

                                    # --- GENERADOR DE CATÁLOGO PERSONALIZADO ---
                                    st.markdown("---")
                                    st.subheader("🖨️ Crear Catálogo Exclusivo de Preferencias")
                                    st.write("Genera un PDF comercial con fichas técnicas de los productos comprados previamente por el cliente.")

                                    c_cat1, c_cat2 = st.columns(2)
                                    inc_p = c_cat1.checkbox("💲 Incluir Precios de Inventario Actuales", value=True, key=f"p_lis_{cli['id']}")
                                    def_v = c_cat2.checkbox("📅 Definir Límite de Validez en el PDF", key=f"v_lis_{cli['id']}")
                                    
                                    f_venc = None
                                    if def_v:
                                        f_venc = c_cat2.date_input("Válido hasta:", value=datetime.date.today(), key=f"f_v_lis_{cli['id']}")

                                    if st.button("✨ Compilar Catálogo a la Medida", type="primary", use_container_width=True, key=f"btn_c_{cli['id']}"):
                                        with st.spinner("Compilando catálogo histórico y procesando fichas técnicas..."):
                                            ids_unicos = df_final_compras['ID'].unique().tolist()
                                            lista_prods_pdf = [p for p in prods_master if int(p.get('ID', 0)) in ids_unicos]

                                            if lista_prods_pdf:
                                                pdf_bytes = self.generar_pdf_catalogo(
                                                    lista_prods_pdf, 
                                                    mostrar_precio=inc_p, 
                                                    fecha_venc_catalogo=f_venc
                                                )
                                                st.download_button(
                                                    label="📥 Descargar Catálogo PDF con Composición",
                                                    data=pdf_bytes,
                                                    file_name=f"catalogo_fichas_{str(cli['nombre']).replace(' ', '_')}.pdf",
                                                    mime="application/pdf",
                                                    use_container_width=True
                                                )
                                                st.success("¡Catálogo e historial procesados exitosamente!")
                                else:
                                    st.info("Los productos comprados históricamente ya no se encuentran activos en la base de datos de inventario.")
                            else:
                                st.error("No se pudo conectar con la tabla 'productos' para complementar los nombres.")
                        else:
                            st.info("La columna 'productos' de las ventas de este cliente está vacía.")
                    else:
                        st.info("El cliente seleccionado no registra transacciones en la tabla 'ventas'.")
        else:
            st.info("No hay clientes registrados.")