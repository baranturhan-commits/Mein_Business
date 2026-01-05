
import pandas as pd
import json
from pathlib import Path

# Config
MANDANT_ID = "Elektroniker_Testbetrieb"
MANDANTEN_DIR = Path(r"c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")
LIEFERSCHEINE_DIR = MANDANTEN_DIR / MANDANT_ID / 'Lieferscheine'
XLSX_PATH = LIEFERSCHEINE_DIR / 'lieferscheine.xlsx'

print(f"📂 Reading {XLSX_PATH}")

if XLSX_PATH.exists():
    df = pd.read_excel(XLSX_PATH, sheet_name='Lieferscheine')
    # Print all columns and rows
    print(df.to_string())
    
    # Also print as list of dicts for clearer value inspection
    print("\n--- JSON Dump ---")
    print(json.dumps(df.to_dict(orient='records'), default=str, indent=2))
else:
    print("❌ File not found.")
