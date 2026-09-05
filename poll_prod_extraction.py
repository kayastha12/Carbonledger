import requests
import time

PROD_URL = 'https://carbonledger-api-8bl2.onrender.com'
login_res = requests.post(f'{PROD_URL}/api/v1/auth/login', json={'email': 'admin@carbonledger.io', 'password': 'Admin@12345'})
token = login_res.json().get('token')
headers = {'Authorization': f'Bearer {token}'}

pdf_path = r'D:\internship\deepseek_html_20260731_54ad15 (1).pdf'

for attempt in range(20):
    t_str = time.strftime('%H:%M:%S')
    print(f"[{t_str}] Attempt {attempt+1}...", flush=True)
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('deepseek_html_20260731_54ad15 (1).pdf', f, 'application/pdf')}
            upload_res = requests.post(f'{PROD_URL}/api/upload/universal', files=files, headers=headers, timeout=60)
        
        if upload_res.status_code == 200:
            data = upload_res.json()
            rec_count = len(data.get('records', []))
            print(f"   Upload Status 200 | Records: {rec_count}", flush=True)
            if rec_count > 0:
                print("   >>> SUCCESS! Extracted real records from live production:", flush=True)
                for r in data['records']:
                    mat = r.get('material')
                    qty = r.get('quantity')
                    unit = r.get('unit')
                    scope = r.get('scope')
                    ready = r.get('carbon_calculation', {}).get('calculation_ready')
                    print(f"      - {mat} | {qty} {unit} | Scope: {scope} | Ready: {ready}", flush=True)
                
                # Now test Approval & Calculation on live production
                print("\n   >>> Testing Approval & Calculate on live production...", flush=True)
                approve_payload = {'upload_id': data['upload_id'], 'records': data['records']}
                app_res = requests.post(f'{PROD_URL}/api/upload/approve', json=approve_payload, headers=headers, timeout=60)
                print(f"   Approval Status: {app_res.status_code}", flush=True)
                if app_res.status_code == 200:
                    app_data = app_res.json()
                    summary = app_data.get('summary', {})
                    print("   >>> Approval summary:", summary, flush=True)
                    print("   >>> Generated reports map:", app_data.get('reports'), flush=True)
                else:
                    print("   Approval Error:", app_res.text[:200], flush=True)
                break
            else:
                logs = data.get('parser_response', {}).get('logs', [])
                print("   Logs:", logs[-1] if logs else 'None', flush=True)
        else:
            print(f"   HTTP {upload_res.status_code}", flush=True)
    except Exception as e:
        print(f"   Exception: {e}", flush=True)
    time.sleep(10)
