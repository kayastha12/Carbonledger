import urllib.request
import urllib.error
import json
import time

url = "https://carbonledger-api-8bl2.onrender.com/api/v1/auth/login"
data = json.dumps({"email": "admin@carbonledger.io", "password": "Admin@12345"}).encode("utf-8")
headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

for i in range(25):
    print(f"[{time.strftime('%H:%M:%S')}] Attempt {i+1} querying {url}...", flush=True)
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(">>> SUCCESS! HTTP Status:", resp.status, flush=True)
            body = resp.read().decode("utf-8")
            print(">>> Response Payload:", body, flush=True)
            break
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"    HTTP Error {e.code}: {e.reason} - {err_body[:100]}", flush=True)
    except Exception as e:
        print(f"    Connection Exception: {e}", flush=True)
    time.sleep(10)
