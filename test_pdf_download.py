
import requests

# Try to fetch the PDF that we know exists (from debug output)
# Path: /api/pdf/Mandanten/Elektroniker_Testbetrieb/Lieferscheine/PROT-2026-999.pdf
url = "http://localhost:5000/api/pdf/Mandanten/Elektroniker_Testbetrieb/Lieferscheine/PROT-2026-999.pdf"

print(f"📡 Requesting {url}...")
try:
    res = requests.get(url)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        print("✅ PDF found! (Header: ", res.headers.get('content-type'), ")")
    else:
        print("❌ Failed.")
        print("Response:", res.text[:200])
except Exception as e:
    print(f"❌ Error: {e}")
