import boto3
from botocore.exceptions import ClientError
from utils.config import config
import json
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.S3_REGION
        )
        self.bucket = config.S3_BUCKET_NAME
    
    def upload_file(self, file_path: str, s3_key: str) -> str:
        """Upload file to S3"""
        try:
            self.s3.upload_file(
                file_path, 
                self.bucket, 
                s3_key,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            url = f"https://{self.bucket}.s3.{config.S3_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded to {url}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise
    
    def upload_content(self, content: bytes, s3_key: str, content_type: str = 'text/plain') -> str:
        """Upload content directly to S3"""
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                ACL='public-read'
            )
            
            url = f"https://{self.bucket}.s3.{config.S3_REGION}.amazonaws.com/{s3_key}"
            return url
            
        except ClientError as e:
            logger.error(f"S3 content upload failed: {str(e)}")
            raise
    
    def upload_json(self, data: dict, s3_key: str) -> str:
        """Upload JSON data to S3"""
        json_content = json.dumps(data, indent=2).encode('utf-8')
        return self.upload_content(json_content, s3_key, 'application/json')
    
    def get_file(self, s3_key: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"S3 download failed: {str(e)}")
            raise
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False