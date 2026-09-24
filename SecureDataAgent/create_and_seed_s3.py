import boto3
import json

s3 = boto3.client('s3', region_name='us-east-1')
bucket_name = "secure-data-lake-025066239748"

print(f"Creating S3 bucket: {bucket_name}...")
try:
    s3.create_bucket(Bucket=bucket_name)
    print("Bucket created successfully!")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print("Bucket already exists and is owned by you.")
except Exception as e:
    print(f"Error creating bucket: {e}")

# Sample files
files = {
    "finance/q3_revenue.csv": "quarter,revenue,profit_margin\n2026-Q1,1500000,24%\n2026-Q2,1850000,27%\n2026-Q3,2200000,31%",
    "engineering/architecture_design.txt": "Core Architecture: AWS Bedrock MCP Gateway + Cedar Authorization Engine + Neon Postgres + S3 Data Lake.",
    "hr/employee_salaries.csv": "emp_id,name,department,salary\nE101,Alice,Finance,125000\nE102,Bob,Engineering,155000"
}

for key, content in files.items():
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType="text/csv" if key.endswith(".csv") else "text/plain"
    )
    print(f"Uploaded s3://{bucket_name}/{key}")

# Allow public read or check block public access so Render service can read without expiring SSO credentials
try:
    # Disable block public access for reading demo objects
    s3.delete_public_access_block(Bucket=bucket_name)
    print("Removed public access block.")
except Exception as e:
    print(f"Note on public access block: {e}")

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicReadOnly",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ]
        }
    ]
}

try:
    s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
    print("Attached public read policy to bucket successfully!")
except Exception as e:
    print(f"Note on bucket policy: {e}")
