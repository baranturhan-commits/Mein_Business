"""
Automatischer Monatsreport
Erstellt am 1. des Monats einen Report für alle Mandanten
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import csv

# Add backend to path
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))

from logger import get_logger
logger = get_logger(__name__)

MANDANTEN_DIR = BACKEND_DIR / 'Mandanten'
REPORTS_DIR = BACKEND_DIR / '04_Controlling' / 'Reports'
REPORTS_DIR.mkdir(exist_ok=True)

def generate_monthly_report():
    """Generiert monatlichen Report für alle Mandanten"""
    
    logger.info("=== Starte monatlichen Report ===")
    print("📊 Generiere Monatsreport...")
    
    current_month = datetime.now().strftime("%Y-%m")
    report_file = REPORTS_DIR / f"Report_{current_month}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Monatlicher Business Report - {current_month}\n")
        f.write("=" * 60 + "\n\n")
        
        total_einnahmen = 0
        total_offen = 0
        mandanten_count = 0
        
        for mandant_dir in MANDANTEN_DIR.iterdir():
            if not mandant_dir.is_dir():
                continue
            
            mandanten_count += 1
            mandant_name = mandant_dir.name
            
            f.write(f"\n🏢 {mandant_name}\n")
            f.write("-" * 40 + "\n")
            
            # Einnahmen
            einnahmen_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
            if not einnahmen_file.exists():
                einnahmen_file = mandant_dir / 'einnahmen.csv'
            
            if einnahmen_file.exists():
                try:
                    if einnahmen_file.suffix == '.xlsx':
                        import excel_utils
                        data = excel_utils.read_data(einnahmen_file, 'Einnahmen')
                    else:
                        data = []
                        with open(einnahmen_file, 'r', encoding='utf-8') as csvf:
                            reader = csv.DictReader(csvf)
                            data = list(reader)
                    
                    einnahmen = sum(float(row.get('Betrag_Netto', 0)) for row in data)
                    offen = sum(float(row.get('Betrag_Netto', 0)) for row in data if row.get('Status') == 'Offen')
                    
                    total_einnahmen += einnahmen
                    total_offen += offen
                    
                    f.write(f"  💰 Einnahmen: {einnahmen:.2f} €\n")
                    f.write(f"  ⏳ Offen: {offen:.2f} €\n")
                    f.write(f"  ✅ Bezahlt: {einnahmen - offen:.2f} €\n")
                    
                except Exception as e:
                    f.write(f"  ⚠️ Fehler beim Laden: {e}\n")
            else:
                f.write("  📭 Keine Einnahmen-Daten\n")
        
        # Zusammenfassung
        f.write("\n" + "=" * 60 + "\n")
        f.write("ZUSAMMENFASSUNG\n")
        f.write("=" * 60 + "\n")
        f.write(f"Mandanten: {mandanten_count}\n")
        f.write(f"Gesamteinnahmen: {total_einnahmen:.2f} €\n")
        f.write(f"Offene Forderungen: {total_offen:.2f} €\n")
        f.write(f"Bezahlt: {total_einnahmen - total_offen:.2f} €\n")
        f.write(f"\nErstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"✅ Report erstellt: {report_file}")
    logger.info(f"Report erstellt: {report_file}")
    
    return report_file

if __name__ == '__main__':
    try:
        generate_monthly_report()
    except Exception as e:
        logger.error(f"Fehler beim Report: {str(e)}")
        print(f"❌ Fehler: {e}")
