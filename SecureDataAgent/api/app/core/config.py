import os
from pydantic import BaseModel

class Settings(BaseModel):
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DEFAULT_S3_BUCKET: str = os.getenv("DEFAULT_S3_BUCKET", "usefulbi-ma-insights-data")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
