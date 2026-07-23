# database.py — Capa de Abstracción de Base de Datos (Supabase + SQLite Local)
# Soporta sincronización bidireccional automática en segundo plano.

import os
import sqlite3
import threading
import time
import json
import streamlit as st

# ─── TABLAS Y ESQUEMAS ORIGINALES MANTENIDOS ──────────────────────────────────
SCHEMAS = {
    "perfiles": """
        CREATE TABLE IF NOT EXISTS perfiles (
            id TEXT PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            clave TEXT,
            rol TEXT,
            creado_en TEXT,
            nombre_completo TEXT,
            cargo TEXT
        )
    """,
    "productos": """
        CREATE TABLE IF NOT EXISTS productos (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            REFERENCIA TEXT UNIQUE,
            MARCA TEXT,
            TIPO TEXT,
            "UBICACIÓN" TEXT,
            DESCRIPCION TEXT,
            "ENTRADA 2019" TEXT,
            "ENTRADA 2024" TEXT,
            "ENTRADA 2025" TEXT,
            CANTIDAD REAL DEFAULT 0,
            "U/M" TEXT,
            "COSTO UNIT" REAL DEFAULT 0,
            TOTAL REAL DEFAULT 0,
            EMPAQUE TEXT,
            "CANTIDAD CAJA" TEXT,
            PESO TEXT,
            CUBICAJE TEXT,
            IMAGEN TEXT,
            codigo_barra INTEGER,
            composicion TEXT
        )
    """,
    "cotizaciones": """
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_cot INTEGER,
            cliente TEXT,
            total REAL,
            detalles TEXT,
            fecha TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    """,
    "ventas": """
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_fact INTEGER,
            cliente TEXT,
            total REAL,
            flete REAL DEFAULT 0,
            descuento REAL DEFAULT 0,
            detalle TEXT,
            via_despacho TEXT,
            fecha TEXT,
            estado TEXT DEFAULT 'PENDIENTE'
        )
    """,
    "recibos": """
        CREATE TABLE IF NOT EXISTS recibos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            monto REAL,
            metodo_pago TEXT,
            id_venta INTEGER,
            fecha TEXT
        )
    """,
    "gastos": """
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monto REAL,
            descripcion TEXT,
            fecha TEXT
        )
    """,
    "depositos": """
        CREATE TABLE IF NOT EXISTS depositos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco TEXT,
            monto REAL,
            referencia TEXT,
            fecha TEXT
        )
    """,
    "logs_sistema": """
        CREATE TABLE IF NOT EXISTS logs_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            usuario TEXT,
            rol TEXT,
            accion TEXT,
            modulo TEXT,
            detalle TEXT,
            created_at TEXT
        )
    """,
    "clientes": """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            identificacion TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            es_offshore INTEGER DEFAULT 0,
            registrado_por TEXT,
            fecha_registro TEXT
        )
    """,
}

JSON_COLUMNS = {"detalles", "detalle"}
SYNC_TABLES = ["productos", "cotizaciones", "ventas", "recibos", "gastos", "depositos", "clientes"]

def _serialize(val):
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    return val

def _deserialize_row(row: dict) -> dict:
    result = {}
    for k, v in row.items():
        if k in JSON_COLUMNS and isinstance(v, str):
            try:
                result[k] = json.loads(v)
            except Exception:
                result[k] = v
        else:
            result[k] = v
    return result

# ─── EMULADOR DE CONSULTA SQLITE ─────────────────────────────────────────────
class SQLiteQueryBuilder:
    def __init__(self, conn: sqlite3.Connection, table: str):
        self._conn = conn
        self._table = table
        self._select = "*"
        self._filters = []
        self._order = None
        self._desc = False
        self._limit = None
        self._data = None
        self._op = None

    def select(self, cols="*"):
        self._select = cols
        self._op = "select"
        return self

    def insert(self, data: dict):
        self._data = data
        self._op = "insert"
        return self

    def update(self, data: dict):
        self._data = data
        self._op = "update"
        return self

    def delete(self):
        self._op = "delete"
        return self

    def upsert(self, data, on_conflict="id"):
        self._data = data
        self._on_conflict = on_conflict
        self._op = "upsert"
        return self

    def eq(self, col, val):
        self._filters.append((col, "=", val))
        return self

    def neq(self, col, val):
        self._filters.append((col, "!=", val))
        return self

    def order(self, col, desc=False):
        self._order = col
        self._desc = desc
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        cur = self._conn.cursor()
        try:
            if self._op == "select":
                return self._do_select(cur)
            elif self._op == "insert":
                return self._do_insert(cur)
            elif self._op == "update":
                return self._do_update(cur)
            elif self._op == "delete":
                return self._do_delete(cur)
            elif self._op == "upsert":
                return self._do_upsert(cur)
        except Exception as e:
            self._conn.rollback()
            raise e

    def _build_where(self):
        if not self._filters:
            return "", []
        clauses = []
        vals = []
        for col, op, val in self._filters:
            clauses.append(f'"{col}" {op} ?')
            vals.append(val)
        return "WHERE " + " AND ".join(clauses), vals

    def _do_select(self, cur):
        where, vals = self._build_where()
        order = f'ORDER BY "{self._order}" {"DESC" if self._desc else "ASC"}' if self._order else ""
        limit = f"LIMIT {self._limit}" if self._limit else ""
        sql = f'SELECT {self._select} FROM "{self._table}" {where} {order} {limit}'
        cur.execute(sql, vals)
        cols = [d[0] for d in cur.description]
        rows = [_deserialize_row(dict(zip(cols, r))) for r in cur.fetchall()]
        class Result: data = rows
        return Result()

    def _do_insert(self, cur):
        d = {k: _serialize(v) for k, v in self._data.items()}
        cols = ", ".join(f'"{c}"' for c in d.keys())
        placeholders = ", ".join("?" for _ in d)
        sql = f'INSERT OR IGNORE INTO "{self._table}" ({cols}) VALUES ({placeholders})'
        cur.execute(sql, list(d.values()))
        self._conn.commit()
        class Result: data = []
        return Result()

    def _do_update(self, cur):
        d = {k: _serialize(v) for k, v in self._data.items()}
        sets = ", ".join(f'"{k}" = ?' for k in d)
        where, wvals = self._build_where()
        sql = f'UPDATE "{self._table}" SET {sets} {where}'
        cur.execute(sql, list(d.values()) + wvals)
        self._conn.commit()
        class Result: data = []
        return Result()

    def _do_delete(self, cur):
        where, wvals = self._build_where()
        sql = f'DELETE FROM "{self._table}" {where}'
        cur.execute(sql, wvals)
        self._conn.commit()
        class Result: data = []
        return Result()

    def _do_upsert(self, cur):
        rows = self._data if isinstance(self._data, list) else [self._data]
        for row in rows:
            d = {k: _serialize(v) for k, v in row.items()}
            cols = ", ".join(f'"{c}"' for c in d.keys())
            placeholders = ", ".join("?" for _ in d)
            sql = f'INSERT OR REPLACE INTO "{self._table}" ({cols}) VALUES ({placeholders})'
            cur.execute(sql, list(d.values()))
        self._conn.commit()
        class Result: data = []
        return Result()

# ─── CLIENTE SQLITE LOCAL ────────────────────────────────────────────────────
class SQLiteClient:
    def __init__(self, db_path: str = "rav_system.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()
        self.client = self

    def _init_schema(self):
        cur = self._conn.cursor()
        for schema_sql in SCHEMAS.values():
            cur.execute(schema_sql)
        self._conn.commit()
        
        # Inicializar el espacio de secuencias de auto-incremento a partir de 100,000 para evitar colisiones
        tablas_autoincrementables = ["productos", "cotizaciones", "ventas", "recibos", "gastos", "depositos", "clientes"]
        for t in tablas_autoincrementables:
            cur.execute("SELECT seq FROM sqlite_sequence WHERE name=?", (t,))
            if not cur.fetchone():
                cur.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, 100000)", (t,))
        self._conn.commit()

    def table(self, table_name: str) -> SQLiteQueryBuilder:
        return SQLiteQueryBuilder(self._conn, table_name)

    def fetch(self, tabla: str, select: str = "*") -> list:
        try:
            res = self.table(tabla).select(select).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"[SQLite] Error en fetch ({tabla}): {e}")
            return []

    def insert(self, tabla: str, data: dict):
        try:
            return self.table(tabla).insert(data).execute()
        except Exception as e:
            print(f"[SQLite] Error en insert ({tabla}): {e}")
            raise e

    def update(self, tabla: str, data: dict, id_registro):
        try:
            return self.table(tabla).update(data).eq("id", id_registro).execute()
        except Exception as e:
            print(f"[SQLite] Error en update ({tabla}): {e}")
            raise e

    def delete(self, tabla: str, id_registro):
        try:
            return self.table(tabla).delete().eq("id", id_registro).execute()
        except Exception as e:
            print(f"[SQLite] Error en delete ({tabla}): {e}")
            return None

    def rpc(self, nombre_funcion, parametros=None):
        class FakeRpc:
            def execute(self):
                class R: data = []
                return R()
        return FakeRpc()

    def registrar_log(self, accion, modulo, detalle):
        try:
            import datetime
            log_data = {
                "usuario": "Sistema",
                "accion": accion,
                "modulo": modulo,
                "detalle": detalle,
                "created_at": datetime.datetime.now().isoformat()
            }
            self.insert("logs_sistema", log_data)
        except Exception:
            pass

# ─── SINCRONIZACIÓN BIDIRECCIONAL ────────────────────────────────────────────
def _hay_internet(supabase_url: str) -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(supabase_url, timeout=4)
        return True
    except Exception:
        return False

def _sincronizar_una_vez(sqlite_client: SQLiteClient, supabase_client, supabase_url: str):
    if not _hay_internet(supabase_url):
        return

    for tabla in SYNC_TABLES:
        try:
            # ── PULL: Supabase → SQLite ──────────────────────────────────────
            res = supabase_client.table(tabla).select("*").execute()
            if res.data:
                for row in res.data:
                    d = {k: _serialize(v) for k, v in row.items()}
                    cols = ", ".join(f'"{c}"' for c in d.keys())
                    placeholders = ", ".join("?" for _ in d)
                    cur = sqlite_client._conn.cursor()
                    sql = f'INSERT OR REPLACE INTO "{tabla}" ({cols}) VALUES ({placeholders})'
                    cur.execute(sql, list(d.values()))
                sqlite_client._conn.commit()

            # ── PUSH: SQLite registros offline (>= 100,000) → Supabase ───────
            cur2 = sqlite_client._conn.cursor()
            try:
                # Normalizar la clave de búsqueda de ID sin importar si está en mayúsculas (ID) o minúsculas (id)
                id_col = "ID" if tabla == "productos" else "id"
                cur2.execute(f'SELECT * FROM "{tabla}" WHERE CAST("{id_col}" AS INTEGER) >= 100000')
                cols_info = [d[0] for d in cur2.description]
                rows_offline = [dict(zip(cols_info, r)) for r in cur2.fetchall()]
            except Exception:
                rows_offline = []

            for row in rows_offline:
                row_clean = {k: json.loads(v) if k in JSON_COLUMNS and isinstance(v, str) else v
                             for k, v in row.items()}
                # Omitir el ID para delegar el control secuencial real a la nube
                row_push = {k: v for k, v in row_clean.items() if k.lower() != "id"}
                try:
                    supabase_client.table(tabla).insert(row_push).execute()
                    # Una vez insertado con éxito en la nube, limpiamos el temporal local
                    id_val = row.get("id") or row.get("ID")
                    cur_del = sqlite_client._conn.cursor()
                    cur_del.execute(f'DELETE FROM "{tabla}" WHERE "{id_col}" = ?', (id_val,))
                    sqlite_client._conn.commit()
                except Exception:
                    pass

        except Exception as e:
            print(f"[SYNC] Error sincronizando tabla {tabla}: {e}")

def iniciar_hilo_sincronizacion(sqlite_client: SQLiteClient, supabase_client, supabase_url: str, intervalo_seg: int = 60):
    if st.session_state.get("_sync_thread_started"):
        return

    def loop():
        while True:
            try:
                _sincronizar_una_vez(sqlite_client, supabase_client, supabase_url)
            except Exception as e:
                print(f"[SYNC THREAD] Error inesperado: {e}")
            time.sleep(intervalo_seg)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    st.session_state["_sync_thread_started"] = True
    print("[SYNC] Hilo de sincronización iniciado.")

def get_db_mode() -> str:
    return (os.environ.get("DB_TYPE") or "supabase").strip().lower()

def hay_internet_rapido(supabase_url: str) -> bool:
    return _hay_internet(supabase_url)