from fastapi import APIRouter
from services.supabase.client import get_supabase

router = APIRouter()


@router.get("/health")
def health():
    try:
        client = get_supabase()
        client.table("_health_check").select("*").limit(1).execute()
        db_status = "ok"
    except Exception as e:
        error = str(e)
        # A "relation does not exist" error still means the DB connection works
        if "does not exist" in error or "relation" in error.lower() or "PGRST205" in error:
            db_status = "ok"
        else:
            return {"status": "error", "db": "unreachable", "detail": error}

    return {"status": "ok", "db": db_status}
