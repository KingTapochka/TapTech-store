from fastapi import APIRouter, HTTPException
from app.database import get_db_connection, release_db_connection, ping_redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check():
    # Проверка PostgreSQL
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="PostgreSQL unavailable")
    finally:
        release_db_connection(conn)

    # Проверка Redis
    if not ping_redis():
        raise HTTPException(status_code=503, detail="Redis unavailable")

    return {"status": "ok"}
