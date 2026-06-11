import os
from supabase import create_client, Client

class SupabaseDataLayer:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(self.url, self.key) if self.url and self.key else None

    def save_checkpoint(self, table: str, data: dict):
        if self.client:
            return self.client.table(table).insert(data).execute()
        return None

db = SupabaseDataLayer()
