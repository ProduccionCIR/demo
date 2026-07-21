# database.py
import sqlite3
import os
import requests
import json
import streamlit as st

class SQLiteHelper:
    def __init__(self, db_name="local_database.db"):
        """
        Inicializa la clase ayudante para la base de datos SQLite local.
        Configura la ruta de almacenamiento dentro del directorio del proyecto.
        """
        data_dir = os.path.join(os.getcwd(), ".data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self.db_path = os.path.join(data_dir, db_name)
        self.inicializar_base_datos()

    def inicializar_base_datos(self):
        """
        Verifica y asegura la existencia del archivo de base de datos local.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except sqlite3.Error as e:
            st.error(f"❌ Error al inicializar la base de datos local: {e}")

    def clonar_desde_supabase(self, url_supabase=None, anon_key=None):
        """
        Descarga la estructura y datos esenciales desde la nube (Supabase)
        y los replica directamente en el motor SQLite local manteniendo llaves primarias nativas.
        """
        url = url_supabase or st.secrets.get("SUPABASE_URL", "TU_URL_DE_SUPABASE")
        key = anon_key or st.secrets.get("SUPABASE_KEY", "TU_ANON_KEY_DE_SUPABASE")
        
        if url == "TU_URL_DE_SUPABASE" or key == "TU_ANON_KEY_DE_SUPABASE":
            st.error("❌ Error: No se han configurado las credenciales reales de Supabase.")
            return False

        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        
        tablas_a_sincronizar = ["perfiles", "inventario", "clientes", "ventas", "cotizaciones"]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for index, tabla in enumerate(tablas_a_sincronizar):
                status_text.text(f"📥 Descargando e integrando tabla local: {tabla}...")
                
                endpoint = f"{url}/rest/v1/{tabla}?select=*"
                response = requests.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    registros = response.json()
                    
                    if registros:
                        cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
                        
                        primer_reg = registros[0]
                        columnas_map = {}
                        columnas_definition = []
                        
                        # Mapeo dinámico completo, incluyendo el ID original como Clave Primaria
                        for col, val in primer_reg.items():
                            if col == 'id':
                                # Mantenemos el ID nativo para no romper llaves foráneas relacionales
                                tipo_sql = "INTEGER PRIMARY KEY" if isinstance(val, int) else "TEXT PRIMARY KEY"
                            elif isinstance(val, int):
                                tipo_sql = "INTEGER"
                            elif isinstance(val, float):
                                tipo_sql = "REAL"
                            else:
                                tipo_sql = "TEXT"
                            
                            columnas_map[col] = tipo_sql
                            if col != 'id':  # El id ya lleva su declaración de PRIMARY KEY incorporada
                                columnas_definition.append(f"{col} {tipo_sql}")
                        
                        # Unimos el ID al principio de la definición de la estructura
                        id_tipo = "INTEGER PRIMARY KEY" if isinstance(primer_reg.get('id'), int) else "TEXT PRIMARY KEY"
                        columnas_sql = f"id {id_tipo}"
                        if columnas_definition:
                            columnas_sql += ", " + ", ".join(columnas_definition)
                            
                        cursor.execute(f"CREATE TABLE {tabla} ({columnas_sql})")
                        
                        for reg in registros:
                            cols = ", ".join(reg.keys())
                            placeholders = ", ".join(["?"] * len(reg))
                            
                            valores_limpios = []
                            for col, val in reg.items():
                                tipo_esperado = columnas_map.get(col, "TEXT")
                                
                                if val is None:
                                    valores_limpios.append(None)
                                elif "INTEGER" in tipo_esperado:
                                    try:
                                        valores_limpios.append(int(val))
                                    except (ValueError, TypeError):
                                        valores_limpios.append(0)
                                elif tipo_esperado == "REAL":
                                    try:
                                        valores_limpios.append(float(val))
                                    except (ValueError, TypeError):
                                        valores_limpios.append(0.0)
                                else:
                                    # Corrección crítica: Serializar objetos de forma segura a JSON string estándar
                                    if isinstance(val, (dict, list)):
                                        valores_limpios.append(json.dumps(val))
                                    else:
                                        valores_limpios.append(str(val))
                            
                            cursor.execute(f"INSERT OR REPLACE INTO {tabla} ({cols}) VALUES ({placeholders})", valores_limpios)
                else:
                    st.warning(f"⚠️ No se pudo acceder a la tabla '{tabla}' (Código HTTP: {response.status_code}).")
                
                progress_bar.progress((index + 1) / len(tablas_a_sincronizar))
            
            conn.commit()
            status_text.empty()
            progress_bar.empty()
            st.success("✅ Base de datos local sincronizada y reconstruida con éxito a partir de la nube.")
            return True
            
        except Exception as e:
            status_text.empty()
            progress_bar.empty()
            st.error(f"❌ Falla crítica durante la clonación de datos: {e}")
            return False
        finally:
            conn.close()

    def ejecutar_consulta(self, query, params=(), fetchall=True):
        """
        Método utilitario para realizar consultas locales (SELECT, INSERT, UPDATE) 
        desde las páginas de la aplicación de manera segura.
        """
        conn = sqlite3.connect(self.db_path)
        # Habilitar acceso por nombre de columna también en este helper genérico
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                resultado = cursor.fetchall() if fetchall else cursor.fetchone()
                return resultado
            else:
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            st.error(f"❌ Error en consulta local: {e}")
            return None
        finally:
            conn.close()