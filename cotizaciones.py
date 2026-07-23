import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML
import io
import json

class ModuloCotizaciones:
    def __init__(self, db):
        self.db = db
        self.logo_path = "logo.png"  

    def get_image_base64(self, path):
        """Convierte el logo a base64 para que sea portable al PDF"""
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except:
            return None

    def generar_pdf_profesional(self, datos, cliente_info, tipo="PROFORMA"):
        """Genera un PDF con logo y formato profesional logístico para Dana"""
        logo_b64 = self.get_image_base64(self.logo_path)
        
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page { size: A4; margin: 10mm; }
                body { font-family: 'Arial', sans-serif; color: #000; font-size: 8.5pt; margin: 0; }
                .header-wrapper { display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 5px; }
                .logo-box { width: 30%; }
                .company-info { width: 70%; text-align: right; font-size: 8pt; line-height: 1.3; }
                .doc-title { text-align: center; font-size: 14pt; font-weight: bold; text-decoration: underline; margin: 10px 0; letter-spacing: 1px; }
                .info-table { width: 100%; margin-top: 5px; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 5px 0; line-height: 1.4; }
                
                .items-table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000; }
                .items-table th { 
                    border: 1px solid #000; 
                    padding: 5px; 
                    text-align: center; 
                    font-size: 8.5pt; 
                    font-weight: bold;
                    background-color: #e0e0e0; 
                }
                .items-table td { 
                    padding: 6px 4px; 
                    vertical-align: middle; 
                    border: 1px solid #000; 
                    font-size: 8pt;
                }
                
                .totals-container { margin-top: 15px; display: flex; justify-content: space-between; page-break-inside: avoid; }
                .summary-box { width: 48%; border: 1px solid #000; padding: 8px; font-size: 8.5pt; line-height: 1.5; }
                .final-totals { width: 40%; text-align: right; line-height: 1.6; font-size: 9pt; }
                .grand-total { font-size: 11pt; font-weight: bold; border-top: 2px solid #000; margin-top: 4px; padding-top: 4px; }
                .text-right { text-align: right; }
                .text-center { text-align: center; }
                .footer-brand { text-align: center; margin-top: 30px; font-size: 7.5pt; font-weight: bold; letter-spacing: 1px; color: #444; }
            </style>
        </head>
        <body>
            <div class="header-wrapper">
                <div class="logo-box">
                    {% if logo %}
                    <img src="data:image/png;base64,{{ logo }}" style="max-width: 150px;">
                    {% endif %}
                </div>
                <div class="company-info">
                    <strong style="font-size: 11pt;">DANA INTERCIONAL </strong><br>
                    RUC: 12440-181-123510 DV83 | TEL: (507) 446-1326 <br>
                    E-MAIL: gerencia@danainternacional.com<br>
                    CALLE 15 & 16, ZONA LIBRE DE COLÓN, PANAMÁ                     
                </div>
            </div>
            
            <div class="doc-title">{{ tipo }}</div>
            
            <table class="info-table">
                <tr>
                    <td width="60%"><strong>VENDIDO A:</strong> {{ cliente | upper }}</td>
                    <td width="40%" class="text-right"><strong>FECHA:</strong> {{ fecha }}</td>
                </tr>
                <tr>
                    <td><strong>REFERENCIA:</strong> {{ id }}</td>
                    <td class="text-right"><strong>TÉRMINOS:</strong> {{ terminos }}</td>
                </tr>
            </table>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th width="40%">PRODUCTO</th>
                        <th width="12%">EMPAQUE</th>
                        <th width="10%">PESO (KG)</th>
                        <th width="10%">CUBIC. (M3)</th>
                        <th width="8%">CANTIDAD</th>
                        <th width="7%">U/M</th>
                        <th width="8%">PRECIO</th>
                        <th width="10%">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in detalles %}
                    <tr>
                        <td>
                            {{ item.nombre }}
                            {% if item.codigo_barra %}
                            <br><small style="color: #555;">CB: {{ item.codigo_barra }}</small>
                            {% endif %}
                        </td>
                        <td class="text-center">{{ item.get('empaque', '') }}</td>
                        <td class="text-right">{{ "{:,.1f}".format(item.get('peso_kg', 0.0)|float) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(item.get('cubic_m3', 0.0)|float) }}</td>
                        <td class="text-center">{{ item.cantidad }}</td>
                        <td class="text-center">{{ item.get('um', 'CAJA') | upper }}</td>
                        <td class="text-right">${{ "{:,.2f}".format(item.precio|float) }}</td>
                        <td class="text-right">${{ "{:,.2f}".format(item.subtotal|float) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="totals-container">
                <div class="summary-box">
                    <strong>RESUMEN LOGÍSTICO:</strong><br>
                    TOTAL BULTOS: {{ total_bultos }}<br>
                    TOTAL PIEZAS: {{ total_cant }}<br>
                    TOTAL PESO: {{ "{:,.2f}".format(total_peso) }} KG<br>
                    TOTAL CUBICACIÓN: {{ "{:,.2f}".format(total_cubic) }} M3<br>
                    <small>ORIGEN: ZONA LIBRE DE COLÓN</small>
                </div>
                <div class="final-totals">
                    SUB-TOTAL: $ {{ "{:,.2f}".format(total) }}<br>
                    TRASPASO: $ 0.00<br>
                    <div class="grand-total">TOTAL NETO: $ {{ "{:,.2f}".format(total) }}</div>
                </div>
            </div>
            <div class="footer-brand">RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO</div>
        </body>
        </html>
        """
        
        raw_detalles = datos.get('detalles', datos.get('detalle', []))
        if isinstance(raw_detalles, str):
            try: detalles = json.loads(raw_detalles)
            except: detalles = []
        else:
            detalles = raw_detalles if raw_detalles is not None else []

        t_bultos = sum(int(i.get('bultos', 0)) for i in detalles if isinstance(i, dict))
        t_cant = sum(int(i.get('cantidad', 0)) for i in detalles if isinstance(i, dict))
        t_peso = sum(float(i.get('peso_kg', 0.0)) for i in detalles if isinstance(i, dict))
        t_cubic = sum(float(i.get('cubic_m3', 0.0)) for i in detalles if isinstance(i, dict))

        tm = Template(html_template)
        html_res = tm.render(
            logo=logo_b64,
            tipo=tipo,
            id=datos.get('num_cot', datos.get('num_fact', '0')),
            fecha=datos.get('fecha'),
            cliente=cliente_info,
            detalles=detalles,
            total=float(datos.get('total', 0)),
            total_bultos=t_bultos,
            total_cant=t_cant,
            total_peso=t_peso,
            total_cubic=t_cubic,
            terminos="AL CONTADO" if tipo == "FACTURA" else "CRÉDITO ZL"
        )

        pdf_out = io.BytesIO()
        HTML(string=html_res).write_pdf(pdf_out)
        return pdf_out.getvalue()

    def vista_crear(self):
        if 'cart_cot' not in st.session_state: 
            st.session_state.cart_cot = []
        if 'cli_editable' not in st.session_state:
            st.session_state.cli_editable = "--"
        
        clientes = self.db.fetch("clientes")
        if not clientes:
            st.warning("No hay clientes registrados.")
            return
            
        df_c = pd.DataFrame(clientes)
        lista_clientes = ["--"] + df_c['nombre'].tolist()
        idx_def = 0
        if st.session_state.cli_editable in lista_clientes:
            idx_def = lista_clientes.index(st.session_state.cli_editable)

        cli_sel = st.selectbox("👤 Seleccionar Cliente", lista_clientes, index=idx_def)
        st.session_state.cli_editable = cli_sel
        
        if cli_sel != "--":
            with st.container(border=True):
                prods = self.db.fetch("productos")
                if prods:
                    df_p = pd.DataFrame(prods)
                    
                    # Normalización defensiva para el caso del campo de base de datos 'codigo_barra'
                    if 'codigo_barra' in df_p.columns:
                        df_p['COD_BARRA'] = df_p['codigo_barra'].fillna('').astype(str).str.strip()
                    elif 'COD_BARRA' in df_p.columns:
                        df_p['COD_BARRA'] = df_p['COD_BARRA'].fillna('').astype(str).str.strip()
                    else:
                        df_p['COD_BARRA'] = ""

                    df_p['REFERENCIA'] = df_p['REFERENCIA'].fillna('').astype(str).str.strip()
                    df_p['MARCA'] = df_p['MARCA'].fillna('').astype(str).str.strip()
                    df_p['DESCRIPCION'] = df_p['DESCRIPCION'].fillna('').astype(str).str.strip()
                    
                    def build_search_string(row):
                        tokens = []
                        if row['COD_BARRA']: tokens.append(f"[{row['COD_BARRA']}]") 
                        if row['REFERENCIA']: tokens.append(row['REFERENCIA'])
                        if row['MARCA']: tokens.append(row['MARCA'])
                        if row['DESCRIPCION']: tokens.append(row['DESCRIPCION'])
                        return " | ".join(tokens) if tokens else "Producto Sin Datos"

                    df_p['search'] = df_p.apply(build_search_string, axis=1)
                    
                    p_sel = st.selectbox("🔍 Buscar Producto (Código de Barra, Referencia, Marca, Descripción)", ["--"] + df_p['search'].tolist())
                    
                    if p_sel != "--":
                        it = df_p[df_p['search'] == p_sel].iloc[0]
                        
                        raw_empaque = it.get('EMPAQUE', '')
                        raw_peso = it.get('PESO', 0.0)
                        raw_cubic = it.get('CUBICAJE', 0.0)
                        raw_um = it.get('U/M', 'CAJA')
                        raw_precio = it.get('COSTO UNIT', 0.0)
                        raw_cb = it.get('COD_BARRA', '')

                        st.markdown("### 📋 Datos de Envío (Campos Editables / Manuales)")
                        
                        cc1, cc2, cc3, cc4 = st.columns(4)
                        empaque = cc1.text_input("Empaque", value=str(raw_empaque if pd.notnull(raw_empaque) else ""))
                        peso_kg = cc2.number_input("Peso Total (KG)", value=float(raw_peso if pd.notnull(raw_peso) else 0.0), step=0.1)
                        cubic_m3 = cc3.number_input("Cubicación Total (M3)", value=float(raw_cubic if pd.notnull(raw_cubic) else 0.0), step=0.01)
                        um = cc4.text_input("Unidad de Medida (U/M)", value=str(raw_um if pd.notnull(raw_um) else "CAJA"))

                        c1, c2, c3, c4 = st.columns(4)
                        precio = c1.number_input("Precio $", value=float(raw_precio if pd.notnull(raw_precio) else 0.0))
                        cant = c2.number_input("Cantidad (Piezas)", min_value=1, value=1)
                        bultos = c3.number_input("Bultos", min_value=0, value=1)
                        
                        if c4.button("➕ Añadir al Detalle", use_container_width=True):
                            st.session_state.cart_cot.append({
                                "id": str(it['REFERENCIA']), 
                                "nombre": f"{it['DESCRIPCION']}".strip(), 
                                "codigo_barra": raw_cb, 
                                "cantidad": cant, 
                                "bultos": bultos,
                                "empaque": empaque,
                                "peso_kg": peso_kg,
                                "cubic_m3": cubic_m3,
                                "um": um,
                                "precio": precio, 
                                "subtotal": cant * precio
                            })
                            st.rerun()

            if st.session_state.cart_cot:
                st.subheader("🛒 Detalle de la Proforma")
                
                h1, h2, h3, h4, h5, h6 = st.columns([1.5, 2.5, 1, 1, 1.5, 0.5])
                h1.caption("REFERENCIA")
                h2.caption("DESCRIPCIÓN / LOGÍSTICA")
                h3.caption("CANT.")
                h4.caption("PRECIO")
                h5.caption("SUBTOTAL")
                h6.caption("ACC")

                for index, item in enumerate(st.session_state.cart_cot):
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2.5, 1, 1, 1.5, 0.5])
                        
                        col1.write(f"**{item['id']}**")
                        if item.get('codigo_barra'):
                            col1.caption(f"CB: {item['codigo_barra']}")
                            
                        col2.write(f"{item['nombre']}")
                        col2.caption(f"Emp: {item.get('empaque','')} | Peso: {item.get('peso_kg',0)}KG | Vol: {item.get('cubic_m3',0)}M3 | U/M: {item.get('um','')}")
                        
                        new_cant = col3.number_input("n_cant", value=item['cantidad'], min_value=1, key=f"q_{index}", label_visibility="collapsed")
                        new_price = col4.number_input("n_pr", value=float(item['precio']), key=f"p_{index}", label_visibility="collapsed")
                        
                        if new_cant != item['cantidad'] or new_price != item['precio']:
                            st.session_state.cart_cot[index]['cantidad'] = new_cant
                            st.session_state.cart_cot[index]['precio'] = new_price
                            st.session_state.cart_cot[index]['subtotal'] = new_cant * new_price
                            st.rerun()

                        col5.write(f"${st.session_state.cart_cot[index]['subtotal']:,.2f}")
                        
                        if col6.button("🗑️", key=f"del_{index}"):
                            st.session_state.cart_cot.pop(index)
                            st.rerun()
                
                total_cot = sum(i['subtotal'] for i in st.session_state.cart_cot)
                st.divider()
                st.markdown(f"### Total General: ${total_cot:,.2f}")

                if st.button("💾 Guardar Documento Proforma ZL", type="primary"):
                    anio_actual = datetime.now().strftime("%Y")
                    c_existentes = self.db.fetch("cotizaciones")
                    
                    secuencia = 1
                    if c_existentes:
                        docs_anio = [d for d in c_existentes if str(d.get('num_cot', '')).startswith(anio_actual)]
                        if docs_anio:
                            max_sec = max(int(str(d.get('num_cot', '0'))[-3:]) for d in docs_anio)
                            secuencia = max_sec + 1
                    
                    id_doc_final = int(f"{anio_actual}{secuencia:03d}")

                    payload = {
                        "num_cot": id_doc_final,
                        "cliente": cli_sel, 
                        "total": total_cot,
                        "detalles": st.session_state.cart_cot,
                        "fecha": datetime.now().strftime("%Y-%m-%d"), 
                        "estado": "Pendiente"
                    }
                    
                    self.db.client.table("cotizaciones").insert(payload).execute()
                    st.session_state.cart_cot = []
                    st.session_state.cli_editable = "--"
                    st.success(f"Documento {id_doc_final} procesado exitosamente.")
                    st.rerun()

    def facturar(self, cot):
        try:
            anio_actual = datetime.now().strftime("%Y")
            v_ex = self.db.fetch("ventas")
            
            secuencia = 1
            if v_ex:
                docs_fact_anio = [v for v in v_ex if str(v.get('num_fact', '')).startswith(anio_actual)]
                if docs_fact_anio:
                    max_sec = max(int(str(v.get('num_fact', '0'))[-3:]) for v in docs_fact_anio)
                    secuencia = max_sec + 1
            
            n_f = int(f"{anio_actual}{secuencia:03d}")

            raw_items = cot.get('detalles', cot.get('detalle', []))
            if isinstance(raw_items, str): items_processed = json.loads(raw_items)
            else: items_processed = raw_items

            venta = {
                "num_fact": n_f, 
                "cliente": cot['cliente'], 
                "total": cot['total'], 
                "detalle": items_processed,
                "fecha": datetime.now().strftime("%Y-%m-%d")
            }
            self.db.client.table("ventas").insert(venta).execute()
            
            for item in items_processed:
                if item.get('id'):
                    curr = self.db.client.table("productos").select("CANTIDAD").eq("REFERENCIA", str(item['id'])).execute()
                    if curr.data:
                        nueva_cant = int(curr.data[0]['CANTIDAD']) - int(item['cantidad'])
                        self.db.client.table("productos").update({"CANTIDAD": nueva_cant}).eq("REFERENCIA", str(item['id'])).execute()
            
            self.db.client.table("cotizaciones").update({"estado": "Facturado"}).eq("id", cot['id']).execute()
            st.success(f"Factura Comercial {n_f} generada e inventario actualizado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error en facturación: {e}")

    def render(self):
        st.header("📄 Cotizaciones y Proformas - ZL")
        t1, t2 = st.tabs(["🆕 Crear Documento", "📜 Historial de Registros"])
        
        with t1: 
            self.vista_crear()
        with t2:
            cots = self.db.fetch("cotizaciones")
            if cots:
                for c in sorted(cots, key=lambda x: x.get('num_cot', 0), reverse=True):
                    id_visible = c.get('num_cot', '0')
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([2, 1, 1.2, 1.3])
                        
                        col1.write(f"**{c['cliente']}**")
                        col1.caption(f"Doc N°: {id_visible} | Fecha: {c['fecha']} | Estado: {c['estado']}")
                        col2.write(f"${float(c['total']):,.2f}")
                        
                        pdf = self.generar_pdf_profesional(c, c['cliente'])
                        col3.download_button("📥 Descargar PDF", pdf, f"Proforma_{id_visible}.pdf", key=f"dl_{c['id']}", use_container_width=True)
                        
                        raw_det = c['detalles']
                        if isinstance(raw_det, str):
                            try: lista_detalles = json.loads(raw_det)
                            except: lista_detalles = []
                        else:
                            lista_detalles = raw_det

                        if c['estado'] == "Pendiente":
                            c3_1, c3_2 = col4.columns(2)
                            
                            if c3_1.button("⚙️ Editar", key=f"mod_{c['id']}", use_container_width=True):
                                st.session_state.cart_cot = lista_detalles
                                st.session_state.cli_editable = c['cliente']
                                self.db.client.table("cotizaciones").delete().eq("id", c['id']).execute()
                                st.success("Cargado en el editor. Modifique los campos necesarios.")
                                st.rerun()
                                
                            if c3_2.button("🚀 Facturar", key=f"f_{c['id']}", use_container_width=True):
                                self.facturar(c)
                                
                        if col4.button("🗑️ Eliminar Registro", key=f"rem_db_{c['id']}", use_container_width=True):
                            self.db.client.table("cotizaciones").delete().eq("id", c['id']).execute()
                            st.success("Documento eliminado del sistema.")
                            st.rerun()
            else:
                st.info("No se registran documentos en el historial.")