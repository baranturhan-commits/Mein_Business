
from pathlib import Path

MANDANT_ID = "Elektroniker_Testbetrieb"
MANDANTEN_DIR = Path(r"c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")
LIEFERSCHEINE_DIR = MANDANTEN_DIR / MANDANT_ID / 'Lieferscheine'

files_to_check = [
    "Lieferschein_PROT-2026-001_1767560752.pdf",
    "PROT-2026-999.pdf"
]

for fname in files_to_check:
    fpath = LIEFERSCHEINE_DIR / fname
    print(f"\n📄 Checking {fname}...")
    if fpath.exists():
        try:
            with open(fpath, 'rb') as f:
                header = f.read(5)
                print(f"   Header: {header}")
                if header.startswith(b'%PDF-'):
                    print("   ✅ Valid PDF Signature")
                else:
                    print("   ❌ Invalid PDF Signature")
        except Exception as e:
            print(f"   ❌ Error reading: {e}")
    else:
        print("   ❌ File not found")
