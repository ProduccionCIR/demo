# utilidades.py — Seguridad, Hashing y Control de Acceso por Rol (RBAC)
import hashlib
import hmac
import os
import streamlit as st

# ─── CONSTANTES DE ROLES ────────────────────────────────────────────────────
ROLES_VALIDOS = ["usuario", "contador", "supervisor", "administrador", "master_it"]

# Prefijo que identifica una contraseña hasheada (para distinguir de texto plano)
HASH_PREFIX = "pbkdf2_sha256$"

# ─── HASHING DE CONTRASEÑAS ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Genera un hash seguro PBKDF2-HMAC-SHA256 con sal aleatoria.
    Formato de salida: pbkdf2_sha256$<sal_hex>$<hash_hex>
    Longitud máxima: ~115 caracteres.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return f"{HASH_PREFIX}{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Verifica una contraseña contra un valor almacenado.
    - Si el valor almacenado empieza con HASH_PREFIX → verifica usando PBKDF2.
    - Si no (texto plano heredado) → comparación directa de cadenas.
    Retorna True si coincide, False en caso contrario.
    """
    if not stored:
        return False
    try:
        if stored.startswith(HASH_PREFIX):
            # Contraseña hasheada: extraer sal y hash
            partes = stored[len(HASH_PREFIX):].split("$")
            if len(partes) != 2:
                return False
            salt = bytes.fromhex(partes[0])
            hash_almacenado = bytes.fromhex(partes[1])
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
            return hmac.compare_digest(dk, hash_almacenado)
        else:
            # Contraseña en texto plano (legacy) — comparación directa
            return password == stored
    except Exception:
        # Fallback de seguridad: si algo falla en la verificación, negar el acceso
        return False


def is_hashed(stored: str) -> bool:
    """Retorna True si la cadena ya está hasheada con el prefijo esperado."""
    return isinstance(stored, str) and stored.startswith(HASH_PREFIX)


# ─── CONTROL DE ACCESO POR ROL (RBAC) ───────────────────────────────────────

def get_rol() -> str:
    """Obtiene el rol del usuario actualmente autenticado desde session_state."""
    user_data = st.session_state.get("user_data") or {}
    # Sanitizar el rol para corregir variaciones involuntarias como "master it" -> "master_it"
    return str(user_data.get("rol", "")).lower().replace(" ", "_").strip()


def check_permiso(modulo: str, accion: str) -> bool:
    """
    Verifica si el usuario autenticado tiene permiso para realizar una acción
    en un módulo determinado del RAV System.
    """
    rol = get_rol()

    # master_it tiene acceso total e irrestricto siempre
    if rol == "master_it":
        return True

    # Matriz de permisos unificada y corregida sin contradicciones
    permisos = {
        "inventario": {
            "ver":      ["usuario", "contador", "supervisor", "administrador"],
            "crear":    ["usuario", "supervisor", "administrador"], # El contador solo visualiza stock
            "editar":   ["supervisor", "administrador"],
            "eliminar": ["administrador"],
        },
        "cotizaciones": {
            "ver":      ["usuario", "contador", "supervisor", "administrador"],
            "crear":    ["usuario", "supervisor", "administrador"],
            "editar":   ["supervisor", "administrador"],
            "facturar": ["supervisor", "administrador"],
            "eliminar": ["supervisor", "administrador"],
        },
        "ventas": {
            "ver":      ["usuario", "contador", "supervisor", "administrador"],
            "crear":    ["usuario", "supervisor", "administrador"],
            "anular":   ["supervisor", "administrador"],
            "eliminar": ["supervisor", "administrador"],
        },
        "clientes": {
            "ver":      ["usuario", "contador", "supervisor", "administrador"],
            "crear":    ["usuario", "supervisor", "administrador"],
            "editar":   ["supervisor", "administrador"],
            "eliminar": ["administrador"],
        },
        "contabilidad": {
            "ver":      ["contador", "administrador"], # Bloqueado para rol 'usuario' y 'supervisor'
            "crear":    ["contador", "administrador"], # Permite registrar egresos, depósitos y recibos
            "editar":   ["contador", "administrador"],
            "anular":   ["contador", "administrador"],
        },
        "configuracion": {
            "ver":      [],  # Exclusivo de master_it
            "crear":    [],
            "editar":   [],
            "eliminar": [],
        },
    }

    modulo_l = modulo.lower()
    accion_l = accion.lower()

    if modulo_l not in permisos:
        return False
    if accion_l not in permisos[modulo_l]:
        return False

    return rol in permisos[modulo_l][accion_l]