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
    
    # Airflow Configuration
    AIRFLOW_ENABLED = os.getenv('AIRFLOW_ENABLED', 'false').lower() == 'true'
    AIRFLOW_BASE_URL = os.getenv('AIRFLOW_BASE_URL', 'http://airflow-webserver:8080')
    AIRFLOW_USERNAME = os.getenv('AIRFLOW_USERNAME', 'admin')
    AIRFLOW_PASSWORD = os.getenv('AIRFLOW_PASSWORD', 'admin')

config = Config()