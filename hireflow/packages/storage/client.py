"""
Object store abstraction — MinIO (dev) / AWS S3 (GA).

All CV files are stored at:
  /{tenant_id}/{job_id}/{candidate_email_hash}/{timestamp}/cv.{ext}

Screenshots:
  /screenshots/{job_id}/{post_id}.png

Presigned URLs expire in 24 hours by default.
"""

import hashlib
import io
import os
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

_client: Minio | None = None
_bucket: str = ""


def _get_client() -> tuple[Minio, str]:
    global _client, _bucket
    if _client is None:
        _client = Minio(
            os.environ["MINIO_ENDPOINT"],
            access_key=os.environ["MINIO_ACCESS_KEY"],
            secret_key=os.environ["MINIO_SECRET_KEY"],
            secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
        )
        _bucket = os.environ.get("MINIO_BUCKET", "hireflow-cvs")
        if not _client.bucket_exists(_bucket):
            _client.make_bucket(_bucket)
    return _client, _bucket


def upload(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client, bucket = _get_client()
    client.put_object(bucket, key, io.BytesIO(data), len(data), content_type=content_type)
    return key


def download(key: str) -> bytes:
    client, bucket = _get_client()
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()


def presigned_url(key: str, expires_hours: int = 24) -> str:
    client, bucket = _get_client()
    return client.presigned_get_object(bucket, key, expires=timedelta(hours=expires_hours))


def cv_key(tenant_id: str, job_id: str, email: str, timestamp: str, ext: str) -> str:
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"{tenant_id}/{job_id}/{email_hash}/{timestamp}/cv.{ext}"


def screenshot_key(job_id: str, post_id: str) -> str:
    return f"screenshots/{job_id}/{post_id}.png"
