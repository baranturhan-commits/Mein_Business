import os
import sys
import json
import datetime

# Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(BASE_DIR)
import excel_utils

# Try Import ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib import colors
except ImportError as e:
    print(f"❌ Fehler: das Modul 'reportlab' konnte nicht geladen werden.")
    print(f"Details: {e}")
    # print("Bitte installieren Sie es mit: pip install reportlab")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_mandanten():
    if not os.path.exists(MANDANTEN_DIR): return []
    return sorted([d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))])

def load_open_offers(mandant_path):
    xlsx = os.path.join(mandant_path, "Angebote", "angebote.xlsx")
    if os.path.exists(xlsx):
        return excel_utils.read_data(xlsx, "Angebote")
    return []

def get_next_delivery_number(mandant_path):
    # LS-YYYY-Nr
    d_dir = os.path.join(mandant_path, "Lieferscheine")
    xlsx = os.path.join(d_dir, "lieferscheine.xlsx")
    current_year = datetime.datetime.now().year
    prefix = f"LS-{current_year}-"
    max_num = 0
    if os.path.exists(xlsx):
        data = excel_utils.read_data(xlsx, "Lieferscheine")
        for row in data:
            nr = str(row.get('Lieferscheinnummer', ''))
            if nr.startswith(prefix):
                try:
                    p = int(nr.split('-')[-1])
                    if p > max_num: max_num = p
                except: pass
    return f"{prefix}{max_num+1:03d}"

def create_blank_protocol_pdf(mandant_path, mandant_name, data):
    d_dir = os.path.join(mandant_path, "Lieferscheine")
    if not os.path.exists(d_dir): os.makedirs(d_dir)
    filename = os.path.join(d_dir, f"{data['nummer']}.pdf")
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # --- STYLE SETUP ---
    # Colors matching image
    blue_color = colors.HexColor("#005b96") # Generic nice blue
    grey_bg = colors.HexColor("#e0e0e0")
    
    # --- TITLE ---
    c.setFillColor(blue_color)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 25*mm, "ABNAHMEPROTOKOLL")
    
    # --- HEADER BLOCK ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    
    start_y = height - 50*mm
    line_h = 8*mm
    label_x = 20*mm
    value_x = 60*mm
    box_w = 120*mm
    
    # Helper to draw row
    def draw_header_row(y, label, value):
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(label_x, y + 2*mm, label)
        
        # Grey Box
        c.setFillColor(grey_bg)
        c.rect(value_x, y, box_w, 6*mm, fill=1, stroke=0)
        
        # Value
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(value_x + 2*mm, y + 2*mm, value)

    draw_header_row(start_y, "Projekt", data.get('projekt', ''))
    draw_header_row(start_y - line_h, "Auftraggeber", data.get('kunde', ''))
    draw_header_row(start_y - 2*line_h, "Auftragnehmer", mandant_name)
    draw_header_row(start_y - 3*line_h, "Teilnehmer", "") # Leer lassen für Handschrift
    
    # Firmenlogo Platzhalter rechts
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawRightString(width - 20*mm, start_y - line_h, "Firmenlogo")
    
    # --- CHECKBOXES ---
    y_check = start_y - 4.5*line_h
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(label_x, y_check, "Art der Abnahme:")
    
    c.setFont("Helvetica", 10)
    c.drawString(value_x + 10*mm, y_check, "Gesamtabnahme")
    c.rect(value_x + 40*mm, y_check - 1*mm, 4*mm, 4*mm) # Box
    
    c.drawString(value_x + 70*mm, y_check, "Teilabnahme")
    c.rect(value_x + 100*mm, y_check - 1*mm, 4*mm, 4*mm) # Box
    
    # --- DATUM ---
    y_date = y_check - 10*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(label_x, y_date, "Datum:")
    
    # Grey Box for Date
    c.setFillColor(grey_bg)
    c.rect(value_x, y_date - 2*mm, 35*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.drawString(value_x + 2*mm, y_date, data.get('datum', ''))
    
    c.drawString(value_x + 40*mm, y_date, "von")
    c.setFillColor(grey_bg)
    c.rect(value_x + 50*mm, y_date - 2*mm, 20*mm, 6*mm, fill=1, stroke=0)
    
    c.setFillColor(colors.black)
    c.drawString(value_x + 75*mm, y_date, "bis")
    c.setFillColor(grey_bg)
    c.rect(value_x + 85*mm, y_date - 2*mm, 20*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.drawString(value_x + 110*mm, y_date, "Uhr")

    # --- TABELLE ---
    y_table = y_date - 15*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(label_x, y_table + 5*mm, "Abnahmepunkte / Prüfpunkte")
    
    # Headers
    headers = ["Gewerk", "Beschreibung (Mängel / Restarbeiten)", "ok", "nok", "Bemerkung"]
    col_widths = [30*mm, 80*mm, 10*mm, 10*mm, 40*mm]
    x_positions = [label_x]
    for w in col_widths: x_positions.append(x_positions[-1] + w)
    
    # Header Row Background
    c.setFillColor(colors.dimgrey)
    c.rect(label_x, y_table, width - 40*mm, 8*mm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    # Draw Headers centered or left?
    c.drawString(x_positions[0]+2*mm, y_table + 2*mm, headers[0])
    c.drawString(x_positions[1]+2*mm, y_table + 2*mm, headers[1])
    c.drawString(x_positions[2]+1*mm, y_table + 2*mm, headers[2])
    c.drawString(x_positions[3]+1*mm, y_table + 2*mm, headers[3])
    c.drawString(x_positions[4]+2*mm, y_table + 2*mm, headers[4])
    
    # Lines
    c.setStrokeColor(colors.white)
    for x in x_positions[1:-1]:
        c.line(x, y_table, x, y_table + 8*mm)
        
    # --- EMPTY ROWS ---
    c.setStrokeColor(colors.white)
    row_h = 8*mm
    curr_y = y_table
    
    num_rows = 15
    for i in range(num_rows):
        curr_y -= row_h
        
        # Alternating bg? Image shows grey bg
        c.setFillColor(grey_bg)
        c.rect(label_x, curr_y, width - 40*mm, row_h, fill=1, stroke=1)
        
        # Grid lines white
        c.setStrokeColor(colors.white)
        c.setLineWidth(1)
        # Vertical lines
        for x in x_positions[1:-1]:
            c.line(x, curr_y, x, curr_y + row_h)
            
        # Numbering
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(label_x - 5*mm, curr_y + 2*mm, str(i+1))

    # --- SIGNATURES ---
    y_sig = 40*mm 
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    
    c.line(20*mm, y_sig, 90*mm, y_sig)
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y_sig - 5*mm, "Ort, Datum, Unterschrift Auftragnehmer")
    
    c.line(110*mm, y_sig, 180*mm, y_sig)
    c.drawString(110*mm, y_sig - 5*mm, "Ort, Datum, Unterschrift Auftraggeber")

    c.save()
    return filename

def main():
    clear_screen()
    print("🚚 ABNAHMEPROTOKOLL ERSTELLEN (BLANKO)")
    print("======================================")
    
    mandanten = list_mandanten()
    if not mandanten: return
    for i, m in enumerate(mandanten, 1): print(f"[{i}] {m}")
    try: idx = int(input("\nAuswahl: "))-1; mandant=mandanten[idx]
    except: return
    mandant_path = os.path.join(MANDANTEN_DIR, mandant)
    
    # Project Info
    print("\nModus:")
    print("[1] Mit Kunden-Verknüpfung (Aus Angebot)")
    print("[2] Direkt für Kunden (Liste)")
    mode = input("Auswahl: ")
    
    kunde_name = ""
    offer_ref = ""
    
    if mode == '1':
        offers = load_open_offers(mandant_path)
        if offers:
            for i, o in enumerate(offers, 1):
                print(f"[{i}] {o.get('Angebotsnummer')} | {o.get('Kunde')}")
            try: o_idx = int(input("Wahl: "))-1; sel_offer=offers[o_idx]
            except: return
            kunde_name = sel_offer.get('Kunde')
            offer_ref = sel_offer.get('Angebotsnummer')
        else:
            print("Keine Angebote gefunden.")
            return

    else:
        kunden = excel_utils.read_data(os.path.join(mandant_path, "Kunden", "kunden.xlsx"), "Kunden")
        if not kunden: print("Keine Kunden."); return
        for i,k in enumerate(kunden,1): print(f"[{i}] {k['Firma']}")
        try: k_idx=int(input("Kunde: "))-1; kunde_name=kunden[k_idx]['Firma']
        except: return
    
    # NO QUESTIONS ASKED LOOP
    
    # Save Logic
    ls_num = get_next_delivery_number(mandant_path)
    datum = datetime.date.today().strftime("%d.%m.%Y")
    
    print("\n⚙️  Erstelle Blanko-PDF...")
    pdf_path = create_blank_protocol_pdf(mandant_path, mandant, {
        'nummer': ls_num, 
        'datum': datum, 
        'kunde': kunde_name, 
        'projekt': "" # Left blank as requested ("den Rest soll er unausgefüllt lassen")
    })
    
    # Register in Excel (Empty Items)
    xlsx_path = os.path.join(mandant_path, "Lieferscheine", "lieferscheine.xlsx")
    row = {
        'Lieferscheinnummer': ls_num,
        'Datum': datum,
        'Kunde': kunde_name,
        'AngebotRef': offer_ref,
        'Status': 'Offen',
        'Items': '[]'
    }
    headers = ['Lieferscheinnummer', 'Datum', 'Kunde', 'AngebotRef', 'Status', 'Items']
    excel_utils.append_data(xlsx_path, row, "Lieferscheine", headers)
    
    print(f"\n✅ Protokoll {ls_num} erstellt!")
    print(f"📄 PDF: {pdf_path}")
    input("\n[Enter] weiter...")

if __name__ == "__main__":
    main()
