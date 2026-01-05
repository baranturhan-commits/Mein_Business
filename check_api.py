
import requests
import json

url = "http://localhost:5000/api/mandanten/Elektroniker_Testbetrieb/lieferscheine"
try:
    print(f"📡 Fetching {url}...")
    res = requests.get(url)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        items = data.get('lieferscheine', [])
        print(f"✅ Received {len(items)} items.")
        print(json.dumps(items, indent=2))
    else:
        print("❌ Error response")
        print(res.text)
except Exception as e:
    print(f"❌ Failed to connect: {e}")
