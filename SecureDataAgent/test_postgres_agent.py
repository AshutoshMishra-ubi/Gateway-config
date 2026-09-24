"""
Strands Agent + PostgreSQL Gateway Integration Test
===================================================
Tests Strands Agent querying live PostgreSQL through the AWS Bedrock MCP Gateway:
1. Inspects tables via DataApiTarget___postgres_get_schema
2. Executes analytical SQL via DataApiTarget___postgres_execute_read_query
"""

import os
import urllib.request
import json
import httpx
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient
from strands import Agent
from strands.models import BedrockModel

GATEWAY_URL = os.getenv(
    "BEDROCK_GATEWAY_URL",
    "https://securedatagatewaylive-s2oqsogine.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)
AUTH_ENDPOINT = "https://gateway-config.onrender.com/auth/token"

def get_auth_token(sub: str, department: str) -> str:
    url = f"{AUTH_ENDPOINT}?sub={sub}&department={department}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["access_token"]

def main():
    print("=" * 70)
    print("1. MINTING AUTH TOKEN FOR ENGINEERING LEAD")
    print("=" * 70)
    token = get_auth_token(sub="engineering-lead", department="engineering")
    print("[OK] Token acquired (sub=engineering-lead, dept=engineering)")

    def create_transport():
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(30.0)
        )
        return streamable_http_client(GATEWAY_URL, http_client=http_client)

    print("\n" + "=" * 70)
    print("2. INITIALIZING STRANDS AGENT (AMAZON NOVA PRO + POSTGRES TOOLS)")
    print("=" * 70)
    mcp_provider = MCPClient(create_transport)
    model = BedrockModel(model_id="amazon.nova-pro-v1:0", region_name="us-east-1")

    agent = Agent(
        model=model,
        tools=[mcp_provider],
        system_prompt="""You are a database and infrastructure analyst.
You have access to PostgreSQL tools through the MCP Gateway:
- DataApiTarget___postgres_get_schema: to list database tables
- DataApiTarget___postgres_execute_read_query: to run SELECT queries

Table definitions:
- engineering.services: columns (id, service_name, tier, language, health_status, p99_latency_ms)
- engineering.deployments: columns (deployment_id, service_name, version, status, deployed_at)
- finance.quarterly_reports: columns (id, fiscal_year, quarter, revenue, net_profit, growth_rate)

When asked about database schemas or data, always use the tools to inspect and query the database accurately."""
    )
    print("[OK] Strands Agent ready with PostgreSQL tools.")

    # 1. Ask about schema
    print("\n" + "=" * 70)
    print("3. TEST CASE 1: INSPECT POSTGRESQL SCHEMA")
    print("User: 'What tables exist in the PostgreSQL database?'")
    print("=" * 70)
    resp_schema = agent("What tables exist in the PostgreSQL database?")
    text_schema = resp_schema.message["content"][0]["text"] if isinstance(resp_schema.message["content"], list) else resp_schema
    print("\nAgent Response:\n" + str(text_schema))

    # 2. Ask query
    print("\n" + "=" * 70)
    print("4. TEST CASE 2: EXECUTE ANALYTICAL QUERY")
    print("User: 'Check the engineering services table and tell me which services have p99 latency under 30ms.'")
    print("=" * 70)
    resp_query = agent("Check the engineering services table and tell me which services have p99 latency under 30ms.")
    text_query = resp_query.message["content"][0]["text"] if isinstance(resp_query.message["content"], list) else resp_query
    print("\nAgent Response:\n" + str(text_query))

if __name__ == "__main__":
    main()
