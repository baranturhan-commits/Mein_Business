"""
Umbenennung existierender Angebote und Protokolle
Neues Format: [TYP]-[MandantenNr]-[Jahr]-[Counter]
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent
MANDANTEN_DIR = BACKEND_DIR / 'Mandanten'

def get_mandant_nummer(mandant_path):
    """Liest Mandantennummer aus Config"""
    config_file = mandant_path / 'mandant_config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                return cfg.get('mandantennummer', '000')
        except:
            pass
    return '000'

def extract_year_from_filename(filename):
    """Versucht Jahr aus Dateiname zu extrahieren"""
    # Pattern: 2025, 2026, etc.
    match = re.search(r'(202[4-9])', filename)
    if match:
        return match.group(1)
    return str(datetime.now().year)

def rename_files_in_folder(folder_path, prefix, mandanten_nr):
    """Benennt alle PDFs in einem Ordner um"""
    if not folder_path.exists():
        print(f"  Ordner nicht gefunden: {folder_path}")
        return 0
    
    renamed = 0
    counter = 1
    
    # Sortiere nach Änderungsdatum (älteste zuerst)
    pdf_files = sorted(folder_path.glob('*.pdf'), key=lambda p: p.stat().st_mtime)
    
    for pdf_file in pdf_files:
        old_name = pdf_file.name
        
        # Prüfe ob bereits im neuen Format
        new_pattern = re.compile(rf'^{prefix}-\d+-\d{{4}}-\d{{3}}\.pdf$')
        if new_pattern.match(old_name):
            print(f"  Bereits OK: {old_name}")
            # Extract counter to continue from there
            match = re.search(r'-(\d{3})\.pdf$', old_name)
            if match:
                counter = max(counter, int(match.group(1)) + 1)
            continue
        
        # Extrahiere Jahr aus altem Namen
        year = extract_year_from_filename(old_name)
        
        # Neuer Name
        new_name = f"{prefix}-{mandanten_nr}-{year}-{counter:03d}.pdf"
        new_path = folder_path / new_name
        
        # Verhindere Überschreiben
        while new_path.exists():
            counter += 1
            new_name = f"{prefix}-{mandanten_nr}-{year}-{counter:03d}.pdf"
            new_path = folder_path / new_name
        
        try:
            pdf_file.rename(new_path)
            print(f"  ✅ {old_name} → {new_name}")
            renamed += 1
            counter += 1
        except Exception as e:
            print(f"  ❌ Fehler bei {old_name}: {e}")
    
    return renamed

def main():
    print("=" * 50)
    print("📂 Umbenennung bestehender Dokumente")
    print("=" * 50)
    
    total_renamed = 0
    
    for mandant_dir in MANDANTEN_DIR.iterdir():
        if not mandant_dir.is_dir():
            continue
        
        print(f"\n🏢 Mandant: {mandant_dir.name}")
        mandanten_nr = get_mandant_nummer(mandant_dir)
        print(f"   Mandantennummer: {mandanten_nr}")
        
        # Angebote umbenennen
        angebote_dir = mandant_dir / 'Angebote'
        print(f"\n   📝 Angebote:")
        renamed = rename_files_in_folder(angebote_dir, 'ANG', mandanten_nr)
        total_renamed += renamed
        
        # Lieferscheine/Protokolle umbenennen
        lieferscheine_dir = mandant_dir / 'Lieferscheine'
        print(f"\n   📋 Lieferscheine/Protokolle:")
        renamed = rename_files_in_folder(lieferscheine_dir, 'LS', mandanten_nr)
        total_renamed += renamed
    
    print("\n" + "=" * 50)
    print(f"✅ Fertig! {total_renamed} Dateien umbenannt.")
    print("=" * 50)

if __name__ == '__main__':
    main()
