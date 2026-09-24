import boto3
import json

client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
gateway_id = 'securedatagatewaylive-s2oqsogine'

with open(r'c:\Users\Admin\Gateway-config\SecureDataAgent\api\openapi.json', 'r') as f:
    openapi_content = f.read()

targets = client.list_gateway_targets(gatewayIdentifier=gateway_id)['items']
data_target = next(t for t in targets if t['name'] == 'DataApiTarget')
target_id = data_target['targetId']

print(f"Updating gateway target {target_id} with new openapi.json...")
resp = client.update_gateway_target(
    gatewayIdentifier=gateway_id,
    targetId=target_id,
    name='DataApiTarget',
    description='Enterprise Data Service on Render with live S3 and Postgres',
    targetConfiguration={
        'mcp': {
            'openApiSchema': {
                'inlinePayload': openapi_content
            }
        }
    }
)
print("SUCCESS updating target!")
print(f"Status: {resp['status']}")
