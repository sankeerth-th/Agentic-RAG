"""Create the configured local source bucket; provisioning stays outside API startup."""

from app.core.config import Settings
from app.core.services import Services
from botocore.exceptions import ClientError

services = Services(Settings())
try:
    try:
        services.storage.check()
    except ClientError as exc:
        if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
            raise
        settings = Settings()
        options = {}
        if settings.s3_region != "us-east-1":
            options["CreateBucketConfiguration"] = {"LocationConstraint": settings.s3_region}
        services.storage.client.create_bucket(Bucket=settings.s3_bucket, **options)
    print("Source bucket is ready.")
finally:
    services.close()
