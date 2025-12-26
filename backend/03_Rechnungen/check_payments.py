import os
import sys
import csv
import tempfile
import shutil

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_mandanten():
    if not os.path.exists(MANDANTEN_DIR):
        print(f"❌ Fehler: Ordner 'Mandanten' nicht gefunden in: {BASE_DIR}")
        sys.exit(1)
    items = [d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(items)

def load_invoices(einnahmen_path):
    """Lädt alle Rechnungen aus einnahmen.csv"""
    invoices = []
    
    if not os.path.exists(einnahmen_path):
        print(f"⚠️  Datei nicht gefunden: {einnahmen_path}")
        return invoices
    
    try:
        with open(einnahmen_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                invoices.append(row)
    except Exception as e:
        print(f"❌ Fehler beim Lesen der CSV: {e}")
        
    return invoices

def update_invoice_status(einnahmen_path, invoice_nr, new_status):
    """Aktualisiert den Status einer Rechnung"""
    
    if not os.path.exists(einnahmen_path):
        print(f"❌ Datei nicht gefunden: {einnahmen_path}")
        return False
    
    try:
        # Lese alle Zeilen
        rows = []
        with open(einnahmen_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            fieldnames = reader.fieldnames
            
            # Sicherstellen, dass Status-Spalte existiert
            if 'Status' not in fieldnames:
                fieldnames = list(fieldnames) + ['Status']
            
            for row in reader:
                if row['Rechnungsnummer'] == invoice_nr:
                    row['Status'] = new_status
                elif 'Status' not in row or not row['Status']:
                    row['Status'] = 'Offen'  # Fallback für alte Einträge
                rows.append(row)
        
        # Schreibe alle Zeilen zurück
        with open(einnahmen_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
            
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren: {e}")
        return False

def display_invoice_details(invoice):
    """Zeigt Details einer Rechnung"""
    print(f"\n📄 Rechnungsnummer: {invoice.get('Rechnungsnummer', 'N/A')}")
    print(f"📅 Datum: {invoice.get('Datum', 'N/A')}")
    print(f"👤 Kunde: {invoice.get('Kunde', 'N/A')}")
    print(f"📝 Beschreibung: {invoice.get('Beschreibung', 'N/A')}")
    print(f"💶 Betrag Brutto: {invoice.get('Betrag_Brutto', 'N/A')} €")
    status = invoice.get('Status', 'Offen')
    status_icon = "✅" if status == "Bezahlt" else "⏳"
    print(f"{status_icon} Status: {status}")
    print("-" * 60)

def main():
    clear_screen()
    print("💰 ZAHLUNGSEINGANGS-CHECKER")
    print("=" * 60)
    
    # 1. Mandant auswählen
    mandanten = list_mandanten()
    if not mandanten:
        print("⚠️  Keine Mandanten gefunden.")
        return
    
    print("\nBitte Mandant wählen:")
    for i, m in enumerate(mandanten, 1):
        print(f"[{i}] {m}")
    
    choice = input("\nAuswahl: ").strip()
    if not choice.isdigit():
        print("❌ Ungültige Eingabe.")
        return
    
    idx = int(choice) - 1
    if not (0 <= idx < len(mandanten)):
        print("❌ Ungültige Auswahl.")
        return
    
    selected_mandant = mandanten[idx]
    mandant_path = os.path.join(MANDANTEN_DIR, selected_mandant)
    einnahmen_path = os.path.join(mandant_path, "einnahmen.csv")
    
    print(f"\n👉 Gewählt: {selected_mandant}")
    print("=" * 60)
    
    # 2. Rechnungen laden
    invoices = load_invoices(einnahmen_path)
    
    if not invoices:
        print("\n⚠️  Keine Rechnungen gefunden.")
        return
    
    # 3. Offene Rechnungen anzeigen
    open_invoices = [inv for inv in invoices if inv.get('Status', 'Offen') == 'Offen']
    paid_invoices = [inv for inv in invoices if inv.get('Status', '') == 'Bezahlt']
    
    print(f"\n📊 ÜBERSICHT:")
    print(f"   Gesamt: {len(invoices)} Rechnungen")
    print(f"   ⏳ Offen: {len(open_invoices)}")
    print(f"   ✅ Bezahlt: {len(paid_invoices)}")
    
    if not open_invoices:
        print("\n🎉 Super! Alle Rechnungen sind bezahlt!")
        
        # Zeige trotzdem alle Rechnungen zur Information
        print("\n📋 Alle Rechnungen:")
        for invoice in invoices:
            display_invoice_details(invoice)
        
        input("\n[Enter] zum Beenden...")
        return
    
    print("\n" + "=" * 60)
    print("⏳ OFFENE RECHNUNGEN:")
    print("=" * 60)
    
    # 4. Durchlaufe offene Rechnungen
    for i, invoice in enumerate(open_invoices, 1):
        display_invoice_details(invoice)
        
        # Frage ob bezahlt
        while True:
            answer = input(f"\n[{i}/{len(open_invoices)}] Wurde diese Rechnung bezahlt? (j/n/s für Überspringen): ").strip().lower()
            
            if answer == 'j':
                # Markiere als bezahlt
                if update_invoice_status(einnahmen_path, invoice['Rechnungsnummer'], 'Bezahlt'):
                    print("✅ Status auf 'Bezahlt' gesetzt!")
                break
            elif answer == 'n':
                print("⏳ Bleibt auf 'Offen'.")
                break
            elif answer == 's':
                print("⏭️  Übersprungen.")
                break
            else:
                print("❌ Bitte 'j' (ja), 'n' (nein) oder 's' (überspringen) eingeben.")
        
        # Zeige Fortschritt
        if i < len(open_invoices):
            print("\n" + "-" * 60)
            continue_check = input("Weiter zur nächsten Rechnung? (Enter = Ja, 'q' = Beenden): ").strip().lower()
            if continue_check == 'q':
                print("\n👋 Abgebrochen.")
                break
    
    # 5. Finale Übersicht
    print("\n" + "=" * 60)
    print("📊 FINALE ÜBERSICHT:")
    
    # Lade nochmal um aktuelle Zahlen zu zeigen
    invoices = load_invoices(einnahmen_path)
    open_invoices = [inv for inv in invoices if inv.get('Status', 'Offen') == 'Offen']
    paid_invoices = [inv for inv in invoices if inv.get('Status', '') == 'Bezahlt']
    
    total_open = sum(float(inv.get('Betrag_Brutto', '0').replace(',', '.')) for inv in open_invoices if inv.get('Betrag_Brutto'))
    total_paid = sum(float(inv.get('Betrag_Brutto', '0').replace(',', '.')) for inv in paid_invoices if inv.get('Betrag_Brutto'))
    
    print(f"   ⏳ Offen: {len(open_invoices)} Rechnungen → {total_open:.2f} €")
    print(f"   ✅ Bezahlt: {len(paid_invoices)} Rechnungen → {total_paid:.2f} €")
    print("=" * 60)
    
    if open_invoices:
        print("\n⚠️  ACHTUNG: Noch offene Forderungen!")
        print("💡 Tipp: Starte 'agent.py' für das Mahnwesen.")
    else:
        print("\n🎉 Perfekt! Keine offenen Forderungen mehr!")
    
    input("\n[Enter] zum Beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Abbruch durch Benutzer.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
