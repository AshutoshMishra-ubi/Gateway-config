import boto3

s3 = boto3.client('s3', region_name='us-east-1')
buckets = [
    'agentcore-poc-chat-artifacts-025066239748',
    'agentcore-test-genai',
    'agentfieldtest',
    'ai-platform-workspace-bucket',
    'ai-pltfm-dev-audit-test-275522615986'
]

for b in buckets:
    try:
        s3.put_object(Bucket=b, Key="test_probe.txt", Body=b"test")
        print(f"SUCCESS on bucket: {b}")
        s3.delete_object(Bucket=b, Key="test_probe.txt")
    except Exception as e:
        print(f"FAILED on bucket {b}: {e}")
