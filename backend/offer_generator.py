"""
Angebots-Generator - Basiert auf invoice.py
Erstellt PDF-Angebote mit Preislisten-Integration
"""

import os
import datetime
import json
import re

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
from pathlib import Path

def get_and_increment_offer_counter(mandant_path, mandant_config=None):
    """Generiert und inkrementiert Angebots-Nummer mit Mandantennummer"""
    counter_file = Path(mandant_path) / "offer_counter.json"
    today = datetime.date.today()
    current_year = str(today.year)
    current_month = f"{today.month:02d}"
    
    # Get Mandantennummer from config
    mandanten_nr = "000"
    if mandant_config:
        mandanten_nr = mandant_config.get('mandantennummer', '000')
    else:
        # Try to load from config file
        config_file = Path(mandant_path) / "mandant_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    mandanten_nr = cfg.get('mandantennummer', '000')
            except:
                pass
    
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Check if year OR month changed
    if (data.get('year') != current_year) or (data.get('month') != current_month):
        # Reset counter for new month
        data = {'year': current_year, 'month': current_month, 'counter': 0}
    
    data['counter'] += 1
    
    # Update month if missing in old data to avoid errors (migration)
    data['month'] = current_month
    data['year'] = current_year

    # Format: ANG-[MandantenNr]-[Jahr]-[Monat]-[Counter]
    nummer = f"ANG-{mandanten_nr}-{current_year}-{current_month}-{data['counter']:03d}"
    
    with open(counter_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    return nummer

def create_offer_pdf(mandant_path, mandant_config, kunde_name, positionen, output_path, nummer, leistungs_von='', leistungs_bis='', kunde_adresse=''):
    """
    Erstellt Angebots-PDF
    
    positionen: [{'bezeichnung': str, 'menge': float, 'einheit': str, 'einzelpreis': float}]
    """
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=0
    )
    
    # Header
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

    # Absender Block
    firma = mandant_config.get('firma', 'Firma')
    adresse = mandant_config.get('adresse', {})
    firmen_block = f"{firma}<br/>{adresse.get('strasse', '')}<br/>{adresse.get('ort', '')}"
    
    story.append(Paragraph(firmen_block, styles['Normal']))
    story.append(Spacer(1, 1.5*cm))
    
    # Title
    story.append(Paragraph(f"<b>ANGEBOT {nummer}</b>", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Kunde & Datum
    kunde_block = f"<b>An:</b> {kunde_name}"
    if kunde_adresse:
        kunde_block += f"<br/>{kunde_adresse}"
    story.append(Paragraph(kunde_block, styles['Normal']))
    datum = datetime.date.today().strftime("%d.%m.%Y")
    story.append(Paragraph(f"<b>Datum:</b> {datum}", styles['Normal']))
    
    if leistungs_von or leistungs_bis:
        story.append(Spacer(1, 0.3*cm))
        lz_text = "<b>Leistungszeitraum:</b> "
        if leistungs_von and leistungs_bis:
            lz_text += f"{leistungs_von} bis {leistungs_bis}"
        elif leistungs_von:
            lz_text += f"ab {leistungs_von}"
        elif leistungs_bis:
            lz_text += f"bis {leistungs_bis}"
        story.append(Paragraph(lz_text, styles['Normal']))
    
    story.append(Spacer(1, 1*cm))
    
    # Positionen-Tabelle
    table_data = [['Pos', 'Beschreibung', 'Menge', 'Einzel', 'Gesamt']]
    
    style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=10, wordWrap='CJK', fontName='Helvetica')
    
    netto_gesamt = 0
    for idx, pos in enumerate(positionen, 1):
        menge = float(pos.get('menge', 0))
        preis = float(pos.get('einzelpreis', 0))
        gesamt = menge * preis
        netto_gesamt += gesamt
        
        table_data.append([
            str(idx),
            Paragraph(clean_text(pos.get('bezeichnung', '')), style_table_cell),
            f"{menge} {clean_text(pos.get('einheit', 'Stk'))}",
            f"{preis:.2f}€",
            f"{gesamt:.2f}€"
        ])
    
    # Styles for Table
    style_right = ParagraphStyle('Right', parent=styles['Normal'], alignment=2) # 2 = TA_RIGHT

    # Summen
    is_kleingewerbe = mandant_config.get('unternehmensform') == 'Kleingewerbe'
    mwst_satz = 0.0 if is_kleingewerbe else 0.19
    
    mwst = netto_gesamt * mwst_satz
    brutto = netto_gesamt + mwst
    
    table_data.append(['', '', '', 'Netto:', f"{netto_gesamt:.2f}€"])
    
    if is_kleingewerbe:
        table_data.append(['', '', '', 'MwSt 0%:', f"{mwst:.2f}€"])
    else:
        table_data.append(['', '', '', 'MwSt 19%:', f"{mwst:.2f}€"])
    
    # Use Paragraph to interpret <b> tags
    table_data.append([
        '', '', '', 
        Paragraph('<b>Brutto:</b>', style_right), 
        Paragraph(f"<b>{brutto:.2f}€</b>", style_right)
    ])
    
    table = Table(table_data, colWidths=[2.3375*cm, 7.65*cm, 2.3375*cm, 2.3375*cm, 2.3375*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-4), 1, colors.black),
        ('LINEBELOW', (0,-3), (-1,-3), 1, colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 1*cm))
    
    # Footer
    if is_kleingewerbe:
        story.append(Paragraph("<font size=10>Gemäß § 19 UStG wird keine Umsatzsteuer ausgewiesen.</font>", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
    ustid = mandant_config.get('ustid', '').strip()
    steuernummer = mandant_config.get('steuernummer', '').strip()

    tax_string = ""
    if ustid:
        tax_string = f"USt-ID: {ustid}"
    elif steuernummer:
        tax_string = f"Steuer-Nr: {steuernummer}"
        
    if tax_string:
        story.append(Paragraph(f"<font size=10>{tax_string}</font>", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<i>Vielen Dank für Ihre Anfrage!</i>", styles['Normal']))
    story.append(Paragraph(f"<i>Angebot gültig bis: {(datetime.date.today() + datetime.timedelta(days=30)).strftime('%d.%m.%Y')}</i>", styles['Normal']))
    
    doc.build(story)
    
    return brutto, netto_gesamt

if __name__ == '__main__':
    # Test
    test_positionen = [
        {'bezeichnung': 'Beratungsstunde', 'menge': 5, 'einheit': 'Std', 'einzelpreis': 80},
        {'bezeichnung': 'Material', 'menge': 1, 'einheit': 'Pauschale', 'einzelpreis': 250}
    ]
    
    config = {
        'firma': 'Test GmbH',
        'adresse': {'strasse': 'Teststr. 1', 'ort': '12345 Berlin'}
    }
    
    create_offer_pdf('.', config, 'Testkunde', test_positionen, 'test_angebot.pdf', 'ANG-2025-001')
    print("✅ Test-PDF erstellt")
