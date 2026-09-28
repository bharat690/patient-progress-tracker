from app.services.object_storage import s3_client
from app.core.config import AWS_S3_BUCKET


response = s3_client.list_objects_v2(
    Bucket=AWS_S3_BUCKET
)

print("Bucket:", AWS_S3_BUCKET)
print("Object storage connection: OK")

for item in response.get("Contents", []):
    print("-", item["Key"])