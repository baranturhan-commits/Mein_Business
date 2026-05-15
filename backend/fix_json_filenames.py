
import os
import json
import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")

def fix_jsons(mandant_path):
    print(f"\n--- Fixing JSONs for {mandant_path.name} ---")
    angebote_dir = mandant_path / 'Angebote'
    if not angebote_dir.exists(): return
    
    # 1. Map existing PDFs by (Year, Counter)
    pdf_map = {}
    for pdf in angebote_dir.glob("*.pdf"):
        # Expect ANG-001-YYYY-MM-NNN.pdf
        m = re.search(r"-(\d{4})-\d{2}-(\d{3})\.pdf", pdf.name)
        if m:
            key = (m.group(1), m.group(2)) # (Year, Counter)
            pdf_map[key] = pdf
    
    # 2. Iterate existing JSONs
    for json_file in angebote_dir.glob("*.json"):
        if "counter" in json_file.name: continue
        
        name = json_file.name
        # Match (Year, Counter) in JSON name
        # Format 1: Angebot_ANG-001-2026-005.json -> (2026, 005)
        # Format 2: Angebot_ANG-2026-001.json -> (2026, 001)
        
        y, c = None, None
        
        m1 = re.search(r"-(\d{4})-(\d{3})\.json", name)
        if m1:
            y, c = m1.group(1), m1.group(2)
        
        if y and c:
            key = (y, c)
            if key in pdf_map:
                pdf_file = pdf_map[key]
                pdf_stem = pdf_file.stem # ANG-001-2026-02-005
                target_name = f"Angebot_{pdf_stem}.json"
                target_path = angebote_dir / target_name
                
                if json_file.name != target_name:
                    print(f"Renaming {json_file.name} -> {target_name}")
                    if target_path.exists():
                        print("  Target exists? Overwriting logic needed? Skipping to be safe.")
                        continue
                        
                    try:
                        # Rename
                        json_file.rename(target_path)
                        
                        # Update content
                        with open(target_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        if data.get('nummer') != pdf_stem:
                            data['nummer'] = pdf_stem
                            with open(target_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4)
                            print("  Updated 'nummer' inside JSON")
                            
                    except Exception as e:
                        print(f"  Error: {e}")
            else:
                print(f"Orphan JSON: {name} (No PDF found for Year={y} Counter={c})")

def main():
    for m in BASE_DIR.iterdir():
        if m.is_dir():
            fix_jsons(m)

if __name__ == "__main__":
    main()
