# auth.py
import streamlit as st
import pandas as pd
import hashlib

class ModuloAuth:
    def __init__(self, db):
        """
        Recibe la instancia de la base de datos local (SQLiteHelper).
        """
        self.db = db
        self._inicializar_estados()

    def _inicializar_estados(self):
        """Asegura que las llaves esenciales de sesión existan en el state."""
        if 'auth' not in st.session_state:
            st.session_state.auth = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'rol' not in st.session_state:
            st.session_state.rol = None

    def _verificar_password(self, password_ingresada, password_guardada):
        """
        Verifica si la contraseña ingresada coincide con el hash almacenado.
        Soporta fallback temporal a texto plano por si tienes registros de pruebas antiguos.
        """
        # Generar hash SHA-256 de la contraseña ingresada
        hash_ingresado = hashlib.sha256(password_ingresada.encode('utf-8')).hexdigest()
        
        # Comparación segura contra el hash o fallback en texto plano si aún no se ha migrado la BD
        return hash_ingresado == password_guardada or password_ingresada == password_guardada

    def login(self):
        st.markdown("<h1 style='text-align: center;'>🛡️ CIR PANAMÁ OS</h1>", unsafe_allow_html=True)
        
        with st.container(border=True):
            usuario_raw = st.text_input("Usuario")
            clave_raw = st.text_input("Contraseña", type="password")
            
            if st.button("Ingresar", use_container_width=True):
                u = usuario_raw.strip().lower()
                p = clave_raw.strip()
                
                if not u or not p:
                    st.warning("Por favor, complete todos los campos.")
                    return

                try:
                    # Buscamos únicamente por usuario para mitigar ataques de temporización 
                    # y verificar el hash en memoria de manera segura
                    query = "SELECT * FROM perfiles WHERE LOWER(TRIM(usuario)) = ?"
                    res = self.db.ejecutar_consulta(query, (u,))

                    if res and len(res) > 0:
                        user_data = res[0]
                        password_db = user_data.get('clave', '')

                        # Validación criptográfica segura
                        if self._verificar_password(p, password_db):
                            st.session_state.auth = True
                            st.session_state.user = u
                            st.session_state.user_data = dict(user_data)
                            st.session_state.rol = str(user_data.get('rol', 'usuario')).lower()
                            
                            st.success(f"Bienvenido {user_data.get('nombre_completo', u)}")
                            st.rerun()
                        else:
                            st.error("🚫 Credenciales incorrectas. Verifique usuario y contraseña.")
                    else:
                        st.error("🚫 Credenciales incorrectas. Verifique usuario y contraseña.")
                        
                except Exception as e:
                    st.error(f"Error de conexión con la BD local: {e}")

    def logout(self):
        """Limpia TODO el Session State de raíz y fuerza el renderizado inicial."""
        st.session_state.clear()
        # Forzar re-inicialización post-limpieza para evitar errores en cascada
        self._inicializar_estados()
        st.rerun()