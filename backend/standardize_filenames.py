import os
import shutil
import re
from pathlib import Path

# Config
MANDANTEN_DIR = Path(r'c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten')

def standardize_invoices(mandant_id):
    print(f"Checking Mandant: {mandant_id}")
    mandant_path = MANDANTEN_DIR / mandant_id
    rechnungen_dir = mandant_path / 'Rechnungen'
    
    if not rechnungen_dir.exists():
        print("No Rechnungen dir found")
        return

    # Find all PDFs
    pdfs = list(rechnungen_dir.rglob('*.pdf'))
    print(f"Found {len(pdfs)} PDFs")
    
    for pdf in pdfs:
        # Pattern: Look for YYYY-NNN
        match = re.search(r'(\d{4}-\d{3})', pdf.name)
        if match:
            nr = match.group(1)
            new_name = f"{nr}.pdf"
            
            # Destination: Flat in Rechnungen dir
            dest = rechnungen_dir / new_name
            
            if pdf != dest:
                print(f"Renaming/Moving: {pdf.name} -> {new_name}")
                try:
                    shutil.move(str(pdf), str(dest))
                except Exception as e:
                    print(f"Error moving {pdf}: {e}")
        else:
            print(f"Skipping {pdf.name} (No ID found)")
            
    # Clean up empty dirs
    for root, dirs, files in os.walk(rechnungen_dir, topdown=False):
        for name in dirs:
            d = Path(root) / name
            if not any(d.iterdir()):
                print(f"Removing empty dir: {d}")
                d.rmdir()

if __name__ == "__main__":
    # Run for active client
    standardize_invoices('Elektroniker_Testbetrieb')
