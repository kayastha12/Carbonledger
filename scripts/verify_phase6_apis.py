import requests
import json

def verify_phase6():
    base_url = "http://localhost:8000"
    print("=" * 60)
    print("CarbonLedger Phase 6 API Endpoint Verification")
    print("=" * 60)
    
    # 1. Digital Twin
    print("\n1. Calling GET /api/v1/twin...")
    r1 = requests.get(f"{base_url}/api/v1/twin")
    print("Status Code:", r1.status_code)
    print("Response JSON:\n", json.dumps(r1.json(), indent=2))
    
    # 2. What-If Simulation
    print("\n2. Calling POST /api/v1/what-if...")
    payload_whatif = {"strategy": "rail_freight"}
    r2 = requests.post(f"{base_url}/api/v1/what-if", json=payload_whatif)
    print("Status Code:", r2.status_code)
    print("Response JSON:\n", json.dumps(r2.json(), indent=2))
    
    # 3. Compliance Validation Checklist Audit
    print("\n3. Calling POST /api/v1/compliance/audit...")
    payload_comp = {
        "framework": "SEC",
        "metrics": {
            "scope_1_direct": 5000.0,
            "scope_2_indirect": 12000.0,
            "governance_oversight": "Board oversight committee active"
        }
    }
    r3 = requests.post(f"{base_url}/api/v1/compliance/audit", json=payload_comp)
    print("Status Code:", r3.status_code)
    print("Response JSON:\n", json.dumps(r3.json(), indent=2))
    print("=" * 60)

if __name__ == "__main__":
    verify_phase6()
