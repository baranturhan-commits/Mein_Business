import os
import sys
import json
import datetime
import shutil

# Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR) # backend/
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# Import Utils
sys.path.append(BASE_DIR)
import excel_utils

# Try Import ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
except ImportError:
    print("❌ ReportLab fehlt! Bitte 'pip install reportlab' ausführen.")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_mandanten():
    if not os.path.exists(MANDANTEN_DIR): return []
    return sorted([d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))])

def load_kunden(mandant_path):
    xlsx_path = os.path.join(mandant_path, "Kunden", "kunden.xlsx")
    if os.path.exists(xlsx_path):
        return excel_utils.read_data(xlsx_path, "Kunden")
    return []

def get_next_offer_number(mandant_path):
    # Format: AN-YYYY-Nr (z.B. AN-2025-001)
    # Read from Excel to find max
    angebote_dir = os.path.join(mandant_path, "Angebote")
    xlsx_path = os.path.join(angebote_dir, "angebote.xlsx")
    
    current_year = datetime.datetime.now().year
    prefix = f"AN-{current_year}-"
    max_num = 0
    
    if os.path.exists(xlsx_path):
        data = excel_utils.read_data(xlsx_path, "Angebote")
        for row in data:
            nr = str(row.get('Angebotsnummer', ''))
            if nr.startswith(prefix):
                try:
                    num_part = int(nr.split('-')[-1])
                    if num_part > max_num: max_num = num_part
                except: pass
                
    return f"{prefix}{max_num + 1:03d}"

# --- PDF GENERATION (Copying style from Invoice mostly) ---
def create_pdf(mandant_name, offer_data, items):
    mandant_path = os.path.join(MANDANTEN_DIR, mandant_name)
    angebote_dir = os.path.join(mandant_path, "Angebote")
    if not os.path.exists(angebote_dir): os.makedirs(angebote_dir)
    
    filename = os.path.join(angebote_dir, f"{offer_data['nummer']}.pdf")
    
    # Load Mandant Config
    config = {}
    try:
        with open(os.path.join(mandant_path, "mandant_config.json"), 'r', encoding='utf-8') as f:
            config = json.load(f)
    except: pass
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # --- HEADER ---
    # Logo
    if config.get('logo_path'):
        logo_file = os.path.join(mandant_path, os.path.basename(config['logo_path']))
        if os.path.exists(logo_file):
            try:
                c.drawImage(logo_file, 20*mm, height - 45*mm, width=50*mm, preserveAspectRatio=True, mask='auto')
            except: pass
            
    # Sender Info (Top Right)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 20*mm, height - 30*mm, config.get('firma', mandant_name))
    c.drawRightString(width - 20*mm, height - 35*mm, f"{config.get('strasse', '')}")
    c.drawRightString(width - 20*mm, height - 40*mm, f"{config.get('plz', '')} {config.get('ort', '')}")
    c.drawRightString(width - 20*mm, height - 45*mm, f"Email: {config.get('email', '')}")

    # --- TITLE ---
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20*mm, height - 70*mm, "ANGEBOT")
    
    c.setFont("Helvetica", 12)
    c.drawString(20*mm, height - 80*mm, f"Angebots-Nr.: {offer_data['nummer']}")
    c.drawString(20*mm, height - 86*mm, f"Datum: {offer_data['datum']}")
    
    # --- RECIPIENT ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, height - 100*mm, offer_data['kunde_firma'])
    # Add address if available in future
    
    # --- TABLE HEADERS ---
    y = height - 120*mm
    c.line(20*mm, y+2*mm, width-20*mm, y+2*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, "Pos")
    c.drawString(30*mm, y, "Beschreibung")
    c.drawRightString(160*mm, y, "Menge")
    c.drawRightString(190*mm, y, "Gesamt")
    c.line(20*mm, y-2*mm, width-20*mm, y-2*mm)
    
    y -= 10*mm
    c.setFont("Helvetica", 10)
    
    total = 0.0
    
    for i, item in enumerate(items, 1):
        desc = item['beschreibung']
        qty = float(item['menge'])
        price = float(item['preis'])
        row_total = qty * price
        total += row_total
        
        c.drawString(20*mm, y, str(i))
        c.drawString(30*mm, y, desc)
        c.drawRightString(160*mm, y, f"{qty:.2f} x {price:.2f} €")
        c.drawRightString(190*mm, y, f"{row_total:.2f} €")
        
        y -= 8*mm
        if y < 30*mm:
            c.showPage()
            y = height - 30*mm

    # --- TOTAL ---
    y -= 5*mm
    c.line(130*mm, y+2*mm, 190*mm, y+2*mm)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(130*mm, y, "Netto:")
    c.drawRightString(190*mm, y, f"{total:.2f} €")
    
    mwst = total * 0.19
    brutto = total + mwst
    
    y -= 6*mm
    c.setFont("Helvetica", 10)
    c.drawString(130*mm, y, "MwSt 19%:")
    c.drawRightString(190*mm, y, f"{mwst:.2f} €")
    
    y -= 8*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(130*mm, y, "Gesamt:")
    c.drawRightString(190*mm, y, f"{brutto:.2f} €")
    
    # --- FOOTER ---
    c.setFont("Helvetica", 8)
    footer_text = f"Geschäftsführer: {config.get('geschaeftsfuehrer', '')} | Bank: {config.get('bank', '')} | IBAN: {config.get('iban', '')}"
    c.drawCentredString(width/2, 10*mm, footer_text)
    
    c.save()
    return filename, total, brutto

def main():
    clear_screen()
    print("📝 NEUES ANGEBOT ERSTELLEN")
    print("=========================")
    
    mandanten = list_mandanten()
    if not mandanten: return
    
    print("Mandant wählen:")
    for i, m in enumerate(mandanten, 1): print(f"[{i}] {m}")
    try:
        idx = int(input("\nAuswahl: ")) - 1
        mandant = mandanten[idx]
    except: return
    
    mandant_path = os.path.join(MANDANTEN_DIR, mandant)
    kunden = load_kunden(mandant_path)
    
    print(f"\nKunde wählen (für {mandant}):")
    if not kunden:
        print("❌ Keine Kunden gefunden. Bitte erst Kunden anlegen.")
        return
        
    for i, k in enumerate(kunden, 1):
        print(f"[{i}] {k['Firma']}")
        
    try:
        k_idx = int(input("\nAuswahl: ")) - 1
        kunde = kunden[k_idx]
    except: return
    
    print("\n📦 Positionen eingeben (leer lassen zum Beenden):")
    items = []
    while True:
        desc = input("Beschreibung: ").strip()
        if not desc: break
        while True:
            val_s = input("Menge/Stunden: ").strip().replace(',', '.')
            try: 
                qty = float(val_s)
                break
            except: print("❌ Bitte eine Zahl eingeben.")
            
        while True:
            val_p = input("Einzelpreis: ").strip().replace(',', '.')
            try:
                price = float(val_p)
                break
            except: print("❌ Bitte eine Zahl eingeben.")
            
        items.append({'beschreibung': desc, 'menge': qty, 'preis': price})
            
    if not items: return
    
    # Generate
    offer_num = get_next_offer_number(mandant_path)
    datum = datetime.date.today().strftime("%d.%m.%Y")
    
    offer_data = {
        'nummer': offer_num,
        'datum': datum,
        'kunde_firma': kunde['Firma']
    }
    
    print("\n⚙️  Erstelle PDF...")
    pdf_path, net_total, gross_total = create_pdf(mandant, offer_data, items)
    
    # Save to Excel
    xlsx_path = os.path.join(mandant_path, "Angebote", "angebote.xlsx")
    
    # We save items as JSON string or simpler summary?
    # For protocol workflow, detailed items are needed.
    # We will save basic info in angebote.xlsx and detailed items need storage?
    # Option: Save details in a separate sheet or simplify.
    # Better: Save items as a pipe-separated string or generic text for now.
    # Wait, the prompt says "Rechnung anhand Lieferschein erstellen". 
    # The Lieferschein needs to know the items.
    # Ideally we save items in a structured way.
    # Let's save a "Details" column with rudimentary JSON.
    
    item_str = json.dumps(items)
    
    row = {
        'Angebotsnummer': offer_num,
        'datum': datum,
        'Kunde': kunde['Firma'],
        'Netto': net_total,
        'Brutto': gross_total,
        'Status': 'Offen', # Offen, Angenommen, Abgelehnt
        'Items': item_str # Hidden detail col
    }
    
    headers = ['Angebotsnummer', 'datum', 'Kunde', 'Netto', 'Brutto', 'Status', 'Items']
    excel_utils.append_data(xlsx_path, row, "Angebote", headers)
    
    print(f"\n✅ Angebot {offer_num} erstellt!")
    print(f"📄 PDF: {pdf_path}")
    print(f"💾 Excel: {xlsx_path}")
    input("\n[Enter] weiter...")

if __name__ == "__main__":
    main()
