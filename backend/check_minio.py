from minio import Minio
from app.core.config import settings

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)
objs = client.list_objects("rxncommons-bucket", recursive=True)
for obj in objs:
    print(obj.object_name, obj.size)
