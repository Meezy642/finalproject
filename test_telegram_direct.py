import urllib.request
import urllib.error
import json

token = "8797666810:AAFNxpfrEAzVrUVTSYc8cGOwChHRc56AesU"
ids_to_try = ["136656884", "-136656884", "-100136656884"]

for cid in ids_to_try:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": f"<b>🔔 Diagnostic notification!</b>\nTesting Chat ID: {cid}",
        "parse_mode": "HTML"
    }
    print(f"Testing chat_id: {cid}...")
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"  --> SUCCESS: {res_data}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"  --> HTTP error {e.code}: {error_body}")
    except Exception as e:
        print(f"  --> Other error: {e}")
