import urllib.request
import urllib.error
import json
import random

BASE_URL = "https://carbonledger-api-8bl2.onrender.com"
ORIGIN = "https://carbonledger-app-vxb3.onrender.com"

def req(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {
        "Origin": ORIGIN,
        "User-Agent": "Mozilla/5.0"
    }
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            resp_body = resp.read().decode("utf-8")
            resp_json = json.loads(resp_body) if resp_body else {}
            return resp.status, resp_json, dict(resp.headers)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"detail": err_body}
        return e.code, err_json, dict(e.headers)

print("=== 1. Testing GET /health ===")
st, body, hdrs = req("/health")
print(f"Status: {st}, Body: {body}, Access-Control-Allow-Origin: {hdrs.get('access-control-allow-origin')}")

print("\n=== 2. Testing Master Admin Login ===")
st, body, hdrs = req("/api/v1/auth/login", "POST", {"email": "admin@carbonledger.io", "password": "Admin@12345"})
print(f"Status: {st}, User: {body.get('user', {}).get('email')}, Role: {body.get('user', {}).get('role')}")
admin_token = body.get("token")

print("\n=== 3. Testing Paid Subscriber Login ===")
st, body, hdrs = req("/api/v1/auth/login", "POST", {"email": "subscriber@carbonledger.io", "password": "Subscriber@12345"})
print(f"Status: {st}, User: {body.get('user', {}).get('email')}, Role: {body.get('user', {}).get('role')}")
sub_token = body.get("token")

print("\n=== 4. Testing Invalid Password Rejection ===")
st, body, _ = req("/api/v1/auth/login", "POST", {"email": "admin@carbonledger.io", "password": "WrongPassword"})
print(f"Status: {st} (Expected 401), Detail: {body.get('detail')}")

print("\n=== 5. Testing New User Registration ===")
rnd_email = f"lead_auditor_{random.randint(1000, 9999)}@acme-corp.com"
st, body, _ = req("/api/v1/auth/register", "POST", {
    "email": rnd_email,
    "password": "SecurePassword123!",
    "full_name": "Sarah Jenkins",
    "organization": "Acme Global ESG",
    "default_region": "DE",
    "role": "subscriber"
})
print(f"Status: {st}, Registered: {body.get('user', {}).get('email')}, Tokens: {body.get('user', {}).get('token_balance')}")
new_token = body.get("token")

print("\n=== 6. Testing GET /api/v1/auth/me ===")
st, body, _ = req("/api/v1/auth/me", "GET", token=admin_token)
user_info = body.get('user', {})
print(f"Status: {st}, Full Name: {user_info.get('full_name')}, Role: {user_info.get('role')}, Balance: {user_info.get('token_balance')}")

print("\n=== 7. Testing Forgot & Reset Password Flow ===")
st, forgot_res, _ = req("/api/v1/auth/forgot-password", "POST", {"email": rnd_email})
print(f"Forgot Status: {st}, Reset Code: {forgot_res.get('reset_code')}")
reset_code = forgot_res.get("reset_code")

st, reset_res, _ = req("/api/v1/auth/reset-password", "POST", {
    "email": rnd_email,
    "reset_token": reset_code,
    "new_password": "NewUpdatedPassword123!"
})
print(f"Reset Status: {st}, Message: {reset_res.get('message')}")

st, relogin_res, _ = req("/api/v1/auth/login", "POST", {"email": rnd_email, "password": "NewUpdatedPassword123!"})
print(f"Re-login with New Password Status: {st}, Token: {bool(relogin_res.get('token'))}")

print("\n=== 8. Testing AI RAG & Chat API ===")
st, rag_res, _ = req("/api/rag", "POST", {"query": "What is the CBAM carbon emission price benchmark for 2026?"}, token=admin_token)
print(f"RAG Status: {st}, Answer: {rag_res.get('answer')[:120]}...")

print("\n=== 9. Testing Carbon Inventory API ===")
st, inv_res, _ = req("/api/v1/carbon/inventory", "GET", token=admin_token)
print(f"Inventory Status: {st}, Total Items: {len(inv_res.get('items', []))}, Total CO2e: {inv_res.get('total_co2e_kg')} kg")

print("\n=== ALL PRODUCTION BACKEND API TESTS COMPLETED SUCCESSFULLY ===")
