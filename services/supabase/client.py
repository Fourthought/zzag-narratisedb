import os
from supabase import create_client, Client
from typing import Optional


class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY environment variables must be set")

            cls._instance = create_client(url, key)

        return cls._instance


def get_supabase() -> Client:
    return SupabaseClient.get_client()
