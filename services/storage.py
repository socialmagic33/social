import boto3
from botocore.exceptions import ClientError
import os
from fastapi import UploadFile
import magic
from app.config import settings

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_BUCKET_NAME

    async def upload_file(self, file: UploadFile, folder: str = "") -> str:
        """Upload a file to S3 bucket and return its URL"""
        content = await file.read()
        content_type = magic.from_buffer(content, mime=True)
        
        # Generate a unique filename
        filename = f"{folder}/{os.urandom(16).hex()}_{file.filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=content,
                ContentType=content_type
            )
            
            # Generate the URL
            url = f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url
            
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def delete_file(self, url: str):
        """Delete a file from S3 bucket"""
        try:
            # Extract key from URL
            key = url.split(f"{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
        except ClientError as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")

storage = S3Storage()