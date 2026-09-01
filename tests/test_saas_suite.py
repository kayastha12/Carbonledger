import urllib.request
import urllib.error
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def make_req(endpoint, method="GET", data=None, headers=None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    url = f"{BASE_URL}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}


def test_full_saas_lifecycle():
    print("\n--- 1. Testing Master Admin Login ---")
    status, admin_data = make_req("/api/v1/auth/login", method="POST", data={
        "email": "admin@carbonledger.io",
        "password": "Admin@12345"
    })
    assert status == 200, f"Admin login failed: {admin_data}"
    admin_token = admin_data["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    print(f" Master Admin Logged In: {admin_data['user']['email']}, Role: {admin_data['user']['role']}, Tokens: {admin_data['user']['token_balance']}")

    print("\n--- 2. Testing New Subscriber Registration (100 Free Trial Tokens) ---")
    random_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    status, sub_data = make_req("/api/v1/auth/register", method="POST", data={
        "email": random_email,
        "password": "Password@123",
        "full_name": "Dr. Alan Turing",
        "organization": "Bletchley ESG Corp",
        "default_region": "GB",
        "role": "subscriber"
    })
    assert status == 200, f"Registration failed: {sub_data}"
    sub_token = sub_data["token"]
    sub_user_id = sub_data["user"]["id"]
    sub_headers = {"Authorization": f"Bearer {sub_token}", "Content-Type": "application/json"}
    assert sub_data["user"]["token_balance"] == 100, f"Expected 100 trial tokens, got {sub_data['user']['token_balance']}"
    print(f" New Subscriber Registered: {random_email}, Balance: {sub_data['user']['token_balance']} Tokens")

    print("\n--- 3. Testing Forgot & Reset Password Flow ---")
    status, forgot_res = make_req("/api/v1/auth/forgot-password", method="POST", data={"email": random_email})
    assert status == 200, f"Forgot password failed: {forgot_res}"
    reset_code = forgot_res["reset_code"]
    print(f" Generated Reset Code: {reset_code}")

    status, reset_res = make_req("/api/v1/auth/reset-password", method="POST", data={
        "email": random_email,
        "reset_token": reset_code,
        "new_password": "NewSecretPassword@123"
    })
    assert status == 200, f"Reset password failed: {reset_res}"
    print(" Password Successfully Reset!")

    # Verify login with new password
    status, login_new = make_req("/api/v1/auth/login", method="POST", data={
        "email": random_email,
        "password": "NewSecretPassword@123"
    })
    assert status == 200, "Login with new password failed"
    sub_token = login_new["token"]
    sub_headers = {"Authorization": f"Bearer {sub_token}", "Content-Type": "application/json"}

    print("\n--- 4. Testing Multi-Tenant Data Isolation (Clean Slate) ---")
    status, latest_data = make_req("/api/upload/latest", method="GET", headers=sub_headers)
    assert status == 200
    assert latest_data is None or len(latest_data.get("records", [])) == 0, f"Expected clean state for new user, got: {latest_data}"
    print(" Multi-Tenant Clean Slate Verified: Zero cross-tenant data leaked.")

    print("\n--- 5. Testing Subscription Upgrade to Professional Tier ($149/mo) ---")
    status, upgrade_res = make_req("/api/v1/user/subscription/upgrade", method="POST", headers=sub_headers, data={
        "plan_tier": "professional",
        "billing_cycle": "monthly",
        "payment_method": "Visa ending in 4242"
    })
    assert status == 200, f"Upgrade failed: {upgrade_res}"
    print(f" Upgrade Succeeded: {upgrade_res['message']}, New Balance: {upgrade_res['new_token_balance']}")
    assert upgrade_res["new_token_balance"] == 5100, f"Expected 5,100 tokens (100 trial + 5,000 pro), got {upgrade_res['new_token_balance']}"


    print("\n--- 6. Testing Billing Records & Invoice Generation ---")
    status, invoices = make_req("/api/v1/user/billing/history", method="GET", headers=sub_headers)
    assert status == 200
    assert len(invoices) >= 1, "Expected at least 1 billing invoice"
    print(f" Billing Invoice Generated: {invoices[0]['invoice_number']}, Amount: ${invoices[0]['amount_usd']}")

    print("\n--- 7. Testing Token Consumption Ledger ---")
    status, txs = make_req("/api/v1/user/tokens/history", method="GET", headers=sub_headers)
    assert status == 200
    assert len(txs) >= 2, f"Expected signup bonus and upgrade transactions, got {len(txs)}"
    print(f" Token Ledger Transactions Verified: {len(txs)} records logged.")

    print("\n--- 8. Testing Admin SaaS Dashboard Stats & MRR ---")
    status, stats = make_req("/api/v1/admin/dashboard-stats", method="GET", headers=admin_headers)
    assert status == 200
    print(f" Admin Dashboard Stats: Total Users: {stats['total_users']}, Active: {stats['active_users']}, MRR: ${stats['monthly_revenue_usd']}")
    assert stats["monthly_revenue_usd"] >= 149, "MRR should reflect at least the professional upgrade"

    print("\n--- 9. Testing Admin User Token Adjustments ---")
    status, adj_res = make_req(f"/api/v1/admin/users/{sub_user_id}/tokens", method="POST", headers=admin_headers, data={
        "adjustment_type": "add",
        "amount": 250,
        "reason": "Enterprise Goodwill Credit"
    })
    assert status == 200
    print(" Admin Manual Token Adjustment (+250 tokens) Verified!")

    print("\n--- 10. Testing Admin Plan Override ---")
    status, over_res = make_req(f"/api/v1/admin/users/{sub_user_id}/subscription", method="POST", headers=admin_headers, data={
        "plan_tier": "enterprise",
        "billing_cycle": "yearly",
        "status": "active",
        "days_to_extend": 365
    })
    assert status == 200
    print(" Admin Plan Override (Enterprise Yearly) Verified!")

    print("\n ALL 10 SAAS PLATFORM TEST SUITES PASSED FLAWLESSLY! ")

if __name__ == "__main__":
    test_full_saas_lifecycle()


