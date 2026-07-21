# inventario.py
import pandas as pd
import os
from datetime import datetime
import streamlit as st
from utilidades import check_permiso

class ModuloInventario:
    def __init__(self, db):
        self.db = db
        self.folder_imagenes = "imagenes_productos"
        if not os.path.exists(self.folder_imagenes):
            os.makedirs(self.folder_imagenes)

    def registrar_evento(self, accion, detalle):
        try:
            session_data = st.session_state.get('user_data', {})
            usuario = session_data.get('usuario', st.session_state.get('usuario', 'Admin_Inventario'))
            query = """
                INSERT INTO logs_sistema (modulo, usuario, accion, detalle, fecha)
                VALUES (?, ?, ?, ?, ?)
            """
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.ejecutar_consulta(query, ("INVENTARIO", usuario, str(accion).upper(), str(detalle), fecha_actual))
        except Exception as e:
            st.error(f"Error al guardar log: {e}")

    def guardar_imagen_local(self, archivo_subido):
        if not archivo_subido:
            return None
        try:
            import uuid
            extension = archivo_subido.name.split('.')[-1]
            nombre_archivo = f"prod_{uuid.uuid4().hex}.{extension}"
            ruta_completa = os.path.join(self.folder_imagenes, nombre_archivo)
            with open(ruta_completa, "wb") as f:
                f.write(archivo_subido.getvalue())
            return ruta_completa
        except Exception as e:
            st.error(f"Error en la carga de imagen: {e}")
            return None

    def render(self):
        st.header("📦 Gestión de Inventario")
        
        # Lectura de la base local
        prods = self.db.ejecutar_consulta("SELECT * FROM productos")
        
        # Construcción ultra-segura del DataFrame contra errores de indexación
        if prods:
            datos_limpios = [dict(row) for row in prods]
            df = pd.DataFrame(datos_limpios)
            
            # Normalizar nombres de columnas a minúsculas
            df.columns = [c.lower() for c in df.columns]
            
            # Manejar la columna especial con barra (u/m) que genera SQLite
            if 'u/m' in df.columns:
                df['um'] = df['u/m']
                
            # Forzar la existencia de columnas críticas con valores por defecto nativos
            columnas_defecto = {
                'id': 0, 'cantidad': 0, 'costo_unit': 0.0, 'costo_unitario': 0.0,
                'peso': 0.0, 'cubicaje': 0.0, 'referencia': '', 'marca': '', 
                'descripcion': '', 'especificacion': '', 'ubicacion': '', 'empaque': '', 'um': 'CAJA'
            }
            for col, def_val in columnas_defecto.items():
                if col not in df.columns:
                    df[col] = def_val
                else:
                    df[col] = df[col].fillna(def_val)

            # --- SOLUCIÓN INTEGRAL USANDO .VALUES (ARREGLO PURO) ---
            df['id'] = df['id'].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0).astype(int)
            df['id_prod_interno'] = df['id'].values # .values evita errores de dimensiones de DataFrame
            
            df['cantidad'] = df['cantidad'].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0).astype('int64')
            df['amount'] = df['cantidad'].values
            
            # Unificar costos
            df['costo_unit'] = df['costo_unit'].fillna(df['costo_unitario'])
            df['costo_unit'] = df['costo_unit'].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0.0).astype(float)
            
            # Multiplicación directa libre de nulos
            df['total'] = df['cantidad'] * df['costo_unit']
            
            df['peso'] = df['peso'].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0.0).astype(float)
            df['cubicaje'] = df['cubicaje'].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0.0).astype(float)
            
            # Limpieza estricta de textos
            columnas_texto = ['referencia', 'marca', 'descripcion', 'empaque', 'um', 'especificacion', 'ubicacion']
            for col in columnas_texto:
                df[col] = df[col].astype(str).str.replace('nan', '', case=False).str.strip()
        else:
            # Estructura limpia para DataFrame vacío si SQLite no tiene datos aún
            columnas_vacias = ['id', 'id_prod_interno', 'referencia', 'especificacion', 'marca', 'descripcion', 
                               'ubicacion', 'cantidad', 'costo_unit', 'total', 'empaque', 'peso', 'cubicaje', 'um', 'imagen']
            df = pd.DataFrame(columns=columnas_vacias)

        tab1, tab2, tab3 = st.tabs([
            "📋 Existencias Actuales", 
            "➕ Nuevo Producto", 
            "🛠️ Modificar / Actualizar"
        ])

        with tab1:
            self.render_existencias(df)

        with tab2:
            self.formulario_nuevo()

        with tab3:
            if not df.empty:
                self.seccion_edicion_busqueda(df)
            else:
                st.info("No hay productos registrados para editar.")

    def render_existencias(self, df):
        st.subheader("Control de Stock y Valorización")
        if df.empty:
            st.info("El inventario local está vacío en este momento.")
            return

        c1, c2 = st.columns([1, 2])
        filtro_stock = c1.selectbox("Filtrar Stock:", ["Todos", "🔴 Crítico", "🟡 Atención", "🟢 Óptimo"])
        busqueda = c2.text_input("🔍 Buscar por descripción, marca, referencia o especificación:", key="inv_search_main")
        
        df_v = df.copy()
        if "Crítico" in filtro_stock: df_v = df_v[df_v['cantidad'] <= 15]
        elif "Atención" in filtro_stock: df_v = df_v[(df_v['cantidad'] > 15) & (df_v['cantidad'] <= 50)]
        elif "Óptimo" in filtro_stock: df_v = df_v[df_v['cantidad'] > 50]
        
        if busqueda:
            df_v = df_v[
                df_v['descripcion'].str.contains(busqueda, case=False, na=False) | 
                df_v['marca'].str.contains(busqueda, case=False, na=False) |
                df_v['referencia'].str.contains(busqueda, case=False, na=False) |
                df_v['especificacion'].str.contains(busqueda, case=False, na=False)
            ]
        
        cols_mostrar = ['id', 'referencia', 'especificacion', 'marca', 'descripcion', 'ubicacion', 'cantidad', 'costo_unit', 'total', 'empaque', 'peso', 'cubicaje', 'um', 'imagen']
        cols_mostrar = [c for c in cols_mostrar if c in df_v.columns]
        df_final = df_v[cols_mostrar].reset_index(drop=True)

        def calcular_color_celda(val):
            try: valor = int(val)
            except: valor = 0
            if valor <= 15: return 'background-color: #ff4b4b; color: white; font-weight: bold;'
            elif valor <= 50: return 'background-color: #f9d71c; color: black; font-weight: bold;'
            else: return 'background-color: #00c853; color: white; font-weight: bold;'

        try:
            df_styled = (df_final.style
                         .map(calcular_color_celda, subset=['cantidad'])
                         .format({
                             'costo_unit': '${:,.2f}',
                             'total': '${:,.2f}',
                             'peso': '{:,.2f} KG',
                             'cubicaje': '{:,.2f} M3'
                         }))
        except:
            df_styled = df_final

        st.dataframe(
            df_styled, 
            width='stretch', 
            hide_index=True,
            column_config={
                "id": "ID", "referencia": "Referencia", "especificacion": "Especificación",
                "marca": "Marca", "descripcion": "Descripción", "ubicacion": "Ubicación",
                "cantidad": "Cantidad", "costo_unit": "Costo Unit.", "total": "Total Valorizado",
                "empaque": "Empaque", "peso": "Peso", "cubicaje": "Cubicaje", "um": "U/M",
                "imagen": st.column_config.ImageColumn("Preview")
            }
        )

    def seccion_edicion_busqueda(self, df):
        st.subheader("Edición de Artículos")
        opciones = {}
        for _, r in df.iterrows():
            ref = str(r.get('referencia', '')).strip()
            desc = str(r.get('descripcion', '')).strip()
            espec = str(r.get('especificacion', '')).strip()
            id_prod = int(r['id_prod_interno'])
            tag_espec = f" ({espec})" if espec else ""
            label = f"{ref} | {desc}{tag_espec} (ID: {id_prod})" if ref else f"S/R | {desc} (ID: {id_prod})"
            opciones[label] = id_prod

        seleccion = st.selectbox("Seleccione artículo para editar:", ["-- Seleccione --"] + list(opciones.keys()))

        if seleccion != "-- Seleccione --":
            id_sel = opciones[seleccion]
            df_filtrado = df[df['id_prod_interno'].astype(int) == int(id_sel)]
            if df_filtrado.empty:
                st.error("❌ El producto no se pudo localizar.")
                return
            item = df_filtrado.iloc[0]
            puede_editar = check_permiso("modificar")

            with st.form("form_edit_full_v2"):
                st.info(f"Modificando Registro - Referencia: {item.get('referencia', 'S/R')} (ID: {id_sel})")
                c_ref, c_img = st.columns([1.2, 1.8])
                n_ref = c_ref.text_input("Referencia", value=str(item.get('referencia', '')))
                archivo_img_edit = c_img.file_uploader("Actualizar foto (.jpg, .png)", type=["jpg", "png", "jpeg"], key="edit_img")
                url_imagen_actual = item.get('imagen', None)

                c1, c2 = st.columns(2)
                n_espec = c1.text_input("Especificación", value=str(item.get('especificacion', '')))
                n_marca = c2.text_input("Marca", value=str(item.get('marca', '')))
                n_desc = st.text_input("Descripción", value=str(item.get('descripcion', '')))
                
                c4, c5, c6 = st.columns(3)
                n_ubica = c4.text_input("Ubicación", value=str(item.get('ubicacion', '')))
                n_cant = c5.number_input("Cantidad", value=int(item.get('cantidad', 0)), step=1)
                n_costo = c6.number_input("Costo Unitario ($)", value=float(item.get('costo_unit', 0)), format="%.2f")
                
                c7, c8, c9, c10 = st.columns(4)
                n_emp = c7.text_input("Detalle Empaque", value=str(item.get('empaque', '')))
                n_peso = c8.number_input("Peso (KG)", value=float(item.get('peso', 0.0)), format="%.2f", step=0.1)
                n_cubic = c9.number_input("Cubicaje (M3)", value=float(item.get('cubicaje', 0.0)), format="%.2f", step=0.01)
                n_um = c10.text_input("U/M", value=str(item.get('um', 'CAJA')))

                btn_guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", width='stretch', disabled=not puede_editar)

                if btn_guardar and puede_editar:
                    ruta_final_img = self.guardar_imagen_local(archivo_img_edit) if archivo_img_edit else url_imagen_actual
                    query = """
                        UPDATE productos SET 
                            referencia=?, especificacion=?, marca=?, descripcion=?, ubicacion=?, 
                            cantidad=?, costo_unit=?, total=?, empaque=?, peso=?, cubicaje=?, um=?, imagen=?
                        WHERE id=?
                    """
                    params = (n_ref, n_espec, n_marca, n_desc, n_ubica, int(n_cant), n_costo, int(n_cant)*n_costo, n_emp, n_peso, n_cubic, n_um, ruta_final_img, id_sel)
                    self.db.ejecutar_consulta(query, params)
                    self.registrar_evento("ACTUALIZACIÓN", f"ID {id_sel}: {n_desc}")
                    st.success("✅ Cambios guardados localmente.")
                    st.rerun()

    def formulario_nuevo(self):
        st.subheader("➕ Registro de Nuevo Producto")
        puede_crear = check_permiso("ingresar")
        
        with st.form("form_nuevo_identity", clear_on_submit=False):
            c_ref, c_img = st.columns([1.2, 1.8])
            ref = c_ref.text_input("Referencia")
            archivo_img = c_img.file_uploader("Seleccionar imagen (.jpg, .png)", type=["jpg", "png", "jpeg"])

            c1, c2 = st.columns(2)
            espec = c1.text_input("Especificación")
            marca = c2.text_input("Marca")
            desc = st.text_input("Descripción Completa")
            
            c3, c4 = st.columns(2)
            ubica = c3.text_input("Ubicación en Bodega")
            um = c4.text_input("U/M", value="CAJA")
            
            c6, c7 = st.columns(2)
            cant = c6.number_input("Cantidad Inicial", min_value=0, value=0, step=1)
            costo = c7.number_input("Costo Unitario ($)", min_value=0.0, format="%.2f")
            
            c8, c9, c10 = st.columns(3)
            emp = c8.text_input("Detalle Empaque")
            peso = c9.number_input("Peso Inicial (KG)", min_value=0.0, format="%.2f", step=0.1)
            cubic = c10.number_input("Cubicaje Inicial (M3)", min_value=0.0, format="%.2f", step=0.01)

            btn_registrar = st.form_submit_button("🚀 Registrar en Inventario", width='stretch', disabled=not puede_crear)

            if btn_registrar and puede_crear:
                if not desc or not marca:
                    st.error("❌ La Marca y la Descripción son obligatorias.")
                else:
                    ruta_imagen_subida = self.guardar_imagen_local(archivo_img)
                    query = """
                        INSERT INTO productos (
                            referencia, especificacion, marca, descripcion, ubicacion, 
                            cantidad, costo_unit, total, empaque, peso, cubicaje, um, imagen
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (ref, espec, marca, desc, ubica, int(cant), costo, int(cant)*costo, emp, peso, cubic, um, ruta_imagen_subida)
                    self.db.ejecutar_consulta(query, params)
                    self.registrar_evento("CREACIÓN", f"Nuevo producto registrado: {desc}")
                    st.success("✅ Producto registrado exitosamente.")
                    st.rerun()