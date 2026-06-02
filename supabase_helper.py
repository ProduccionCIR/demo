class SupabaseHelper:
    def __init__(self, client):
        self.client = client

    def fetch(self, tabla, select="*"):
        try:
            res = self.client.table(tabla).select(select).execute()
            return res.data if res.data else []
        except Exception as e:
            print(f"Error en fetch ({tabla}): {e}")
            return []

    def insert(self, tabla, data):
        try:
            res = self.client.table(tabla).insert(data).execute()
            return res.data
        except Exception as e:
            print(f"Error en insert ({tabla}): {e}")
            raise e

    def update(self, tabla, data, id_registro):
        try:
            res = self.client.table(tabla).update(data).eq("id", id_registro).execute()
            return res.data
        except Exception as e:
            print(f"Error en update ({tabla}): {e}")
            raise e

    def delete(self, tabla, id_registro):
        try:
            return self.client.table(tabla).delete().eq("id", id_registro).execute()
        except Exception as e:
            print(f"Error en delete: {e}")
            return None

    def rpc(self, nombre_funcion, parametros=None):
        """Retorna la ejecución del RPC directo del cliente nativo"""
        params = parametros if parametros is not None else {}
        return self.client.rpc(nombre_funcion, params)