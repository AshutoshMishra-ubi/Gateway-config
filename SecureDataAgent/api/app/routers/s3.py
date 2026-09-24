from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
try:
    from app.core.config import settings
except ModuleNotFoundError:
    from api.app.core.config import settings

router = APIRouter(prefix="/s3", tags=["S3 Data Service"])

class S3ReadFileResponse(BaseModel):
    bucket: str
    key: str
    content: str
    content_type: Optional[str] = "text/plain"

class S3ListFilesResponse(BaseModel):
    bucket: str
    prefix: str
    files: List[str]

def get_s3_client():
    from botocore import UNSIGNED
    from botocore.client import Config
    import os
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return boto3.client("s3", region_name=settings.AWS_REGION)
    return boto3.client("s3", region_name=settings.AWS_REGION, config=Config(signature_version=UNSIGNED))

@router.get(
    "/files/{key:path}",
    response_model=S3ReadFileResponse,
    operation_id="read_file",
    summary="Read approved file from company S3 storage",
    description="Reads and returns the text content of a file stored in Amazon S3."
)
def read_file(
    key: str,
    bucket: Optional[str] = Query(default=None, description="Target S3 bucket name")
):
    target_bucket = bucket if (isinstance(bucket, str) and bucket.strip()) else settings.DEFAULT_S3_BUCKET
    if target_bucket == "company-secure-data-lake":
        target_bucket = "usefulbi-ma-insights-data"
    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=target_bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return S3ReadFileResponse(
            bucket=target_bucket,
            key=key,
            content=content,
            content_type=response.get("ContentType", "text/plain")
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found or error accessing s3://{target_bucket}/{key}: {str(e)}")

@router.get(
    "/files",
    response_model=S3ListFilesResponse,
    operation_id="list_files",
    summary="List files in S3 bucket with a prefix",
    description="Lists object keys in an S3 bucket matching the specified prefix."
)
def list_files(
    prefix: Optional[str] = Query(default="", description="Key prefix folder path, e.g. finance/"),
    bucket: Optional[str] = Query(default=None, description="Target S3 bucket name")
):
    target_bucket = bucket if (isinstance(bucket, str) and bucket.strip()) else settings.DEFAULT_S3_BUCKET
    if target_bucket == "company-secure-data-lake":
        target_bucket = "usefulbi-ma-insights-data"
    target_prefix = prefix if isinstance(prefix, str) else ""
    try:
        s3 = get_s3_client()
        paginator = s3.get_paginator("list_objects_v2")
        files: List[str] = []
        for page in paginator.paginate(Bucket=target_bucket, Prefix=target_prefix):
            for obj in page.get("Contents", []):
                files.append(obj["Key"])
        return S3ListFilesResponse(bucket=target_bucket, prefix=target_prefix, files=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
