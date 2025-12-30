import os
from typing import Optional

class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:Aru247899!@localhost/ostrich_db")
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
        self.aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_s3_bucket: Optional[str] = os.getenv("AWS_S3_BUCKET")

settings = Settings()