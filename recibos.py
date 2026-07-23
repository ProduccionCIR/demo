#recibos.py
import streamlit as st
import pandas as pd
import io
import os
import base64
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

class ModuloRecibos:
    def __init__(self, db):
        self.db = db
        self.logo_path = "logo.png"

    def get_image_base64(self, path):
        try:
            if os.path.exists(path):
                with open(path, "rb") as img:
                    return base64.b64encode(img.read()).decode('utf-8')
            return None
        except Exception as e:
            print(f"Error al leer imagen {path}: {e}")
            return None

    def generar_pdf_recibo(self, datos):
        logo_b64 = self.get_image_base64(self.logo_path)
        
        html_template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page { size: A4; margin: 8mm; }
                body { font-family: 'Courier New', Courier, monospace; color: #000; font-size: 8.5pt; margin: 0; padding: 0; }
                .recibo-block { height: 132mm; border-bottom: 1px dashed #000; padding-bottom: 5px; margin-bottom: 15px; box-sizing: border-box; }
                .recibo-block:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
                .header-wrapper { display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 4px; }
                .logo-box { width: 30%; }
                .company-info { width: 70%; text-align: right; font-size: 7.5pt; line-height: 1.2; }
                .doc-title { text-align: center; font-size: 13pt; font-weight: bold; text-decoration: underline; margin: 8px 0; letter-spacing: 1px; }
                .info-table { width: 100%; margin-top: 5px; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 4px 0; }
                .details-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                .details-table th { border-bottom: 1px solid #000; border-top: 1px solid #000; padding: 5px; text-align: left; font-size: 8pt; background-color: #f2f2f2; }
                .details-table td { padding: 6px; vertical-align: top; border-bottom: 1px solid #eee; }
                .totals-container { margin-top: 15px; display: flex; justify-content: space-between; }
                .summary-box { width: 55%; border: 1px solid #000; padding: 6px; background-color: #fafafa; font-size: 8pt; }
                .final-totals { width: 40%; text-align: right; line-height: 1.5; font-size: 9pt; }
                .grand-total { font-size: 11pt; font-weight: bold; border-top: 2px solid #000; margin-top: 4px; padding-top: 4px; }
                .text-right { text-align: right; }
                .firma-space { margin-top: 20px; text-align: center; font-size: 8pt; border-top: 1px solid #000; width: 180px; float: right; }
            </style>
        </head>
        <body>
            {% for copia in ['ORIGINAL CLIENTE', 'COPIA CONTABILIDAD'] %}
            <div class="recibo-block">
                <div style="float: left; font-size: 7pt; font-weight: bold; border: 1px solid #000; padding: 2px; text-transform: uppercase;">{{ copia }}</div>
                <div style="clear: both;"></div>
                <div class="header-wrapper">
                    <div class="logo-box">
                        {% if logo %}<img src="data:logo.png;base64,{logo}" style="max-width: 120px;">{% endif %}
                    </div>
                    <div style="text-align: right; font-size: 8pt; color: #475569;">
                    <strong style="font-size: 11pt; color: #0f172a;">DANA INTERNACIONAL</strong><br>
                    ZONA LIBRE DE COLÓN, PANAMÁ<br>
                    </div>
                </div>
                
                <div class="doc-title">RECIBO DE PAGO / PAYMENT RECEIPT</div>
                
                <table class="info-table">
                    <tr>
                        <td width="60%"><strong>CLIENTE:</strong> {{ cliente | upper }}</td>
                        <td width="40%" class="text-right"><strong>RECIBO N°:</strong> {{ num_recibo }}</td>
                    </tr>
                    <tr>
                        <td><strong>CONCEPTO:</strong> {{ concepto | upper }}</td>
                        <td class="text-right"><strong>FECHA:</strong> {{ fecha }}</td>
                    </tr>
                    <tr>
                        <td><strong>MÉTODO DE PAGO:</strong> {{ metodo_pago | upper }}</td>
                        <td class="text-right"><strong>TIPO:</strong> {{ tipo_recibo }}</td>
                    </tr>
                </table>

                <table class="details-table">
                    <thead>
                        <tr>
                            <th width="50%">DESCRIPCIÓN DEL MOVIMIENTO</th>
                            <th width="25%" class="text-right">SALDO ANTERIOR</th>
                            <th width="25%" class="text-right">MONTO ABONADO</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{{ nota if nota else 'Aplicación de pago a cuenta del cliente.' }}</td>
                            <td class="text-right">$ {{ "{:,.2f}".format(saldo_anterior) }}</td>
                            <td class="text-right"><strong>$ {{ "{:,.2f}".format(monto_abono) }}</strong></td>
                        </tr>
                    </tbody>
                </table>

                <div class="totals-container">
                    <div class="summary-box">
                        <strong>INFORMACIÓN DE CONTROL:</strong><br>
                        {% if id_venta %}
                        Asociado a Factura N°: {{ id_venta }}<br>
                        {% endif %}
                        Estado Final Factura: {{ 'PAGADA / LIQUIDADA' if saldo_restante <= 0 else 'CON SALDO PENDIENTE' }}
                    </div>
                    <div class="final-totals">
                        SALDO ANTERIOR: $ {{ "{:,.2f}".format(saldo_anterior) }}<br>
                        TOTAL ABONADO: $ {{ "{:,.2f}".format(monto_abono) }}<br>
                        <div class="grand-total">SALDO RESTANTE: $ {{ "{:,.2f}".format(saldo_restante) }}</div>
                    </div>
                </div>
                
                <div class="firma-space">Recibido Conforme (Cajero/a)</div>
                <div style="clear: both;"></div>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        tm = Template(html_template)
        html_res = tm.render(
            logo=logo_b64,
            num_recibo=datos.get('num_recibo', 'N/A'),
            cliente=datos.get('cliente', 'S/N'),
            concepto=datos.get('concepto', 'Pago General'),
            metodo_pago=datos.get('metodo_pago', 'Efectivo'),
            tipo_recibo=datos.get('tipo_recibo', 'MANUAL'),
            fecha=str(datos.get('fecha', ''))[:10],
            nota=datos.get('nota', ''),
            saldo_anterior=float(datos.get('saldo_anterior', 0.0)),
            monto_abono=float(datos.get('monto_abono', 0.0)),
            saldo_restante=float(datos.get('saldo_restante', 0.0)),
            id_venta=datos.get('id_venta')
        )

        pdf_out = io.BytesIO()
        HTML(string=html_res).write_pdf(pdf_out)
        return pdf_out.getvalue()

    def obtener_siguiente_secuencia(self):
        anio_actual = datetime.now().strftime("%Y")
        secuencia = 1
        try:
            res = self.db.client.table("recibos").select("num_recibo").execute()
            recibos_existentes = res.data if res and hasattr(res, 'data') else []
        except Exception:
            recibos_existentes = []

        if recibos_existentes:
            docs_anio = []
            for r in recibos_existentes:
                if r is not None:
                    val_rec = r.get('num_recibo')
                    if val_rec is not None:
                        str_rec = str(val_rec).split('.')[0].strip()
                        if str_rec.startswith(anio_actual):
                            docs_anio.append(str_rec)
            if docs_anio:
                max_sec = max(int(s[-3:]) for s in docs_anio if s[-3:].isdigit())
                secuencia = max_sec + 1
        return str(f"{anio_actual}{secuencia:03d}")

    def render(self):
        st.header("💵 Control de Caja y Recibos")
        t1, t2 = st.tabs(["📝 Registrar Ingreso / Recibo", "📜 Historial de Movimientos"])

        with t1:
            modo_emision = st.radio("Método de Emisión", ["Asociado a una Factura Pendiente", "Recibo Manual Independiente"], horizontal=True)
            
            if modo_emision == "Asociado a una Factura Pendiente":
                ventas_raw = []
                try:
                    # Mapeado a 'num_factura' según tu estructura real
                    res_ventas = self.db.client.table("ventas").select("*").neq("estado", "PAGADA").execute()
                    ventas_raw = res_ventas.data if res_ventas and hasattr(res_ventas, 'data') else []
                except Exception as e:
                    st.error(f"Error al cargar facturas pendientes: {e}")

                if not ventas_raw:
                    st.info("No hay facturas pendientes con saldo por cobrar.")
                else:
                    opciones_facturas = {}
                    for v in ventas_raw:
                        if v is not None:
                            num_f = int(float(v.get('num_factura', 0)))
                            cli_f = v.get('cliente', 'S/N')
                            tot_f = float(v.get('total', 0.0))
                            opciones_facturas[f"Factura #{num_f} - Cliente: {cli_f} (Total: ${tot_f:,.2f})"] = v

                    sel_factura = st.selectbox("Seleccione la Factura a aplicar pago:", list(opciones_facturas.keys()))
                    
                    if sel_factura:
                        factura_sel = opciones_facturas[sel_factura]
                        num_fact_sel = int(float(factura_sel.get('num_factura', 0)))
                        
                        pagos_previos = []
                        try:
                            # Mapeado a 'id_venta'
                            res_pagos = self.db.client.table("recibos").select("monto_abono").eq("id_venta", num_fact_sel).execute()
                            pagos_previos = res_pagos.data if res_pagos and hasattr(res_pagos, 'data') else []
                        except Exception:
                            pass
                            
                        total_abonado_antes = sum(float(p.get('monto_abono', 0.0)) for p in pagos_previos if p is not None)
                        saldo_actual_factura = float(factura_sel.get('total', 0.0)) - total_abonado_antes
                        
                        st.warning(f"📋 Saldo Original: ${float(factura_sel.get('total', 0.0)):,.2f} | 💰 Saldo Pendiente Actual: ${saldo_actual_factura:,.2f}")
                        
                        with st.form("form_recibo_vinculado"):
                            c1, c2 = st.columns(2)
                            monto_pago = c1.number_input("Monto a pagar $", min_value=0.01, max_value=max(0.01, saldo_actual_factura), value=max(0.01, saldo_actual_factura), step=0.01, format="%.2f")
                            metodo = c2.selectbox("Método de Pago", ["Efectivo", "Depósito Bancario", "Transferencia ACH", "Cheque"])
                            
                            concepto = c1.text_input("Concepto", value=f"Abono a Factura N° {num_fact_sel}")
                            nota = c2.text_area("Notas / Detalles del pago")

                            if st.form_submit_button("🚀 Procesar Pago y Cerrar / Abonar Factura", use_container_width=True):
                                num_recibo_final = self.obtener_siguiente_secuencia()
                                nuevo_saldo = saldo_actual_factura - monto_pago
                                
                                payload_recibo = {
                                    "num_recibo": num_recibo_final,
                                    "cliente": str(factura_sel.get('cliente', 'S/N')),
                                    "concepto": concepto,
                                    "metodo_pago": metodo,
                                    "monto": float(monto_pago),  # Soportando tu campo 'monto' nativo original
                                    "monto_abono": float(monto_pago),
                                    "saldo_anterior": float(saldo_actual_factura),
                                    "saldo_restante": float(nuevo_saldo),
                                    "id_venta": num_fact_sel,
                                    "tipo_recibo": "VINCULADO",
                                    "nota": nota,
                                    "fecha": datetime.now().isoformat()
                                }
                                
                                try:
                                    self.db.client.table("recibos").insert(payload_recibo).execute()
                                    
                                    if nuevo_saldo <= 0.01:
                                        self.db.client.table("ventas").update({"estado": "PAGADA"}).eq("num_factura", num_fact_sel).execute()
                                        st.success(f"🎉 ¡La factura #{num_fact_sel} ha sido saldada por completo!")
                                    else:
                                        self.db.client.table("ventas").update({"estado": "ABONADA"}).eq("num_factura", num_fact_sel).execute()
                                        st.info(f"📉 Abono registrado. Nuevo saldo pendiente: ${nuevo_saldo:,.2f}")
                                        
                                    st.success(f"✅ Recibo N° {num_recibo_final} guardado con éxito.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al procesar la cobranza: {e}")

            elif modo_emision == "Recibo Manual Independiente":
                with st.form("form_recibo_manual"):
                    c1, c2 = st.columns(2)
                    cliente_manual = c1.text_input("Nombre del Cliente").strip().upper()
                    monto_manual = c2.number_input("Monto Recibido $", min_value=0.01, step=0.01, format="%.2f")
                    
                    metodo_m = c1.selectbox("Método de Pago", ["Efectivo", "Depósito Bancario", "Transferencia ACH", "Cheque"], key="met_m")
                    concepto_m = c2.text_input("Concepto del Recibo", value="Pago general a cuenta")
                    
                    saldo_ant_m = c1.number_input("Saldo Anterior (Opcional) $", min_value=0.0, step=0.01, format="%.2f")
                    nota_m = c2.text_area("Observaciones")

                    if st.form_submit_button("💾 Guardar Recibo Manual", use_container_width=True):
                        if not cliente_manual:
                            st.error("Debe escribir el nombre del cliente.")
                        else:
                            num_recibo_final = self.obtener_siguiente_secuencia()
                            saldo_restante_m = max(0.0, float(saldo_ant_m) - float(monto_manual))
                            
                            payload_manual = {
                                "num_recibo": num_recibo_final,
                                "cliente": cliente_manual,
                                "concepto": concepto_m,
                                "metodo_pago": metodo_m,
                                "monto": float(monto_manual),
                                "monto_abono": float(monto_manual),
                                "saldo_anterior": float(saldo_ant_m),
                                "saldo_restante": float(saldo_restante_m),
                                "tipo_recibo": "MANUAL",
                                "nota": nota_m,
                                "fecha": datetime.now().isoformat()
                            }
                            
                            try:
                                self.db.client.table("recibos").insert(payload_manual).execute()
                                st.success(f"✅ Recibo Manual N° {num_recibo_final} generado de forma correcta.")
                                st.rerun()
                            except Exception as e:
                                r_msg = str(e)
                                st.error(f"Error al guardar recibo manual: {r_msg}")

        with t2:
            st.subheader("📜 Historial de Cobros y Recibos")
            
            try:
                res_recibos = self.db.client.table("recibos").select("*").execute()
                recibos_raw = res_recibos.data if res_recibos and hasattr(res_recibos, 'data') else []
            except Exception as err_rec:
                st.error(f"Error al consultar la tabla recibos: {err_rec}")
                recibos_raw = []
            
            if not recibos_raw:
                st.info("No se registran recibos de pago emitidos.")
            else:
                df_r = pd.DataFrame(recibos_raw)
                
                if 'num_recibo' in df_r.columns:
                    df_r['num_recibo_clean'] = df_r['num_recibo'].apply(lambda x: int(float(x)) if pd.notnull(x) and str(x).replace('.','',1).isdigit() else 0)
                    df_r = df_r.sort_values(by="num_recibo_clean", ascending=False)
                else:
                    df_r['num_recibo_clean'] = df_r.get('id', 0)
                
                for _, r in df_r.iterrows():
                    if r is not None:
                        num_vis = r.get('num_recibo', 'S/N')
                        dict_recibo = r.to_dict()
                        
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            col1.write(f"**Recibo #{num_vis}** ({r.get('tipo_recibo', 'MANUAL')}) | Cliente: {r.get('cliente', 'S/N')}")
                            col1.caption(f"Fecha: {str(r.get('fecha', ''))[:10]} | Monto Abonado: **${float(r.get('monto_abono', 0.0)):,.2f}** | Saldo Restante: ${float(r.get('saldo_restante', 0.0)):,.2f}")
                            
                            pdf_data = self.generar_pdf_recibo(dict_recibo)
                            col2.download_button("📄 Imprimir Recibo", pdf_data, f"RECIBO_{num_vis}.pdf", key=f"btn_rec_{r.get('id')}")