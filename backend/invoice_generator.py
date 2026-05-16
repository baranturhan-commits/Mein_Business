import os
import sys
import excel_utils
import csv
import datetime
import re
import json

def clean_text(text):
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
    text = text.replace('\u25A0', ' ')
    return text

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Valid for scripts in backend root:
BASE_DIR = SCRIPT_DIR 
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


import shutil # Important for migration

def load_kunden(mandant_path):
    kunden_dir = os.path.join(mandant_path, "Kunden")
    xlsx_path = os.path.join(kunden_dir, "kunden.xlsx")
    
    kunden = []
    if os.path.exists(xlsx_path):
        data = excel_utils.read_data(xlsx_path, "Kunden")
        for row in data:
            kunden.append({
                'firma': row.get('Firma', ''),
                'email': row.get('Email', ''),
                'anrede': row.get('Anrede', '')
            })
            
    # Fallback to CSV if XL missing? No, we migrate.
    return kunden

def get_and_increment_counter(mandant_path, mandant_config=None):
    counter_file = os.path.join(mandant_path, "counter.json")
    today = datetime.date.today()
    current_year = str(today.year)
    current_month = f"{today.month:02d}"
    
    # Get Mandantennummer
    mandanten_nr = "000"
    if mandant_config:
         mandanten_nr = mandant_config.get('mandantennummer', '000')
    if mandanten_nr == "000":
         # Try load if not provided
         c_path = os.path.join(mandant_path, "mandant_config.json")
         if os.path.exists(c_path):
             try:
                 with open(c_path, 'r', encoding='utf-8') as f:
                     cfg = json.load(f)
                     mandanten_nr = cfg.get('mandantennummer', '000')
             except: pass
    
    data = {"year": current_year, "month": current_month, "count": 0}
    
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
            
    # Reset if changed
    if (str(data.get("year")) != current_year) or (str(data.get("month")) != current_month):
        data["year"] = current_year
        data["month"] = current_month
        data["count"] = 1
    else:
        data["count"] = data.get("count", 0) + 1
        
    try:
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️  Fehler beim Speichern des Counters: {e}")
        
    return f"RE-{mandanten_nr}-{current_year}-{current_month}-{data['count']:03d}"

def create_pdf(invoice_data, mandant_path, mandant_config, kunde_data):
    """Erstellt PDF mit neuem Layout (Logo rechts, Info-Block, 6-Spalten Tabelle)."""
    
    # 1. Zielordner: Mandanten/[Mandant]/Rechnungen/[Kunde]/
    # Clean Filename
    kunde_safe = re.sub(r'[^\w\-_]', '_', kunde_data.get('firma', 'Unbekannt'))
    save_dir = os.path.join(mandant_path, "Rechnungen", kunde_safe)
    
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            print(f"❌ Fehler beim Erstellen des Ordners: {e}")
            return False

    # 2. Dateiname
    nr_safe = re.sub(r'[^\w\-]', '_', invoice_data['nummer'])
    filename = os.path.join(save_dir, f"{nr_safe}.pdf")

    # 3. PDF Generierung
    try:
        # Custom Page Template for Footer using Canvas
        def add_footer(canvas, doc):
            canvas.saveState()
            
            # Footer Configuration
            footer_y = 2 * cm
            
            # Draw Line
            canvas.setStrokeColor(colors.lightgrey)
            canvas.setLineWidth(0.5)
            canvas.line(2*cm, footer_y + 1.5*cm, A4[0]-2*cm, footer_y + 1.5*cm)
            
            # Content
            styles = getSampleStyleSheet()
            style_footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.grey)
            
            # Column 1: Company & Address
            m_adr = mandant_config.get('adresse', {})
            col1 = [
                f"<b>{mandant_config.get('firma', '')}</b>",
                m_adr.get('strasse', ''),
                m_adr.get('ort', ''),
                f"Tel: {mandant_config.get('telefon', '-')}" if mandant_config.get('telefon') else "",
                f"Email: {mandant_config.get('email', '-')}" if mandant_config.get('email') else "",
            ]
            
            # Column 2: Bank
            bank = mandant_config.get('bank', {})
            col2 = [
                "<b>Bankverbindung</b>",
                f"Bank: {bank.get('name', '-')}",
                f"IBAN: {bank.get('iban', '-')}",
                f"BIC: {bank.get('bic', '-')}",
            ]
            
            # Column 3: Legal / Tax
            ustid = mandant_config.get('ustid', '').strip()
            steuernummer = mandant_config.get('steuernummer', '').strip()

            tax_string = ""
            if ustid:
                tax_string = f"USt-ID: {ustid}"
            elif steuernummer:
                tax_string = f"Steuer-Nr: {steuernummer}"
                
            col3 = [
                f"<b>Geschäftsführer:</b>",
                mandant_config.get('geschaeftsfuehrer', '-'),
                tax_string,
                "Gerichtsstand: " + (m_adr.get('ort', '').split(' ')[1] if ' ' in m_adr.get('ort', '') else m_adr.get('ort', ''))
            ]
            
            # Render Columns
            # Col 1
            t1 = Paragraph("<br/>".join([c for c in col1 if c]), style_footer)
            w1, h1 = t1.wrap(5*cm, 5*cm)
            t1.drawOn(canvas, 2*cm, footer_y + 1.2*cm - h1)
            
            # Col 2
            t2 = Paragraph("<br/>".join([c for c in col2 if c]), style_footer)
            w2, h2 = t2.wrap(5*cm, 5*cm)
            t2.drawOn(canvas, 8*cm, footer_y + 1.2*cm - h2)
            
            # Col 3
            t3 = Paragraph("<br/>".join([c for c in col3 if c]), style_footer)
            w3, h3 = t3.wrap(5*cm, 5*cm)
            t3.drawOn(canvas, 14*cm, footer_y + 1.2*cm - h3)
            
            # Page Number
            page_num = canvas.getPageNumber()
            text = "Seite %d" % page_num
            canvas.drawRightString(20*cm, footer_y, text) # 1cm from bottom
            
            canvas.restoreState()

        doc = SimpleDocTemplate(filename, pagesize=A4, 
                              rightMargin=2*cm, leftMargin=2*cm, 
                              topMargin=1*cm, bottomMargin=4*cm) # More bottom margin for footer
        story = []
        styles = getSampleStyleSheet()
        
        # Define Custom Styles
        style_right = ParagraphStyle('RightAlign', parent=styles['Normal'], alignment=2)
        style_header_small = ParagraphStyle('HeaderSmall', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')
        style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=9, wordWrap='CJK', fontName='Helvetica')
        
        # --- HEADER (Logo Right) ---
        logo_path = None
        if mandant_config.get("logo"):
            p_logo = os.path.join(mandant_path, mandant_config["logo"])
            if os.path.exists(p_logo):
                logo_path = p_logo

        # Top Spacer
        story.append(Spacer(1, 1*cm))

        # Logo Row
        if logo_path:
            im = ReportLabImage(logo_path, width=6*cm, height=3*cm, kind='proportional')
            im.hAlign = 'RIGHT'
            # Table to force right alignment reliably
            # Col 1: Empty, Col 2: Logo
            logo_table = Table([['', im]], colWidths=[10*cm, 7*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(logo_table)
        else:
            story.append(Spacer(1, 2*cm))
            
        story.append(Spacer(1, 1*cm))
        
        # --- ADDRESS & INFO BLOCK ---
        # Left: Sender (Small) + Recipient
        # Right: Info Block (Rechnung Nr, Datum, etc.)
        
        # Left Content
        m_adr = mandant_config.get('adresse', {})
        sender_line = f"{mandant_config.get('firma', '')} · {m_adr.get('strasse', '')} · {m_adr.get('ort', '')}"
        
        recipient = [
            Paragraph(f"<u>{sender_line}</u>", style_header_small),
            Spacer(1, 0.5*cm),
            Paragraph(kunde_data.get('anrede', ''), styles['Normal']),
            Paragraph(f"<b>{kunde_data.get('firma', '')}</b>", styles['Normal']),
            Paragraph(kunde_data.get('adresse', ''), styles['Normal']) if kunde_data.get('adresse') else Spacer(1,0),
        ]
        
        # Right Content (Info Block)
        # Format dates
        datum = invoice_data.get('datum', datetime.date.today().strftime('%d.%m.%Y'))
        l_von = invoice_data.get('leistungs_von', '')
        l_bis = invoice_data.get('leistungs_bis', '')
        
        # "Leistungszeitraum" Logic
        l_datum_text = datum # Default to invoice date if no period
        if l_von and l_bis:
            if l_von == l_bis:
                 l_datum_text = l_von
            else:
                 l_datum_text = f"{l_von} bis {l_bis}"
        elif l_von:
            l_datum_text = f"ab {l_von}"
        elif l_bis:
            l_datum_text = f"bis {l_bis}"
            
        
        info_data = [
            ['Rechnung Nr.:', invoice_data['nummer']],
            ['Kundennummer:', kunde_data.get('kundennummer', 'K-0000')], # Fallback if not in data
            ['Rechnungsdatum:', datum],
            ['Leistungsz.:', l_datum_text],
            ['Sachbearbeiter:', mandant_config.get('geschaeftsfuehrer', '')] # Or specific user
        ]
        
        # Create Info Table
        info_table = Table(info_data, colWidths=[3.5*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEADING', (0,0), (-1,-1), 12),
        ]))
        
        # Layout Table for Address (Left) and Info (Right)
        
        layout_data = [[recipient, info_table]]
        layout_table = Table(layout_data, colWidths=[10*cm, 7.5*cm])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        story.append(layout_table)
        story.append(Spacer(1, 1.5*cm))
        
        # --- TITLE ---
        story.append(Paragraph(f"<b>Rechnung</b>", ParagraphStyle('TitleBold', parent=styles['Heading1'], fontSize=16)))
        story.append(Spacer(1, 0.2*cm))
        # Optional Subject/Project line
        if invoice_data.get('betreff'):
             story.append(Paragraph(f"<b>{invoice_data['betreff']}</b>", styles['Normal']))
        else:
             pass
             
        story.append(Spacer(1, 0.8*cm))
        
        # --- ITEM TABLE (6 Columns) ---
        # Pos | Menge | Einh. | Bezeichnung | E-Preis | Gesamt
        
        table_header = ['Pos.', 'Menge', 'Einh.', 'Bezeichnung', 'E-Preis', 'Gesamt']
        table_data = [table_header]
        
        total_netto = 0.0
        
        for i, item in enumerate(invoice_data.get('items', []), 1):
            # Parse values. Expected: dict with structured data. 
            
            try:
                menge = float(item.get('menge', 1))
                einheit = clean_text(item.get('einheit', 'Stk'))
                bezeichnung = clean_text(item.get('beschreibung', '')) # Or 'bezeichnung'
                
                if 'einzelpreis' in item:
                    ep = float(item['einzelpreis'])
                    gesamt = menge * ep
                else:
                    # Fallback old style
                    gesamt = float(item.get('betrag', 0))
                    ep = gesamt / menge if menge else 0
                
                total_netto += gesamt
                
                # Format
                row = [
                    str(i),
                    f"{menge:.2f}".replace('.', ','),
                    einheit,
                    Paragraph(bezeichnung, style_table_cell), # Allow wrapping
                    f"{ep:.2f}".replace('.', ','),
                    f"{gesamt:.2f}".replace('.', ',')
                ]
                table_data.append(row)
                
            except Exception as e:
                print(f"Error parsing item {item}: {e}")
                continue
                
        # --- TOTALS BLOCK ---
        mwst_satz = 0.19 # Configurable?
        
        # Check for Kleingewerbe
        is_kleingewerbe = mandant_config.get('unternehmensform') == 'Kleingewerbe'
        if is_kleingewerbe:
            mwst_satz = 0.0

        mwst = total_netto * mwst_satz
        brutto = total_netto + mwst
        
        table_data.append(['', '', '', '', '', '']) # Spacer Line
        
        # Styles for Table
        col_widths = [1.87*cm, 1.87*cm, 1.87*cm, 7.65*cm, 1.87*cm, 1.87*cm]
        
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        t_styles = [
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Header Bold
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (2,-1), 'CENTER'), # Pos, Menge, Einh Center
            ('ALIGN', (3,0), (3,-1), 'LEFT'),   # Desc Left
            ('ALIGN', (4,0), (-1,-1), 'RIGHT'), # Prices Right
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.black), # Line under Header
            ('LINEBELOW', (0,-2), (-1,-2), 0.5, colors.grey), # Line above empty row (spacer)
        ]
        
        t.setStyle(TableStyle(t_styles))
        story.append(t)
        
        # Summary Block
        
        summary_data = [
            ['Summe netto', f"{total_netto:.2f}".replace('.', ',')]
        ]
        
        if is_kleingewerbe:
            summary_data.append(['Umsatzsteuer 0%', f"{mwst:.2f}".replace('.', ',')])
            summary_data.append(['Gesamtsumme €', f"{brutto:.2f}".replace('.', ',')])
        else:
            summary_data.append([f'Umsatzsteuer {int(mwst_satz*100)}%', f"{mwst:.2f}".replace('.', ',')])
            summary_data.append(['Gesamtsumme €', f"{brutto:.2f}".replace('.', ',')])
        
        st = Table(summary_data, colWidths=[3.5*cm, 2.5*cm])
        st.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,-1), 'RIGHT'), # Numbers Right
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Total Bold
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black), # Line above Total
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black), # Double line? Just one for now
            ('LEADING', (0,0), (-1,-1), 12),
        ]))
        
        # Container to push to right
        ct = Table([['', st]], colWidths=[11*cm, 6*cm])
        ct.setStyle(TableStyle([
             ('ALIGN', (1,0), (1,0), 'RIGHT'),
             ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        story.append(Spacer(1, 0.2*cm))
        story.append(ct)
        
        # --- PAYMENT TERMS ---
        story.append(Spacer(1, 1.5*cm))
        # Date + 14 days
        try:
             d_obj = datetime.datetime.strptime(datum, '%d.%m.%Y')
        except:
             d_obj = datetime.date.today()
             
        due_date = d_obj + datetime.timedelta(days=14)
        due_str = due_date.strftime('%d.%m.%Y')
        
        terms_text = f"Der Rechnungsbetrag ist zahlbar bis zum <b>{due_str}</b> ohne Abzug."
        story.append(Paragraph(terms_text, styles['Normal']))
        
        if is_kleingewerbe:
            story.append(Paragraph("Gemäß § 19 UStG wird keine Umsatzsteuer ausgewiesen.", styles['Normal']))
        
        # Optional: Legal Text
        legal_text = "Bitte geben Sie bei der Überweisung immer die Rechnungsnummer an."
        story.append(Paragraph(legal_text, styles['Normal']))

        # Build Data
        doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
        print(f"\n✅ PDF erfolgreich erstellt!")
        print(f"📂 Pfad: {filename}")

        # --- UMSATZ VERBUCHEN (EXCEL) ---
        try:
            einnahmen_dir = os.path.join(mandant_path, "Einnahmen")
            if not os.path.exists(einnahmen_dir): os.makedirs(einnahmen_dir, exist_ok=True)
            
            xlsx_path = os.path.join(einnahmen_dir, "einnahmen.xlsx")

            # Beschreibungen zusammenfügen
            # New structure: items have 'beschreibung'
            desc_list = [i.get('beschreibung', '') for i in invoice_data.get('items', [])]
            full_desc = ", ".join(desc_list)
            
            data_row = {
                "Rechnungsnummer": invoice_data['nummer'],
                "Datum": invoice_data['datum'],
                "Kunde": kunde_data.get('firma', 'Unbekannt'),
                "Beschreibung": full_desc,
                "Betrag_Netto": f"{total_netto:.2f}",
                "Betrag_Brutto": f"{brutto:.2f}",
                "Status": "Offen"
            }
            
            headers = ["Rechnungsnummer", "Datum", "Kunde", "Beschreibung", "Betrag_Netto", "Betrag_Brutto", "Status"]
            excel_utils.append_data(xlsx_path, data_row, "Einnahmen", headers)
                
            print(f"✅ Umsatz in Einnahmen/einnahmen.xlsx verbucht.")
            
        except Exception as e:
            print(f"⚠️  Fehler beim Verbuchen des Umsatzes: {e}")

        return filename
        
    except Exception as e:
        print(f"❌ Fehler bei der PDF-Erstellung: {e}")
        return None

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
    
    # 3. Modus: Manuell oder Lieferschein
    print("\nModus wählen:")
    print("[1] Manuelle Eingabe")
    print("[2] Aus Lieferschein übernehmen")
    mode = input("Auswahl: ").strip()
    
    items = []
    lieferschein_ref = ""
    
    if mode == '2':
        # Load Open Delivery Notes
        ls_xlsx = os.path.join(mandant_path, "Lieferscheine", "lieferscheine.xlsx")
        available = []
        if os.path.exists(ls_xlsx):
            all_ls = excel_utils.read_data(ls_xlsx, "Lieferscheine")
            # Only exact customer match? Or show all open?
            # Better show only for selected customer to avoid errors
            available = [l for l in all_ls if l.get('Status') == 'Offen' and l.get('Kunde') == selected_kunde['firma']]
            
        if not available:
            print("❌ Keine offenen Lieferscheine für diesen Kunden gefunden.")
            return
            
        print("\nOffene Lieferscheine:")
        for i, l in enumerate(available, 1):
             print(f"[{i}] {l.get('Lieferscheinnummer')} | {l.get('Datum')}")
             
        try:
            ls_idx = int(input("Wahl: ")) - 1
            sel_ls = available[ls_idx]
            lieferschein_ref = sel_ls.get('Lieferscheinnummer')
            
            import json
            raw = sel_ls.get('Items', '[]')
            ls_items = json.loads(raw)
            
            print(f"\nPreise für {len(ls_items)} Positionen festlegen:")
            print("-" * 30)
            
            for i, it in enumerate(ls_items, 1):
                desc_text = it['beschreibung']
                qty = float(it['menge'])
                
                print(f"\nPos {i}: {desc_text}")
                print(f"Menge: {qty}")
                
                # Preis abfragen (Standard = 0 oder Wert aus LS falls vorhanden)
                default_price = float(it.get('preis', 0.0))
                
                while True:
                    p_in = input(f"Einzelpreis (Netto) [Enter={default_price}]: ").strip().replace(',', '.')
                    if not p_in:
                        price = default_price
                        break
                    try:
                        price = float(p_in)
                        break
                    except: print("❌ Zahl erwartet.")
                
                # Summe
                line_total = price * qty
                
                # Format Description for Invoice: "5.0x Anfahrt (@ 50.0€)"
                # Or just Description? Usually invoice needs "Quantity | Description | Unit Price | Total"
                # But current create_pdf takes simple items list with 'betrag' as total?
                # Check create_pdf logic.
                # line 169: for item in items:
                #    desc = item['beschreibung']
                #    price = item['betrag'] (TOTAL)
                #    table_data.append([desc, f"{price:.2f} €"])
                
                # So we must format the description string to include details
                # because simple invoice generator doesn't split columns yet.
                final_desc = f"{qty}x {desc_text} (EP: {price:.2f}€)"
                
                items.append({
                    'beschreibung': final_desc,
                    'betrag': line_total
                })
                
            print(f"✅ Positionen übernommen.")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return
    else:
        # Manuell
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
    
    result = create_pdf(data, mandant_path, mandant_config, selected_kunde)
    
    if result:
        # Update Lieferschein if needed
        if mode == '2' and lieferschein_ref:
            ls_xlsx = os.path.join(mandant_path, "Lieferscheine", "lieferscheine.xlsx")
            excel_utils.update_status(ls_xlsx, "Lieferscheinnummer", lieferschein_ref, "Status", "Abgerechnet")
            print(f"✅ Lieferschein {lieferschein_ref} als 'Abgerechnet' markiert.")
            
    input("\n[Enter] zum Beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")
