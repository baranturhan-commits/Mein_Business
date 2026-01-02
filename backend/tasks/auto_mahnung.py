"""
Automatische Mahnprüfung
Erstellt eine Liste aller fälligen Mahnungen
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import csv

# Add backend to path
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))

from logger import get_logger
logger = get_logger(__name__)

MANDANTEN_DIR = BACKEND_DIR / 'Mandanten'

def check_mahnungen():
    """Prüft alle Mandanten auf fällige Rechnungen"""
    
    logger.info("=== Starte Mahnprüfung ===")
    print("⚠️ Prüfe offene Rechnungen...")
    
    faellige_rechnungen = []
    today = datetime.now()
    
    for mandant_dir in MANDANTEN_DIR.iterdir():
        if not mandant_dir.is_dir():
            continue
        
        mandant_name = mandant_dir.name
        einnahmen_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        
        if not einnahmen_file.exists():
            einnahmen_file = mandant_dir / 'einnahmen.csv'
        
        if not einnahmen_file.exists():
            continue
        
        try:
            # Lade Einnahmen
            if einnahmen_file.suffix == '.xlsx':
                import excel_utils
                data = excel_utils.read_data(einnahmen_file, 'Einnahmen')
            else:
                data = []
                with open(einnahmen_file, 'r', encoding='utf-8') as csvf:
                    reader = csv.DictReader(csvf)
                    data = list(reader)
            
            # Prüfe offene Rechnungen
            for row in data:
                if row.get('Status') != 'Offen':
                    continue
                
                # Prüfe Datum (älter als 30 Tage = fällig)
                datum_str = row.get('Datum', '')
                try:
                    datum = datetime.strptime(datum_str, '%d.%m.%Y')
                    tage_alt = (today - datum).days
                    
                    if tage_alt >= 30:  # Fällig nach 30 Tagen
                        faellige_rechnungen.append({
                            'mandant': mandant_name,
                            'rechnung_nr': row.get('Rechnungsnummer', 'N/A'),
                            'kunde': row.get('Kunde', 'N/A'),
                            'betrag': row.get('Betrag_Brutto', 'N/A'),
                            'datum': datum_str,
                            'tage_alt': tage_alt
                        })
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Fehler bei {mandant_name}: {str(e)}")
    
    # Ausgabe
    if faellige_rechnungen:
        print(f"\n⚠️ {len(faellige_rechnungen)} fällige Rechnung(en) gefunden:\n")
        
        for rechnung in faellige_rechnungen:
            print(f"  📄 {rechnung['mandant']} - {rechnung['rechnung_nr']}")
            print(f"     Kunde: {rechnung['kunde']}")
            print(f"     Betrag: {rechnung['betrag']}€")
            print(f"     Alter: {rechnung['tage_alt']} Tage")
            print()
        
        logger.info(f"{len(faellige_rechnungen)} fällige Rechnungen gefunden")
        
        # Optional: Speichere in Mahnliste
        mahnliste = BACKEND_DIR / '01_Mahnwesen' / 'faellige_mahnungen.txt'
        with open(mahnliste, 'w', encoding='utf-8') as f:
            f.write(f"Fällige Mahnungen - {today.strftime('%Y-%m-%d')}\n")
            f.write("=" * 60 + "\n\n")
            for r in faellige_rechnungen:
                f.write(f"Mandant: {r['mandant']}\n")
                f.write(f"Rechnung: {r['rechnung_nr']}\n")
                f.write(f"Kunde: {r['kunde']}\n")
                f.write(f"Betrag: {r['betrag']}€\n")
                f.write(f"Alter: {r['tage_alt']} Tage\n\n")
        
        print(f"💾 Liste gespeichert: {mahnliste}")
    else:
        print("✅ Keine fälligen Rechnungen!")
        logger.info("Keine fälligen Rechnungen")
    
    return faellige_rechnungen

if __name__ == '__main__':
    try:
        check_mahnungen()
    except Exception as e:
        logger.error(f"Fehler bei Mahnprüfung: {str(e)}")
        print(f"❌ Fehler: {e}")
