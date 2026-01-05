
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# Config
MANDANT_ID = "Elektroniker_Testbetrieb"
MANDANTEN_DIR = Path(r"c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")
LIEFERSCHEINE_DIR = MANDANTEN_DIR / MANDANT_ID / 'Lieferscheine'
XLSX_PATH = LIEFERSCHEINE_DIR / 'lieferscheine.xlsx'

# Ensure dir
LIEFERSCHEINE_DIR.mkdir(parents=True, exist_ok=True)

# Dummy Data
nummer = "PROT-2026-999"
pdf_filename = f"{nummer}.pdf"
pdf_path_full = LIEFERSCHEINE_DIR / pdf_filename

# 1. Create Dummy PDF if not exists
if not pdf_path_full.exists():
    with open(pdf_path_full, "wb") as f:
        f.write(b"%PDF-1.4 header dummy") # Minimal dummy
    print(f"📄 Created dummy PDF: {pdf_filename}")

# 2. Add to Excel
items = [
    {'text': 'Wartung durchgeführt', 'menge': 1},
    {'text': 'Dichtungen erneuert', 'menge': 3}
]

new_row = {
    'Lieferscheinnummer': nummer,
    'Datum': datetime.now().strftime("%d.%m.%Y"), # Today 2026
    'Kunde': 'Testkunde 2026',
    'Angebot': 'ANG-2026-001',
    'Items': json.dumps(items),
    'PDF_Path': f"Mandanten/{MANDANT_ID}/Lieferscheine/{pdf_filename}",
    'Status': 'Offen'
}

# Load or Create
if XLSX_PATH.exists():
    df = pd.read_excel(XLSX_PATH, sheet_name='Lieferscheine')
    # Check if exists
    if nummer in df['Lieferscheinnummer'].astype(str).values:
        print("⚠️ Entry already exists. Skipping excel append.")
    else:
        new_df = pd.DataFrame([new_row])
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_excel(XLSX_PATH, sheet_name='Lieferscheine', index=False)
        print("✅ Added new row to Excel.")
else:
    df = pd.DataFrame([new_row])
    df.to_excel(XLSX_PATH, sheet_name='Lieferscheine', index=False)
    print("✅ Created new Excel with row.")

print("Done.")
