import os
import sys
import excel_utils
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

def get_and_increment_counter(mandant_path):
    counter_file = os.path.join(mandant_path, "counter.json")
    config_file = os.path.join(mandant_path, "mandant_config.json")
    
    # Load Mandant Nummer
    mandant_nr = "000"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                c = json.load(f)
                mandant_nr = c.get("mandant_nummer", "000")
        except: pass

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
        
    # Format: RE-[NR]-[YEAR]-[COUNT]
    return f"RE-{mandant_nr}-{current_year}-{data['count']:03d}"

def create_pdf(invoice_data, mandant_path, mandant_config, kunde_data):
    """Erstellt PDF im neuen 'Green Design'."""
    
    # 1. Zielordner & Dateiname
    kunde_safe = re.sub(r'[^\w\-_]', '_', kunde_data['firma'])
    save_dir = os.path.join(mandant_path, "Rechnungen", kunde_safe)
    
    if not os.path.exists(save_dir):
        try: os.makedirs(save_dir)
        except OSError: return False

    nr_safe = re.sub(r'[^\w\-]', '_', invoice_data['nummer'])
    filename = os.path.join(save_dir, f"{nr_safe}.pdf")

    # 2. Setup ReportLab
    try:
        # Colors
        ACCENT_COLOR = colors.HexColor("#2E8B57") # SeaGreen
        TEXT_COLOR = colors.HexColor("#333333")
        LINE_COLOR = colors.HexColor("#dddddd")

        doc = SimpleDocTemplate(filename, pagesize=A4, 
                                rightMargin=2*cm, leftMargin=2*cm, 
                                topMargin=1.5*cm, bottomMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        style_norm = styles['Normal']
        style_norm.fontName = 'Helvetica'
        style_norm.fontSize = 10
        style_norm.textColor = TEXT_COLOR
        
        style_bold = ParagraphStyle('Bold', parent=style_norm, fontName='Helvetica-Bold')
        style_small = ParagraphStyle('Small', parent=style_norm, fontSize=8, textColor=colors.grey)
        
        style_heading = ParagraphStyle('Heading', parent=styles['Heading1'], 
                                       fontName='Helvetica-Bold', fontSize=18, 
                                       textColor=TEXT_COLOR, spaceAfter=20)

        # --- HEADER (Logo Right, Sender Left) ---
        # Logo
        logo_img = []
        if mandant_config.get("logo"):
            p_logo = os.path.join(mandant_path, mandant_config["logo"])
            if os.path.exists(p_logo):
                im = ReportLabImage(p_logo, width=5*cm, height=2.5*cm, kind='proportional')
                im.hAlign = 'RIGHT'
                logo_img = [im]
        
        # Sender Address (Small Line)
        m_adr = mandant_config.get('adresse', {})
        sender_line = f"{mandant_config.get('firma', '')} · {m_adr.get('strasse', '')} · {m_adr.get('ort', '')}"
        
        # Header Layout: invisible table
        # Row 1: Logo (Right)
        # Row 2: Sender Line (Left)
        
        if logo_img:
            tbl_logo = Table([[logo_img[0]]], colWidths=[17*cm])
            tbl_logo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
            story.append(tbl_logo)
        else:
            story.append(Spacer(1, 2*cm))
            
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(sender_line, style_small))
        story.append(Spacer(1, 0.5*cm))

        # --- ADDRESS & INFO BLOCK ---
        # Left: Recipient
        kunde_text = f"{kunde_data['firma']}<br/>{kunde_data['anrede']}"
        p_kunde = Paragraph(kunde_text, style_bold)
        
        # Right: Metadata Block
        # Nummer, Kundennummer, Datum
        meta_data = [
            ["Nummer:", invoice_data['nummer']],
            ["Kundennummer:", "K-" + str(len(kunde_data['firma']))], # Dummy logic if no ID
            ["Datum:", invoice_data['datum']],
            ["Sachbearbeiter:", mandant_config.get('geschaeftsfuehrer', '')]
        ]
        
        tbl_meta = Table(meta_data, colWidths=[3.5*cm, 4*cm])
        tbl_meta.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TEXTCOLOR', (0,0), (-1,-1), TEXT_COLOR),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        
        # Combine Address and Meta in a Table
        tbl_layout = Table([[p_kunde, tbl_meta]], colWidths=[9*cm, 8*cm])
        tbl_layout.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(tbl_layout)
        
        story.append(Spacer(1, 1.5*cm))
        
        # --- TITLE ---
        story.append(Paragraph("Rechnung", style_heading))
        # Subject / Description line (optional first item desc?)
        if invoice_data.get('subject'):
             story.append(Paragraph(f"<b>{invoice_data['subject']}</b>", style_norm))
        story.append(Spacer(1, 0.5*cm))

        # --- ITEMS TABLE ---
        # Headers: Pos, Menge, Einbeit, Bezeichnung, E-Preis, Gesamt
        data = [['Pos', 'Menge', 'Einh.', 'Bezeichnung', 'E-Preis', 'Gesamt']]
        
        total_netto = 0.0
        
        for i, item in enumerate(invoice_data['items'], 1):
            # Parse structured data or fallback
            qty = item.get('menge', 1.0)
            unit = item.get('einheit', 'Stk')
            text = item.get('text', item.get('beschreibung', '')) # 'beschreibung' might be full string in legacy
            price = item.get('einzelpreis', 0.0)
            
            # Legacy fallback: if price is 0 but 'betrag' exists (manual mode old)
            if price == 0 and item.get('betrag', 0) > 0 and qty == 1:
                price = item['betrag']
            
            total = qty * price
            total_netto += total
            
            data.append([
                str(i),
                f"{qty:.2f}".replace('.', ','),
                unit,
                Paragraph(text, style_norm), # Wrap long text
                f"{price:.2f} €".replace('.', ','),
                f"{total:.2f} €".replace('.', ',')
            ])
            
        # Summary Calculation
        mwst = total_netto * 0.19
        total_brutto = total_netto + mwst
        
        # Append empty row for spacing
        data.append(['', '', '', '', '', ''])
        
        # Table Styling
        col_widths = [1*cm, 2*cm, 1.5*cm, 7.5*cm, 2.5*cm, 2.5*cm]
        t = Table(data, colWidths=col_widths)
        
        ts = [
            # Header Style
            ('LINEBELOW', (0,0), (-1,0), 1, TEXT_COLOR),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,0), 'LEFT'),
            ('ALIGN', (-2,0), (-1,-1), 'RIGHT'), # Prices right aligned
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),  # Qty right aligned
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (-1,0), (-1,-1), 0),
        ]
        t.setStyle(TableStyle(ts))
        story.append(t)
        
        # --- SUMMARY BLOCK ---
        story.append(Spacer(1, 0.5*cm))
        
        sum_data = [
            ['Summe netto', f"{total_netto:.2f} €".replace('.', ',')],
            ['Umsatzsteuer 19%', f"{mwst:.2f} €".replace('.', ',')],
            ['Gesamtsumme', f"{total_brutto:.2f} €".replace('.', ',')]
        ]
        
        t_sum = Table(sum_data, colWidths=[4*cm, 3*cm])
        t_sum.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('LINEABOVE', (0,2), (-1,2), 1, TEXT_COLOR), # Line above Total
            ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
            ('FONTSIZE', (0,2), (-1,2), 11),
        ]))
        # Align to right side of page
        t_sum_wrap = Table([[t_sum]], colWidths=[17*cm])
        t_sum_wrap.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
        story.append(t_sum_wrap)

        story.append(Spacer(1, 1.5*cm))
        
        # --- FOOTER ---
        # Payment Terms
        pay_text = "Der Rechnungsbetrag ist zahlbar innerhalb von 14 Tagen ohne Abzug."
        story.append(Paragraph(pay_text, style_norm))
        story.append(Spacer(1, 1*cm))
        
        # 3 Column Footer
        bank = mandant_config.get('bank', {})
        
        f1 = f"<b>{mandant_config.get('firma', '')}</b><br/>{m_adr.get('strasse', '')}<br/>{m_adr.get('ort', '')}"
        
        f2 = "<b>Bankverbindung</b><br/>" \
             f"Bank: {bank.get('name', '')}<br/>" \
             f"IBAN: {bank.get('iban', '')}<br/>" \
             f"BIC: {bank.get('bic', '')}"
             
        f3 = f"<b>Kontakt</b><br/>Geschäftsführer: {mandant_config.get('geschaeftsfuehrer', '')}<br/>" \
             "Steuer-Nr: -folgt-"

        t_foot = Table([[Paragraph(f1, style_small), Paragraph(f2, style_small), Paragraph(f3, style_small)]], 
                       colWidths=[5.6*cm, 5.6*cm, 5.6*cm])
        t_foot.setStyle(TableStyle([
             ('VALIGN', (0,0), (-1,-1), 'TOP'),
             ('LINEABOVE', (0,0), (-1,0), 0.5, LINE_COLOR),
             ('TOPPADDING', (0,0), (-1,0), 10),
        ]))
        story.append(t_foot)

        doc.build(story)
        print(f"\n✅ PDF erfolgreich erstellt (Green Design)!")
        print(f"📂 Pfad: {filename}")

        # --- BOOKKEEPING (Excel) ---
        try:
            einnahmen_dir = os.path.join(mandant_path, "Einnahmen")
            if not os.path.exists(einnahmen_dir): os.makedirs(einnahmen_dir, exist_ok=True)
            xlsx_path = os.path.join(einnahmen_dir, "einnahmen.xlsx")

            # Simple Desc for Booking
            desc_list = [i.get('text', i.get('beschreibung','Item')) for i in invoice_data['items']]
            full_desc = ", ".join(desc_list)
            
            data_row = {
                "Rechnungsnummer": invoice_data['nummer'],
                "Datum": invoice_data['datum'],
                "Kunde": kunde_data['firma'],
                "Beschreibung": full_desc,
                "Betrag_Netto": f"{total_netto:.2f}",
                "Betrag_Brutto": f"{total_brutto:.2f}",
                "Status": "Offen"
            }
            headers = ["Rechnungsnummer", "Datum", "Kunde", "Beschreibung", "Betrag_Netto", "Betrag_Brutto", "Status"]
            excel_utils.append_data(xlsx_path, data_row, "Einnahmen", headers)
            print(f"✅ Umsatz verbucht.")
            
        except Exception as e:
            print(f"⚠️  Fehler beim Verbuchen: {e}")

        return filename
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Fehler bei PDF-Erstellung: {e}")
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
                    'text': desc_text,
                    'menge': qty,
                    'einheit': it.get('einheit', 'Stk'),
                    'einzelpreis': price, 
                    'bericht': final_desc # Legacy holder
                })
                
            print(f"✅ Positionen übernommen.")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return
    else:
        # Manuell
        print("\n📦 Positionen eingeben:")
        while True:
            text = input("   Bezeichnung: ").strip()
            if not text: break
            
            try:
                # Ask for Quantity
                qty_s = input("   Menge [1.0]: ").strip().replace(',', '.')
                qty = float(qty_s) if qty_s else 1.0

                unit = input("   Einheit [Stk]: ").strip()
                if not unit: unit = "Stk"
                
                # Ask for Unit Price
                price_s = input("   Einzelpreis (Netto): ").replace(',', '.')
                if not price_s: break
                price = float(price_s)
                
                items.append({
                    'text': text,
                    'menge': qty,
                    'einheit': unit,
                    'einzelpreis': price,
                    # 'beschreibung' for legacy compat (simplified)
                    'beschreibung': f"{qty}x {text}"
                })
                print(f"   ok: {qty} {unit} x {price:.2f}€")
                
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
