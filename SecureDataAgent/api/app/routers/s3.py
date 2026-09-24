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
    return boto3.client("s3", region_name=settings.AWS_REGION)

# Mock data for local testing when AWS S3 bucket is not configured
SAMPLE_FILES = {
    "finance/revenue.csv": "quarter,revenue,growth\n2026-Q1,1500000,12%\n2026-Q2,1850000,15%\n2026-Q3,2100000,18%",
    "finance/expenses.csv": "category,amount\noperations,450000\nmarketing,320000\nengineering,680000",
    "hr/salaries.csv": "employee_id,department,salary\nemp_101,finance,120000\nemp_102,engineering,140000",
    "engineering/specs.txt": "AgentCore Gateway Architecture: MCP protocol with Cedar authorization at the edge."
}

@router.get(
    "/files/{key:path}",
    response_model=S3ReadFileResponse,
    operation_id="read_file",
    summary="Read approved file from company S3 storage",
    description="Reads and returns the text content of a file stored in Amazon S3."
)
def read_file(
    key: str,
    bucket: str = Query(default=settings.DEFAULT_S3_BUCKET, description="Target S3 bucket name")
):
    # Local mock fallback
    if key in SAMPLE_FILES:
        return S3ReadFileResponse(
            bucket=bucket,
            key=key,
            content=SAMPLE_FILES[key],
            content_type="text/csv" if key.endswith(".csv") else "text/plain"
        )
    
    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return S3ReadFileResponse(
            bucket=bucket,
            key=key,
            content=content,
            content_type=response.get("ContentType", "text/plain")
        )
    except Exception as e:
        # If not found in S3 or AWS credentials missing, raise 404
        raise HTTPException(status_code=404, detail=f"File not found: s3://{bucket}/{key}")

@router.get(
    "/files",
    response_model=S3ListFilesResponse,
    operation_id="list_files",
    summary="List files in S3 bucket with a prefix",
    description="Lists object keys in an S3 bucket matching the specified prefix."
)
def list_files(
    prefix: str = Query(default="", description="Key prefix folder path, e.g. finance/"),
    bucket: str = Query(default=settings.DEFAULT_S3_BUCKET, description="Target S3 bucket name")
):
    try:
        s3 = get_s3_client()
        paginator = s3.get_paginator("list_objects_v2")
        files: List[str] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                files.append(obj["Key"])
        return S3ListFilesResponse(bucket=bucket, prefix=prefix, files=files)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
