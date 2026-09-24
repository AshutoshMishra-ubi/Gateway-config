"""
Strands Agent + S3 Bedrock Gateway Live Test
============================================
Tests end-to-end Cedar policy enforcement and real S3 object retrieval:
1. Finance user reads finance/q3_revenue.csv -> PERMIT (Real S3 data returned)
2. Finance user tries to read engineering/architecture_design.txt -> DENIED by Cedar
3. Engineering user reads engineering/architecture_design.txt -> PERMIT (Real S3 data returned)
4. Engineering user tries to read finance/q3_revenue.csv -> DENIED by Cedar
"""

import urllib.request
import json
import httpx
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient
from strands import Agent

GATEWAY_MCP_URL = "https://securedatagatewaylive-s2oqsogine.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
AUTH_URL = "https://gateway-config.onrender.com/auth/token"

def get_token(sub: str, dept: str) -> str:
    url = f"{AUTH_URL}?sub={sub}&department={dept}&role=lead&audience=local-test-client"
    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data["access_token"]
    except Exception as e:
        # Fallback to direct local minting if local auth server is reloading
        from api.app.routers.auth import generate_token
        res = generate_token(department=dept, sub=sub, role="lead", audience="local-test-client")
        return res.access_token

def test_gateway_mcp_call(token: str, user_label: str, tool_name: str, arguments: dict):
    print(f"\n[{user_label}] Calling tool: {tool_name} with {arguments}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Send JSON-RPC call directly to Bedrock Gateway MCP endpoint
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(GATEWAY_MCP_URL, headers=headers, json=payload)
        status = resp.status_code
        data = resp.json()
        
        if "error" in data:
            err = data["error"]
            print(f" -> RESULT: GATEWAY / CEDAR DENIED ({err.get('message', err)})")
            return False, err
        elif "result" in data:
            content = data["result"].get("content", [])
            text = content[0].get("text", "") if content else ""
            print(f" -> RESULT: PERMITTED! Response:\n{text[:200]}")
            return True, text
        else:
            print(f" -> UNEXPECTED: {data}")
            return False, data

def main():
    print("=" * 70)
    print("S3 DATA LAKE + CEDAR POLICY ENFORCEMENT LIVE TEST")
    print("=" * 70)
    
    # 1. Mint tokens
    fin_token = get_token("finance-lead", "finance")
    eng_token = get_token("engineering-lead", "engineering")
    
    print("\nTokens acquired:")
    print(" - Finance Lead:     sub=finance-lead")
    print(" - Engineering Lead: sub=engineering-lead")
    
    # 2. Test 1: Finance user reads finance file (SHOULD PERMIT)
    print("\n" + "=" * 70)
    print("TEST 1: Finance Lead reads finance/q3_revenue.csv")
    print("Policy Expected: PERMIT (FinanceDataPolicy)")
    print("=" * 70)
    test_gateway_mcp_call(fin_token, "FINANCE LEAD", "DataApiTarget___read_file", {"key": "finance/q3_revenue.csv"})
    
    # 3. Test 2: Finance user attempts to read engineering file (SHOULD DENY)
    print("\n" + "=" * 70)
    print("TEST 2: Finance Lead attempts to read engineering/architecture_design.txt")
    print("Policy Expected: DENIED by Cedar (Context does not match finance/*)")
    print("=" * 70)
    test_gateway_mcp_call(fin_token, "FINANCE LEAD", "DataApiTarget___read_file", {"key": "engineering/architecture_design.txt"})
    
    # 4. Test 3: Engineering user reads engineering file (SHOULD PERMIT)
    print("\n" + "=" * 70)
    print("TEST 3: Engineering Lead reads engineering/architecture_design.txt")
    print("Policy Expected: PERMIT (EngineeringDataPolicy)")
    print("=" * 70)
    test_gateway_mcp_call(eng_token, "ENGINEERING LEAD", "DataApiTarget___read_file", {"key": "engineering/architecture_design.txt"})
    
    # 5. Test 4: Engineering user attempts to read finance file (SHOULD DENY)
    print("\n" + "=" * 70)
    print("TEST 4: Engineering Lead attempts to read finance/q3_revenue.csv")
    print("Policy Expected: DENIED by Cedar (Context does not match engineering/*)")
    print("=" * 70)
    test_gateway_mcp_call(eng_token, "ENGINEERING LEAD", "DataApiTarget___read_file", {"key": "finance/q3_revenue.csv"})

if __name__ == "__main__":
    main()
