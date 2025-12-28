import os
import sys

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR) # backend/
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")

# Import excel_utils
sys.path.append(BASE_DIR)
import excel_utils

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_mandanten():
    if not os.path.exists(MANDANTEN_DIR):
        print(f"❌ Fehler: Ordner 'Mandanten' nicht gefunden in: {BASE_DIR}")
        sys.exit(1)
    items = [d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(items)

def load_invoices(xlsx_path):
    """Lädt alle Rechnungen aus Excel"""
    if not os.path.exists(xlsx_path):
        return []
    
    try:
        data = excel_utils.read_data(xlsx_path, "Einnahmen")
        return data
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Excel: {e}")
        return []

def update_invoice_status(xlsx_path, rechnungsnummer, new_status="Bezahlt"):
    return excel_utils.update_status(xlsx_path, "Rechnungsnummer", rechnungsnummer, "Status", new_status)

def display_invoice_details(invoice):
    """Zeigt Details einer Rechnung"""
    print(f"\n📄 Rechnungsnummer: {invoice.get('Rechnungsnummer', 'N/A')}")
    print(f"📅 Datum: {invoice.get('Datum', 'N/A')}")
    print(f"👤 Kunde: {invoice.get('Kunde', 'N/A')}")
    print(f"📝 Beschreibung: {invoice.get('Beschreibung', 'N/A')}")
    print(f"💶 Betrag Brutto: {invoice.get('Betrag_Brutto', '0,00')} €")
    status = invoice.get('Status', 'Offen')
    status_icon = "✅" if status == "Bezahlt" else "⏳"
    print(f"{status_icon} Status: {status}")
    print("-" * 60)

def main():
    clear_screen()
    print("💰 ZAHLUNGSEINGANG PRÜFEN (OP-Liste)")
    print("====================================")
    
    mandanten = list_mandanten()
    if not mandanten: 
        print("Keine Mandanten gefunden.")
        return
    
    print("\nBitte Mandant wählen:")
    for i, m in enumerate(mandanten, 1):
        print(f"[{i}] {m}")
    
    choice = input("\nAuswahl: ").strip()
    if not choice.isdigit(): return
    
    idx = int(choice) - 1
    if not (0 <= idx < len(mandanten)): return
    
    selected_mandant = mandanten[idx]
    mandant_path = os.path.join(MANDANTEN_DIR, selected_mandant)
    print(f"\n👉 Gewählt: {selected_mandant}")
    print("=" * 60)
    
    # Paths
    einnahmen_dir = os.path.join(mandant_path, "Einnahmen")
    xlsx_path = os.path.join(einnahmen_dir, "einnahmen.xlsx")
    
    # Rechnungen laden
    invoices = load_invoices(xlsx_path)
    
    if not invoices:
        print("✅ Keine Rechnungen gefunden.")
        input("\n[Enter] zurück...")
        return

    # Filter
    open_invoices = [inv for inv in invoices if inv.get('Status', 'Offen') == 'Offen']
    paid_invoices = [inv for inv in invoices if inv.get('Status') == 'Bezahlt']

    print(f"Gesamt: {len(invoices)} | Offen: {len(open_invoices)} | Bezahlt: {len(paid_invoices)}")
    
    if not open_invoices:
        print("\n🎉 Keine offenen Posten!")
    else:
        print("\n⏳ OFFENE POSTEN:")
        print("=" * 60)
        for i, invoice in enumerate(open_invoices, 1):
            display_invoice_details(invoice)
            
            while True:
                ans = input(f"Rechnung bezahlt? (j=Ja, n=Nein, s=Skip, q=Quit): ").strip().lower()
                if ans == 'j':
                    if update_invoice_status(xlsx_path, invoice.get('Rechnungsnummer'), "Bezahlt"):
                        print("✅ Markiert als BEZAHLT.")
                    else:
                        print("❌ Fehler beim Speichern.")
                    break
                elif ans == 'n':
                    print("Ok, bleibt offen.")
                    break
                elif ans == 's':
                    break
                elif ans == 'q':
                    return

    # Übersicht
    print("\n" + "=" * 60)
    print("FINALE STATUS:")
    invoices = load_invoices(xlsx_path) # Reload
    open_inv = [i for i in invoices if i.get('Status')=='Offen']
    
    if not open_inv:
        print("🎉 Alles bezahlt!")
    else:
        print(f"⚠️  Noch {len(open_inv)} offen.")
        
    input("\n[Enter] beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")
