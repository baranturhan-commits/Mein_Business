"""
API Endpoint für Payment Status Updates
Ermöglicht das Markieren von Rechnungen als bezahlt/offen
"""

from pathlib import Path
import sys

# Add backend to path
CURRENT_DIR = Path(__file__).parent
sys.path.append(str(CURRENT_DIR))

import excel_utils
from logger import get_logger
logger = get_logger(__name__)

def update_invoice_status(mandant_dir, rechnung_nr, new_status):
    """Aktualisiert den Status einer Rechnung"""
    
    xlsx_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
    csv_file = mandant_dir / 'Einnahmen' / 'einnahmen.csv'
    
    if xlsx_file.exists():
        # Update Excel
        try:
            excel_utils.update_status(
                str(xlsx_file),
                'Rechnungsnummer',
                rechnung_nr,
                'Status',
                new_status
            )
            logger.info(f"Status aktualisiert: {rechnung_nr} → {new_status}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Excel-Update: {str(e)}")
            return False
    
    elif csv_file.exists():
        # Update CSV
        try:
            import csv
            import tempfile
            import shutil
            
            # Lese alle Zeilen
            rows = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row.get('Rechnungsnummer') == rechnung_nr:
                        row['Status'] = new_status
                    rows.append(row)
            
            # Schreibe zurück
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"CSV Status aktualisiert: {rechnung_nr} → {new_status}")
            return True
        
        except Exception as e:
            logger.error(f"Fehler beim CSV-Update: {str(e)}")
            return False
    
    return False
