import requests
import json

def verify_apis():
    base_url = "http://localhost:8000"
    print("=" * 60)
    print("CarbonLedger API Endpoint Integration Verification")
    print("=" * 60)
    
    # 1. Check compliance endpoints
    print("\n1. Calling GET /api/v1/compliance/sec...")
    headers = {"Authorization": "Bearer tenant_enterprise:Sustainability Manager"}
    r1 = requests.get(f"{base_url}/api/v1/compliance/sec", headers=headers)
    print("Status Code:", r1.status_code)
    print("Response JSON:\n", json.dumps(r1.json(), indent=2))
    
    print("\n2. Calling GET /api/v1/compliance/csrd...")
    r2 = requests.get(f"{base_url}/api/v1/compliance/csrd", headers=headers)
    print("Status Code:", r2.status_code)
    print("Response JSON:\n", json.dumps(r2.json(), indent=2))
    
    # 2. Check MCP Tool listing
    print("\n3. Calling GET /api/v1/mcp/tools...")
    r3 = requests.get(f"{base_url}/api/v1/mcp/tools")
    print("Status Code:", r3.status_code)
    print("Response JSON:\n", json.dumps(r3.json(), indent=2))
    
    # 3. Check Chat assistant
    print("\n4. Calling POST /api/v1/chat...")
    payload = {"query": "Explain direct emissions", "tenant_id": "tenant_enterprise"}
    r4 = requests.post(f"{base_url}/api/v1/chat", json=payload)
    print("Status Code:", r4.status_code)
    print("Response JSON:\n", json.dumps(r4.json(), indent=2))
    print("=" * 60)

if __name__ == "__main__":
    verify_apis()
