# contabilidad.py
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64
import os
from utilidades import check_permiso  # <-- INTEGRACIÓN DEL CANDADO DE SEGURIDAD

class ModuloContabilidad:
    def __init__(self, db):
        self.db = db
        self.logo_path = "logo.png"

    def get_image_base64(self, path):
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except Exception:
            return None

    def generar_formato_impresion(self, titulo, datos):
        """Mantiene el formato original tipo recibo/voucher doble para transacciones individuales"""
        logo_b64 = self.get_image_base64(self.logo_path)
        
        fecha_raw = datos.get('fecha')
        fecha = fecha_raw[:10] if isinstance(fecha_raw, str) else pd.Timestamp.now().strftime("%Y-%m-%d")
        
        folio = datos.get('id', '000')
        sujeto = datos.get('cliente') or datos.get('descripcion') or datos.get('banco') or "S/N"
        monto = float(datos.get('total') or datos.get('monto') or 0)
        concepto = datos.get('nota') or datos.get('descripcion') or datos.get('referencia') or "Registro Contable"
        
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 150px;">' if logo_b64 else ""

        html_content = ""
        for i in range(2):
            tipo = "ORIGINAL" if i == 0 else "COPIA CONTABILIDAD"
            html_content += f"""
            <div style="border: 1px solid #000; padding: 20px; margin-bottom: 50px; font-family: 'Courier New', Courier, monospace; min-height: 450px; color: #000; position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 10px;">
                    <div style="width: 30%;">{logo_html}</div>
                    <div style="width: 70%; text-align: right; font-size: 9pt; line-height: 1.2;">
                        <strong style="font-size: 11pt;">SONIX LTD. #1</strong><br>
                    RUC: 1570526-1-660611 DV80 | TEL: (507) 6239-7128 <br>
                    LOTE 1, DE LA MANZANA 26-A, AVE. SAN ELADIO CALLE 17 ,ZONA LIBRE DE COLÓN , REPÚBLICA PANAMÁ. 
                    </div>
                </div>
                <div style="text-align: center; margin: 15px 0;">
                    <h2 style="margin:0; text-decoration: underline; font-size: 16pt;">{titulo}</h2>
                    <p style="margin:5px 0; font-weight: bold; color: #d32f2f;">N° DOCUMENTO: {folio}</p>
                </div>
                <div style="text-align: center; background: #eee; padding: 3px; font-weight: bold; font-size: 8pt; margin-bottom: 15px;">{tipo}</div>
                <table style="width: 100%; font-size: 10pt; border-collapse: collapse;">
                    <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>FECHA:</strong> {fecha}</td></tr>
                    <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>SUJETO / REF:</strong> {str(sujeto).upper()}</td></tr>
                    <tr>
                        <td style="padding: 20px 5px; border-bottom: 1px solid #000;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>POR LA SUMA DE:</strong>
                                <span style="font-size: 18pt; font-weight: bold; border: 2px solid #000; padding: 5px 15px; background: #f9f9f9;">$ {monto:,.2f}</span>
                            </div>
                        </td>
                    </tr>
                    <tr><td style="padding: 15px 5px; vertical-align: top;"><strong>CONCEPTO:</strong><br><div style="margin-top: 5px; font-style: italic;">{concepto}</div></td></tr>
                </table>
                <div style="display: flex; justify-content: space-between; margin-top: 80px;">
                    <div style="width: 40%; border-top: 1px solid #000; text-align: center; font-size: 8pt;">FIRMA AUTORIZADA</div>
                    <div style="width: 40%; border-top: 1px solid #000; text-align: center; font-size: 8pt;">RECIBIDO CONFORME</div>
                </div>
                <div style="position: absolute; bottom: 10px; width: 95%; text-align: center; font-size: 7pt; color: #666;">RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO</div>
            </div>
            """
        return f"<div>{html_content}</div><script>window.print();</script>"

    def generar_informe_hoja_unica(self, titulo, datos, items_detalle=None):
        """Genera una plantilla de Reporte Ejecutivo formal con la lista explícita de documentos incluidos"""
        logo_b64 = self.get_image_base64(self.logo_path)
        
        fecha_raw = datos.get('fecha')
        fecha = fecha_raw[:10] if isinstance(fecha_raw, str) else pd.Timestamp.now().strftime("%Y-%m-%d")
        
        folio = datos.get('id', '000')
        origen = datos.get('cliente') or "Departamento de Contabilidad"
        monto = float(datos.get('total') or 0)
        concepto = datos.get('nota') or "Cierre del periodo fiscal"
        
        nombre_descarga = f"{titulo.replace(' ', '_')}_{fecha}"
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 55px;">' if logo_b64 else ""

        tabla_items_html = ""
        if items_detalle and len(items_detalle) > 0:
            filas_html = ""
            for item in items_detalle:
                doc_id = item.get('id', 'S/N')
                doc_fecha_raw = item.get('fecha', '')
                doc_fecha = doc_fecha_raw[:10] if isinstance(doc_fecha_raw, str) else ''
                
                doc_sujeto = item.get('cliente') or item.get('banco') or item.get('descripcion') or 'GENERAL'
                if len(str(doc_sujeto)) > 30:
                    doc_sujeto = str(doc_sujeto)[:28] + ".."
                
                doc_ref = item.get('referencia') or item.get('metodo_pago') or item.get('descripcion') or 'Registro'
                if len(str(doc_ref)) > 35:
                    doc_ref = str(doc_ref)[:33] + ".."
                    
                doc_monto = float(item.get('total') or item.get('monto') or 0)

                filas_html += f"""
                <tr style="border-bottom: 1px solid #e2e8f0; font-size: 9pt;">
                    <td style="padding: 6px 10px; font-family: monospace; font-weight: bold;">#{doc_id}</td>
                    <td style="padding: 6px 10px;">{doc_fecha}</td>
                    <td style="padding: 6px 10px; text-transform: uppercase;">{doc_sujeto}</td>
                    <td style="padding: 6px 10px; font-style: italic; color: #4a5568;">{doc_ref}</td>
                    <td style="padding: 6px 10px; text-align: right; font-weight: bold;">$ {doc_monto:,.2f}</td>
                </tr>
                """
            
            tabla_items_html = f"""
            <div style="margin-top: 20px; margin-bottom: 25px;">
                <h4 style="margin: 0 0 10px 0; color: #1a365d; text-transform: uppercase; font-size: 10pt; letter-spacing: 0.5px; border-bottom: 2px solid #1a365d; padding-bottom: 4px;">
                    Documentos e Historial Incluido en el Periodo
                </h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt;">
                    <thead>
                        <tr style="background-color: #1a365d; color: #fff; text-align: left; font-size: 8.5pt;">
                            <th style="padding: 6px 10px;">ID DOC</th>
                            <th style="padding: 6px 10px;">FECHA</th>
                            <th style="padding: 6px 10px;">SUJETO / ENTIDAD</th>
                            <th style="padding: 6px 10px;">REFERENCIA CORTA</th>
                            <th style="padding: 6px 10px; text-align: right;">MONTO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{nombre_descarga}</title>
            <style>
                @media print {{
                    @page {{
                        size: A4 portrait;
                        margin: 15mm 10mm 15mm 10mm;
                    }}
                    body {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 10px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.4; background-color: #fff;">
            <div style="max-width: 800px; margin: 0 auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #1a365d; padding-bottom: 12px; margin-bottom: 20px;">
                    <div style="width: 40%; text-align: left;">{logo_html}</div>
                    <div style="width: 60%; text-align: right; font-size: 8.5pt; color: #555;">
                        <strong style="font-size: 11pt;">SONIX LTD. #1</strong><br>
                    RUC: 1570526-1-660611 DV80 | TEL: (507) 6239-7128 <br>
                    LOTE 1, DE LA MANZANA 26-A, AVE. SAN ELADIO CALLE 17 ,ZONA LIBRE DE COLÓN , REPÚBLICA PANAMÁ. 
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 5px 0; color: #1a365d; font-size: 15pt; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</h2>
                    <div style="font-size: 9pt; color: #666;">Reporte de Auditoría Interna / Control de Caja</div>
                </div>

                <table style="width: 100%; font-size: 9.5pt; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f7fafc;">
                        <td style="padding: 8px; border: 1px solid #e2e8f0; width: 30%;"><strong>N° REPORTE:</strong></td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; font-family: monospace; font-weight: bold; color: #d32f2f;">{folio}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>FECHA DE CORTE:</strong></td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0;">{fecha}</td>
                    </tr>
                    <tr style="background-color: #f7fafc;">
                        <td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>ÁREA / DEPARTAMENTO:</strong></td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0;">{str(origen).upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; vertical-align: top;"><strong>DESCRIPCIÓN:</strong></td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; font-style: italic; color: #4a5568;">{concepto}</td>
                    </tr>
                </table>

                {tabla_items_html}

                <div style="background: #1a365d; color: #fff; padding: 12px 20px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); -webkit-print-color-adjust: exact;">
                    <span style="font-size: 10pt; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Monto Total Consolidado:</span>
                    <span style="font-size: 18pt; font-weight: bold; font-family: 'Courier New', monospace;">$ {monto:,.2f}</span>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 45px; padding: 0 20px;">
                    <div style="width: 40%; border-top: 1.5px solid #a0aec0; text-align: center; font-size: 8.5pt; color: #4a5568; padding-top: 8px;">
                        <strong>Firma de Auditoría / Caja</strong><br>SONIX LTD. #1
                    </div>
                    <div style="width: 40%; border-top: 1.5px solid #a0aec0; text-align: center; font-size: 8.5pt; color: #4a5568; padding-top: 8px;">
                        <strong>Recibido Administración</strong><br>Control Interno
                    </div>
                </div>
                
                <div style="margin-top: 60px; border-top: 1px solid #e2e8f0; padding-top: 10px; text-align: center; font-size: 7.5pt; color: #a0aec0; letter-spacing: 0.5px;">
                    RAV SYSTEM - SISTEMA DE CONTROL DE GESTIÓN EMPRESARIAL
                </div>
            </div>
            <script>
                window.parent.document.title = "{nombre_descarga}";
                setTimeout(function() {{
                    window.print();
                }}, 250);
            </script>
        </body>
        </html>
        """
        return html_content

    def eliminar_factura(self, factura):
        """Elimina la factura y devuelve el stock a productos (Migrado a Local SQLite)"""
        try:
            # Reconstruir o extraer los ítems guardados en la factura si vienen serializados
            detalle = factura.get('detalle', [])
            if isinstance(detalle, str):
                import json
                try: detalle = json.loads(detalle)
                except: detalle = []

            for item in detalle:
                # Consulta limpia emulando local sin cloud helpers
                res = self.db.ejecutar_consulta_sqlite_local("SELECT CANTIDAD FROM productos WHERE REFERENCIA = ?", (item['id'],))
                if res:
                    nueva_q = int(res[0]['cantidad']) + int(item['cantidad'])
                    self.db.ejecutar_consulta_sqlite_local("UPDATE productos SET CANTIDAD = ? WHERE REFERENCIA = ?", (nueva_q, item['id']))
            
            # Borrados locales limpios
            self.db.ejecutar_consulta_sqlite_local("DELETE FROM recibos WHERE id_venta = ?", (factura['id'],))
            self.db.ejecutar_consulta_sqlite_local("DELETE FROM ventas WHERE id = ?", (factura['id'],))
            st.success(f"Factura #{factura['id']} eliminada y stock restaurado en la base local.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al eliminar factura localmente: {e}")

    def render(self):
        st.header("📊 Contabilidad y Finanzas")
        
        # Evaluación de los permisos centralizados para el módulo contable
        puede_ingresar = check_permiso("ingresar")
        puede_modificar = check_permiso("modificar")
        puede_eliminar = check_permiso("eliminar")

        # 1. CARGA DE DATOS LOCALES
        ventas = self.db.fetch("ventas") or []
        recibos = self.db.fetch("recibos") or []
        gastos = self.db.fetch("gastos") or []
        depositos = self.db.fetch("depositos") or []

        # 2. MÉTRICAS GENERALES
        t_ingresos = sum(v.get('total', 0) for v in ventas)
        t_gastos = sum(g.get('monto', 0) for g in gastos)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales Históricas", f"${t_ingresos:,.2f}")
        c2.metric("Gastos Totales", f"${t_gastos:,.2f}", delta_color="inverse")
        c3.metric("Utilidad Bruta", f"${(t_ingresos - t_gastos):,.2f}")

        # 3. CXC
        st.divider()
        st.subheader("🔍 Cuentas por Cobrar (CXC)")
        if ventas:
            df_v = pd.DataFrame(ventas)
            df_r = pd.DataFrame(recibos) if recibos else pd.DataFrame(columns=['id_venta', 'monto'])
            p_pagos = df_r.groupby('id_venta')['monto'].sum().reset_index() if not df_r.empty else pd.DataFrame(columns=['id_venta', 'monto'])
            p_pagos.columns = ['id_venta', 'total_pagado']
            cxc_df = pd.merge(df_v, p_pagos, left_on='id', right_on='id_venta', how='left').fillna(0)
            cxc_df['saldo'] = cxc_df['total'] - cxc_df['total_pagado']
            pendientes = cxc_df[cxc_df['saldo'] > 0.01]
            if not pendientes.empty:
                st.error(f"Pendiente de cobro: ${pendientes['saldo'].sum():,.2f}")
                with st.expander("Ver detalle CXC"):
                    for _, p in pendientes.iterrows():
                        st.write(f"📌 {p['cliente']} | Factura #{p['id']} | **Saldo: ${p['saldo']:.2f}**")
            else:
                st.success("✅ Cartera al día.")

        # 4. PESTAÑAS PRINCIPALES
        tabs = st.tabs(["📉 Gastos", "🏦 Depósitos", "📄 Recibos", "📑 Historial Facturas", "🔒 Cierre e Informes"])

        with tabs[0]: # GASTOS
            with st.form("f_g"):
                m, d = st.columns([1,2])
                monto_g = m.number_input("Monto $", min_value=0.0, format="%.2f")
                desc_g = d.text_input("Descripción")
                
                btn_gasto = st.form_submit_button("💾 Guardar Gasto", disabled=not puede_ingresar)
                if btn_gasto and puede_ingresar:
                    self.db.insert("gastos", {"monto": monto_g, "descripcion": desc_g.upper(), "fecha": pd.Timestamp.now().isoformat()})
                    st.rerun()
                    
            for g in gastos:
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    fecha_g = g.get('fecha')[:10] if g.get('fecha') else "S/F"
                    c1.write(f"📅 {fecha_g} | **{g.get('descripcion')}** | ${g.get('monto'):.2f}")
                    
                    if c2.button("🖨️", key=f"pg_{g['id']}", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_formato_impresion("COMPROBANTE DE GASTO", g)
                        st.rerun()

        with tabs[1]: # DEPÓSITOS
            with st.form("f_d"):
                b = st.selectbox("Banco", ["Banco General", "Banistmo", "BAC", "Global Bank", "Otro"])
                m = st.number_input("Monto $", min_value=0.0, format="%.2f")
                r = st.text_input("Referencia")
                
                btn_deposito = st.form_submit_button("💾 Guardar Depósito", disabled=not puede_ingresar)
                if btn_deposito and puede_ingresar:
                    self.db.insert("depositos", {"banco": b, "monto": m, "referencia": r.upper(), "fecha": pd.Timestamp.now().isoformat()})
                    st.rerun()
                    
            for d in depositos:
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    c1.write(f"🏦 {d.get('banco')} | Ref: {d.get('referencia')} | ${d.get('monto'):.2f}")
                    
                    if c2.button("🖨️", key=f"pd_{d['id']}", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_formato_impresion("COMPROBANTE DE DEPÓSITO", d)
                        st.rerun()

        with tabs[2]: # RECIBOS
            if ventas:
                with st.expander("📝 Generar Nuevo Recibo"):
                    df_v_rec = pd.DataFrame(ventas)
                    opciones = [f"#{x['id']} - {x['cliente']} (${x['total']})" for _, x in df_v_rec.iterrows()]
                    with st.form("f_r"):
                        sel = st.selectbox("Factura", opciones)
                        idx = opciones.index(sel)
                        f_sel = df_v_rec.iloc[idx]
                        m_rec = st.number_input("Monto Recibido $", value=float(f_sel['total']), format="%.2f")
                        met = st.selectbox("Método", ["Efectivo", "ACH", "Yappy", "Cheque"])
                        
                        btn_recibo = st.form_submit_button("✅ Procesar Recibo", disabled=not puede_ingresar)
                        if btn_recibo and puede_ingresar:
                            self.db.insert("recibos", {"cliente": f_sel['cliente'].upper(), "monto": m_rec, "metodo_pago": met, "id_venta": int(f_sel['id']), "fecha": pd.Timestamp.now().isoformat()})
                            st.rerun()
            for r in recibos:
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    c1.write(f"📄 Recibo #{r['id']} | {r.get('cliente')} | ${r.get('monto'):.2f}")
                    
                    if c2.button("🖨️", key=f"pr_{r['id']}", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_formato_impresion("RECIBO DE CAJA", r)
                        st.rerun()

        with tabs[3]: # HISTORIAL FACTURAS
            if ventas:
                bus = st.text_input("🔍 Buscar Factura...").lower()
                for v in reversed(ventas):
                    if bus in str(v['id']) or bus in v['cliente'].lower():
                        with st.container(border=True):
                            columnas = [3, 1, 1] if puede_eliminar else [4, 1]
                            cols_f = st.columns(columnas)
                            
                            cols_f[0].write(f"🧾 Factura #{v['id']} | **{v['cliente']}**")
                            fecha_v = v['fecha'][:10] if v.get('fecha') else "S/F"
                            cols_f[0].caption(f"Total: ${v['total']:.2f} | Fecha: {fecha_v}")
                            
                            if cols_f[1].button("🖨️ Reimprimir", key=f"reim_{v['id']}", disabled=not puede_modificar):
                                st.session_state.print_html = self.generar_formato_impresion("FACTURA DE VENTA", v)
                                st.rerun()
                            
                            if puede_eliminar:
                                if cols_f[2].button("🗑️ Eliminar", key=f"del_{v['id']}", type="secondary"):
                                    self.eliminar_factura(v)

        with tabs[4]: # 🔒 CIERRE E INFORMES
            st.subheader("🔒 Centro de Cierre Operativo")
            
            df_v = pd.DataFrame(ventas) if ventas else pd.DataFrame(columns=['id', 'total', 'fecha', 'cliente', 'nota'])
            df_r = pd.DataFrame(recibos) if recibos else pd.DataFrame(columns=['id', 'monto', 'fecha', 'cliente', 'metodo_pago'])
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

                    v_d = items_v_d['total'].sum() if not items_v_d.empty else 0.0
                    r_d = items_r_d['monto'].sum() if not items_r_d.empty else 0.0
                    g_d = items_g_d['monto'].sum() if not items_g_d.empty else 0.0
                    d_d = items_d_d['monto'].sum() if not items_d_d.empty else 0.0
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Ventas (Facturado)", f"${v_d:,.2f}")
                    m2.metric("Recibos (Recaudado)", f"${r_d:,.2f}")
                    m3.metric("Gastos (Egresos)", f"${g_d:,.2f}", delta_color="inverse")
                    m4.metric("Depósitos (Bancos)", f"${d_d:,.2f}")
                    
                    st.divider()
                    st.write("#### Acciones de Impresión (Informe Corporativo con Lista de Documentos)")
                    
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    if col_b1.button("🖨️ Informe Ventas", key="p_v_d", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE VENTA DIARIA", 
                            {"id": f"V-{dia_sel.replace('-','')}", "fecha": dia_sel, "cliente": "Caja General de Ventas", "total": v_d, "nota": "Consolidado fiscal y arqueo general diario de facturación."},
                            items_v_d.to_dict('records') if not items_v_d.empty else None
                        )
                        st.rerun()
                    if col_b2.button("🖨️ Informe Recibos", key="p_r_d", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE RECIBOS DE CAJA", 
                            {"id": f"R-{dia_sel.replace('-','')}", "fecha": dia_sel, "cliente": "Caja General de Cobros", "total": r_d, "nota": "Consolidado resumido de ingresos por cobros ejecutados in el día."},
                            items_r_d.to_dict('records') if not items_r_d.empty else None
                        )
                        st.rerun()
                    if col_b3.button("🖨️ Informe Gastos", key="p_g_d", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DIARIO DE GASTOS", 
                            {"id": f"G-{dia_sel.replace('-','')}", "fecha": dia_sel, "cliente": "Egresos de Caja Chica", "total": g_d, "nota": "Consolidado resumido de salidas y gastos operativos autorizados."},
                            items_g_d.to_dict('records') if not items_g_d.empty else None
                        )
                        st.rerun()
                    if col_b4.button("🖨️ Informe Depósitos", key="p_d_d", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME DE DEPÓSITOS BANCARIOS", 
                            {"id": f"D-{dia_sel.replace('-','')}", "fecha": dia_sel, "cliente": "Tesorería / Conciliación Bancaria", "total": d_d, "nota": "Consolidado y arqueo diario de fondos asegurados vía ACH/Depósitos."},
                            items_d_d.to_dict('records') if not items_d_d.empty else None
                        )
                        st.rerun()
                else:
                    st.info("No se hallaron transacciones diarias.")

            with sub_tabs[1]:
                if todos_meses:
                    mes_sel = st.selectbox("Seleccione Mes para Reportar", todos_meses, key="sel_mes_u")
                    
                    items_v_m = df_v[df_v['fecha_mes'] == mes_sel] if not df_v.empty else pd.DataFrame()
                    items_r_m = df_r[df_r['fecha_mes'] == mes_sel] if not df_r.empty else pd.DataFrame()
                    items_g_m = df_g[df_g['fecha_mes'] == mes_sel] if not df_g.empty else pd.DataFrame()
                    items_d_m = df_d[df_d['fecha_mes'] == mes_sel] if not df_d.empty else pd.DataFrame()

                    v_m = items_v_m['total'].sum() if not items_v_m.empty else 0.0
                    r_m = items_r_m['monto'].sum() if not items_r_m.empty else 0.0
                    g_m = items_g_m['monto'].sum() if not items_g_m.empty else 0.0
                    d_m = items_d_m['monto'].sum() if not items_d_m.empty else 0.0
                    
                    mm1, mm2, mm3, mm4 = st.columns(4)
                    mm1.metric("Total Ventas", f"${v_m:,.2f}")
                    mm2.metric("Total Recibos", f"${r_m:,.2f}")
                    mm3.metric("Total Gastos", f"${g_m:,.2f}", delta_color="inverse")
                    mm4.metric("Total Depósitos", f"${d_m:,.2f}")
                    
                    st.divider()
                    st.write("#### Acciones de Impresión Mensual (Informe Corporativo con Lista de Documentos)")
                    
                    col_bm1, col_bm2, col_bm3, col_bm4 = st.columns(4)
                    if col_bm1.button("🖨️ Reporte Ventas", key="p_v_m", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE VENTAS", 
                            {"id": f"MV-{mes_sel.replace('-','')}", "fecha": f"{mes_sel}-01", "cliente": "Auditoría de Ventas Corporativas", "total": v_m, "nota": f"Informe gerencial analítico de facturación total del período fiscal: {mes_sel}."},
                            items_v_m.to_dict('records') if not items_v_m.empty else None
                        )
                        st.rerun()
                    if col_bm2.button("🖨️ Reporte Recibos", key="p_r_m", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE RECAUDACIÓN", 
                            {"id": f"MR-{mes_sel.replace('-','')}", "fecha": f"{mes_sel}-01", "cliente": "Administración de Cartera / Cobros", "total": r_m, "nota": f"Informe analítico de ingresos reales a caja: {mes_sel}."},
                            items_r_m.to_dict('records') if not items_r_m.empty else None
                        )
                        st.rerun()
                    if col_bm3.button("🖨️ Reporte Gastos", key="p_g_m", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE EGRESOS", 
                            {"id": f"MG-{mes_sel.replace('-','')}", "fecha": f"{mes_sel}-01", "cliente": "Administración / Control de Costos", "total": g_m, "nota": f"Análisis general de egresos e inversiones liquidadas durante el mes: {mes_sel}."},
                            items_g_m.to_dict('records') if not items_g_m.empty else None
                        )
                        st.rerun()
                    if col_bm4.button("🖨️ Reporte Depósitos", key="p_d_m", disabled=not puede_modificar):
                        st.session_state.print_html = self.generar_informe_hoja_unica(
                            "INFORME MENSUAL DE DEPÓSITOS", 
                            {"id": f"MD-{mes_sel.replace('-','')}", "fecha": f"{mes_sel}-01", "cliente": "Contabilidad General / Bancos", "total": d_m, "nota": f"Conciliación bancaria consolidada acumulada del período: {mes_sel}."},
                            items_d_m.to_dict('records') if not items_d_m.empty else None
                        )
                        st.rerun()
                else:
                    st.info("No se hallaron transacciones mensuales.")

        # DISPARADOR DE IMPRESIÓN (Gestión limpia del ciclo de vida del iframe)
        if "print_html" in st.session_state and st.session_state.print_html:
            html_code = st.session_state.print_html
            # Consumimos y limpiamos el estado preventivamente para que no repita el bucle de impresión en rerruns fútiles
            st.session_state.print_html = None
            components.html(html_code, height=0, width=0)