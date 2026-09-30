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


def delete_files(object_keys: list[str]) -> None:
    for start in range(0, len(object_keys), 1000):
        response = s3_client.delete_objects(
            Bucket=AWS_S3_BUCKET,
            Delete={
                "Objects": [
                    {"Key": object_key}
                    for object_key in object_keys[start : start + 1000]
                ],
                "Quiet": True,
            },
        )
        errors = response.get("Errors", [])
        if errors:
            failed_keys = ", ".join(
                item.get("Key", "<unknown>") for item in errors
            )
            raise RuntimeError(
                f"Failed to delete object-storage files: {failed_keys}"
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