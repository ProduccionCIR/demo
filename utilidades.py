# utilidades.py
import streamlit as st

# Definimos el peso de cada rol en la jerarquía del sistema
ROLES_JERARQUIA = {
    "usuario": 1,
    "supervisor": 2,
    "administrador": 3,
    "master_it": 4
}

def check_permiso(accion_requerida):
    """
    Controlador de seguridad jerárquico para RAV System.
    Determina si el usuario en sesión tiene el nivel suficiente para ejecutar una acción.
    """
    # 1. Recuperar el rol actual de la sesión de forma segura
    rol_actual = st.session_state.get('rol')
    if not rol_actual:
        return False
    
    # Sanitizar strings para evitar fallas por espacios o mayúsculas
    rol_actual = str(rol_actual).strip().lower()
    accion_requerida = str(accion_requerida).strip().lower()
    
    # Si el rol en sesión no está mapeado, denegar por seguridad
    if rol_actual not in ROLES_JERARQUIA:
        return False
        
    nivel_usuario = ROLES_JERARQUIA[rol_actual]
    
    # 2. Evaluar el nivel mínimo requerido para cada acción del negocio
    nivel_requerido = 99  # Por defecto, nadie pasa a menos que coincida abajo
    
    if accion_requerida in ["ingresar", "crear", "ver"]:
        nivel_requerido = ROLES_JERARQUIA["usuario"]        # Nivel 1 en adelante
        
    elif accion_requerida in ["modificar", "editar", "actualizar"]:
        nivel_requerido = ROLES_JERARQUIA["supervisor"]     # Nivel 2 en adelante
        
    elif accion_requerida in ["eliminar", "borrar", "purgar"]:
        nivel_requerido = ROLES_JERARQUIA["administrador"]  # Nivel 3 en adelante
        
    elif accion_requerida in ["configurar", "clonar", "auditar"]:
        nivel_requerido = ROLES_JERARQUIA["master_it"]      # Solo nivel 4

    # 3. Contraste jerárquico: Si tu nivel es mayor o igual al requerido, tienes acceso
    return nivel_usuario >= nivel_requerido