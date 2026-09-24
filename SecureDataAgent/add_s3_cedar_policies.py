import boto3
import time

client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
engine_id = 'DataAccessPolicyEngine-if8r3u62or'
gw_arn = "arn:aws:bedrock-agentcore:us-east-1:025066239748:gateway/securedatagatewaylive-s2oqsogine"

policies = [
    {
        "name": "EngineeringDataPolicy",
        "description": "Permit engineering users to read engineering S3 files",
        "statement": f"""permit (
    principal is AgentCore::OAuthUser,
    action == AgentCore::Action::"DataApiTarget___read_file",
    resource == AgentCore::Gateway::"{gw_arn}"
)
when {{
    principal.id like "engineering-*" &&
    context.input.key like "engineering/*"
}};"""
    },
    {
        "name": "EngineeringListPolicy",
        "description": "Permit engineering users to list files in S3",
        "statement": f"""permit (
    principal is AgentCore::OAuthUser,
    action == AgentCore::Action::"DataApiTarget___list_files",
    resource == AgentCore::Gateway::"{gw_arn}"
)
when {{
    principal.id like "engineering-*"
}};"""
    },
    {
        "name": "FinanceListPolicy",
        "description": "Permit finance users to list files in S3",
        "statement": f"""permit (
    principal is AgentCore::OAuthUser,
    action == AgentCore::Action::"DataApiTarget___list_files",
    resource == AgentCore::Gateway::"{gw_arn}"
)
when {{
    principal.id like "finance-*"
}};"""
    }
]

existing = {p['name']: p['policyId'] for p in client.list_policies(policyEngineId=engine_id)['policies']}

for p in policies:
    if p['name'] not in existing:
        resp = client.create_policy(
            policyEngineId=engine_id,
            name=p['name'],
            description=p['description'],
            definition={'cedar': {'statement': p['statement']}}
        )
        print(f"Created {p['name']}: {resp['policyId']}")
    else:
        print(f"Policy {p['name']} already exists.")

print("Waiting 6 seconds for policy engine validation...")
time.sleep(6)

for p in client.list_policies(policyEngineId=engine_id)['policies']:
    print(f"Policy: {p['name']:32} -> Status: {p['status']}")
