import boto3

s3 = boto3.client('s3', region_name='us-east-1')
bucket = "usefulbi-ma-insights-data"

files = {
    "finance/q3_revenue.csv": "quarter,revenue,profit_margin,status\n2026-Q1,1500000,24%,audited\n2026-Q2,1850000,27%,audited\n2026-Q3,2200000,31%,projected",
    "engineering/architecture_design.txt": "AgentCore Enterprise Gateway Architecture:\n- Protocol: Model Context Protocol (MCP)\n- Auth: Custom OAuth2 / JWT (RS256 via Netlify JWKS)\n- Authorization: AWS Bedrock Cedar Policy Engine\n- Data Plane: Render Cloud API + AWS S3 (usefulbi-ma-insights-data) + Neon PostgreSQL",
    "hr/employee_salaries.csv": "emp_id,name,department,salary\nE101,Alice Smith,Finance,125000\nE102,Bob Johnson,Engineering,155000\nE103,Carol White,Human Resources,110000"
}

print(f"Uploading files to real S3 bucket: s3://{bucket}/ ...")
for key, content in files.items():
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType="text/csv" if key.endswith(".csv") else "text/plain"
    )
    print(f"Uploaded: s3://{bucket}/{key}")

print("All real S3 files uploaded successfully!")
