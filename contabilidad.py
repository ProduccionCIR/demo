# contabilidad.py
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64
import os
import logging

# Configuración formal del sistema de logs para RAV System
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ModuloContabilidad")

class ModuloContabilidad:
    def __init__(self, db):
        self.db = db
        self.logo_path = "logo.png"
        logger.info("Módulo de Contabilidad y Finanzas inicializado correctamente.")

    def get_image_base64(self, path):
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"No se pudo cargar la imagen del logo en {path}: {e}")
            return None

    def generar_formato_impresion(self, titulo, datos):
        """Genera comprobantes y recibos con el formato formal corporativo idéntico al de las facturas"""
        if not datos:
            logger.warning("Intento de impresión fallido: el diccionario de datos está vacío.")
            return "<div>No hay datos para imprimir</div>"
            
        titulo_str = str(titulo if titulo is not None else "DOCUMENTO")
            
        logo_b64 = self.get_image_base64(self.logo_path)
        fecha = str(datos.get('fecha', ''))[:10] if datos.get('fecha') else pd.Timestamp.now().strftime("%Y-%m-%d")
        folio = str(datos.get('id', datos.get('num_recibo', '000')))
        
        raw_sujeto = datos.get('cliente') or datos.get('descripcion') or datos.get('banco') or "CLIENTE CONTADO"
        sujeto = str(raw_sujeto if raw_sujeto is not None else "CLIENTE CONTADO")
        
        val_monto = datos.get('total') or datos.get('monto') or datos.get('monto_abono')
        monto = float(val_monto) if val_monto is not None else 0.0
        
        raw_concepto = datos.get('nota') or datos.get('concepto') or datos.get('descripcion') or datos.get('referencia') or "PAGO GENERAL A CUENTA"
        concepto = str(raw_concepto if raw_concepto is not None else "PAGO GENERAL A CUENTA")

        metodo_pago = str(datos.get('metodo_pago', 'EFECTIVO'))
        
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 55px;" alt="Logo">' if logo_b64 else '<div style="font-size: 28pt; font-weight: bold; font-family: serif; border: 2px solid #000; padding: 2px 10px; display: inline-block;">D</div><div style="font-size: 6pt; font-weight: bold; margin-top: 2px;">DANA INTERNACIONAL S.A</div>'

        html_content = ""
        for i in range(2):
            tipo_copia = "ORIGINAL CLIENTE" if i == 0 else "COPIA CONTABILIDAD"
            html_content += f"""
            <div style="font-family: Arial, sans-serif; padding: 25px; color: #1e293b; max-width: 800px; margin: 0 auto 40px auto; border: 1px solid #cbd5e1; background: #ffffff; position: relative;">
                <div style="text-align: right; font-size: 8pt; font-weight: bold; color: #64748b; margin-bottom: 5px;">{tipo_copia}</div>
                
                <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #0f172a; padding-bottom: 12px; margin-bottom: 15px;">
                    <div style="width: 35%; text-align: left;">{logo_html}</div>
                    <div style="width: 65%; text-align: right; font-size: 8.5pt; color: #333; line-height: 1.3;">
                        <strong style="font-size: 11pt; color: #0f172a;">DANA INTERNACIONAL</strong><br>
                        RUC: 12440-181-123510 DV83 | TEL: 446-1326<br>
                        CALLE 15 & 16, ZONA LIBRE DE COLÓN, REP. DE PANAMÁ
                    </div>
                </div>
                
                <div style="background-color: #0f172a; color: #ffffff; text-align: center; padding: 8px; font-weight: bold; font-size: 11pt; letter-spacing: 0.5px; margin-bottom: 15px; text-transform: uppercase;">
                    {titulo_str}
                </div>

                <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                    <div style="flex: 2; border: 1px solid #cbd5e1; padding: 10px; background: #f8fafc;">
                        <div style="font-size: 8.5pt; color: #64748b; font-weight: bold; margin-bottom: 4px;">CLIENTE:</div>
                        <div style="font-size: 10pt; font-weight: bold; text-transform: uppercase;">{sujeto}</div>
                        <div style="font-size: 8.5pt; margin-top: 8px;"><strong>CONCEPTO:</strong> {concepto}</div>
                        <div style="font-size: 8.5pt; margin-top: 4px;"><strong>MÉTODO DE PAGO:</strong> {metodo_pago}</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #cbd5e1; padding: 10px; background: #f8fafc; font-size: 9pt;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #64748b; font-weight: bold;">RECIBO N°:</span>
                            <span style="font-weight: bold; color: #d32f2f;">{folio}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="color: #64748b; font-weight: bold;">FECHA:</span>
                            <span>{fecha}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #64748b; font-weight: bold;">TIPO:</span>
                            <span>MANUAL</span>
                        </div>
                    </div>
                </div>

                <div style="margin-bottom: 15px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 9pt;">
                        <thead>
                            <tr style="background-color: #e2e8f0; color: #0f172a; text-align: left; font-size: 8.5pt; border-bottom: 2px solid #cbd5e1;">
                                <th style="padding: 8px 10px; width: 60%;">DESCRIPCIÓN DEL MOVIMIENTO</th>
                                <th style="padding: 8px 10px; text-align: right; width: 20%;">SALDO ANTERIOR</th>
                                <th style="padding: 8px 10px; text-align: right; width: 20%;">MONTO ABONADO</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 10px; text-transform: uppercase;">{concepto}</td>
                                <td style="padding: 10px; text-align: right;">$ 0.00</td>
                                <td style="padding: 10px; text-align: right; font-weight: bold;">$ {monto:,.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div style="display: flex; gap: 10px; align-items: flex-start; margin-bottom: 30px;">
                    <div style="flex: 1.5; border: 1px solid #cbd5e1; padding: 10px; background: #f8fafc; font-size: 8.5pt;">
                        <strong style="color: #0f172a; display: block; margin-bottom: 5px; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px;">INFORMACIÓN DE CONTROL:</strong>
                        <div>Asociado a Factura N°: S/N</div>
                        <div>Estado Final Factura: PROCESADO</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #cbd5e1; padding: 10px; background: #f8fafc; font-size: 9pt;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #475569;">
                            <span>SALDO ANTERIOR:</span>
                            <span>$ 0.00</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px;">
                            <span>TOTAL ABONADO:</span>
                            <span>$ {monto:,.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 11pt; color: #047857;">
                            <span>SALDO RESTANTE:</span>
                            <span>$ 0.00</span>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 40px; padding: 0 20px;">
                    <div style="width: 40%; border-top: 1.5px solid #a0aec0; text-align: center; font-size: 8.5pt; color: #4a5568; padding-top: 6px;">
                        Recibido Conforme (Cajero/a)
                    </div>
                    <div style="width: 40%; border-top: 1.5px solid #a0aec0; text-align: center; font-size: 8.5pt; color: #4a5568; padding-top: 6px;">
                        Firma Autorizada
                    </div>
                </div>

                <div style="margin-top: 25px; text-align: center; font-size: 7.5pt; color: #94a3b8; font-weight: bold;">
                    SISTEMA RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO
                </div>
            </div>
            """
        logger.info(f"Formato de impresión generado con éxito para el documento: {folio} ({titulo_str})")
        return f"<div>{html_content}</div><script>window.print();</script>"

    def generar_informe_hoja_unica(self, titulo, datos, items_detalle=None):
        """Genera una plantilla de Reporte Ejecutivo formal con la lista explícita de documentos incluidos"""
        if not datos:
            logger.warning("Intento de generar informe de hoja única fallido: no hay datos proporcionados.")
            return "<div>No hay datos para generar el informe</div>"

        titulo_str = str(titulo if titulo is not None else "INFORME_GENERAL")
        fecha_str_base = str(datos.get('fecha', ''))[:10] if datos.get('fecha') else pd.Timestamp.now().strftime("%Y-%m-%d")
        
        safe_titulo_for_replace = str(titulo_str if titulo_str is not None else "INFORME")
        nombre_descarga = f"{safe_titulo_for_replace.replace(' ', '_')}_{fecha_str_base}"

        logo_b64 = self.get_image_base64(self.logo_path)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 55px;" alt="Logo">' if logo_b64 else ""

        tabla_items_html = ""
        if items_detalle and len(items_detalle) > 0:
            filas_html = ""
            for item in items_detalle:
                if item is not None:
                    raw_id = item.get('num_recibo') or item.get('num_factura') or item.get('id') or 'S/N'
                    doc_id = str(raw_id if raw_id is not None else 'S/N')
                    
                    doc_fecha = str(item.get('fecha', ''))[:10]
                    
                    raw_sujeto = item.get('cliente') or item.get('banco') or item.get('descripcion') or 'GENERAL'
                    doc_sujeto_str = str(raw_sujeto if raw_sujeto is not None else 'GENERAL')
                    if len(doc_sujeto_str) > 30:
                        doc_sujeto_str = doc_sujeto_str[:28] + ".."
                    
                    raw_ref = item.get('referencia') or item.get('metodo_pago') or item.get('concepto') or item.get('descripcion') or 'Registro'
                    doc_ref_str = str(raw_ref if raw_ref is not None else 'Registro')
                    if len(doc_ref_str) > 35:
                        doc_ref_str = doc_ref_str[:33] + ".."
                        
                    raw_item_monto = item.get('monto_abono') or item.get('monto') or item.get('total')
                    doc_monto = float(raw_item_monto) if raw_item_monto is not None else 0.0

                    filas_html += f"""
                    <tr style="border-bottom: 1px solid #e2e8f0; font-size: 9pt;">
                        <td style="padding: 6px 10px; font-family: monospace; font-weight: bold;">#{doc_id}</td>
                        <td style="padding: 6px 10px;">{doc_fecha}</td>
                        <td style="padding: 6px 10px; text-transform: uppercase;">{doc_sujeto_str}</td>
                        <td style="padding: 6px 10px; font-style: italic; color: #4a5568;">{doc_ref_str}</td>
                        <td style="padding: 6px 10px; text-align: right; font-weight: bold;">$ {doc_monto:,.2f}</td>
                    </tr>
                    """
            tabla_items_html = f"""
            <div style="margin-top: 20px;">
                <h3 style="font-size: 11pt; border-bottom: 2px solid #333; padding-bottom: 5px;">DETALLE DE TRANSACCIONES</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background: #f1f5f9; text-align: left; font-size: 8pt; border-bottom: 2px solid #cbd5e1;">
                            <th style="padding: 8px;">N° DOC</th>
                            <th style="padding: 8px;">FECHA</th>
                            <th style="padding: 8px;">SUJETO</th>
                            <th style="padding: 8px;">REFERENCIA / CONCEPTO</th>
                            <th style="padding: 8px; text-align: right;">MONTO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>
            </div>
            """

        raw_total_datos = datos.get('total')
        monto_total = float(raw_total_datos) if raw_total_datos is not None else 0.0
        
        raw_nota = datos.get('nota') or "Cierre del periodo fiscal"
        concepto_total = str(raw_nota if raw_nota is not None else "Cierre del periodo fiscal")

        logger.info(f"Informe ejecutivo de hoja única generado: {titulo_str} con {len(items_detalle) if items_detalle else 0} registros asociados.")
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 25px; color: #1e293b; max-width: 800px; margin: auto; border: 1px solid #cbd5e1; background: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 15px;">
                <div>{logo_html}</div>
                <div style="text-align: right; font-size: 8pt; color: #475569;">
                    <strong style="font-size: 11pt; color: #0f172a;">DANA INTERNACIONAL</strong><br>
                    ZONA LIBRE DE COLÓN, PANAMÁ<br>
                    FECHA DE EMISIÓN: {fecha_str_base}
                </div>
            </div>
            <div style="margin: 20px 0; text-align: center;">
                <h2 style="margin: 0; color: #0f172a; text-transform: uppercase; font-size: 14pt;">{titulo_str}</h2>
            </div>
            <div style="background: #f8fafc; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px;">
                <p style="margin: 4px 0;"><strong>Concepto General:</strong> {concepto_total}</p>
                <p style="margin: 4px 0;"><strong>Monto Acumulado / Total:</strong> <span style="font-size: 12pt; color: #047857; font-weight: bold;">$ {monto_total:,.2f}</span></p>
            </div>
            {tabla_items_html}
            <div style="margin-top: 40px; display: flex; justify-content: space-between;">
                <div style="width: 45%; border-top: 1px solid #94a3b8; text-align: center; font-size: 8pt; padding-top: 5px; color: #475569;">ELABORADO POR</div>
                <div style="width: 45%; border-top: 1px solid #94a3b8; text-align: center; font-size: 8pt; padding-top: 5px; color: #475569;">APROBADO / GERENCIA</div>
            </div>
            <div style="margin-top: 30px; text-align: center; font-size: 7pt; color: #94a3b8;">RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO</div>
        </div>
        <script>window.print();</script>
        """

    def eliminar_factura(self, factura):
        """Elimina la factura de forma segura y devuelve el stock (formateado como entero)"""
        if not factura or 'id' not in factura:
            logger.warning("Intento de eliminar factura inválida o sin ID.")
            st.error("No se puede eliminar una factura sin un identificador válido.")
            return
            
        try:
            detalle = factura.get('detalles') or factura.get('detalle', [])
            for item in detalle:
                ref_prod = item.get('id') or item.get('REFERENCIA')
                raw_cant = item.get('cantidad') or item.get('CANTIDAD')
                cant_prod = float(raw_cant) if raw_cant is not None else 0.0
                
                if ref_prod:
                    res = self.db.client.table("productos").select("CANTIDAD").eq("REFERENCIA", ref_prod).execute()
                    if res and res.data:
                        raw_bd_cant = res.data[0].get('CANTIDAD')
                        bd_cant_float = float(raw_bd_cant) if raw_bd_cant is not None else 0.0
                        nueva_q = int(bd_cant_float + cant_prod)
                        self.db.client.table("productos").update({"CANTIDAD": nueva_q}).eq("REFERENCIA", ref_prod).execute()
            
            num_f_asoc = factura.get('num_factura') or factura['id']
            self.db.client.table("recibos").delete().eq("id_venta", num_f_asoc).execute()
            self.db.client.table("ventas").delete().eq("id", factura['id']).execute()
            logger.info(f"Factura #{factura['id']} eliminada exitosamente y stock restaurado en inventario.")
            st.success(f"Factura #{factura['id']} eliminada y stock restaurado de manera exitosa.")
            st.rerun()
        except Exception as e:
            logger.error(f"Error crítico al eliminar la factura #{factura.get('id')}: {e}")
            st.error(f"Error al eliminar la factura de la base de datos: {e}")

    def eliminar_recibo(self, recibo):
        """Elimina un recibo y actualiza el estado de la factura asociada si corresponde"""
        if not recibo or 'id' not in recibo:
            logger.warning("Intento de eliminar recibo con ID inválido.")
            st.error("Identificador de recibo inválido.")
            return
            
        try:
            id_recibo = recibo['id']
            id_venta_asoc = recibo.get('id_venta')
            
            self.db.client.table("recibos").delete().eq("id", id_recibo).execute()
            
            if id_venta_asoc:
                self.db.client.table("ventas").update({"estado": "PENDIENTE"}).eq("num_factura", id_venta_asoc).execute()
                
            logger.info(f"Recibo ID {id_recibo} eliminado correctamente. Venta asociada #{id_venta_asoc} marcada como PENDIENTE.")
            st.success("Recibo eliminado de forma correcta.")
            st.rerun()
        except Exception as e:
            logger.error(f"Error crítico al eliminar el recibo ID {recibo.get('id')}: {e}")
            st.error(f"Error al eliminar el recibo solicitado: {e}")

    def render(self):
        st.header("📊 Contabilidad y Finanzas")
        
        # 1. CARGA DE DATOS SEGUROS
        ventas = self.db.fetch("ventas") or []
        recibos = self.db.fetch("recibos") or []
        gastos = self.db.fetch("gastos") or []
        depositos = self.db.fetch("depositos") or []

        # 2. MÉTRICAS GENERALES BLINDADAS CON VALORES DE RESPALDO SEGUROS
        t_ingresos = sum(float(v.get('total') or 0.0) for v in ventas if v and v.get('total') is not None)
        t_gastos = sum(float(g.get('monto') or 0.0) for g in gastos if g and g.get('monto') is not None)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales Historicas", f"${t_ingresos:,.2f}")
        c2.metric("Gastos Totales", f"${t_gastos:,.2f}", delta_color="inverse")
        c3.metric("Utilidad Bruta", f"${(t_ingresos - t_gastos):,.2f}")

        # 3. CONTROL SEGURO DE CUENTAS POR COBRAR (CXC)
        st.divider()
        st.subheader("🔍 Cuentas por Cobrar (CXC)")
        if ventas:
            df_v = pd.DataFrame(ventas)
            if 'total' in df_v.columns:
                df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0.0)
                
            if recibos:
                df_r = pd.DataFrame(recibos)
                monto_col = 'monto_abono' if 'monto_abono' in df_r.columns else ('monto' if 'monto' in df_r.columns else None)
                if monto_col and 'id_venta' in df_r.columns:
                    df_r[monto_col] = pd.to_numeric(df_r[monto_col], errors='coerce').fillna(0.0)
                    p_pagos = df_r.groupby('id_venta')[monto_col].sum().reset_index()
                    p_pagos.columns = ['id_venta', 'total_pagado']
                else:
                    p_pagos = pd.DataFrame(columns=['id_venta', 'total_pagado'])
            else:
                p_pagos = pd.DataFrame(columns=['id_venta', 'total_pagado'])
                
            if 'num_factura' in df_v.columns and not p_pagos.empty:
                cxc_df = pd.merge(df_v, p_pagos, left_on='num_factura', right_on='id_venta', how='left').fillna(0)
            else:
                cxc_df = df_v.copy()
                cxc_df['total_pagado'] = 0.0
                
            cxc_df['saldo'] = cxc_df['total'] - cxc_df['total_pagado']
            
            if 'estado' in cxc_df.columns:
                pendientes = cxc_df[(cxc_df['saldo'] > 0.01) & (cxc_df['estado'] != 'PAGADA')]
            else:
                pendientes = cxc_df[cxc_df['saldo'] > 0.01]
                
            if not pendientes.empty:
                st.error(f"Pendiente de cobro en cartera: ${float(pendientes['saldo'].sum()):,.2f}")
                with st.expander("Ver detalle CXC"):
                    for _, p in pendientes.iterrows():
                        num_f_vis = p.get('num_factura') or p.get('id', 0)
                        st.write(f"📌 {p.get('cliente', 'S/N')} | Factura #{int(float(num_f_vis))} | **Saldo Pendiente: ${float(p['saldo']):,.2f}**")
            else:
                st.success("✅ Cartera al día.")

        # 4. PESTAÑAS PRINCIPALES
        tabs = st.tabs(["📉 Gastos", "🏦 Depósitos", "📄 Recibos", "📑 Historial Facturas", "🔒 Cierre e Informes"])

        with tabs[0]: # GASTOS
            with st.form("f_g"):
                m, d = st.columns([1,2])
                monto_g = m.number_input("Monto $", min_value=0.0, format="%.2f")
                desc_g = d.text_input("Descripción")
                if st.form_submit_button("💾 Guardar Gasto"):
                    if monto_g > 0 and desc_g:
                        try:
                            self.db.insert("gastos", {"monto": monto_g, "descripcion": desc_g.upper(), "fecha": pd.Timestamp.now().isoformat()})
                            logger.info(f"Gasto registrado con éxito: ${monto_g:,.2f} - {desc_g.upper()}")
                            st.success("Gasto guardado correctamente.")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error al registrar gasto en BD: {e}")
                            st.error(f"No se pudo guardar el gasto: {e}")
                    else:
                        st.warning("Debe ingresar un monto y una descripción válidos.")
            for idx, g in enumerate(gastos):
                if g:
                    g_id = g.get('id', idx)
                    with st.container(border=True):
                        c1, c2 = st.columns([5, 1])
                        raw_g_monto = g.get('monto')
                        g_monto_float = float(raw_g_monto) if raw_g_monto is not None else 0.0
                        c1.write(f"📅 {str(g.get('fecha',''))[:10]} | **{g.get('descripcion', 'GASTO')}** | ${g_monto_float:,.2f}")
                        if c2.button("🖨️", key=f"pg_{g_id}"):
                            st.session_state.print_html = self.generar_formato_impresion("COMPROBANTE DE GASTO", g)

        with tabs[1]: # DEPÓSITOS
            with st.form("f_d"):
                b = st.selectbox("Banco", ["Banco General", "Banistmo", "BAC", "Global Bank", "Otro"])
                m = st.number_input("Monto $", min_value=0.0, format="%.2f")
                r = st.text_input("Referencia")
                if st.form_submit_button("💾 Guardar Depósito"):
                    if m > 0:
                        try:
                            self.db.insert("depositos", {"banco": b, "monto": m, "referencia": r.upper(), "fecha": pd.Timestamp.now().isoformat()})
                            logger.info(f"Depósito registrado con éxito en {b}: ${m:,.2f} - Ref: {r.upper()}")
                            st.success("Depósito registrado correctamente.")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error al registrar depósito en BD: {e}")
                            st.error(f"No se pudo guardar el depósito: {e}")
                    else:
                        st.warning("El monto del depósito debe ser mayor a 0.")
            for idx, d in enumerate(depositos):
                if d:
                    d_id = d.get('id', idx)
                    with st.container(border=True):
                        c1, c2 = st.columns([5, 1])
                        raw_d_monto = d.get('monto')
                        d_monto_float = float(raw_d_monto) if raw_d_monto is not None else 0.0
                        c1.write(f"🏦 {d.get('banco')} | Ref: {d.get('referencia', 'S/R')} | ${d_monto_float:,.2f}")
                        if c2.button("🖨️", key=f"pd_{d_id}"):
                            st.session_state.print_html = self.generar_formato_impresion("COMPROBANTE DE DEPÓSITO", d)

        with tabs[2]: # RECIBOS (MÓDULO DE CAJA INTEGRADO CON LOGS Y MANEJO DE RLS)
            if ventas:
                with st.expander("📝 Registrar Abono / Recibo Manual"):
                    df_v_rec = pd.DataFrame(ventas)
                    opciones = [f"#{int(float(x.get('num_factura', x.get('id', 0))))} - {x.get('cliente','S/N')} (${x.get('total',0)})" for _, x in df_v_rec.iterrows()]
                    with st.form("f_r"):
                        sel = st.selectbox("Factura Asociada", opciones)
                        idx = opciones.index(sel)
                        f_sel = df_v_rec.iloc[idx]
                        m_rec = st.number_input("Monto Recibido $", value=float(f_sel.get('total', 0.0)), format="%.2f")
                        met = st.selectbox("Método", ["Efectivo", "ACH", "Yappy", "Cheque"])
                        if st.form_submit_button("✅ Procesar e Insertar Recibo"):
                            num_f_asoc = int(float(f_sel.get('num_factura', f_sel.get('id', 0))))
                            nuevo_recibo_dict = {
                                "cliente": str(f_sel.get('cliente', 'S/N')).upper(), 
                                "monto": m_rec, 
                                "monto_abono": m_rec,
                                "metodo_pago": met, 
                                "id_venta": num_f_asoc, 
                                "tipo_recibo": "VINCULADO",
                                "fecha": pd.Timestamp.now().isoformat()
                            }
                            try:
                                self.db.insert("recibos", nuevo_recibo_dict)
                                logger.info(f"Recibo insertado exitosamente para factura #{num_f_asoc} por valor de ${m_rec:,.2f}")
                                st.success("Recibo procesado e insertado correctamente.")
                                st.rerun()
                            except Exception as e:
                                logger.error(f"Fallo al insertar recibo en tabla 'recibos' (Posible restricción RLS): {e}")
                                st.error(f"Error de base de datos al guardar recibo: {e}")
                            
            st.write("### 📜 Listado de Recibos de Caja")
            for idx, r in enumerate(recibos):
                if r:
                    r_id = r.get('id', f"rec_{idx}")
                    with st.container(border=True):
                        col_inf, col_ed, col_del, col_pr = st.columns([4, 1, 1, 0.5])
                        num_r_vis = r.get('num_recibo') or r_id
                        raw_r_monto = r.get('monto_abono') or r.get('monto')
                        monto_r_vis = float(raw_r_monto) if raw_r_monto is not None else 0.0
                        
                        col_inf.write(f"**Recibo #{num_r_vis}** ({r.get('tipo_recibo', 'MANUAL')}) | Cliente: {r.get('cliente', 'S/N')}")
                        col_inf.caption(f"Método: {r.get('metodo_pago', 'S/M')} | Fecha: {str(r.get('fecha',''))[:10]} | **Abonado: ${monto_r_vis:,.2f}**")
                        
                        with col_ed.popover("✏️ Editar"):
                            nuevo_monto = st.number_input("Ajustar Monto $", min_value=0.01, value=monto_r_vis, step=1.0, format="%.2f", key=f"ed_m_{r_id}_{idx}")
                            if st.button("💾 Actualizar", key=f"save_ed_{r_id}_{idx}", use_container_width=True):
                                try:
                                    self.db.client.table("recibos").update({"monto_abono": nuevo_monto, "monto": nuevo_monto}).eq("id", r_id).execute()
                                    logger.info(f"Recibo ID {r_id} actualizado con nuevo monto: ${nuevo_monto:,.2f}")
                                    st.success("Monto actualizado con éxito.")
                                    st.rerun()
                                except Exception as e:
                                    logger.error(f"Error al actualizar recibo ID {r_id}: {e}")
                                    st.error(f"No se pudo actualizar el registro: {e}")
                                    
                        if col_del.button("🗑️ Eliminar", key=f"del_r_{r_id}_{idx}", type="secondary", use_container_width=True):
                            self.eliminar_recibo(r)
                            
                        if col_pr.button("🖨️", key=f"pr_{r_id}_{idx}"):
                            st.session_state.print_html = self.generar_formato_impresion("RECIBO DE PAGO / PAYMENT RECEIPT", r)

        with tabs[3]: # HISTORIAL FACTURAS
            if ventas:
                bus = st.text_input("🔍 Buscar Factura por Número o Nombre...").lower()
                for idx, v in enumerate(reversed(ventas)):
                    if v:
                        v_id = v.get('id', idx)
                        num_f_vis = str(int(float(v.get('num_factura', v_id))))
                        if bus in num_f_vis or bus in str(v.get('cliente', '')).lower():
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([3, 1, 1])
                                c1.write(f"🧾 Factura #{num_f_vis} | **{v.get('cliente', 'S/N')}**")
                                
                                raw_v_total = v.get('total')
                                v_total_float = float(raw_v_total) if raw_v_total is not None else 0.0
                                c1.caption(f"Total: ${v_total_float:,.2f} | Fecha: {str(v.get('fecha',''))[:10]}")
                                
                                if c2.button("🖨️ Reimprimir", key=f"reim_{v_id}_{idx}", use_container_width=True):
                                    st.session_state.print_html = self.generar_formato_impresion("FACTURA DE VENTA / SALES INVOICE", v)
                                
                                if c3.button("🗑️ Eliminar Factura", key=f"del_{v_id}_{idx}", type="secondary", use_container_width=True):
                                    self.eliminar_factura(v)

        with tabs[4]: # CIERRE E INFORMES
            st.subheader("🔒 Centro de Cierre Operativo")
            
            df_v = pd.DataFrame(ventas) if ventas else pd.DataFrame(columns=['id', 'total', 'fecha', 'cliente', 'nota', 'num_factura'])
            df_r = pd.DataFrame(recibos) if recibos else pd.DataFrame(columns=['id', 'monto', 'monto_abono', 'fecha', 'cliente', 'metodo_pago', 'num_recibo'])
            df_g = pd.DataFrame(gastos) if gastos else pd.DataFrame(columns=['id', 'monto', 'fecha', 'descripcion'])
            df_d = pd.DataFrame(depositos) if depositos else pd.DataFrame(columns=['id', 'monto', 'fecha', 'banco', 'referencia'])

            for df in [df_v, df_r, df_g, df_d]:
                if not df.empty and 'fecha' in df.columns:
                    df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
                    df['fecha_dia'] = df['fecha_dt'].dt.strftime('%Y-%m-%d')
                    df['fecha_mes'] = df['fecha_dt'].dt.strftime('%Y-%m')
                else:
                    df['fecha_dia'] = pd.Series(dtype='str')
                    df['fecha_mes'] = pd.Series(dtype='str')

            todos_dias = sorted(list(set(df_v['fecha_dia'].dropna().tolist() + df_r['fecha_dia'].dropna().tolist() + df_g['fecha_dia'].dropna().tolist() + df_d['fecha_dia'].dropna().tolist())), reverse=True)
            todos_meses = sorted(list(set(df_v['fecha_mes'].dropna().tolist() + df_r['fecha_mes'].dropna().tolist() + df_g['fecha_mes'].dropna().tolist() + df_d['fecha_mes'].dropna().tolist())), reverse=True)

            sub_tabs = st.tabs(["📆 Cuadre Diario Unificado", "📅 Balance Mensual Unificado"])

            with sub_tabs[0]:
                if todos_dias:
                    dia_sel = st.selectbox("Seleccione Día para Reportar", todos_dias, key="sel_dia_u")
                    
                    items_v_d = df_v[df_v['fecha_dia'] == dia_sel] if not df_v.empty else pd.DataFrame()
                    items_r_d = df_r[df_r['fecha_dia'] == dia_sel] if not df_r.empty else pd.DataFrame()
                    items_g_d = df_g[df_g['fecha_dia'] == dia_sel] if not df_g.empty else pd.DataFrame()
                    items_d_d = df_d[df_d['fecha_dia'] == dia_sel] if not df_d.empty else pd.DataFrame()

                    v_d = pd.to_numeric(items_v_d['total'], errors='coerce').sum() if not items_v_d.empty and 'total' in items_v_d.columns else 0.0
                    
                    if not items_r_d.empty:
                        col_act = 'monto_abono' if 'monto_abono' in items_r_d.columns else 'monto'
                        r_d = pd.to_numeric(items_r_d[col_act], errors='coerce').sum()
                    else:
                        r_d = 0.0
                        
                    g_d = pd.to_numeric(items_g_d['monto'], errors='coerce').sum() if not items_g_d.empty and 'monto' in items_g_d.columns else 0.0
                    d_d = pd.to_numeric(items_d_d['monto'], errors='coerce').sum() if not items_d_d.empty and 'monto' in items_d_d.columns else 0.0
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Ventas (Facturado)", f"${v_d:,.2f}")
                    m2.metric("Recibos (Recaudado)", f"${r_d:,.2f}")
                    m3.metric("Gastos (Egresos)", f"${g_d:,.2f}", delta_color="inverse")
                    m4.metric("Depósitos (Bancos)", f"${d_d:,.2f}")
                    
                    st.divider()
                    st.write("#### Acciones de Impresión (Informe Corporativo)")
                    
                    dia_str = str(dia_sel if dia_sel is not None else pd.Timestamp.now().strftime("%Y-%m-%d"))
                    dia_id_limpio = dia_str.replace('-', '')

                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    if col_b1.button("🖨️ Informe Ventas", key="p_v_d"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE VENTA DIARIA", 
                            {"id": f"V-{dia_id_limpio}", "fecha": dia_str, "cliente": "Caja General de Ventas", "total": v_d, "nota": "Consolidado fiscal diario."},
                            items_v_d.to_dict('records') if not items_v_d.empty else None
                        )
                    if col_b2.button("🖨️ Informe Recibos", key="p_r_d"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE RECIBOS DE CAJA", 
                            {"id": f"R-{dia_id_limpio}", "fecha": dia_str, "cliente": "Caja General de Cobros", "total": r_d, "nota": "Consolidado diario de ingresos."},
                            items_r_d.to_dict('records') if not items_r_d.empty else None
                        )
                    if col_b3.button("🖨️ Informe Gastos", key="p_g_d"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DIARIO DE GASTOS", 
                            {"id": f"G-{dia_id_limpio}", "fecha": dia_str, "cliente": "Egresos de Caja Chica", "total": g_d, "nota": "Consolidado diario de salidas."},
                            items_g_d.to_dict('records') if not items_g_d.empty else None
                        )
                    if col_b4.button("🖨️ Informe Depósitos", key="p_d_d"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE DEPÓSITOS BANCARIOS", 
                            {"id": f"D-{dia_id_limpio}", "fecha": dia_str, "cliente": "Tesorería / Conciliación Bancaria", "total": d_d, "nota": "Consolidado diario de fondos."},
                            items_d_d.to_dict('records') if not items_d_d.empty else None
                        )
                else:
                    st.info("No se hallaron transacciones diarias.")

            with sub_tabs[1]:
                if todos_meses:
                    mes_sel = st.selectbox("Seleccione Mes para Reportar", todos_meses, key="sel_mes_u")
                    
                    items_v_m = df_v[df_v['fecha_mes'] == mes_sel] if not df_v.empty else pd.DataFrame()
                    items_r_m = df_r[df_r['fecha_mes'] == mes_sel] if not df_r.empty else pd.DataFrame()
                    items_g_m = df_g[df_g['fecha_mes'] == mes_sel] if not df_g.empty else pd.DataFrame()
                    items_d_m = df_d[df_d['fecha_mes'] == mes_sel] if not df_d.empty else pd.DataFrame()

                    v_m = pd.to_numeric(items_v_m['total'], errors='coerce').sum() if not items_v_m.empty and 'total' in items_v_m.columns else 0.0
                    
                    if not items_r_m.empty:
                        col_act_m = 'monto_abono' if 'monto_abono' in items_r_m.columns else 'monto'
                        r_m = pd.to_numeric(items_r_m[col_act_m], errors='coerce').sum()
                    else:
                        r_m = 0.0
                        
                    g_m = pd.to_numeric(items_g_m['monto'], errors='coerce').sum() if not items_g_m.empty and 'monto' in items_g_m.columns else 0.0
                    d_m = pd.to_numeric(items_d_m['monto'], errors='coerce').sum() if not items_d_m.empty and 'monto' in items_d_m.columns else 0.0
                    
                    mm1, mm2, mm3, mm4 = st.columns(4)
                    mm1.metric("Total Ventas", f"${v_m:,.2f}")
                    mm2.metric("Total Recibos", f"${r_m:,.2f}")
                    mm3.metric("Total Gastos", f"${g_m:,.2f}", delta_color="inverse")
                    mm4.metric("Total Depósitos", f"${d_m:,.2f}")
                    
                    st.divider()
                    st.write("#### Acciones de Impresión Mensual")
                    
                    mes_str = str(mes_sel if mes_sel is not None else pd.Timestamp.now().strftime("%Y-%m"))
                    mes_id_limpio = mes_str.replace('-', '')

                    col_bm1, col_bm2, col_bm3, col_bm4 = st.columns(4)
                    if col_bm1.button("🖨️ Reporte Ventas", key="p_v_m"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE VENTAS", 
                            {"id": f"MV-{mes_id_limpio}", "fecha": f"{mes_str}-01", "cliente": "Auditoría de Ventas", "total": v_m, "nota": f"Facturación total del periodo: {mes_str}."},
                            items_v_m.to_dict('records') if not items_v_m.empty else None
                        )
                    if col_bm2.button("🖨️ Reporte Recibos", key="p_r_m"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE RECAUDACIÓN", 
                            {"id": f"MR-{mes_id_limpio}", "fecha": f"{mes_str}-01", "cliente": "Administración de Cartera", "total": r_m, "nota": f"Ingresos reales a caja: {mes_str}."},
                            items_r_m.to_dict('records') if not items_r_m.empty else None
                        )
                    if col_bm3.button("🖨️ Reporte Gastos", key="p_g_m"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE EGRESOS", 
                            {"id": f"MG-{mes_id_limpio}", "fecha": f"{mes_str}-01", "cliente": "Control de Costos", "total": g_m, "nota": f"Egresos liquidados del mes: {mes_str}."},
                            items_g_m.to_dict('records') if not items_g_m.empty else None
                        )
                    if col_bm4.button("🖨️ Reporte Depósitos", key="p_d_m"):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE DEPÓSITOS", 
                            {"id": f"MD-{mes_id_limpio}", "fecha": f"{mes_str}-01", "cliente": "Contabilidad / Bancos", "total": d_m, "nota": f"Fondos del periodo: {mes_str}."},
                            items_d_m.to_dict('records') if not items_d_m.empty else None
                        )
                else:
                    st.info("No se hallaron transacciones mensuales.")

        # DISPARADOR DE IMPRESIÓN SEGURO
        if "print_html" in st.session_state:
            components.html(st.session_state.print_html, height=1, width=1)
            del st.session_state.print_html