from fastapi import APIRouter
from services.supabase.client import get_supabase

router = APIRouter(prefix="/shield-codes")


@router.get("")
def get_shield_codes():
    client = get_supabase()
    result = client.table("chirp_shield_codes").select(
        "*, chirp_shield_code_categories(name)"
    ).execute()
    return result.data
