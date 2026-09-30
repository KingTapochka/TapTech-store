import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "172.17.0.1")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def ping_redis():
    return redis_client.ping()
