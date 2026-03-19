import hashlib
from typing import BinaryIO, Optional
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

def ensure_bucket_exists():
    bucket_name = "rxncommons-bucket"
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except S3Error as err:
        print(f"MinIO bucket error: {err}")

ensure_bucket_exists()

def generate_file_key(owner_id: uuid.UUID, file_hash: str) -> str:
    """ Generate the MinIO object key per physical_storage_objects rule. """
    return f"{owner_id}_{file_hash}"

