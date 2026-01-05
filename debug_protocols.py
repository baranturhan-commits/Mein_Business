
import sys
import os
import json
# Add backend to path
sys.path.append(os.path.abspath("backend"))

from api_server import get_lieferscheine, app
import pandas as pd
from pathlib import Path

MANDANT_ID = "Elektroniker_Testbetrieb"
MANDANTEN_DIR = Path(r"c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")
file_path = MANDANTEN_DIR / MANDANT_ID / 'Lieferscheine' / 'lieferscheine.xlsx'

print(f"📂 Checking {file_path}")

try:
    if not file_path.exists():
        print("❌ File does not exist!")
        sys.exit(1)

    df = pd.read_excel(file_path, sheet_name='Lieferscheine')
    print("✅ Excel loaded.")
    print(f"📊 Rows: {len(df)}")
    print("📋 Columns:", df.columns.tolist())
    
    data = df.to_dict(orient='records')
    normalized = []
    
    for row in data:
        item = {}
        for k, v in row.items():
            item[k.lower()] = v
        
        print(f"\n🔍 Processing Row: {item.get('lieferscheinnummer')}")
        
        # Path Check Logic from api_server.py
        path_val = item.get('pdf_path') or item.get('pdf path') or item.get('path') or item.get('dateipfad')
        print(f"   path_val raw: {path_val}")
        
        if not path_val:
            nummer = item.get('lieferscheinnummer') or item.get('nummer')
            if nummer:
                path_val = f"{nummer}.pdf"
                print(f"   path_val constructed: {path_val}")

        if path_val:
             fname = str(path_val).strip()
             lieferscheine_dir = MANDANTEN_DIR / MANDANT_ID / 'Lieferscheine'
             # Handle relative paths if present in excel
             if "Mandanten" in fname:
                 fname = os.path.basename(fname)
                 
             full_path = lieferscheine_dir / fname
             
             exists = full_path.exists()
             print(f"   Full Path: {full_path}")
             print(f"   Exists: {exists}")
             
             if not exists:
                 # Check fallback logic
                 if not fname.lower().endswith('.pdf'):
                     test_path = lieferscheine_dir / f"{fname}.pdf"
                     if test_path.exists():
                         print("   Restored via .pdf extension")
                         exists = True
                     else:
                         print("   ❌ File really missing")
            
             if exists:
                 normalized.append(item)
        else:
            print("   ❌ No Path Value found")

    print(f"\n🏁 Result: {len(normalized)} items would be returned.")

except Exception as e:
    print(f"❌ Error: {e}")
