
import os
import json
import shutil
import re
import datetime
import pandas as pd
from pathlib import Path

# Config
BASE_DIR = Path(r"C:\Users\Admin\Desktop\Mein_Business\backend")
MANDANTEN_DIR = BASE_DIR / "Mandanten"

def load_mandant_config(mandant_path):
    config_file = mandant_path / "mandant_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def backup_file(file_path):
    if file_path.exists():
        timestamp = int(datetime.datetime.now().timestamp())
        backup_path = file_path.parent / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        print(f"📦 Backed up {file_path.name}")

def get_mandant_nr(config):
    return config.get('mandantennummer', '000')

def parse_date(date_val, file_mtime):
    # Try parsing date string or fallback to mtime
    if not date_val:
        return datetime.datetime.fromtimestamp(file_mtime)
    
    # Check for NaN/NaT
    if pd.isna(date_val): 
         return datetime.datetime.fromtimestamp(file_mtime)

    for fmt in ['%Y-%m-%d', '%d.%m.%Y']:
        try:
            return datetime.datetime.strptime(str(date_val), fmt)
        except: continue
    
    return datetime.datetime.fromtimestamp(file_mtime)

def migrate_offers(mandant_path, mandant_nr):
    print(f"\n--- Migrating Offers for {mandant_path.name} ---")
    angebote_dir = mandant_path / 'Angebote'
    excel_path = angebote_dir / 'angebote.xlsx'
    
    if not angebote_dir.exists(): return

    if excel_path.exists(): backup_file(excel_path)
    
    df = pd.DataFrame()
    if excel_path.exists():
        try:
            df = pd.read_excel(excel_path, sheet_name='Angebote')
        except: pass

    for pdf_file in angebote_dir.glob("*.pdf"):
        name = pdf_file.name
        
        # Checking regex for ALREADY CORRECT files
        # New Format: ANG-[Nr]-[YYYY]-[MM]-[NNN].pdf
        # MandantNr (3 digits), Year (4), Month (2), Counter (3)
        if re.match(r"^ANG-\d{3}-\d{4}-\d{2}-\d{3}\.pdf$", name):
            print(f"✅ Skipping {name} (Already migrated)")
            continue
            
        stat = pdf_file.stat()
        dt = datetime.datetime.fromtimestamp(stat.st_mtime)
        
        row_idx = None
        if not df.empty and 'PDF_Path' in df.columns:
            mask = df['PDF_Path'] == name
            if mask.any():
                row_idx = df.index[mask][0]
                dt = parse_date(df.at[row_idx, 'Datum'], stat.st_mtime)
        
        month_str = f"{dt.month:02d}"
        year_str = str(dt.year)
        
        counter = "001"
        # Extract counter from ANG-001-2026-005.pdf -> 005
        # Or Angebot_ANG-000-2025-001... -> 001
        m1 = re.search(r"ANG-\d+-(\d{4})-(\d{3})", name)
        if m1:
             counter = m1.group(2)
             # Use year from filename if present
             if m1.group(1): year_str = m1.group(1) 
        else:
             # Try simple digits at end of STEM
             stem = pdf_file.stem
             # Fallback: assume 001 if nothing found
             pass

        new_name = f"ANG-{mandant_nr}-{year_str}-{month_str}-{counter}.pdf"
        new_pdf_path = angebote_dir / new_name
        
        if new_pdf_path.exists() and new_pdf_path != pdf_file:
             print(f"Exists: {new_name}")
             continue
             
        try:
            pdf_file.rename(new_pdf_path)
            print(f"RENAME: {name} -> {new_name}")
            
            new_id = f"ANG-{mandant_nr}-{year_str}-{month_str}-{counter}"
            if row_idx is not None:
                if 'PDF_Path' in df.columns: df.at[row_idx, 'PDF_Path'] = new_name
                if 'Nummer' in df.columns: df.at[row_idx, 'Nummer'] = new_id
            
            # JSON update (simplified: rename matching json)
            # Find json with old ID. 
            # If name was "Angebot_ANG-001-2026-001...", ID was likely "ANG-..."
            # Let's just create a new JSON if needed or skip. 
            # Updating JSON is complex if we don't know the exact old ID.
            # But we can try finding `Angebot_ANG-001-2026-005.json` and rename it.
            # Construct OLD ID from filename match above
            
            old_id_guess = None
            if m1:
                 # Reconstruct: ANG-{nr}-{year}-{counter}
                 # But we don't know mandant nr in old filename 100%?
                 # Assuming it was in filename
                 pass
            
        except Exception as e:
            print(f"❌ Error renaming {name}: {e}")

    if not df.empty:
        df.to_excel(excel_path, sheet_name='Angebote', index=False)


def migrate_protocols(mandant_path, mandant_nr):
    print(f"\n--- Migrating Protocols for {mandant_path.name} ---")
    ls_dir = mandant_path / 'Lieferscheine'
    excel_path = ls_dir / 'lieferscheine.xlsx'
    if not ls_dir.exists(): return

    if excel_path.exists(): backup_file(excel_path)
    
    df = pd.DataFrame()
    if excel_path.exists():
        try:
            df = pd.read_excel(excel_path, sheet_name='Lieferscheine')
        except: pass

    for pdf_file in ls_dir.rglob("*.pdf"):
        if pdf_file.parent != ls_dir: continue 
        name = pdf_file.name
        
        # Check correct
        if re.match(r"^LS-\d{3}-\d{4}-\d{2}-\d{3}\.pdf$", name):
             print(f"Skipping {name}")
             continue

        stat = pdf_file.stat()
        dt = datetime.datetime.fromtimestamp(stat.st_mtime)
        year_str = str(dt.year)
        month_str = f"{dt.month:02d}"

        # Match logic: Try to find old ID in Excel
        # Filename: "Lieferschein_LS-2025-001_..."
        # ID: "LS-2025-001"
        
        old_id = None
        # Extract potential ID
        m = re.search(r"(LS-[0-9-]+)", name)
        if m: old_id = m.group(1)
        
        row_idx = None
        if not df.empty and old_id and 'Lieferscheinnummer' in df.columns:
            mask = df['Lieferscheinnummer'] == old_id
            if mask.any():
                row_idx = df.index[mask][0]
                dt = parse_date(df.at[row_idx, 'Datum'], stat.st_mtime)
                month_str = f"{dt.month:02d}"
                year_str = str(dt.year)
        
        # New Counter
        counter = "001"
        if old_id:
             m2 = re.search(r"-(\d{3})$", old_id) # End with 001
             if m2: counter = m2.group(1)

        new_name = f"LS-{mandant_nr}-{year_str}-{month_str}-{counter}.pdf"
        new_pdf_path = ls_dir / new_name

        if new_pdf_path.exists() and new_pdf_path != pdf_file:
             continue
        
        try:
            pdf_file.rename(new_pdf_path)
            print(f"RENAME: {name} -> {new_name}")
            
            new_id = f"LS-{mandant_nr}-{year_str}-{month_str}-{counter}"
            if row_idx is not None:
                if 'Lieferscheinnummer' in df.columns: 
                    df.at[row_idx, 'Lieferscheinnummer'] = new_id
                
        except Exception as e:
            print(f"Error: {e}")

    if not df.empty:
        df.to_excel(excel_path, sheet_name='Lieferscheine', index=False)

def migrate_invoices(mandant_path, mandant_nr):
    print(f"\n--- Migrating Invoices for {mandant_path.name} ---")
    rechnungen_base = mandant_path / 'Rechnungen'
    einnahmen_path = mandant_path / 'Einnahmen' / 'einnahmen.xlsx'
    
    if not rechnungen_base.exists(): return
    if einnahmen_path.exists(): backup_file(einnahmen_path)
    
    df = pd.DataFrame()
    if einnahmen_path.exists():
        try:
            df = pd.read_excel(einnahmen_path, sheet_name='Einnahmen')
        except: pass
        
    for pdf_file in rechnungen_base.rglob("*.pdf"):
        name = pdf_file.name
        
        if re.match(r"^RE-\d{3}-\d{4}-\d{2}-\d{3}\.pdf$", name):
             continue
             
        stat = pdf_file.stat()
        dt = datetime.datetime.fromtimestamp(stat.st_mtime)
        year_str = str(dt.year)
        month_str = f"{dt.month:02d}"
        
        # Search for ID in filename
        # e.g. "RE-000-2026-001.pdf" (from recent create_invoice tests?)
        # or "2026-001.pdf"
        
        counter = "001"
        match_id = None
        
        # Regex variants
        # 1. RE-000-2026-001
        m1 = re.search(r"RE-\d+-(\d{4})-(\d{3})", name)
        if m1:
             counter = m1.group(2)
             match_id = m1.group(0) # The whole ID
        else:
             # 2. 2026-001 (Old invoice generator format)
             m2 = re.search(r"(\d{4})-(\d{3})", name)
             if m2:
                 counter = m2.group(2)
                 match_id = m2.group(0) # YYYY-NNN

        row_idx = None
        if not df.empty and match_id and 'Rechnungsnummer' in df.columns:
             # Match substrings if needed
             mask = df['Rechnungsnummer'].astype(str).str.contains(match_id)
             if mask.any():
                  row_idx = df.index[mask][0]
                  dt = parse_date(df.at[row_idx, 'Datum'], stat.st_mtime)
                  month_str = f"{dt.month:02d}"
                  year_str = str(dt.year)

        new_name = f"RE-{mandant_nr}-{year_str}-{month_str}-{counter}.pdf"
        new_pdf_path = pdf_file.parent / new_name
        
        if new_pdf_path.exists() and new_pdf_path != pdf_file:
             continue
             
        try:
            pdf_file.rename(new_pdf_path)
            print(f"RENAME: {name} -> {new_name}")
            
            new_id = f"RE-{mandant_nr}-{year_str}-{month_str}-{counter}"
            
            if row_idx is not None:
                 df.at[row_idx, 'Rechnungsnummer'] = new_id

        except Exception as e:
            print(f"Error: {e}")
            
    if not df.empty:
        df.to_excel(einnahmen_path, sheet_name='Einnahmen', index=False)

def main():
    print("starting migration...")
    for mandant in MANDANTEN_DIR.iterdir():
        if mandant.is_dir():
            config = load_mandant_config(mandant)
            mandant_nr = get_mandant_nr(config)
            
            migrate_offers(mandant, mandant_nr)
            migrate_protocols(mandant, mandant_nr)
            migrate_invoices(mandant, mandant_nr)
    print("Done.")

if __name__ == "__main__":
    main()
