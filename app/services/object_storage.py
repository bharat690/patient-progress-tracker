import boto3
from botocore.client import Config

from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_ENDPOINT_URL_S3,
    AWS_S3_BUCKET,
)

if not all(
    [
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_REGION,
        AWS_ENDPOINT_URL_S3,
        AWS_S3_BUCKET,
    ]
):
    raise RuntimeError("Neon Object Storage configuration is incomplete")


s3_client = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL_S3,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
    config=Config(signature_version="s3v4"),
)


def upload_file(
    file_path: str,
    object_key: str,
    content_type: str = "application/pdf",
):
    s3_client.upload_file(
        file_path,
        AWS_S3_BUCKET,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )


def download_file(object_key: str) -> bytes:
    response = s3_client.get_object(
        Bucket=AWS_S3_BUCKET,
        Key=object_key,
    )

    return response["Body"].read()


def file_exists(object_key: str) -> bool:
    from botocore.exceptions import ClientError

    try:
        s3_client.head_object(
            Bucket=AWS_S3_BUCKET,
            Key=object_key,
        )
        return True
    except ClientError:
        return False