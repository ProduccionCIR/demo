# cotizaciones.py
import streamlit as st
import pandas as pd
import base64
import os
import sqlite3
import json
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML
import io

class ModuloCotizaciones:
    def __init__(self, db_path="local.db"):
        self.db_path = db_path
        self.logo_path = "eslogo.png"  # Ajustado al logo oficial del sistema
        self.inicializar_tablas_locales()

    def get_connection(self):
        """Retorna una conexión limpia a la base de datos SQLite local"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  
        return conn

    def inicializar_tablas_locales(self):
        """Asegura que existan las tablas locales con la estructura correcta"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Crear tabla cotizaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                num_cot INTEGER PRIMARY KEY,
                cliente TEXT,
                total REAL,
                detalles TEXT,
                fecha TEXT,
                estado TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        """)
        
        # 2. Crear tabla ventas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                num_fact INTEGER PRIMARY KEY,
                cliente TEXT,
                total REAL,
                detalle TEXT,
                fecha TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        """)
        
        # Migración al vuelo: Por si la tabla existía en local.db pero no tenía la columna 'sincronizado'
        try:
            cursor.execute("ALTER TABLE cotizaciones ADD COLUMN sincronizado INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass  # Ya existía la columna
            
        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN sincronizado INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass  # Ya existía la columna

        conn.commit()
        conn.close()

    def get_image_base64(self, path):
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except:
            return None

    def generar_pdf_profesional(self, datos, cliente_info, tipo="PROFORMA"):
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
                    <strong style="font-size: 11pt;">SONIX LTD. #1</strong><br>
                    RUC: 1570526-1-660611 DV80 | TEL: (507) 6239-7128 <br>
                    E-MAIL: traficosonix@gmail.com<br>
                    CALLE 15 & 16, ZONA LIBRE DE COLÓN, REP. DE PANAMÁ
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
                        <th width="10%">CUBIC. (P3)</th>
                        <th width="8%">CANTIDAD</th>
                        <th width="7%">U/M</th>
                        <th width="8%">PRECIO</th>
                        <th width="10%">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in detalles %}
                    <tr>
                        <td>{{ item.nombre }}</td>
                        <td class="text-center">{{ item.get('empaque', '') }}</td>
                        <td class="text-right">{{ "{:,.1f}".format(item.get('peso_kg', 0.0)|float) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(item.get('cubic_p3', 0.0)|float) }}</td>
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
                    TOTAL CUBICACIÓN: {{ "{:,.2f}".format(total_cubic) }} P3<br>
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
        t_cubic = sum(float(i.get('cubic_p3', 0.0)) for i in detalles if isinstance(i, dict))

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
        
        conn = self.get_connection()
        clientes = conn.execute("SELECT nombre FROM clientes").fetchall()
        
        if not clientes:
            st.warning("No hay clientes registrados en la base de datos local.")
            conn.close()
            return
            
        lista_clientes = ["--"] + [c['nombre'] for c in clientes]
        idx_def = 0
        if st.session_state.cli_editable in lista_clientes:
            idx_def = lista_clientes.index(st.session_state.cli_editable)

        cli_sel = st.selectbox("👤 Seleccionar Cliente", lista_clientes, index=idx_def)
        st.session_state.cli_editable = cli_sel
        
        if cli_sel != "--":
            with st.container(border=True):
                prods = conn.execute("SELECT REFERENCIA, MARCA, DESCRIPCION, EMPAQUE, PESO, CUBICAJE, [U/M], PRECIO FROM productos").fetchall()
                
                if prods:
                    df_p = pd.DataFrame([dict(p) for p in prods])
                    for col in ['REFERENCIA', 'MARCA', 'DESCRIPCION']:
                        df_p[col] = df_p[col].fillna('').astype(str).str.strip()
                    
                    df_p['search'] = df_p.apply(lambda r: " | ".join([x for x in [r['REFERENCIA'], r['MARCA'], r['DESCRIPCION']] if x]), axis=1)
                    p_sel = st.selectbox("🔍 Buscar Producto", ["--"] + df_p['search'].tolist())
                    
                    if p_sel != "--":
                        it = df_p[df_p['search'] == p_sel].iloc[0]
                        
                        st.markdown("### 📋 Datos de Envío (Campos Editables)")
                        cc1, cc2, cc3, cc4 = st.columns(4)
                        empaque = cc1.text_input("Empaque", value=str(it['EMPAQUE'] if pd.notnull(it['EMPAQUE']) else ""))
                        peso_kg = cc2.number_input("Peso Total (KG)", value=float(it['PESO'] if pd.notnull(it['PESO']) else 0.0), step=0.1)
                        cubic_p3 = cc3.number_input("Cubicación Total (P3)", value=float(it['CUBICAJE'] if pd.notnull(it['CUBICAJE']) else 0.0), step=0.01)
                        um = cc4.text_input("Unidad de Medida (U/M)", value=str(it['U/M'] if pd.notnull(it['U/M']) else "CAJA"))

                        c1, c2, c3, c4 = st.columns(4)
                        precio = c1.number_input("Precio $", value=float(it['PRECIO'] if pd.notnull(it['PRECIO']) else 0.0))
                        cant = c2.number_input("Cantidad (Piezas)", min_value=1, value=1)
                        bultos = c3.number_input("Bultos", min_value=0, value=1)
                        
                        if c4.button("➕ Añadir al Detalle", use_container_width=True):
                            st.session_state.cart_cot.append({
                                "id": str(it['REFERENCIA']), 
                                "nombre": f"{it['DESCRIPCION']}".strip(), 
                                "cantidad": cant, 
                                "bultos": bultos,
                                "empaque": empaque,
                                "peso_kg": peso_kg,
                                "cubic_p3": cubic_p3,
                                "um": um,
                                "precio": precio, 
                                "subtotal": cant * precio
                            })
                            st.rerun()
        conn.close()

        if st.session_state.cart_cot:
            st.subheader("🛒 Detalle de la Proforma")
            
            h1, h2, h3, h4, h5, h6 = st.columns([1.5, 2.5, 1, 1, 1.5, 0.5])
            h1.caption("REFERENCIA")
            h2.caption("DESCRIPCIÓN / LOGÍSTICA")
            h3.caption("CANT.")
            h4.caption("PRECIO")
            h5.caption("SUBTOTAL")
            h6.caption("ACC")

            indice_eliminar = None
            
            for index, item in enumerate(st.session_state.cart_cot):
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2.5, 1, 1, 1.5, 0.5])
                    col1.write(f"**{item['id']}**")
                    col2.write(f"{item['nombre']}")
                    col2.caption(f"Emp: {item.get('empaque','')} | Peso: {item.get('peso_kg',0)}KG | Vol: {item.get('cubic_p3',0)}P3")
                    
                    new_cant = col3.number_input("n_cant", value=item['cantidad'], min_value=1, key=f"q_{index}", label_visibility="collapsed")
                    new_price = col4.number_input("n_pr", value=float(item['precio']), key=f"p_{index}", label_visibility="collapsed")
                    
                    st.session_state.cart_cot[index]['cantidad'] = new_cant
                    st.session_state.cart_cot[index]['precio'] = new_price
                    st.session_state.cart_cot[index]['subtotal'] = new_cant * new_price

                    col5.write(f"${st.session_state.cart_cot[index]['subtotal']:,.2f}")
                    if col6.button("🗑️", key=f"del_{index}"):
                        indice_eliminar = index

            if indice_eliminar is not None:
                st.session_state.cart_cot.pop(indice_eliminar)
                st.rerun()
            
            total_cot = sum(i['subtotal'] for i in st.session_state.cart_cot)
            st.divider()
            st.markdown(f"### Total General Local: ${total_cot:,.2f}")

            if st.button("💾 Guardar Documento Proforma ZL (Local)", type="primary"):
                anio_actual = datetime.now().strftime("%Y")
                conn = self.get_connection()
                
                row = conn.execute("SELECT MAX(num_cot) as max_cot FROM cotizaciones WHERE CAST(num_cot AS TEXT) LIKE ?", (f"{anio_actual}%",)).fetchone()
                secuencia = 1
                if row and row['max_cot']:
                    secuencia = int(str(row['max_cot'])[-3:]) + 1
                
                id_doc_final = int(f"{anio_actual}{secuencia:03d}")

                detalles_json = json.dumps(st.session_state.cart_cot)
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                conn.execute("""
                    INSERT INTO cotizaciones (num_cot, cliente, total, detalles, fecha, estado, sincronizado)
                    VALUES (?, ?, ?, ?, ?, 'Pendiente', 0)
                """, (id_doc_final, cli_sel, total_cot, detalles_json, fecha_hoy))
                
                conn.commit()
                conn.close()

                st.session_state.cart_cot = []
                st.session_state.cli_editable = "--"
                st.success(f"Documento local N° {id_doc_final} guardado.")
                st.rerun()

    def facturar_local(self, cot):
        try:
            anio_actual = datetime.now().strftime("%Y")
            conn = self.get_connection()
            
            row = conn.execute("SELECT MAX(num_fact) as max_fact FROM ventas WHERE CAST(num_fact AS TEXT) LIKE ?", (f"{anio_actual}%",)).fetchone()
            secuencia = 1
            if row and row['max_fact']:
                secuencia = int(str(row['max_fact'])[-3:]) + 1
            
            n_f = int(f"{anio_actual}{secuencia:03d}")
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")

            raw_items = cot['detalles']
            items_processed = json.loads(raw_items) if isinstance(raw_items, str) else raw_items

            for item in items_processed:
                if item.get('id'):
                    prod = conn.execute("SELECT CANTIDAD FROM productos WHERE REFERENCIA = ?", (str(item['id']),)).fetchone()
                    if prod and int(prod['CANTIDAD']) < int(item['cantidad']):
                        st.error(f"❌ Stock Insuficiente para {item['nombre']}. Disponible: {prod['CANTIDAD']}")
                        conn.close()
                        return

            conn.execute("""
                INSERT INTO ventas (num_fact, cliente, total, detalle, fecha, sincronizado)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (n_f, cot['cliente'], cot['total'], json.dumps(items_processed), fecha_hoy))

            for item in items_processed:
                if item.get('id'):
                    prod = conn.execute("SELECT CANTIDAD FROM productos WHERE REFERENCIA = ?", (str(item['id']),)).fetchone()
                    if prod:
                        nueva_cant = int(prod['CANTIDAD']) - int(item['cantidad'])
                        conn.execute("UPDATE productos SET CANTIDAD = ? WHERE REFERENCIA = ?", (nueva_cant, str(item['id'])))

            conn.execute("UPDATE cotizaciones SET estado = 'Facturado', sincronizado = 0 WHERE num_cot = ?", (cot['num_cot'],))
            
            conn.commit()
            conn.close()
            st.success(f"Factura Comercial {n_f} procesada exitosamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error en facturación local: {e}")

    def render(self):
        st.header("📄 RAV System - Módulo de Cotizaciones Local")
        t1, t2 = st.tabs(["🆕 Crear Documento", "📜 Historial de Registros Local"])
        
        with t1: 
            self.vista_crear()
        with t2:
            conn = self.get_connection()
            cots = conn.execute("SELECT * FROM cotizaciones ORDER BY num_cot DESC").fetchall()
            
            if cots:
                for row_cot in cots:
                    c = dict(row_cot)
                    id_visible = c['num_cot']
                    
                    with st.container(border=True):
                        col1, col2, col3, col_edit, col_fact, col_del = st.columns([2, 1, 1.2, 0.8, 0.8, 0.8])
                        
                        sinc_status = "☁️ Sincronizado" if c.get('sincronizado') == 1 else "💻 Local"
                        col1.write(f"**{c['cliente']}**")
                        col1.caption(f"Doc N°: {id_visible} | {c['fecha']} | Estado: {c['estado']} | **[{sinc_status}]**")
                        col2.write(f"${float(c['total']):,.2f}")
                        
                        pdf = self.generar_pdf_profesional(c, c['cliente'])
                        col3.download_button("📥 PDF local", pdf, f"Proforma_{id_visible}.pdf", key=f"dl_{id_visible}", use_container_width=True)
                        
                        if c['estado'] == "Pendiente":
                            if col_edit.button("⚙️", key=f"mod_{id_visible}", help="Editar Proforma", use_container_width=True):
                                st.session_state.cart_cot = json.loads(c['detalles']) if isinstance(c['detalles'], str) else c['detalles']
                                st.session_state.cli_editable = c['cliente']
                                
                                conn.execute("DELETE FROM cotizaciones WHERE num_cot = ?", (id_visible,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                                
                            if col_fact.button("🚀", key=f"f_{id_visible}", help="Facturar Documento", use_container_width=True):
                                conn.close()
                                self.facturar_local(c)
                                st.rerun()
                                
                            if col_del.button("🗑️", key=f"rem_db_{id_visible}", help="Eliminar", use_container_width=True):
                                conn.execute("DELETE FROM cotizaciones WHERE num_cot = ?", (id_visible,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                        else:
                            if col_del.button("🗑️ Reg", key=f"rem_hist_{id_visible}", help="Eliminar Historial Facturado", use_container_width=True):
                                conn.execute("DELETE FROM cotizaciones WHERE num_cot = ?", (id_visible,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                conn.close()
            else:
                st.info("No se registran documentos en el almacenamiento local.")
                conn.close()