import redis
import uuid
import pickle
from typing import Any
from app.core.config import settings

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_CACHE_DB = settings.REDIS_CACHE_DB


class RedisCache:
    """Simple Redis cache for storing Python objects using pickle."""

    def __init__(self, host: str, port: int, db: int) -> None:
        """Initialize Redis connection."""
        self.cache: redis.Redis = redis.Redis(host=host, port=port, db=db)

    def save(self, payload: Any) -> str:
        """Save a Python object to Redis and return a unique key."""
        key: str = f"payload:{uuid.uuid4()}"
        self.cache.set(key, pickle.dumps(payload))
        return key

    def load(self, key: str) -> Any:
        """Load a Python object from Redis using its key."""
        return pickle.loads(self.cache.get(key))

    def delete(self, key: str) -> None:
        """Delete an object from Redis using its key."""
        self.cache.delete(key)

CACHE = RedisCache(REDIS_HOST, REDIS_PORT, REDIS_CACHE_DB)
