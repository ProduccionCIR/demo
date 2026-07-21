# ventas.py
import streamlit as st
import pandas as pd
import base64
import os
import io
import math
import sqlite3
import json
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

class ModuloVentas:
    def __init__(self, db):
        if hasattr(db, 'db_path'):
            self.db_path = db.db_path
        elif isinstance(db, str):
            self.db_path = db
        else:
            self.db_path = "local.db"
            
        self.logo_path = "logo.png"

    def get_connection(self):
        """Retorna una conexión limpia a la base de datos SQLite local"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  
        return conn

    def sanitize_data(self, data):
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(v) for v in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return 0.0
            return data
        else:
            return data

    def get_image_base64(self, path):
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except:
            return None

    def generar_pdf_factura(self, datos, es_offshore=False):
        logo_b64 = self.get_image_base64(self.logo_path)
        tipo_doc = "INVOICE / FACTURA OFFSHORE" if es_offshore else "FACTURA DE VENTA / INVOICE "
        
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page { size: A4; margin: 10mm; }
                body { font-family: 'Courier New', Courier, monospace; color: #000; font-size: 9pt; margin: 0; }
                .header-wrapper { display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 5px; }
                .logo-box { width: 30%; }
                .company-info { width: 70%; text-align: right; font-size: 8pt; line-height: 1.2; }
                .doc-title { text-align: center; font-size: 15pt; font-weight: bold; text-decoration: underline; margin: 10px 0; }
                .info-table { width: 100%; margin-top: 10px; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 5px 0; }
                .items-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                .items-table th { border-bottom: 1px solid #000; border-top: 1px solid #000; padding: 6px; text-align: left; font-size: 8pt; background-color: #f2f2f2; }
                .items-table td { padding: 5px; vertical-align: top; border-bottom: 1px solid #eee; }
                .totals-container { margin-top: 30px; display: flex; justify-content: space-between; page-break-inside: avoid; }
                .summary-box { width: 48%; border: 1px solid #000; padding: 8px; background-color: #fafafa; }
                .final-totals { width: 45%; text-align: right; line-height: 1.6; }
                .grand-total { font-size: 12pt; font-weight: bold; border-top: 2px solid #000; margin-top: 5px; padding-top: 5px; }
                .text-right { text-align: right; }
            </style>
        </head>
        <body>
            <div class="header-wrapper">
                <div class="logo-box">
                    {% if logo %}<img src="data:image/png;base64,{{ logo }}" style="max-width: 150px;">{% endif %}
                </div>
                <div class="company-info">
                    <strong style="font-size: 11pt;">SONIX LTD. #1</strong><br>
                    RUC: 1570526-1-660611 DV80 | TEL: (507) 6239-7128 <br>
                    LOTE 1, DE LA MANZANA 26-A, AVE. SAN ELADIO CALLE 17 ,ZONA LIBRE DE COLÓN , REPÚBLICA PANAMÁ. 
                </div>
            </div>
            <div class="doc-title">{{ tipo_doc }}</div>
            <table class="info-table">
                <tr>
                    <td width="60%"><strong>CLIENTE:</strong> {{ cliente | upper }}</td>
                    <td width="40%" class="text-right"><strong>FECHA:</strong> {{ fecha }}</td>
                </tr>
                <tr>
                    <td><strong>DOC N°:</strong> {{ num_fact }}</td>
                    <td class="text-right"><strong>VÍA:</strong> {{ via | upper }}</td>
                </tr>
            </table>
            <table class="items-table">
                <thead>
                    <tr>
                        <th width="40%">DESCRIPCIÓN</th>
                        <th width="10%" style="text-align:center;">BULTOS</th>
                        <th width="10%" style="text-align:center;">CANT.</th>
                        <th width="15%" class="text-right">PRECIO</th>
                        <th width="25%" class="text-right">SUBTOTAL $</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in detalles %}
                    <tr>
                        <td>{{ item.nombre }}<br><small>Ref: {{ item.id }}</small></td>
                        <td style="text-align:center;">{{ item.get('bultos', 0) }}</td>
                        <td style="text-align:center;">{{ item.cantidad }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(item.precio) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(item.subtotal) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <div class="totals-container">
                <div class="summary-box">
                    <strong style="text-decoration: underline;">RESUMEN LOGÍSTICO</strong><br>
                    <table style="width: 100%; font-size: 8pt; margin-top: 5px;">
                        <tr><td>TOTAL BULTOS:</td><td class="text-right"><strong>{{ total_bultos }}</strong></td></tr>
                        <tr><td>TOTAL PESO:</td><td class="text-right"><strong>{{ "{:,.2f}".format(total_peso) }} KG</strong></td></tr>
                        <tr><td>TOTAL CUBICAJE:</td><td class="text-right"><strong>{{ "{:,.3f}".format(total_cbm) }} m³</strong></td></tr>
                        <tr><td>TOTAL PIEZAS:</td><td class="text-right">{{ total_cant }}</td></tr>
                    </table>
                </div>
                <div class="final-totals">
                    FLETE / MANEJO: $ {{ "{:,.2f}".format(flete) }}<br>
                    DESCUENTO: $ {{ "{:,.2f}".format(descuento) }}<br>
                    <div class="grand-total">TOTAL NETO: $ {{ "{:,.2f}".format(total_neto) }}</div>
                </div>
            </div>
            <div style="margin-top: 30px; font-size: 7pt; text-align: center; color: #666;">
                SISTEMA RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO
            </div>
        </body>
        </html>
        """
        
        raw_detalles = datos.get('detalle', datos.get('detalles', []))
        if isinstance(raw_detalles, str):
            try: detalles = json.loads(raw_detalles)
            except: detalles = []
        else:
            detalles = raw_detalles if raw_detalles is not None else []

        t_bultos = sum(int(i.get('bultos', 0)) for i in detalles if isinstance(i, dict))
        t_peso = sum(float(i.get('peso', 0.0)) for i in detalles if isinstance(i, dict))
        t_cbm = sum(float(i.get('cbm', 0.0)) for i in detalles if isinstance(i, dict))
        t_cant = sum(int(i.get('cantidad', 0)) for i in detalles if isinstance(i, dict))
        
        total_neto = float(datos.get('total', 0.0))
        flete = float(datos.get('flete', 0.0))
        desc = float(datos.get('descuento', 0.0))

        tm = Template(html_template)
        html_res = tm.render(
            logo=logo_b64, tipo_doc=tipo_doc,
            num_fact=str(datos.get('num_fact', 'N/A')),
            fecha=str(datos.get('fecha'))[:10],
            cliente=datos.get('cliente', 'S/N'),
            via=datos.get('via_despacho', datos.get('via', 'N/A')),
            detalles=detalles,
            flete=flete, descuento=desc,
            total_neto=total_neto,
            total_bultos=t_bultos, total_peso=t_peso, 
            total_cbm=t_cbm, total_cant=t_cant
        )

        pdf_out = io.BytesIO()
        HTML(string=html_res).write_pdf(pdf_out)
        return pdf_out.getvalue()

    def formulario_venta(self, es_offshore=False):
        tipo_str = "off" if es_offshore else "zlc"
        if f'cart_{tipo_str}' not in st.session_state: 
            st.session_state[f'cart_{tipo_str}'] = []

        conn = self.get_connection()
        
        clientes_raw = conn.execute("SELECT nombre FROM clientes").fetchall()
        lista_clientes = ["--"] + [c['nombre'] for c in clientes_raw]
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            cli = c1.selectbox(f"👤 Cliente", lista_clientes, key=f"cli_{tipo_str}")
            via = c2.selectbox("🚢 Vía Despacho", ["Marítima", "Terrestre", "Aérea", "Traspaso"], key=f"via_{tipo_str}")
            flete = c3.number_input("💰 Flete/Manejo $", min_value=0.0, step=0.01, value=0.0, format="%.2f", key=f"flete_{tipo_str}")
            desc = c4.number_input("📉 Descuento $", min_value=0.0, step=0.01, value=0.0, format="%.2f", key=f"desc_{tipo_str}")

        st.write("### 🔍 Selección de Productos")
        productos_raw = conn.execute("SELECT REFERENCIA, MARCA, DESCRIPCION, CANTIDAD, COSTO_UNIT FROM productos").fetchall()
        
        if productos_raw:
            df_p = pd.DataFrame([dict(p) for p in productos_raw])
            for col in ['REFERENCIA', 'MARCA', 'DESCRIPCION']:
                df_p[col] = df_p[col].fillna('').astype(str).str.strip()
            
            search = st.text_input("Buscar producto...", key=f"search_{tipo_str}")
            if search:
                df_p = df_p[df_p["REFERENCIA"].str.contains(search, case=False) | 
                            df_p["DESCRIPCION"].str.contains(search, case=False)]

            st.dataframe(df_p[["REFERENCIA", "DESCRIPCION", "CANTIDAD", "COSTO_UNIT"]], use_container_width=True, hide_index=True)
            
            with st.expander("➕ Configurar Línea", expanded=True):
                lista_refs = df_p["REFERENCIA"].unique().tolist()
                sel_ref = st.selectbox("Producto", lista_refs, key=f"sel_ref_{tipo_str}")
                it = df_p[df_p["REFERENCIA"] == sel_ref].iloc[0]
                
                c1, c2, c3, c4, c5 = st.columns(5)
                costo_base = float(it['COSTO_UNIT']) if pd.notnull(it['COSTO_UNIT']) else 0.0
                
                pr = c1.number_input("Precio Venta", value=costo_base, format="%.2f", key=f"pr_{tipo_str}")
                ct = c2.number_input("Cantidad", min_value=1, value=1, key=f"ct_{tipo_str}")
                bu = c3.number_input("Bultos", min_value=1, value=1, key=f"bu_{tipo_str}")
                pe = c4.number_input("Peso (KG)", min_value=0.0, value=0.0, format="%.2f", key=f"pe_{tipo_str}")
                cb = c5.number_input("CBM (m³)", min_value=0.0, value=0.0, format="%.3f", key=f"cb_{tipo_str}")

                if st.button("Añadir al Carrito", use_container_width=True, key=f"add_{tipo_str}"):
                    nuevo_item = {
                        "id": str(it["REFERENCIA"]), 
                        "nombre": str(it["DESCRIPCION"]), 
                        "cantidad": int(ct), 
                        "precio": float(pr), 
                        "subtotal": float(ct * pr),
                        "bultos": int(bu), 
                        "peso": float(pe), 
                        "cbm": float(cb)
                    }
                    st.session_state[f'cart_{tipo_str}'].append(self.sanitize_data(nuevo_item))
                    conn.close()
                    st.rerun()

        carrito = st.session_state[f'cart_{tipo_str}']
        if carrito:
            st.divider()
            
            # --- NUEVA SECCIÓN DE MONITOREO EN TIEMPO REAL ---
            st.write("### 🛒 Detalle de Artículos en la Factura Actual")
            df_carrito = pd.DataFrame(carrito)
            
            # Renombrar columnas para una presentación impecable en pantalla
            df_display = df_carrito.rename(columns={
                "id": "Referencia",
                "nombre": "Descripción",
                "cantidad": "Cant.",
                "precio": "Precio ($)",
                "subtotal": "Subtotal ($)",
                "bultos": "Bultos",
                "peso": "Peso (KG)",
                "cbm": "CBM (m³)"
            })
            
            # Formatear la tabla visual
            st.dataframe(
                df_display[["Referencia", "Descripción", "Bultos", "Cant.", "Precio ($)", "Subtotal ($)", "Peso (KG)", "CBM (m³)"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Botón para limpiar/resetear la preparación por si necesitas cambiar datos
            if st.button("🗑️ Vaciar Carrito / Empezar de nuevo", type="secondary", key=f"clear_{tipo_str}"):
                st.session_state[f'cart_{tipo_str}'] = []
                conn.close()
                st.rerun()
            # -------------------------------------------------

            total_mercancia = sum(i['subtotal'] for i in carrito)
            total_neto = (total_mercancia + flete) - desc

            st.metric("TOTAL NETO", f"${total_neto:,.2f}", delta=f"Desc: -${desc:,.2f}")
            
            if st.button(f"🚀 Finalizar Factura", type="primary", use_container_width=True, key=f"btn_save_{tipo_str}"):
                if cli == "--":
                    st.error("⚠️ Error: Debe seleccionar un cliente.")
                    conn.close()
                    return

                for item in carrito:
                    prod_stock = conn.execute("SELECT CANTIDAD FROM productos WHERE REFERENCIA = ?", (item['id'],)).fetchone()
                    if prod_stock and int(prod_stock['CANTIDAD']) < item['cantidad']:
                        st.error(f"❌ Stock Insuficiente para {item['nombre']}. Disponible local: {prod_stock['CANTIDAD']}")
                        conn.close()
                        return

                anio_actual = datetime.now().strftime("%Y")
                row = conn.execute("SELECT MAX(num_fact) as max_fact FROM ventas WHERE CAST(num_fact AS TEXT) LIKE ?", (f"{anio_actual}%",)).fetchone()
                
                secuencia = 1
                if row and row['max_fact']:
                    secuencia = int(str(row['max_fact'])[-3:]) + 1
                
                num_fact_final = int(f"{anio_actual}{secuencia:03d}")
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                try:
                    conn.execute("""
                        INSERT INTO ventas (num_fact, cliente, total, flete, descuento, detalle, via_despacho, fecha, sincronizado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (num_fact_final, cli, total_neto, flete, desc, json.dumps(carrito), via, fecha_hoy))
                    
                    for i in carrito:
                        prod_stock = conn.execute("SELECT CANTIDAD FROM productos WHERE REFERENCIA = ?", (i['id'],)).fetchone()
                        if prod_stock:
                            nueva_q = int(prod_stock['CANTIDAD']) - i['cantidad']
                            conn.execute("UPDATE productos SET CANTIDAD = ? WHERE REFERENCIA = ?", (nueva_q, i['id']))
                    
                    conn.commit()
                    st.success(f"✅ Factura {num_fact_final} guardada correctamente de forma local.")
                    st.session_state[f'cart_{tipo_str}'] = []
                    conn.close()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error de base de datos local: {e}")
                    
        conn.close()

    def render_historial(self):
        st.subheader("📜 Historial de Ventas Local")
        conn = self.get_connection()
        ventas = conn.execute("SELECT * FROM ventas ORDER BY num_fact DESC").fetchall()
        
        if not ventas:
            st.info("No hay ventas registradas.")
            conn.close()
            return
        
        for row_v in ventas:
            v = dict(row_v)
            num_visible = int(v['num_fact'])
            sinc_status = "☁️ Sincronizado" if v.get('sincronizado') == 1 else "💻 Local"
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**Factura #{num_visible}** | Cliente: {v['cliente']}")
                c1.caption(f"Fecha: {v['fecha'][:10]} | Total: ${float(v['total']):,.2f} | **[{sinc_status}]**")
                
                pdf_data = self.generar_pdf_factura(v)
                c2.download_button("📄 PDF", pdf_data, f"FACT_{num_visible}.pdf", key=f"pdf_h_{num_visible}")
        
        conn.close()

    def render(self):
        st.header("💰 RAV System - Módulo de Ventas Local")
        t1, t2 = st.tabs(["📄 Nueva Factura", "📜 Historial"])
        with t1:
            sub1, sub2 = st.tabs(["Zona Libre (ZLC)", "Offshore (Export)"])
            with sub1: self.formulario_venta(es_offshore=False)
            with sub2: self.formulario_venta(es_offshore=True)
        with t2:
            self.render_historial()