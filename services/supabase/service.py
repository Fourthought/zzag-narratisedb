from supabase import Client
from typing import Dict, Any, List, Optional


class SupabaseService:
    def __init__(self, client: Client):
        self.client = client

    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else {}

    def get_records(self, table: str, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = self.client.table(table).select("*")

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        return result.data

    def get_record_by_id(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table(table).select(
            "*").eq("id", record_id).execute()
        return result.data[0] if result.data else None

    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.client.table(table).update(
            data).eq("id", record_id).execute()
        return result.data[0] if result.data else {}

    def delete_record(self, table: str, record_id: str) -> bool:
        result = self.client.table(table).delete().eq(
            "id", record_id).execute()
        return bool(result.data)
