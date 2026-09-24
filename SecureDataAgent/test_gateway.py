"""
End-to-End Test for AgentCore Gateway + Custom JWT + Cedar Policies
Tests both an authorized (finance -> finance/*) and unauthorized (hr -> finance/*) call.
"""

import requests
import json
import sys

import os

# Production Render API and Live AWS Bedrock MCP Gateway
API_BASE_URL = "https://gateway-config.onrender.com"
GATEWAY_URL = os.getenv(
    "BEDROCK_GATEWAY_URL",
    "https://securedatagatewaylive-s2oqsogine.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)

def get_token(department: str, username: str = "test-user") -> str:
    """Mint a signed JWT from our local auth endpoint with the specified department."""
    url = f"{API_BASE_URL}/auth/token?department={department}&sub={username}"
    res = requests.post(url)
    if res.status_code != 200:
        print(f"[-] Failed to get token: {res.text}")
        sys.exit(1)
    return res.json()["access_token"]

def test_mcp_call(token: str, tool_name: str, arguments: dict, test_label: str):
    print(f"\n==================================================")
    print(f"RUNNING: {test_label}")
    print(f"Tool: {tool_name} | Args: {arguments}")
    print(f"==================================================")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Standard MCP tools/call payload
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        res = requests.post(f"{GATEWAY_URL}", headers=headers, json=payload, timeout=30)
        print(f"Gateway HTTP Status: {res.status_code}")
        try:
            print("Response Body:\n" + json.dumps(res.json(), indent=2))
        except Exception:
            print(f"Raw Response: {res.text}")
    except requests.exceptions.Timeout:
        print(f"[-] Gateway request timed out after 30s.")
    except requests.exceptions.ConnectionError:
        print(f"[-] Could not connect to Gateway at {GATEWAY_URL}.")
        print("    Check the port in your 'agentcore dev' terminal output.")

if __name__ == "__main__":
    print("--- 1. Testing Finance User -> Finance Data (EXPECTED: ALLOW) ---")
    finance_token = get_token("finance", "finance-alice")
    test_mcp_call(
        token=finance_token,
        tool_name="DataApiTarget___read_file",
        arguments={"key": "finance/q3_revenue.csv"},
        test_label="Finance user reading finance/q3_revenue.csv"
    )

    print("\n--- 2. Testing HR User -> Finance Data (EXPECTED: DENY) ---")
    hr_token = get_token("hr", "hr-bob")
    test_mcp_call(
        token=hr_token,
        tool_name="DataApiTarget___read_file",
        arguments={"key": "finance/q3_revenue.csv"},
        test_label="HR user trying to read finance/q3_revenue.csv"
    )
