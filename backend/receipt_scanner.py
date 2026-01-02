# scanner.py
# Professioneller Multi-Item Beleg-Scanner mit Mandanten-Support
import google.generativeai as genai
import os
import csv
import json
import sys
import io
import shutil
import hashlib
import glob
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# [NEW] Excel Support
# [NEW] Excel Support
# sys.path.append(os.path.dirname(CURRENT_DIR)) 
import excel_utils

# Windows Console Fix für Sonderzeichen (Euro, Umlaute)

# ... (rest unchanged) ...

def get_mandant_paths(mandant_name, category):
    """
    Erstellt Pfade für Mandant und Kategorie.
    Struktur: Mandanten/[Mandant]/Ausgaben/[Kategorie]/Dateien
    XLSX: Mandanten/[Mandant]/Ausgaben/ausgaben.xlsx
    """
    if not mandant_name or not category:
        return None, None

    # Basis Ausgaben Ordner des Mandanten
    ausgaben_root = os.path.join(MANDANTEN_DIR, mandant_name, "Ausgaben")
    if not os.path.exists(ausgaben_root):
        os.makedirs(ausgaben_root)
    
    # XLSX Pfad
    xlsx_path = os.path.join(ausgaben_root, "ausgaben.xlsx")
    
    # Ziel-Ordner für die Datei
    safe_cat = "".join(c for c in category if c.isalnum() or c in (' ', '_', '-')).strip()
    target_dir = os.path.join(ausgaben_root, safe_cat)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    return xlsx_path, target_dir

# ... (omitting validate_csv_headers and load_beleg_counter as they might need adjustment or removal, but let's focus on logic replacement)

def generate_beleg_nr(mandant_path=""): 
    # Simplified counter - ideally read from max in excel, but for now simple random or time based 
    # OR read from excel if possible. Let's keep global counter heuristic or just use TimeID for now to avoid complexity reading back
    # BETTER: Read count from excel.
    # For now, let's stick to the simpler global heuristic or just random.
    # Let's keep logic simple: random/time based is safer without complex read-back.
    # Existing logic used a global counter loaded from CSV.
    # Let's use Timestamp
    return f"RE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def save_and_move(filepath, mandant_name, category, items):
    """Speichert Daten in Excel und verschiebt Datei."""
    xlsx_path, target_dir = get_mandant_paths(mandant_name, category)
    
    new_rows = []
    
    for item in items:
        # Override Category
        item['Kategorie'] = category
        item['Brutto'] = format_german_number(item['Brutto'])
        item['Netto'] = format_german_number(item['Netto'])
        item['MwSt'] = format_german_number(item['MwSt'])
        item['Beleg-Nr.'] = generate_beleg_nr()
        
        # Save to Excel
        excel_utils.append_data(xlsx_path, item, "Ausgaben", EXPECTED_HEADERS)
        new_rows.append(item)
        print(f"✅ Excel Eintrag: {item['Beleg-Nr.']} | {item['Firma']} | {item['Brutto']}")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- KONFIGURATION ---
# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print("❌ Fehler: GOOGLE_API_KEY nicht in .env gefunden!")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)
# Gemini 2.0 Flash-Lite: schnell, günstig, perfekt für Belege
model = genai.GenerativeModel('models/gemini-2.0-flash-lite')

# --- PFADE ---
# --- PFADE ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR) # Mein_Business Root (Parent of backend)
# Wait, if scanner is in backend/, BASE_DIR (parent) is Mein_Business. 
# But Mandanten is in backend/Mandanten. 
# Previous code: scanner was in 02_Buchhaltung. CURRENT_DIR=02_Buchhaltung. BASE_DIR=backend.
# Now: CURRENT_DIR=backend. BASE_DIR=Mein_Business.
# MANDANTEN_DIR should be os.path.join(CURRENT_DIR, "Mandanten")
MANDANTEN_DIR = os.path.join(CURRENT_DIR, "Mandanten")
# INPUT_SCANS_DIR should be in Mein_Business root? Or backend?
# Previously: BASE_DIR was backend? No, `os.path.dirname(CURRENT_DIR)`.
# If scanner was in `backend/02_Buchhaltung`, `dirname` is `backend`.
# `MANDANTEN_DIR` was in `backend/Mandanten`. Correct.
# `INPUT_SCANS_DIR` was `backend/Input_Scans`? 
# Let's check listing of backend. `Input_Scans` is NOT in backend listing I saw earlier.
# Check Main Dir listing.
INPUT_SCANS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "Input_Scans")

# Erwartete Header-Struktur (für Validierung)
EXPECTED_HEADERS = ['Datum', 'Beleg-Nr.', 'Firma', 'Beschreibung', 'Kategorie', 'Netto', 'MwSt', 'Brutto']

# Globale Variable für Beleg-Counter (wird pro CSV geladen)
beleg_counter = 1

# Standard-Kategorien für Vorschläge
DEFAULT_CATEGORIES = ["Material", "Kfz-Kosten", "Bürobedarf", "Werbung", "Bewirtung", "Tanken", "Sonstiges"]

def ensure_base_directories():
    """Stellt sicher, dass der Input-Ordner existiert."""
    if not os.path.exists(INPUT_SCANS_DIR):
        print(f"⚠️  Ordner 'Input_Scans' nicht gefunden.")
        os.makedirs(INPUT_SCANS_DIR)
        print(f"✅ Ordner erstellt: {INPUT_SCANS_DIR}")
        print("👉 Bitte lege deine Belege (Bilder/PDFs) in diesen Ordner.")
        input("   Drücke ENTER, wenn du bereit bist... ") 
    else:
        # Check if empty
        if not glob.glob(os.path.join(INPUT_SCANS_DIR, "*.*")):
            print(f"ℹ️  Ordner '{os.path.basename(INPUT_SCANS_DIR)}' ist leer.")
            print("👉 Bitte lege deine Belege dort ab.")
            input("   Drücke ENTER, wenn du bereit bist... ")

def get_mandanten():
    """Listet alle Mandanten-Ordner auf."""
    if not os.path.exists(MANDANTEN_DIR):
        os.makedirs(MANDANTEN_DIR)
        return []
    
    mandanten = [d for d in os.listdir(MANDANTEN_DIR) 
                 if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(mandanten)

def select_mandant():
    """Fragt den Nutzer nach dem Mandanten."""
    mandanten = get_mandanten()
    if not mandanten:
        print("❌ Keine Mandanten gefunden! Bitte erstelle Ordner in 'Mandanten/'.")
        return None

    print("\n🏢 Für welchen Mandanten ist das?")
    print("="*40)
    for idx, m in enumerate(mandanten, 1):
        print(f"{idx}. {m}")
    print("x. Abbrechen")

    while True:
        choice = input("\nAuswahl: ").strip()
        if choice.lower() == 'x':
            return None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(mandanten):
                return mandanten[idx]
        print("❌ Ungültige Auswahl.")

def select_category():
    """Fragt den Nutzer nach einer Kategorie."""
    print("\n📂 Kategorie wählen:")
    print("-" * 40)
    for idx, cat in enumerate(DEFAULT_CATEGORIES, 1):
        print(f"{idx}. {cat}")
    print("0. Eigene eingeben")
    
    while True:
        choice = input("\nAuswahl: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(DEFAULT_CATEGORIES):
                return DEFAULT_CATEGORIES[idx]
            if choice == "0":
                custom = input("Bitte Kategorie eingeben: ").strip()
                if custom: return custom
        # Fallback: Wenn Text eingegeben wurde, nimm ihn als Kategorie
        if not choice.isdigit() and choice:
             # Check if input matches a category name directly (case insensitive)
             for cat in DEFAULT_CATEGORIES:
                 if cat.lower() == choice.lower():
                     return cat
             return choice # Als Custom Category

        print("❌ Ungültige Auswahl.")

def get_mandant_paths(mandant_name, category):
    """
    Erstellt Pfade für Mandant und Kategorie.
    Struktur: Mandanten/[Mandant]/Ausgaben/[Kategorie]/Dateien
    XLSX: Mandanten/[Mandant]/Ausgaben/ausgaben.xlsx
    """
    if not mandant_name or not category:
        return None, None

    # Basis Ausgaben Ordner des Mandanten
    ausgaben_root = os.path.join(MANDANTEN_DIR, mandant_name, "Ausgaben")
    if not os.path.exists(ausgaben_root):
        os.makedirs(ausgaben_root)
    
    # XLSX Pfad
    xlsx_path = os.path.join(ausgaben_root, "ausgaben.xlsx")
    
    # Ziel-Ordner für die Datei
    safe_cat = "".join(c for c in category if c.isalnum() or c in (' ', '_', '-')).strip()
    target_dir = os.path.join(ausgaben_root, safe_cat)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    return xlsx_path, target_dir

def validate_csv_headers(csv_path):
    """Prüft und erstellt CSV Header."""
    if not os.path.isfile(csv_path):
        # Neue Datei erstellen
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        return True
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file, delimiter=';')
            first_row = next(reader, None)
            if first_row != EXPECTED_HEADERS:
                pass
            return True
    except:
        return True

def load_beleg_counter(csv_path):
    """Lädt den letzten Beleg-Zähler aus der CSV."""
    global beleg_counter
    beleg_counter = 1 # Reset defaults
    if not os.path.isfile(csv_path):
        return
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            rows = list(reader)
            if rows:
                last_beleg = rows[-1].get('Beleg-Nr.', '')
                if last_beleg and '-' in last_beleg:
                    try:
                        last_num = int(last_beleg.split('-')[-1])
                        beleg_counter = last_num + 1
                    except:
                        pass
    except:
        pass

def generate_beleg_nr():
    """Generiert automatisch eine Beleg-Nummer."""
    global beleg_counter
    jahr = datetime.now().year
    beleg_nr = f"RE-{jahr}-{beleg_counter:03d}"
    beleg_counter += 1
    return beleg_nr

def format_german_number(value):
    """Standardisiert 12.50 -> 12,50 €"""
    if isinstance(value, (int, float)):
        num = value
    else:
        clean = str(value).replace('€', '').strip().replace(',', '.')
        try:
            num = float(clean)
        except ValueError:
            return str(value)

    return f"{num:.2f}".replace('.', ',') + " €"

def analyze_beleg(filepath):
    """Sendet Beleg an Gemini."""
    print("🧠 Analysiere Beleg... (Das kann kurz dauern)")
    
    # Prompt so anpassen, dass nur notwendiges generiert wird, Category wird vom User überschrieben
    prompt = """
    Analysiere diesen Beleg. Erstelle eine JSON-Liste von Ausgaben.
    Felder: Datum (DD.MM.YYYY), Firma, Beschreibung, Kategorie (Rate mal), Brutto, MwSt_Satz (0, 7 or 19).
    Berechne Netto und MwSt Beträge.
    Output NUR JSON: [{"Datum": "...", "Firma": "...", ...}]
    """
    
    try:
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        
        if ext == '.pdf':
            uploaded_file = genai.upload_file(filepath)
            response = model.generate_content([prompt, uploaded_file])
        else:
            img = Image.open(filepath)
            response = model.generate_content([prompt, img])
            
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        start = clean_json.find("[")
        end = clean_json.rfind("]")
        if start != -1 and end != -1:
            return json.loads(clean_json[start:end+1])
        # Try finding object
        start = clean_json.find("{")
        end = clean_json.rfind("}")
        if start != -1 and end != -1:
            return [json.loads(clean_json[start:end+1])]
            
        return []
    except Exception as e:
        print(f"❌ Fehler bei KI-Analyse: {e}")
        return []

def save_and_move(filepath, mandant_name, category, items):
    """Speichert Daten in Excel und verschiebt Datei."""
    xlsx_path, target_dir = get_mandant_paths(mandant_name, category)
    
    new_rows = []
    
    for item in items:
        # Override Category
        item['Kategorie'] = category
        item['Brutto'] = format_german_number(item['Brutto'])
        item['Netto'] = format_german_number(item['Netto'])
        item['MwSt'] = format_german_number(item['MwSt'])
        item['Beleg-Nr.'] = generate_beleg_nr()
        
        # Save to Excel
        # Map Item keys to Header keys exactly
        data_row = {
            'Datum': item.get('Datum', ''),
            'Beleg-Nr.': item['Beleg-Nr.'],
            'Firma': item.get('Firma', ''),
            'Beschreibung': item.get('Beschreibung', ''),
            'Kategorie': category,
            'Netto': item['Netto'],
            'MwSt': item['MwSt'],
            'Brutto': item['Brutto']
        }
        
        excel_utils.append_data(xlsx_path, data_row, "Ausgaben", EXPECTED_HEADERS)
        new_rows.append(data_row)
        print(f"✅ Excel Eintrag: {data_row['Beleg-Nr.']} | {data_row['Firma']} | {data_row['Brutto']}")

    # 2. Datei Verschieben
    # Generate new filename
    try:
        if new_rows:
            # Use info from first item
            first = new_rows[0]
            date_str = first['Datum']
            firma = first['Firma']
            betrag = first['Brutto'].replace(' €', '').replace(',', '.')
        else:
            # Fallback if no CSV rows (e.g. all duplicates or empty)
            date_str = datetime.now().strftime("%d.%m.%Y")
            firma = "Scan"
            betrag = "0"

        # Datum umformatieren für Dateiname YYYY-MM-DD
        try:
            d_obj = datetime.strptime(date_str, "%d.%m.%Y")
            date_fmt = d_obj.strftime("%Y-%m-%d")
        except:
            date_fmt = datetime.now().strftime("%Y-%m-%d")

        safe_firma = "".join(c for c in firma if c.isalnum() or c in ('_', '-')).strip()
        _, ext = os.path.splitext(filepath)
        
        new_filename = f"{date_fmt}_{safe_firma}_{betrag}{ext}"
        target_path = os.path.join(target_dir, new_filename)
        
        # Collision check
        c = 1
        while os.path.exists(target_path):
            new_filename = f"{date_fmt}_{safe_firma}_{betrag}_{c}{ext}"
            target_path = os.path.join(target_dir, new_filename)
            c += 1
            
        shutil.move(filepath, target_path)
        print(f"📦 Datei verschoben nach: .../{mandant_name}/Ausgaben/{category}/{new_filename}")
        
    except Exception as e:
        print(f"❌ Fehler beim Verschieben: {e}")

def main():
    print("=" * 60)
    print("🧾 MULTI-CLIENT SCANNER (Mandanten-Modus)")
    print("=" * 60)
    
    ensure_base_directories()
    
    while True:
        # Suche alle Dateien in Input_Scans
        search_pattern = os.path.join(INPUT_SCANS_DIR, "*")
        files = [f for f in glob.glob(search_pattern) if os.path.isfile(f)]
        
        if not files:
            print("📭 Keine Dateien in Input_Scans gefunden.")
            # Option zum Beenden oder Retry
            choice = input("🔄 Erneut scannen? (Enter) oder 'x' zum Beenden: ")
            if choice.lower() == 'x':
                break
            continue

        print(f"🔎 {len(files)} Datei(en) gefunden.\n")
        
        for filepath in files:
            filename = os.path.basename(filepath)
            print(f"\n📄 Bearbeite: {filename}")
            print("-" * 40)
            
            # 1. Mandant
            mandant = select_mandant()
            if not mandant:
                print("⏭️  Überspringe Datei.")
                continue
                
            # 2. Kategorie
            category = select_category()
            
            # 3. Analyse
            try:
                items = analyze_beleg(filepath)
                if not items:
                    print("⚠️  Konnte keine Daten auslesen. Verschiebe nur Datei...")
                    items = [] # Leere Liste, nur Datei bewegen
                    
                # 4. Speichern & Verschieben
                save_and_move(filepath, mandant, category, items)
                
            except Exception as e:
                print(f"❌ Fehler bei Datei {filename}: {e}")

        print("\n🎉 Alle Dateien verarbeitet.")
        choice = input("\n🏁 Fertig? (x = Beenden, Enter = Neustart): ")
        if choice.lower() == 'x':
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")