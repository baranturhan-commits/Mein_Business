
import requests

# The long filename that corresponds to the "filled" protocol
# Path from check_api.py output
url = "http://localhost:5000/api/pdf/Mandanten/Elektroniker_Testbetrieb/Lieferscheine/Lieferschein_PROT-2026-001_1767560752.pdf"

print(f"📡 Requesting {url}...")
try:
    res = requests.get(url)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        print("✅ PDF found! (Size:", len(res.content), "bytes)")
    else:
        print("❌ Failed.")
        print("Response:", res.text[:200])
except Exception as e:
    print(f"❌ Error: {e}")
