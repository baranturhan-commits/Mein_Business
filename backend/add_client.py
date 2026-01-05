import os
import sys
import csv
import re
import json
import shutil
import excel_utils # [NEW]

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANDANTEN_DIR = os.path.join(SCRIPT_DIR, "Mandanten")

def clean_name(name):
    """
    Konvertiert "Bäckerei Müller" -> "Baeckerei_Mueller"
    """
    if not name: return ""
    
    # Umlaute
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    name = name.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    
    # Leerzeichen -> Underscore
    name = name.strip().replace(" ", "_")
    
    # Sonderzeichen entfernen (außer _ und -)
    name = re.sub(r'[^\w\-_]', '', name)
    return name

def ensure_mandanten_dir():
    if not os.path.exists(MANDANTEN_DIR):
        os.makedirs(MANDANTEN_DIR)

def list_mandanten():
    ensure_mandanten_dir()
    items = [d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(items)

def create_mandant():
    print("\n🏢 MODUS: NEUER MANDANT")
    print("=======================")
    
    # --- STAMMDATEN ABFRAGE ---
    name = input("Firmenname (z.B. 'Maler Müller'): ").strip()
    if not name:
        print("❌ Name darf nicht leer sein.")
        return

    mandant_nr = input("Mandantennummer (z.B. '101'): ").strip()
    if not mandant_nr:
        # Default fallback or require? Let's default to generic if empty, but better to encourage it.
        # But for new clients we want it.
        print("⚠️  Keine Nummer angegeben. Verwende '000'.")
        mandant_nr = "000"

    safe_name = clean_name(name)
    mandant_path = os.path.join(MANDANTEN_DIR, safe_name)
    
    if os.path.exists(mandant_path):
        print(f"❌ Mandant '{safe_name}' existiert bereits.")
        return

    print("\n📍 Adresse & Details:")
    strasse = input("Straße & Hausnummer: ").strip()
    ort = input("PLZ & Ort: ").strip()
    gf = input("Geschäftsführer: ").strip()
    
    print("\n🏦 Bankverbindung:")
    iban = input("IBAN: ").strip()
    bic = input("BIC: ").strip()
    bank = input("Bankname: ").strip()
    
    print("\n🖼️  Logo (Optional):")
    logo_input = input("Pfad zur Bilddatei (z.B. C:/Bilder/logo.png): ").strip().replace('"', '')
    
    try:
        # 1. Folder Structure
        os.makedirs(mandant_path, exist_ok=True)
        os.makedirs(os.path.join(mandant_path, "Rechnungen"), exist_ok=True)
        os.makedirs(os.path.join(mandant_path, "Angebote"), exist_ok=True) # [NEW]
        os.makedirs(os.path.join(mandant_path, "Lieferscheine"), exist_ok=True) # [NEW]
        os.makedirs(os.path.join(mandant_path, "Kunden"), exist_ok=True)
        os.makedirs(os.path.join(mandant_path, "Einnahmen"), exist_ok=True)
        os.makedirs(os.path.join(mandant_path, "Ausgaben"), exist_ok=True)
        os.makedirs(os.path.join(mandant_path, "Reports"), exist_ok=True)
        
        # 2. Logo Handling
        logo_filename = None
        if logo_input and os.path.exists(logo_input):
            ext = os.path.splitext(logo_input)[1]
            if not ext: ext = ".png" # Default fallback
            
            logo_filename = f"logo{ext}"
            dest_logo = os.path.join(mandant_path, logo_filename)
            try:
                shutil.copy(logo_input, dest_logo)
                print(f"✅ Logo kopiert nach: {dest_logo}")
            except Exception as e:
                print(f"⚠️  Konnte Logo nicht kopieren: {e}")
                logo_filename = None
        
        # 3. Config JSON
        config_data = {
            "firma": name,
            "mandant_nummer": mandant_nr,
            "adresse": {
                "strasse": strasse,
                "ort": ort,
            },
            "geschaeftsfuehrer": gf,
            "bank": {
                "iban": iban,
                "bic": bic,
                "name": bank
            },
            "logo": logo_filename
        }
        
        config_path = os.path.join(mandant_path, "mandant_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
            
        print("✅ Mandantendaten gespeichert (mandant_config.json).")
        
        # 4. Excel Init (statt CSV)
        xlsx_path = os.path.join(mandant_path, "Kunden", "kunden.xlsx")
        excel_utils.init_file(xlsx_path, ['Firma', 'Email', 'Anrede'], "Kunden")
        
        # 5. Einnahmen Excel Init
        einnahmen_xlsx = os.path.join(mandant_path, "Einnahmen", "einnahmen.xlsx")
        excel_utils.init_file(einnahmen_xlsx, 
            ['Rechnungsnummer', 'Datum', 'Kunde', 'Beschreibung', 'Betrag_Netto', 'Betrag_Brutto', 'Status'], 
            "Einnahmen")
        
        # 6. Ausgaben Excel Init  
        ausgaben_xlsx = os.path.join(mandant_path, "Ausgaben", "ausgaben.xlsx")
        excel_utils.init_file(
            str(mandant_path / 'Ausgaben' / 'ausgaben.xlsx'),
            ['Datum', 'Beleg-Nr.', 'Firma', 'Beschreibung', 'Kategorie', 'Netto', 'MwSt', 'Brutto'],
            'Ausgaben'
        )
        
        # 7. Preisliste Excel Init
        preisliste_xlsx = os.path.join(mandant_path, "preisliste.xlsx")
        excel_utils.init_file(preisliste_xlsx,
            ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie'],
            "Preisliste")
        
        # 8. Angebote Excel Init  
        angebote_xlsx = os.path.join(mandant_path, "Angebote", "angebote.xlsx")
        excel_utils.init_file(angebote_xlsx,
            ['Nummer', 'Datum', 'Kunde', 'Netto', 'Brutto', 'Status', 'PDF_Path'],
            "Angebote")

        # 9. Lieferscheine Excel Init
        lieferscheine_xlsx = os.path.join(mandant_path, "Lieferscheine", "lieferscheine.xlsx")
        os.makedirs(os.path.dirname(lieferscheine_xlsx), exist_ok=True)
        excel_utils.init_file(lieferscheine_xlsx,
            ['Nummer', 'Datum', 'Kunde', 'Angebot', 'PDF_Path', 'Status'],
            "Lieferscheine")    
        print(f"\n✨ Mandant '{name}' erfolgreich angelegt!")
        print(f"   Ordner: {mandant_path}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

def create_kunde():
    print("\n👤 MODUS: NEUER KUNDE")
    print("====================")
    
    mandanten = list_mandanten()
    if not mandanten:
        print("⚠️  Keine Mandanten gefunden.")
        print("Bitte erst einen Mandanten anlegen.")
        return

    print("Vorhandene Mandanten:")
    for i, m in enumerate(mandanten, 1):
        print(f"{i}. {m}")
        
    choice = input("\nBitte wählen (Nummer): ").strip()
    
    selected_mandant = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(mandanten):
            selected_mandant = mandanten[idx]
            
    if not selected_mandant:
        print("❌ Ungültige Auswahl.")
        return
        
    print(f"\nGewählt: {selected_mandant}")
    print("-" * 20)
    
    # --- Kunde Data Input ---
    raw_firma = input("Name für Rechnung (z.B. 'Hans Meier'): ").strip()
    if not raw_firma:
        print("❌ Name darf nicht leer sein.")
        return
        
    contact = input("Ansprechpartner: ").strip()
    email = input("Email: ").strip()
    
    safe_firma = clean_name(raw_firma)
    
    if "herr" in contact.lower():
        anrede = f"Sehr geehrter {contact}"
    elif "frau" in contact.lower():
        anrede = f"Sehr geehrte {contact}"
    else:
        anrede = "Sehr geehrte Damen und Herren"
        
    # Paths
    mandant_path = os.path.join(MANDANTEN_DIR, selected_mandant)
    kunden_dir = os.path.join(mandant_path, "Kunden")
    if not os.path.exists(kunden_dir): os.makedirs(kunden_dir, exist_ok=True)
    
    xlsx_path = os.path.join(kunden_dir, "kunden.xlsx")
    
    invoice_folder = os.path.join(mandant_path, "Rechnungen", safe_firma)
    
    try:
        if not os.path.exists(invoice_folder):
            os.makedirs(invoice_folder)
            
        # Append to Excel
        data = {
            'Firma': safe_firma,
            'Email': email,
            'Anrede': anrede
        }
        excel_utils.append_data(xlsx_path, data, "Kunden", ['Firma', 'Email', 'Anrede'])
            
        print(f"✅ Kunde '{safe_firma}' erfolgreich für '{selected_mandant}' angelegt.")
        print(f"   Rechnungsordner: {invoice_folder}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "mandant":
            create_mandant()
        elif mode == "kunde":
            create_kunde()
        else:
            print(f"⚠️  Unbekannter Modus: {mode}")
            print("Nutzung: python add_client.py [mandant|kunde]")
    else:
        print("⚠️  Bitte Argument übergeben.")
        print("Nutzung: python add_client.py [mandant|kunde]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Abbruch durch Benutzer.")
        sys.exit(0)
