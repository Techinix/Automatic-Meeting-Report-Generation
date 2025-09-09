import redis
import uuid
import pickle
import boto3
from abc import ABC, abstractmethod
from typing import Any, Optional
from app.core.config import settings


class Cache(ABC):
    @abstractmethod
    def save(self, key: str, payload: Any, expire: Optional[int] = None) -> None:
        """Save a value with a key and optional expiry (seconds)."""
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load a value by key. Return None if not found."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value by key."""
        pass

class RedisCache(Cache):
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


class S3Cache(Cache):
    """Simple S3 cache for storing Python objects using pickle."""

    def __init__(self, bucket: str, endpoint_url: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 region_name: str = "us-east-1") -> None:
        """Initialize S3 client and ensure the bucket exists."""
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,  # MinIO or AWS S3
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        # Create bucket if it doesn't exist (for local dev with MinIO)
        existing_buckets = [b["Name"] for b in self.s3.list_buckets()["Buckets"]]
        print("Existing buckets are :", existing_buckets)
        if bucket not in existing_buckets:
            self.s3.create_bucket(Bucket=bucket)

    def save(self, data: bytes, key: Optional[str] = None) :
        key: str = f"payload:{uuid.uuid4()}" if key is None else key
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        return key

    def load(self, key: str) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def delete(self, key: str) -> None:
        """Delete an object from S3 using its key."""
        self.s3.delete_object(Bucket=self.bucket, Key=key)
        
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a pre-signed URL for the given S3 object.
        :param key: Object key in S3
        :param expires_in: Expiration time in seconds (default 1 hour)
        """
        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in
        )
        return url

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_CACHE_DB = settings.REDIS_CACHE_DB


REDIS_CACHE = RedisCache(REDIS_HOST, REDIS_PORT, REDIS_CACHE_DB)

BUCKET = settings.S3_BUCKET
ENDPOINT_PROTOCOL = settings.S3_ENDPOINT_PROTOCOL
ENDPOINT_HOST = settings.S3_ENDPOINT_HOST
ENDPOINT_PORT = settings.S3_ENDPOINT_PORT
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
REGION = settings.S3_REGION

ENDPOINT_URL = f"{ENDPOINT_PROTOCOL}://{ENDPOINT_HOST}:{ENDPOINT_PORT}"

S3_CACHE = S3Cache(
    BUCKET,
    ENDPOINT_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    REGION
)
