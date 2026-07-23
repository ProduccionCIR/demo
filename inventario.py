#inventario.py
import streamlit as st
import pandas as pd
import datetime
import io
import base64
import requests
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ModuloInventario:
    def __init__(self, db):
        self.db = db
        self.tabla = "productos"
        
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
            "modulo": "Inventario",
            "detalle": detalle,
            "fecha": datetime.datetime.now().isoformat()
        }
        try:
            self.supabase_nativo.table("logs_sistema").insert(log_data).execute()
        except:
            pass

    def generar_pdf_catalogo_general(self, productos_list, fecha_inicio, fecha_fin, mostrar_precio=True):
        """Genera un catálogo en PDF en formato de lista limpia (1 columna) con portada y logo corporativo local."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # --- ESTILOS DE LA PORTADA ---
        cover_title_style = ParagraphStyle(
            'CoverTitle', parent=styles['Heading1'], fontSize=30, leading=36,
            textColor=colors.HexColor("#1A252F"), alignment=1, spaceAfter=15, fontName="Helvetica-Bold"
        )
        cover_subtitle_style = ParagraphStyle(
            'CoverSubtitle', parent=styles['Normal'], fontSize=13, leading=18,
            textColor=colors.HexColor("#7F8C8D"), alignment=1, spaceAfter=40
        )
        cover_date_label = ParagraphStyle(
            'CoverDateLabel', parent=styles['Normal'], fontSize=11, leading=15,
            textColor=colors.HexColor("#34495E"), alignment=1, fontName="Helvetica-Bold"
        )
        cover_date_val = ParagraphStyle(
            'CoverDateVal', parent=styles['Normal'], fontSize=13, leading=18,
            textColor=colors.HexColor("#2980B9"), alignment=1, fontName="Helvetica-Bold", spaceAfter=25
        )
        cover_footer_style = ParagraphStyle(
            'CoverFooter', parent=styles['Normal'], fontSize=9, leading=13,
            textColor=colors.HexColor("#95A5A6"), alignment=1
        )
        
        # --- ESTILOS DEL CUERPO ---
        title_style = ParagraphStyle(
            'CatalogTitle', parent=styles['Heading1'], fontSize=22, leading=26,
            textColor=colors.HexColor("#2C3E50"), alignment=0, spaceAfter=5, fontName="Helvetica-Bold"
        )
        meta_style = ParagraphStyle(
            'ProdMeta', parent=styles['Normal'], fontSize=10, leading=15, 
            textColor=colors.HexColor("#2C3E50")
        )
        vigencia_style = ParagraphStyle(
            'ProdVigencia', parent=styles['Normal'], fontSize=11, leading=15, 
            textColor=colors.HexColor("#C0392B"), fontName="Helvetica-Bold", alignment=0, spaceAfter=20
        )
        price_style = ParagraphStyle(
            'ProdPrice', parent=styles['Normal'], fontSize=14, leading=18, 
            textColor=colors.HexColor("#27AE60"), fontName="Helvetica-Bold", alignment=2
        )

        story = []
        
        # ==========================================
        # 1. PORTADA MEJORADA & LOGO LOCAL
        # ==========================================
        story.append(Spacer(1, 30))
        
        logo_flowable = None
        # Buscar logo en la raíz o sesión
        try:
            if os.path.exists("logo.png"):
                logo_flowable = RLImage("logo.png", width=180, height=180, kind='proportional')
            else:
                logo_empresa = st.session_state.get('logo_empresa_url') or st.session_state.get('empresa_logo')
                if logo_empresa:
                    if str(logo_empresa).startswith("data:image"):
                        header, encoded = str(logo_empresa).split(",", 1)
                        img_data = base64.b64decode(encoded)
                        logo_flowable = RLImage(io.BytesIO(img_data), width=180, height=180, kind='proportional')
                    elif str(logo_empresa).startswith("http"):
                        response = requests.get(logo_empresa, timeout=3)
                        if response.status_code == 200:
                            logo_flowable = RLImage(io.BytesIO(response.content), width=180, height=180, kind='proportional')
        except Exception as e:
            logo_flowable = None
                
        if logo_flowable:
            logo_table = Table([[logo_flowable]], colWidths=[500])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 30)
            ]))
            story.append(logo_table)
        else:
            story.append(Paragraph("🏢", ParagraphStyle('EmojiLogo', fontSize=70, alignment=1, spaceAfter=25)))
            
        story.append(Paragraph("CATÁLOGO OFICIAL DE PRODUCTOS", cover_title_style))
        story.append(Paragraph("PORTAFOLIO DE INVENTARIO Y FICHA LOGÍSTICA", cover_subtitle_style))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph("PERÍODO DE VIGENCIA", cover_date_label))
        vigencia_texto = f"DESDE: {fecha_inicio.strftime('%d/%m/%Y')} &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; HASTA: {fecha_fin.strftime('%d/%m/%Y')}"
        story.append(Paragraph(vigencia_texto, cover_date_val))
        
        story.append(Spacer(1, 140))
        story.append(Paragraph(f"Documento generado de forma automatizada el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", cover_footer_style))
        story.append(Paragraph("Información de inventario confidencial y de uso comercial exclusivo.", cover_footer_style))
        
        story.append(PageBreak())
        
        # ==========================================
        # 2. CUERPO DEL CATÁLOGO (DISEÑO AMPLIO - 1 COLUMNA)
        # ==========================================
        story.append(Paragraph("📋 PORTAFOLIO DE INVENTARIO", title_style))
        story.append(Paragraph(f"Período de Validez: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}", vigencia_style))
        
        for item in productos_list:
            if not isinstance(item, dict):
                continue
            
            img_url = item.get('IMAGEN')
            img_flowable = None
            
            if img_url:
                try:
                    if str(img_url).startswith("data:image"):
                        header, encoded = str(img_url).split(",", 1)
                        img_data = base64.b64decode(encoded)
                        img_flowable = RLImage(io.BytesIO(img_data), width=85, height=85, kind='proportional')
                    elif str(img_url).startswith("http"):
                        response = requests.get(img_url, timeout=3)
                        if response.status_code == 200:
                            img_flowable = RLImage(io.BytesIO(response.content), width=85, height=85, kind='proportional')
                except:
                    img_flowable = None
                    
            if not img_flowable:
                img_flowable = Paragraph("<font color='#95A5A6'>[ Sin Imagen ]</font>", ParagraphStyle('NoImg', fontName='Helvetica-Oblique', fontSize=9, alignment=1))

            ref = item.get('REFERENCIA') or "S/R"
            desc = item.get('DESCRIPCION') or ""
            marca = item.get('MARCA') or "N/A"
            costo = item.get('COSTO UNIT') or 0.0
            cb = item.get('codigo_barra') or ""
            
            empaque = item.get('EMPAQUE') or ""
            peso = item.get('PESO') or ""
            cant_caja = item.get('CANTIDAD CAJA') or ""
            
            tag_cb = f"&nbsp;&nbsp;|&nbsp;&nbsp;<b>EAN:</b> {cb}" if cb else ""
            tag_logistica = f"<br/><font color='#7F8C8D'><b>Empaque:</b> {empaque} &nbsp;&nbsp;•&nbsp;&nbsp; <b>Caja:</b> {cant_caja} &nbsp;&nbsp;•&nbsp;&nbsp; <b>Peso:</b> {peso}</font>" if (empaque or peso or cant_caja) else ""
            
            info_html = f"<font size=12><b>{ref}</b></font> &nbsp;&nbsp; ({marca})<br/>{desc}{tag_cb}{tag_logistica}"
            precio_html = f"<font size=14>${float(costo):,.2f}</font><br/><font size=8 color='gray'>P.U. Neto</font>" if mostrar_precio else ""
            
            fila_producto_data = [
                [img_flowable, Paragraph(info_html, meta_style), Paragraph(precio_html, price_style)]
            ]
            
            tarjeta_producto = Table(fila_producto_data, colWidths=[90, 310, 100])
            tarjeta_producto.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('TOPPADDING', (0, 0), (-1, -1), 14),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ]))
            
            story.append(tarjeta_producto)
            
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def render(self):
        st.header("📦 Gestión de Inventario")
        
        prods = []
        try:
            response = self.supabase_nativo.table(self.tabla).select("*").order("ID").execute()
            if response and hasattr(response, 'data') and isinstance(response.data, list):
                prods = [dict(p) for p in response.data if isinstance(p, dict)]
        except Exception as e:
            st.error(f"Error crítico al leer datos de Supabase: {e}")
            prods = []
            
        df = pd.DataFrame(prods) if prods else pd.DataFrame()

        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Existencias Actuales", 
            "➕ Nuevo Producto", 
            "🛠️ Modificar / Actualizar",
            "🖨️ Catálogo General"
        ])

        # TAB 1: EXISTENCIAS
        with tab1:
            st.subheader("📋 Existencias en Planta e Inventario")
            if not df.empty:
                df_visual = df.copy()
                if 'codigo_barra' in df_visual.columns:
                    df_visual['codigo_barra'] = df_visual['codigo_barra'].fillna(0).astype(str).str.replace('.0', '', regex=False)
                
                # Exclusión absoluta del Historial de Entradas e ID en la visualización
                columnas_ocultas = {"ID": None, "ENTRADA 2019": None, "ENTRADA 2024": None, "ENTRADA 2025": None}
                column_config_limpia = {k: v for k, v in columnas_ocultas.items() if k in df_visual.columns}

                st.dataframe(
                    df_visual, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config=column_config_limpia
                )
            else:
                st.info("No hay productos registrados en el inventario.")

        # TAB 2: NUEVO PRODUCTO
        with tab2:
            st.subheader("➕ Registrar Nuevo Producto")
            
            archivo_imagen = st.file_uploader("🖼️ Cargar Foto del Producto (JPG/PNG)", type=["jpg", "png", "jpeg"], key="upload_nuevo")
            string_imagen = None
            if archivo_imagen:
                bytes_data = archivo_imagen.read()
                base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                string_imagen = f"data:image/jpeg;base64,{base64_encoded}"
                st.image(bytes_data, width=120, caption="Vista previa de la foto")

            with st.form("form_nuevo_producto", clear_on_submit=False):
                c_top1, c_top2 = st.columns(2)
                referencia = c_top1.text_input("Referencia / Código Interno *").strip().upper()
                cod_barra = c_top2.text_input("🔢 Código de Barras")

                c1, c2 = st.columns(2)
                marca = c1.text_input("Marca").strip().upper()
                tipo = c2.text_input("Tipo de Producto").strip().upper()
                ubicacion = c1.text_input("Ubicación en Bodega").strip().upper()
                
                descripcion = st.text_area("Descripción Comercial del Producto *").strip().upper()
                
                # --- INFORMACIÓN LOGÍSTICA / EMBALAJE ---
                st.write("📦 **Detalles de Empaque y Logística**")
                c_log1, c_log2, c_log3, c_log4 = st.columns(4)
                empaque = c_log1.text_input("Empaque (Ej: Caja/Bolsa)").strip().upper()
                cant_caja = c_log2.text_input("Cantidad por Caja").strip().upper()
                peso = c_log3.text_input("Peso (Kg/Lbs)").strip().upper()
                cubicaje = c_log4.text_input("Cubicaje (m³)").strip().upper()
                
                st.write("💵 **Valores y Stock**")
                c3, c4, c5 = st.columns(3)
                cantidad = c3.number_input("Cantidad Inicial", min_value=0.0, value=0.0)
                um = c4.text_input("Unidad de Medida (U/M)", value="PCS").strip().upper()
                costo = c5.number_input("Costo Unitario ($)", min_value=0.0, value=0.0, format="%.2f")

                if st.form_submit_button("💾 Guardar en Inventario", use_container_width=True):
                    if referencia and descripcion:
                        cb_numeric = None
                        if cod_barra.strip().isdigit():
                            cb_numeric = int(cod_barra.strip())

                        nuevo_p = {
                            "REFERENCIA": referencia,
                            "MARCA": marca,
                            "TIPO": tipo,
                            "UBICACIÓN": ubicacion,
                            "DESCRIPCION": descripcion,
                            "EMPAQUE": empaque if empaque else None,
                            "CANTIDAD CAJA": cant_caja if cant_caja else None,
                            "PESO": peso if peso else None,
                            "CUBICAJE": cubicaje if cubicaje else None,
                            "CANTIDAD": cantidad,
                            "U/M": um,
                            "COSTO UNIT": costo,
                            "TOTAL": cantidad * costo,
                            "IMAGEN": string_imagen if string_imagen else None,
                            "codigo_barra": cb_numeric
                        }
                        try:
                            self.supabase_nativo.table(self.tabla).insert(nuevo_p).execute()
                            self.registrar_log("Creación", f"Producto REF: {referencia} guardado con éxito.")
                            st.success(f"✅ Producto {referencia} registrado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                    else:
                        st.warning("⚠️ La Referencia y la Descripción son obligatorias.")

        # TAB 3: MODIFICAR / ACTUALIZAR
        with tab3:
            st.subheader("🛠️ Modificar Producto Existente")
            if prods:
                opciones_prod = {}
                for p in prods:
                    try:
                        p_id = p.get('ID')
                        if p_id is None:
                            continue
                        ref_str = str(p.get('REFERENCIA') or 'SIN REF')
                        desc_str = str(p.get('DESCRIPCION') or 'SIN DESCRIPCION')
                        label = f"{ref_str} - {desc_str[:35]}..."
                        opciones_prod[label] = p
                    except:
                        continue
                
                seleccion = st.selectbox("Seleccione el producto a editar:", ["-- Seleccionar --"] + list(opciones_prod.keys()))
                
                if seleccion != "-- Seleccionar --":
                    p_sel = opciones_prod[seleccion]
                    
                    archivo_imagen_edit = st.file_uploader("🖼️ Cambiar/Reemplazar Foto del Producto", type=["jpg", "png", "jpeg"], key="upload_edit")
                    string_imagen_edit = p_sel.get('IMAGEN')
                    
                    if archivo_imagen_edit:
                        bytes_data_edit = archivo_imagen_edit.read()
                        base64_encoded_edit = base64.b64encode(bytes_data_edit).decode("utf-8")
                        string_imagen_edit = f"data:image/jpeg;base64,{base64_encoded_edit}"
                        st.image(bytes_data_edit, width=120, caption="Nueva foto cargada")

                    with st.form(f"form_edit_{p_sel.get('ID', 'unique')}"):
                        st.write(f"✍️ Editando Referencia: **{p_sel.get('REFERENCIA')}**")
                        
                        val_cb_str = ""
                        if p_sel.get('codigo_barra'):
                            val_cb_str = str(p_sel.get('codigo_barra')).replace('.0', '')
                        
                        ec_top1, ec_top2 = st.columns(2)
                        e_ref = ec_top1.text_input("Referencia", value=str(p_sel.get('REFERENCIA') or ''))
                        e_cb = ec_top2.text_input("🔢 Código de Barras", value=val_cb_str)

                        ec1, ec2 = st.columns(2)
                        e_marca = ec1.text_input("Marca", value=str(p_sel.get('MARCA') or ''))
                        e_tipo = ec2.text_input("Tipo", value=str(p_sel.get('TIPO') or ''))
                        e_ubi = ec1.text_input("Ubicación", value=str(p_sel.get('UBICACIÓN') or ''))
                        
                        e_desc = st.text_area("Descripción", value=str(p_sel.get('DESCRIPCION') or ''))

                        # --- INFORMACIÓN LOGÍSTICA EDICIÓN ---
                        st.write("📦 **Detalles de Empaque y Logística**")
                        ec_log1, ec_log2, ec_log3, ec_log4 = st.columns(4)
                        e_empaque = ec_log1.text_input("Empaque", value=str(p_sel.get('EMPAQUE') or ''))
                        e_cant_caja = ec_log2.text_input("Cantidad por Caja", value=str(p_sel.get('CANTIDAD CAJA') or ''))
                        e_peso = ec_log3.text_input("Peso", value=str(p_sel.get('PESO') or ''))
                        e_cubicaje = ec_log4.text_input("Cubicaje", value=str(p_sel.get('CUBICAJE') or ''))
                        
                        st.write("💵 **Valores y Stock**")
                        ec3, ec4, ec5 = st.columns(3)
                        
                        try: val_cant = float(p_sel.get('CANTIDAD') or 0.0)
                        except: val_cant = 0.0
                        try: val_costo = float(p_sel.get('COSTO UNIT') or 0.0)
                        except: val_costo = 0.0

                        e_cant = ec3.number_input("Cantidad", min_value=0.0, value=val_cant)
                        e_um = ec4.text_input("U/M", value=str(p_sel.get('U/M') or 'PCS'))
                        e_costo = ec5.number_input("Costo Unitario ($)", min_value=0.0, value=val_costo, format="%.2f")

                        if st.form_submit_button("💾 Actualizar Cambios", use_container_width=True):
                            cb_numeric_edit = None
                            if e_cb.strip().isdigit():
                                cb_numeric_edit = int(e_cb.strip())

                            upd_p = {
                                "REFERENCIA": e_ref.upper(),
                                "MARCA": e_marca.upper(),
                                "TIPO": e_tipo.upper(),
                                "UBICACIÓN": e_ubi.upper(),
                                "DESCRIPCION": e_desc.upper(),
                                "EMPAQUE": e_empaque if e_empaque else None,
                                "CANTIDAD CAJA": e_cant_caja if e_cant_caja else None,
                                "PESO": e_peso if e_peso else None,
                                "CUBICAJE": e_cubicaje if e_cubicaje else None,
                                "CANTIDAD": e_cant,
                                "U/M": e_um.upper(),
                                "COSTO UNIT": e_costo,
                                "TOTAL": e_cant * e_costo,
                                "IMAGEN": string_imagen_edit,
                                "codigo_barra": cb_numeric_edit
                            }
                            try:
                                self.supabase_nativo.table(self.tabla).update(upd_p).eq("ID", p_sel['ID']).execute()
                                self.registrar_log("Edición", f"Producto ID {p_sel['ID']} modificado.")
                                st.success("¡Cambios aplicados correctamente!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar: {e}")
            else:
                st.info("No hay productos disponibles para modificar.")

        # TAB 4: CATÁLOGO GENERAL
        with tab4:
            st.subheader("🖨️ Impresión de Catálogo Comercial Global")
            st.write("Genera un documento PDF corporativo que incluye **Portada Ejecutiva**, Logo y los rangos de vigencia.")
            
            if prods:
                col_c1, col_c2 = st.columns(2)
                cat_precios = col_c1.checkbox("💲 Incluir precios de costo/lista actuales", value=True, key="chk_gen_precios")
                
                st.write("📆 **Período de Validez del Portafolio**")
                col_f1, col_f2 = st.columns(2)
                fecha_inicio = col_f1.date_input("Fecha de Inicio de Vigencia", value=datetime.date.today())
                fecha_fin = col_f2.date_input("Fecha de Fin de Vigencia", value=datetime.date.today() + datetime.timedelta(days=30))
                
                st.markdown(" ")
                if st.button("✨ Compilar Catálogo de Todo el Stock", type="primary", use_container_width=True):
                    if fecha_fin < fecha_inicio:
                        st.error("Error: La fecha de fin de vigencia no puede ser anterior a la fecha de inicio.")
                    else:
                        with st.spinner("Diseñando portada exclusiva y estructurando fichas técnicas..."):
                            pdf_global_bytes = self.generar_pdf_catalogo_general(
                                prods, 
                                fecha_inicio=fecha_inicio, 
                                fecha_fin=fecha_fin, 
                                mostrar_precio=cat_precios
                            )
                            
                            st.download_button(
                                label="📥 Descargar PDF de Catálogo Comercial",
                                data=pdf_global_bytes,
                                file_name=f"catalogo_vigencia_{fecha_inicio.isoformat()}_al_{fecha_fin.isoformat()}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("¡Catálogo generado con Portada Oficial y Vigencias integradas!")
            else:
                st.warning("No hay productos cargados en el inventario para poder exportar un catálogo.")