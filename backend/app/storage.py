import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket():
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)


def get_presigned_url(key: str, expires_in: int = 3600):
    # 1. Генерируем ссылку на MinIO с ПУБЛИЧНЫМ адресом
    public_s3_client = boto3.client(
        "s3",
        endpoint_url=settings.public_url,  # <-- Используем наш ngrok URL
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

    url = public_s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": key},
        ExpiresIn=expires_in,
    )

    # 2. Добавляем префикс /minio/, чтобы запрос шел через Nginx
    # (endpoint_url был https://ngrok, получится https://ngrok/key, нужно https://ngrok/minio/key)
    return url.replace(f"{settings.public_url}/", f"{settings.public_url}/minio/")
