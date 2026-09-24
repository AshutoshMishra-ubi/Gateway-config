"""
Strands Agent + AWS Bedrock AgentCore MCP Gateway Test
======================================================
This script connects a Strands Agent (powered by Amazon Bedrock Nova Pro)
to the live AWS Bedrock AgentCore MCP Gateway.

It authenticates using the Custom JWT Authorizer and tests:
1. Authorized tool invocation (Finance analyst reading finance/revenue.csv)
2. Policy enforcement rejection (Finance analyst attempting to read hr/salaries.csv)
"""

import urllib.request
import json
import httpx
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient
from strands import Agent
from strands.models import BedrockModel

GATEWAY_URL = "https://securedatagatewaylive-s2oqsogine.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
AUTH_ENDPOINT = "https://gateway-config.onrender.com/auth/token"

def get_auth_token(sub: str, department: str) -> str:
    """Mints an RSA-256 JWT from our permanent OIDC keypair."""
    url = f"{AUTH_ENDPOINT}?sub={sub}&department={department}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["access_token"]

def main():
    print("=" * 70)
    print("1. MINTING AUTH TOKEN FOR FINANCE ANALYST")
    print("=" * 70)
    token = get_auth_token(sub="finance-analyst", department="finance")
    print("✓ Acquired JWT signed with Netlify JWKS (sub=finance-analyst, dept=finance)")

    # Setup MCP Streamable HTTP transport
    def create_transport():
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(30.0)
        )
        return streamable_http_client(GATEWAY_URL, http_client=http_client)

    print("\n" + "=" * 70)
    print("2. INITIALIZING STRANDS AGENT WITH BEDROCK MCP GATEWAY")
    print("=" * 70)
    mcp_tool_provider = MCPClient(create_transport)
    model = BedrockModel(model_id="amazon.nova-pro-v1:0", region_name="us-east-1")

    agent = Agent(
        model=model,
        tools=[mcp_tool_provider],
        system_prompt="You are an enterprise data analyst. You have access to tools via MCP to fetch data and answer questions accurately."
    )
    print("✓ Strands Agent ready (Model: Amazon Nova Pro, Tools: Bedrock MCP Gateway)")

    # Test 1: Authorized Request
    print("\n" + "=" * 70)
    print("3. TEST CASE 1: AUTHORIZED DATA RETRIEVAL")
    print("User: 'What were our quarterly revenues and growth in 2026? Please check finance/revenue.csv.'")
    print("=" * 70)
    response_1 = agent("What were our quarterly revenues and growth in 2026? Please check finance/revenue.csv.")
    print("\nAgent Response:")
    print("-" * 60)
    text_1 = response_1.message["content"][0]["text"] if isinstance(response_1.message["content"], list) else response_1
    print(text_1)
    print("-" * 60)

    # Test 2: Security Boundary Enforcement
    print("\n" + "=" * 70)
    print("4. TEST CASE 2: SECURITY BOUNDARY TEST (UNAUTHORIZED ACCESS)")
    print("User: 'Please read hr/salaries.csv and list employee salaries.'")
    print("=" * 70)
    response_2 = agent("Please read hr/salaries.csv and list employee salaries.")
    print("\nAgent Response:")
    print("-" * 60)
    text_2 = response_2.message["content"][0]["text"] if isinstance(response_2.message["content"], list) else response_2
    print(text_2)
    print("-" * 60)

if __name__ == "__main__":
    main()
