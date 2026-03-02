import boto3
import os
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger

class S3Storage:
    def __init__(self):
        if settings.USE_S3:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket = settings.AWS_S3_BUCKET

    def upload_file(self, file_content: bytes, file_key: str):
        if not settings.USE_S3:
            # Fallback to local
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            path = os.path.join(settings.UPLOAD_DIR, file_key)
            with open(path, "wb") as f:
                f.write(file_content)
            return path

        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=file_key,
                Body=file_content,
                ContentType='application/pdf'
            )
            return f"s3://{self.bucket}/{file_key}"
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            raise e

    def download_file(self, file_key: str, destination_path: str):
        if not settings.USE_S3:
            # Local case: file is already there, but we copy it to temp if needed
            return os.path.join(settings.UPLOAD_DIR, file_key)

        try:
            self.s3.download_file(self.bucket, file_key, destination_path)
            return destination_path
        except ClientError as e:
            logger.error(f"S3 Download Error: {e}")
            raise e

    def delete_file(self, file_key: str):
        if not settings.USE_S3:
            path = os.path.join(settings.UPLOAD_DIR, file_key)
            if os.path.exists(path):
                os.remove(path)
            return

        try:
            self.s3.delete_object(Bucket=self.bucket, Key=file_key)
        except ClientError as e:
            logger.error(f"S3 Delete Error: {e}")

storage = S3Storage()
