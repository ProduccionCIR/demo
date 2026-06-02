import streamlit as st
import pandas as pd
import base64
import os
import io
import math
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

class ModuloVentas:
    def __init__(self, db):
        self.db = db
        self.logo_path = "logo.png"

    def sanitize_data(self, data):
        """
        Limpia recursivamente diccionarios y listas reemplazando NaN/Inf por 0.0
        para asegurar total compatibilidad con el formato JSON de la base de datos.
        """
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
        tipo_doc = "OFFSHORE INVOICE / FACTURA OFFSHORE" if es_offshore else "FACTURA DE VENTA / SALES INVOICE"
        
        # --- DISEÑO MONOCROMÁTICO (BLANCO Y NEARO PURO) ---
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page { 
                    size: letter; 
                    margin: 12mm 10mm 15mm 10mm; 
                    @bottom-right {
                        content: "Página " counter(page) " de " counter(pages);
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 7pt;
                        color: #666666;
                    }
                }
                body { 
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
                    color: #000000; 
                    font-size: 9pt; 
                    line-height: 1.35;
                    margin: 0; 
                }
                
                /* --- ENCABEZADO OPTIMIZADO PARA LOGO MÁS GRANDE --- */
                .header-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                .logo-box { width: 40%; vertical-align: middle; }
                .company-info { width: 60%; text-align: right; font-size: 8.5pt; color: #000000; line-height: 1.4; vertical-align: middle; }
                .company-name { font-size: 15pt; font-weight: bold; color: #000000; margin-bottom: 3px; }
                
                .title-bar { 
                    background-color: #000000; 
                    color: #FFFFFF; 
                    text-align: center; 
                    font-size: 12pt; 
                    font-weight: bold; 
                    padding: 6px; 
                    letter-spacing: 1px;
                    margin-bottom: 15px;
                }
                
                .info-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                .info-table td { vertical-align: top; padding: 4px 0; }
                .info-block { background-color: #FFFFFF; border: 1px solid #000000; padding: 8px; border-radius: 0px; min-height: 50px; }
                
                .items-table { width: 100%; border-collapse: collapse; margin-top: 5px; }
                .items-table th { 
                    background-color: #000000; 
                    color: #FFFFFF; 
                    font-weight: bold; 
                    font-size: 8.5pt; 
                    padding: 7px 6px; 
                    text-align: left; 
                    border: 1px solid #000000;
                }
                .items-table td { padding: 6px; vertical-align: middle; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 8.5pt; }
                .items-table tr:nth-child(even) { background-color: #F2F2F2; }
                
                .totals-wrapper { width: 100%; margin-top: 15px; page-break-inside: avoid; }
                .logistics-box { width: 50%; vertical-align: top; background-color: #FFFFFF; border: 1px solid #000000; border-radius: 0px; padding: 10px; }
                .logistics-title { font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 3px; margin-bottom: 6px; font-size: 8.5pt; text-transform: uppercase; }
                .finances-box { width: 45%; vertical-align: top; text-align: right; padding-top: 5px; }
                
                .finance-row { margin-bottom: 4px; font-size: 9pt; color: #000000; }
                .grand-total-row { 
                    font-size: 11pt; 
                    font-weight: bold; 
                    color: #FFFFFF;
                    background-color: #000000;
                    margin-top: 8px; 
                    padding: 6px;
                    text-align: right;
                }
                
                .text-center { text-align: center; }
                .text-right { text-align: right; }
                .font-bold { font-weight: bold; }
                .footer-notice { margin-top: 30px; font-size: 7.5pt; text-align: center; color: #555555; border-top: 1px solid #000000; padding-top: 10px; }
            </style>
        </head>
        <body>
            <table class="header-table">
                <tr>
                    <td class="logo-box">
                        {% if logo %}<img src="data:image/png;base64,{{ logo }}" style="max-height: 95px; width: auto; display: block;">{% endif %}
                    </td>
                    <td class="company-info">
                        <div class="company-name">DANA INTERNACIONAL</div>
                        <div>RUC: 12440-181-123510 DV83 | TEL: 446-1326</div>
                        <div>CALLE 15 & 16, ZONA LIBRE DE COLÓN, REP. DE PANAMÁ</div>
                    </td>
                </tr>
            </table>

            <div class="title-bar">{{ tipo_doc }}</div>

            <table class="info-table">
                <tr>
                    <td width="55%" style="padding-right: 10px;">
                        <div class="info-block">
                            <span class="font-bold">CLIENTE:</span> {{ cliente | upper }}
                        </div>
                    </td>
                    <td width="45%">
                        <div class="info-block">
                            <table width="100%" style="font-size: 8.5pt;">
                                <tr><td class="font-bold">DOC N°:</td><td class="text-right font-bold">{{ num_fact }}</td></tr>
                                <tr><td class="font-bold">FECHA:</td><td class="text-right">{{ fecha }}</td></tr>
                                <tr><td class="font-bold">VÍA DESPACHO:</td><td class="text-right">{{ via | upper }}</td></tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>

            <table class="items-table">
                <thead>
                    <tr>
                        <th width="15%">REFERENCIA</th>
                        <th width="40%">DESCRIPCIÓN</th>
                        <th width="10%" class="text-center">BULTOS</th>
                        <th width="10%" class="text-center">CANT.</th>
                        <th width="12%" class="text-right">PRECIO</th>
                        <th width="13%" class="text-right">SUBTOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in detalles %}
                    <tr>
                        <td class="font-bold">{{ item.id }}</td>
                        <td>{{ item.nombre }}</td>
                        <td class="text-center">{{ item.get('bultos', 0) }}</td>
                        <td class="text-center">{{ item.cantidad }}</td>
                        <td class="text-right">$ {{ "{:,.2f}".format(item.precio) }}</td>
                        <td class="text-right font-bold">$ {{ "{:,.2f}".format(item.subtotal) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            <table class="totals-wrapper">
                <tr>
                    <td class="logistics-box">
                        <div class="logistics-title">Resumen Logístico</div>
                        <table width="100%" style="font-size: 8.5pt; line-height: 1.5;">
                            <tr><td>TOTAL BULTOS:</td><td class="text-right font-bold">{{ total_bultos }}</td></tr>
                            <tr><td>TOTAL PESO:</td><td class="text-right font-bold">{{ "{:,.2f}".format(total_peso) }} KG</td></tr>
                            <tr><td>TOTAL CUBICAJE:</td><td class="text-right font-bold">{{ "{:,.3f}".format(total_cbm) }} m³</td></tr>
                            <tr><td>TOTAL PIEZAS:</td><td class="text-right font-bold">{{ total_cant }}</td></tr>
                        </table>
                    </td>
                    <td width="5%"></td>
                    <td class="finances-box">
                        <div class="finance-row">SUBTOTAL MERCANCÍA: <span class="font-bold">$ {{ "{:,.2f}".format(total_neto + descuento - flete) }}</span></div>
                        <div class="finance-row">FLETE / MANEJO: <span class="font-bold">$ {{ "{:,.2f}".format(flete) }}</span></div>
                        <div class="finance-row">DESCUENTO: <span class="font-bold">-$ {{ "{:,.2f}".format(descuento) }}</span></div>
                        <div class="grand-total-row">TOTAL NETO: $ {{ "{:,.2f}".format(total_neto) }}</div>
                    </td>
                </tr>
            </table>

            <div class="footer-notice">
                SISTEMA RAV SYSTEM - GESTIÓN QUE IMPULSA TU ÉXITO
            </div>
        </body>
        </html>"""
        
        detalles = datos.get('detalle', [])
        t_bultos = sum(int(i.get('bultos', 0)) for i in detalles)
        t_peso = sum(float(i.get('peso', 0.0)) for i in detalles)
        t_cbm = sum(float(i.get('cbm', 0.0)) for i in detalles)
        t_cant = sum(int(i.get('cantidad', 0)) for i in detalles)
        
        total_neto = float(datos.get('total', 0.0))
        flete = float(datos.get('flete', 0.0))
        desc = float(datos.get('descuento', 0.0))

        tm = Template(html_template)
        html_res = tm.render(
            logo=logo_b64, tipo_doc=tipo_doc,
            num_fact=str(datos.get('num_fact', 'N/A')),
            fecha=str(datos.get('fecha'))[:10],
            cliente=datos.get('cliente', 'S/N'),
            via=datos.get('via_despacho', 'N/A'),
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

        with st.container(border=True):
            clientes_raw = self.db.fetch("clientes") or []
            df_c = pd.DataFrame(clientes_raw)
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            
            lista_clientes = ["--"]
            if not df_c.empty:
                df_c.columns = [c.lower() for c in df_c.columns]
                col_nombre = 'nombre' if 'nombre' in df_c.columns else df_c.columns[0]
                lista_clientes += df_c[col_nombre].tolist()
            
            cli = c1.selectbox(f"👤 Cliente", lista_clientes, key=f"cli_{tipo_str}")
            via = c2.selectbox("🚢 Vía Despacho", ["Marítima", "Terrestre", "Aérea", "Traspaso"], key=f"via_{tipo_str}")
            
            flete = c3.number_input("💰 Flete/Manejo $", min_value=0.0, step=0.01, value=0.0, format="%.2f", key=f"flete_{tipo_str}")
            desc = c4.number_input("📉 Descuento $", min_value=0.0, step=0.01, value=0.0, format="%.2f", key=f"desc_{tipo_str}")

        # --- LÓGICA DE PRODUCTOS SEGÚN EL MODO ---
        if not es_offshore:
            st.write("### 🔍 Selección de Productos")
            productos_raw = self.db.fetch("productos") or []
            
            if productos_raw:
                df_p = pd.DataFrame(productos_raw)
                df_p.columns = [c.upper() for c in df_p.columns]
                col_ref, col_des, col_can, col_cos = "REFERENCIA", "DESCRIPCION", "CANTIDAD", "COSTO UNIT"

                search = st.text_input("Buscar producto...", key=f"search_{tipo_str}")
                if search:
                    df_p = df_p[df_p[col_ref].astype(str).str.contains(search, case=False) | 
                                df_p[col_des].astype(str).str.contains(search, case=False)]

                st.dataframe(df_p[[col_ref, col_des, col_can, col_cos]], width="stretch", hide_index=True)
                
                with st.expander("➕ Configurar Línea", expanded=True):
                    lista_refs = df_p[col_ref].unique().tolist()
                    sel_ref = st.selectbox("Producto", lista_refs, key=f"sel_ref_{tipo_str}")
                    it = df_p[df_p[col_ref] == sel_ref].iloc[0]
                    
                    c1, c2, c3, c4, c5 = st.columns(5)
                    costo_base = float(it.get(col_cos, 0.0)) if not pd.isna(it.get(col_cos)) else 0.0
                    
                    pr = c1.number_input("Precio Venta", value=costo_base, format="%.2f", key=f"pr_{tipo_str}")
                    ct = c2.number_input("Cantidad", min_value=1, value=1, key=f"ct_{tipo_str}")
                    bu = c3.number_input("Bultos", min_value=1, value=1, key=f"bu_{tipo_str}")
                    pe = c4.number_input("Peso (KG)", min_value=0.0, value=0.0, format="%.2f", key=f"pe_{tipo_str}")
                    cb = c5.number_input("CBM (m³)", min_value=0.0, value=0.0, format="%.3f", key=f"cb_{tipo_str}")

                    if st.button("Añadir al Carrito", width="stretch", key=f"add_{tipo_str}"):
                        nuevo_item = {
                            "id": str(it[col_ref]), 
                            "nombre": str(it[col_des]), 
                            "cantidad": int(ct), 
                            "precio": float(pr), 
                            "subtotal": float(ct * pr),
                            "bultos": int(bu), 
                            "peso": float(pe), 
                            "cbm": float(cb)
                        }
                        st.session_state[f'cart_{tipo_str}'].append(self.sanitize_data(nuevo_item))
                        st.rerun()
        else:
            # --- MODO OFFSHORE: INGRESO MANUAL COMPLETO (SIN CARGAR INVENTARIO) ---
            st.write("### ✍️ Ingreso Manual de Productos (Offshore)")
            with st.container(border=True):
                c_ref, c_desc = st.columns([1, 2])
                manual_ref = c_ref.text_input("Referencia", key=f"man_ref_{tipo_str}")
                manual_desc = c_desc.text_input("Descripción / Nombre", key=f"man_desc_{tipo_str}")
                
                c1, c2, c3, c4, c5 = st.columns(5)
                pr = c1.number_input("Precio Venta", min_value=0.0, value=0.0, format="%.2f", key=f"pr_{tipo_str}")
                ct = c2.number_input("Cantidad", min_value=1, value=1, key=f"ct_{tipo_str}")
                bu = c3.number_input("Bultos", min_value=1, value=1, key=f"bu_{tipo_str}")
                pe = c4.number_input("Peso (KG)", min_value=0.0, value=0.0, format="%.2f", key=f"pe_{tipo_str}")
                cb = c5.number_input("CBM (m³)", min_value=0.0, value=0.0, format="%.3f", key=f"cb_{tipo_str}")

                if st.button("Añadir al Carrito", width="stretch", key=f"add_{tipo_str}"):
                    if not manual_ref.strip() or not manual_desc.strip():
                        st.error("⚠️ Error: Referencia y Descripción son campos obligatorios en el modo manual.")
                    else:
                        nuevo_item = {
                            "id": str(manual_ref).strip().upper(), 
                            "nombre": str(manual_desc).strip(), 
                            "cantidad": int(ct), 
                            "precio": float(pr), 
                            "subtotal": float(ct * pr),
                            "bultos": int(bu), 
                            "peso": float(pe), 
                            "cbm": float(cb)
                        }
                        st.session_state[f'cart_{tipo_str}'].append(self.sanitize_data(nuevo_item))
                        st.rerun()

        # --- MOSTRAR EL CARRITO Y PROCESAR CIERRE DE FACTURA ---
        carrito = st.session_state[f'cart_{tipo_str}']
        if carrito:
            st.divider()
            
            # Vista rápida de las líneas agregadas al carrito actual
            st.write("**Líneas agregadas:**")
            df_items_cart = pd.DataFrame(carrito)
            st.dataframe(df_items_cart[["id", "nombre", "cantidad", "bultos", "precio", "subtotal"]], hide_index=True, width="stretch")
            
            total_mercancia = sum(i['subtotal'] for i in carrito)
            total_neto = (total_mercancia + flete) - desc

            st.metric("TOTAL NETO", f"${total_neto:,.2f}", delta=f"Desc: -${desc:,.2f}")
            
            if st.button(f"🚀 Finalizar Factura", type="primary", width="stretch", key=f"btn_save_{tipo_str}"):
                if cli == "--":
                    st.error("⚠️ Error: Debe seleccionar un cliente.")
                    return

                anio_actual = datetime.now().strftime("%Y")
                ventas_existentes = self.db.fetch("ventas") or []
                
                secuencia = 1
                if ventas_existentes:
                    docs_anio = []
                    for v in ventas_existentes:
                        val_fact = v.get('num_fact')
                        if val_fact is not None:
                            str_fact = str(val_fact).split('.')[0].strip()
                            if str_fact.startswith(anio_actual):
                                docs_anio.append(str_fact)
                    
                    if docs_anio:
                        max_sec = max(int(s[-3:]) for s in docs_anio if s[-3:].isdigit())
                        secuencia = max_sec + 1
                
                num_fact_final = int(f"{anio_actual}{secuencia:03d}")

                raw_payload = {
                    "num_fact": num_fact_final, 
                    "cliente": str(cli), 
                    "total": float(total_neto), 
                    "flete": float(flete), 
                    "descuento": float(desc),
                    "detalle": carrito,
                    "via_despacho": str(via), 
                    "fecha": datetime.now().isoformat(),
                    "estado": "PENDIENTE"
                }
                
                final_payload = self.sanitize_data(raw_payload)
                
                try:
                    self.db.client.table("ventas").insert(final_payload).execute()
                    
                    # SI NO ES OFFSHORE, restamos del inventario. Si es offshore, saltamos este bloque.
                    if not es_offshore:
                        for i in carrito:
                            res = self.db.client.table("productos").select("CANTIDAD").eq("REFERENCIA", i['id']).execute()
                            if res.data:
                                nueva_q = int(res.data[0]['CANTIDAD']) - i['cantidad']
                                self.db.client.table("productos").update({"CANTIDAD": nueva_q}).eq("REFERENCIA", i['id']).execute()
                    
                    st.success(f"✅ Factura {num_fact_final} guardada correctamente.")
                    st.session_state[f'cart_{tipo_str}'] = []
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error de base de datos: {e}")

    def render_historial(self):
        st.subheader("📜 Historial de Ventas")
        ventas = self.db.fetch("ventas") or []
        if not ventas:
            st.info("No hay ventas registradas.")
            return
        
        df_v = pd.DataFrame(ventas)
        if 'num_fact' in df_v.columns:
            df_v['num_fact_clean'] = df_v['num_fact'].apply(lambda x: int(float(x)) if pd.notnull(x) else 0)
            df_v = df_v.sort_values(by="num_fact_clean", ascending=False)
        else:
            df_v['num_fact_clean'] = df_v['id']
            df_v = df_v.sort_values(by="id", ascending=False)

        for _, v in df_v.iterrows():
            num_visible = int(v['num_fact_clean'])
            dict_venta = v.to_dict()
            dict_venta['num_fact'] = num_visible
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**Factura #{num_visible}** | Cliente: {v['cliente']}")
                c1.caption(f"Fecha: {v['fecha'][:10]} | Total: ${float(v['total']):,.2f}")
                
                pdf_data = self.generar_pdf_factura(dict_venta)
                c2.download_button("📄 PDF", pdf_data, f"FACT_{num_visible}.pdf", key=f"pdf_h_{v['id']}", width="stretch")

    def render(self):
        st.header("💰 Módulo de Ventas")
        t1, t2 = st.tabs(["📄 Nueva Factura", "📜 Historial"])
        with t1:
            sub1, sub2 = st.tabs(["Zona Libre (ZLC)", "Offshore (Export)"])
            with sub1: self.formulario_venta(es_offshore=False)
            with sub2: self.formulario_venta(es_offshore=True)
        with t2:
            self.render_historial()