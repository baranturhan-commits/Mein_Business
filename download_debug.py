
import requests
import os

url = "http://localhost:5000/api/pdf/Mandanten/Elektroniker_Testbetrieb/Lieferscheine/Lieferschein_PROT-2026-001_1767560752.pdf"
save_path = "downloaded_debug.pdf"

print(f"📥 Downloading {url}...")

try:
    res = requests.get(url, stream=True)
    print(f"Status: {res.status_code}")
    print(f"Headers: {res.headers}")
    
    with open(save_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192): 
            f.write(chunk)
            
    size = os.path.getsize(save_path)
    print(f"💾 Saved {size} bytes.")
    
    if size < 500:
        print("⚠️ File too small! Dumping content:")
        with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read())
            
    with open(save_path, 'rb') as f:
        print(f"Start: {f.read(20)}")
        
except Exception as e:
    print(f"❌ Error: {e}")
