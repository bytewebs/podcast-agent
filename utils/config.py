import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://podcast_user:podcast_pass@localhost:5432/podcast_db')
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
    KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'podcast-generation-group')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    
    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # Prefect Configuration
    PREFECT_ENABLED = os.getenv('PREFECT_ENABLED', 'true').lower() == 'true'
    PREFECT_API_URL = os.getenv('PREFECT_API_URL', 'http://prefect-server:4200/api')
    PREFECT_API_KEY = os.getenv('PREFECT_API_KEY')  # For Prefect Cloud

    # Email Approval Configuration
    EMAIL_APPROVAL_ENABLED = os.getenv('EMAIL_APPROVAL_ENABLED', 'true').lower() == 'true'
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL', os.getenv('SMTP_USER'))
    
    # Base URL for approval links
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5050')
    
    # Email Security
    EMAIL_SECRET_KEY = os.getenv('EMAIL_SECRET_KEY', 'your-secret-key-change-this')
    
    # Approval Settings
    AUTO_APPROVE_OUTLINE = os.getenv('AUTO_APPROVE_OUTLINE', 'false').lower() == 'true'
    AUTO_APPROVE_SCRIPT = os.getenv('AUTO_APPROVE_SCRIPT', 'false').lower() == 'true'
    AUTO_APPROVE_AUDIO = os.getenv('AUTO_APPROVE_AUDIO', 'false').lower() == 'true'
    
    # Default email for approvals (fallback)
    DEFAULT_APPROVAL_EMAIL = os.getenv('DEFAULT_APPROVAL_EMAIL')
    
    # Approval timeouts
    APPROVAL_TIMEOUT_HOURS = int(os.getenv('APPROVAL_TIMEOUT_HOURS', 168))  # 7 days
    APPROVAL_CHECK_INTERVAL = int(os.getenv('APPROVAL_CHECK_INTERVAL', 30))  # 30 seconds

config = Config()
