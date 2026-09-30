from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db_connection, release_db_connection, ping_redis
from app.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Проверка БД при старте
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print("PostgreSQL OK")
    finally:
        release_db_connection(conn)

    if ping_redis():
        print("Redis OK")
    else:
        raise RuntimeError("Redis не отвечает")
    
    yield

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для разработки; в проде укажите конкретные домены
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Shop API"}
