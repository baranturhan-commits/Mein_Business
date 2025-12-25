import os
import sys
import csv
import datetime
import re
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def ensure_mandanten_dir():
    if not os.path.exists(MANDANTEN_DIR):
        print(f"❌ Fehler: Ordner 'Mandanten' nicht gefunden in: {BASE_DIR}")
        print("Bitte erst 'add_client.py' ausführen.")
        sys.exit(1)

def list_mandanten():
    ensure_mandanten_dir()
    items = [d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(items)

def load_mandant_config(mandant_path, mandant_name):
    """Lade Stammdaten aus mandant_config.json"""
    config_path = os.path.join(mandant_path, "mandant_config.json")
    
    # Default Fallback
    config = {
        "firma": mandant_name,
        "adresse": {"strasse": "", "ort": ""},
        "geschaeftsfuehrer": "",
        "bank": {"iban": "", "bic": "", "name": ""},
        "logo": None
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception as e:
            print(f"⚠️  Fehler beim Laden der mandant_config.json: {e}")
            
    return config

def load_kunden(mandant_path):
    csv_path = os.path.join(mandant_path, "kunden.csv")
    kunden = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)
                if rows and rows[0][0] == "Firma": 
                    rows = rows[1:]
                
                for row in rows:
                    if len(row) >= 1:
                        kunden.append({
                            'firma': row[0],
                            'email': row[1] if len(row) > 1 else "",
                            'anrede': row[2] if len(row) > 2 else ""
                        })
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen der CSV: {e}")
    return kunden

def get_and_increment_counter(mandant_path):
    counter_file = os.path.join(mandant_path, "counter.json")
    current_year = datetime.date.today().year
    data = {"year": current_year, "count": 0}
    
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
            
    if data.get("year") != current_year:
        data["year"] = current_year
        data["count"] = 1
    else:
        data["count"] = data.get("count", 0) + 1
        
    try:
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️  Fehler beim Speichern des Counters: {e}")
        
    return f"{current_year}-{data['count']:03d}"

def create_pdf(invoice_data, mandant_path, mandant_config, kunde_data):
    """Erstellt PDF mit Logo und Stammdaten."""
    
    # 1. Zielordner: Mandanten/[Mandant]/Rechnungen/[Kunde]/
    kunde_safe = re.sub(r'[^\w\-_]', '_', kunde_data['firma'])
    save_dir = os.path.join(mandant_path, "Rechnungen", kunde_safe)
    
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            print(f"❌ Fehler beim Erstellen des Ordners: {e}")
            return False

    # 2. Dateiname
    datum_safe = invoice_data['datum'].replace('.', '-')
    nr_safe = re.sub(r'[^\w\-]', '_', invoice_data['nummer'])
    filename = os.path.join(save_dir, f"{datum_safe}_Rechnung_{nr_safe}.pdf")

    # 3. PDF Generierung
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()
        
        # --- HEADER BEREICH (Logo rechts, Absender links) ---
        
        # Logo Check
        logo_path = None
        if mandant_config.get("logo"):
            p_logo = os.path.join(mandant_path, mandant_config["logo"])
            if os.path.exists(p_logo):
                logo_path = p_logo

        if logo_path:
            # Logo Placement using Table to align right
            im = ReportLabImage(logo_path, width=5*cm, height=2.5*cm, kind='proportional')
            im.hAlign = 'RIGHT'
            logo_table = Table([[im]], colWidths=[17*cm])
            logo_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
            story.append(logo_table)
            story.append(Spacer(1, 0.5*cm))
        else:
            story.append(Spacer(1, 1*cm))

        # Absender (Klein über Empfänger oder oben links)
        m_adr = mandant_config.get('adresse', {})
        firmen_block = f"{mandant_config.get('firma', '')}<br/>{m_adr.get('strasse', '')}<br/>{m_adr.get('ort', '')}"
        
        story.append(Paragraph(firmen_block, styles['Normal']))
        story.append(Spacer(1, 1.5*cm))
        
        # Empfänger
        empf_text = f"An:\n{kunde_data['firma']}\n{kunde_data['anrede']}"
        story.append(Paragraph(empf_text.replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 1.5*cm))
        
        # Titel & Datum
        story.append(Paragraph(f"Rechnung {invoice_data['nummer']}", styles['Heading1']))
        story.append(Paragraph(f"Datum: {invoice_data['datum']}", styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # --- POSITIONEN ---
        table_data = [['Beschreibung', 'Betrag (Netto)']]
        total = 0.0
        
        for item in invoice_data['items']:
            desc = item['beschreibung']
            price = item['betrag']
            total += price
            table_data.append([desc, f"{price:.2f} €"])
            
        mwst = total * 0.19
        brutto = total + mwst
        
        table_data.append(['', ''])
        table_data.append(['Netto:', f"{total:.2f} €"])
        table_data.append(['MwSt 19%:', f"{mwst:.2f} €"])
        table_data.append(['Gesamtbetrag:', f"{brutto:.2f} €"])
        
        t = Table(table_data, colWidths=[12*cm, 4*cm])
        ts = [
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ]
        t.setStyle(TableStyle(ts))
        story.append(t)
        
        # --- FOOTER ---
        story.append(Spacer(1, 2*cm))
        
        bank = mandant_config.get('bank', {})
        footer_info = (
            f"Bitte überweisen Sie den Betrag innerhalb von 14 Tagen.<br/><br/>"
            f"<b>Geschäftsführer:</b> {mandant_config.get('geschaeftsfuehrer', '')} | "
            f"<b>Bank:</b> {bank.get('name', '')} | "
            f"<b>IBAN:</b> {bank.get('iban', '')} | "
            f"<b>BIC:</b> {bank.get('bic', '')}"
        )
        
        story.append(Paragraph(footer_info, styles['Normal']))
        
        doc.build(story)
        print(f"\n✅ PDF erfolgreich erstellt!")
        print(f"📂 Pfad: {filename}")

        # --- UMSATZ VERBUCHEN ---
        try:
            einnahmen_path = os.path.join(mandant_path, "einnahmen.csv")
            file_exists = os.path.exists(einnahmen_path)
            
            # Beschreibungen zusammenfügen und bereinigen
            desc_list = [i['beschreibung'] for i in invoice_data['items']]
            full_desc = ", ".join(desc_list)
            full_desc = full_desc.replace(";", " ") # Semikolon entfernen für CSV Sicherheit
            
            with open(einnahmen_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Header schreiben, falls Datei neu
                if not file_exists:
                    writer.writerow(["Rechnungsnummer", "Datum", "Kunde", "Beschreibung", "Betrag_Netto", "Betrag_Brutto"])
                
                # Daten schreiben
                writer.writerow([
                    invoice_data['nummer'], 
                    invoice_data['datum'], 
                    kunde_data['firma'],
                    full_desc,
                    f"{total:.2f}", 
                    f"{brutto:.2f}"
                ])
                
            print(f"✅ Umsatz in einnahmen.csv verbucht.")
            
        except Exception as e:
            print(f"⚠️  Fehler beim Verbuchen des Umsatzes: {e}")

        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der PDF-Erstellung: {e}")
        return False

def main():
    clear_screen()
    print("📝 RECHNUNGS-GENERATOR (Agency Pro)")
    print("===================================")
    
    # 1. Mandant
    mandanten = list_mandanten()
    if not mandanten:
        print("⚠️  Keine Mandanten gefunden.")
        return

    print("Bitte Mandant wählen (Auftraggeber):")
    for i, m in enumerate(mandanten, 1):
        print(f"[{i}] {m}")
        
    c = input("\nAuswahl: ").strip()
    if not c.isdigit(): return
    idx = int(c) - 1
    if not (0 <= idx < len(mandanten)): return
    
    selected_mandant_name = mandanten[idx]
    mandant_path = os.path.join(MANDANTEN_DIR, selected_mandant_name)
    
    # Lade Config
    mandant_config = load_mandant_config(mandant_path, selected_mandant_name)
    print(f"👉 Gewählt: {mandant_config.get('firma')}")
    print("-" * 30)
    
    # 2. Kunde
    kunden = load_kunden(mandant_path)
    if not kunden:
        print(f"⚠️  Keine Kunden gefunden.")
        return
        
    print(f"Bitte Kunde wählen (Empfänger):")
    for i, k in enumerate(kunden, 1):
        print(f"[{i}] {k['firma']}")
        
    c = input("\nAuswahl: ").strip()
    if not c.isdigit(): return
    idx = int(c) - 1
    if not (0 <= idx < len(kunden)): return
    
    selected_kunde = kunden[idx]
    print(f"👉 Gewählt: {selected_kunde['firma']}")
    print("-" * 30)
    
    # 3. Positionen
    items = []
    print("\n📦 Positionen eingeben:")
    while True:
        desc = input("   Beschreibung: ").strip()
        if not desc: break
        try:
            amt_s = input("   Betrag (Netto): ").replace(',', '.')
            if not amt_s: break
            amt = float(amt_s)
            items.append({'beschreibung': desc, 'betrag': amt})
        except ValueError:
            print("❌ Ungültig.")
            
    if not items: return
        
    # 4. Auto-Nummer
    print("\n🤖 Generiere Rechnungsnummer...")
    inv_nr = get_and_increment_counter(mandant_path)
    print(f"👉 Automatische Nummer: {inv_nr}")
    
    # 5. Generieren
    today = datetime.date.today().strftime("%d.%m.%Y")
    data = {
        'nummer': inv_nr,
        'datum': today,
        'items': items
    }
    
    create_pdf(data, mandant_path, mandant_config, selected_kunde)
    input("\n[Enter] zum Beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")
